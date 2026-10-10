# Session 01 — Executable Truth Audit

**Date:** 2026-10-10  
**Repo:** https://github.com/BeediGoua/StatCheck  
**Auditor mode:** read-only on production code; allowed to create this file + `PROJECT_STATUS.md` only.

---

## 1. Commands executed

```text
git status
git branch --show-current
git rev-parse HEAD
git log -5 --oneline

# pytest not on global PATH (Python 3.14)
python -m pytest --collect-only -q   # → No module named pytest

# uv created .venv from pyproject (49 packages); pytest not a project dep
uv run pytest --collect-only -q      # → Failed to spawn pytest

# Audit-only installs into .venv (NOT committed; NOT added to pyproject)
uv pip install pytest pydantic scipy openai
uv pip install dateparser instructor

uv run --with pytest python -m pytest --collect-only -q
uv run --with pytest python -m pytest tests src/evaluation/tests src/fusion/tests --ignore=scratch --collect-only -q
uv run --with pytest python -m pytest tests src/evaluation/tests src/fusion/tests --ignore=scratch --continue-on-collection-errors --collect-only -q
uv run --with pytest python -m pytest tests/test_lot7.py tests/test_postgres_e2e.py -q --tb=line
uv run --with pytest python -m pytest tests/parser/llm tests/test_lot7.py -q --tb=line
uv run --with pytest python -m pytest tests/test_postgres_e2e.py -q --tb=line
```

Also inspected (read/grep, not executed as full pipelines):  
`src/parser/**`, `src/fusion/**`, `src/evaluation/**`, `src/providers/insee_bdm.py`, `src/ingestion/**`, `src/engine/calculator.py`, `src/models/**`, `src/db/**`, `src/database/**`, `scripts/etape_{4,5,6,7}/**`, `scripts/verify_mvp.py`, `scripts/test_r1_pipeline.py`, `data/corpus/pilotes_20.json`, `pyproject.toml`, `requirements-e2e.txt`, `docker-compose.yml`, `main.py`.

---

## 2. Results — git snapshot

| Item | Value |
|---|---|
| Branch | `main` |
| HEAD | `a2f7bfcbc346141c93b732abfffb8437ca499d39` |
| Tip message | Architecture R1 : cible V1 |
| Recent | dabf11f SDMX metadata; 7562f37 search engine; a0527c1 claim parsing; d1b5a04 constrained LLM |
| Dirty tracked | `src/db/__pycache__/database.cpython-314.pyc` only |
| Untracked important | `scripts/test_r1_pipeline.py` (MagicMock R1 smoke) |
| Created by audit | `.venv/` (local), `PROJECT_STATUS.md`, this file |

Nothing was deleted or force-reset during the audit itself.

**Post-audit repository hygiene (Session 01.5):** tracked `__pycache__` / `*.pyc` and regenerable `.cache/bdm/` were untracked; `.gitignore` updated; `scripts/test_r1_pipeline.py` moved to `scripts/demos/mock_r1_resolution_demo.py` with an explicit MOCK/DEMO header. No production code changed. Canonical CONTRACT_DRIFT collection errors remain intentional Session-02 starting points.

---

## 3. Results — test collection & execution

### 3.1 Collection (full tree, first successful collect after pytest install)

- **13 tests collected**
- **12 collection ERRORs** (scratch, scripts, evaluation, fusion, llm, regression)

Notable first-pass errors:

| Module | Essential cause | Category |
|---|---|---|
| `scratch/test_qwen.py` | `instructor` missing | EXTERNAL_DEPENDENCY |
| `scratch/test_retry.py` | `instructor` missing | EXTERNAL_DEPENDENCY |
| `scratch/test_validators.py` | `dateparser` missing | EXTERNAL_DEPENDENCY |
| `scripts/test_baseline.py` | `spacy` missing | EXTERNAL_DEPENDENCY |
| `src/evaluation/run_final_test.py` | `CanonicalMentionBase` missing | CONTRACT_DRIFT |
| `src/evaluation/tests/test_router.py` | `CanonicalIndicator` missing | CONTRACT_DRIFT |
| `src/evaluation/tests/test_scorer.py` | `SourceScope` missing | CONTRACT_DRIFT |
| `src/fusion/tests/test_fusion.py` | `SourceScope` missing | CONTRACT_DRIFT |
| `tests/parser/llm/test_post_validators.py` | `dateparser` missing | EXTERNAL_DEPENDENCY |
| `tests/parser/llm/test_prompt.py` | `instructor` missing | EXTERNAL_DEPENDENCY |
| `tests/parser/llm/test_schemas.py` | basename clash with `scratch/test_schemas.py` | ENVIRONMENT / layout |
| `tests/test_regression_c3.py` | `CanonicalIndicator` missing | CONTRACT_DRIFT |

