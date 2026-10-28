"""Génère le site web statique de la veille : python -m veille.site [dossier_de_sortie]"""
import html
import json
import re
import shutil
import sys
from pathlib import Path

import markdown

from .rendu import TITRES

RACINE = Path(__file__).resolve().parent.parent
NAV = [("index.html", "Cette semaine"), ("archives.html", "Archives"), ("lecons.html", "Leçons"),
       ("idees.html", "Idées"), ("prix.html", "Prix")]
MOIS = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre",
        "novembre", "décembre"]

CSS = """
:root{--fond:#fff;--surface:#fafafa;--texte:#111113;--doux:#6b6b73;--leger:#9a9aa2;--bord:#e7e7ea;
--accent:#1f4fd1;--ok:#0f7a4a}
@media (prefers-color-scheme:dark){:root{--fond:#0e0e10;--surface:#161619;--texte:#ededf0;--doux:#a0a0a8;
--leger:#6f6f78;--bord:#26262b;--accent:#7aa2ff;--ok:#4cc38a}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%}
body{margin:0;background:var(--fond);color:var(--texte);
font:15px/1.6 "Inter",system-ui,-apple-system,"Segoe UI",sans-serif;font-feature-settings:"cv11","ss01"}
a{color:inherit;text-decoration:none}
a:hover{color:var(--accent)}
header{border-bottom:1px solid var(--bord);background:var(--fond)}
.barre{max-width:1120px;margin:auto;padding:0 24px;display:flex;align-items:center;gap:40px;height:56px}
.logo{font-weight:600;letter-spacing:-.01em}
nav{display:flex;gap:28px;height:100%;overflow-x:auto}
nav a{display:flex;align-items:center;color:var(--doux);font-size:14px;border-bottom:2px solid transparent;
white-space:nowrap}
nav a.actif{color:var(--texte);border-bottom-color:var(--texte)}
main{max-width:1120px;margin:auto;padding:48px 24px 80px}
.surtitre{font-size:12px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--leger);margin:0 0 8px}
h1{font-size:32px;line-height:1.2;letter-spacing:-.02em;font-weight:600;margin:0 0 8px}
h2{font-size:13px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--doux);
margin:0 0 4px;padding-bottom:10px;border-bottom:1px solid var(--texte);display:flex;justify-content:space-between}
h2 small{font-weight:500;color:var(--leger)}
.sous{color:var(--doux);margin:0}
.entete{margin-bottom:40px}
.synthese{border-left:2px solid var(--texte);padding:2px 0 2px 18px;margin:28px 0 0;max-width:760px;font-size:16px}
.mise-en-page{display:grid;grid-template-columns:minmax(0,1fr) 280px;gap:64px}
@media (max-width:900px){.mise-en-page{grid-template-columns:1fr;gap:48px}}
.filtres{display:flex;gap:6px;flex-wrap:wrap;margin:0 0 36px}
.filtre{font:inherit;font-size:13px;color:var(--doux);background:none;border:1px solid var(--bord);
border-radius:6px;padding:5px 11px;cursor:pointer}
.filtre:hover{color:var(--texte);border-color:var(--leger)}
.filtre.actif{color:var(--fond);background:var(--texte);border-color:var(--texte)}
.filtre span{color:var(--leger);margin-left:4px}.filtre.actif span{color:inherit;opacity:.6}
section{margin-bottom:48px}
.item{padding:20px 0;border-bottom:1px solid var(--bord)}
.item h3{font-size:17px;line-height:1.4;font-weight:600;letter-spacing:-.01em;margin:0 0 4px}
.meta{font-size:13px;color:var(--leger)}
.item p{margin:8px 0 0;color:var(--texte)}
.item ul{margin:10px 0 0;padding-left:18px;color:var(--doux);font-size:14px}
.item li{margin:2px 0}
.pertinence{font-size:14px;color:var(--doux)}
.pertinence b{font-weight:600;color:var(--texte)}
aside section{margin-bottom:40px}
aside h2{margin-bottom:0}
.bloc{list-style:none;padding:0;margin:0}
.bloc li{padding:14px 0;border-bottom:1px solid var(--bord);font-size:14px}
.bloc li b{display:block;font-weight:600;margin-bottom:2px}
.bloc .meta{margin-top:4px}
.lien{color:var(--accent);font-size:14px}
.lien:hover{text-decoration:underline}
.prose{max-width:760px}
.prose h1{margin-bottom:24px}
.prose h2{margin-top:40px;margin-bottom:16px}
.prose a{color:var(--accent)}
.prose a:hover{text-decoration:underline}
.prose pre{background:var(--surface);border:1px solid var(--bord);border-radius:6px;padding:14px;overflow-x:auto;
font-size:13px}
.prose code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.9em}
.prose ul{padding-left:20px}
.idees ul{list-style:none;padding:0}
.idees li{position:relative;padding:10px 0 10px 28px;border-bottom:1px solid var(--bord)}
.case{position:absolute;left:0;top:15px;width:15px;height:15px;border:1.5px solid var(--leger);border-radius:3px}
.case.coche{background:var(--texte);border-color:var(--texte);
box-shadow:inset 0 0 0 2.5px var(--fond)}
.outils{display:flex;gap:16px;flex-wrap:wrap;align-items:end;margin:32px 0 24px}
label{font-size:12px;font-weight:500;color:var(--doux);display:flex;flex-direction:column;gap:6px}
input,select{font:inherit;font-size:14px;padding:8px 10px;border:1px solid var(--bord);border-radius:6px;
background:var(--fond);color:var(--texte);min-width:180px;height:38px}
input:focus,select:focus{outline:none;border-color:var(--texte)}
input[type=search]{width:100%;max-width:560px}
.tableau{overflow-x:auto;border-top:1px solid var(--texte)}
table{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}
th,td{padding:12px 14px;border-bottom:1px solid var(--bord);text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left;padding-left:0}
th{font-size:12px;font-weight:600;letter-spacing:.04em;text-transform:uppercase;color:var(--doux);
cursor:pointer;user-select:none}
th:hover{color:var(--texte)}
tbody tr:hover{background:var(--surface)}
.tag{display:none;margin-left:8px;font-size:11px;font-weight:600;color:var(--ok);letter-spacing:.02em}
tr.moins-cher .tag{display:inline}
tr.moins-cher td:last-child{color:var(--ok);font-weight:600}
.note{font-size:13px;color:var(--leger);margin-top:16px}
.vide{color:var(--leger)}
footer{border-top:1px solid var(--bord)}
footer p{max-width:1120px;margin:auto;padding:20px 24px;font-size:12px;color:var(--leger)}
.logo{white-space:nowrap}
@media (max-width:600px){main{padding:32px 16px 64px}h1{font-size:26px}
.barre{padding:12px 16px 0;height:auto;flex-wrap:wrap;gap:0}.logo{width:100%}nav{gap:20px;height:44px}}
"""

