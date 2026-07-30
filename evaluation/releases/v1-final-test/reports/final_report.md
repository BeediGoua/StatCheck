# Rapport Officiel du Test Final (V1)

## Contexte
L'objectif de StatCheck est d'extraire de manière déterministe et fiable des statistiques depuis du texte libre. Ce rapport consigne l'évaluation finale.

## Architecture
- **Architecture retenue** : V1 (Cascade C3).
- **Modèle** : Qwen2.5 via Ollama (avec Baseline locale).

## Données
- **Corpus** : 40 affirmations inédites.
- **Hash du test manifest** : 36c0ded63b1682a1a6fff5b9649f660a5a017f4e7b20e182d3874018a9000fe8

## Protocole
Une seule campagne d'évaluation. Aucun ajustement post-évaluation.

## Résultats
- **Exact Match** : 77.5% [IC95%: 65.0% - 90.0%]
- **Erreurs critiques silencieuses** : 0

## Limites
Taille du test limitée (40 items). Ne couvre pas l'ensemble des cas ambigus possibles. Dépendance au modèle local pour les cas extrêmes.

## Conclusion
Sur un jeu de test gelé de 40 affirmations statistiques françaises, jamais utilisé pendant le développement, l'architecture V1 a correctement produit l'interprétation complète de 31 affirmations sur 40. Les résultats restent exploratoires compte tenu de la taille du corpus et du périmètre limité aux sources couvertes.
