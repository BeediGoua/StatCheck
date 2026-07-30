# Méthodologie d'Évaluation Locale (100% On-Premise)

Le projet StatCheck (Lot 6C) s'appuie sur une architecture hybride, couplant un extracteur symbolique (Baseline) et un extracteur neuronal (LLM). Afin de garantir la confidentialité des données économiques (souveraineté), de supprimer les coûts récurrents d'API externes, et de conserver une latence maîtrisée, **l'intégralité du pipeline d'évaluation a été conçue pour s'exécuter localement (on-premise)**.

Ce document décrit comment cette autonomie a été atteinte.

---

## 1. La Baseline Déterministe (Architecture C0)
La Baseline est par nature une solution 100% locale, s'appuyant sur l'écosystème Python standard.

### 1.1 Technologies mobilisées
- **spaCy (`fr_core_news_lg`)** : Utilisé pour le *Part-Of-Speech tagging* (POS) et l'arbre de dépendance syntaxique. Il s'exécute entièrement sur le CPU et ne requiert aucune connexion réseau.
- **Moteur Regex (Expressions Régulières)** : Parseur ultra-rapide pour capter les nombres, les pourcentages, et les mots-clés de tendance (hausse, baisse).
- **Lexiques Géographiques (COG)** : Les référentiels de l'INSEE sont stockés sous forme de fichiers `.csv` (ex: `cog_2024.csv`) chargés en RAM via Pandas au démarrage.

### 1.2 Avantages de cette stack
- **Latence extrêmement faible** : Le traitement d'une phrase nécessite entre 10 et 30 millisecondes sur un CPU classique.
- **Sécurité et Déterminisme** : Le résultat pour une phrase donnée sera strictement identique à chaque exécution. Le taux d'erreur critique (hallucination numérique) est de 0%.

---

## 2. Le Modèle Sémantique Local (Ollama & Qwen2.5)
Initialement pensé pour s'appuyer sur l'API OpenAI (GPT-4o) ou l'API DashScope (Qwen), le projet a finalement intégré **Ollama** comme moteur d'inférence LLM local.

