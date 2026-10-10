# Fusion Policy V1

**Status:** normative for Session 3  
**Scope:** combining Baseline Spec + LLM Spec into one `ClaimSpecification` at **claim level**  
**Non-goals:** dataset/SDMX compatibility, INSEE observations, verdicts, threshold tuning

## 1. Principles

1. **Alignment ≠ agreement.** Alignment means “same textual mention / same piece of the claim.” Authority decides agreement, conflict, or alternatives.
2. **No silent third interpretation.** Prefer `AMBIGUOUS` / `CONTRADICTION` / `PARTIAL` over inventing a fused value.
3. **Explicit text ≠ correct canonical code.** Especially for territories and populations.
4. **Rich quantity semantics must match entirely** for AGREEMENT (`numeric_value`, `unit`, `scale`, `role`, `approximation`, `sign`, bounds).
5. Every decision is traced: `field`, `baseline_value`, `llm_value`, `decision`, `explanation`, `evidence`.

## 2. Decision types

| Decision | Meaning |
|---|---|
| `AGREEMENT` | Both sides compatible; result keeps baseline copy (or shared value) |
| `BASELINE_SELECTED` | Only baseline, or baseline preferred for a justified reason |
| `LLM_SELECTED` | Only LLM, accepted when baseline absent |
| `DETERMINISTIC_VALIDATOR_SELECTED` | Same span, numeric disagreement → baseline extractor wins if validated |
| `BOTH_RETAINED_AS_ALTERNATIVES` | Keep primary + alternatives; status → AMBIGUOUS |
| `CONFLICT_UNRESOLVED` | Cannot choose safely; status → CONTRADICTION |
| `REJECTED` | Value unusable |

## 3. Field policies

### 3.1 Quantity (`claimed_quantity` / `reference_quantities`)

- **AGREEMENT** only if all equal (None==None): `numeric_value`, `unit`, `scale`, `role`, `approximation`, `sign`, `lower_bound`, `upper_bound`.
- Mismatch on `unit` / `scale` / `approximation` / bounds → `CONFLICT_UNRESOLVED` (not AGREEMENT).
- Role mismatch → `BOTH_RETAINED_AS_ALTERNATIVES` or `CONFLICT_UNRESOLVED` if same span.
- Same `span_offsets` + different `numeric_value` + baseline `validation_status=ACCEPTED` & confidence ≥ 0.9 → `DETERMINISTIC_VALIDATOR_SELECTED` (baseline value), **only if** unit/scale/approx/sign/bounds agree; otherwise conflict.

### 3.2 Territory

- **AGREEMENT** if `canonical_value` equal (case-normalized).
- Same surface label (or same offsets) but different `canonical_value` → `CONFLICT_UNRESOLVED` (`CANONICAL_CODE_CONFLICT`).
- **Never** auto-win baseline solely because `presence=EXPLICIT`.
- Orphan baseline / LLM → select that side if present and not MISSING.

### 3.3 Indicator / population / frequency / adjustment

- Same `canonical_value` (or equal normalized `original_label` if both canonical null) → AGREEMENT.
- Otherwise → `BOTH_RETAINED_AS_ALTERNATIVES` (alternatives list stores the other).

### 3.4 Time

- AGREEMENT if `start_date`, `end_date`, `precision`, `is_relative` agree.
- Otherwise → `BOTH_RETAINED_AS_ALTERNATIVES` or conflict if both absolute and incompatible.
- Relative unresolved periods are finalized as `PARTIAL` by post-validators.

### 3.5 Statistical operation

- AGREEMENT if `canonical_value` equal (normalized).
- Else → `BOTH_RETAINED_AS_ALTERNATIVES`.
- Op × unit incompatibilities handled in post-validators (not by inventing a unit).

## 4. Semantic relation (alignment layer)

| Relation | Meaning |
|---|---|
| `SAME_MENTION` | Same or nested offsets / same surface span |
| `SAME_MEANING` | Aligned and rich values / canonical equal |
| `SEMANTIC_DISAGREEMENT` | Aligned but values diverge |
| `UNRELATED` | Below alignment threshold |

## 5. Post-validation (claim-level)

After authority merge:

| Invariant | Effect |
|---|---|
| `RELATIVE_CHANGE` with percentage-point unit | → CONTRADICTION / warning + not COMPLETE |
| `POINT_CHANGE` with plain PERCENT when points expected | → conflict / not COMPLETE |
| `BETWEEN` without both bounds | → PARTIAL |
| START+END roles inconsistent | → AMBIGUOUS / PARTIAL |
| Relative period without dates | → PARTIAL |
| Missing indicator | → PARTIAL |
| Any `CONFLICT_UNRESOLVED` in log | → CONTRADICTION |
| Any `BOTH_RETAINED` or non-empty ambiguities | → AMBIGUOUS |
| Else | → COMPLETE |

## 6. C3 interaction

C3 chooses **CALL_LLM** vs **BASELINE_ONLY**. It does **not** set final answerability.

- BASELINE_ONLY → return baseline Spec as-is (may already be ACCEPTED/PARTIAL/…).
- CALL_LLM → run Fusion + post-validators; result may remain AMBIGUOUS/CONTRADICTION/PARTIAL. Never promote to COMPLETE merely because LLM ran.