### 3.2 Collection (core paths, after dateparser+instructor, `--continue-on-collection-errors`)

- **21 tests collected**
- **4 collection ERRORs** — all CONTRACT_DRIFT on canonical mentions API

### 3.3 Execution

| Command scope | PASS | FAIL | ERROR | SKIP |
|---|---|---|---|---|
| `tests/parser/llm` + `tests/test_lot7.py` | 14 | 0 | 0 | 3 |
| `tests/test_postgres_e2e.py` | 0 | 0 | 4 | 0 |

- Lot7 unit tests (RRF, reranker, nDCG/HNWR): **all passed** (algorithm code paths with in-memory / script helpers).
- LLM schema + post-validator unit tests: **passed** after installing `dateparser`/`instructor`.
- Prompt tests: **skipped** (`@pytest.mark.skip` — need Ollama).
- Postgres E2E: **ERROR at setup** — `psycopg2.OperationalError: Connection refused` on `localhost:5432`. Category: **ENVIRONMENT** (docker-compose DB not running). Not used to claim retrieval broken.

**No obsolete test was edited to pass.**

---

## 4. Errors & classifications (detail)

### CONTRACT_DRIFT (P0)

Consumers import a **mention-style** canonical API that is **not present** in current `src/parser/canonical.py`:

Missing symbols referenced by tests/prod:

- `CanonicalIndicator`, `CanonicalTerritory` (as mention type), `CanonicalTimeExpression`
- `CanonicalMentionBase`, `SourceScope`
- Fields: `indicators`, `time_expressions`, `operation`, `measures` with `value`/`source_text`/`origin`/`offsets`

Current Lot-8 `CanonicalParseResult` fields:

- `indicator`, `populations`, `territories`, `time_period`, `expressed_frequency`, `unit`, `expected_dimensions`, `statistical_operation`, `comparison`, `parse_status`, `warnings`
- Requires `claim_id`, `original_text`
- Measure uses `numeric_value`, not legacy `value`

**Verdict:** production fusion/router/scorer are **BROKEN at import** relative to current canonical. Tests that encode the old contract are **OBSOLETE relative to Lot-8 file** OR the Lot-8 rewrite is the breaking change — either way the repo does not have one coherent contract.

### ENVIRONMENT

- Global `pytest` missing; project does not declare pytest.
- Postgres not running → E2E suite ERROR.
- `spacy` still not installed → baseline script collection still blocked if attempted without it.

### EXTERNAL_DEPENDENCY (declared deps incomplete)

Imports in `src/` without pyproject entry (verified by reading `pyproject.toml` + imports):

| Package | Example import sites |
|---|---|
| pydantic | `canonical.py`, LLM schemas, `sdmx_selection.py`, … |
| openai / instructor | `openai_client.py`, `retry_policy.py` |
| spacy | `document_analyzer.py` |
| dateparser | `baseline/extractors/time.py` |
| pandas / pyarrow | `observation_ingester.py` |

Transitive present via sentence-transformers: numpy, scipy (not first-class declared).

### MOCK (evaluation scientific invalidity)

See section 6.

---

## 5. Files inspected (inventory)

### Entry points (real)

No `[project.scripts]`. Executable surface = `python path/to/script.py`.

| Role | Path |
|---|---|
| Stub | `main.py` |
| Baseline smoke | `scripts/test_baseline.py`, `scripts/evaluate_baseline.py` |
| Eval | `src/evaluation/run_baseline_eval.py`, `run_llm_eval.py`, `select_v1.py`, `run_final_test.py`, … |
| Ingestion | `scripts/run_*_ingestion.py`, snapshot scripts |
| Retrieval Lot7 | `scripts/etape_7/01_init_schema.py` … `03_run_benchmark.py`, `evaluate_retrieval.py` |
| Calc smoke | `scripts/verify_mvp.py` |
| R1 mock | `scripts/test_r1_pipeline.py` (untracked) |

### Component notes