JS_FILTRE = """
document.querySelectorAll('.filtre').forEach(f=>f.onclick=()=>{
  document.querySelectorAll('.filtre').forEach(x=>x.classList.toggle('actif',x===f));
  document.querySelectorAll('section[data-cat]').forEach(s=>
    s.hidden=f.dataset.cat!=='tout'&&s.dataset.cat!==f.dataset.cat);
});
"""

JS_RECHERCHE = """
const champ=document.getElementById('recherche'),res=document.getElementById('resultats');
const echap=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
champ.oninput=()=>{
  const q=champ.value.trim().toLowerCase();
  if(q.length<2){res.innerHTML='';return;}
  const t=ELEMENTS.filter(e=>(e.titre+' '+e.resume+' '+e.source).toLowerCase().includes(q)).slice(0,50);
  res.innerHTML=t.length?t.map(e=>`<li><a href="${echap(e.url)}" target="_blank" rel="noopener"><b>${echap(e.titre)}</b></a>
    <div class="meta">${echap(e.cat)} · ${echap(e.source)} · ${e.date}</div></li>`).join('')
    :'<li class="vide">Aucun résultat.</li>';
};
"""

JS_PRIX = """
const corps=document.querySelector('#prix tbody'),lignes=[...corps.rows];
const fin=document.getElementById('tok-in'),fout=document.getElementById('tok-out'),ff=document.getElementById('fourn');
function maj(){
  const a=+fin.value||0,b=+fout.value||0;let min=Infinity;
  lignes.forEach(l=>{const c=a*l.dataset.entree+b*l.dataset.sortie;l.dataset.cout=c;
    l.cells[l.cells.length-1].textContent=c.toLocaleString('fr-FR',{style:'currency',currency:'USD'});
    l.hidden=ff.value&&l.dataset.fourn!==ff.value;if(!l.hidden)min=Math.min(min,c);});
  lignes.forEach(l=>l.classList.toggle('moins-cher',!l.hidden&&+l.dataset.cout===min));
}
document.querySelectorAll('#prix th').forEach((th,i)=>{let asc=true;th.onclick=()=>{
  const cle=th.dataset.tri;
  lignes.sort((x,y)=>{const u=cle?+x.dataset[cle]:x.cells[i].textContent,v=cle?+y.dataset[cle]:y.cells[i].textContent;
    return (u>v?1:u<v?-1:0)*(asc?1:-1);});
  asc=!asc;lignes.forEach(l=>corps.appendChild(l));};});
[fin,fout,ff].forEach(e=>e.oninput=maj);maj();
"""


