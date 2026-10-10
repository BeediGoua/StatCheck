# Micro-Gold V0 — E2E oracle contract

**Status:** CANDIDATE (Session 4)  
**Path:** [`data/gold/micro_gold_v0/micro_gold_v0.yaml`](../../data/gold/micro_gold_v0/micro_gold_v0.yaml)  
**Loader:** [`src/gold/micro_gold_v0.py`](../../src/gold/micro_gold_v0.py)

## Purpose

Document, for a tiny set of realistic claims, the **exact expected proof chain**:

```text
claim → answerability → ClaimSpecification
  → provider / dataset / series / idbank
  → dimensions / periods / official observations
  → deterministic operation / result
  → verdict or abstention
  → ambiguities / provenance
```

This file is an **oracle for future Retrieval/SDMX sessions**. It is **not** a model benchmark and must not be marked `VALIDATED` merely because the schema exists.

## Non-goals

- Do not copy labels from `data/corpus/gold_validation.json` or sealed MOCK releases.
- Do not annotate from retriever or LLM suggestions.
- Do not tune C3 / fusion / retrieval.

## Enums

| Field | Allowed values |
|---|---|
| `answerability.status` | `FOUND`, `AMBIGUOUS`, `NOT_FOUND`, `INSUFFICIENT` |
| `expected_verdict` | `SUPPORTED`, `REFUTED`, `INSUFFICIENT_EVIDENCE`, or `null` |
| `gold_status` | `CANDIDATE` only until Session 4.1 verdict accepted (never auto-`VALIDATED`) |
| `annotation.review_status` | `DRAFT`, `SOURCE_CHECKED`, `NEEDS_HUMAN_REVIEW` |
| `annotation.verification_status` | `CONFIRMED`, `CORRECTED`, `NEEDS_HUMAN_REVIEW`, `UNRESOLVED` (Session 4.1) |
| `expected_computation.operation` | `VALUE`, `POINT_CHANGE`, `RELATIVE_CHANGE`, `RATIO`, `SUM`, `NONE` |

Session 4.1 rule: FOUND with `verification_status` in {CONFIRMED, CORRECTED} **requires** a non-null `idbank`.

## Structural rules

### FOUND

Must have:

- `expected_grounding.dataset_id`
- `expected_grounding.idbank` **or** `series_id`
- non-empty `expected_observations`
- `expected_computation` with `result` (unless operation `NONE` — forbidden for FOUND)
- `expected_verdict` ∈ {`SUPPORTED`, `REFUTED`}

### AMBIGUOUS / INSUFFICIENT / NOT_FOUND

Must have non-empty `ambiguities` (or for NOT_FOUND a documented search reason in `answerability.reason` **and** `ambiguities`).  
`expected_verdict` should be `INSUFFICIENT_EVIDENCE` or `null`.  
Grounding may be partial / candidate-only.

### Provenance

Every FOUND case must list at least one official INSEE URL and an `as_of_date`.  
When publication values diverge from a later revised series, `revision_note` is **required**.

## ClaimSpecification subtree

`claim_specification` mirrors Session 2 fields (not a full Pydantic Spec dump): indicator, populations, territories, time_period, claimed_quantity, statistical_operation, expressed_frequency, adjustment. Values are the **expected** parse for oracle comparison later.

## Computation alignment

Operations align with [`src/engine/calculator.py`](../../src/engine/calculator.py):

| Gold op | Calculator |
|---|---|
| `VALUE` | `get_value` |
| `POINT_CHANGE` | `point_variation` |
| `RELATIVE_CHANGE` | `relative_variation` |
| `RATIO` | `ratio` |
| `SUM` | `sum` |

Structural tests recompute from `expected_observations` with a documented tolerance (default absolute 0.05 for rounded %).

## Fixture set V0

Exactly 12 claims `MG001` … `MG012` with **frozen claim text**. See YAML + Session 4 audit.
