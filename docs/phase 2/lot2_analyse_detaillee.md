# Documentation et Analyse Détaillée : Lot 2 (Socle de Données et Architecture)

Ce document retrace la conception et l'implémentation du Lot 2 de la Phase 2 de StatCheck. Ce lot établit le socle fondamental de données permettant d'ingérer, de structurer et d'historiser le catalogue de l'INSEE.

---

## 1. Objectif et Philosophie de l'Architecture

Plutôt que d'aspirer aveuglément des milliards d'observations statistiques, la stratégie de la Phase 2 repose sur la construction d'un **catalogue local interrogeable**. Le but est d'avoir une cartographie exacte des jeux de données, dimensions et modalités disponibles à l'INSEE.

### 1.1 L'Architecture aux 3 Zones
Pour répondre aux exigences d'auditabilité (prouver l'origine d'un chiffre) et de performance, les données sont ségréguées en trois zones :

1. **La Zone d'Audit (JSON/XML Bruts) :** 
   - Stockage physique des fichiers originaux tels que renvoyés par les API (Melodi / BDM SDMX).
   - *Rôle :* Preuve irréfutable, débogage, reproductibilité. Si l'INSEE modifie une donnée silencieusement, le fichier brut original signé fait foi.
2. **La Zone de Recherche (PostgreSQL) :** 
   - Stockage normalisé des métadonnées (Catalogue, Structures, Dimensions).
   - *Rôle :* C'est le cerveau relationnel. Il permet le filtrage ("Trouve-moi les datasets avec la dimension SEXE") et sera la base du moteur de recherche hybride (Lot 7).
3. **La Zone d'Analyse (Fichiers Parquet) :**
   - Stockage des séries temporelles et des observations mathématiques.
   - *Rôle :* Le format Parquet, compressé et partitionné en colonnes, permet des agrégations ultra-rapides et évite de saturer PostgreSQL avec des milliards de lignes temporelles répétitives.

---

## 2. Dictionnaire de Données et Sémantique (Sous-lot 2A)

Avant de créer la base, un glossaire strict a été défini pour éviter toute confusion linguistique entre les formats de l'INSEE (SDMX vs Melodi).

- **Source :** Le système externe (ex: `INSEE_BDM`).
- **Dataset :** Notre représentation générique d'un produit (ex: "Chômage trimestriel").
- **Dimension :** Un axe d'analyse (ex: "Sexe", "Tranche d'âge").
- **Modalité :** Les valeurs possibles d'une dimension (ex: "Hommes", "Femmes").
- **Observation :** La valeur numérique exacte à un instant T (ex: 7.2 %).

### 2.1 La Méthode des 3 Hashs (Versionnement)
Pour détecter les altérations de données de manière déterministe :
- **Hash Brut :** Empreinte SHA-256 du fichier téléchargé original (XML/JSON).
- **Hash Normalisé :** Empreinte après nettoyage (retrait des balises d'en-tête, des timestamps techniques de l'API).
- **Hash Métier :** Empreinte sur la *sémantique* (les valeurs elles-mêmes ont-elles changé ?).

---

## 3. Schéma PostgreSQL Minimal (Sous-lot 2B)

La modélisation de PostgreSQL a été pensée en 4 grands groupes.

### 3.1 Groupe Fournisseurs et Catalogue
- `sources` : Liste des API.
- `datasets` : Table centrale avec l'ID normalisé, le titre, et l'alias de l'INSEE.

### 3.2 Groupe Structurel
- `dimensions` et `dataset_dimensions` : Lient un dataset à ses axes (ex: Le dataset "Natalité" requiert la dimension "Âge de la mère").
- `modalities` : Liste exhaustive des valeurs possibles (stockées via les *codelists* SDMX).

### 3.3 Groupe Séries
- `series` : Identifie une série unique (ex: Taux de chômage des Hommes de 15-24 ans).
- Les *observations* de ces séries iront majoritairement en Parquet (Niveau 3 de l'ingestion), mais leurs métadonnées restent ici.

### 3.4 Groupe Ingestion et Audit
- `ingestion_runs` : Trace chaque exécution du robot d'ingestion.
- `resource_versions` : Relie un dataset à son fichier brut dans `data/raw/` avec le fameux **Hash Brut**.

---

## 4. Organisation du Stockage Fichiers (Sous-lot 2C)

Une arborescence rigide a été imposée sur le disque pour accompagner PostgreSQL :
- `data/raw/` : Archives intouchables.
- `data/normalized/` : Fichiers Parquet prêts pour le traitement analytique.
- `data/temporary/` : Dossier tampon. Les téléchargements partiellement échoués restent ici et n'empoisonnent pas le pipeline.
- `data/quarantine/` : Isolation des réponses inattendues de l'API INSEE (erreurs 500 récurrentes, schémas corrompus).

---

## Conclusion du Lot 2
Le Lot 2 a jeté les bases d'un système conçu non pas pour "gratter des données rapidement", mais pour construire une **cathédrale d'audit**. Chaque donnée qui entre dans StatCheck dispose désormais d'une place désignée, d'une preuve de son origine, et d'un schéma relationnel permettant une interrogation complexe par les futurs modèles d'Intelligence Artificielle.
