# Session 4 — Fabriquer une petite vérité terrain

## En une phrase

Avant de mesurer le moteur, on a commencé à construire un **oracle** : douze affirmations réelles pour lesquelles on documente à la main ce que serait une bonne chaîne de preuve.

## Contexte

Jusqu’ici, on a surtout rendu StatCheck plus propre *en interne* : contrat unique, fusion plus honnête, routeur mieux compris.  
Mais un système propre peut encore échouer au grounding : mauvaise série INSEE, mauvais territoire, confusion chômage BIT / catégorie A, points vs pourcentages, stock vs flux.

Pour tester ça sérieusement, il ne suffit pas d’un gros corpus flou ou d’anciens “gold” historiques. Il faut un petit ensemble **auditable** où un humain peut dire :

> Voici le claim.  
> Voici s’il est answerable.  
> Voici le dataset.  
> Voici la série.  
> Voici les observations.  
> Voici le calcul.  
> Voici le verdict attendu.  
> Voici ce qui reste ambigu.

La Session 4 construit exactement ça : le Micro-Gold V0.

## Ce qu’on a fait

1. **Audité les anciens gold** sans les recopier comme vérité. On a notamment rappelé le piège historique : confondre demandeurs d’emploi catégorie A et chômage BIT.
2. **Défini un schéma** clair pour chaque cas (claim, answerability, spécification attendue, grounding, dimensions, observations, calcul, verdict, ambiguïtés, provenance, revue).
3. **Annoté 12 claims figés** (MG001 à MG012), choisis pour enseigner des erreurs critiques :
   - chômage simple et variations (points vs %) ;
   - ambiguïté “jeunes” ;
   - mélange BIT / catégorie A ;
   - inflation annuelle vs mensuelle ;
   - valeur fausse sur bonne série ;
   - population stock ;
   - naissances ;
   - naissances présentées comme hausse de population ;
   - créations d’entreprises.
4. **Vérifié** les chiffres principaux sur des publications INSEE (informations rapides / focus / première).
5. **Ajouté des tests structurels** (unicité, règles FOUND/AMBIGUOUS, cohérence de calcul, jamais marqué VALIDATED automatiquement).
6. **Documenté** ce qui est solide et ce qui reste à pinner (surtout certains identifiants de séries BDM).

Important : chaque cas reste `CANDIDATE`. On n’a pas déclaré “VALIDATED” juste parce que le fichier existe.

## Résultats

Répartition utile (pas “statistiquement représentative”, mais structurellement riche) :

- plusieurs cas **FOUND / SUPPORTED** (happy paths et variations) ;
- deux cas **FOUND / REFUTED** (bonne piste, mauvaise affirmation) ;
- un cas **AMBIGUOUS** (“chômage des jeunes”) ;
- un cas **INSUFFICIENT** (BIT mélangé à catégorie A).

On a aussi documenté un point scientifique très intéressant sur le chômage : la valeur d’une **publication** peut différer d’une **série révisée plus tard**. Ce n’est pas un bug du Gold : c’est une leçon de provenance.

Les tests structurels du Micro-Gold passent.  
Le système StatCheck **n’est pas encore** évalué contre cet oracle : ce n’était pas le but.

## Pourquoi maintenant

Parce que sans oracle, Session 5 (retrieval / SDMX) risquerait de “réussir” en collant à d’anciens labels douteux, ou en se félicitant de trouver *une* série plausible.  
Avec un oracle humble mais sérieux, on pourra enfin demander : “as-tu trouvé *la* bonne chaîne ?”

## Analyse et interprétation

Trois apprentissages majeurs apparaissent déjà :

1. **Le ClaimSpecification tient à peu près**, mais le vrai saut de difficulté commence au grounding (dataset + série + dimensions).
2. **Answerability n’est pas un détail** : certains claims compréhensibles ne doivent pas être tranchés (MG004, MG005).
3. **Un chiffre vrai peut soutenir une fausse affirmation** (MG011 : vraies naissances, fausse hausse de population). C’est exactement le genre d’erreur dangereuse pour un fact-checker.

La Session 4 n’améliore pas encore le score du modèle. Elle améliore notre **capacité à juger** le modèle et le retrieval plus tard.

## Ce qui reste fragile

- Certains idbanks BDM ne sont pas encore épinglés (IPC, population, naissances, créations) : les valeurs de publication sont vérifiées, l’identifiant machine exact demande encore une revue humaine.
- Le Gold est candidat, pas une vérité figée à jamais.
- On n’a pas encore branché le runtime dessus.

Donc : Session 4 est **réussie comme construction d’oracle candidat**, et **partielle** si on exige déjà un Gold “VALIDATED” à 100 %.

## Pour la suite

La suite naturelle n’est pas de retuner la fusion. C’est :

1. pinner les identifiants de séries encore manquants ;
2. seulement ensuite attaquer `ClaimSpecification → recherche dataset/série → plan SDMX` **contre** ce Micro-Gold ;
3. juger retrieval et résolution avec abstention honnête quand le cas est ambigu.

## Leçons tirées

- Douze bons cas valent mieux que cent labels douteux.
- Ne jamais laisser le retriever ou le LLM écrire le Gold.
- Séparer “publication à une date” et “série révisée” est indispensable pour la confiance.
- Un oracle sert d’abord à discipliner l’équipe et le système, pas à produire un beau pourcentage.

## Où lire la version technique

[`docs/audit/session_04_micro_gold.md`](../audit/session_04_micro_gold.md) · [`docs/contracts/micro_gold_v0.md`](../contracts/micro_gold_v0.md) · [`data/gold/micro_gold_v0/micro_gold_v0.yaml`](../../data/gold/micro_gold_v0/micro_gold_v0.yaml)
