"""Mise en forme du digest, de la leçon et du backlog d'idées."""
import re
import unicodedata
from pathlib import Path

import markdown

TITRES = {
    "modele": "🤖 Modèles et labos (Claude, NVIDIA, OpenAI, Google, open source…)",
    "article": "📄 Articles scientifiques",
    "robotique": "🦾 Robotique",
    "parsing": "🔍 Parsing de documents avec l'IA",
    "monitoring": "📈 Monitoring et observabilité",
    "pratique": "🛠️ Nouvelles pratiques",
    "comparatif": "⚖️ Benchmarks et comparatifs",
}


def slug(texte):
    texte = unicodedata.normalize("NFKD", texte).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", texte.lower()).strip("-")[:60] or "lecon"


def digest_markdown(date, digest, lecon, tableau_prix=""):
    lignes = [f"# Veille IA — semaine du {date}", ""]
    if digest.get("tendance"):
        lignes += [f"> **Tendance de la semaine :** {digest['tendance']}", ""]

    for cat, titre in TITRES.items():
        items = [s for s in digest["selection"] if s.get("categorie") == cat]
        if not items:
            continue
        lignes += [f"## {titre}", ""]
        for s in items:
            lignes += [
                f"### [{s['titre']}]({s['url']})",
                f"*{s['source']}*", "",
                s.get("resume", ""), "",
            ]
            lignes += [f"- {point}" for point in s.get("specificites", [])]
            lignes += ["", f"👉 {s.get('pourquoi', '')}", ""]

    if tableau_prix:
        lignes += ["## 💰 Comparatif prix / qualité", "",
                   "*Prix réels OpenRouter en $ par million de tokens.*", "", tableau_prix, ""]
        if digest.get("comparatif"):
            lignes += [digest["comparatif"], ""]

    if lecon.get("idees"):
        lignes += ["## 💡 Idées à proposer à ton équipe", ""]
    for i, idee in enumerate(lecon.get("idees", []), 1):
        lignes += [f"{i}. **{idee['titre']}** (effort : {idee.get('effort', '?')}) — {idee['description']}"]
    if lecon.get("lecon"):
        lignes += ["", f"## 🎓 Leçon de la semaine : {lecon['lecon']['titre']}", "", lecon["lecon"]["markdown"], ""]
    else:
        lignes += ["", "*La leçon n'a pas pu être générée cette semaine.*", ""]
    lignes += ["---", "*Résumés générés par IA à partir des abstracts : vérifie la source avant de citer.*"]
    return "\n".join(lignes)


def en_html(md):
    corps = markdown.markdown(md, extensions=["fenced_code", "tables"])
    return (
        '<html><body style="font-family:Arial,sans-serif;max-width:720px;margin:auto;'
        'line-height:1.5;color:#222">' + corps + "</body></html>"
    )


def sauvegarder(racine, date, digest_md, lecon, idees):
    racine = Path(racine)
    (racine / "digests").mkdir(exist_ok=True)
    (racine / "lecons").mkdir(exist_ok=True)
    (racine / "digests" / f"{date}.md").write_text(digest_md, encoding="utf-8")

    if idees:
        with open(racine / "idees.md", "a", encoding="utf-8") as f:
            f.write(f"\n## Semaine du {date}\n\n")
            for idee in idees:
                source = f" ([source]({idee['source']}))" if idee.get("source") else ""
                f.write(f"- [ ] **{idee['titre']}** (effort : {idee.get('effort', '?')}) — "
                        f"{idee['description']}{source}\n")
    if not lecon.get("lecon"):
        return None

    titre = lecon["lecon"]["titre"]
    chemin_lecon = racine / "lecons" / f"{date}-{slug(titre)}.md"
    chemin_lecon.write_text(f"# {titre}\n\n*Leçon du {date}*\n\n{lecon['lecon']['markdown']}\n", encoding="utf-8")
    return chemin_lecon
