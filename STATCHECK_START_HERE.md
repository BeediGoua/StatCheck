# StatCheck France — Start here

> **Snapshot documenté :** branche `main`, commit `bf55afcd7fbb0b7d2ea7f7c623ddd10ba6644cee`  
> (*harden ClaimSpecification with strict fields and rich quantities*)  
> **But :** carte d’entrée pour comprendre ce que StatCheck cherche à faire, ce qui est réel, et où lire la vérité runtime.

---

## 1. Règle absolue

**Documentation ≠ vérité du runtime.**

| Statut | Signification |
|---|---|
| `TARGET` | souhaité |
| `IMPLEMENTED` | code présent |
| `TESTED` | test exécuté avec succès |
| `VALIDATED` | démontré sur données/benchmark appropriés |
| `MOCK` | simulation |
| `BROKEN` | ne marche pas au commit concerné |
| `TODO` | absent |

Source de vérité prioritaire :

1. [`PROJECT_STATUS.md`](PROJECT_STATUS.md)
2. [`docs/audit/session_01_executable_truth.md`](docs/audit/session_01_executable_truth.md)
3. le code + les tests

`ARCHITECTURE.md` / `README.md` décrivent surtout l’intention historique.

---

## 2. StatCheck en une phrase

Transformer une affirmation statistique en **preuve exécutable** (ou abstention) à partir de données officielles :

```text
Claim
  → ClaimSpecification
  → Retrieval dataset
  → Résolution série / dimensions
  → Observations INSEE
  → Calcul déterministe
  → Verdict ou abstention
  → Provenance
```

```text
LLM = compréhension sémantique
Code déterministe = données + résolution + calcul + preuve
```

**Aujourd’hui :** pas encore de Golden Path E2E claim→verdict. Les briques existent surtout en îlots.

---

## 3. Où en est-on (sessions)

| Session | Objet | Statut |
|---|---|---|
| 1 | Audit executable truth | DONE — `PROJECT_STATUS.md` + audit |
| 1.5 | Hygiène repo (caches, `.gitignore`, mock R1 reclassé) | DONE |
| 2 | `ClaimSpecification` V1 + adapters + migration Router/Fusion/Scorer | DONE |
| 2.1 | Hardening contrat (`extra=forbid`, `ParseStatus`, quantités riches, provenance) | DONE |
| 3 | Fusion policy + AuthorityMatrix + post-validators + C3 route | DONE |
| **4** | **Micro-Gold V0 oracle (12 claims CANDIDATE)** | **DONE (CANDIDATE; not VALIDATED)** |
| 5+ | RetrievalService, SDMX plan, verdict, preuve… | plus tard |

### Session 2 — contrat unique du claim

Contrat normatif : [`docs/contracts/claim_specification_v1.md`](docs/contracts/claim_specification_v1.md)

```text
Baseline dict ──► baseline_to_canonical ──┐
                                          ├──► ClaimSpecification
LLM ClaimParseResult ──► llm_to_canonical ┘
                                          │
                     ┌────────────────────┼────────────────────┐
                     ▼                    ▼                    ▼
                  C3Router             Fusion               Scorer
```

Fichiers clés :

- `src/parser/claim_specification.py`
- `src/parser/adapters/baseline_to_canonical.py`
- `src/parser/adapters/llm_to_canonical.py`
- `src/parser/canonical.py` (re-export mince, **pas** l’ancien API mention)
- `src/evaluation/router.py`, `src/fusion/`, `src/evaluation/scorer.py`

Important : `claimed_quantity` / `reference_quantities` = ce que l’utilisateur **affirme**.  
Ce n’est **pas** une observation officielle ni une quantité calculée par StatCheck.

### Session 3 — fusion sémantique

Politique : [`docs/contracts/fusion_policy_v1.md`](docs/contracts/fusion_policy_v1.md)  
Audit : [`docs/audit/session_03_fusion_c3.md`](docs/audit/session_03_fusion_c3.md)

```text
Alignement (même mention) → Authority (qui gagne / conflit) → Post-validators → statut
C3 = CALL_LLM | BASELINE_ONLY  (pas l’answerability finale)
```

### Session 4 — Micro-Gold oracle

Contrat : [`docs/contracts/micro_gold_v0.md`](docs/contracts/micro_gold_v0.md)  
Données : [`data/gold/micro_gold_v0/micro_gold_v0.yaml`](data/gold/micro_gold_v0/micro_gold_v0.yaml)  
Audit : [`docs/audit/session_04_micro_gold.md`](docs/audit/session_04_micro_gold.md)

