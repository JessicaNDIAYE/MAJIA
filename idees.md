# Backlog d’idées à proposer

Coche une idée quand tu l’as présentée à ton équipe.

## Semaine du 2026-10-28

- [ ] **Transition de l'extraction structurée vers le scoring de logprobs pour les tâches d'étiquetage** (effort : moyen) — Remplacer les prompts générant du JSON ou des listes syntaxiques (ex. validation binaire, classification textuelle) par l'extraction directe des probabilités des tokens cibles (YES/NO). Cette approche, validée par LinkedIn, élimine les erreurs de parsing en sortie et accélère radicalement le débit d'inférence en production. ([source](https://arxiv.org/abs/2610.36383))
- [ ] **Audit et purge temporelle du contexte pour fiabiliser la mémoire des agents** (effort : faible) — Implémenter une étape d'invalidation explicite des faits obsolètes avant l'injection en mémoire contextuelle de l'agent. Des travaux récents montrent qu'élargir la fenêtre de retrieval sans filtrer l'historique fait chuter la précision (de 45% à 32% sur FactConsolidation), car le modèle échoue à prioriser le fait le plus récent lors de la génération. ([source](https://arxiv.org/abs/2610.36308))
- [ ] **Optimisation du parsing de documents longs avec un modèle dédié 1.3B ou Docling v2.144** (effort : moyen) — Délester les pipelines RAG de l'usage systématique de LLM coûteux en intégrant OXR-1.0 (1,3B paramètres) ou Docling v2.144 pour extraire la hiérarchie des titres sans parsing lourd. Cela permet de préserver la VRAM, de contourner le découpage manuel de PDF complexes et de réduire la facture d'API de vision. ([source](https://news.google.com/rss/articles/CBMisgFBVV95cUxPVEZnaWdmVEJlYVE5SnBMTFdTaGVTSzFFd3d0T1dPdk5hYTQ1MnlrU2N3d2QydTNITEZud0lRYTJaWXY5cVU0QUdOUlI1OVlfTExCREJCeEVhekZvSmpMUGs2VklUbmp0TVB3endQY05lSEpyRlVWZEFGT04yT0Z2bk8wTHU0dVNoQWhaLUhENnB0NmhzVG1COGdRbThINk1fNXB4T2l1cHNtNDh2cFlsekhR?oc=5))

## Semaine du 2026-11-09

- [ ] **Audit des timeouts vLLM et gestion des requêtes orphelines** (effort : moyen) — Analyser notre configuration vLLM et nos proxys pour vérifier si les annulations de clients après un dépassement de délai propagent correctement l'arrêt du calcul au moteur, évitant ainsi le gaspillage de ressources sur des requêtes abandonnées. ([source](https://arxiv.org/abs/2611.08684))
- [ ] **Robustesse des agents de raisonnement face aux injections de pensée** (effort : élevé) — Mettre en place des garde-fous pour nos agents LLM utilisant des chaînes de pensée explicites afin d'éviter qu'un retour de texte non sécurisé imitant la délibération ne détourne le comportement du modèle. ([source](https://arxiv.org/abs/2611.08811))
- [ ] **Hybridation locale/serveur pour l'optimisation des coûts d'inférence** (effort : élevé) — S'inspirer de l'approche 'VLA Handover' pour concevoir une architecture de routage dynamique qui bascule nos requêtes vers de grands modèles de serveur uniquement en cas de risque d'échec détecté sur un modèle local plus léger. ([source](https://arxiv.org/abs/2611.08987))
