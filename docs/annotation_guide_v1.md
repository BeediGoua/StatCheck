# Guide d'Annotation du Corpus Gold (v1.0)

Ce guide définit les règles strictes d'annotation pour la validation du module `StatCheck`.
L'annotation s'effectue via les tables `gold_annotations` et `gold_annotation_keys`.

## 1. Unité d'Annotation
L'unité fondamentale est le triplet : `(claim_id, dataflow_id, metadata_snapshot_id)`.
Une affirmation ne peut avoir qu'une seule vérité terrain par jeu de données INSEE (dataflow) pour une version donnée de ses métadonnées (snapshot).

## 2. Statut Attendu (`expected_status`)
- **FOUND** : La série statistique exacte correspondant à l'affirmation existe.
- **NOT_FOUND** : Le sujet existe mais la combinaison précise de dimensions ou la période est inexistante ou interdite.
- **AMBIGUOUS** : La phrase est trop vague ou incomplète pour trancher avec certitude entre plusieurs séries fondamentalement différentes.

## 3. Clés de Série Acceptables (`gold_annotation_keys`)
Pour chaque statut `FOUND`, au moins une clé SDMX ordonnée (`expected_ordered_key`) doit être fournie.
- **EXACT** : Correspond parfaitement à la demande.
- **ACCEPTABLE** : Correspond à une approximation valide (ex: un indice de substitution très proche).
- **INSUFFICIENT** : La clé est techniquement valide pour le dataflow, mais sémantiquement insuffisante pour la phrase (utilisée pour vérifier le rejet par le LLM).

## 4. Exceptions et Limites
- `forbidden_substitutions` : Liste explicite des dimensions ou codes que le modèle NE DOIT PAS inférer (ex: interdire l'inférence "France Entière" si la phrase parle d'une ville précise).
- `allowed_defaults` : Liste explicite des codes par défaut acceptés pour une dimension omise par l'utilisateur.
- `ambiguities` / `limitations` : Explications textuelles pour l'arbitrage.

*Généré automatiquement.*
