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
:root{--fond:#fff;--gris:#f0f0ed;--gris2:#e4e5e0;--forme:#d5d8cd;--olive:#7b8a5a;--olive-fonce:#5f6c43;
--texte:#2a2b27;--doux:#6d6e68;--leger:#9c9d96;--bord:#e3e3de}
@media (prefers-color-scheme:dark){:root{--fond:#141513;--gris:#1b1d19;--gris2:#232620;--forme:#30352a;
--olive:#9aab74;--olive-fonce:#b4c38f;--texte:#ecece6;--doux:#a5a69e;--leger:#7c7d76;--bord:#2c2f28}}
*{box-sizing:border-box}
html{-webkit-text-size-adjust:100%;scroll-behavior:smooth}
body{margin:0;background:var(--fond);color:var(--texte);font:15px/1.65 "Montserrat",system-ui,sans-serif}
a{color:inherit;text-decoration:none}
.conteneur{max-width:1120px;margin:auto;padding:0 24px}
header{background:var(--fond);border-bottom:1px solid var(--bord);position:sticky;top:0;z-index:10}
.barre{display:flex;align-items:center;gap:40px;height:64px}
.logo{font-weight:600;letter-spacing:-.01em;white-space:nowrap}
.logo b{color:var(--olive);font-weight:600}
nav{display:flex;gap:28px;overflow-x:auto}
nav a{font-size:13px;color:var(--doux);white-space:nowrap;padding:4px 0;border-bottom:1.5px solid transparent}
nav a:hover{color:var(--texte)}
nav a.actif{color:var(--texte);border-bottom-color:var(--olive)}
.date-entete{margin-left:auto;font-size:12px;color:var(--leger);white-space:nowrap}
.bouton{display:inline-block;background:var(--olive);color:#fff;border:0;border-radius:999px;padding:11px 26px;
font:500 13px "Montserrat",sans-serif;cursor:pointer;transition:background .15s}
.bouton:hover{background:var(--olive-fonce);color:#fff}
.bouton.clair{background:var(--fond);color:var(--texte);border:1px solid var(--bord)}
.bouton.clair:hover{border-color:var(--olive);color:var(--olive-fonce)}
.bande{position:relative;overflow:hidden;background:var(--gris)}
.bande::before{content:"";position:absolute;width:560px;height:560px;border-radius:50%;background:var(--gris2);
left:-200px;top:-300px}
.bande.droite::before{left:auto;right:-220px;top:auto;bottom:-320px}
.bande>*{position:relative}
section.bloc-page{padding:88px 0}
.titre-section{text-align:center;font-size:24px;font-weight:600;margin:0 0 48px}
.surtitre{font-size:12px;font-weight:600;letter-spacing:.12em;text-transform:uppercase;color:var(--olive);margin:0 0 12px}
/* Héros */
.heros{display:grid;grid-template-columns:1.1fr .9fr;gap:48px;align-items:center;padding-top:72px;padding-bottom:88px}
.heros h1{font-size:42px;line-height:1.18;font-weight:600;letter-spacing:-.02em;margin:0 0 18px}
.heros p{color:var(--doux);max-width:480px;margin:0 0 32px}
.formes{position:relative;height:380px}
.arche{position:absolute;right:30px;top:0;width:270px;height:360px;border-radius:135px 135px 0 0;background:var(--forme)}
.cercle{position:absolute;left:30px;bottom:0;width:200px;height:200px;border-radius:50%;background:var(--gris2);
display:flex;flex-direction:column;align-items:center;justify-content:center;text-align:center;
border:8px solid var(--fond)}
.cercle strong{font-size:44px;font-weight:600;line-height:1}
.cercle span{font-size:12px;color:var(--doux);margin-top:6px}
/* Synthèse */
.synthese{display:grid;grid-template-columns:.8fr 1.2fr;gap:48px;align-items:center;padding-top:80px;padding-bottom:80px}
.synthese h2{font-size:28px;font-weight:600;margin:0;color:var(--olive-fonce)}
.synthese p{margin:0;font-size:16px;line-height:1.75}
/* Chiffres */
.chiffres{display:grid;grid-template-columns:repeat(3,1fr);gap:40px;text-align:center}
.pastille{width:72px;height:72px;margin:0 auto 16px;border-radius:50%;border:1.5px solid var(--olive);
display:flex;align-items:center;justify-content:center;font-size:22px;font-weight:600;color:var(--olive-fonce)}
.chiffres h3{font-size:15px;font-weight:600;margin:0 0 6px}
.chiffres p{font-size:13px;color:var(--doux);margin:0 auto;max-width:260px}
/* À la une */
.cartes{display:grid;grid-template-columns:repeat(3,1fr);gap:28px}
.carte{background:var(--fond);border-radius:6px;overflow:hidden;display:flex;flex-direction:column}
.visuel{height:150px;background:var(--forme);display:flex;align-items:flex-end;padding:16px 18px;position:relative;overflow:hidden}
.visuel::after{content:"";position:absolute;width:150px;height:150px;border-radius:50%;background:var(--gris2);
right:-40px;top:-50px;opacity:.7}
.visuel span{position:relative;z-index:1;font-size:11px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;
background:var(--fond);border-radius:999px;padding:4px 12px;color:var(--olive-fonce)}
.carte-corps{padding:20px 20px 24px;display:flex;flex-direction:column;gap:8px;flex:1}
.carte h3{font-size:15px;line-height:1.45;font-weight:600;margin:0}
.meta{font-size:12px;color:var(--leger)}
.carte p{font-size:13px;color:var(--doux);margin:0;flex:1}
.carte .bouton{align-self:flex-start;margin-top:8px;padding:8px 20px}
/* Thèmes */
.raccourcis{display:flex;gap:8px;flex-wrap:wrap;justify-content:center;margin:-24px 0 56px}
.raccourcis a{font-size:12px;border:1px solid var(--bord);border-radius:999px;padding:6px 14px;color:var(--doux)}
.raccourcis a:hover{border-color:var(--olive);color:var(--olive-fonce)}
.rangee{display:grid;grid-template-columns:.9fr 1.1fr;gap:56px;align-items:start;margin-bottom:72px;scroll-margin-top:90px}
.rangee:nth-of-type(odd) .panneau{order:2}
.panneau{background:var(--gris);border-radius:6px;min-height:220px;padding:28px;position:relative;overflow:hidden;
display:flex;flex-direction:column;justify-content:flex-end}
.panneau::before{content:"";position:absolute;width:240px;height:240px;border-radius:50%;background:var(--gris2);
right:-60px;top:-80px}
.panneau strong{position:relative;font-size:48px;font-weight:600;line-height:1;color:var(--olive-fonce)}
.panneau span{position:relative;font-size:13px;color:var(--doux);margin-top:6px}
.rangee h3{font-size:22px;font-weight:600;margin:0 0 8px}
.liste{list-style:none;margin:0;padding:0}
.liste li{padding:16px 0;border-bottom:1px solid var(--bord)}
.liste li:first-child{padding-top:4px}
.liste a.titre{font-weight:600;font-size:14px}
.liste a.titre:hover,.carte h3 a:hover{color:var(--olive-fonce)}
.liste p{margin:6px 0 0;font-size:13px;color:var(--doux)}
details{margin-top:6px;font-size:13px}
summary{cursor:pointer;color:var(--olive-fonce);font-weight:500;list-style:none}
summary::-webkit-details-marker{display:none}
summary::after{content:" +"}details[open] summary::after{content:" −"}
details ul{margin:8px 0 0;padding-left:18px;color:var(--doux)}
details .pertinence{margin:8px 0 0;color:var(--texte)}
/* Bandeau prix */
.bandeau{text-align:center;padding-top:80px;padding-bottom:80px}
.bandeau h2{font-size:22px;font-weight:600;margin:0 0 8px}
.bandeau p{color:var(--doux);margin:0 0 28px}
.analyse{max-width:640px;margin:0 auto 32px;text-align:left;font-size:14px;background:var(--fond);border-radius:6px;
padding:18px 24px}
.analyse ul{margin:0;padding-left:18px}.analyse p{margin:0;color:var(--texte)}
/* Carrousel des idées */
.carrousel{display:grid;grid-template-columns:40px 1fr 40px;gap:16px;align-items:center}
.piste{display:grid;grid-auto-flow:column;grid-auto-columns:calc((100% - 48px)/3);gap:24px;overflow-x:auto;
scroll-snap-type:x mandatory;scrollbar-width:none;padding:4px}
.piste::-webkit-scrollbar{display:none}
.idee{scroll-snap-align:start;background:var(--gris);border-radius:6px;padding:28px 24px;display:flex;flex-direction:column;gap:10px}
.idee:nth-child(3n+2){background:var(--forme)}
.idee h3{font-size:15px;font-weight:600;margin:0}
.idee p{font-size:13px;margin:0;color:var(--doux);flex:1}
.idee:nth-child(3n+2) p{color:var(--texte)}
.fleche{width:40px;height:40px;border-radius:50%;border:1px solid var(--bord);background:var(--fond);color:var(--texte);
font-size:18px;cursor:pointer}
.fleche:hover{border-color:var(--olive);color:var(--olive-fonce)}
.points{display:flex;gap:8px;justify-content:center;margin-top:24px}
.points button{width:8px;height:8px;border-radius:50%;border:0;padding:0;background:var(--forme);cursor:pointer}
.points button.actif{background:var(--olive)}
/* Leçon */
.lecon{display:grid;grid-template-columns:.8fr 1.2fr;gap:56px;align-items:stretch}
.lecon h2{font-size:28px;font-weight:600;line-height:1.25;margin:0 0 16px}
.lecon dl{margin:24px 0 32px;font-size:13px}
.lecon dt{color:var(--leger);margin-top:12px}.lecon dd{margin:2px 0 0;font-weight:500}
.encart{background:var(--gris);border-radius:6px;min-height:300px;padding:40px;display:flex;align-items:center;
justify-content:center;text-align:center;position:relative;overflow:hidden}
.encart::before{content:"";position:absolute;width:300px;height:300px;border-radius:50%;background:var(--gris2);
left:-90px;bottom:-120px}
.encart p{position:relative;font-size:20px;font-weight:600;max-width:420px;margin:0;color:var(--olive-fonce)}
/* Pages intérieures */
.entete-page{padding-top:64px;padding-bottom:56px}
.entete-page h1{font-size:34px;font-weight:600;letter-spacing:-.02em;margin:0 0 10px}
.entete-page p{color:var(--doux);margin:0;max-width:640px}
.contenu{padding-top:56px;padding-bottom:88px}
.prose{max-width:760px;font-size:15px}
.prose h1{font-size:30px;font-weight:600;margin:0 0 24px}
.prose h2{font-size:18px;font-weight:600;margin:40px 0 12px;color:var(--olive-fonce)}
.prose a{color:var(--olive-fonce);text-decoration:underline}
.prose pre{background:var(--gris);border-radius:6px;padding:16px;overflow-x:auto;font-size:13px}
.prose code{font-family:ui-monospace,SFMono-Regular,Menlo,monospace;font-size:.9em}
.idees ul{list-style:none;padding:0}
.idees li{position:relative;padding:12px 0 12px 30px;border-bottom:1px solid var(--bord)}
.case{position:absolute;left:0;top:17px;width:16px;height:16px;border:1.5px solid var(--leger);border-radius:4px}
.case.coche{background:var(--olive);border-color:var(--olive);box-shadow:inset 0 0 0 3px var(--fond)}
.outils{display:flex;gap:16px;flex-wrap:wrap;align-items:end;margin:0 0 28px}
label{font-size:12px;font-weight:500;color:var(--doux);display:flex;flex-direction:column;gap:6px}
input,select{font:inherit;font-size:14px;height:42px;padding:0 16px;border:1px solid var(--bord);border-radius:999px;
background:var(--fond);color:var(--texte);min-width:200px}
input:focus,select:focus{outline:none;border-color:var(--olive)}
input[type=search]{width:100%;max-width:560px}
.tableau{overflow-x:auto;background:var(--fond);border-radius:6px;border:1px solid var(--bord)}
table{border-collapse:collapse;width:100%;font-size:14px;font-variant-numeric:tabular-nums}
th,td{padding:14px 18px;border-bottom:1px solid var(--bord);text-align:right;white-space:nowrap}
tbody tr:last-child td{border-bottom:0}
th:first-child,td:first-child{text-align:left}
th{font-size:11px;font-weight:600;letter-spacing:.08em;text-transform:uppercase;color:var(--doux);
cursor:pointer;user-select:none;background:var(--gris)}
th:hover{color:var(--olive-fonce)}
.tag{display:none;margin-left:10px;font-size:11px;font-weight:600;color:#fff;background:var(--olive);
border-radius:999px;padding:2px 10px}
tr.moins-cher .tag{display:inline-block}
tr.moins-cher td:last-child{color:var(--olive-fonce);font-weight:600}
.note{font-size:12px;color:var(--leger);margin-top:16px}
.vide{color:var(--leger)}
.liste-simple{list-style:none;padding:0;margin:0;max-width:760px}
.liste-simple li{padding:18px 0;border-bottom:1px solid var(--bord)}
.liste-simple b{display:block;font-weight:600}
.liste-simple a:hover b{color:var(--olive-fonce)}
footer{background:var(--gris)}
footer .conteneur{display:flex;justify-content:space-between;gap:24px;flex-wrap:wrap;padding:32px 24px;font-size:12px;
color:var(--doux)}
@media (max-width:900px){
.heros,.synthese,.rangee,.lecon{grid-template-columns:1fr;gap:32px}
.rangee:nth-of-type(odd) .panneau{order:0}
.formes{height:300px;max-width:420px}.arche{width:210px;height:290px;border-radius:105px 105px 0 0}
.cercle{width:160px;height:160px}.cercle strong{font-size:34px}
.cartes{grid-template-columns:1fr 1fr}.piste{grid-auto-columns:calc((100% - 24px)/2)}}
@media (max-width:600px){
.conteneur{padding:0 16px}.barre{height:auto;flex-wrap:wrap;gap:0;padding-top:14px}.logo{width:50%}
.date-entete{display:none}nav{width:100%;height:46px;align-items:center;gap:22px}
section.bloc-page{padding:64px 0}.heros{padding-top:40px;padding-bottom:64px}.heros h1{font-size:30px}
.chiffres,.cartes{grid-template-columns:1fr}.carrousel{grid-template-columns:1fr}.fleche{display:none}
.piste{grid-auto-columns:85%}.entete-page h1{font-size:28px}
.panneau{min-height:110px;padding:20px}.panneau strong{font-size:36px}.rangee{margin-bottom:48px;gap:20px}}
"""

JS_ACCUEIL = """
document.querySelectorAll('.carrousel').forEach(c=>{
  const piste=c.querySelector('.piste'),pts=[...c.parentElement.querySelectorAll('.points button')];
  const pas=()=>piste.firstElementChild.getBoundingClientRect().width+24;
  const nav=[c.querySelector('.prec'),c.querySelector('.suiv'),c.parentElement.querySelector('.points')];
  const verifier=()=>nav.forEach(n=>n.style.visibility=piste.scrollWidth>piste.clientWidth+2?'':'hidden');
  addEventListener('resize',verifier);verifier();
  c.querySelector('.prec').onclick=()=>piste.scrollBy({left:-pas(),behavior:'smooth'});
  c.querySelector('.suiv').onclick=()=>piste.scrollBy({left:pas(),behavior:'smooth'});
  pts.forEach((p,i)=>p.onclick=()=>piste.scrollTo({left:i*pas(),behavior:'smooth'}));
  piste.onscroll=()=>{const i=Math.round(piste.scrollLeft/pas());pts.forEach((p,j)=>p.classList.toggle('actif',i===j));};
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


def page(titre, contenu, actif="", prefixe="", script="", date=""):
    liens = "".join(
        f'<a href="{prefixe}{href}" class="{"actif" if href == actif else ""}">{nom}</a>' for href, nom in NAV)
    return f"""<!doctype html>
<html lang="fr"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(titre)} · Veille IA</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Montserrat:wght@400;500;600&display=swap" rel="stylesheet">
<link rel="stylesheet" href="{prefixe}style.css"></head>
<body><header><div class="conteneur barre"><a class="logo" href="{prefixe}index.html">Veille <b>IA</b></a>
<nav>{liens}</nav>{f'<span class="date-entete">{e(date)}</span>' if date else ""}</div></header>
<main>{contenu}</main>
<footer><div class="conteneur"><span>Veille IA · mise à jour chaque lundi</span>
<span>Résumés générés automatiquement à partir des sources citées. À vérifier avant diffusion.</span></div></footer>
{f"<script>{script}</script>" if script else ""}</body></html>"""


def entete_page(surtitre, titre, texte=""):
    return (f'<div class="bande"><div class="conteneur entete-page"><p class="surtitre">{surtitre}</p>'
            f'<h1>{titre}</h1>{f"<p>{texte}</p>" if texte else ""}</div></div>')


def lien_externe(item, classe=""):
    return (f'<a class="{classe}" href="{e(item["url"])}" target="_blank" rel="noopener">'
            f'{e(item["titre"])}</a>')


def element_liste(item):
    points = "".join(f"<li>{e(p)}</li>" for p in item.get("specificites", []))
    pertinence = f'<p class="pertinence">Pertinence : {e(item["pourquoi"])}</p>' if item.get("pourquoi") else ""
    details = f"<details><summary>Détails</summary><ul>{points}</ul>{pertinence}</details>" \
        if points or pertinence else ""
    return (f'<li>{lien_externe(item, "titre")}<div class="meta">{e(item.get("source"))}</div>'
            f'<p>{e(item.get("resume"))}</p>{details}</li>')


def moins_cher(modeles):
    """Modèle au prix moyen le plus bas (pondéré 3 tokens d'entrée pour 1 de sortie)."""
    if not modeles:
        return None
    return min(modeles, key=lambda m: (3 * m["entree"] + m["sortie"]) / 4)


def contenu_semaine(s, prefixe=""):
    par_cat = {c: [i for i in s["selection"] if i.get("categorie") == c] for c in TITRES}
    par_cat = {c: items for c, items in par_cat.items() if items}
    idees = s.get("idees", [])
    lecon = s.get("lecon") or {}
    lien_lecon = f'{prefixe}lecon/{Path(lecon["fichier"]).stem}.html' if lecon.get("fichier") else ""
    total = len(s["selection"])

    heros = f"""<div class="conteneur heros"><div>
<p class="surtitre">Semaine du {date_fr(s['date'])}</p>
<h1>Veille IA et nouvelles pratiques de la semaine</h1>
<p>Modèles, recherche, robotique, scraping web et monitoring : une sélection commentée, des idées à proposer et une leçon.</p>
<a class="bouton" href="#themes">Lire la sélection</a></div>
<div class="formes" aria-hidden="true"><div class="arche"></div>
<div class="cercle"><strong>{total}</strong><span>contenus<br>sélectionnés</span></div></div></div>"""

    synthese = f"""<div class="bande"><div class="conteneur synthese"><h2>Synthèse de la semaine</h2>
<p>{e(s["tendance"])}</p></div></div>""" if s.get("tendance") else ""

    chiffres = f"""<section class="bloc-page"><div class="conteneur"><h2 class="titre-section">En un coup d'œil</h2>
<div class="chiffres">
<div><div class="pastille">{total}</div><h3>Contenus</h3><p>Sélectionnés parmi les sources suivies, résumés et commentés.</p></div>
<div><div class="pastille">{len(par_cat)}</div><h3>Thèmes</h3><p>{e(", ".join(TITRES[c] for c in par_cat))}.</p></div>
<div><div class="pastille">{len(idees)}</div><h3>Idées</h3><p>Propositions concrètes à présenter à ton équipe.</p></div>
</div></div></section>"""

    # À la une : le premier contenu de chacun des trois premiers thèmes.
    une = [items[0] for items in par_cat.values()][:3]
    cartes = "".join(f"""<article class="carte"><div class="visuel"><span>{e(TITRES[i["categorie"]])}</span></div>
<div class="carte-corps"><h3>{lien_externe(i)}</h3><div class="meta">{e(i.get("source"))}</div>
<p>{e(i.get("resume"))}</p>
<a class="bouton clair" href="{e(i["url"])}" target="_blank" rel="noopener">Lire la source</a></div></article>"""
                     for i in une)
    a_la_une = f"""<div class="bande droite"><section class="bloc-page"><div class="conteneur">
<h2 class="titre-section">À la une</h2><div class="cartes">{cartes}</div></div></section></div>""" if une else ""

    raccourcis = "".join(f'<a href="#theme-{c}">{TITRES[c]}</a>' for c in par_cat)
    rangees = "".join(f"""<div class="rangee" id="theme-{c}"><div class="panneau"><strong>{len(items)}</strong>
<span>contenu{"s" if len(items) > 1 else ""}</span></div><div><h3>{TITRES[c]}</h3>
<ul class="liste">{"".join(element_liste(i) for i in items)}</ul></div></div>""" for c, items in par_cat.items())
    themes = f"""<section class="bloc-page" id="themes" style="scroll-margin-top:64px"><div class="conteneur">
<h2 class="titre-section">Par thème</h2><div class="raccourcis">{raccourcis}</div>{rangees}</div></section>"""

    m = moins_cher(s.get("prix") or [])
    bandeau = f"""<div class="bande"><div class="conteneur bandeau">
<h2>{f"Le moins cher cette semaine : {e(m['nom'])}" if m else "Comparatif des prix"}</h2>
<p>{f"{m['entree']} $ en entrée et {m['sortie']} $ en sortie par million de tokens. " if m else ""}
Compare les modèles et simule ton coût mensuel.</p>
{f'<div class="analyse">{md_html(s["comparatif"])}</div>' if s.get("comparatif") else ""}
<a class="bouton" href="{prefixe}prix.html">Voir le comparatif</a></div></div>"""

    carrousel = ""
    if idees:
        slides = "".join(f"""<div class="idee"><h3>{e(i["titre"])}</h3><p>{e(i["description"])}</p>
<div class="meta">Effort {e(i.get("effort"))}</div></div>""" for i in idees)
        points = "".join(f'<button aria-label="Idée {n + 1}" class="{"actif" if n == 0 else ""}"></button>'
                         for n in range(len(idees)))
        carrousel = f"""<section class="bloc-page"><div class="conteneur"><h2 class="titre-section">Idées à proposer</h2>
<div class="carrousel"><button class="fleche prec" aria-label="Précédent">‹</button><div class="piste">{slides}</div>
<button class="fleche suiv" aria-label="Suivant">›</button></div><div class="points">{points}</div></div></section>"""

    bloc_lecon = ""
    if lien_lecon:
        bloc_lecon = f"""<section class="bloc-page" style="padding-top:0"><div class="conteneur lecon"><div>
<p class="surtitre">Leçon de la semaine</p><h2>{e(lecon.get("titre"))}</h2>
<dl><dt>Format</dt><dd>Concept, application, exercice de 30 minutes</dd>
<dt>Auto-évaluation</dt><dd>3 questions avec réponses</dd></dl>
<a class="bouton" href="{lien_lecon}">Lire la leçon</a></div>
<div class="encart"><p>{e(lecon.get("titre"))}</p></div></div></section>"""

    return heros + synthese + chiffres + a_la_une + themes + bandeau + carrousel + bloc_lecon


def page_prix(modeles):
    if not modeles:
        return '<p class="vide">Les prix apparaîtront après la première veille.</p>'
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
    return f"""<div class="outils">
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
    derniere = f"Semaine du {date_fr(semaines[0]['date'])}" if semaines else ""

    # Accueil : la dernière veille.
    if semaines:
        accueil = contenu_semaine(semaines[0])
    else:
        accueil = entete_page("Bienvenue", "Veille IA hebdomadaire", "La première veille apparaîtra ici après la "
                              "prochaine exécution (chaque lundi, ou via Actions → Run workflow).")
    (sortie / "index.html").write_text(
        page("Cette semaine", accueil, "index.html", script=JS_ACCUEIL, date=derniere), "utf-8")

    # Archives + recherche dans toutes les semaines.
    elements, liste = [], ""
    for s in semaines:
        (sortie / "semaine" / f"{s['date']}.html").write_text(
            page(f"Semaine du {date_fr(s['date'])}", contenu_semaine(s, "../"), "archives.html", "../",
                 JS_ACCUEIL, f"Semaine du {date_fr(s['date'])}"), "utf-8")
        liste += (f'<li><a href="semaine/{s["date"]}.html"><b>Semaine du {date_fr(s["date"])}</b></a>'
                  f'{e(s.get("tendance", ""))[:200]}<div class="meta">{len(s["selection"])} contenus</div></li>')
        elements += [{"titre": i["titre"], "url": i["url"], "source": i.get("source", ""),
                      "resume": i.get("resume", ""), "cat": TITRES.get(i.get("categorie"), ""),
                      "date": date_fr(s["date"])}
                     for i in s["selection"]]
    donnees = json.dumps(elements, ensure_ascii=False).replace("</", "<\\/")
    archives = entete_page("Archives", "Toutes les veilles", "Recherche dans l'ensemble des contenus publiés.") + f"""
<div class="conteneur contenu"><input id="recherche" type="search" placeholder="Rechercher : Claude, NVIDIA, scraping, humanoïde…">
<ul id="resultats" class="liste-simple" style="margin:8px 0 48px"></ul>
<ul class="liste-simple">{liste or '<li class="vide">Aucune veille pour le moment.</li>'}</ul></div>"""
    (sortie / "archives.html").write_text(page("Archives", archives, "archives.html",
                                               script=f"const ELEMENTS={donnees};{JS_RECHERCHE}", date=derniere),
                                          "utf-8")

    # Leçons : une page par fichier de lecons/.
    liste = ""
    for f in sorted((racine / "lecons").glob("*.md"), reverse=True):
        texte = f.read_text(encoding="utf-8")
        titre = texte.splitlines()[0].lstrip("# ").strip() if texte else f.stem
        corps = re.sub(r"\A# .*\n", "", texte)
        (sortie / "lecon" / f"{f.stem}.html").write_text(page(
            titre, entete_page(f"Leçon du {date_fr(f.stem)}", e(titre))
            + f'<div class="conteneur contenu"><div class="prose">{md_html(corps)}</div></div>',
            "lecons.html", "../", date=derniere), "utf-8")
        liste += (f'<li><a href="lecon/{f.stem}.html"><b>{e(titre)}</b></a>'
                  f'<div class="meta">{date_fr(f.stem)}</div></li>')
    (sortie / "lecons.html").write_text(page("Leçons", entete_page(
        "Formation", "Leçons", "Une leçon par semaine, tirée de la veille.")
        + f'<div class="conteneur contenu"><ul class="liste-simple">'
          f'{liste or "<li class=vide>Aucune leçon pour le moment.</li>"}</ul></div>', "lecons.html",
        date=derniere), "utf-8")

    # Idées : le backlog idees.md, sans son titre (la page a le sien).
    fichier_idees = racine / "idees.md"
    idees = fichier_idees.read_text(encoding="utf-8") if fichier_idees.exists() else ""
    idees = re.sub(r"\A# .*\n+(?:[^#\n].*\n+)?", "", idees)
    (sortie / "idees.html").write_text(page("Idées", entete_page(
        "Backlog", "Idées à proposer", "Pour marquer une idée comme présentée, remplacez <code>[ ]</code> par "
        "<code>[x]</code> dans <code>idees.md</code> : le site se met à jour automatiquement.")
        + f'<div class="conteneur contenu"><div class="prose idees">'
          f'{md_html(idees) or "<p class=vide>Aucune idée pour le moment.</p>"}</div></div>', "idees.html",
        date=derniere), "utf-8")

    # Prix : la dernière photo des prix.
    fichier_prix = racine / "data" / "prix.json"
    modeles = json.loads(fichier_prix.read_text(encoding="utf-8")) if fichier_prix.exists() else []
    (sortie / "prix.html").write_text(page("Prix", entete_page(
        "Comparatif", "Prix des modèles", "Tarifs OpenRouter en dollars par million de tokens. "
        "Cliquez sur une colonne pour trier.") + f'<div class="conteneur contenu">{page_prix(modeles)}</div>',
        "prix.html", script=JS_PRIX if modeles else "", date=derniere), "utf-8")
    return sortie


if __name__ == "__main__":
    print(f"Site généré dans {construire(sortie=sys.argv[1] if len(sys.argv) > 1 else None)}")