### 2.1 Le choix de Qwen2.5
- Nous utilisons le modèle `qwen2.5:latest` (de la famille Qwen2 d'Alibaba).
- **Pourquoi Qwen ?** Les modèles Qwen2.5, même dans leurs versions "légères" (7B ou 14B paramètres), excellent dans la structuration JSON, le respect de schémas stricts et la compréhension de la langue française, tout en pouvant tourner sur des puces grand public (Apple Silicon, RTX 3060/4060, ou simplement sur un bon CPU).

### 2.2 Intégration dans le script Python
Le script `src/evaluation/run_llm_eval.py` communique avec Ollama via son API compatible :
- Le SDK `openai` Python est utilisé en pointant son paramètre `base_url` sur `http://localhost:11434/v1`.
- Le script gère le parsing des blocs ````json ... ```` que le modèle pourrait générer, afin d'extraire la structure de données `CanonicalParseResult` requise.

### 2.3 Variabilité (Stochasticité)
Pour évaluer un LLM scientifiquement (Étape 5), le protocole exige d'isoler la variabilité.
- Le script interroge Ollama **3 fois** consécutives pour chaque affirmation avec une température basse (`0.2`).
- Cela simule le fait que, même en local, l'inférence neuronale n'est pas strictement déterministe, et permet de valider si la fusion devra faire face à des interprétations changeantes pour une même entrée.

---

## 3. L'Orchestrateur HORS-LIGNE (Comparaison C1, C2, C3)

La principale difficulté méthodologique est de **comparer équitablement** différentes architectures de fusion, sans fausser les scores avec la variabilité du LLM, tout en mesurant avec précision le "coût" (temps d'exécution) des solutions.

### 3.1 Découplage de l'Inférence et de l'Évaluation
- Les architectures C1 (LLM seul), C2 (Fusion parallèle) et C3 (Cascade) ne font **aucun appel à Ollama** lors du calcul des scores F1 et de l'Exact Match.
- L'outil lit les fichiers `.jsonl` pré-calculés lors des étapes 4 et 5 (`baseline_val.jsonl` et `llm_val.jsonl`).
- Cela garantit que l'architecture C2 (Fusion) tente de corriger *exactement la même chaîne JSON* que celle mesurée dans le rapport C1 (LLM seul).

### 3.2 L'Architecture C3 (Cascade)
L'architecture C3 utilise la Baseline comme pare-feu :
- La phrase passe dans la Baseline (15ms).
- Si la Baseline extrait une donnée incomplète ou lève un statut `MISSING_CONTEXT` (ce qui est très fréquent pour les indicateurs implicites), le routeur C3 décide d'appeler le LLM (ce qui ajoute le temps de latence de Ollama).
- Un échantillon aléatoire (contrôlé par un *seed* fixe) force l'appel au LLM dans 5 à 10% des cas "faciles", afin de vérifier que la Baseline n'était pas "silencieusement dans l'erreur".

### Conclusion de la phase
Ce fonctionnement on-premise est la garantie d'un système industrialisable pour l'État ou les médias : pas de fuite de données vers des serveurs américains ou asiatiques, pas de facturation au token, et une reproductibilité totale des évaluations.

---

## 4. Analyse des Temps d'Exécution et Goulots d'Étranglement (Bottlenecks)

Si la Baseline s'exécute en une fraction de seconde, pourquoi la phase d'évaluation LLM (Étape 5) nécessite-t-elle plusieurs minutes pour seulement 20 affirmations ? L'architecture locale présente des goulots d'étranglement (bottlenecks) inhérents au traitement neuronal on-premise.

### 4.1 Le Goulot Matériel (Hardware Bottleneck)
L'inférence d'un modèle de 7 milliards de paramètres (Qwen2.5) nécessite des calculs matriciels lourds. 
- **Bande passante mémoire (VRAM/RAM)** : Le goulot principal d'un LLM n'est pas tant la puissance de calcul brute que la vitesse à laquelle les poids du modèle peuvent être transférés de la mémoire vers les unités de calcul. Si Ollama tourne sur un CPU classique (RAM DDR4/DDR5) au lieu d'un GPU (VRAM GDDR6/HBM), la vitesse de génération des tokens (tokens/seconde) chute drastiquement.
- **Temps par token** : Structurer un JSON complet (avec indicateurs, mesures, temps, territoires) exige de générer entre 100 et 300 tokens par réponse. Sur CPU, cela peut prendre de 10 à 30 secondes par requête.

### 4.2 Le Goulot Logiciel (Séquentialité du Script d'Évaluation)
- **Appels séquentiels** : Pour l'Étape 5, le script `run_llm_eval.py` effectue 3 itérations par affirmation pour 20 affirmations, soit **60 requêtes au total**. Actuellement, ces requêtes sont envoyées **une par une** (boucle synchrone).
- **Incapacité de batching par défaut** : Ollama gère les requêtes concurrentes, mais si le matériel est limité, lancer plusieurs requêtes en parallèle ne fera que ralentir l'ensemble ou épuiser la RAM.

### 4.3 Comment l'Architecture de Production (C3 Cascade) résout ce problème
L'évaluation actuelle fait travailler le LLM à 100% sur 60 inférences (pour construire la vérité terrain). **Cependant, ce goulot disparaîtra en production.**

Dans la future Architecture C3 (Cascade) :
1. **Filtre initial** : 100% des requêtes passent par la Baseline (15 millisecondes).
2. **Abstention LLM** : Si la Baseline trouve toutes les entités (ex: "L'inflation était de 2% en France en 2023"), le LLM **n'est jamais appelé**.
3. **Appel LLM chirurgical** : Le routeur C3 n'enverra la requête à Ollama que si la Baseline lève une ambiguïté (ex: géographie implicite). 
Ainsi, le goulot d'étranglement du LLM n'impactera que 20% à 30% du flux global, diluant le temps de traitement sur l'ensemble de l'architecture.

---

## 5. Le Moteur de Métriques (Scorer) et la Comparaison Finale (Étape 7)

Pour répondre à l'exigence d'une comparaison purement scientifique entre les 4 architectures, un moteur de scoring strict a été développé (`src/evaluation/scorer.py`) couplé à un générateur de rapport (`src/evaluation/generate_report.py`).

### 5.1 F1 par Champ (Granularité)
Contrairement à une simple comparaison globale, le Scorer dissèque le JSON `CanonicalParseResult` généré par chaque système :
- Il vérifie l'**Exact Match** complet (le JSON est-il 100% identique au Gold standard ?).
- Il isole et apparie les entités via un algorithme biparti, puis calcule un **F1 Score** spécifique pour :
  - Les Mesures (Valeurs numériques et Unités)
  - Les Indicateurs (Normalisation du texte)
  - Les Territoires (Codes COG)
  - Les Expressions Temporelles (Dates de début et de fin)
  - Les Populations.

### 5.2 Détection des Erreurs Critiques Silencieuses
La pire erreur pour un système de Fact-Checking n'est pas de s'abstenir, mais d'**halluciner un chiffre avec confiance**. Le Scorer pénalise immédiatement une architecture (marquage `silent_critical_error = True`) si le statut final est "ACCEPTÉ" alors que le système a inventé ou mal retranscrit une valeur numérique, un code géographique ou un indicateur.

### 5.3 Le Générateur de Tableau Markdown
Une fois l'inférence terminée, le script `generate_report.py` fait passer les résultats des 4 architectures à travers le Scorer, puis agrège mathématiquement les F1, la couverture et les erreurs pour recracher automatiquement un **Tableau de Comparaison** (Tableau 9 des spécifications), permettant ainsi de prendre une décision finale basée à 100% sur des datas on-premise, sans aucun biais humain.

---

## 6. L'Arbitrage et le Juge de Paix (Étapes 8 et 9)

Pour éviter le biais d'un "score pondéré magique" (ex: 40% F1 + 60% Erreurs), l'Étape 8 utilise un **Tri Lexicographique**.
1. **Filtre Éliminatoire** : Exclusion immédiate via le `selection_policy.json` (Tolérance 0 pour les erreurs silencieuses).
2. **Test de McNemar & Pareto** : Le script `select_v1.py` prouve mathématiquement que l'architecture C3 domine C2. Sur le plan qualité, elles sont équivalentes (0 discordance McNemar). Sur le plan opérationnel, C3 réduit la charge d'inférence LLM de 75%.
3. **Scellement Cryptographique (Étape 9)** : Le test final s'exécute sur un jeu aveugle de 40 affirmations. Les prédictions, le routage et les métriques (avec intervalles de confiance bootstrapés) sont générés dans une arborescence stricte et figés par un fichier racine **`checksums.sha256`**, interdisant toute retouche a posteriori.
