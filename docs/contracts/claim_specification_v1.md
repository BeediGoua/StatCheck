# ClaimSpecification V1

**Status:** normative contract for Session 2 (+ hardening Session 2.1)  
**Scope:** representation of a statistical **claim as asserted in text**  
**Non-goals:** official observations, computed quantities, SDMX keys, verdicts  
**Strictness:** all IR models use Pydantic v2 `ConfigDict(extra="forbid")` — unknown/legacy fields (`indicators`, `measures`, typos) raise `ValidationError`.

## 1. Purpose

`ClaimSpecification` is the **single** in-memory / API representation of a parsed claim shared by:

- baseline → adapter → Spec
- LLM → adapter → Spec
- Fusion, C3Router, Scorer (and later retrieval / resolution)

It must **not** mix:

| Layer | Example |
|---|---|
| What the user asserts | `claimed_quantity = -20%` |
| Official observations (later) | `obs_2020 = 8.0`, `obs_2024 = 7.1` |
| What StatCheck computes (later) | `computed_quantity = -11.25%` |

## 2. Shape

```text
ClaimSpecification
├── claim_id: str
├── original_text: str
│
├── indicator: ClaimSlot?
├── populations: ClaimSlot[]
├── territories: ClaimSlot[]
├── time_period: ClaimTime?
├── expressed_frequency: ClaimSlot?
├── adjustment: ClaimSlot?
├── expected_dimensions: ClaimSlot[]
│
├── claimed_quantity: ClaimedQuantity?      # asserted headline quantity
├── reference_quantities: ClaimedQuantity[] # START_VALUE / END_VALUE / …
├── statistical_operation: ClaimSlot?
├── comparison: ClaimSlot?
│
├── parse_status: ParseStatus
├── ambiguities: Ambiguity[]
└── warnings: str[]
```

### 2.1 ClaimSlot (shared metadata)

| Field | Meaning |
|---|---|
| `canonical_value` | Normalized code/label when known |
| `original_label` | Surface form in the claim text |
| `span_offsets` | `(start, end)` in `original_text` |
| `provenance` | `EXPLICIT_TEXT` / `IMPLICIT_CONTEXT` / `INFERRED` / `DEFAULTED` |
| `presence` | `EXPLICIT` / `IMPLICIT` / `MISSING` |
| `constraint_type` | `HARD_CONSTRAINT` / `PREFERENCE` / `UNCERTAIN_INFERENCE` |
| `confidence` | `[0, 1]` |
| `alternatives` | Competing interpretations |

### 2.2 ClaimTime

Extends `ClaimSlot` with: `start_date`, `end_date`, `precision`, `is_relative`.

### 2.3 ClaimedQuantity

Extends `ClaimSlot` with:

| Field | Meaning |
|---|---|
| `numeric_value` | Float asserted by the claim (optional if only bounds) |
| `lower_bound` / `upper_bound` | Interval asserted (« entre 4 et 6 % ») |
| `unit` | e.g. `PERCENT`, `PERCENTAGE_POINT`, `COUNT` |
| `scale` | `UNIT` / `THOUSAND` / `MILLION` / `BILLION` / `TRILLION` / `NONE` |
| `role` | See §3 |
| `approximation` | `EXACT` / `APPROXIMATELY` / `AT_LEAST` / `AT_MOST` / `MORE_THAN` / `LESS_THAN` / `BETWEEN` |
| `sign` | Optional claim-side sign string (e.g. `-`) |

### 2.4 Ambiguity

| Field | Meaning |
|---|---|
| `field` | Spec field name (`indicator`, `territories`, …) |
| `reason` | Why unresolved |
| `alternatives` | Candidate values |
| `requires_human_validation` | bool |

## 3. Quantity roles

| Role | Goes to |
|---|---|
| `CURRENT_VALUE` | `claimed_quantity` (level asserted now) |
| `CLAIMED_CHANGE` | `claimed_quantity` |
| `RELATIVE_CHANGE` | `claimed_quantity` |
| `ABSOLUTE_CHANGE` | `claimed_quantity` |
| `START_VALUE` | `reference_quantities` |
| `END_VALUE` | `reference_quantities` |
| `THRESHOLD`, `NUMERATOR`, … | `reference_quantities` (or ambiguity if unclear) |

**Examples**

1. « L'inflation est de 5 %. »  
   - `claimed_quantity`: 5, `PERCENT`, `CURRENT_VALUE`  
   - `statistical_operation.canonical_value`: `VALUE`