def e(texte):
    return html.escape(str(texte or ""))


def date_fr(iso):
    try:
        a, m, j = (int(x) for x in iso[:10].split("-"))
        return f"{j} {MOIS[m - 1]} {a}"
    except (ValueError, IndexError):
        return iso


def md_html(texte):
    texte = re.sub(r"^(\s*)- \[ \] ", r'\1- <span class="case"></span> ', texte or "", flags=re.M)
    texte = re.sub(r"^(\s*)- \[[xX]\] ", r'\1- <span class="case coche"></span> ', texte, flags=re.M)
    return markdown.markdown(texte, extensions=["fenced_code", "tables"])


def page(titre, contenu, actif="", prefixe="", script=""):
    liens = "".join(
        f'<a href="{prefixe}{href}" class="{"actif" if href == actif else ""}">{nom}</a>' for href, nom in NAV)
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titre)} · Veille IA</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefixe}style.css"></head>
<body><header><div class="barre"><a class="logo" href="{prefixe}index.html">Veille IA</a>
<nav>{liens}</nav></div></header>
<main>{contenu}</main>
<footer><p>Résumés générés automatiquement à partir des sources citées. À vérifier avant diffusion.</p></footer>
{f"<script>{script}</script>" if script else ""}</body></html>"""


def article(item):
    points = "".join(f"<li>{e(p)}</li>" for p in item.get("specificites", []))
    pertinence = f'<p class="pertinence"><b>Pertinence.</b> {e(item["pourquoi"])}</p>' if item.get("pourquoi") else ""
    return f"""<article class="item">
<h3><a href="{e(item['url'])}" target="_blank" rel="noopener">{e(item['titre'])}</a></h3>
<div class="meta">{e(item.get('source'))}</div>
<p>{e(item.get('resume'))}</p>{f"<ul>{points}</ul>" if points else ""}{pertinence}</article>"""


def contenu_semaine(s, prefixe=""):
    par_cat = {c: [i for i in s["selection"] if i.get("categorie") == c] for c in TITRES}
    par_cat = {c: items for c, items in par_cat.items() if items}
    filtres = f'<button class="filtre actif" data-cat="tout">Tout<span>{len(s["selection"])}</span></button>' + "".join(
        f'<button class="filtre" data-cat="{c}">{TITRES[c]}<span>{len(items)}</span></button>'
        for c, items in par_cat.items())
    sections = "".join(
        f'<section data-cat="{c}"><h2>{TITRES[c]}<small>{len(items)}</small></h2>'
        + "".join(article(i) for i in items) + "</section>"
        for c, items in par_cat.items())

    cote = ""
    lecon = s.get("lecon") or {}
    if lecon.get("fichier"):
        cote += (f'<section><h2>Leçon de la semaine</h2><ul class="bloc"><li>'
                 f'<a href="{prefixe}lecon/{Path(lecon["fichier"]).stem}.html"><b>{e(lecon.get("titre"))}</b></a>'
                 f'<span class="lien">Lire la leçon →</span></li></ul></section>')
    if s.get("idees"):
        cote += '<section><h2>Idées à proposer</h2><ul class="bloc">' + "".join(
            f'<li><b>{e(i["titre"])}</b>{e(i["description"])}<div class="meta">Effort {e(i.get("effort"))}</div></li>'
            for i in s["idees"]) + "</ul></section>"
    if s.get("comparatif"):
        cote += (f'<section><h2>Prix et qualité</h2><div class="prose" style="font-size:14px">'
                 f'{md_html(s["comparatif"])}</div><a class="lien" href="{prefixe}prix.html">'
                 f'Tableau complet et simulateur →</a></section>')

    nb_cat = len(par_cat)
    return f"""<div class="entete"><p class="surtitre">Semaine du {date_fr(s['date'])}</p>
