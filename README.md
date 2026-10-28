# MAJIA — Ma veille IA hebdomadaire

Chaque lundi matin, ce projet :

1. **collecte** les nouveautés de 13 sources (articles scientifiques, nouveaux modèles, nouvelles pratiques) ;
2. **trie et résume** les plus utiles pour ton profil avec Gemini (offre gratuite) ;
3. génère **3 idées à proposer à ton équipe** et **une leçon complète** (concept, application, exercice, auto-évaluation) ;
4. t'envoie le tout **par e-mail** et l'archive dans le dépôt.

| Dossier / fichier | Rôle |
|---|---|
| `sources.yaml` | Ton profil, tes mots-clés et la liste des sources (à personnaliser) |
| `digests/` | Les veilles hebdomadaires archivées |
| `lecons/` | Ta base de cours, une leçon par semaine |
| `idees.md` | Ton backlog d'idées, à cocher quand tu les présentes |
| `data/vus.json` | Les liens déjà traités (évite les doublons) |

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

4. **Premier envoi** : onglet *Actions* → *Veille IA hebdomadaire* → *Run workflow*.

Ensuite, la veille part automatiquement chaque lundi vers 7 h (heure de Paris).

## Personnaliser

- **Ton profil** (`profil` dans `sources.yaml`) : plus il est précis, plus les idées et leçons sont pertinentes.
- **Mots-clés** (`mots_cles`) : filtrent les flux arXiv, très volumineux.
- **Sources** : ajoute un bloc `nom` / `url` (flux RSS ou Atom) / `categorie` (`article`, `modele` ou `pratique`).
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
- Les blogs d'Anthropic et de Mistral n'ont pas de flux RSS : ils ne sont pas inclus.
- Si une source est en panne ou change d'URL, elle est ignorée (visible dans les logs de l'Action) et la veille part quand même.

## Ta routine (le vrai levier)

- **Lundi, 30 min** : lis la veille, fais la leçon et son exercice.
- **Dans la semaine** : présente **une** idée de `idees.md` à ton équipe, puis coche-la.
