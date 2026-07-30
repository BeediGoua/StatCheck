# Rapport Technique et Benchmark du Déploiement PostgreSQL E2E (Lot 7)

## 1. Objectif Global et Contexte
Ce document synthétise l'aboutissement technique (prototype E2E) du **Lot 7**.
Nous sommes passés d'un mock Python à une véritable infrastructure de production basée sur **PostgreSQL** avec `unaccent` et `pgvector`. 
**Attention :** Ce document valide la faisabilité et les performances informatiques (latence). La validation scientifique (Qualité Retrieval) nécessite la complétion du Gold Corpus et fait l'objet d'une campagne séparée.

---

## 2. Informations de Reproductibilité
- **Catalogue :** 222 datasets réels extraits depuis les XML de l'INSEE (Dataflows BDM actifs au 1er janvier). Hash et logs d'ingestion à documenter et consolider.
- **Requêtes :** 7 affirmations extraites du corpus Gold (échantillon expérimental pilote).
- **Protocole :** 7 requêtes × 20 itérations séquentielles (140 exécutions à chaud).
- **Modèle NLP :** `paraphrase-multilingual-MiniLM-L12-v2` (dimension 384, exécution CPU locale).
- **Base de données :** PostgreSQL 16 via Docker `pgvector/pgvector:pg16`.
- **Infrastructure :** Windows local, exécution script Python séquentielle (1 seul utilisateur).

---

## 3. Résultats des Latences (Benchmark Exploratoire)

*Les percentiles sont calculés indépendamment pour chaque composant et directement sur la latence totale ; ils ne sont donc pas additifs.*

| Composant (Latence) | p50 (médiane) | p95 | p99 |
|:---|---:|---:|---:|
| **Embedding de la requête (NLP)** | 31.29 ms | 49.60 ms | 98.91 ms |
| **FTS PostgreSQL (Lexical)** | 1.92 ms | 2.37 ms | 5.12 ms |
| **Vectoriel exact pgvector** | 7.75 ms | 50.69 ms | 52.56 ms |
| **Fusion RRF (Python)** | 0.17 ms | 0.25 ms | 0.31 ms |
| **Reranker Déterministe** | 0.25 ms | 0.38 ms | 0.42 ms |
| **Total Pipeline E2E** | **42.61 ms** | **84.67 ms** | **116.01 ms** |

---

## 4. Analyse et Décisions Techniques

### 4.1 La recherche exacte et l'HNSW
La recherche vectorielle exacte (`<=>`) obtient une médiane de 7.75 ms. 
**Attention au p95 :** Le bond à 50.69 ms sur seulement 222 vecteurs suggère une distribution bimodale ou des coûts externes (acquisition de connexion, GC Python, ordonnancement Windows) qu'il faudra investiguer.
> **Décision V1 :** HNSW n'est pas retenu pour la V1 expérimentale avec 222 embeddings. La décision sera réévaluée selon la croissance du catalogue, la concurrence (tests en charge) et les objectifs de latence stricts, en comparant systématiquement HNSW à la recherche exacte.

### 4.2 Le goulot d'étranglement de l'encodage
Sur les médianes observées, l'encodage NLP représente environ **73,4 %** de la latence E2E (31,29 / 42,61). 

### 4.3 Rappel ANN vs Recall Retrieval
La recherche exacte pgvector garantit un **Rappel ANN parfait** (trouver les vrais plus proches voisins selon la distance cosinus). Cependant, cela ne garantit pas la qualité du *Retrieval* (le bon dataset pourrait ne pas avoir le bon embedding ou un vocabulaire adapté, ou le modèle peut échouer à capturer le concept).

---

## 5. Mesures de Qualité Scientifique (À Venir)

Le benchmark de latence ne clôture pas le Lot 7. Une campagne complète sur les **40 affirmations du set de validation** doit être exécutée pour remplir le tableau de vérité suivant :

| Architecture | Exact R@1 | Exact R@5 | Exact R@10 | Acceptable R@5 | MRR | nDCG@5 | HNWR |
|---|---:|---:|---:|---:|---:|---:|---:|
| FTS | À mesurer | | | | | | |
| Vectoriel | À mesurer | | | | | | |
| RRF | À mesurer | | | | | | |
| RRF + règles | À mesurer | | | | | | |

*L'architecture expérimentale avec Cross-Encoder (RRF + Règles + Cross-Encoder + Vérification finale) sera testée séparément et ne remplacera jamais les contraintes métier dures.*

---

## 6. Conclusion et État du Lot 7

> Le déploiement PostgreSQL E2E du Lot 7 est **fonctionnel**. Sur un snapshot expérimental de 222 datasets et 140 exécutions séquentielles en environnement chaud, le pipeline obtient une latence médiane de 42,61 ms et un p95 de 84,67 ms. La recherche vectorielle exacte est suffisamment rapide dans ce périmètre ; HNSW n'est donc pas retenu pour la V1 actuelle.
>
> Ces résultats valident la faisabilité technique et la performance initiale du pipeline, **mais pas encore sa qualité Retrieval générale**. La complétion du Gold, l'évaluation sur les 40 affirmations de validation, la calibration de l'abstention, les tests concurrents et la documentation du snapshot restent nécessaires avant de clôturer le Lot 7 ou de qualifier le système pour la production.
