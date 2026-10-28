"""Collecte des contenus depuis les flux RSS et l'API Hugging Face."""
import calendar
import logging
import re
import time
from dataclasses import dataclass, asdict

import feedparser
import requests

log = logging.getLogger(__name__)
HF_PAPERS_API = "https://huggingface.co/api/daily_papers"
HEADERS = {"User-Agent": "veille-ia/1.0 (+https://github.com)"}


@dataclass
class Element:
    id: str
    titre: str
    url: str
    source: str
    categorie: str
    resume: str
    date: float  # timestamp UTC

    def to_dict(self):
        return asdict(self)


def nettoyer(texte, limite=600):
    texte = re.sub(r"<[^>]+>", " ", texte or "")
    texte = re.sub(r"\s+", " ", texte).strip()
    return texte[:limite]


def _date_entree(entree):
    for cle in ("published_parsed", "updated_parsed"):
        if entree.get(cle):
            return calendar.timegm(entree[cle])
    return time.time()


def lire_flux(source, contenu):
    flux = feedparser.parse(contenu)
    elements = []
    for e in flux.entries:
        url = e.get("link", "")
        if not url:
            continue
        elements.append(Element(
            id=url,
            titre=nettoyer(e.get("title", ""), 200),
            url=url,
            source=source["nom"],
            categorie=source["categorie"],
            resume=nettoyer(e.get("summary", "")),
            date=_date_entree(e),
        ))
    return elements


def lire_hf_papers(source, donnees):
    elements = []
    for item in donnees:
        papier = item.get("paper", {})
        pid = papier.get("id")
        if not pid:
            continue
        date = item.get("publishedAt") or papier.get("publishedAt")
        ts = time.time()
        if date:
            ts = calendar.timegm(time.strptime(date[:19], "%Y-%m-%dT%H:%M:%S"))
        elements.append(Element(
            id=f"https://huggingface.co/papers/{pid}",
            titre=nettoyer(papier.get("title", ""), 200),
            url=f"https://huggingface.co/papers/{pid}",
            source=source["nom"],
            categorie=source["categorie"],
            resume=nettoyer(papier.get("summary", "")),
            date=ts,
        ))
    return elements


def correspond(element, mots_cles):
    texte = f"{element.titre} {element.resume}".lower()
    return any(re.search(rf"\b{re.escape(m.lower())}\b", texte) for m in mots_cles)


def collecter(config, deja_vus, maintenant=None):
    """Retourne les nouveaux éléments récents, sans doublons, triés du plus récent au plus ancien."""
    maintenant = maintenant or time.time()
    limite = maintenant - config.get("jours", 7) * 86400
    max_par_source = config.get("max_par_source", 12)
    resultats, vus = [], set(deja_vus)

    for source in config["sources"]:
        try:
            if source.get("type") == "hf_papers":
                r = requests.get(HF_PAPERS_API, headers=HEADERS, timeout=20)
                r.raise_for_status()
                elements = lire_hf_papers(source, r.json())
            else:
                r = requests.get(source["url"], headers=HEADERS, timeout=20)
                r.raise_for_status()
                elements = lire_flux(source, r.content)
        except Exception as exc:  # une source en panne ne doit pas bloquer la veille
            log.warning("Source ignorée %s : %s", source["nom"], exc)
            continue

        mots_cles = source.get("mots_cles") or config.get("mots_cles", [])
        elements.sort(key=lambda e: e.date, reverse=True)
        gardes = 0
        for el in elements:
            if gardes >= max_par_source:
                break
            if el.id in vus or el.date < limite:
                continue
            if source.get("filtrer") and not correspond(el, mots_cles):
                continue
            vus.add(el.id)
            resultats.append(el)
            gardes += 1
        log.info("%s : %d éléments retenus", source["nom"], gardes)

    resultats.sort(key=lambda e: e.date, reverse=True)
    return resultats[: config.get("max_elements", 150)]
