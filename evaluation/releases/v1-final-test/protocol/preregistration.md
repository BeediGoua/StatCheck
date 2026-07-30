# Test Final V1 : Pré-enregistrement du Protocole (Gel)

- **Architecture Choisie** : V1 = C3 (Cascade Baseline-First)
- **Modèle LLM** : `qwen2.5:latest` via Ollama (Local)
- **Paramètres LLM** : Temperature = 0.2, Format = JSON Structured Outputs.
- **Ressources Baseline** : spaCy `fr_core_news_lg`, COG 2024.

## 1. Corpus de Test
- Le test s'effectue sur 40 affirmations (fichier `test_split.jsonl`), formellement non vues durant les phases d'apprentissage et de validation.

## 2. Déroulement de l'Exécution (Harnais)
- Exécution de l'Architecture C3 (1 seule itération finale par affirmation).
- Les métriques générées par `src/evaluation/scorer.py` feront foi.
- **Retry Policy** : Uniquement pour défaillance technique d'Ollama (timeout). Aucun retry métier autorisé.
- Aucun changement de prompt ni de règle regex autorisé à partir de ce point.

## 3. Succès
Le système sera jugé opérationnel si :
1. Le taux d'erreurs critiques silencieuses reste à 0.
2. La latence reste inférieure au traitement 100% LLM (bénéfice C3).
3. Le score Exact Match et F1 est calculé formellement avec ses intervalles de confiance.
