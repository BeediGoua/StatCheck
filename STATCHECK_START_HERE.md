# StatCheck France — Start here

> **Snapshot documenté :** branche `main`, commit `5aaf667b978c299ad7ffb3f2b7ad8df3c268d874`  
> (*ClaimSpecification V1 and baseline/LLM adapters*)  
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
| **2.1** | **Hardening contrat** (`extra=forbid`, `ParseStatus`, quantités riches, provenance) | **DONE** |
| 3 | Réparer réellement Fusion + C3 + post-validations | NEXT |
| 4+ | Micro-gold, retrieval service, SDMX plan, verdict, preuve… | plus tard |

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

---

## 4. Par où commencer ?

### Comprendre l’état réel (15 min)

1. [`PROJECT_STATUS.md`](PROJECT_STATUS.md)
2. [`docs/audit/session_01_executable_truth.md`](docs/audit/session_01_executable_truth.md)
3. [`docs/contracts/claim_specification_v1.md`](docs/contracts/claim_specification_v1.md)

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
│   ├── audit/                 Journal Session 1
│   ├── contracts/             ClaimSpecification V1
│   └── …                      Docs historiques de phase
├── src/
│   ├── parser/
│   │   ├── baseline/          Parser déterministe → dict legacy
│   │   ├── llm/               Parser LLM → ClaimParseResult
│   │   ├── adapters/          → ClaimSpecification
│   │   ├── claim_specification.py
│   │   └── resolvers/         SDMX / dimensions (PARTIAL)
│   ├── fusion/                Fusion Spec (post-validators encore stub)
│   ├── evaluation/            Router, scorer, reports (certains scripts MOCK)
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
5. garder `PROJECT_STATUS.md` comme source de statut détaillée.