2. « Le chômage a baissé de 20 % depuis 2020. »  
   - `claimed_quantity`: 20 (sign/direction via operation), `PERCENT`, `RELATIVE_CHANGE` or `CLAIMED_CHANGE`  
   - `time_period.is_relative` / start around 2020  
   - `statistical_operation`: decrease / relative change

3. « Le taux est passé de 8 % à 7 %. »  
   - `reference_quantities`: `START_VALUE=8`, `END_VALUE=7`  
   - `claimed_quantity` optional (derived change not required in V1 if only anchors are stated)

## 4. ParseStatus (typed enum)

`parse_status` is a `ParseStatus` enum (not a free string). Allowed values:

| Status | Meaning |
|---|---|
| `ACCEPTED` | Spec complete enough for downstream routing |
| `PARTIAL` | Missing critical slots |
| `AMBIGUOUS` | Competing interpretations recorded in `ambiguities` |
| `MISSING_CONTEXT` | Cannot resolve without external context |
| `REJECTED` | Unusable / contradictory |
| `PENDING` | Intermediate (fusion only) |
| `COMPLETE` | Fusion success synonym of accepted fused result |
| `CONTRADICTION` | Unresolved conflict after fusion |

Invalid values raise `ValidationError`.

Baseline `status.answerability` mapping:

| Baseline | Spec `parse_status` |
|---|---|
| `VERIFIABLE` | `ACCEPTED` |
| `AMBIGUOUS` | `AMBIGUOUS` |
| `MISSING_CONTEXT` | `MISSING_CONTEXT` |
| `CONTRADICTION` | `REJECTED` |

LLM `parse_status` mapping:

| LLM | Spec |
|---|---|
| `COMPLETE` | `ACCEPTED` |
| `PARTIAL` | `PARTIAL` |
| `AMBIGUOUS` | `AMBIGUOUS` |
| `UNSUPPORTED` | `REJECTED` |

### 4.1 Provenance / presence mapping

| Upstream signal | `provenance` | `presence` |
|---|---|---|
| Explicit mention in claim | `EXPLICIT_TEXT` | `EXPLICIT` |
| Implicit / context mention (LLM `certainty=IMPLICIT` or context scope) | `IMPLICIT_CONTEXT` | `IMPLICIT` |
| Ambiguous / inferred (LLM `certainty=AMBIGUOUS`, baseline `territory_status=INFERRED`) | `INFERRED` | `IMPLICIT` |
| Missing / defaulted (baseline `territory_status=MISSING`) | `DEFAULTED` | `MISSING` |

Adapters must not force `EXPLICIT_TEXT` when upstream encodes implicit/inferred certainty.

## 5. Mapping — Baseline dict → ClaimSpecification

| Baseline | Spec |
|---|---|
| `identity.text` | `original_text` |
| `subject.indicator` | `indicator.original_label` (+ canonical if known) |
| `subject.territory_main` | `territories[0]` |
| `subject.population` | `populations[0]` |
| `time.*` | `time_period` |
| `time.frequency` | `expressed_frequency` |
| `measures[]` by `role` | `claimed_quantity` / `reference_quantities` (§3) |
| `operation.{type,direction,polarity}` | `statistical_operation` (+ direction in canonical_value / alternatives) |
| `modifiers.adjustments` | `adjustment` |
| `status.answerability` | `parse_status` (§4) |

## 6. Mapping — LLM ClaimParseResult → ClaimSpecification

| LLM | Spec |
|---|---|
| `indicators[0]` | `indicator` (extras → `alternatives` / `ambiguities`) |
| `populations` | `populations` |
| `territories` | `territories` |
| `time_expressions` | merge into single `time_period` (multi → ambiguity) |
| `measures[]` by `role` | `claimed_quantity` / `reference_quantities` |
| `operation` | `statistical_operation` |
| `comparisons` | `comparison` (+ extras in alternatives) |
| `frequency` | `expressed_frequency` |
| `adjustment` | `adjustment` |
| `ambiguities` / `missing_context` | `ambiguities` / status |
| `parse_status` | §4 |

## 7. Removed legacy fields

Do **not** reintroduce as public Spec API:

- `indicators[]`, `measures[]`, `time_expressions[]`, `operation` (plural/mention style)
- `CanonicalIndicator`, `CanonicalMentionBase`, `SourceScope`, `CanonicalTimeExpression`
- top-level Spec `unit` (unit lives on `ClaimedQuantity`)

## 8. Adapters

| Function | Module |
|---|---|
| `baseline_dict_to_claim_specification` | `src/parser/adapters/baseline_to_canonical.py` |
| `llm_result_to_claim_specification` | `src/parser/adapters/llm_to_canonical.py` |

Parsers keep their internal formats; only adapters produce `ClaimSpecification`.
