# Session 05.0 — Retrieval executable truth

**Date:** 2026-10-10  
**Scope:** establish what retrieval actually exists; classify mock vs real; attempt one live smoke query.  
**Out of scope:** new `RetrievalService`, Micro-Gold retrieval eval, Fusion/C3, SDMX.

**Récit humain :** [`docs/sessions/session_05_0_verite_du_retrieval.md`](../sessions/session_05_0_verite_du_retrieval.md)

---

## OBSERVATION

There is **no** `RetrievalService` (or equivalent) under `src/`.  
The hybrid retrieval stack lives as **Lot-7 scripts** plus two reusable algorithm modules and a SQL schema.

### Reconstructed pipeline (as coded)

```text
query_text
  → FTS SQL on search_documents.lexical_vector   (etape_7 execute_fts)
  → MiniLM encode query                           (sentence-transformers)
  → pgvector cosine ORDER BY embedding <=>        (etape_7 execute_vector)
  → RRF fusion                                    (etape_7 fuse_results; also etape_5 perform_rrf)
  → deterministic reranker                        (etape_6 apply_deterministic_reranker)
  → ranked dataset_id list (+ abstention)
```

### Component matrix

| Composant | Implémenté | Exécutable aujourd’hui | Vraies données | Tests | Décision |
|---|---:|---:|---:|---:|---|
| FTS SQL (`french_unaccent`) | oui | non (DB down) | prévu sur `search_documents` | e2e ERROR | reuse SQL pattern |
| Embedding encode | oui | oui (local model) | modèle local | non E2E | reuse MiniLM path |
| pgvector search | oui | non (DB down) | prévu | e2e ERROR | reuse SQL pattern |
| RRF | oui | oui (in-memory) | n/a (ranks) | lot7 8/8 | **reuse** |
| Reranker déterministe | oui | oui (in-memory) | n/a (dicts) | lot7 | **reuse** |
| Schema retrieval SQL | oui | non (DB down) | n/a | — | reuse + fix dim drift |
| Init schema `01_init` | oui | bloqué env | — | — | reuse |
| Ingest `02_ingest` + MiniLM | oui | bloqué env | JSON 222 datasets | — | reuse after DB up |
| Catalogue search JSON | oui (fichier) | oui (fichier) | 222 dataflows INSEE | — | reuse as seed |
| ORM CatalogIngester | oui | non testé ici | HTTP INSEE → `datasets` | — | **autre monde** vs search |
| `RetrievalCandidate` model | oui | n/a | n/a | — | contrat Lot7→8 only |
| RetrievalService | **non** | — | — | — | TODO |

### File inventory (exact)

| File | Role | Status |
|---|---|---|
| [`src/database/schema_retrieval.sql`](../../src/database/schema_retrieval.sql) | FTS config, `search_documents`, `entity_embeddings`, `vector(1024)` | IMPLEMENTED; dim drift vs runtime |
| [`scripts/etape_7/01_init_schema.py`](../../scripts/etape_7/01_init_schema.py) | Creates DB + applies schema SQL | IMPLEMENTED; ENVIRONMENT_BLOCKED |
| [`scripts/etape_7/extract_real_datasets.py`](../../scripts/etape_7/extract_real_datasets.py) | Builds `data/catalog/search_documents_real.json` | IMPLEMENTED (artifact present) |
| [`scripts/etape_7/02_ingest_real_data.py`](../../scripts/etape_7/02_ingest_real_data.py) | Load JSON, ALTER vector→384, MiniLM embed, UPDATE rows | IMPLEMENTED; ENVIRONMENT_BLOCKED |
| [`scripts/etape_7/03_run_benchmark.py`](../../scripts/etape_7/03_run_benchmark.py) | Live FTS+vector+RRF+rerank latency bench | IMPLEMENTED; ENVIRONMENT_BLOCKED |
| [`scripts/etape_7/evaluate_retrieval.py`](../../scripts/etape_7/evaluate_retrieval.py) | `main` = live PG eval; also `mock_fts_search` / `mock_vector_search` | IMPLEMENTED + MOCK helpers; ENVIRONMENT_BLOCKED for main |
| [`scripts/etape_7/analyze_vector_latency.py`](../../scripts/etape_7/analyze_vector_latency.py) | EXPLAIN ANALYZE vector scan | IMPLEMENTED; ENVIRONMENT_BLOCKED |
| [`scripts/etape_5/hybrid_search.py`](../../scripts/etape_5/hybrid_search.py) | `perform_rrf` (pure); `optimize_rrf_parameters` dummy | IMPLEMENTED + DEMO |
| [`scripts/etape_6/deterministic_reranker.py`](../../scripts/etape_6/deterministic_reranker.py) | `apply_deterministic_reranker`; `demo_reranker` mock | IMPLEMENTED + DEMO; TESTED |
| [`scripts/etape_4/generate_embeddings.py`](../../scripts/etape_4/generate_embeddings.py) | Prototype BGE-M3 / hardcoded 2 docs / mock vector | DEMO / MOCK / UNUSED by etape_7 |
| [`src/models/retrieval_candidate.py`](../../src/models/retrieval_candidate.py) | Pydantic TopK contract | IMPLEMENTED; UNUSED by scripts |
| [`src/evaluation/retrieval_metrics.py`](../../src/evaluation/retrieval_metrics.py) | recall/MRR/nDCG helpers | IMPLEMENTED; separate from etape_7 metrics |
| [`src/ingestion/catalog_ingester.py`](../../src/ingestion/catalog_ingester.py) | SDMX dataflow → ORM `Dataset` | IMPLEMENTED; **not** wired to `search_documents` |
| [`tests/test_lot7.py`](../../tests/test_lot7.py) | Unit RRF/reranker/nDCG on synthetic lists | TESTED (8 passed this session) |
| [`tests/test_postgres_e2e.py`](../../tests/test_postgres_e2e.py) | Extensions, FTS, vector dim 384 | ENVIRONMENT_BLOCKED (4 ERROR connection refused) |
| Alembic versions | Catalogue/structure/gold tables | **No** `search_documents` migration |
| [`docker-compose.yml`](../../docker-compose.yml) | `pgvector/pgvector:pg16` | IMPLEMENTED; daemon not running |

