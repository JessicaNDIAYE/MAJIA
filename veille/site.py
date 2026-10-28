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
ICONES = {cat: titre.split(" ")[0] for cat, titre in TITRES.items()}
NOMS = {cat: titre.split(" ", 1)[1].split(" (")[0] for cat, titre in TITRES.items()}
NAV = [("index.html", "Cette semaine"), ("archives.html", "Archives"), ("lecons.html", "Leçons"),
       ("idees.html", "Idées"), ("prix.html", "Prix")]

CSS = """
:root{--fond:#fbf7ff;--carte:#fff;--texte:#2d2640;--doux:#7a7191;--bord:#efe6fb;--accent:#a855f7;
--accent2:#ec4899;--accent-doux:#f5ecff;--ok:#16a36a;--ombre:0 6px 20px rgba(168,85,247,.10)}
@media (prefers-color-scheme:dark){:root{--fond:#17131f;--carte:#221c2e;--texte:#f1ecfa;--doux:#a99fbd;
--bord:#342a45;--accent:#c084fc;--accent2:#f472b6;--accent-doux:#2e2442;--ok:#4ade80;--ombre:none}}
*{box-sizing:border-box}
body{margin:0;background:var(--fond);color:var(--texte);font:16px/1.6 "Nunito",system-ui,sans-serif}
a{color:var(--accent)}
header{position:sticky;top:0;z-index:5;background:color-mix(in srgb,var(--carte) 88%,transparent);
backdrop-filter:blur(8px);border-bottom:1px solid var(--bord)}
.barre{max-width:1100px;margin:auto;padding:10px 16px;display:flex;gap:16px;align-items:center;flex-wrap:wrap}
.logo{font-weight:800;font-size:19px;text-decoration:none;color:var(--texte)}
.logo span{background:linear-gradient(90deg,var(--accent),var(--accent2));-webkit-background-clip:text;
background-clip:text;color:transparent}
nav{display:flex;gap:4px;flex-wrap:wrap}
nav a{padding:6px 14px;border-radius:999px;text-decoration:none;color:var(--doux);font-size:15px;font-weight:600}
nav a.actif,nav a:hover{background:var(--accent-doux);color:var(--accent)}
main{max-width:1100px;margin:auto;padding:24px 16px 64px}
.hero{background:linear-gradient(135deg,#f3e8ff,#fce7f3 60%,#e0f2fe);border-radius:24px;padding:26px 28px;
margin-bottom:8px;color:#2d2640}
@media (prefers-color-scheme:dark){.hero{background:linear-gradient(135deg,#3b2a5c,#4a2440 60%,#1e3a4f);color:#f1ecfa}}
.hero h1{margin:0 0 4px}.hero p{margin:0;opacity:.8}
h1{font-size:28px;margin:0 0 4px;font-weight:800}
h2{font-size:21px;margin:36px 0 12px;font-weight:800}
.sous{color:var(--doux);margin:0 0 20px}
.tendance{background:var(--carte);border:2px dashed var(--accent);border-radius:18px;padding:14px 18px;margin:18px 0}
.puces{display:flex;gap:8px;flex-wrap:wrap;margin:20px 0}
.puce{border:1px solid var(--bord);background:var(--carte);color:var(--texte);border-radius:999px;
padding:7px 15px;font:600 14px "Nunito",system-ui,sans-serif;cursor:pointer;transition:transform .15s}
.puce:hover{transform:translateY(-2px)}
.puce.actif{background:linear-gradient(90deg,var(--accent),var(--accent2));border-color:transparent;color:#fff}
.grille{display:grid;grid-template-columns:repeat(auto-fill,minmax(310px,1fr));gap:18px}
.carte{background:var(--carte);border:1px solid var(--bord);border-radius:20px;padding:18px 20px;
box-shadow:var(--ombre);transition:transform .15s,box-shadow .15s;border-top:5px solid var(--c,var(--accent))}
.carte:hover{transform:translateY(-3px);box-shadow:0 10px 28px rgba(168,85,247,.18)}
.carte h3{font-size:17px;margin:8px 0 4px;line-height:1.35}
.carte h3 a{color:var(--texte);text-decoration:none}
.carte h3 a:hover{color:var(--accent)}
.meta{font-size:13px;color:var(--doux)}
.carte ul{padding-left:18px;margin:8px 0}
.carte li{font-size:14px}.carte li::marker{content:"✦ ";color:var(--c,var(--accent))}
.pourquoi{font-size:14px;background:var(--accent-doux);border-radius:12px;padding:8px 12px;margin:10px 0 0}
.badge{display:inline-block;font-size:12px;font-weight:700;background:var(--cb,var(--accent-doux));
color:var(--c,var(--accent));border-radius:999px;padding:3px 10px}
[data-cat=modele]{--c:#8b5cf6;--cb:#ede9fe}[data-cat=article]{--c:#0ea5e9;--cb:#e0f2fe}
[data-cat=robotique]{--c:#f97316;--cb:#ffedd5}[data-cat=parsing]{--c:#14b8a6;--cb:#ccfbf1}
[data-cat=monitoring]{--c:#ef4444;--cb:#fee2e2}[data-cat=pratique]{--c:#22c55e;--cb:#dcfce7}
[data-cat=comparatif]{--c:#eab308;--cb:#fef9c3}
@media (prefers-color-scheme:dark){[data-cat]{--cb:color-mix(in srgb,var(--c) 22%,transparent)}}
.liste{list-style:none;padding:0;margin:0}
.liste li{background:var(--carte);border:1px solid var(--bord);border-radius:16px;padding:12px 16px;
margin-bottom:10px;box-shadow:var(--ombre)}
.prose{background:var(--carte);border:1px solid var(--bord);border-radius:20px;padding:8px 26px 20px;
overflow-x:auto;box-shadow:var(--ombre)}
.prose pre{background:var(--fond);padding:12px;border-radius:12px;overflow-x:auto}
.idees li{list-style:none;margin-left:-20px}
.outils{display:flex;gap:12px;flex-wrap:wrap;align-items:end;margin:16px 0}
.outils label{font-size:13px;font-weight:700;color:var(--doux);display:flex;flex-direction:column;gap:4px}
input,select{font:inherit;padding:9px 14px;border:2px solid var(--bord);border-radius:14px;
background:var(--carte);color:var(--texte);outline:none}
input:focus,select:focus{border-color:var(--accent)}
input[type=search]{width:100%;max-width:560px}
.tableau{margin-bottom:14px;overflow-x:auto;background:var(--carte);border:1px solid var(--bord);border-radius:20px;box-shadow:var(--ombre)}
table{border-collapse:collapse;width:100%;font-size:14px}
th,td{padding:11px 14px;border-bottom:1px solid var(--bord);text-align:right;white-space:nowrap}
th:first-child,td:first-child{text-align:left}
th{cursor:pointer;user-select:none;color:var(--doux);font-weight:800}
th:hover{color:var(--accent)}
tr.moins-cher td{color:var(--ok);font-weight:800}tr.moins-cher td:first-child::before{content:"🏆 "}
.vide{color:var(--doux);font-style:italic}
footer{text-align:center;color:var(--doux);font-size:13px;padding:0 16px 32px}
"""

