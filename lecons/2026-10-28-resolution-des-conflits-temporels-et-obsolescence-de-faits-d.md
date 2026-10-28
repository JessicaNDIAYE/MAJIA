# Résolution des conflits temporels et obsolescence de faits dans la mémoire des agents LLM

*Leçon du 2026-10-28*

## Le concept

Lorsqu'un agent conversationnel ou un pipeline RAG accumule des informations au fil des sessions, il stocke souvent des versions contradictoires ou successives d'un même attribut (par exemple : « L'adresse de facturation est à Lyon » en session 1, puis « Le client a déménagé à Nantes » en session 3).

L'intuition classique consiste à penser que fournir davantage de tokens de contexte au modèle permettra toujours d'améliorer sa prise de décision, dès lors que l'information la plus récente figure dans le prompt. Les récents travaux de recherche (« When Retrieval Is Not Enough: Obsolete Facts in Agent Memory ») démontrent empiriquement l'inverse : sur la tâche standardisée *FactConsolidation*, la précision chute de **45% à 32%** lorsque le budget de tokens passe de 64 à 512 tokens. L'échec ne provient pas du retrieval (qui a bien retrouvé le fait valide), mais de l'incapacité de la phase de génération du LLM à arbitrer et prioriser le fait récent face au bruit historique accumulé.

## Pourquoi c'est important

En tant qu'ingénieur construisant des agents et des architectures RAG en production, ce phénomène a des répercussions directes sur vos métriques de qualité :
1. **La régression contextuelle paradoxale** : Injecter un historique brut ou étendre indistinctement la fenêtre de contexte dégrade la fidélité de l'agent au lieu de la renforcer.
2. **Les hallucinations par inertie** : Le LLM a tendance à moyenner les informations ou à sélectionner le fait qui apparaît le plus souvent dans le prompt plutôt que le plus récent.
3. **L'illusion du « long-context »** : Même avec des contextes atteignant 1M de tokens, la présence de versions conflictuelles déstabilise l'attention du décodeur. Le problème doit être résolu en amont (au niveau de la gestion de mémoire et du parsing d'état) et non espéré lors de la génération finale.

## Comment l'appliquer

Pour mitiger l'impact des faits obsolètes, il faut découpler l'acquisition de mémoire et la consolidation d'état avant injection dans le prompt de raisonnement.

### Stratégie recommandée :
- Maintenir une couche de métadonnées temporelles explicites (`valid_from`, `is_active`).
- Définir un algorithme d'invalidation sélective des clés obsolètes avant l'assemblage du prompt final.

```python
from datetime import datetime
from typing import Dict, List, Optional
from pydantic import BaseModel, Field

class MemoryFact(BaseModel):
    key: str
    value: str
    timestamp: datetime
    is_obsolete: bool = False

class AgentFactStore:
    def __init__(self):
        self.facts: Dict[str, List[MemoryFact]] = {}

    def upsert_fact(self, key: str, value: str, timestamp: Optional[datetime] = None):
        ts = timestamp or datetime.utcnow()
        new_fact = MemoryFact(key=key, value=value, timestamp=ts)
        
        if key not in self.facts:
            self.facts[key] = []
        
        # Invalidation explicite des faits précédents pour la même clé
        for f in self.facts[key]:
            f.is_obsolete = True
            
        self.facts[key].append(new_fact)

    def get_consolidated_context(self) -> str:
        """
        Génère un contexte nettoyé contenant uniquement les faits actifs,
        évitant de saturer la fenêtre avec des versions contradictoires.
        """
        active_facts = [
            f"{k}: {facts[-1].value} (mis à jour le {facts[-1].timestamp.strftime('%Y-%m-%d')})"
            for k, facts in self.facts.items()
            if facts and not facts[-1].is_obsolete
        ]
        return "\n".join(active_facts)

# Exemple d'usage dans un pipeline d'agent
store = AgentFactStore()
store.upsert_fact("base_de_donnees", "PostgreSQL 14", datetime(2025, 1, 10))
# Migration ultérieure
store.upsert_fact("base_de_donnees", "PostgreSQL 16", datetime(2026, 2, 1))

# Injection dans le prompt : l'ancienne version est éliminée de la mémoire contextuelle
prompt_context = store.get_consolidated_context()
# Sortie: 'base_de_donnees: PostgreSQL 16 (mis à jour le 2026-02-01)'
```

## Exercice pratique (30 min max)

1. **Objectif** : Reproduire et corriger un scénario de conflit d'obsolescence dans votre pipeline d'agent.
2. **Étape 1 (10 min)** : Créez un prompt contenant un profil utilisateur avec deux instructions contradictoires espacées dans le texte :
   - Au début : `"L'utilisateur demande un export au format CSV."`
   - À la fin : `"Mise à jour : L'utilisateur a changé d'avis, exporter impérativement en JSON."`
3. **Étape 2 (10 min)** : Testez le comportement avec votre LLM habituel en faisant varier la taille du contexte intermédiaire (ajoutez 100, 300 puis 500 tokens de faux logs de conversation entre les deux instructions). Observez si le modèle continue à choisir systématiquement le format JSON.
4. **Étape 3 (10 min)** : Implémentez un pré-processeur qui extrait les paires (clé, valeur, horodatage) et supprime les directives écrasées avant que le prompt ne soit transmis au modèle final.

## Questions d'auto-évaluation

1. **Pourquoi l'augmentation de la fenêtre de contexte (ex. de 64 à 512 tokens) entraîne-t-elle une baisse de 13 points de précision sur FactConsolidation ?**
   - *Réponse* : Parce que le mécanisme d'attention et de génération du LLM subit des interférences sémantiques accrues entre les anciennes et les nouvelles versions. Le modèle ne dispose pas d'un a priori temporel strict et tend à s'appuyer sur la redondance textuelle ou la position relative sans savoir trancher de façon fiable lors de la génération.
2. **Si le retrieval RAG extrait avec succès le document le plus récent, pourquoi l'agent peut-il quand même répondre une information fausse ?**
   - *Réponse* : Parce que la présence du bon document dans le prompt n'assure pas sa prise en compte prioritaire par le décodeur s'il est noyé au milieu d'extraits contradictoires ou de biais paramétriques internes au modèle.
3. **Quelle est la différence fondamentale entre une heuristique fixe ("toujours privilégier le contexte") et une approche d'arbitrage structurée ?**
   - *Réponse* : Une règle fixe échoue dès lors que le retrieval ramène des données corrompues, bruitées ou obsolètes face aux connaissances stables du modèle. Une approche structurée (ex. pondération bayésienne ou invalidation explicite par graphe d'état) conditionne l'arbitrage à la fiabilité et à la validité temporelle mesurées de chaque source.

## Pour aller plus loin

- Étude détaillée sur les défaillances de consolidation de mémoire : [When Retrieval Is Not Enough: Obsolete Facts in Agent Memory](https://arxiv.org/abs/2610.36308)
- Modélisation théorique des arbitrages mémoire vs contexte : [Don't Pick a Winner: Knowledge Conflicts Need a Prior, Not a Rule](https://arxiv.org/abs/2610.36169)
- Structuration logique et validation formelle de connaissances : [OA-RAG: Ontology-based Agentic RAG for Faithful LLM Reasoning](https://arxiv.org/abs/2610.36335)