| Component | Main file | In | Out | PG | INSEE | LLM | Status |
|---|---|---|---|---|---|---|---|
| Baseline | `baseline_parser.py` | text | legacy nested dict | no* | no | no | IMPLEMENTED |
| LLM | `llm_parser.py` + schemas | envelope | `ClaimParseResult` | no | no | yes | IMPLEMENTED |
| Canonical | `canonical.py` | — | Lot-8 slots | no | no | no | IMPLEMENTED but incompatible |
| Fusion | `fusion/engine.py` | 2× Canonical | Canonical + log | no | no | no | BROKEN import / PARTIAL logic |
| Router | `evaluation/router.py` | Canonical + text | trigger dict | no | no | no | BROKEN import |
| Scorer | `evaluation/scorer.py` | pred/gold Canonical | metrics | no | no | no | BROKEN import |
| Retrieval scripts | etape_5/6/7 | query / docs | ranked datasets | yes (real path) | no | embeddings local | IMPLEMENTED + DEMO modes |
| Resolvers | `orchestrator.py` | top-k dicts + dims | status + keys | yes | fallback | no | PARTIAL / mismatch |
| Provider | `insee_bdm.py` | idbank / dims | observations | cache files | yes | no | IMPLEMENTED |
| Calculator | `calculator.py` | observations + periods | float | no | no | no | IMPLEMENTED |
| Verdict | — | — | — | — | — | — | TODO |

\*Baseline may use SQLAlchemy matchers in some validators/resolvers when wired.

---

## 6. Schema drift (full matrix)

| Concept | Canonical Lot-8 | Baseline dict | LLM `ClaimParseResult` | Fusion | C3Router | Scorer | Gold (`pilotes_20`) | SDMX |
|---|---|---|---|---|---|---|---|---|
| Indicator | `indicator` | `subject.indicator` | `indicators[]` | comment/stub `indicators` | `.indicators` | `.indicators` | `subject.indicator` | via dataflow / dims |
| Population | `populations[]` | `subject.population` | `populations[]` | stub | — | `.populations` | `subject.population` | dims |
| Territory | `territories[]` slots | `subject.territory_*` | `territories[]` | fuse measures only | `.territories` + status | `.territories` | `subject.territory_main` | GEO codes |
| Time | `time_period` | `time` | `time_expressions[]` | stub | `.time_expressions` | `.time_expressions` | `time` | `time_window` |
| Operation | `statistical_operation` | `operation` | `operation` | — | `.operation` | — | `operation` | `aggregation_operation` UNRESOLVED only |
| Measure | `numeric_value` / `unit` slot | `measures[]` + roles | `measures[]` | `.measures` | `.measures` | `.measures` | singular `measure` | obs values later |
| Status | `parse_status` | `status.answerability` | `parse_status` enum | sets COMPLETE/… | triggers on statuses | silent errors | `answerability` | plan `status` |
| Identity | `claim_id`+`original_text` | `identity` | envelope | empty ctor in legacy tests | — | — | `claim_id` | `claim_id` + snapshot |

**Conclusion:** at least three incompatible families coexist; fusion/router/scorer/tests still speak family “legacy mentions”; Lot-8 file and R1 docs speak “slots”; gold speaks “baseline nested”; LLM speaks “mention lists with different field names”.

---

## 7. Mocks / historical metrics

### REAL IMPLEMENTATION

- RRF function, deterministic reranker rules, nDCG/HNWR helpers (covered by `test_lot7`).
- Catalog/structure/observation ingesters (HTTP + DB/parquet) — code present; **not re-run** this session → not VALIDATED here.
- `InseeBdmProvider`, `Calculator` — code present.
- Resolver modules (alias, joint combo, availability cascade, time, defaults) — code present with known bugs.

### PROTOTYPE

- Fusion: only measures fused; other entity types commented as future; `_apply_post_validators` = `pass`.
- `SDMXSelectionPlan`: schema without producer (`SDMXSelectionPlan(` appears only as class definition).

### MOCK / DEMO

| Location | Behavior |
|---|---|
| `select_v1.py` | `golds = baselines`; McNemar vectors all `True`; `best_arch = "C3"` forced; ADR text invents latency/McNemar story; config hash of `b"V1_FINAL_CONFIG"` |
| `run_final_test.py` | `random.seed(42)`; success iff `random() < 0.75`; gold/pred are synthetic `CanonicalMeasure` objects incompatible with current Canonical ctor; fake `durations_ms`; no call to real parsers |
| etape_5 optimize | mock lexical/vector rank lists |
| etape_6 `demo_reranker` | hard-coded candidates |
| etape_4 embeddings | mock fallback vectors |
| `test_r1_pipeline.py` | MagicMock session |
| `manifest_builder.py` | placeholder SHA strings |
| `run_llm_eval.py` | TODO skips real pydantic validation (`validated_data = parsed_json.copy()`) |

