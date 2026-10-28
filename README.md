# MAJIA — Ma veille IA hebdomadaire

Chaque lundi matin, ce projet :

1. **collecte** les nouveautés de ~30 sources réparties en 7 thèmes (voir ci-dessous) ;
2. **trie et résume** les plus utiles pour ton profil avec Gemini (offre gratuite), avec pour chaque élément
   ses **spécificités concrètes** (chiffres, forces, limites), sans blabla marketing ;
3. construit un **tableau comparatif prix / qualité** des modèles à partir de données réelles,
   et signale les nouveaux modèles et les changements de prix ;
4. génère **3 idées à proposer à ton équipe** et **une leçon complète** (concept, application, exercice, auto-évaluation) ;
5. t'envoie le tout **par e-mail** et l'archive dans le dépôt.

## Ce que tu reçois

| Section | Sources |
|---|---|
| 🤖 Modèles et labos | Anthropic/Claude (actus, releases Claude Code et SDK), NVIDIA (blog + blog technique), OpenAI, Google DeepMind, Google AI, Hugging Face, Mistral/DeepSeek/Qwen/Llama |
| 📄 Articles scientifiques | Hugging Face Daily Papers, arXiv cs.AI / cs.CL / cs.LG (filtrés par mots-clés) |
| 🦾 Robotique | IEEE Spectrum Robotics, The Robot Report, arXiv cs.RO, actus robots humanoïdes |
| 🔍 Parsing de documents avec l'IA | Actus (LlamaParse, Docling, OCR + LLM…), releases Docling, arXiv cs.CV (documents) |
| 📈 Monitoring et observabilité | Actus observabilité LLM / AIOps, releases Langfuse, Hacker News |
| 🛠️ Nouvelles pratiques | Raschka, Latent Space, Import AI, Simon Willison, LangChain, Hacker News |
| ⚖️ Benchmarks et comparatifs | Actus benchmarks, LMArena, Artificial Analysis |
| 💰 Comparatif prix / qualité | Tableau chiffré : prix réels [OpenRouter](https://openrouter.ai/models) (entrée/sortie en $ par million de tokens, contexte) pour Claude, GPT, Gemini, Mistral, Llama, DeepSeek, Qwen, Grok, NVIDIA ; score de qualité et vitesse [Artificial Analysis](https://artificialanalysis.ai) si tu ajoutes la clé (optionnel) ; analyse du meilleur rapport qualité/prix par usage |

| Dossier / fichier | Rôle |
|---|---|
| `sources.yaml` | Ton profil, tes mots-clés et la liste des sources (à personnaliser) |
| `digests/` | Les veilles hebdomadaires archivées |
| `lecons/` | Ta base de cours, une leçon par semaine |
| `idees.md` | Ton backlog d'idées, à cocher quand tu les présentes |
| `data/vus.json` | Les liens déjà traités (évite les doublons) |
| `data/prix.json` | Les prix de la semaine précédente (pour détecter les changements) |

## Mise en route (≈ 15 min)

1. **Clé Gemini** : crée une clé gratuite sur <https://aistudio.google.com/apikey>.
2. **Mot de passe d'application Gmail** : active la validation en deux étapes sur ton compte Google, puis crée un mot de passe sur <https://myaccount.google.com/apppasswords>.
3. **Secrets GitHub** : dans *Settings → Secrets and variables → Actions*, ajoute :

   | Secret | Valeur |
   |---|---|
   | `GEMINI_API_KEY` | ta clé Gemini |
   | `SMTP_USER` | ton adresse Gmail |
   | `SMTP_PASSWORD` | le mot de passe d'application (16 caractères) |
   | `EMAIL_TO` | l'adresse qui reçoit la veille (plusieurs : séparées par des virgules) |
   | `ARTIFICIAL_ANALYSIS_API_KEY` | *(optionnel)* clé gratuite sur <https://artificialanalysis.ai> pour ajouter les scores de qualité et de vitesse au comparatif |

4. **Premier envoi** : onglet *Actions* → *Veille IA hebdomadaire* → *Run workflow*.

Ensuite, la veille part automatiquement chaque lundi vers 7 h (heure de Paris).

## Personnaliser

- **Ton profil** (`profil` dans `sources.yaml`) : plus il est précis, plus les idées et leçons sont pertinentes.
- **Mots-clés** (`mots_cles`) : filtrent les flux très volumineux (arXiv, Hacker News). Une source peut avoir ses propres `mots_cles`.
- **Sources** : ajoute un bloc `nom` / `url` (flux RSS ou Atom) / `categorie`
  (`modele`, `article`, `robotique`, `parsing`, `monitoring`, `pratique` ou `comparatif`).
  Astuce : n'importe quelle recherche Google News devient un flux avec
  `https://news.google.com/rss/search?q=TA+RECHERCHE+when:7d&hl=en-US&gl=US&ceid=US:en`,
  et les releases d'un projet GitHub avec `https://github.com/OWNER/REPO/releases.atom`.
- **Comparatif** (`prix` dans `sources.yaml`) : fournisseurs suivis et nombre de modèles récents par fournisseur.
- **Volume** : `max_par_source` (plafond par source) et `max_selection` (nombre d'éléments dans l'e-mail).
- **Modèle** : variable d'environnement `GEMINI_MODEL` (par défaut `gemini-2.5-flash`).
- **Autre serveur mail** : variables `SMTP_HOST` et `SMTP_PORT` (SSL, 465 par défaut).

## En local

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
pytest -q                                              # test complet avec un LLM simulé
GEMINI_API_KEY=xxx python -m veille.main --dry-run     # affiche la veille sans envoyer d'e-mail
```

## Limites à connaître

- Les résumés se basent sur les **abstracts et extraits RSS**, pas sur les PDF complets : vérifie l'article avant de le citer en réunion.
- Le LLM ne peut citer que des liens réellement collectés (les liens inventés sont rejetés), mais un résumé peut rester imprécis.
- Anthropic et Mistral n'ont pas de flux RSS officiel : ils sont suivis via Google News et les releases GitHub, donc certaines annonces peuvent arriver avec du retard ou via des articles de presse.
- Les prix OpenRouter sont ceux de la plateforme (en général identiques aux tarifs officiels, mais vérifie avant une décision budgétaire). La « qualité » n'est chiffrée que si tu ajoutes la clé Artificial Analysis ; sans elle, le comparatif se base sur les prix et les benchmarks cités dans l'actualité.
- Si une source est en panne ou change d'URL, elle est ignorée (visible dans les logs de l'Action) et la veille part quand même.

## Ta routine (le vrai levier)

- **Lundi, 30 min** : lis la veille, fais la leçon et son exercice.
- **Dans la semaine** : présente **une** idée de `idees.md` à ton équipe, puis coche-la.
