# Session 2 — Un seul langage pour décrire une affirmation

## En une phrase

On a décidé qu’une affirmation statistique devait être représentée **partout de la même façon**, avec un contrat unique : le ClaimSpecification.

## Contexte

Avant cette session, plusieurs parties du système parlaient de “claims” avec des formats différents. Le parseur déterministe produisait un style de structure. Le parseur LLM en produisait un autre. La fusion, le routeur et le scoreur s’attendaient parfois encore à d’anciennes formes.

Résultat typique d’un tel décalage : les tests n’arrivent plus à s’importer, les pièces ne se branchent plus, et on passe du temps à “réparer des symptoms” au lieu de travailler sur le vrai problème.

La Session 2 répond à une question simple :

> Quelle est **la** représentation d’un claim après parsing, avant retrieval ?

## Ce qu’on a fait

On a introduit et documenté un contrat unique pour le claim, puis on a branché les adaptateurs :

- d’un côté, le format interne du parseur baseline ;
- de l’autre, le format interne du parseur LLM ;
- au milieu, une forme commune consommée par le routeur, la fusion et le scoreur.

On a aussi clarifié une idée essentielle pour StatCheck :

> La quantité “affirmée” par le claim n’est **pas** une observation officielle.  
> C’est ce que quelqu’un *prétend*. La preuve officielle vient plus tard.

## Résultats

- Un contrat documenté et un modèle commun existent.
- Les consommateurs principaux ne dépendent plus d’un vieux format “mentions” incompatible.
- Les erreurs de collection liées à ce décalage de contrat sont en grande partie résolues au niveau import.
- Ce n’est **pas** encore une validation E2E claim → INSEE → verdict. C’est une fondation.

## Pourquoi c’était le bon moment

Sans format commun, toute amélioration de fusion, de retrieval ou de benchmark reste fragile : on compare des pommes et des oranges.  
Avec un format commun, on peut enfin poser des questions scientifiques du type : “est-ce que deux analyses du même claim parlent de la même quantité ?”

## Analyse et interprétation

Cette session change la nature du projet. On passe d’un assemblage de prototypes à un système qui commence à avoir une **grammaire**.

Mais une grammaire stricte trop tôt peut aussi casser. C’est pourquoi la Session 2.1 existe juste après : durcir sans tout casser, enrichir ce qui manquait (bornes, approximations, etc.).

## Pour la suite

Une fois le contrat en place, deux urgences apparaissent :

1. fusionner proprement Baseline et LLM (Session 3) ;
2. annoter de vrais claims pour savoir si ce contrat suffit vraiment (Session 4).

## Leçons tirées

- Unifier le langage interne est plus important qu’ajouter une feature visible.
- Adapter deux mondes vers un centre est plus sain que de forcer un parseur à imiter l’autre.
- “Contrat unique” ne veut pas dire “tout est validé” : ça veut dire “on peut enfin discuter avec les mêmes mots”.

## Où lire la version technique

[`docs/contracts/claim_specification_v1.md`](../contracts/claim_specification_v1.md) · notes Session 2 dans [`PROJECT_STATUS.md`](../../PROJECT_STATUS.md)