### Answers to the 16 audit questions

1. **FTS code?** SQL in `03_run_benchmark.execute_fts` / `evaluate_retrieval.main.execute_fts` — `ts_rank_cd(lexical_vector, to_tsquery('french_unaccent', …))` on `search_documents`. Trigger build in `schema_retrieval.sql`.
2. **Vector search?** Same scripts: `ORDER BY embedding <=> %s::vector`. Also SQL function `search_vectorial`.
3. **Embeddings computed where?** Production path: `02_ingest_real_data.py` (`SentenceTransformer.encode`). Prototype: `etape_4/generate_embeddings.py` (not used by ingest).
4. **Which embedding model?** **Live path:** `paraphrase-multilingual-MiniLM-L12-v2` (384-d). **Schema/etape_4:** documents `BAAI/bge-m3` / `vector(1024)` — **drift**.
5. **RRF?** `scripts/etape_5/hybrid_search.perform_rrf` (k=60, list-of-ids). **Also duplicated** in etape_7 `fuse_results` (k=30, weight vector 1.25, dict payloads). Not the same API.
6. **Reranker?** `scripts/etape_6/deterministic_reranker.apply_deterministic_reranker` — hard rejects + lexicographic sort; needs `claim_context` dict.
7. **Scripts with real DB?** `01_init`, `02_ingest`, `03_run_benchmark`, `evaluate_retrieval.main`, `analyze_vector_latency`, `test_postgres_e2e`.
8. **Scripts with mock?** `etape_4`, `optimize_rrf_parameters`, `demo_reranker`, `mock_fts_search`/`mock_vector_search` (helpers; main path is real).
9. **PostgreSQL schema expected?** `schema_retrieval.sql` tables + extensions `vector`/`unaccent` + `french_unaccent`. Default URL `postgresql://postgres:postgrespassword@localhost:5432/statcheck`.
10. **Migrations match code?** **No** — retrieval tables are **not** in Alembic; applied by `01_init_schema.py`. ORM catalogue is separate Alembic world.
11. **Can we start DB and search today?** **No.** Docker installed (29.6.1) but **Docker Desktop engine not running**; localhost:5432 connection refused → **ENVIRONMENT_BLOCKED**.
12. **INSEE catalogue present/ingestible?** Search index seed **present**: `data/catalog/search_documents_real.json` (**222** datasets, includes `CHOMAGE-TRIM-NATIONAL`). ORM catalogue path exists but is a different store.
13. **Query format today?** Free-text `query_text` + for rerank a `claim_context` dict: `required_indicator`, `required_dimensions`, `forbidden_sources`.
14. **ClaimSpecification fields usable later?** `indicator`, `expected_dimensions` / dimension-like slots, `territories`, `populations`, `expressed_frequency`, `adjustment`, plus `original_text` as lexical query. No adapter today.
15. **Clean reusable service class?** **No.** Closest reusable units: `perform_rrf`, `apply_deterministic_reranker`, SQL snippets, `RetrievalCandidate` schema.
16. **Dispersed scripts only?** **Yes** for the integrated pipeline.

---

## RUNTIME TEST

| Step | Command / action | Result |
|---|---|---|
| Docker CLI | `docker --version` | OK 29.6.1 |
| Compose | `docker compose up -d db` | **FAIL** — cannot connect to `dockerDesktopLinuxEngine` pipe |
| Postgres TCP | `psycopg2.connect(...localhost:5432/statcheck)` | **FAIL** — Connection refused |
| Unit algos | `.venv\Scripts\python.exe -m pytest tests/test_lot7.py -q` | **8 passed** |
| E2E PG | `pytest tests/test_postgres_e2e.py -q` | **4 ERROR** setup (connection refused) |
| Catalogue seed | count `search_documents_real.json` | **222** rows; `CHOMAGE-TRIM-NATIONAL` present |

