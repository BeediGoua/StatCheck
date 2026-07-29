# Rapport de Qualité - Fin de Phase 2

## 1. Volumétrie Globale
- **Datasets** : 229
- **Dimensions (Filtres)** : 59
- **Modalités (Valeurs)** : 6891
- **Séries Temporelles (Pilotes)** : 2954

## 2. Traçabilité et Robustesse
- **Traçabilité** : 229 / 229 datasets ont une origine traçable (Source = INSEE_BDM).
- **Résilience** : Le mécanisme `try/except` a prouvé son efficacité. Les erreurs de l'API ont été isolées sans bloquer le reste du pipeline.

## 3. Statut des Ingestions (Derniers Runs)

### Structures SDMX
- **SUCCESS** : 29
- **RUNNING** : 1

### Observations (Data Pilotes)
- **SUCCESS** : 4
- **FAILED** : 11
