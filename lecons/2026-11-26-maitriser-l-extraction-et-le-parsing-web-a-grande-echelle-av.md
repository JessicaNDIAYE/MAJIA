# Maîtriser l'extraction et le parsing web à grande échelle avec Nemotron 3.5 Parse et Firecrawl

*Leçon du 2026-11-26*

## Le concept
Le parsing et l'extraction de données web pour alimenter des agents LLM ou des pipelines RAG nécessitent de traiter de grands volumes de texte structuré tout en maîtrisant les coûts et la latence. L'association de **Firecrawl** (pour convertir proprement des pages web en Markdown) et de modèles spécialisés ultra-rapides comme **Nemotron 3.5 Parse** (via le modèle `nvidia/nemotron-3.5-lightning`) permet de traiter efficacement des contextes massifs allant jusqu'à 1 million de tokens.

## Pourquoi c'est important
En tant qu'ingénieure IA, vous savez que le coût et la vitesse sont des goulots d'étranglement majeurs lors du scraping de sites web complexes. Avec un modèle facturé à seulement 0.07 $ par million de tokens en entrée et 0.2 $ en sortie, couplé à une capacité de contexte énorme (1 048 576 tokens) et optimisé par fine-tuning sur des données ouvertes, vous pouvez transformer radicalement l'efficacité économique de vos pipelines de données.

## Comment l'appliquer
Pour appliquer cette approche dans vos pipelines actuels :
1. Utilisez la dernière version de **Firecrawl** (`v2.11.871`) pour extraire le contenu brut des pages web cibles sous un format Markdown propre et structuré.
2. Passez ce contenu nettoyé au modèle `nvidia/nemotron-3.5-lightning` via l'API appropriée pour extraire les entités ou structurer les informations selon vos besoins.
3. Profitez de la grande fenêtre de contexte pour envoyer des lots de pages ou des sites entiers en une seule fois, réduisant ainsi les allers-retours.

## Exercice pratique (30 min max)
- **Étape 1** : Passez en revue la documentation de l'article Hugging Face sur Nemotron 3.5 Parse.
- **Étape 2** : Configurez un script de test local simulant l'appel au modèle `nvidia/nemotron-3.5-lightning` avec un prompt d'extraction structurée.
- **Étape 3** : Estimez le coût pour traiter 10 000 pages web en vous basant sur la grille tarifaire (0.07$ / 1M tokens d'entrée).

## Questions d'auto-évaluation
1. **Quel est le coût d'entrée par million de tokens pour le modèle Nemotron 3.5 Lightning ?**
   - *Réponse* : 0.07 $ par million de tokens.
2. **Quelle est la taille maximale de la fenêtre de contexte supportée ?**
   - *Réponse* : 1 048 576 tokens.
3. **Quel rôle joue Firecrawl dans ce pipeline de données ?**
   - *Réponse* : Il convertit les pages web en Markdown propre et exploitable par les agents.

## Pour aller plus loin
- [Building on Nemotron 3.5 Parse: Open Data, Fine-Tuning, and Faster Inference](https://huggingface.co/blog/nvidia/building-on-nemotron-35-parse-open-data-fine-tunin)
- [Firecrawl v2.11.871 Release](https://github.com/firecrawl/firecrawl/releases/tag/v2.11.871)
