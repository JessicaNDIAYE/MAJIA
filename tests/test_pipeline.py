"""Test de bout en bout avec un LLM simulé et des sources simulées (aucun appel réseau)."""
import datetime as dt
import json
import shutil
import time
from pathlib import Path

import pytest

from veille import collecte, main, prix

RACINE = Path(__file__).resolve().parent.parent
MAINTENANT = time.time()
MERCREDI = dt.date(2026, 10, 28)

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Agents with MCP tool use</title><link>https://ex.org/a</link>
<description>A new agent benchmark using MCP.</description>
<pubDate>{date}</pubDate></item>
<item><title>Protein folding</title><link>https://ex.org/b</link>
<description>Biology only.</description><pubDate>{date}</pubDate></item>
</channel></rss>"""


OPENROUTER = {"data": [
    {"id": "anthropic/claude-test", "name": "Claude Test", "created": 2, "context_length": 200000,
     "pricing": {"prompt": "0.000003", "completion": "0.000015"}},
    {"id": "anthropic/claude-test:free", "name": "Gratuit", "created": 3, "context_length": 1,
     "pricing": {"prompt": "0", "completion": "0"}},
    {"id": "inconnu/modele", "name": "Hors liste", "created": 1, "context_length": 1,
     "pricing": {"prompt": "0.000001", "completion": "0.000001"}},
]}


class FausseReponse:
    def __init__(self, contenu=b"", donnees=None):
        self.content, self._donnees = contenu, donnees

    def raise_for_status(self):
        pass

    def json(self):
        return self._donnees


class FauxLLM:
    def json(self, prompt):
        if "Sélectionne" in prompt:
            return {"selection": [
                {"id": "https://ex.org/a", "categorie": "inconnue", "resume": "Résumé.",
                 "specificites": ["Contexte 200k tokens"], "pourquoi": "Utile."},
                {"id": "https://invente.org/x", "categorie": "modele", "resume": "Faux", "pourquoi": "Faux"},
            ], "tendance": "Les agents MCP.", "comparatif": "- Claude Test est le moins cher."}
        return {"idees": [{"titre": "Tester MCP", "description": "Brancher un serveur MCP.",
                           "effort": "faible", "source": "https://ex.org/a"}],
                "lecon": {"titre": "Les agents MCP", "markdown": "## Le concept\nTexte."}}


@pytest.fixture
def projet(tmp_path, monkeypatch):
    config = (RACINE / "sources.yaml").read_text(encoding="utf-8").replace("lecon_le: lundi", "lecon_le: tous")
    (tmp_path / "sources.yaml").write_text(config, encoding="utf-8")
    (tmp_path / "idees.md").write_text("# Backlog\n", encoding="utf-8")
    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(MAINTENANT - 3600))

    def faux_get(url, **_):
        if url == collecte.HF_PAPERS_API:
            return FausseReponse(donnees=[])
        if url == prix.OPENROUTER_API:
            return FausseReponse(donnees=OPENROUTER)
        if "arxiv" in url:
            return FausseReponse(RSS.format(date=date).encode())
        raise ConnectionError("source hors ligne")  # les autres sources tombent en panne

    monkeypatch.setattr(collecte.requests, "get", faux_get)
    return tmp_path


def test_pipeline_complet(projet):
    envois = []
    md = main.executer(projet, FauxLLM(), lambda *a: envois.append(a), MAINTENANT, MERCREDI)

    assert "Agents with MCP tool use" in md
    assert "invente.org" not in md  # un lien inventé par le LLM est rejeté
    assert "Protein folding" not in md  # filtré par mots-clés
    assert "## Recherche" in md  # catégorie inconnue → catégorie de la source
    assert "- Contexte 200k tokens" in md
    assert "| Claude Test | 3.0 | 15.0 | 200k |" in md
    assert "Hors liste" not in md and "Gratuit" not in md
    assert "Claude Test est le moins cher" in md
    assert len(envois) == 1 and "<html>" in envois[0][2]
    assert list((projet / "lecons").glob("*-les-agents-mcp.md"))
    assert "- [ ] **Tester MCP**" in (projet / "idees.md").read_text(encoding="utf-8")
    assert json.loads((projet / "data" / "vus.json").read_text()) == ["https://ex.org/a"]

    # Deuxième exécution : plus rien de nouveau, pas de doublon.
    assert main.executer(projet, FauxLLM(), None, MAINTENANT, MERCREDI) is None


def test_evolution_des_prix():
    avant = [{"id": "a/x", "entree": 1.0, "sortie": 2.0}]
    modeles = prix.comparer([{"id": "a/x", "entree": 0.5, "sortie": 2.0},
                             {"id": "a/y", "entree": 1.0, "sortie": 1.0}], avant)
    assert modeles[0]["evolution"].startswith("prix modifié")
    assert modeles[1]["evolution"] == "Nouveau"


def test_qualite_artificial_analysis():
    modeles = [{"id": "anthropic/claude-test", "nom": "Claude Test", "entree": 3, "sortie": 15, "contexte": 200000}]
    prix.ajouter_qualite(modeles, {"data": [{"slug": "claude-test", "median_output_tokens_per_second": 80.4,
                                             "evaluations": {"artificial_analysis_intelligence_index": 61}}]})
    assert "| 61 | 80 |" in prix.tableau_markdown(modeles)


def test_plafond_et_mots_cles_par_source(monkeypatch):
    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(MAINTENANT - 3600))
    items = "".join(f"<item><title>Humanoid {i}</title><link>https://r.org/{i}</link>"
                    f"<pubDate>{date}</pubDate></item>" for i in range(5))
    flux = f'<?xml version="1.0"?><rss version="2.0"><channel>{items}</channel></rss>'.encode()
    monkeypatch.setattr(collecte.requests, "get", lambda url, **_: FausseReponse(flux))
    config = {"max_par_source": 3, "mots_cles": ["MCP"], "sources": [
        {"nom": "RO", "url": "u", "categorie": "robotique", "filtrer": True, "mots_cles": ["humanoid"]}]}
    assert len(collecte.collecter(config, [], MAINTENANT)) == 3


def test_site_web(projet):
    from veille import site
    main.executer(projet, FauxLLM(), None, MAINTENANT, MERCREDI)
    sortie = site.construire(projet, projet / "_site")

    accueil = (sortie / "index.html").read_text(encoding="utf-8")
    assert "Agents with MCP tool use" in accueil and 'id="theme-article"' in accueil
    assert "Claude Test est le moins cher" in accueil
    assert "Claude Test" in (sortie / "prix.html").read_text(encoding="utf-8")
    assert "Agents with MCP tool use" in (sortie / "archives.html").read_text(encoding="utf-8")
    assert 'class="case"' in (sortie / "idees.html").read_text(encoding="utf-8")
    lecons = list((sortie / "lecon").glob("*.html"))
    assert len(lecons) == 1 and "../style.css" in lecons[0].read_text(encoding="utf-8")
    assert len(list((sortie / "jour").glob("*.html"))) == 1


def test_site_echappe_le_html(tmp_path):
    from veille import site
    (tmp_path / "data" / "semaines").mkdir(parents=True)
    semaine = {"date": "2026-01-05", "selection": [{"titre": "<script>alert(1)</script>", "url": "https://x.org",
                                                    "categorie": "article"}]}
    (tmp_path / "data" / "semaines" / "2026-01-05.json").write_text(json.dumps(semaine))
    sortie = site.construire(tmp_path, tmp_path / "_site")
    assert "<script>alert(1)" not in (sortie / "index.html").read_text(encoding="utf-8")
    assert "<\\/script>" in (sortie / "archives.html").read_text(encoding="utf-8")


def test_gemini_remplace_un_modele_disparu(monkeypatch):
    from veille import llm
    appels = []

    class R:
        def __init__(self, code, donnees=None):
            self.status_code, self._d, self.ok, self.text = code, donnees, code == 200, ""

        def json(self):
            return self._d

        def raise_for_status(self):
            pass

    def post(url, **_):
        appels.append(url)
        if "gemini-2.5-flash:" in url:
            return R(404)
        return R(200, {"candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}}]})

    modeles = [{"name": f"models/{n}", "supportedGenerationMethods": ["generateContent"]} for n in
               ["gemini-2.5-flash", "gemini-3.1-flash", "gemini-3.1-flash-lite", "gemini-4-flash-preview",
                "gemini-3.1-pro", "gemini-3-flash"]]
    monkeypatch.setattr(llm.requests, "post", post)
    monkeypatch.setattr(llm.requests, "get", lambda *a, **k: R(200, {"models": modeles}))

    client = llm.GeminiLLM(cle="x", modele="gemini-2.5-flash")
    assert client.json("prompt") == {"ok": True}
    assert client.modele == "gemini-3.1-flash"
    assert "gemini-3.1-flash:" in appels[-1]


def test_veille_envoyee_meme_si_la_lecon_echoue(projet):
    class LLMSansLecon(FauxLLM):
        def json(self, prompt):
            if "Sélectionne" in prompt:
                return super().json(prompt)
            raise ConnectionError("Remote end closed connection without response")

    envois = []
    md = main.executer(projet, LLMSansLecon(), lambda *a: envois.append(a), MAINTENANT, MERCREDI)
    assert "Agents with MCP tool use" in md and "pas pu être générée" in md
    assert envois and envois[0][0].endswith("2026-10-28")
    assert not list((projet / "lecons").glob("*.md"))
    assert (projet / "idees.md").read_text(encoding="utf-8") == "# Backlog\n"

    from veille import site
    assert "Agents with MCP" in (site.construire(projet, projet / "_site") / "index.html").read_text("utf-8")


def test_gemini_reessaie_apres_une_coupure(monkeypatch):
    from veille import llm
    essais = []

    class R:
        status_code, ok, text = 200, True, ""

        def json(self):
            return {"candidates": [{"content": {"parts": [{"text": '{"ok": 1}'}]}}]}

    def post(url, **_):
        essais.append(url)
        if len(essais) < 3:
            raise llm.requests.ConnectionError("Connection aborted.")
        return R()

    monkeypatch.setattr(llm.requests, "post", post)
    monkeypatch.setattr(llm.time, "sleep", lambda s: None)
    assert llm.GeminiLLM(cle="x").json("p") == {"ok": 1} and len(essais) == 3


def test_titre_des_releases_github():
    flux = (b'<?xml version="1.0"?><feed xmlns="http://www.w3.org/2005/Atom">'
            b'<entry><title>v2.144.0</title><link href="https://github.com/a/b/releases/tag/v2.144.0"/></entry>'
            b'<entry><title>Crawl4AI 0.8</title><link href="https://github.com/a/b/releases/tag/0.8"/></entry></feed>')
    source = {"nom": "Crawl4AI (releases)", "url": "https://github.com/a/b/releases.atom", "categorie": "parsing"}
    assert [e.titre for e in collecte.lire_flux(source, flux)] == ["Crawl4AI v2.144.0", "Crawl4AI 0.8"]


def ecrire_jour(racine, date, titre, **extra):
    dossier = racine / "data" / "semaines"
    dossier.mkdir(parents=True, exist_ok=True)
    jour = {"date": date, "tendance": f"Tendance du {date}", "prix": [], "idees": [], "lecon": None,
            "selection": [{"titre": titre, "url": f"https://ex.org/{date}", "source": "S", "categorie": "pratique",
                           "resume": "Résumé."}], **extra}
    (dossier / f"{date}.json").write_text(json.dumps(jour), encoding="utf-8")


def test_lecon_seulement_le_jour_prevu(projet):
    config = (projet / "sources.yaml").read_text(encoding="utf-8").replace("lecon_le: tous", "lecon_le: lundi")
    (projet / "sources.yaml").write_text(config, encoding="utf-8")
    md = main.executer(projet, FauxLLM(), None, MAINTENANT, MERCREDI)
    assert "Leçon de la semaine" not in md and "pas pu être générée" not in md
    assert not list((projet / "lecons").glob("*.md"))
    assert main.jour_de_lecon({"lecon_le": "lundi"}, dt.date(2026, 10, 26))


def test_pas_de_mail_le_weekend(projet):
    envois = []
    assert main.executer(projet, FauxLLM(), lambda *a: envois.append(a), MAINTENANT, dt.date(2026, 10, 31))
    assert envois == [] and (projet / "data" / "semaines" / "2026-10-31.json").exists()
    assert main.mail_du_jour({"mail_weekend": "normal"}, dt.date(2026, 10, 31))


def test_mail_du_lundi_resume_le_weekend(projet):
    ecrire_jour(projet, "2026-10-31", "Nouveauté du samedi")
    ecrire_jour(projet, "2026-11-01", "Nouveauté du dimanche")
    envois = []
    main.executer(projet, FauxLLM(), lambda *a: envois.append(a), MAINTENANT, dt.date(2026, 11, 2))
    sujet, texte, _ = envois[0]
    assert "+ week-end" in sujet and "Ce que tu as raté ce week-end" in texte
    assert texte.index("Samedi 31/10") < texte.index("Nouveauté du samedi") < texte.index("Nouveauté du dimanche")


def test_site_historique_hier_et_weekend(tmp_path):
    from veille import site
    ecrire_jour(tmp_path, "2026-10-31", "Samedi A")
    ecrire_jour(tmp_path, "2026-11-01", "Dimanche B")
    ecrire_jour(tmp_path, "2026-11-02", "Lundi C")
    sortie = site.construire(tmp_path, tmp_path / "_site")

    accueil = (sortie / "index.html").read_text(encoding="utf-8")
    assert "Lundi C" in accueil
    assert 'href="jour/2026-11-01.html">Voir hier' in accueil
    assert 'href="weekend/2026-10-31.html">Voir le week-end' in accueil
    weekend = (sortie / "weekend" / "2026-10-31.html").read_text(encoding="utf-8")
    assert "Week-end du 31 octobre au 1er novembre 2026" in weekend and "Samedi A" in weekend and "Dimanche B" in weekend
    dimanche = (sortie / "jour" / "2026-11-01.html").read_text(encoding="utf-8")
    assert "../jour/2026-10-31.html" in dimanche and "../jour/2026-11-02.html" in dimanche
    historique = (sortie / "archives.html").read_text(encoding="utf-8")
    assert "Novembre 2026" in historique and "Octobre 2026" in historique
