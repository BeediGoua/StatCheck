# Documentation et Analyse Détaillée : Lot 5 (Infrastructure d’Évaluation)

Ce document explore l'architecture d'évaluation (Lot 5) mise en place pour la Phase 3 du projet StatCheck. Ce lot est essentiel : il fournit les outils mathématiques et logiciels permettant d'évaluer objectivement les modèles NLP (Lot 6) et les moteurs de recherche (Lot 7).

---

## 1. Philosophie de l'Évaluation
Dans un pipeline RAG (Retrieval-Augmented Generation), une erreur au début de la chaîne (mal comprendre l'affirmation) entraîne inévitablement un échec à la fin de la chaîne (trouver la mauvaise donnée). L'infrastructure d'évaluation du Lot 5 a été conçue pour tracer précisément chaque étape.

### 1.1 Importation dans PostgreSQL
La première étape structurante a été l'ingestion du Corpus Gold (Lot 4) dans PostgreSQL (`scripts/import_gold_corpus.py`).
- **Idempotence :** Le script a été conçu pour pouvoir être rejoué à tout moment sans générer de doublons.
- **Relationalité :** Le format JSON, parfait pour la portabilité, a été décomposé en tables relationnelles (`claims`, `claim_annotations`, `claim_spans`). Cela permet aux scripts d'évaluation de faire des requêtes JOIN complexes pour croiser les prédictions d'un modèle avec la Vérité Terrain.

## 2. Métriques de Parsing (Compréhension du texte)

Le module `src/evaluation/parsing_metrics.py` s'occupe de juger si le système a bien extrait les entités d'une affirmation. L'évaluation NLP est intrinsèquement complexe, c'est pourquoi nous utilisons une double approche :

### 2.1 Exact Match (Tout ou Rien)
- **Concept :** Une vérification stricte d'égalité. Si la Vérité Terrain attend l'indicateur "CHOMAGE_BIT" et que le modèle prédit "CHOMAGE", le score est de 0.
- **Utilité :** Cette métrique est impitoyable mais garantit l'intégrité de la donnée. Dans le contexte de la donnée statistique, une erreur d'approximation sur une unité (ex: "%" vs "points de %") invalide complètement la vérification.

### 2.2 F1-Score par Champ (Granulaire)
- **Concept :** Inspiré des standards NLP, le F1-Score combine la Précision et le Rappel. 
- **Utilité :** Il permet d'isoler les faiblesses d'un modèle. Par exemple, un LLM peut avoir un F1-Score de 0.95 sur l'extraction des indicateurs, mais un score de 0.40 sur l'extraction temporelle. Cela permet de cibler les efforts d'optimisation (prompt engineering ou expressions régulières) de façon chirurgicale.

## 3. Métriques de Retrieval (Moteur de Recherche)

Le module `src/evaluation/retrieval_metrics.py` évalue la capacité du système (construit lors du Lot 7) à trouver le bon dataset dans le catalogue INSEE, à partir des entités extraites.

### 3.1 Recall@K (Rappel à K)
- **Définition :** Le bon dataset (Score de pertinence >= 2) est-il présent dans les K premiers résultats retournés par le moteur ?
- **K = 1 :** Idéal (Le moteur pointe directement sur le bon tableau).
- **K = 5 ou 10 :** Acceptable si l'on utilise un Reranker ultérieur.
- **Implémentation :** Les scripts calculent systématiquement l'Exact Recall (pertinence = 3) et l'Acceptable Recall (pertinence >= 2).

### 3.2 Mean Reciprocal Rank (MRR)
- **Définition :** La moyenne de l'inverse du rang du premier résultat pertinent (`1 / Rang`).
- **Utilité :** Permet d'évaluer la qualité du tri. Si le bon résultat est 1er, le score est 1. S'il est 2ème, le score est 0.5, etc.

### 3.3 nDCG (Normalized Discounted Cumulative Gain)
- **Définition :** Une métrique avancée qui prend en compte le "poids" de la pertinence (ex: 3 pour "Parfait", 1 pour "Partiel") et pénalise fortement la rétrogradation de résultats parfaits dans le classement.
- **Implémentation spécifique :** Un gain exponentiel (`2^rel - 1`) a été appliqué. Le moteur est ainsi lourdement pénalisé s'il classe un document "Partiel" avant un document "Parfait".

## 4. Génération de Rapports d'Expérimentations
Le script `src/evaluation/report_generator.py` clôture le Lot 5.
- Il agrège les métriques de Parsing et de Retrieval.
- Il stocke les résultats des "runs" (ex: Run A = Lexical pur, Run B = LLM + Vectoriel) dans les tables `parser_runs` et `retrieval_runs`.
- Il formate ces données en Markdown pour offrir aux développeurs des tableaux de bord instantanés de comparaison de performance.

## Conclusion du Lot 5
Le Lot 5 fournit à StatCheck son "Juge" mathématique. En séparant l'infrastructure de test du code de l'IA elle-même, nous avons garanti que le développement ultérieur des moteurs NLP et RAG s'effectuerait dans un cadre scientifique rigoureux, où chaque modification peut être objectivement mesurée.