```text
12 claims MG001–MG012 (CANDIDATE)
→ answerability / ClaimSpec / dataset / série / obs / calcul / verdict
≠ VALIDATED système  (plusieurs idbanks BDM encore à pinner)
```

---

## 4. Par où commencer ?

### Comprendre l’état réel (15 min)

1. [`PROJECT_STATUS.md`](PROJECT_STATUS.md)
2. **Récits humains (recommandé) :** [`docs/sessions/README.md`](docs/sessions/README.md)
3. Audits techniques : [`docs/audit/`](docs/audit/)
4. Contrats : [`docs/contracts/claim_specification_v1.md`](docs/contracts/claim_specification_v1.md), [`fusion_policy_v1.md`](docs/contracts/fusion_policy_v1.md), [`micro_gold_v0.md`](docs/contracts/micro_gold_v0.md)

### Modifier le parsing / le contrat claim

1. `docs/contracts/claim_specification_v1.md`
2. `src/parser/claim_specification.py`
3. `src/parser/adapters/`
4. `src/parser/baseline/` et `src/parser/llm/` (formats internes legacy — ne pas les « fusionner » dans le Spec)
5. consommateurs : `src/fusion/`, `src/evaluation/router.py`, `src/evaluation/scorer.py`
6. tests : `tests/parser/test_claim_adapters.py`, `tests/test_regression_c3.py`, `src/fusion/tests/`, `src/evaluation/tests/`

### Données INSEE / retrieval (plus tard — pas Session 3)

1. `src/providers/insee_bdm.py`, `src/ingestion/`
2. `scripts/etape_5|6|7/` (algos + demos)
3. `src/parser/resolvers/`
4. Attention : résultats `select_v1.py` / `run_final_test.py` / `evaluation/releases/v1-final-test/` = **MOCK / non scientifiques**

---

## 5. Carte courte du dépôt

```text
StatCheck/
├── PROJECT_STATUS.md          Vérité exécutable (à lire en premier)
├── STATCHECK_START_HERE.md    Ce guide
├── docs/
│   ├── sessions/              Récits humains par session (lire ça)
│   ├── audit/                 Traces techniques par session
│   ├── contracts/             ClaimSpecification + fusion + micro_gold V0
│   └── …                      Docs historiques de phase
├── data/
│   └── gold/micro_gold_v0/    Oracle E2E CANDIDATE (Session 4)
├── src/
│   ├── parser/
│   │   ├── baseline/          Parser déterministe → dict legacy
│   │   ├── llm/               Parser LLM → ClaimParseResult
│   │   ├── adapters/          → ClaimSpecification
│   │   ├── claim_specification.py
│   │   └── resolvers/         SDMX / dimensions (PARTIAL)
│   ├── fusion/                Align + Authority + post-validators (Session 3)
│   ├── gold/                  Micro-Gold loader
│   ├── evaluation/            C3 router, scorer, reports (certains scripts MOCK)
│   ├── providers/             INSEE BDM
│   ├── ingestion/             Catalogue / structures / observations
│   ├── engine/                Calculator
│   ├── models/                ORM + contrats SDMX
│   ├── db/                    SQLAlchemy
│   └── database/              Schéma retrieval SQL
├── scripts/                   CLI historiques, demos, ingestion
│   └── demos/                 Ex. mock_r1_resolution_demo.py (MOCK explicite)
├── tests/
├── data/
├── alembic/
├── README.md / ARCHITECTURE.md   Intention / cible
└── main.py                    Stub (pas le pipeline)
```

---

## 6. Ce que ce fichier n’est pas

- une promesse que le pipeline E2E marche ;
- un benchmark ;
- un remplacement des tests ou de `PROJECT_STATUS.md`.

---

## 7. Maintenance

À chaque session structurante :

1. mettre à jour le **commit** en tête de ce fichier ;
2. ajuster le tableau des sessions ;
3. pointer les chemins exacts ;
4. ne jamais écrire `VALIDATED` sans expérience réelle ;
5. garder `PROJECT_STATUS.md` comme source de statut détaillée ;
6. écrire/mettre à jour un **récit** dans [`docs/sessions/`](docs/sessions/) (clair, peu technique) ;
7. garder/compléter l’**audit technique** dans [`docs/audit/`](docs/audit/).
