# Session 02.1 — ClaimSpecification contract hardening

**Date:** 2026-10-10  
**Base commit (Session 2):** `5aaf667b978c299ad7ffb3f2b7ad8df3c268d874`  
**Scope:** harden IR only — no Fusion semantics, retrieval, SDMX, INSEE, verdicts.  
**Récit humain :** [`docs/sessions/session_02_1_durcissement.md`](../sessions/session_02_1_durcissement.md)

## Goals completed

1. **Strict models** — `ConfigDict(extra="forbid")` on `ClaimSlot`, `ClaimTime`, `ClaimedQuantity`, `Ambiguity`, `ClaimSpecification`.
2. **Typed `ParseStatus`** — enum with ACCEPTED / PARTIAL / AMBIGUOUS / MISSING_CONTEXT / REJECTED / PENDING / COMPLETE / CONTRADICTION.
3. **Rich claim-side quantities** — `lower_bound`, `upper_bound`, `scale`, `approximation`, `sign` on `ClaimedQuantity` (+ canonical enums `QuantityScale`, `QuantityApproximation`).
4. **Provenance mapping** — LLM certainty / baseline `territory_status` no longer force `EXPLICIT_TEXT` for implicit/inferred cases.
5. **Tests** — strict rejection + semantic adapter cases C–H.

## Decisions

- Did **not** reintroduce `ACCEPTED_WITH_WARNINGS` / `ACCEPTED_WITH_CORRECTIONS`. Scorer silent-critical applies only for `ACCEPTED` and `COMPLETE`.
- Canonical quantity enums live in `claim_specification.py` (not imported from LLM schemas) to avoid coupling.
- Baseline `territory_status=MISSING` → `presence=MISSING`, `provenance=DEFAULTED`; `INFERRED` → `INFERRED` + `IMPLICIT`.

## Commands run

```text
uv run --with pytest python -m pytest tests src/evaluation/tests src/fusion/tests --ignore=scratch --continue-on-collection-errors --collect-only -q
# → 64 tests collected, 0 collection errors

uv run --with pytest python -m pytest tests/test_regression_c3.py src/evaluation/tests src/fusion/tests tests/parser/test_claim_adapters.py tests/parser/test_claim_specification_strict.py -q --tb=line
# → 43 passed

uv run --with pytest python -m pytest tests/parser/llm tests/test_lot7.py -q --tb=line
# → 14 passed, 3 skipped
```

## Files touched

- `src/parser/claim_specification.py`
- `src/parser/canonical.py`
- `src/parser/adapters/baseline_to_canonical.py`
- `src/parser/adapters/llm_to_canonical.py`
- `src/evaluation/router.py`, `scorer.py`, `generate_report.py`
- `src/fusion/engine.py` (ParseStatus only)
- tests under `tests/parser/`, `tests/test_regression_c3.py`, evaluation/fusion tests
- `docs/contracts/claim_specification_v1.md`
- `PROJECT_STATUS.md`, `STATCHECK_START_HERE.md`
- this audit note

## Out of scope (Session 3+)

Fusion authority rewrite, post-validators, C3 threshold tuning, retrieval, SDMX, verdicts.