### Smoke query (intended, not executed live)

```text
query = "taux de chômage au sens du BIT"
```

**Not run** against Postgres (ENVIRONMENT_BLOCKED).  
Would require, once Docker is up:

```text
docker compose up -d db
.venv\Scripts\python.exe scripts/etape_7/01_init_schema.py
.venv\Scripts\python.exe scripts/etape_7/02_ingest_real_data.py   # needs MiniLM download first time
# then evaluate_retrieval.main or ad-hoc execute_fts/execute_vector/fuse_results
```

---

## RESULTS

| What | Outcome |
|---|---|
| Algorithm layer (RRF, reranker, nDCG helpers) | Works offline; TESTED |
| Integrated hybrid search on real DB | **Not executable this session** — ENVIRONMENT_BLOCKED |
| Embedding model consistency | **Broken contract** between schema (1024/BGE) and etape_7 (384/MiniLM) |
| Service boundary ClaimSpec → retrieval | Missing |
| Dual catalogue | ORM `datasets` ≠ retrieval `search_documents` |

---

## MOCK VS REAL

| Artifact | Classification |
|---|---|
| `perform_rrf` / `apply_deterministic_reranker` | REAL algorithms; TESTED on synthetic inputs |
| `test_lot7.py` | TESTED helpers — **not** production retrieval evidence |
| `mock_fts_search` / `mock_vector_search` | MOCK (word overlap / Jaccard) |
| `demo_reranker` / `optimize_rrf_parameters` | DEMO |
| `etape_4/generate_embeddings.py` | DEMO/MOCK (hardcoded docs; optional fake vectors) |
| `03_run_benchmark` / `evaluate_retrieval.main` SQL | REAL path (when DB up) — **not VALIDATED** this session |
| Historical lot7 latency/nDCG docs | Not treated as scientific evidence here |
| `search_documents_real.json` | REAL extracted catalogue seed (file), not yet proven loaded in PG |

---

## SCHEMA / ENVIRONMENT ISSUES

1. **ENVIRONMENT_BLOCKED:** Docker Desktop engine stopped → no `pgvector` container → no smoke.
2. **Schema drift:** `schema_retrieval.sql` defaults `vector(1024)`; `02_ingest_real_data.py` ALTERs to `vector(384)` for MiniLM; e2e asserts 384; etape_4 still documents BGE-M3/1024.
3. **No Alembic for retrieval tables** — schema applied by side script only.
4. **Duplicated RRF** with different knobs (`k=60` vs `k=30`, different input shapes).
5. **Two catalogues:** Alembic/ORM ingestion vs `search_documents` JSON ingest — not unified.
6. **No HNSW/IVFFlat** — exact scan (acceptable for ~222 rows; documented).

---

## CLAIMSPEC INTEGRATION GAP

| ClaimSpecification | Retrieval today |
|---|---|
| `original_text` | Could feed `query_text` |
| `indicator.canonical_value` / label | Closest to `claim_context.required_indicator` (today often dataset_id in gold JSON) |
| `expected_dimensions` / populations / territories | Closest to `required_dimensions` (string list matching metadata.dimensions) |
| `expressed_frequency`, `adjustment` | Usable as soft filters later — **unused** |
| `claimed_quantity` | Not a retrieval input |
| — | No adapter; scripts expect free text + hand-built `claim_context` |

Future boundary (not implemented): ClaimSpec → `{query_text, claim_context}` → ranked `RetrievalTopK`.

---

## DECISION

```text
C. REUSE CORE ALGORITHMS BUT REBUILD INTEGRATION LAYER
```

**Evidence:**

- Reusable cores exist and are unit-tested: `perform_rrf`, `apply_deterministic_reranker`, FTS/pgvector SQL patterns, MiniLM ingest script, 222-row catalogue seed.
- There is **no** clean service; pipeline is script-dispersed; RRF is duplicated; embedding dim/model contracts conflict; ORM catalogue ≠ search index.
- Live path is **ENVIRONMENT_BLOCKED** today (not algorithmically absent) — once DB is up, the next work is still integration cleanup, not “just wrap as-is” (rules out A) and more than a one-line fix (rules out pure B). D would overstate: the path is coded and close, but not currently runnable here.

---

## NEXT EXPERIMENT (single)

```text
Start Docker Desktop → docker compose up -d db → 01_init_schema.py → 02_ingest_real_data.py
→ one smoke query "taux de chômage au sens du BIT" (FTS+vector+RRF)
→ record top dataset_ids from real search_documents rows.
```

Only after that smoke succeeds: decide whether Session 5.1 is a thin `RetrievalService` wrapper around cleaned scripts, or catalogue unification first.

**STOP.** No Session 5.1 in this session.