### HISTORICAL

- `evaluation/releases/v1-final-test/**` and ADR narratives derived from the above mocks → **not scientific**.

### TODO

- Verdict producer / proof verification module.
- Wired parse → retrieval → resolve → fetch → calc → verdict.
- XML stub in `scripts/etape_1b/fetch_real_catalog.py` (`pass`).

---

## 8. External dependencies & environment

- **docker-compose.yml:** Postgres 16 + pgvector only (`statcheck_dev_db`).
- **pyproject.toml deps:** alembic, psycopg2-binary, requests, sentence-transformers, sqlalchemy.
- **requirements-e2e.txt:** subset of the above (no pydantic/openai/spacy/pandas).
- **Audit session local installs:** pytest, pydantic, openai, dateparser, instructor (and uv sync of declared deps into `.venv`). These were **not** written into project dependency files.

INSEE / LLM / PG were **not** required for the 14 unit PASSes; PG absence caused 4 ERRORs; Ollama absence caused 3 SKIPs.

---

## 9. INSEE / SDMX audit notes

| Concern | Finding |
|---|---|
| Catalogue / structures / dims / modalities | IMPLEMENTED via ingesters |
| Series + IDBANK | IMPLEMENTED in observation path (`Series.external_id`) |
| Available series index | Model `AvailableSeriesKey` + snapshot scripts; comments still mention mock series in places |
| Availability checker | Queries `Series` with `snapshot_id` / `series_key` — **columns absent** on `Series` (BUG / CONTRACT_DRIFT vs `AvailableSeriesKey.ordered_key`) |
| Defaults | `default_policy_manager` reads `policy.target_code`; model field is `target_modality_code` (BUG) |
| Observations | Parquet under `data/normalized/…` — IMPLEMENTED; deps undeclared |
| Hashes | `raw_hash` written; normalized/business hashes incomplete |
| Provenance / selection plan | Contracts exist; **no end-to-end producer** of `SDMXSelectionPlan` |
| Network errors | `SDMXNetworkError` distinguished from missing series — IMPLEMENTED in checker |
| Ambiguities | `TOO_AMBIGUOUS` / combo bound — logic present; status machine not fully emitted |

---

## 10. End-to-end conclusion

**No executable automatic path today** from unknown claim text to calibrated verdict.

```text
Parser                 IMPLEMENTED (env gaps)
Parser → Canonical     BROKEN (no shared adapter / dual schemas)
Canonical → Retrieval  NOT WIRED
Retrieval              IMPLEMENTED (PG); unit algos TESTED; PG E2E NOT VERIFIED
Retrieval → Resolver   PARTIAL / NOT WIRED from parse
Resolver               PARTIAL (+ ORM mismatches)
Resolver → Provider    NOT WIRED (no selection-plan producer)
Provider               IMPLEMENTED
Provider → Calculator  PARTIAL (hardcoded idbanks in verify_mvp)
Calculator             IMPLEMENTED
Calculator → Verdict   TODO
```

---

## 11. Uncertainties (explicit)

- Whether Lot-7 Postgres benchmarks in `docs/phase 3/*` were run on real gold quality — **NOT RE-EXECUTED**; unit tests alone do not VALIDATE business retrieval.
- Whether `verify_mvp.py` still matches live INSEE revisions — **NOT RUN** this session (would need network).
- Whether untracked `scripts/test_r1_pipeline.py` was intended as committed smoke — present on disk, MagicMock only.
- Exact intended winner between Lot-8 slot canonical vs legacy mention canonical — code conflict unresolved; docs may claim either.

---

## 12. Conclusion

At commit `a2f7bfc`, StatCheck is a set of **partially strong islands** (baseline/LLM parsing code, Lot-7 retrieval algorithms, INSEE ingestion/provider, calculator) sitting on a **broken semantic spine** (canonical contract drift) with **scientifically invalid “final” evaluation scripts** and **no verdict stage**.

Documentation and historical release reports must not be treated as current validation.

---

## 13. Most informative next experiment

**One change only:** pick a single canonical schema; restore fusion/router/scorer (+ their tests) to import and construct it; add thin adapters from baseline dict and LLM `ClaimParseResult`.

**Success criterion:**  
`pytest src/fusion/tests src/evaluation/tests tests/test_regression_c3.py --collect-only` collects with 0 import errors, then those unit tests run (pass or fail for real logic reasons, not missing symbols).

That experiment restores the evaluation spine before any score chasing or retrieval tuning.
