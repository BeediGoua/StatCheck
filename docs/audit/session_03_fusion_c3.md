# Session 03 — Fusion + C3 (fiabilité sémantique)

**Date:** 2026-10-10  
**Base commit:** `bf55afcd7fbb0b7d2ea7f7c623ddd10ba6644cee`  
**Scope:** fusion policy, AuthorityMatrix, claim-level post-validators, honest status, C3 route semantics.  
**Out of scope:** retrieval, SDMX, INSEE, verdicts, tuning of alignment threshold `0.45` / confidence `0.9`.

## Goals completed

1. **Policy** — `docs/contracts/fusion_policy_v1.md` (per-field authority + status rules).
2. **Alignment** — `semantic_relation` ∈ `{SAME_MENTION, SAME_MEANING, SEMANTIC_DISAGREEMENT, UNRELATED}` (alignment ≠ agreement).
3. **AuthorityMatrix** — rich `fuse_quantity`, territory without EXPLICIT auto-win, indicator/population/time/operation/frequency/adjustment slots.
4. **FusionEngine** — all Golden Path fields fused via align→authority→log; no silent `baseline or llm`.
5. **Post-validators** — claim-level invariants; status COMPLETE only when earned.
6. **C3** — documents `CALL_LLM` vs `BASELINE_ONLY`; orchestrator returns fusion status as-is (may stay AMBIGUOUS/CONTRADICTION).
7. **Adversarial tests** — 12 cases + non-regression S2/S2.1 / lot7 / LLM.

## Key decisions

| Topic | Decision |
|---|---|
| Agreement on quantity | Requires full rich equality (value, unit, scale, role, approx, sign, bounds) |
| Territory EXPLICIT | Never auto-wins when same surface + different codes → `CONFLICT_UNRESOLVED` |
| Status honesty | `CONFLICT_UNRESOLVED` → CONTRADICTION; alternatives → AMBIGUOUS; missing indicator → PARTIAL |
| C3 role | Routing only; never promotes to COMPLETE because LLM ran |
| Thresholds | Unchanged (`0.45` IoU/align, indicator confidence `0.9`, control `0.05`) |

## Commands run

```text
.venv\Scripts\python.exe -m pytest tests src/fusion/tests src/evaluation/tests --collect-only -q
# → 76 tests collected, 0 collection errors

.venv\Scripts\python.exe -m pytest tests/test_regression_c3.py src/evaluation/tests src/fusion/tests tests/parser/test_claim_adapters.py tests/parser/test_claim_specification_strict.py -q --tb=line
# → 55 passed

.venv\Scripts\python.exe -m pytest tests/parser/llm tests/test_lot7.py -q --tb=line
# → 14 passed, 3 skipped
```

## Files touched

- `docs/contracts/fusion_policy_v1.md` (new)
- `docs/audit/session_03_fusion_c3.md` (this file)
- `src/fusion/alignment.py` — `SemanticRelation`
- `src/fusion/authority.py` — full matrix + explanation codes
- `src/fusion/post_validators.py` (new)
- `src/fusion/engine.py` — multi-field + post-validators
- `src/evaluation/router.py` — `route` field + docs
- `src/evaluation/orchestrator.py` — `route_log`, no COMPLETE promotion
- `src/fusion/tests/test_fusion.py`, `test_fusion_conflicts.py`
- `src/evaluation/tests/test_c3_cascade.py`
- `PROJECT_STATUS.md`, `STATCHECK_START_HERE.md`

## Adversarial coverage

1. Quantity AGREEMENT (rich equality)  
2. Unit mismatch → CONFLICT  
3. Scale mismatch → CONFLICT  
4. Approximation mismatch → CONFLICT  
5. Territory AGREEMENT  
6. Same surface + different codes → CONFLICT (no EXPLICIT win)  
7. Population 15-24 vs 15-29 → AMBIGUOUS  
8. RELATIVE_CHANGE + percentage points → CONTRADICTION  
9. Missing indicator → PARTIAL  
10. C3 baseline sufficient → BASELINE_ONLY  
11. C3 ambiguous baseline → CALL_LLM  
12. C3 fusion remains non-COMPLETE after LLM path  