JS_FILTRE = """
document.querySelectorAll('.puce').forEach(p=>p.onclick=()=>{
  document.querySelectorAll('.puce').forEach(x=>x.classList.toggle('actif',x===p));
  document.querySelectorAll('.carte[data-cat]').forEach(c=>
    c.hidden=p.dataset.cat!=='tout'&&c.dataset.cat!==p.dataset.cat);
});
"""

JS_RECHERCHE = """
const champ=document.getElementById('recherche'),res=document.getElementById('resultats');
const echap=s=>s.replace(/[&<>"]/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]));
champ.oninput=()=>{
  const q=champ.value.trim().toLowerCase();
  if(q.length<2){res.innerHTML='';return;}
  const t=ELEMENTS.filter(e=>(e.titre+' '+e.resume+' '+e.source).toLowerCase().includes(q)).slice(0,50);
  res.innerHTML=t.length?t.map(e=>`<li data-cat="${echap(e.c)}"><span class="badge">${echap(e.cat)}</span>
    <a href="${echap(e.url)}" target="_blank" rel="noopener">${echap(e.titre)}</a>
    <div class="meta">${echap(e.source)} · ${e.date}</div></li>`).join(''):'<li class="vide">Aucun résultat.</li>';
};
"""

JS_PRIX = """
const corps=document.querySelector('#prix tbody'),lignes=[...corps.rows];
const fin=document.getElementById('tok-in'),fout=document.getElementById('tok-out'),ff=document.getElementById('fourn');
function maj(){
  const a=+fin.value||0,b=+fout.value||0;let min=Infinity;
  lignes.forEach(l=>{const c=a*l.dataset.entree+b*l.dataset.sortie;l.dataset.cout=c;
    l.cells[l.cells.length-1].textContent=c.toFixed(2)+' $';
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


def md_html(texte):
    texte = re.sub(r"^(\s*)- \[ \] ", r"\1- ☐ ", texte or "", flags=re.M)
    texte = re.sub(r"^(\s*)- \[[xX]\] ", r"\1- ✅ ", texte, flags=re.M)
    return markdown.markdown(texte, extensions=["fenced_code", "tables"])


def page(titre, contenu, actif="", prefixe="", script=""):
    liens = "".join(
        f'<a href="{prefixe}{href}" class="{"actif" if href == actif else ""}">{nom}</a>' for href, nom in NAV)
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titre)} · Veille IA</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Nunito:wght@400;600;700;800&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefixe}style.css"></head>
<body><header><div class="barre"><a class="logo" href="{prefixe}index.html">🧠 <span>Veille IA</span> ✨</a>
<nav>{liens}</nav></div></header>
<main>{contenu}</main>
<footer>Fait avec 💜 · résumés générés par IA, vérifie la source avant de citer</footer>{f"<script>{script}</script>" if script else ""}</body></html>"""


