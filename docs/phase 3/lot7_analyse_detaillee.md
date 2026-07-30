# Documentation et Analyse Détaillée : Lot 7 (Moteur de Recherche RAG)

Ce document retrace exhaustivement la conception, l'implémentation et l'analyse des résultats du Lot 7 pour le projet StatCheck. Ce lot est le cœur du système "Retrieval-Augmented Generation" (RAG) et s'appuie sur une architecture hybride (Lexicale et Vectorielle) construite sur PostgreSQL.

---

## 1. Vue d'Ensemble de l'Architecture
Le Lot 7 a été structuré pour répondre au double défi de la recherche sur des données statistiques INSEE :
1. **La précision lexicale (Exact Match)** : Nécessaire pour retrouver des codes d'indicateurs précis (ex: "CHOMAGE_BIT").
2. **Le gouffre sémantique** : Nécessaire pour comprendre que "personnes sans emploi" correspond à "chômage" même si le mot n'est pas explicite.

L'architecture s'articule autour de trois moteurs fusionnés :
- **D0a : Moteur Lexical (FTS - Full Text Search)**
- **D0b : Moteur Sémantique (Vectoriel via pgvector)**
- **D1 : Reranker Déterministe**

### 1.1 Modélisation Physique (Étape 2 & 3 & 4)
Tout commence par le schéma de la base de données. L'approche choisie a été de centraliser la logique de recherche au sein de PostgreSQL pour bénéficier d'une co-localisation des données et éviter les allers-retours réseaux coûteux.

**Le Schéma SQL (`search_documents`) :**
Le cœur de la recherche est stocké dans la table `search_documents`.

```sql
CREATE EXTENSION IF NOT EXISTS vector;
CREATE EXTENSION IF NOT EXISTS unaccent;

CREATE TEXT SEARCH CONFIGURATION french_unaccent ( COPY = french );
ALTER TEXT SEARCH CONFIGURATION french_unaccent
    ALTER MAPPING FOR hword, hword_part, word
    WITH unaccent, french_stem;

CREATE TABLE IF NOT EXISTS search_documents (
    dataset_id VARCHAR(100) PRIMARY KEY,
    catalog_snapshot_id VARCHAR(100) REFERENCES catalog_snapshots(snapshot_id),
    
    indicator_code VARCHAR(100),
    title TEXT,
    description TEXT,
    
    lexical_vector tsvector,
    embedding_text TEXT,
    embedding vector(1024)
);
```

**Analyse de la Modélisation :**
- **Extension `unaccent` et `french_stem` :** Essentielles. Les utilisateurs font fréquemment des fautes d'accentuation ("chomage" vs "chômage"). La configuration `french_unaccent` permet de normaliser les requêtes.
- **Le Trigger SQL (`setweight`) :** Nous avons automatisé la création du `tsvector` lors de l'insertion ou la mise à jour via un trigger. Le Titre reçoit le poids 'A', l'Indicateur 'B' et la Description 'C'. Cela garantit que le moteur FTS de PostgreSQL classe un dataset plus haut si le mot-clé se trouve dans le titre plutôt que dans une longue description.
- **Cache de Hachage pour l'IA (`entity_embeddings`) :** Calculer des embeddings à 1024 dimensions (comme le modèle BGE-M3) coûte cher. Nous avons créé une table `entity_embeddings` utilisant un hash SHA-256 du texte comme clé primaire. Si l'INSEE met à jour un dataset sans modifier sa description, nous ne recalculons pas le vecteur, nous le récupérons depuis le cache.

---

## 2. Le Moteur de Recherche Hybride

### 2.1 La Recherche Vectorielle (Cosinus Exact)
Contrairement aux bases vectorielles classiques qui utilisent d'emblée des index HNSW (Hierarchical Navigable Small World) ou IVFFlat, nous avons fait le choix de l'opérateur `<=>` (Distance Cosinus Exacte) de PostgreSQL :
```sql
SELECT dataset_id, (1 - (embedding <=> query_embedding))::NUMERIC AS similarity
FROM search_documents
ORDER BY embedding <=> query_embedding LIMIT 50;
```
**Justification :** Le catalogue de l'INSEE ne contient pas des millions de datasets, mais plutôt de l'ordre du millier. Un index HNSW sacrifie un faible pourcentage de précision (Recall) pour de la vitesse. Sur une volumétrie faible, le scan complet de la table (K-NN exact) prend moins de 10ms. La précision étant primordiale dans StatCheck, nous privilégions le calcul exact.

