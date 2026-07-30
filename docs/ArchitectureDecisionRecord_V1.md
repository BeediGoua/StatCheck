# ArchitectureDecisionRecord_V1

- **decision_id**: ADR-2026-07-30-V1
- **selected_architecture**: C3
- **selected_version**: 1.0.0
- **decision_date**: 2026-07-30
- **candidate_runs**: C0, C1, C2, C3
- **elimination_policy_version**: v1.0
- **eliminated_architectures**: C1 (LLM pur)
- **elimination_reasons**: Violation du seuil de sécurité (3 erreurs critiques silencieuses).
- **ranking_results**: 1. C3 / 2. C2 / 3. C0
- **human_review_reference**: N/A (Discordances McNemar = 0)
- **accepted_tradeoffs**: Augmentation marginale de la latence (+1.5s sur 25% des requêtes) acceptée au profit d'une sécurité absolue (0 erreur silencieuse).
- **known_limitations**: Dépendant d'un hardware capable de faire tourner Qwen2.5 (8GB VRAM minimum) pour le routeur C3.
- **fallback_architecture**: C0 (Baseline symbolique).
- **approver**: Comité Architecture
- **frozen_configuration_hash**: 8f6632cdce65a7c2ace5ac969351597482806347b85ef887ad98d8384b3a7fc4

## Détails du Front de Pareto et McNemar
Comparaison stricte entre C2 et C3 (les favoris) :
C3 domine C2. Sur le plan de la qualité, C3 == C2 (Discordances McNemar = 0). Sur le plan coût, C3 réduit la charge d'inférence de 75%.