# Session 04.1 — Micro-Gold series truth hardening

**Date:** 2026-10-10  
**Scope:** verify/correct INSEE dataset + idbank + dimensions + observations for MG001–MG012.  
**Out of scope:** RetrievalService, SDMX plan, fusion/C3 tuning.

**Récit humain :** [`docs/sessions/session_04_1_verite_de_serie.md`](../sessions/session_04_1_verite_de_serie.md)

---

## Verdict Session 4.1

```text
PARTIAL — il reste 1 cas non résolu (MG012)
FIX NEEDED — corrections matérielles sur MG006–MG011 (idbanks / observations)
```

**Oracle de grounding ?** Assez fiable pour chômage + IPC + population + naissances (FOUND CONFIRMED/CORRECTED avec idbank).  
**Pas encore DONE** tant que MG012 n’a pas d’idbank BDM national actif (séries Ensemble–France arrêtées dans le dataflow `CREATIONS-ENTREPRISES`).

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
| MG012 | OK SIDE / Première 2092 | **pas d’idbank BDM actif** | pub. FR / A | OK 1165800 | **UNRESOLVED** |

---

## Corrections apportées

1. **IPC** — remplacement des handles fictifs `IPC_YOY_ENSEMBLE_FR` / null idbank par `011814632` (YoY) et `011814631` (MoM), dataset `IPC-2025` (base 2025, pas 2015).
2. **Population** — idbank `001760077` ; obs 2025 corrigée de 68 605 600 (table portrait) → **68 851 996** (BDM provisoire révisée). Claim « environ 68,6 M » reste SUPPORTED.
3. **MG011** — Δpop BDM **213 619** (plus 169 000 de l’ancienne table) ; toujours REFUTED vs 643 905 naissances.
4. **Naissances** — idbank mensuel France `001641601` ; somme 2025 = **643 905** (match Focus). Rejet de la série métropole seule `000067677`.
5. **Chômage** — métadonnées BDM confirmées (`REF_AREA=FR-D976`, CVS, ensemble). Snapshot publication **conservé** (7.5) malgré historique de révision (IR ultérieur 7.6 / BDM live 7.5+OBS_REV).

## Non résolu

- **MG012** : dans `CREATIONS-ENTREPRISES`, les séries « Ensemble - France » sont **arrêtées**. Valeur annuelle SIDE confirmée en publication seulement.

## MG001–MG003 publication vs révision

| Source | 2025-Q2 |
|---|---|
| IR 8627586 (08/08/2025) — Gold snapshot | **7.5** |
| IR 8989990 table (plus tard) | 7.6 |
| BDM live `001688527` (inspecté 2026-10-10) | **7.5** (OBS_REV=1) |

Oracle MG001–MG003 = **publication snapshot**, pas « dernière valeur vue un jour ».

## Tests

```text
.venv\Scripts\python.exe -m pytest tests/gold/test_micro_gold_v0.py -q --tb=short
# → 13 passed
```

## Stop

Ne pas démarrer Retrieval / Session 5 tant que ce verdict n’est pas accepté.  
Prochaine action humaine possible : trouver le successeur BDM des créations Ensemble–France, ou accepter MG012 comme oracle **publication-only**.
