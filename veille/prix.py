"""Tableau comparatif prix / qualité des modèles, à partir de données chiffrées (pas du LLM).

- Prix et contexte : API publique OpenRouter (sans clé).
- Qualité et vitesse (optionnel) : API Artificial Analysis si ARTIFICIAL_ANALYSIS_API_KEY est défini.
"""
import logging
import os
import re

import requests

log = logging.getLogger(__name__)
OPENROUTER_API = "https://openrouter.ai/api/v1/models"
AA_API = "https://artificialanalysis.ai/api/v2/data/llms/models"


def _normaliser(nom):
    return re.sub(r"[^a-z0-9]", "", nom.lower())


def lire_openrouter(donnees, fournisseurs, par_fournisseur):
    """Garde les modèles les plus récents de chaque fournisseur suivi, prix en $ par million de tokens."""
    par_fourn = {}
    for m in donnees.get("data", []):
        mid = m.get("id", "")
        fourn = mid.split("/")[0]
        if fourn not in fournisseurs or ":" in mid:  # ignore les variantes :free, :beta…
            continue
        try:
            entree = float(m["pricing"]["prompt"]) * 1e6
            sortie = float(m["pricing"]["completion"]) * 1e6
        except (KeyError, TypeError, ValueError):
            continue
        if entree <= 0 or sortie <= 0:
            continue
        par_fourn.setdefault(fourn, []).append({
            "id": mid,
            "nom": m.get("name", mid),
            "fournisseur": fourn,
            "entree": round(entree, 3),
            "sortie": round(sortie, 3),
            "contexte": m.get("context_length") or 0,
            "cree": m.get("created") or 0,
        })
    modeles = []
    for fourn in fournisseurs:
        recents = sorted(par_fourn.get(fourn, []), key=lambda x: x["cree"], reverse=True)
        modeles += recents[:par_fournisseur]
    return modeles


def ajouter_qualite(modeles, donnees_aa):
    """Associe l'indice d'intelligence et la vitesse d'Artificial Analysis par nom de modèle."""
    index = {}
    for m in donnees_aa.get("data", []):
        index[_normaliser(m.get("slug") or m.get("name", ""))] = m
    for modele in modeles:
        cle = _normaliser(modele["id"].split("/", 1)[1])
        aa = index.get(cle)
        if not aa:
            continue
        modele["qualite"] = (aa.get("evaluations") or {}).get("artificial_analysis_intelligence_index")
        modele["vitesse"] = aa.get("median_output_tokens_per_second")
    return modeles


def comparer(modeles, precedents):
    """Repère les nouveaux modèles et les changements de prix depuis la semaine dernière."""
    avant = {m["id"]: m for m in precedents}
    for m in modeles:
        ancien = avant.get(m["id"])
        if not ancien:
            m["evolution"] = "🆕 nouveau" if precedents else ""
        elif (ancien["entree"], ancien["sortie"]) != (m["entree"], m["sortie"]):
            m["evolution"] = f"prix modifié (avant {ancien['entree']} / {ancien['sortie']} $)"
        else:
            m["evolution"] = ""
    return modeles


def recuperer(config, precedents):
    reglages = config.get("prix") or {}
    if not reglages:
        return []
    try:
        r = requests.get(OPENROUTER_API, timeout=30)
        r.raise_for_status()
        modeles = lire_openrouter(r.json(), reglages.get("fournisseurs", []),
                                  reglages.get("modeles_par_fournisseur", 4))
    except Exception as exc:
        log.warning("Prix indisponibles : %s", exc)
        return []

    cle = os.environ.get("ARTIFICIAL_ANALYSIS_API_KEY")
    if cle:
        try:
            r = requests.get(AA_API, headers={"x-api-key": cle}, timeout=30)
            r.raise_for_status()
            ajouter_qualite(modeles, r.json())
        except Exception as exc:
            log.warning("Scores de qualité indisponibles : %s", exc)
    return comparer(modeles, precedents)


def tableau_markdown(modeles):
    if not modeles:
        return ""
    avec_qualite = any(m.get("qualite") is not None for m in modeles)
    entete = "| Modèle | Entrée $/M | Sortie $/M | Contexte |"
    sep = "|---|---:|---:|---:|"
    if avec_qualite:
        entete += " Qualité (AA) | Vitesse tok/s |"
        sep += "---:|---:|"
    lignes = [entete + " Évolution |", sep + "---|"]
    for m in modeles:
        ligne = f"| {m['nom']} | {m['entree']} | {m['sortie']} | {m['contexte'] // 1000}k |"
        if avec_qualite:
            q, v = m.get("qualite"), m.get("vitesse")
            ligne += f" {q if q is not None else '–'} | {round(v) if v else '–'} |"
        lignes.append(ligne + f" {m.get('evolution', '')} |")
    return "\n".join(lignes)
