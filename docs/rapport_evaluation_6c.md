# Rapport d'Évaluation Détaillé (Lot 6C) : Architectures C0 à C3

Ce document de synthèse détaille les résultats de la campagne d'évaluation menée sur le corpus de validation StatCheck (Lot 6C). 
L'objectif est d'apporter des métriques quantifiables et des analyses qualitatives pour trancher sur le choix de l'**Architecture V1** en production.

---

## 1. Protocole Expérimental

L'évaluation repose sur un corpus de validation de **20 affirmations économiques pilotes**.
Chaque affirmation a été soumise à deux extracteurs fondamentalement différents :

### 1.1 L'Architecture C0 (La Baseline 6A)
- **Technologie** : Déterministe. Moteur hybride utilisant `spaCy` (modèle `fr_core_news_lg`) pour l'analyse syntaxique, complété par un moteur d'expressions régulières et un matching par lexiques géographiques (COG Insee).
- **Paradigme** : Si la donnée n'est pas explicite ou ne matche pas un pattern connu, la Baseline refuse de s'engager (`MISSING_CONTEXT`).

### 1.2 L'Architecture C1 (LLM Local - Qwen2.5)
- **Technologie** : Probabiliste. Modèle interrogé localement.
  - *Note de reproductibilité :* Pour garantir la reproductibilité, le modèle utilisé est `Qwen2.5 7B` (Quantification `Q4_K_M`), via Ollama v0.1.27, avec une température fixée à 0.2.
- **Paradigme** : Compréhension sémantique globale de l'affirmation, structuration via un schéma strict, et correction a posteriori par une chaîne de validateurs déterministes.
- **Protocole de variabilité** : Afin d'isoler la stochasticité inhérente aux LLMs, chaque affirmation est traitée **3 fois** (soit 60 inférences au total).

---

## 2. Analyse Approfondie de l'Architecture C0 (Baseline)

La Baseline a été exécutée sur l'intégralité du corpus. Les logs révèlent les tendances suivantes :

### 2.1 Métriques de Performance Opérationnelle
- **Latence** : Le temps de traitement par affirmation oscille entre **0 ms et 80 ms** (moyenne ~20 ms). C'est un atout majeur pour un traitement à très haute volumétrie.
- **Coût d'infrastructure** : Quasi nul.

### 2.2 Analyse Qualitative par Champ

#### 🟢 Points Forts (Haute Précision)
1. **Mesures et Unités (`measures`)** :
   - La baseline est prioritaire sur les valeurs numériques explicites lorsque ses règles déterministes produisent une extraction validée et non ambiguë (ex: `12 %`, `6 millions`). 
2. **Géographie Explicite (`territory`)** :
   - Matching direct avec la taxonomie COG lorsque le territoire est formellement nommé.

#### 🔴 Points Faibles (Faible Recall)
1. **Incapacité Sémantique sur les Indicateurs** :
   - Les patterns syntaxiques stricts ne parviennent pas à isoler l'indicateur cible si la formulation est complexe, menant souvent à un rejet (`MISSING_CONTEXT`).
2. **Périodes temporelles complexes (`time`)** :
   - Les expressions relatives telles que *"depuis quinze ans"* ou *"sur un an"* embrouillent le parseur.

---

## 3. Analyse de l'Architecture C1 (LLM - Qwen2.5)

L'inférence des 60 itérations a été exécutée. Les résultats confirment l'intérêt mais aussi le danger du LLM.

### 3.1 Promesses Théoriques Validées
- **Identification des Indicateurs** : Le F1 score sur les indicateurs bondit à 85%.
- **Le Danger de l'Implicite** : Le modèle tend à inférer que le contexte d'une phrase d'actualité française implique le territoire "France". Cependant, dans un système de fact-checking, cela doit être géré avec une extrême prudence (`territory.status = INFERRED`, `confidence = moyenne`) et ne doit surtout pas remplacer la valeur stricte `MISSING` sans preuve contextuelle.

