"""Appels au LLM (Gemini par défaut) pour trier, résumer et créer la leçon."""
import json
import logging
import os
import re
import time

import requests

log = logging.getLogger(__name__)

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{modele}:generateContent"
GEMINI_MODELES_URL = "https://generativelanguage.googleapis.com/v1beta/models"

CATEGORIES = "article|modele|robotique|parsing|monitoring|pratique|comparatif"

PROMPT_DIGEST = """Tu es un veilleur expert en IA, très technique. Voici mon profil :
{profil}

Voici les contenus collectés cette semaine (JSON) :
{elements}

Voici le tableau des prix réels des modèles (en $ par million de tokens, JSON) :
{prix}

Sélectionne au maximum {max_selection} éléments les plus utiles pour mon travail, en couvrant
si possible chaque catégorie : {categories}.
Règles :
- Sois concret et technique : chiffres, versions, tailles de contexte, prix, benchmarks, limites.
- Pas de formules marketing ni de généralités ("révolutionnaire", "change la donne"…).
- N'utilise que les informations présentes dans les contenus ou le tableau ; si une donnée manque, ne l'invente pas.
- Écris en français.
Réponds UNIQUEMENT en JSON avec ce format :
{{"selection": [{{"id": "<id exact de l'élément>", "categorie": "{categories}",
"resume": "2-3 phrases factuelles",
"specificites": ["2 à 4 points précis : ce qui distingue ce modèle/outil/article, forces, limites, chiffres"],
"pourquoi": "1 phrase : pourquoi c'est utile pour moi"}}],
"tendance": "2-3 phrases sur la tendance principale de la semaine",
"comparatif": "Analyse en Markdown (liste à puces) du tableau de prix : meilleur rapport qualité/prix
par usage (agents, RAG, parsing, volume), modèles les moins chers, changements de la semaine.
Chaque affirmation doit s'appuyer sur un chiffre du tableau. Chaîne vide si le tableau est vide."}}"""

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
    """Client Gemini. Si le modèle demandé n'existe plus, choisit le meilleur modèle Flash disponible."""

    def __init__(self, cle=None, modele=None):
        self.cle = cle or os.environ["GEMINI_API_KEY"]
        self.modele = modele or os.environ.get("GEMINI_MODEL") or "gemini-flash-latest"

    def _appeler(self, prompt):
        corps = {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.4},
        }
        for essai in range(4):
            r = requests.post(GEMINI_URL.format(modele=self.modele), params={"key": self.cle},
                              json=corps, timeout=300)
            if r.status_code not in (429, 500, 503) or essai == 3:
                return r
            time.sleep(15 * (essai + 1))  # quota ou surcharge passagère : on réessaie

    def json(self, prompt):
        r = self._appeler(prompt)
        if r.status_code == 404:
            ancien, self.modele = self.modele, self.choisir_modele()
            log.warning("Modèle %s introuvable, utilisation de %s", ancien, self.modele)
            r = self._appeler(prompt)
        if not r.ok:
            raise RuntimeError(f"Gemini {self.modele} : erreur {r.status_code} — {r.text[:500]}")
        texte = r.json()["candidates"][0]["content"]["parts"][0]["text"]
        return json.loads(texte)

    def choisir_modele(self):
        r = requests.get(GEMINI_MODELES_URL, params={"key": self.cle, "pageSize": 1000}, timeout=30)
        r.raise_for_status()
        return meilleur_modele(r.json().get("models", []))


def meilleur_modele(modeles):
    """Le modèle Flash stable le plus récent qui sait générer du texte."""
    exclus = ("lite", "image", "tts", "audio", "live", "embedding", "thinking", "exp", "preview")

    def version(nom):
        return tuple(int(n) for n in re.findall(r"\d+", nom.split("gemini-", 1)[-1].split("-flash")[0]))

    candidats = [
        m["name"].removeprefix("models/") for m in modeles
        if "generateContent" in m.get("supportedGenerationMethods", [])
        and re.fullmatch(r"models/gemini-[\d.]+-flash(-\d+)?", m.get("name", ""))
        and not any(x in m["name"] for x in exclus)
    ]
    if not candidats:
        raise RuntimeError("Aucun modèle Gemini Flash disponible pour cette clé API.")
    return max(candidats, key=lambda nom: (version(nom), -len(nom)))


def faire_digest(llm, config, elements, prix=None):
    entree = [
        {"id": e.id, "titre": e.titre, "source": e.source, "categorie": e.categorie, "resume": e.resume}
        for e in elements
    ]
    reponse = llm.json(PROMPT_DIGEST.format(
        profil=config.get("profil", ""),
        elements=json.dumps(entree, ensure_ascii=False),
        max_selection=config.get("max_selection", 25),
        prix=json.dumps(prix or [], ensure_ascii=False),
        categories=CATEGORIES,
    ))
    # On ne garde que les ids réellement collectés : le LLM ne peut pas inventer de lien.
    par_id = {e.id: e for e in elements}
    selection = []
    for item in reponse.get("selection", []):
        el = par_id.get(item.get("id"))
        if el:
            categorie = item.get("categorie")
            if categorie not in CATEGORIES.split("|"):
                categorie = el.categorie
            selection.append({**item, "categorie": categorie, "titre": el.titre, "url": el.url,
                              "source": el.source})
    return {"selection": selection, "tendance": reponse.get("tendance", ""),
            "comparatif": reponse.get("comparatif", "")}


def faire_lecon(llm, config, selection):
    return llm.json(PROMPT_LECON.format(
        profil=config.get("profil", ""),
        selection=json.dumps(selection, ensure_ascii=False),
    ))
