# Arborescence de Stockage des Données (StatCheck)

Ce répertoire `data/` contient l'ensemble des fichiers bruts et transformés gérés par le pipeline d'ingestion de StatCheck.

Il est divisé en plusieurs sous-répertoires stricts pour garantir la traçabilité et l'auditabilité :

- **`raw/`** : L'archive inaltérable. Contient les fichiers JSON/XML exacts tels que téléchargés depuis l'INSEE. C'est la "preuve" mathématique d'origine.
- **`normalized/`** : Les données prêtes pour le calcul. Contient les observations (les chiffres) converties au format colonnaire **Parquet**. C'est ce dossier que `Pandas` lira pour le moteur de fact-checking.
- **`manifests/`** : Les métadonnées de téléchargement. Fichiers descriptifs contenant la date exacte, les headers HTTP et les statuts des opérations d'ingestion.
- **`quarantine/`** : La zone d'isolement. Les fichiers API corrompus, tronqués ou ne respectant pas le schéma attendu y sont placés pour analyse manuelle sans bloquer le reste de l'ingestion.
- **`temporary/`** : Zone de transit. Utilisée par le robot pendant le téléchargement des gros fichiers pour éviter d'enregistrer un fichier incomplet en cas de coupure réseau. Vidé automatiquement à chaque démarrage.

> [!WARNING]  
> Ne modifiez **jamais** les fichiers dans le dossier `raw/` manuellement. Toute modification corromprait le Hash cryptographique (`raw_hash`) stocké dans PostgreSQL, ce qui déclencherait une alerte de falsification.
