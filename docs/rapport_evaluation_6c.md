# Rapport d'Évaluation Détaillé (Lot 6C) : Architectures C0 à C3

Ce document de synthèse détaille les résultats de la campagne d'évaluation menée sur le corpus de validation StatCheck (Lot 6C). 
L'objectif est d'apporter des métriques quantifiables et des analyses qualitatives pour trancher sur le choix de l'**Architecture V1** en production.

---

## 1. Définitions et Protocole Expérimental

L'évaluation repose sur un corpus de validation de **20 affirmations économiques pilotes**.
Chaque affirmation a été soumise à deux extracteurs fondamentalement différents.

### 1.1 Définitions des Métriques
- **Exact Match Complet** : Une prédiction est comptée en Exact Match uniquement si tous les champs obligatoires correspondent au Gold après normalisation : indicateur, territoire, période, opération, mesures, unités et statut d’abstention. Une erreur sur un seul champ rend l’affirmation incorrecte au niveau Exact Match.
- **Erreur Critique Silencieuse** : Une erreur critique silencieuse est une sortie déclarée exploitable qui modifie le sens statistique de l’affirmation sans déclencher d’abstention ni de signal d’incertitude : valeur, unité, signe, période, territoire, population, dénominateur ou indicateur incorrect.

### 1.2 L'Architecture C0 (La Baseline 6A)
- **Technologie** : Déterministe. Moteur hybride utilisant `spaCy` (modèle `fr_core_news_lg`), expressions régulières et lexiques géographiques.
- **Paradigme** : Si la donnée n'est pas explicite ou ne matche pas un pattern connu, la Baseline refuse de s'engager (`MISSING_CONTEXT`).

### 1.3 L'Architecture C1 (LLM Local - Qwen2.5)
- **Technologie** : Probabiliste. Modèle interrogé localement sans réseau.
- **Reproductibilité** :
  - Modèle : `qwen2.5:7b-instruct-q4_K_M` (le digest exact est consigné dans le manifeste `checksums.sha256`).
  - Serveur : `Ollama v0.1.27` vérifié dans les journaux d'exécution.
  - Paramètres : `temperature = 0.2`, `seed = 42`, `top_p = 0.9`, `num_ctx = 4096`.
  - Artefacts : Les hashs du prompt système et du JSON Schema sont inclus dans le package de release.
- **Protocole des 3 passages** : Le passage numéro 1, déterminé avant l’expérience, sert au calcul des performances principales. Les trois passages servent uniquement à mesurer la stabilité. Aucune sélection a posteriori de la meilleure sortie n’est autorisée.

---

## 2. Analyse Approfondie de l'Architecture C0 (Baseline)

### 2.1 Métriques de Performance Opérationnelle
- **Latence** : Le temps de traitement par affirmation oscille entre **0 ms et 80 ms** (moyenne ~20 ms). C'est un atout majeur pour un traitement à très haute volumétrie.
- **Coût d'infrastructure** : Quasi nul.

### 2.2 Analyse Qualitative par Champ
- 🟢 **Points Forts** : La baseline est prioritaire sur les valeurs numériques explicites lorsque ses règles déterministes produisent une extraction validée et non ambiguë (ex: `12 %`). 
- 🔴 **Points Faibles** : Les patterns syntaxiques stricts ne parviennent pas à isoler l'indicateur cible si la formulation est complexe, menant à une couverture globale très faible.

---

## 3. Analyse de l'Architecture C1 (LLM - Qwen2.5)

L'inférence a été exécutée. Les résultats confirment l'intérêt mais aussi le danger du LLM.

### 3.1 Promesses Théoriques Validées
- **Identification des Indicateurs** : Le F1 score sur les indicateurs bondit à 85%.
- **Le Danger de l'Implicite** : Le modèle tend à inférer que le contexte français implique le territoire "France". Dans un système de fact-checking, l’absence de territoire est une information importante. Cela doit être géré avec prudence (`territory.status = INFERRED`, `confidence = moyenne`) et ne remplace pas la valeur stricte `MISSING` si aucun contexte externe ne justifie l'inférence.

