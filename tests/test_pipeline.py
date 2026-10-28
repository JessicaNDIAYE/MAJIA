"""Test de bout en bout avec un LLM simulé et des sources simulées (aucun appel réseau)."""
import json
import shutil
import time
from pathlib import Path

import pytest

from veille import collecte, main

RACINE = Path(__file__).resolve().parent.parent
MAINTENANT = time.time()

RSS = """<?xml version="1.0"?><rss version="2.0"><channel><title>t</title>
<item><title>Agents with MCP tool use</title><link>https://ex.org/a</link>
<description>A new agent benchmark using MCP.</description>
<pubDate>{date}</pubDate></item>
<item><title>Protein folding</title><link>https://ex.org/b</link>
<description>Biology only.</description><pubDate>{date}</pubDate></item>
</channel></rss>"""


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
                {"id": "https://ex.org/a", "categorie": "article", "resume": "Résumé.", "pourquoi": "Utile."},
                {"id": "https://invente.org/x", "categorie": "modele", "resume": "Faux", "pourquoi": "Faux"},
            ], "tendance": "Les agents MCP."}
        return {"idees": [{"titre": "Tester MCP", "description": "Brancher un serveur MCP.",
                           "effort": "faible", "source": "https://ex.org/a"}],
                "lecon": {"titre": "Les agents MCP", "markdown": "## Le concept\nTexte."}}


@pytest.fixture
def projet(tmp_path, monkeypatch):
    shutil.copy(RACINE / "sources.yaml", tmp_path / "sources.yaml")
    (tmp_path / "idees.md").write_text("# Backlog\n", encoding="utf-8")
    date = time.strftime("%a, %d %b %Y %H:%M:%S GMT", time.gmtime(MAINTENANT - 3600))

    def faux_get(url, **_):
        if url == collecte.HF_PAPERS_API:
            return FausseReponse(donnees=[])
        if "arxiv" in url:
            return FausseReponse(RSS.format(date=date).encode())
        raise ConnectionError("source hors ligne")  # les autres sources tombent en panne

    monkeypatch.setattr(collecte.requests, "get", faux_get)
    return tmp_path


def test_pipeline_complet(projet):
    envois = []
    md = main.executer(projet, FauxLLM(), lambda *a: envois.append(a), MAINTENANT)

    assert "Agents with MCP tool use" in md
    assert "invente.org" not in md  # un lien inventé par le LLM est rejeté
    assert "Protein folding" not in md  # filtré par mots-clés
    assert len(envois) == 1 and "<html>" in envois[0][2]
    assert list((projet / "lecons").glob("*-les-agents-mcp.md"))
    assert "- [ ] **Tester MCP**" in (projet / "idees.md").read_text(encoding="utf-8")
    assert json.loads((projet / "data" / "vus.json").read_text()) == ["https://ex.org/a"]

    # Deuxième exécution : plus rien de nouveau, pas de doublon.
    assert main.executer(projet, FauxLLM(), None, MAINTENANT) is None
