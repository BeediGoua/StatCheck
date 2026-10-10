# Session 04 — Micro-Gold E2E V0 (oracle)

**Date:** 2026-10-10  
**Scope:** schema + 12 candidate cases + structural tests.  
**Out of scope:** RetrievalService, SDMX plan, C3/fusion tuning, full VALIDATED gold.  
**Récit humain :** [`docs/sessions/session_04_oracle_micro_gold.md`](../sessions/session_04_oracle_micro_gold.md)

## Scientific question

For MG001–MG012, can we document the expected chain claim → answerability → ClaimSpecification → INSEE grounding → observations → deterministic computation → verdict/abstention **independently of the runtime system**?

## Existing gold risks (read-only audit)

| Source | Risk | Session 4 action |
|---|---|---|
| `data/corpus/gold_validation.json` `val_006` | Query "Demandeurs d'emploi catégorie A" golded to `CHOMAGE-TRIM-NATIONAL` (BIT) | Anti-pattern; mirrored by **MG005** (INSUFFICIENT) |
| `pilotes_20` / `corpus_complet` / splits | Parse-slot gold only; answerability enums differ | Not copied into Micro-Gold |
| `evaluation/releases/v1-final-test/` | MOCK / non-scientific | Ignored |
| ORM `GoldAnnotation` | Useful vocab FOUND/AMBIGUOUS/NOT_FOUND | Not imported |

**No old gold label was reused as Micro-Gold truth.**

## Deliverables

| Artifact | Path |
|---|---|
| Contract | `docs/contracts/micro_gold_v0.md` |
| Data | `data/gold/micro_gold_v0/micro_gold_v0.yaml` |
| Loader | `src/gold/micro_gold_v0.py` |
| Tests | `tests/gold/test_micro_gold_v0.py` |

## Case summary

| ID | Answerability | Verdict | Manually verified |
|---|---|---|---|
| MG001 | FOUND | SUPPORTED | IR 8627586 snapshot 7.5% T2 2025; idbank `001688527`; revision caveat |
| MG002 | FOUND | SUPPORTED | POINT_CHANGE +0.2 from same publication |
| MG003 | FOUND | SUPPORTED | RELATIVE_CHANGE → Calculator 2.74 vs claim 2.7 |
| MG004 | AMBIGUOUS | INSUFFICIENT_EVIDENCE | "jeunes" not unique; 15-24=19% is candidate only |
| MG005 | INSUFFICIENT | INSUFFICIENT_EVIDENCE | BIT ≠ catégorie A |
| MG006 | FOUND | SUPPORTED | IR 8655430 YoY +1.2%; **BDM idbank not pinned** |
| MG007 | FOUND | SUPPORTED | IR 8655430 MoM −1.0%; idbank not pinned |
| MG008 | FOUND | REFUTED | Same YoY series, claimed 1.0 vs official 1.2 |
| MG009 | FOUND | SUPPORTED | Pop 68.6056M at 2025-01-01; idbank not pinned |
| MG010 | FOUND | SUPPORTED | Births 643905 (Focus 9017867); idbank not pinned |
| MG011 | FOUND | REFUTED | Δpop ≈169k ≠ births 643905 |
| MG012 | FOUND | SUPPORTED | Creations 1165800 (Première 8721354); idbank not pinned |

## What is assumed / still uncertain

1. **BDM idbanks** for IPC, population, births, business creation are **not** pinned — `series_id` is a publication-level handle; `review_status=NEEDS_HUMAN_REVIEW` for those cases.
2. Unemployment idbank `001688527` / youth candidate `001688537` taken from known series + user fixture; publication values verified on IR pages.
3. MG001/MG002 deliberately use **publication snapshot** (7.5 / 7.3), acknowledging later series revision risk (e.g. 7.6).
4. Micro-Gold remains `gold_status: CANDIDATE` — **not VALIDATED**.

## Decisions

- YAML single file for human auditability.
- `VALUE` on published YoY/MoM rates for IPC (not recomputed from raw index levels in V0).
- Calculator coherence tolerance = 0.05 absolute.
- Session 4 status: **PARTIAL toward VALIDATED**, **DONE for CANDIDATE oracle + structural tests**.

## Commands run

```text
.venv\Scripts\python.exe -m pytest tests/gold/test_micro_gold_v0.py -q --tb=short
# → 10 passed
```

## Next (Session 5+)

Only after human pin of remaining idbanks / acceptance of CANDIDATE as oracle:  
`ClaimSpecification → RetrievalService → SDMXSelectionPlan` evaluated against this set.