### 3.2 Dangers Observés (Erreurs Silencieuses)
- **Hallucinations Numériques** : Le LLM a généré des erreurs critiques (ex: confusion entre hausse en points et en %). Ces erreurs de C1 sont comptées **après post-validation** (la validation n'a pas pu les bloquer car la structure JSON était sémantiquement valide mais mathématiquement fausse).

**Détail des erreurs (Dénominateurs stricts) :**
| Mesure | Numérateur | Dénominateur |
|---|---:|---:|
| Sorties avec erreur critique | 3 | 60 exécutions |
| Affirmations touchées | 2 | 20 affirmations |

---

## 4. Conclusion Préliminaire et Design de la Fusion (Architectures C2 & C3)

L'évaluation de la Baseline prouve qu'**une architecture C0 seule n'est pas viable pour la production**.
La stratégie de **Fusion** s'impose. La Matrice d'Autorité donne la priorité à la Baseline pour les extractions déterministes validées, et au LLM pour la sémantique.

### La Cascade (C3) vs Parallèle (C2)
L'Architecture C3 (Cascade) se positionne comme le candidat opérationnel. 
**Le vrai principe de déclenchement de C3 est :** Appeler le LLM lorsque la baseline est incomplète, ambiguë, incohérente ou insuffisamment fiable. (Et non pas uniquement lorsqu'elle lève un `MISSING_CONTEXT`).

---

## 5. Tableau de Comparaison Final (Split de Validation)

| Métrique | C0 (Baseline) | C1 (LLM seul) | C2 (Fusion Parallèle) | C3 (Cascade) |
|---|---:|---:|---:|---:|
| Exact Match complet | 25.0% | 60.0% | 85.0% | 85.0% |
| F1 indicateur | 15.0% | 85.0% | 85.0% | 85.0% |
| F1 mesure | 95.0% | 75.0% | 95.0% | 95.0% |
| Erreurs critiques silencieuses | **0** | **3** | **0** | **0** |
| Couverture (Absence d'abstention) | 30.0% | 95.0% | 95.0% | 95.0% |
| Taux d'appel LLM | 0.0% | 100.0% | 100.0% | **70.0%** |

---

## 6. Arbitrage de l'Architecture V1 (Étape 8)

Conformément à la politique d'élimination formelle :
1. **Filtre Sécurité** : Les architectures C0, C2 et C3 n'ont produit aucune erreur critique silencieuse. C1 est éliminé pour violation du seuil.
2. **Comparaison appariée de C2 et C3** : 
   - Sur les 20 affirmations de validation, aucune discordance n’a été observée entre les décisions finales de C2 et C3.
   - En l’absence de paire discordante, le test de McNemar n’apporte pas d’information statistique exploitable.
   - Cette observation ne démontre pas l’équivalence générale des deux architectures.
3. **Candidat Pareto-préféré** : Sur les métriques actuellement mesurées, C3 est préférée à C2 : les deux architectures obtiennent les mêmes scores observés, tandis que C3 effectue 30 % d’appels LLM en moins. Cette préférence devra être confirmée par les mesures réelles de latence et de consommation.

**Décision d'ingénierie : L'architecture C3 est promue V1 pour la suite du développement.**

---

## 7. Le Grand Test Final (Étape 9)

Un ultime run a été exécuté sur **40 affirmations inédites**.

- **Exact Match Complet** : 77,5 % — IC 95 % [62,5 % ; 87,7 %], calculé avec l’intervalle de Wilson à partir de 31 affirmations entièrement correctes sur 40.
- **Erreurs critiques silencieuses observées** : 0

*Note sur le risque :* Aucune erreur critique silencieuse n’a été observée sur les 40 affirmations du test. Compte tenu de la taille de l’échantillon (règle de trois), la borne supérieure du risque est d'environ 7,5%. Cela ne permet pas d'affirmer que le risque réel est nul.

- **Package de Preuve** : Le package final `evaluation/releases/v1-final-test/` contient les 40 entrées, les prédictions, la configuration exacte de C3, le digest du modèle, et les métriques recalculables. Le manifeste `checksums.sha256` permet de vérifier l’intégrité du package à partir de sa date de scellement.

**Conclusion Globale :**
Ce test fournit une première validation expérimentale, reproductible et encourageante de l’architecture V1 sur le périmètre économique étudié. Une généralisation à d’autres domaines et à des volumes plus importants reste nécessaire.

---

## 8. Travaux Futurs (Prochaine Campagne)

L'évaluation a répondu à ses objectifs de choix d'architecture opérationnelle. La prochaine grande campagne de validation (pour publication) devra intégrer :
1. L'extension du corpus et une mesure mathématique de l'accord inter-annotateurs.
2. Une évaluation formelle et séparée de la politique dynamique d’abstention.
3. La fourniture des matrices d'erreurs multi-classes détaillées (par sous-groupe).
4. Les relevés de consommation système réels (Temps de chargement du LLM, latences d'inférence p50/p95/p99, empreinte VRAM).
