# Schéma Relationnel PostgreSQL - Phase 2 (Lot 2B)

Ce document explique l'organisation des tables dans notre future base de données PostgreSQL. Le schéma est découpé en **5 grands groupes de tables** (domaines), chacun ayant une responsabilité unique pour garantir la robustesse du système StatCheck.

---

## 1. Groupe "Fournisseurs" (Sources)
*Objectif : Savoir à qui on s'adresse pour récupérer les données.*

L'INSEE n'est qu'un fournisseur parmi d'autres potentiels (on pourrait un jour ajouter Eurostat ou la Banque Mondiale). De plus, l'INSEE expose plusieurs API (BDM, Melodi).

- **`sources`** : Contient l'identité du fournisseur (ex: `INSEE_BDM`). On y stocke l'URL de base, la limite de requêtes (pour ne pas se faire bannir), et un statut pour désactiver un fournisseur s'il est en maintenance.
- **`source_endpoints`** : Un fournisseur a plusieurs "portes d'entrée" (endpoints). Par exemple, pour l'INSEE BDM, il y a une URL pour la liste des datasets, une autre pour la structure, et une autre pour les valeurs. Les lister ici évite de coder des URLs "en dur" dans le script Python.

---

## 2. Groupe "Catalogue" (Métadonnées)
*Objectif : Le coeur de la recherche pour notre future IA.*

C'est ici que l'on range les "livres" de notre bibliothèque statistique.

- **`datasets`** : La table centrale. Contient les métadonnées officielles de chaque jeu de données (titre, description, fréquence, lien de documentation). C'est ce qu'on affiche en premier à l'utilisateur.
- **`dataset_aliases`** : L'INSEE utilise des termes très techniques. Cette table sert de "dictionnaire des synonymes" pour l'IA. Par exemple, l'alias "Chômage" pointera vers le dataset au nom complexe `EMPLOI-CHOMAGE-BIT-TRIM`.
- **`dataset_relations`** : Parfois, l'INSEE remplace un vieux dataset par un nouveau (ex: l'inflation base 2015 remplacée par la base 2025). Cette table permet de créer des liens de parenté (`remplace`, `est remplacé par`) entre les jeux de données.

---

## 3. Groupe "Structure" (Les Filtres)
*Objectif : Savoir comment interroger précisément un Dataset.*

Un jeu de données est inutile si on ne sait pas comment le filtrer. Par exemple, le chômage peut être filtré par Sexe, Âge et Région.

- **`dimensions`** : Le dictionnaire central des axes d'analyse (ex: la dimension `SEXE`).
- **`modalities`** : Les valeurs possibles pour une dimension (ex: pour la dimension `SEXE`, on aura `1=Hommes`, `2=Femmes`, `T=Ensemble`).
- **`dataset_dimensions`** : Associe un dataset à ses dimensions. Par exemple, elle indique que le dataset "Chômage" possède la dimension "Sexe", mais que cette dimension est à la 3ème position de la clé SDMX (capital pour générer l'ID de la série).
- **`dataset_dimension_modalities`** : Indique si une modalité précise est disponible pour ce dataset. (ex: La modalité "Corse" existe dans la géographie française, mais n'est peut-être pas mesurée pour le dataset Chômage).

---

## 4. Groupe "Séries" (L'index des mathématiques)
*Objectif : Faire le pont avec nos fichiers Parquet (les observations).*

- **`series`** : Une série est une combinaison unique de filtres (ex: "Chômage + Femmes + 15-24 ans"). Cette table contient le fameux `idbank` que nous cherchions à la main en Phase 1. 
- **`series_dimension_values`** : Au lieu de créer une table avec 50 colonnes (une par dimension possible), on utilise cette table pour lister verticalement les filtres appliqués à une série. C'est idéal pour la recherche SQL rapide.

---

## 5. Groupe "Ingestion et Audit" (La Salle de Contrôle)
*Objectif : Gérer le robot de téléchargement et assurer les preuves.*

Le catalogue de l'INSEE est énorme. Si on le télécharge, le script va tourner pendant des heures. S'il y a une coupure internet, on ne veut pas recommencer à zéro.

- **`ingestion_runs`** : Le journal de bord. À chaque fois qu'on lance le robot, on crée une ligne ici (ex: "Lancement du 14 Mars, statut RUNNING").
- **`ingestion_items`** : La "To-Do list" du robot. S'il y a 800 datasets à télécharger, il y aura 800 lignes ici. Si le robot plante au 500ème, il lira cette table au redémarrage pour reprendre au 501ème.
- **`resource_versions`** : Le coffre-fort. À chaque fois que l'INSEE modifie une donnée, on ajoute une ligne ici avec le Hash du fichier téléchargé. C'est ce qui permet de prouver qu'une donnée a été révisée par rapport à une date antérieure.
- **`ingestion_errors`** : Si le format d'un fichier de l'INSEE change et fait planter le script, l'erreur détaillée (traceback Python) est stockée ici pour qu'on puisse réparer le code sans avoir bloqué les 799 autres téléchargements réussis.