def carte(item):
    points = "".join(f"<li>{e(p)}</li>" for p in item.get("specificites", []))
    cat = item.get("categorie", "")
    return f"""<article class="carte" data-cat="{e(cat)}">
<span class="badge">{ICONES.get(cat, "")} {e(NOMS.get(cat, cat))}</span>
<h3><a href="{e(item['url'])}" target="_blank" rel="noopener">{e(item['titre'])}</a></h3>
<div class="meta">{e(item.get('source'))}</div>
<p>{e(item.get('resume'))}</p>{f"<ul>{points}</ul>" if points else ""}
<p class="pourquoi">👉 {e(item.get('pourquoi'))}</p></article>"""


def contenu_semaine(s, prefixe=""):
    cats = [c for c in TITRES if any(i.get("categorie") == c for i in s["selection"])]
    puces = '<button class="puce actif" data-cat="tout">Tout</button>' + "".join(
        f'<button class="puce" data-cat="{c}">{ICONES[c]} {NOMS[c]}</button>' for c in cats)
    ordre = {c: i for i, c in enumerate(TITRES)}
    cartes = "".join(carte(i) for i in sorted(s["selection"], key=lambda i: ordre.get(i.get("categorie"), 99)))
    idees = "".join(f"<li><strong>{e(i['titre'])}</strong> <span class='badge'>effort : {e(i.get('effort'))}</span>"
                    f"<div>{e(i['description'])}</div></li>" for i in s.get("idees", []))
    lecon = s.get("lecon") or {}
    lien_lecon = f'{prefixe}lecon/{Path(lecon.get("fichier", "")).stem}.html' if lecon.get("fichier") else ""
    return f"""<div class="hero"><h1>☀️ Semaine du {e(s['date'])}</h1>
<p>{len(s['selection'])} contenus choisis pour toi · {len(s.get('idees', []))} idées · 1 leçon</p></div>
{f'<div class="tendance"><strong>🔮 Tendance :</strong> {e(s["tendance"])}</div>' if s.get("tendance") else ""}
<div class="puces">{puces}</div><div class="grille">{cartes}</div>
{f'<h2>💰 Comparatif prix / qualité</h2><div class="prose">{md_html(s["comparatif"])}'
 f'<p><a href="{prefixe}prix.html">Voir le tableau complet et simuler ton coût →</a></p></div>'
 if s.get("comparatif") else ""}
{f"<h2>💡 Idées à proposer à ton équipe</h2><ul class='liste'>{idees}</ul>" if idees else ""}
{f'<h2>🎓 Leçon de la semaine</h2><ul class="liste"><li><a href="{lien_lecon}">{e(lecon.get("titre"))}</a></li></ul>'
 if lien_lecon else ""}"""