### 3.2 Dangers Observés (Erreurs Silencieuses)
- **Stabilité** : Bonne, mais 15% des requêtes souffrent de légères dérives stochastiques sur le choix des termes canoniques (sur les 3 passages).
- **Hallucinations Numériques (Le point noir)** : Le LLM a généré des erreurs critiques (confusion entre hausse en points et en %, ou invention d'une année).

**Détail des erreurs (Dénominateurs stricts) :**
| Mesure | Numérateur | Dénominateur |
|---|---:|---:|
| Sorties avec erreur critique | 3 | 60 exécutions |
| Affirmations touchées | 2 | 20 affirmations |

---

## 4. Conclusion Préliminaire et Design de la Fusion (Architectures C2 & C3)

L'évaluation de la Baseline prouve qu'**une architecture C0 seule n'est pas viable pour la production** en raison de sa faible couverture.
La stratégie de **Fusion** s'impose. La Matrice d'Autorité donne la priorité à la Baseline pour les nombres, dates et codes, et au LLM pour la sémantique et les relations.

### La Cascade (C3) vs Parallèle (C2)
L'Architecture C3 (Cascade) se positionne comme le candidat opérationnel. 
**Le vrai principe de déclenchement de C3 est :** Appeler le LLM lorsque la baseline est incomplète, ambiguë, incohérente ou insuffisamment fiable (et non pas uniquement lorsqu'elle renvoie `MISSING_CONTEXT`, car une baseline peut retourner un résultat complet mais erroné).

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
1. **Filtre Sécurité** : Les architectures C0, C2 et C3 n'ont produit aucune erreur critique silencieuse. C1 est éliminé.
2. **Test de McNemar (C2 vs C3)** : Sur les 20 affirmations du split de validation, aucune différence n’a été observée entre C2 et C3. La taille réduite de l’échantillon ne permet toutefois pas de démontrer leur équivalence générale.
3. **Front de Pareto** : C3 est le candidat préféré sur la validation, car il atteint les mêmes scores observés que C2 avec 30 % d’appels LLM en moins (réduction relative de 100% à 70%). Cette domination opérationnelle doit être confirmée à l'avenir par des métriques d'infrastructure exhaustives (temps p95/p99, RAM, coût énergétique).

**Décision d'ingénierie : L'architecture C3 est promue V1 pour la suite du développement.**

---

## 7. Le Grand Test Final (Étape 9)

Un ultime run a été exécuté sur **40 affirmations inédites**.

- **Exact Match Complet** : 77.5% [IC 95%: 65.0% - 90.0% *(Calculé par approximation de Wilson)*]
- **Erreurs critiques silencieuses observées** : 0

*Note sur le risque :* Aucune erreur critique silencieuse n’a été observée sur les 40 affirmations du test. Compte tenu de la taille de l’échantillon (règle de trois), la borne supérieure du risque est d'environ 7,5%. Cela ne permet pas d'affirmer que le risque réel est nul.

- **Package de Preuve** : `evaluation/releases/v1-final-test/`. Le manifeste `checksums.sha256` permet de vérifier l’intégrité du package à partir de sa date de scellement.

**Conclusion Globale :**
Ce test fournit une première validation expérimentale, reproductible et encourageante de l’architecture V1 sur le périmètre économique étudié. Une généralisation à d’autres domaines et à des volumes plus importants reste nécessaire.

---

## 8. Ce qu'il manque au rapport (Travaux Futurs)

Pour considérer ce rapport comme scientifiquement publiable (ex: soumission à une conférence), il devra être complété par les éléments suivants lors de la prochaine campagne :
1. La composition exacte des 20 et 40 affirmations et leur répartition par difficulté.
2. Les règles d’annotation du Gold, le nombre d’annotateurs, et l'accord inter-annotateurs.
3. La définition formelle mathématique de chaque métrique.
4. Les scores par champ, les matrices d'erreurs, et les résultats par sous-groupe.
5. Les vrais temps de latence (p50, p95, p99) et le calcul précis du coût LLM.
6. Le protocole exact d’agrégation des trois passages LLM.
7. La liste anonymisée de toutes les erreurs.
8. La politique d’abstention et son évaluation séparée.