### 2.2 La Fusion par les Rangs (RRF - Reciprocal Rank Fusion)
L'étape 5 a consisté à fusionner les résultats lexicaux et vectoriels sans avoir à normaliser les scores de distance cosinus (qui varient entre 0 et 1) avec les scores TS_RANK (qui n'ont pas de borne supérieure fixe).

**L'algorithme RRF :**
```python
def get_rrf_score(rank, k=60, weight=1.0):
    if rank is None: return 0.0
    return weight * (1.0 / (k + rank))
```
**Analyse des Paramètres RRF :**
Nous avons envisagé une simulation d'optimisation sur un set de validation. Les résultats attendus montrent que :
- **k = 30** pourrait être plus performant que `k = 60` car notre corpus Gold favorisera les résultats qui tombent directement dans le Top 5 de chaque sous-moteur.
- **Poids Vectoriel = 1.25 vs Lexical = 1.0 :** Le sémantique pourrait être légèrement avantagé pour capter les nuances des affirmations politiques face au vocabulaire très technique de l'INSEE.
- Le concept de bonus de consensus additif a été abandonné car il faussait l'échelle mathématique du RRF. La fusion repose désormais purement sur les rangs réciproques.

---

## 3. L'Intelligence Métier (Reranker Déterministe)
L'Étape 6 est ce qui transforme un simple moteur de recherche textuel en un système robuste pour le Fact-Checking (Architecture D1).

Le score RRF pur a une faiblesse : il peut classer 1er un dataset qui parle très bien du sujet, mais qui n'a pas la dimension requise par l'affirmation. La magie s'opère dans **`scripts/etape_6/deterministic_reranker.py`**. Le Reranker ne modifie pas les scores avec des bonus massifs arbitraires qui écraseraient le RRF. Au lieu de cela, il adopte une approche de **Tri Lexicographique (Solution A)**, structurée par niveaux de priorité :
1. **Niveau 1 (Contraintes dures)** : Validation de l'activité du dataset, autorisation de la source, et exclusion immédiate si contrainte non respectée.
2. **Niveau 2 (Indicateur exact)** : Vérification de la correspondance du code indicateur principal.
3. **Niveau 3 (Dimensions)** : Nombre de dimensions indispensables trouvées dans le dataset.
4. **Niveau 4 (RRF Score)** : Le score RRF brut qui sert de mécanisme de départage naturel pour les ex æquo sur les niveaux précédents.

Un tuple de scoring `(is_valid, has_exact_indicator, satisfied_dimensions_count, rrf_score)` garantit que les règles métier priment toujours, tout en préservant le pouvoir de classement granulaire du RRF à l'intérieur d'un même tiers de pertinence.

**La Logique d'Abstention :**
L'algorithme s'abstient volontairement si tous les candidats sont rejetés par contrainte dure.
- Un **seuil d'abstention dynamique (cosine_threshold)** paramétrable, pour rejeter les meilleurs candidats s'ils sont sémantiquement trop éloignés de l'affirmation. Il vaut mieux dire "Je ne trouve pas de données de l'INSEE pour valider ça" que de valider avec le mauvais tableau.

---

## 4. Évaluation et Tests Unitaires (Étape 7)
Nous avons implémenté le script `evaluate_retrieval.py` pour comparer mathématiquement l'architecture.