def page_prix(modeles):
    if not modeles:
        return '<h1>💰 Comparatif des prix</h1><p class="vide">Les prix apparaîtront après la première veille.</p>'
    qualite = any(m.get("qualite") is not None for m in modeles)
    fourns = sorted({m["fournisseur"] for m in modeles})
    options = "".join(f'<option value="{e(f)}">{e(f)}</option>' for f in fourns)
    lignes = ""
    for m in modeles:
        q = f"<td>{e(m.get('qualite', '–'))}</td><td>{round(m['vitesse']) if m.get('vitesse') else '–'}</td>" \
            if qualite else ""
        lignes += (f'<tr data-fourn="{e(m["fournisseur"])}" data-entree="{m["entree"]}" data-sortie="{m["sortie"]}"'
                   f' data-contexte="{m["contexte"]}" data-qualite="{m.get("qualite") or 0}">'
                   f'<td>{e(m["nom"])}</td><td>{m["entree"]}</td><td>{m["sortie"]}</td>'
                   f'<td>{m["contexte"] // 1000}k</td>{q}<td>{e(m.get("evolution"))}</td><td></td></tr>')
    entete_q = '<th data-tri="qualite">Qualité (AA)</th><th>Vitesse tok/s</th>' if qualite else ""
    return f"""<h1>💰 Comparatif des prix</h1>
<p class="sous">Prix réels OpenRouter en $ par million de tokens. Clique sur une colonne pour trier.</p>
<div class="outils">
<label>Tokens d'entrée / mois (millions)<input id="tok-in" type="number" min="0" step="0.1" value="10"></label>
<label>Tokens de sortie / mois (millions)<input id="tok-out" type="number" min="0" step="0.1" value="2"></label>
<label>Fournisseur<select id="fourn"><option value="">Tous</option>{options}</select></label></div>
<div class="tableau"><table id="prix"><thead><tr><th>Modèle</th><th data-tri="entree">Entrée $/M</th>
<th data-tri="sortie">Sortie $/M</th><th data-tri="contexte">Contexte</th>{entete_q}<th>Évolution</th>
<th data-tri="cout">Coût / mois</th></tr></thead><tbody>{lignes}</tbody></table></div>
<p class="sous">🏆 = le modèle le moins cher pour ton volume. Vérifie les tarifs officiels
avant une décision budgétaire.</p>"""


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
        accueil = ('<div class="hero"><h1>Bienvenue 👋</h1><p>Ta première veille apparaîtra ici après la prochaine '
                   'exécution (chaque lundi, ou via Actions → Run workflow).</p></div>')
    (sortie / "index.html").write_text(page("Cette semaine", accueil, "index.html", script=JS_FILTRE), "utf-8")

    # Archives + recherche dans toutes les semaines.
    elements, liste = [], ""
    for s in semaines:
        (sortie / "semaine" / f"{s['date']}.html").write_text(
            page(f"Semaine du {s['date']}", contenu_semaine(s, "../"), "archives.html", "../", JS_FILTRE), "utf-8")
        liste += (f'<li><a href="semaine/{s["date"]}.html">Semaine du {e(s["date"])}</a>'
                  f'<div class="meta">{len(s["selection"])} contenus · {e(s.get("tendance", ""))[:160]}</div></li>')
        elements += [{"titre": i["titre"], "url": i["url"], "source": i.get("source", ""),
                      "resume": i.get("resume", ""), "cat": NOMS.get(i.get("categorie"), ""), "c": i.get("categorie", ""),
                      "date": s["date"]}
                     for i in s["selection"]]
    donnees = json.dumps(elements, ensure_ascii=False).replace("</", "<\\/")
    archives = f"""<h1>🗂️ Archives</h1><p class="sous">Cherche dans toutes tes veilles passées.</p>
<input id="recherche" type="search" placeholder="🔎 Claude, NVIDIA, OCR, humanoïde…">
<ul id="resultats" class="liste" style="margin-top:12px"></ul>
<h2>Toutes les semaines</h2><ul class="liste">{liste or '<li class="vide">Aucune veille pour le moment.</li>'}</ul>"""
    (sortie / "archives.html").write_text(
        page("Archives", archives, "archives.html", script=f"const ELEMENTS={donnees};{JS_RECHERCHE}"), "utf-8")

    # Leçons : une page par fichier de lecons/.
    liste = ""
    for f in sorted((racine / "lecons").glob("*.md"), reverse=True):
        texte = f.read_text(encoding="utf-8")
        titre = texte.splitlines()[0].lstrip("# ").strip() if texte else f.stem
        (sortie / "lecon" / f"{f.stem}.html").write_text(
            page(titre, f'<div class="prose">{md_html(texte)}</div>', "lecons.html", "../"), "utf-8")
        liste += f'<li><a href="lecon/{f.stem}.html">{e(titre)}</a><div class="meta">{f.stem[:10]}</div></li>'
    (sortie / "lecons.html").write_text(page("Leçons", f"""<h1>🎓 Leçons</h1>
<p class="sous">Ta base de cours, une leçon par semaine.</p>
<ul class="liste">{liste or '<li class="vide">Aucune leçon pour le moment.</li>'}</ul>""", "lecons.html"), "utf-8")

    # Idées : le backlog idees.md (☐ à présenter, ✅ présentée).
    fichier_idees = racine / "idees.md"
    idees = fichier_idees.read_text(encoding="utf-8") if fichier_idees.exists() else ""
    (sortie / "idees.html").write_text(page("Idées", '<h1>💡 Idées</h1><p class="sous">Ton backlog de propositions : ☐ à présenter, ✅ présentée.</p>'
        f'<div class="prose idees">{md_html(idees)}</div>'
        '<p class="sous">Pour cocher une idée, remplace <code>[ ]</code> par <code>[x]</code> dans '
        '<code>idees.md</code> sur GitHub : le site se met à jour tout seul.</p>', "idees.html"), "utf-8")

    # Prix : la dernière photo des prix.
    fichier_prix = racine / "data" / "prix.json"
    modeles = json.loads(fichier_prix.read_text(encoding="utf-8")) if fichier_prix.exists() else []
    (sortie / "prix.html").write_text(
        page("Prix", page_prix(modeles), "prix.html", script=JS_PRIX if modeles else ""), "utf-8")
    return sortie


if __name__ == "__main__":
    print(f"Site généré dans {construire(sortie=sys.argv[1] if len(sys.argv) > 1 else None)}")
