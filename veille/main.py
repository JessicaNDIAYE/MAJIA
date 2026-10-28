"""Point d'entrée : python -m veille.main [--dry-run]"""
import argparse
import datetime as dt
import json
import logging
import sys
from pathlib import Path

import yaml

from . import collecte, llm, prix, rendu

RACINE = Path(__file__).resolve().parent.parent
FICHIER_VUS = RACINE / "data" / "vus.json"


JOURS = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]


def jour_de_lecon(config, jour):
    """La leçon et les idées sont générées une fois par semaine (par défaut le lundi), ou chaque jour."""
    reglage = str(config.get("lecon_le", "lundi")).lower()
    return reglage == "tous" or JOURS[jour.weekday()] == reglage


def mail_du_jour(config, jour):
    """Avec mail_weekend: lundi (défaut), pas d'e-mail le samedi ni le dimanche : ils sont résumés le lundi."""
    return jour.weekday() < 5 or str(config.get("mail_weekend", "lundi")).lower() != "lundi"


def lire_weekend(racine, config, jour):
    """Le lundi, les veilles du samedi et du dimanche précédents, pour la section « raté ce week-end »."""
    if jour.weekday() != 0 or mail_du_jour(config, jour - dt.timedelta(days=1)):
        return []
    jours = []
    for decalage in (2, 1):
        fichier = racine / "data" / "semaines" / f"{(jour - dt.timedelta(days=decalage)).isoformat()}.json"
        if fichier.exists():
            jours.append(json.loads(fichier.read_text(encoding="utf-8")))
    return jours


def executer(racine, client_llm, envoyer=None, maintenant=None, aujourd_hui=None):
    config = yaml.safe_load((racine / "sources.yaml").read_text(encoding="utf-8"))
    fichier_vus = racine / "data" / "vus.json"
    deja_vus = json.loads(fichier_vus.read_text()) if fichier_vus.exists() else []

    elements = collecte.collecter(config, deja_vus, maintenant)
    if not elements:
        logging.warning("Aucun nouveau contenu depuis la dernière veille.")
        return None

    fichier_prix = racine / "data" / "prix.json"
    prix_avant = json.loads(fichier_prix.read_text()) if fichier_prix.exists() else []
    modeles = prix.recuperer(config, prix_avant)

    digest = llm.faire_digest(client_llm, config, elements, modeles)
    if not digest["selection"]:
        logging.warning("Le LLM n'a rien sélectionné.")
        return None
    aujourd_hui = aujourd_hui or dt.date.today()
    lecon = {"idees": [], "lecon": None}
    if jour_de_lecon(config, aujourd_hui):
        try:
            lecon = llm.faire_lecon(client_llm, config, digest["selection"])
        except Exception as exc:  # la veille part quand même, sans leçon ni idées
            logging.error("Leçon non générée : %s", exc)
            lecon = {"idees": [], "lecon": None, "echec": True}

    date = aujourd_hui.isoformat()
    md = rendu.digest_markdown(date, digest, lecon, prix.tableau_markdown(modeles))
    chemin_lecon = rendu.sauvegarder(racine, date, md, lecon, lecon.get("idees", []))

    # Version structurée du jour, utilisée par le site web.
    semaine = {**digest, "date": date, "prix": modeles, "idees": lecon.get("idees", []),
               "lecon": {**lecon["lecon"], "fichier": chemin_lecon.name} if chemin_lecon else None}
    (racine / "data" / "semaines").mkdir(parents=True, exist_ok=True)
    (racine / "data" / "semaines" / f"{date}.json").write_text(
        json.dumps(semaine, indent=1, ensure_ascii=False), encoding="utf-8")

    if envoyer and mail_du_jour(config, aujourd_hui):
        weekend = lire_weekend(racine, config, aujourd_hui)
        corps = md + rendu.weekend_markdown(weekend)
        sujet = f"Veille IA — {date}" + (" + week-end" if weekend else "") + (
            f" — {lecon['lecon']['titre']}" if lecon["lecon"] else "")
        envoyer(sujet, corps, rendu.en_html(corps))
    elif envoyer:
        logging.info("Week-end : pas d'e-mail aujourd'hui, la veille sera résumée lundi.")

    # Garde un historique borné des liens déjà traités pour éviter les doublons.
    fichier_vus.parent.mkdir(exist_ok=True)
    tous = deja_vus + [e.id for e in elements]
    fichier_vus.write_text(json.dumps(tous[-5000:], indent=0), encoding="utf-8")
    if modeles:
        fichier_prix.write_text(json.dumps(modeles, indent=1, ensure_ascii=False), encoding="utf-8")
    return md


def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
    parser = argparse.ArgumentParser(description="Génère et envoie la veille IA quotidienne.")
    parser.add_argument("--dry-run", action="store_true", help="n'envoie pas l'e-mail, affiche le digest")
    args = parser.parse_args()

    envoyer = None
    if not args.dry_run:
        from .envoi import envoyer
    md = executer(RACINE, llm.GeminiLLM(), envoyer)
    if args.dry_run and md:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())
