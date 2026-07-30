# Snapshot Documenté : Catalogue de 222 Datasets (Lot 7)

## 1. Provenance des Données

Ce catalogue expérimental a été constitué à partir de **fichiers XML bruts au format SDMX 2.1**.
- **Source :** API INSEE, banque de données macroéconomiques (BDM).
- **Emplacement brut :** `data/raw/insee_bdm_structure_*.xml`
- **Volume initial :** 233 fichiers XML.
- **Volume extrait après déduplication :** 222 datasets uniques.

## 2. Structure SDMX et Limites de Métadonnées

L'investigation du format de l'INSEE a révélé une limite fondamentale sur la richesse sémantique disponible pour la vectorisation :

Dans les fichiers SDMX fournis par la BDM, l'information textuelle se trouve exclusivement dans la balise `<structure:DataStructure>`, sous la forme de `<common:Name>`.
**Il n'y a aucune balise `<common:Description>`** permettant de décrire le jeu de données de manière plus exhaustive.

Exemple d'extraction sur le `CHOMAGE-TRIM-NATIONAL` :
- **Titre (Name) :** "Chômage, taux de chômage par sexe et âge (sens BIT)"
- **Description :** Vide (non fournie par la source).
- **Dimensions :** "SEXE", "AGE", etc.

### Impact sur le Moteur de Recherche
Le fait que la description soit systématiquement vide dans le Snapshot BDM explique les performances limitées observées lors du benchmark initial :
- Le `tsvector` FTS repose uniquement sur le Titre (Poids A) et les Dimensions (Poids B).
- L'embedding généré par `MiniLM-L12` encode un texte très court : *"Dataset: Chômage... (CHOMAGE). Description: . Dimensions: SEXE, AGE"*.

## 3. Identifiants extraits (Exemples)
- `BALANCE-PAIEMENTS`
- `CHOMAGE-TRIM-NATIONAL`
- `CLIMAT-AFFAIRES`
- `CNA-2014-PIB`
- `IPC-2015`

## 4. Conclusion du Snapshot
Le snapshot des 222 datasets est **fiable et reflète la dure réalité des API Insee** (très peu de texte, forte granularité technique).
L'évaluation scientifique sur ce jeu de données sera donc un véritable "stress-test" pour l'algorithme de RRF (Reciprocal Rank Fusion), qui devra compenser l'absence de description par le matching strict des dimensions.
