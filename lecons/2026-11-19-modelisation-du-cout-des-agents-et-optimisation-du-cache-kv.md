# Modélisation du coût des agents et optimisation du cache KV

*Leçon du 2026-11-19*

# Modélisation du coût des agents et optimisation du cache KV

## Le concept
L'exécution de pipelines d'agents LLM génère une quantité massive de tokens. Récemment, la recherche s'est penchée sur la thermodynamique logicielle pour modéliser le coût des agents de codage en séparant le travail de la chaleur, utilisant par exemple les tests unitaires comme démon de Maxwell. Parallèlement, l'optimisation des moteurs d'inférence (comme la recherche par faisceau pour la recommandation générative) cherche à éviter les accès redondants au cache KV sur les préfixes de prompts partagés.

## Pourquoi c'est important
En tant qu'ingénieure IA construisant des agents et des pipelines RAG, la maîtrise de la consommation de tokens et de la latence est critique. Ignorer la redondance des accès au cache KV ou laisser les agents s'échanger des messages superflus entraîne des coûts d'infrastructure exorbitants et une latence inacceptable en production.

## Comment l'appliquer
Pour optimiser vos flux d'agents et réduire la surcharge d'invocation du moteur de service, structurez vos prompts et vos appels pour maximiser le partage de préfixes et bénéficier de l'optimisation du cache KV. Vous pouvez également vous inspirer des approches d'optimisation de la recherche par faisceau pour les séquences longues.

```python
# Exemple conceptuel d'optimisation du cache KV pour un prompt partagé en RAG
class KV byłaCacheOptimizer:
    def __init__(self, shared_prefix_prompt: str):
        self.shared_prefix = shared_prefix_prompt
        # Le moteur de service doit identifier ce préfixe pour éviter les accès redondants

    def generate_with_shared_context(self, user_query: str):
        optimized_payload = {
            "prefix_cache": self.shared_prefix,
            "query": user_query
        }
        return optimized_payload
```

## Exercice pratique (30 min max)
1. Analysez un de vos pipelines d'agents actuels et identifiez les sections où le même contexte (ex: instructions système, schémas de base de données pour le text-to-SQL) est répété à chaque tour.
2. Évaluez la part de "chaleur" (tokens générés ou passés inutilement) par rapport au "travail" effectif.
3. Rédigez un plan pour mutualiser ces préfixes et activer l'optimisation du cache KV.

## Questions d'auto-évaluation
1. **Qu'est-ce que modélise la théorie de la thermodynamique logicielle pour les agents de codage ?**
   - *Réponse :* Elle modélise le coût d'exécution en comptant les tokens générés, séparés en travail et en chaleur, avec les tests unitaires comme démon de Maxwell.
2. **Quel est l'objectif principal de l'optimisation de la recherche par faisceau présentée dans la veille ?**
   - *Réponse :* Éviter les accès redondants au cache KV sur le préfixe de prompt partagé pour réduire la surcharge du moteur de service.
3. **Comment les tests unitaires sont-ils qualifiés dans ce modèle thermodynamique ?**
   - *Réponse :* Ils agissent comme un démon de Maxwell.

## Pour aller plus loin
- [Where the Tokens Go: Heat, Entropy and Error in Agentic Coding](https://arxiv.org/abs/2611.23375)
- [Optimize the Cob, Then the Kernel: Optimizing Beam Search for Generative Recommendation Inference](https://arxiv.org/abs/2611.23339)

