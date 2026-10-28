"""Appels au LLM (Gemini par défaut) pour trier, résumer et créer la leçon."""
import json
import os

import requests

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent"

PROMPT_DIGEST = """Tu es un veilleur expert en IA. Voici mon profil :
{profil}

Voici les contenus collectés cette semaine (JSON) :
{elements}

Sélectionne au maximum {max_selection} éléments les plus utiles pour mon travail.
Privilégie la nouveauté, l'impact pratique et la fiabilité. Écris en français.
Réponds UNIQUEMENT en JSON avec ce format :
{{"selection": [{{"id": "<id exact de l'élément>", "categorie": "article|modele|pratique",
"resume": "2-3 phrases factuelles", "pourquoi": "1 phrase : pourquoi c'est utile pour moi"}}],
"tendance": "2-3 phrases sur la tendance principale de la semaine"}}"""

PROMPT_LECON = """Tu es un formateur expert en IA. Voici mon profil :
{profil}

Voici la sélection de veille de la semaine (JSON) :
{selection}

1. Propose 3 idées concrètes que je peux proposer à mon équipe, inspirées de cette veille.
2. Choisis LE sujet le plus formateur et écris une leçon complète en Markdown (en français) avec :
   ## Le concept, ## Pourquoi c'est important, ## Comment l'appliquer (avec exemple de code si pertinent),
   ## Exercice pratique (30 min max), ## Questions d'auto-évaluation (3 questions + réponses),
   ## Pour aller plus loin (liens issus de la sélection uniquement).
N'invente aucun fait ni lien : appuie-toi seulement sur la sélection.
Réponds UNIQUEMENT en JSON avec ce format :
{{"idees": [{{"titre": "...", "description": "2-3 phrases", "effort": "faible|moyen|élevé", "source": "<url>"}}],
"lecon": {{"titre": "...", "markdown": "..."}}}}"""


class GeminiLLM:
    def __init__(self, cle=None, modele=None):
        self.cle = cle or os.environ["GEMINI_API_KEY"]
        self.modele = modele or os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    def json(self, prompt):
        r = requests.post(
            GEMINI_URL.format(modele=self.modele),
            params={"key": self.cle},
            json={
                "contents": [{"parts": [{"text": prompt}]}],
                "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4},
            },
            timeout=180,
        )
        r.raise_for_status()
        texte = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(texte)


def faire_digest(llm, config, elements):
    entree = [
        {"id": e.id, "titre": e.titre, "source": e.source, "categorie": e.categorie, "resume": e.resume}
        for e in elements
    ]
    reponse = llm.json(PROMPT_DIGEST.format(
        profil=config.get("profil", ""),
        elements=json.dumps(entree, ensure_ascii=False),
        max_selection=config.get("max_selection", 12),
    ))
    # On ne garde que les ids réellement collectés : le LLM ne peut pas inventer de lien.
    par_id = {e.id: e for e in elements}
    selection = []
    for item in reponse.get("selection", []):
        el = par_id.get(item.get("id"))
        if el:
            selection.append({**item, "titre": el.titre, "url": el.url, "source": el.source})
    return {"selection": selection, "tendance": reponse.get("tendance", "")}


def faire_lecon(llm, config, selection):
    return llm.json(PROMPT_LECON.format(
        profil=config.get("profil", ""),
        selection=json.dumps(selection, ensure_ascii=False),
    ))
