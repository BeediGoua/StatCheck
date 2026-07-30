# Documentation et Analyse Détaillée : Lot 6 (Parsing des Affirmations)

Le Lot 6 de la Phase 3 est consacré au Parsing, c'est-à-dire l'extraction d'entités structurées depuis une affirmation formulée en langage naturel. Le but est de remplir fidèlement le schéma JSON (défini au Lot 4) pour nourrir le moteur de recherche (Lot 7).

Afin d'adopter une démarche scientifique, nous avons implémenté et comparé deux approches radicalement différentes : la **Baseline Déterministe (6A)** et le **LLM Contraint (6B)**, avant de procéder à la **Fusion (6C)**.

---

## 1. Sous-Lot 6A : Baseline Hybride Classique

La Baseline classique est une approche déterministe. Elle ne "devine" rien : elle extrait en utilisant la syntaxe, les mathématiques et des règles rigides.

### 1.1 Architecture en Pipeline Unidirectionnel
Le pipeline `src/parser/baseline/` est conçu de manière modulaire :
1. **Normalisation non-destructive :** Génère 3 versions du texte (Brut, Affichage, Matching regex avec accents conservés).
2. **Analyse Linguistique (spaCy) :** Le modèle `fr_core_news_md` est appelé *une seule fois*. Il génère un arbre syntaxique utilisé par les extracteurs en aval.
3. **Extraction spécialisée :** Des modules isolés (`measure.py`, `time.py`, `territory.py`) cherchent des candidats.
4. **Résolution (Désambiguïsation) :** Croisement des données (ex: associer "Vienne" à son code COG exact).
5. **Validation (Anti-Contradiction) :** Bloque les absurdités mathématiques (ex: Début - Fin ≠ Changement).

### 1.2 Implémentations Marquantes
- **Le Territoire (Adieu au "France par défaut") :** Le système intègre le vrai Code Officiel Géographique (COG). S'il ne trouve pas de territoire explicite, il renvoie `MISSING`. Il ne suppose plus que l'on parle de la France.
- **Rôles des Nombres :** Les expressions régulières regardent le contexte immédiat pour différencier `START_VALUE` ("de 5%"), `END_VALUE` ("à 7%"), ou `CLAIMED_CHANGE` ("soit +2 points").
- **Encadrement du Temps :** La librairie `dateparser` est strictement ancrée à la `reference_date` (Date de l'article). "Le mois dernier" est donc évalué par rapport au jour de la publication, pas au jour de l'exécution du code.
- **Négation et Lemmatisation :** L'extracteur vérifie la négation ("ne ... pas"). Ainsi, le verbe "baisser" génère `DECREASE`, mais "ne baisse pas" devient `NOT_DECREASE`.

**Bilan 6A :** Sur un corpus pilote piégé (`pilote_6A_V.json`), la Baseline a atteint un Exact Match de **100%** grâce à l'application scrupuleuse des validateurs. Elle constitue la fondation de confiance du projet.

---

## 2. Sous-Lot 6B : Parseur LLM Contraint

Contrairement à la Baseline qui souffre d'un faible Rappel sur des phrases complexes ou du vocabulaire inédit, le LLM (Large Language Model) excelle dans la compréhension sémantique. L'enjeu du 6B était de dompter cette IA.

### 2.1 Le Structured Output (JSON Schema)
Pour empêcher le LLM d'halluciner ou de modifier la structure, nous avons utilisé l'approche "Structured Output" (ex: via l'API OpenAI `response_format`).
- L'IA est contrainte de répondre en respectant *strictement* le `schema_annotation.json` du Lot 4.
- Le prompt système inclut le "Guide d'Annotation" en contexte.

### 2.2 Post-Validation Déterministe
Même sous contrainte, un LLM peut commettre des erreurs (ex: arrondir "3.54" à "3.5", ce qui fausse la donnée).
Nous avons implémenté un post-validateur :
- Il vérifie que chaque `span_text` renvoyé par le LLM existe bel et bien *verbatim* dans la phrase d'origine.
- Si le LLM invente une valeur, la propriété est rejetée et classée `CONTRADICTION`.

---

## 3. Sous-Lot 6C : Évaluation et Fusion

Le Lot 6 s'achève par l'évaluation des deux moteurs via l'infrastructure du Lot 5.

### 3.1 Forces et Faiblesses
- **Baseline (6A) :** Précision parfaite sur les chiffres et dates simples. Faible Rappel (incapable d'extraire le concept métier exact si la phrase est tordue).
- **LLM (6B) :** Excellent Rappel pour extraire les entités et concepts ("indicateur", "population"). Cependant, a tendance à lisser ou dénaturer parfois les relations mathématiques complexes.

### 3.2 L'Approche V1 (Hybridation)
L'expérimentation a mené à figer une architecture de fusion :
1. **La Baseline** est le maître absolu des chiffres (`measures`), du temps absolu (`time`), et de la localisation COG (`territory`). Ses extractions écrasent celles de l'IA.
2. **Le LLM** prend le relais pour l'extraction sémantique métier : quel est l'indicateur principal ? Quelle est la population visée ? Quelles sont les dimensions transversales ?

## Conclusion du Lot 6
Le pipeline de Parsing est désormais robuste. En combinant la rigueur déterministe de la Baseline 6A pour les données mathématiques et l'intelligence sémantique du LLM 6B pour le sens global, le système génère un objet JSON riche, validé et prêt à attaquer le moteur de recherche hybride du Lot 7.
