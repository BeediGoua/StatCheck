# Session 04.1 — Micro-Gold series truth hardening

**Date:** 2026-10-10  
**Scope:** verify/correct INSEE dataset + idbank + dimensions + observations for MG001–MG012.  
**Out of scope:** RetrievalService, SDMX plan, fusion/C3 tuning.

**Récit humain :** [`docs/sessions/session_04_1_verite_de_serie.md`](../sessions/session_04_1_verite_de_serie.md)

**Addendum 4.1bis (2026-10-10):** fermeture MG012 via idbank actif `010755537`.

---

## Verdict Session 4.1 (+ 4.1bis)

```text
DONE — tous les FOUND ont série+dims+obs CONFIRMED/CORRECTED
FIX NEEDED — corrections matérielles (dont MG012 idbank + dual vintage)
```

**Oracle de grounding ?** Oui pour les FOUND : chaque cas CONFIRMED/CORRECTED a un idbank BDM pinné (ou abstention volontaire MG004/MG005).  
`gold_status` reste **CANDIDATE**. Ne pas écrire VALIDATED.

---

## Matrice de vérification

| Claim | Dataset | Série/idbank | Dimensions | Obs | Statut |
|---|---|---|---|---|---|
| MG001 | OK CHOMAGE-TRIM-NATIONAL | OK `001688527` | OK FR-D976 / Q / SA / % | OK pub. 7.5 / 7.3 | **CONFIRMED** |
| MG002 | OK | OK `001688527` | OK | OK +0.2 pt | **CONFIRMED** |
| MG003 | OK | OK `001688527` | OK | OK rel. ~2.74 | **CONFIRMED** |
| MG004 | candidat OK | candidat `001688537` | under-25 (pas unique) | 19.0 candidat | **CONFIRMED** (abstention AMBIGUOUS) |
| MG005 | n/a | null | n/a | n/a | **CONFIRMED** (abstention INSUFFICIENT) |
| MG006 | OK IPC-2025 | OK `011814632` | OK FE / M / YoY / COICOP00 | OK 1.2 | **CORRECTED** |
| MG007 | OK IPC-2025 | OK `011814631` | OK FE / M / MoM | OK −1.0 | **CORRECTED** |
| MG008 | OK IPC-2025 | OK `011814632` | OK | OK 1.2 vs claim 1.0 | **CORRECTED** |
| MG009 | OK ESTIMATIONS-POPULATION | OK `001760077` | OK FE / A | CORRECTED 68851996 | **CORRECTED** |
| MG010 | OK ETAT-CIVIL | OK `001641601` (mensuel→somme) | OK FE / M | OK sum=643905 | **CORRECTED** |
| MG011 | OK pop | OK `001760077` | OK | CORRECTED Δ=213619 | **CORRECTED** |
| MG012 | OK CREATIONS-ENTREPRISES | OK `010755537` (succ. `001564301`) | OK FE / M / BRUTE / Ensemble | 12 mois 2025 ; SUM=**1165795** | **CORRECTED** |

---

## Corrections apportées

1. **IPC** — remplacement des handles fictifs `IPC_YOY_ENSEMBLE_FR` / null idbank par `011814632` (YoY) et `011814631` (MoM), dataset `IPC-2025` (base 2025, pas 2015).
2. **Population** — idbank `001760077` ; obs 2025 corrigée de 68 605 600 (table portrait) → **68 851 996** (BDM provisoire révisée). Claim « environ 68,6 M » reste SUPPORTED.
3. **MG011** — Δpop BDM **213 619** (plus 169 000 de l’ancienne table) ; toujours REFUTED vs 643 905 naissances.
4. **Naissances** — idbank mensuel France `001641601` ; somme 2025 = **643 905** (match Focus). Rejet de la série métropole seule `000067677`.
5. **Chômage** — métadonnées BDM confirmées (`REF_AREA=FR-D976`, CVS, ensemble). Snapshot publication **conservé** (7.5) malgré historique de révision (IR ultérieur 7.6 / BDM live 7.5+OBS_REV).
6. **MG012 (4.1bis)** — idbank actif `010755537` (« Ensemble - France - Données mensuelles brutes ») ; successeur documenté de `001564301` (série arrêtée, même libellé). Dual vintage : publication claim **1 165 800** / SIDE exact **1 165 795** vs BDM `annual_sum` **1 165 795**. `discrepancy_cause=CLAIM_ROUNDING`. Opération Gold `SUM`. Statut **CORRECTED** (pas CONFIRMED : libellé arrondi ≠ somme exacte).

### MG012 — mensuels BDM 2025 (`010755537`, LAST_UPDATE=2026-09-18)

| Période | Valeur | Flags |
|---|---|---|
| 2025-01 | 105 274 | A / DEF |
| 2025-02 | 95 051 | A / DEF |
| 2025-03 | 95 697 | A / DEF |
| 2025-04 | 97 861 | A / DEF |
| 2025-05 | 87 988 | A / DEF |
| 2025-06 | 93 835 | A / DEF |
| 2025-07 | 101 879 | A / DEF |
| 2025-08 | 80 456 | A / DEF |
| 2025-09 | 101 006 | A / DEF |
| 2025-10 | 116 385 | A / DEF |
| 2025-11 | 93 992 | A / DEF |
| 2025-12 | 96 371 | A / DEF |
| **SUM** | **1 165 795** | = SIDE exact ; claim arrondi 1 165 800 |

Écart claim arrondi vs somme : **−5** (`CLAIM_ROUNDING`). Un écart ~200 parfois cité n’apparaît **pas** sur le vintage inspecté (somme = SIDE exact).

---

## MG001–MG003 publication vs révision

| Source | 2025-Q2 |
|---|---|
| IR 8627586 (08/08/2025) — Gold snapshot | **7.5** |
| IR 8989990 table (plus tard) | 7.6 |
| BDM live `001688527` (inspecté 2026-10-10) | **7.5** (OBS_REV=1) |

Oracle MG001–MG003 = **publication snapshot**, pas « dernière valeur vue un jour ».

---

## Tests

```text
.venv\Scripts\python.exe -m pytest tests/gold/test_micro_gold_v0.py -q --tb=short
# → 13 passed (après 4.1bis)
```

## Stop

Ne pas démarrer Retrieval / Session 5 tant que ce verdict n’est pas accepté.
