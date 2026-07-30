# Documentation et Analyse Détaillée : Lot 4 (Corpus Gold)

Ce document retrace la conception et la construction du Corpus "Gold" (Lot 4) de la Phase 3 de StatCheck. Ce corpus constitue la vérité terrain inaltérable sur laquelle repose l'évaluation de tous nos modèles de compréhension du langage (Parsing) et de recherche d'information (Retrieval).

---

## 1. Objectif du Corpus Gold

L'objectif principal du Lot 4 était de créer un référentiel robuste de 200 affirmations (claims). Sans une vérité terrain stricte, il est impossible de mesurer la performance des systèmes d'intelligence artificielle de manière scientifique.

Le défi majeur du NLP appliqué au fact-checking statistique est de transformer une affirmation floue ("Le chômage a baissé de 2 points l'an dernier") en une requête formelle compréhensible par la base de données de l'INSEE. Le corpus Gold est la "correction" de cet exercice pour 200 phrases.

## 2. Sous-lot 4A : Spécification et Pilote

Avant de générer la donnée, il a fallu définir le "moule" dans lequel chaque affirmation devait s'insérer.

### 2.1 Le Schéma d'Annotation JSON (`schema_annotation.json`)
Nous avons conçu un schéma JSON strict qui définit les entités et relations attendues.
- **Identity** : Qui parle, quand, et où.
- **Subject** : De quoi parle l'affirmation (Indicateur INSEE, concept économique).
- **Time** : Les périodes exactes ou relatives mentionnées.
- **Measure** : Les valeurs, unités, et changements revendiqués.
- **Operation** : La dynamique de la phrase (hausse, baisse, stabilité, comparaison).

**Justification technique :** Si nous avions laissé un format libre, les évaluateurs et les LLM auraient structuré les données de mille façons différentes, rendant la comparaison automatisée (F1-score, Exact Match) impossible. Le `schema_annotation.json` fait office de contrat d'interface.

### 2.2 Le Guide d'Annotation (`guide_annotation.md`)
Ce manuel d'instructions encadre la sémantique.
- **Exemple de résolution :** Si un texte indique "Le taux a baissé de 2 %", le guide stipule s'il faut extraire "PERCENTAGE" ou "PERCENTAGE_POINT". 
- Ce guide a permis d'aligner la compréhension humaine avant d'exiger quoi que ce soit d'une machine.

### 2.3 Le Pilote (20 Affirmations)
Une validation empirique a été menée sur 20 affirmations issues de la Phase 0. Ce pilote a permis de confirmer que notre schéma JSON était suffisamment expressif pour couvrir des phrases complexes sans générer d'ambiguïté insoluble.

---

## 3. Sous-lot 4B : Constitution du Corpus Complet

### 3.1 Génération et Normalisation
Un script (`generate_synthetic_corpus.py`) a été mis à l'épreuve pour générer le reste du corpus et atteindre le seuil de 200 affirmations, nécessaire pour avoir une représentativité statistique valide lors des tests.

### 3.2 Gestion du Data Leakage (Fuite de Données)
Un élément critique de notre modélisation a été l'ajout de la variable `paraphrase_group_id`.
- **Problème :** Si "Le chômage est à 7%" (Train) et "7% de chômeurs" (Test) sont séparés sans précaution, le modèle apprendra par cœur le lien sémantique et trichera lors de l'évaluation.
- **Solution :** Nous avons forcé le regroupement des affirmations similaires dans le même split (soit tout dans le Train, soit tout dans le Test). Cela garantit que les métriques finales mesurent la capacité de **généralisation** du modèle, et non sa mémorisation.

### 3.3 Accord Inter-Juges (Double Annotation)
Pour modéliser la difficulté inhérente au langage, 50 affirmations ont été soumises à une double annotation. 
- **Signification :** La machine ne pourra jamais atteindre 100% de réussite si les humains eux-mêmes sont en désaccord sur 15% des phrases complexes. Cet accord inter-juges définit le "plafond" de performance attendu.

### 3.4 Sanctuarisation des Splits
Le corpus a été rigoureusement scindé :
- **Train (120 affirmations - 60%) :** Données accessibles pour le développement, l'optimisation des prompts (Few-Shot), et l'affinage des règles manuelles.
- **Validation (40 affirmations - 20%) :** Données utilisées pour l'optimisation des hyperparamètres (comme les poids du RRF dans le Lot 7) et la comparaison des modèles.
- **Test (40 affirmations - 20%) :** Le coffre-fort. Ce set a été gelé et n'est utilisé qu'à la toute fin du pipeline pour l'évaluation finale.

---

## Conclusion du Lot 4
Le Lot 4 a posé les fondations scientifiques du projet. Grâce à un schéma JSON contraignant, un guide humain précis et une séparation stricte des données (Train/Val/Test), StatCheck dispose d'un outil de mesure incontestable pour évaluer l'intelligence artificielle des lots suivants.
