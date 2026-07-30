# Documentation et Analyse Détaillée : Lot 3 (Pipeline d'Ingestion Automatisé)

Le Lot 3 de la Phase 2 est le moteur mécanique de StatCheck. C'est l'ensemble des scripts (le "Robot") chargé de dialoguer avec les API de l'INSEE pour peupler les bases de données créées lors du Lot 2. L'objectif était de garantir un fonctionnement totalement automatisé, idempotent et résilient aux erreurs.

---

## 1. La Philosophie d'Ingestion par "Niveaux"

L'ingestion ne se fait pas d'un seul bloc. L'API BDM/SDMX de l'INSEE est vaste et hiérarchique. Télécharger le catalogue, les structures, puis les observations simultanément provoquerait des timeouts et rendrait le débogage impossible. Nous avons donc découpé le robot en 3 sous-lots (niveaux).

### 1.1 Niveau 1 : Le Catalogue Brut (Sous-lot 3A)
Le but du Niveau 1 (implémenté via `catalog_ingester.py`) est purement exploratoire : lister tous les jeux de données existants.

1. **Interrogation :** Le robot récupère le fichier XML global du *dataflow* INSEE.
2. **Preuve Cryptographique :** Le fichier est immédiatement hashé (SHA-256) et sauvegardé dans `data/raw/`. Son hash est enregistré en base (`resource_versions`).
3. **Le "Fast-Path" (Idempotence rapide) :** C'est l'optimisation clé. Si le hash du fichier téléchargé est identique au hash du dernier *Run* réussi, le script s'arrête instantanément. Il "sait" que rien n'a changé côté INSEE, économisant ainsi de précieuses minutes d'itération en base de données.
4. **L'Upsert :** S'il y a du changement, le script boucle sur chaque nœud XML. Il exécute des `INSERT` pour les nouveautés et des `UPDATE` si les métadonnées (titre, description) ont évolué.

### 1.2 Niveau 2 : Structures et Modalités (Sous-lot 3B & 3C)
Une fois que StatCheck connaît l'existence du dataset "Chômage", il doit comprendre **comment** le filtrer. C'est le rôle du Niveau 2.

1. **Extraction de la DataStructure :** Le robot demande à l'API SDMX la structure spécifique du dataset. Il récupère l'ordre exact des dimensions (ex: d'abord le Sexe, ensuite l'Âge).
2. **Codelists (Modalités) :** Pour chaque dimension, le robot télécharge la liste des valeurs autorisées (les `codelists`).
3. **Gestion de l'Historisation :**
   - Règle stricte : **On ne supprime jamais.** Si l'INSEE décide de retirer la modalité "15-24 ans" de l'API demain, nous ne faisons pas de `DELETE` en base, car nous pourrions avoir d'anciennes données Parquet (Niveau 3) qui s'y réfèrent. 
   - L'idempotence s'applique ici aussi : l'exécution multiple ne duplique aucune modalité.

### 1.3 Niveau 3 : Préparation des Observations (Sous-lot 3D)
Le niveau 3 s'attaque à la data pure : les séries temporelles.
- **Requêtage :** Le robot télécharge les JSON/XML contenant les millions de valeurs (les pourcentages de chômage par mois, par exemple).
- **Transformation Parquet :** Plutôt que d'inonder PostgreSQL (qui gère très mal les milliards de lignes temporelles simples), les données sont transformées en DataFrames. Elles sont standardisées (gestion des statuts : définitif, provisoire, révisé) puis écrites au format compressé **Parquet**.
- **Partitionnement :** Les fichiers Parquet sont sauvegardés intelligemment (ex: `data/normalized/INSEE_BDM/CHOMAGE/2026/`).

---

## 2. La Sécurité d'Exécution

Le pipeline d'ingestion est une machinerie lourde fonctionnant potentiellement la nuit (CRON job). Il fallait le doter de garde-fous.

### 2.1 Les Sessions d'Audit (`ingestion_runs`)
- Avant la première requête réseau, le robot crée une ligne en base avec le statut `RUNNING`.
- Si un script Python plante violemment (coupure mémoire, OOM), le statut restera bloqué sur `RUNNING` (ou `FAILED`), servant de signal d'alarme pour l'administrateur.

### 2.2 Résilience et Reprise sur Erreur (Fault Tolerance)
- Si le script boucle sur 500 datasets (Niveau 2) et que l'API INSEE renvoie une erreur 502 (Bad Gateway) sur le 400ème :
  - Le système ne crash pas globalement.
  - Il enregistre l'échec dans `ingestion_errors` avec le détail HTTP.
  - Il passe au dataset 401.
- **La Reprise :** Au prochain lancement, le robot ignore automatiquement les 399 premiers (déjà marqués en succès) et ne retente que ceux en échec ou manquants. C'est l'essence même d'un pipeline robuste.

## Conclusion du Lot 3
Le Lot 3 a transformé une simple base de données vide (Lot 2) en un organisme vivant capable de se synchroniser automatiquement avec le gouvernement. Ses mécanismes cryptographiques (Hash) et de résilience (Upsert, Reprise sur erreur) garantissent que les données ingérées par StatCheck sont non seulement exactes, mais juridiquement prouvables grâce à l'archivage brut des requêtes originales.