### 4.1 Les Métriques Utilisées
- **Exact Recall@K** : Vrai si le dataset avec une pertinence parfaite (3) est dans le Top K.
- **nDCG@K (Normalized Discounted Cumulative Gain)** : Mesure l'utilité globale du classement en pénalisant les bons résultats qui se trouvent trop bas dans la liste. Un gain exponentiel (`2^rel - 1`) a été appliqué pour s'assurer que rater un document "Parfait" (3) chute sévèrement le score par rapport à un document "Acceptable" (2).
- **HNWR (Hard Negative Win Rate)** : Le pourcentage de fois où la vraie réponse est classée au-dessus d'un "Hard Negative" (un leurre sémantique).

### 4.2 Résultats de la Campagne sur les Vraies Données (222 Datasets INSEE)
Afin de valider l'approche au-delà des simulations abstraites, le moteur (FTS + Vector + Reranker) a été exécuté sur un export réel de 222 Dataflows INSEE (`data/raw/*.xml`), évalué contre un sous-ensemble du corpus Gold (7 requêtes complexes).

| Architecture | Exact R@5 | nDCG@5 | Abstention | Observations |
|---|---:|---:|---:|---|
| **D0** (RRF Seul) | 43 % | 0.40 | 0.0% | Souffre du gouffre sémantique et ne gère pas les contraintes dures. Classe souvent un Hard Negative haut. |
| **D1** (RRF + Reranker) | **71 %** | **0.64** | **14.3%** | Les règles d'Indicateur Exact et de Dimensions propulsent le Vrai Dataset en 1ère position et rejettent les leurres. |

**Analyse de l'Abstention :**
L'abstention de 14.3 % (1 cas sur 7) s'est déclenchée correctement sur la requête "Chômage par région" (contrainte `REG`), car le dataset `CHOMAGE-TRIM-NATIONAL` ne possédait pas la dimension régionale. Le système a préféré dire "Je ne sais pas" plutôt que de fournir la mauvaise granularité géographique.

### 4.3 Validation par Tests (Test-Driven)
Pour solidifier l'ensemble, nous avons migré les scripts vers un environnement testable et créé `tests/test_lot7.py` via `unittest`.
- Tous les modules (Mathématiques RRF, Logique d'abstention du Reranker, et les Métriques nDCG) disposent de tests unitaires validant leur comportement.
- L'exécution de `python tests/test_lot7.py` montre un taux de réussite de 100% sur 8 tests critiques couvrant les limites mathématiques, les rejets stricts et les divisions par zéro potentielles.

---

## Conclusion et Statut (En Cours de Validation Scientifique)

L'architecture globale (Hybride + Lexicographique) a produit un **succès technique exploratoire**. Le pipeline E2E PostgreSQL (avec `pgvector` et `unaccent`) est robuste mathématiquement, et son efficacité sémantique vient d'être techniquement validée sur **un snapshot réel du catalogue INSEE (222 datasets)** avec des latences excellentes (médiane à ~42 ms).

**Toutefois, le Lot 7 n'est pas encore fonctionnellement et scientifiquement clos.** 

La rigueur de StatCheck exige de séparer la validation technique de la **Qualité Retrieval**. Les prochaines étapes absolues (Sous-lot 7D - Validation Scientifique) avant la clôture du lot et le passage au Lot 8 sont :

1. **Documenter précisément le snapshot des 222 datasets** (provenance, catalogues couverts, dates, hash).
2. **Analyser les pics de latence à 50ms** observés sur le vectoriel exact en p95.
3. **Compléter l'annotation manuelle** du reste du corpus Gold (Train & Validation).
4. **Exécuter l'évaluation (FTS, Vectoriel, RRF, Règles) sur le set de Validation (40 requêtes)**.
5. **Produire les métriques de qualité** (Exact R@5, Acceptable R@5, MRR, nDCG@5, HNWR) pour prouver le Rappel Retrieval.
6. **Calibrer mathématiquement l'abstention** (Précision, Rappel, F1-Score).
7. **Geler l'architecture Retrieval V1**.

Le système ne se contente plus de faire de la similarité textuelle : il raisonne sur des attributs forts (codes INSEE, dimensions). Une fois que la campagne de validation sur les 40 affirmations aura prouvé son efficacité de classement, ce lot deviendra la clé de voûte de la crédibilité du fact-checking automatisé de StatCheck.
