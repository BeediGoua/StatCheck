# Héritage de la Phase 1 : De l'Exploration à l'Architecture (Phase 2)

Ce document explique précisément comment les découvertes, cartographies et expérimentations réalisées lors de la Phase 1 ont dicté la modélisation de notre base de données PostgreSQL (Lot 2B).

Rien n'a été créé au hasard : chaque table répond à une douleur ou à une observation faite lors de nos premiers tests avec l'API de l'INSEE.

---

## 1. La Cartographie des 10 Dataflows et l'origine des Données
Lors de la Phase 1 (dans le document `cartographie_dataflow_insee.md`), nous avons constaté que l'INSEE expose ses données via **deux systèmes différents** :
- **INSEE_BDM** : Pour les séries temporelles macros (comme l'inflation ou le chômage).
- **INSEE_MELODI** : Pour les données locales territoriales.

**Impact sur la Base de Données :**
C'est la raison exacte pour laquelle la table `sources` existe. Au lieu de coder en dur "INSEE", le système est capable de gérer indépendamment la source BDM et la source Melodi, avec chacune ses propres limites de requêtes (Rate Limits) et ses propres points d'entrée (`source_endpoints`).

---

## 2. La rigidité des Dimensions SDMX
La cartographie a également montré que chaque jeu de données possède une structure stricte. Par exemple, le chômage nécessite de renseigner les filtres `FREQ`, `INDICATEUR`, `NATURE`, `SEXE`, et `AGE` dans un ordre extrêmement précis.

**Impact sur la Base de Données :**
Nous avons créé le groupe de tables `Structure` :
- La table `dimensions` permet de définir "SEXE" une seule fois de manière globale.
- La table de liaison `dataset_dimensions` permet de lier "SEXE" au dataset du chômage, mais surtout, elle possède une colonne **`position`**. Cette colonne est vitale pour respecter l'ordre exact imposé par la norme SDMX de l'API.

---

## 3. Le problème des `idbank` manquants (Le Notebook)
Dans le fichier `Test_moteur.ipynb`, nous avons testé 30 affirmations (nos MVP). Le constat fut sans appel : sur 30 affirmations, nous ne connaissions l'identifiant exact de la série (`idbank`) que pour 5 d'entre elles. Il était impossible pour un humain de deviner les 25 autres sans passer des heures sur le site de l'INSEE.

**Impact sur la Base de Données :**
C'est la genèse de la table `series`. Son rôle est de recenser l'intégralité des combinaisons de filtres possibles (via `series_dimension_values`) pour un dataset. 
Ainsi, l'algorithme n'aura plus besoin d'un `idbank` manuel. Il fera simplement une requête SQL : *"Trouve l'idbank de la série où Dataset=Inflation, Produit=Alimentation"*, et la base le retournera instantanément.

---

## 4. Le risque de Bannissement et la conservation des Preuves
Dans notre notebook de test, nous avions été obligés de créer un système de cache dans un dossier `.cache/bdm/` pour stocker les fichiers JSON, sous peine de nous faire bloquer par l'API à force de relancer les tests.

**Impact sur la Base de Données :**
Ce besoin "bricolé" est devenu une fondation robuste de notre architecture :
- Le répertoire de cache est devenu l'arborescence officielle de stockage (`data/raw/`).
- La table `resource_versions` a été créée pour garder une trace de chaque téléchargement. C'est elle qui implémente la méthode des **3 Hashs** (Brut, Normalisé, Métier) pour archiver la preuve mathématique des données publiées par l'INSEE à une date précise.

---

## 5. La séparation des Observations
Enfin, la classe `Observation` (qui contenait la valeur et la date) codée en Phase 1 n'a **pas** été transformée en table PostgreSQL.
Les observations sont des points de données qui se comptent en dizaines de millions. Mettre cela dans Postgres ralentirait les recherches textuelles (qui sont la priorité de la base de données). C'est pourquoi le schéma SQL s'arrête aux "Séries", tandis que les "Observations" mathématiques seront stockées sous forme de fichiers **Parquet** compressés, parfaitement adaptés pour `Pandas` et le Moteur de Calcul.