<h1>Veille hebdomadaire</h1>
<p class="sous">{len(s['selection'])} contenus · {nb_cat} thème{"s" if nb_cat > 1 else ""}</p>
{f'<p class="synthese">{e(s["tendance"])}</p>' if s.get("tendance") else ""}</div>
<div class="mise-en-page"><div><div class="filtres">{filtres}</div>{sections}</div>
<aside>{cote}</aside></div>"""


def page_prix(modeles):
    entete = ('<div class="entete"><p class="surtitre">Comparatif</p><h1>Prix des modèles</h1>'
              '<p class="sous">Tarifs OpenRouter en dollars par million de tokens. Cliquez sur une colonne pour trier.'
              '</p></div>')
    if not modeles:
        return entete + '<p class="vide">Les prix apparaîtront après la première veille.</p>'
    qualite = any(m.get("qualite") is not None for m in modeles)
    fourns = sorted({m["fournisseur"] for m in modeles})
    options = "".join(f'<option value="{e(f)}">{e(f)}</option>' for f in fourns)
    lignes = ""
    for m in modeles:
        q = f"<td>{e(m.get('qualite', '–'))}</td><td>{round(m['vitesse']) if m.get('vitesse') else '–'}</td>" \
            if qualite else ""
        lignes += (f'<tr data-fourn="{e(m["fournisseur"])}" data-entree="{m["entree"]}" data-sortie="{m["sortie"]}"'
                   f' data-contexte="{m["contexte"]}" data-qualite="{m.get("qualite") or 0}">'
                   f'<td>{e(m["nom"])}<span class="tag">Le moins cher</span></td><td>{m["entree"]}</td>'
                   f'<td>{m["sortie"]}</td><td>{m["contexte"] // 1000}k</td>{q}'
                   f'<td class="meta">{e(m.get("evolution"))}</td><td></td></tr>')
    entete_q = '<th data-tri="qualite">Qualité AA</th><th>Tok/s</th>' if qualite else ""
    return f"""{entete}
<div class="outils">
<label>Tokens d'entrée par mois (millions)<input id="tok-in" type="number" min="0" step="0.1" value="10"></label>
<label>Tokens de sortie par mois (millions)<input id="tok-out" type="number" min="0" step="0.1" value="2"></label>
<label>Fournisseur<select id="fourn"><option value="">Tous</option>{options}</select></label></div>
<div class="tableau"><table id="prix"><thead><tr><th>Modèle</th><th data-tri="entree">Entrée</th>
<th data-tri="sortie">Sortie</th><th data-tri="contexte">Contexte</th>{entete_q}<th>Évolution</th>
<th data-tri="cout">Coût mensuel</th></tr></thead><tbody>{lignes}</tbody></table></div>
<p class="note">Coût estimé pour le volume indiqué. Vérifiez les tarifs officiels avant toute décision budgétaire.</p>"""


def construire(racine=RACINE, sortie=None):
    racine = Path(racine)
    sortie = Path(sortie or racine / "_site")
    if sortie.exists():
        shutil.rmtree(sortie)
    (sortie / "semaine").mkdir(parents=True)
    (sortie / "lecon").mkdir()
    (sortie / "style.css").write_text(CSS, encoding="utf-8")

    semaines = [json.loads(f.read_text(encoding="utf-8"))
                for f in sorted((racine / "data" / "semaines").glob("*.json"), reverse=True)]

    # Accueil : la dernière veille.
    if semaines:
        accueil = contenu_semaine(semaines[0])
    else:
        accueil = ('<div class="entete"><h1>Veille hebdomadaire</h1><p class="sous">La première veille apparaîtra '
                   'ici après la prochaine exécution (chaque lundi, ou via Actions → Run workflow).</p></div>')
    (sortie / "index.html").write_text(page("Cette semaine", accueil, "index.html", script=JS_FILTRE), "utf-8")

    # Archives + recherche dans toutes les semaines.
    elements, liste = [], ""
    for s in semaines:
        (sortie / "semaine" / f"{s['date']}.html").write_text(
            page(f"Semaine du {date_fr(s['date'])}", contenu_semaine(s, "../"), "archives.html", "../", JS_FILTRE),
            "utf-8")
        liste += (f'<li><a href="semaine/{s["date"]}.html"><b>Semaine du {date_fr(s["date"])}</b></a>'
                  f'{e(s.get("tendance", ""))[:200]}<div class="meta">{len(s["selection"])} contenus</div></li>')
        elements += [{"titre": i["titre"], "url": i["url"], "source": i.get("source", ""),
                      "resume": i.get("resume", ""), "cat": TITRES.get(i.get("categorie"), ""),
                      "date": date_fr(s["date"])}
                     for i in s["selection"]]
    donnees = json.dumps(elements, ensure_ascii=False).replace("</", "<\\/")
    archives = f"""<div class="entete"><p class="surtitre">Archives</p><h1>Toutes les veilles</h1>
