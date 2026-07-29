# Contrat de Données (Glossaire et Dictionnaire) - Phase 2

Ce document définit le vocabulaire officiel et les règles d'intégrité de la base de données StatCheck. Il sert de référence pour tous les développements futurs.

---

## 1. Glossaire Métier

Pour éviter toute confusion lors du développement, les termes suivants ont un sens strict dans le code et la base de données de StatCheck :

| Terme | Définition | Exemple Concret |
|---|---|---|
| **Source** | Un système externe ou une API qui publie des données statistiques. | `INSEE_BDM`, `INSEE_MELODI` |
| **Dataset** | (Jeu de données). L'objet fonctionnel présenté à l'utilisateur, regroupant des thématiques précises. | `CHOMAGE-TRIM-NATIONAL`, `IPC-2025` |
| **Objet externe** | Le nom exact de l'objet tel qu'appelé chez le fournisseur (pour éviter de déformer sa nature). | Un "Dataflow" SDMX, un "ConceptScheme" |
| **Dimension** | Un axe permettant de filtrer, décrire ou catégoriser une donnée. | `FREQUENCE`, `SEXE`, `AGE`, `TERRITOIRE` |
| **Modalité** | Une valeur possible ou précise prise par une dimension. | Pour la dimension Sexe : `Hommes`, `Femmes`, `Ensemble`. |
| **Série** | Une combinaison précise et unique de modalités décrivant un indicateur suivi dans le temps. (L'équivalent d'une courbe sur un graphique). | `Fréquence=Trimestrielle + Territoire=France + Indicateur=Chômage + Sexe=Ensemble + Âge=15-24 ans` |
| **Observation** | Le point de donnée ponctuel et mathématique (une valeur, à une date précise, pour une série précise). | `2025-T1 -> 7,4 %` |

---

## 2. Dictionnaire de Données (Règles et Identifiants)

Afin de garantir que StatCheck ne génère pas de doublons et conserve une traçabilité parfaite, les règles d'intégrité suivantes doivent être implémentées dans PostgreSQL.

### 2.1 Les Identifiants (IDs)
1. **Identifiants internes (Clés primaires)** : Toutes les tables principales (`datasets`, `dimensions`, `modalities`, etc.) utiliseront des **UUID v4** générés par StatCheck. 
   - *Raison* : Cela permet de générer les IDs côté applicatif (Python) avant l'insertion en base, facilitant grandement les insertions massives (Bulk inserts).
2. **Identifiants externes (`external_id`)** : Stockés sous forme de chaînes de caractères (String/Varchar). Ils correspondent exactement à la clé fournie par l'INSEE.

### 2.2 Règles d'Unicité absolues (Contraintes SQL)
Pour éviter de dupliquer les données si le robot d'ingestion passe deux fois, les clés d'unicité (UNIQUE CONSTRAINTS) suivantes doivent être respectées :

- **Unicité d'un Dataset** : Un dataset est unique par la combinaison de 3 champs :
  `[source_id] + [type_externe] + [external_id]`
  *(Exemple : Source=INSEE_BDM + Type=Dataflow + ID=IPC-2025)*

- **Unicité d'une Dimension** : 
  `[external_id]` canonique (ex: `SEXE`, `FREQ`).

- **Unicité d'une Modalité** : Une modalité n'existe qu'au sein d'une dimension.
  `[dimension_id] + [code_modalite]`
  *(Exemple : Dimension=SEXE + Code=F)*

- **Unicité d'une Série** : 
  `[dataset_id] + [external_series_id (ex: idbank)]`

- **Unicité d'une Observation (dans Parquet)** : 
  `[series_id] + [time_period]`

### 2.3 Conventions de nommage (Nommage Base de données)
- Tous les noms de tables et colonnes doivent être en `snake_case` (ex: `ingestion_runs`, `dataset_aliases`).
- Les dates de création et de mise à jour s'appelleront toujours `created_at` et `updated_at` (en UTC, format Timestamp with Timezone).
- Les booléens d'activation s'appelleront `is_active` (Par défaut à TRUE).

### 2.4 Historisation (La règle de la suppression)
- **Soft Delete** : Aucune donnée (Dataset, Dimension, Modalité) ne doit être supprimée (`DELETE`) physiquement de la base si elle disparaît de l'API de l'INSEE. 
- *Action* : Si l'INSEE retire une modalité, StatCheck doit basculer son champ `is_active` à `FALSE`. Cela garantit que les observations historiques de l'année précédente (qui utilisaient cette modalité) ne soient pas corrompues ("orphelines").

---

## 3. Définitions du Cycle de Vie (Ingestion)

### 3.1 Les États de traitement (Statuts)
Lorsqu'un processus d'ingestion (le "robot") tourne, chaque objet traité (une exécution, un téléchargement) doit obligatoirement avoir l'un des statuts suivants :
- `PENDING` : Tâche créée, en attente de traitement.
- `RUNNING` : En cours de téléchargement ou d'analyse.
- `SUCCESS` : Traité avec succès et enregistré en base.
- `FAILED` : Échec critique (erreur 500, format invalide) après épuisement des tentatives.
- `PARTIAL_SUCCESS` : L'exécution s'est terminée, mais avec quelques erreurs mineures non bloquantes.
- `CANCELLED` : Annulé volontairement ou stoppé par le système.

### 3.2 Règles de conservation (Rétention et Quarantaine)
- **Quarantaine** : Tout fichier XML/JSON téléchargé qui ne correspond pas au format attendu (invalide, tronqué) doit être placé dans le répertoire `data/quarantine/`. L'objet en base passe en état `FAILED` avec un lien vers ce fichier pour audit humain. Le système ne doit pas s'arrêter.
- **Rétention (JSON bruts)** : Les fichiers JSON/XML bruts originaux (`data/raw/`) doivent être conservés indéfiniment. Ils constituent la "preuve" mathématique (l'archive) de ce qui a été publié par l'INSEE à une date donnée.
- **Fichiers temporaires** : Le dossier `data/temporary/` doit être vidé automatiquement à chaque démarrage d'une nouvelle exécution d'ingestion (nettoyage des téléchargements avortés).

### 3.3 Le Versionnement : Méthode des 3 Hashs
Pour garantir que l'on détecte correctement une vraie révision mathématique par l'INSEE (et pas juste un changement de virgule ou d'espace dans leur fichier), on utilise une méthode stricte à 3 niveaux :

1. **Hash Brut (Preuve d'origine)** :
   - *Calcul* : SHA-256 direct sur les octets du fichier JSON/XML reçu de l'API.
   - *Rôle* : Savoir si l'INSEE a techniquement touché au fichier depuis la dernière fois.
2. **Hash Normalisé (Preuve de structure)** :
   - *Calcul* : SHA-256 généré après avoir trié les clés du JSON par ordre alphabétique et retiré les dates de téléchargement techniques.
   - *Rôle* : Éviter les fausses alertes si l'INSEE a juste renvoyé les mêmes données dans le désordre.
3. **Hash Métier (Alerte de Révision)** :
   - *Calcul* : SHA-256 calculé *uniquement* sur les valeurs mathématiques des observations extraites (la valeur, l'unité, la période).
   - *Rôle* : Si ce hash change, cela déclenche une alerte critique : l'INSEE a officiellement révisé un chiffre du passé !