<p class="sous">Recherche dans l'ensemble des contenus publiés.</p></div>
<input id="recherche" type="search" placeholder="Rechercher : Claude, NVIDIA, OCR, humanoïde…">
<ul id="resultats" class="bloc" style="margin:8px 0 48px"></ul>
<section><h2>Semaines<small>{len(semaines)}</small></h2>
<ul class="bloc">{liste or '<li class="vide">Aucune veille pour le moment.</li>'}</ul></section>"""
    (sortie / "archives.html").write_text(
        page("Archives", archives, "archives.html", script=f"const ELEMENTS={donnees};{JS_RECHERCHE}"), "utf-8")

    # Leçons : une page par fichier de lecons/.
    liste, nb = "", 0
    for f in sorted((racine / "lecons").glob("*.md"), reverse=True):
        texte = f.read_text(encoding="utf-8")
        titre = texte.splitlines()[0].lstrip("# ").strip() if texte else f.stem
        (sortie / "lecon" / f"{f.stem}.html").write_text(
            page(titre, f'<div class="prose">{md_html(texte)}</div>', "lecons.html", "../"), "utf-8")
        liste += f'<li><a href="lecon/{f.stem}.html"><b>{e(titre)}</b></a><div class="meta">{date_fr(f.stem)}</div></li>'
        nb += 1
    (sortie / "lecons.html").write_text(page("Leçons", f"""<div class="entete"><p class="surtitre">Formation</p>
<h1>Leçons</h1><p class="sous">Une leçon par semaine, tirée de la veille.</p></div>
<section><h2>Toutes les leçons<small>{nb}</small></h2>
<ul class="bloc">{liste or '<li class="vide">Aucune leçon pour le moment.</li>'}</ul></section>""", "lecons.html"), "utf-8")

    # Idées : le backlog idees.md, sans son titre (la page a le sien).
    fichier_idees = racine / "idees.md"
    idees = fichier_idees.read_text(encoding="utf-8") if fichier_idees.exists() else ""
    idees = re.sub(r"\A# .*\n+(?:[^#\n].*\n+)?", "", idees)
    (sortie / "idees.html").write_text(page("Idées", f"""<div class="entete"><p class="surtitre">Backlog</p>
<h1>Idées à proposer</h1><p class="sous">Pour marquer une idée comme présentée, remplacez <code>[ ]</code> par
<code>[x]</code> dans <code>idees.md</code> : le site se met à jour automatiquement.</p></div>
<div class="prose idees">{md_html(idees) or '<p class="vide">Aucune idée pour le moment.</p>'}</div>""",
        "idees.html"), "utf-8")

    # Prix : la dernière photo des prix.
    fichier_prix = racine / "data" / "prix.json"
    modeles = json.loads(fichier_prix.read_text(encoding="utf-8")) if fichier_prix.exists() else []
    (sortie / "prix.html").write_text(
        page("Prix", page_prix(modeles), "prix.html", script=JS_PRIX if modeles else ""), "utf-8")
    return sortie


if __name__ == "__main__":
    print(f"Site généré dans {construire(sortie=sys.argv[1] if len(sys.argv) > 1 else None)}")
