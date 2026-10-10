# Session 3 — Fusionner sans mentir

## En une phrase

On a appris à combiner l’analyse déterministe (Baseline) et l’analyse LLM **sans inventer un accord fictif**, et sans déclarer un claim “complet” juste parce qu’un LLM a été appelé.

## Contexte

StatCheck a deux regards sur un même texte :

- un parseur déterministe, stable, parfois limité ;
- un parseur LLM, plus souple, parfois inventif.

La tentation est grande de “prendre le meilleur des deux” en silence. C’est dangereux. Si l’un dit “France” et l’autre “Île-de-France”, ou si l’un parle en points et l’autre en pourcentage, on ne doit pas fabriquer une troisième réponse confortable.

La Session 3 pose donc une discipline :

> Aligner ≠ être d’accord.  
> Autorité ≠ “prendre le LLM parce qu’il a l’air intelligent”.  
> Appeler le LLM ≠ avoir une réponse complète.

## Ce qu’on a fait

On a formalisé une politique de fusion écrite, puis on l’a implémentée en trois couches mentales :

1. **Alignement** — est-ce que les deux analyses parlent du même morceau du claim ? (même mention, même sens, désaccord, ou sans rapport)
2. **Autorité** — qui gagne, qui reste en alternative, où est le conflit non résolu (quantité riche, territoire, population, temps, opération, etc.)
3. **Post-validation** — vérifications de cohérence au niveau du claim (ex. variation relative avec des points de pourcentage, période relative sans dates, indicateur manquant)

On a aussi clarifié le rôle de C3 : ce n’est pas “le juge final”. C’est un aiguillage :

- soit la baseline suffit ;
- soit on appelle le LLM puis on fusionne.

Et après fusion, le résultat peut rester ambigu, contradictoire ou partiel. C’est une feature, pas un échec.

Enfin, on a écrit des tests adversariaux (cas pièges) pour figer ces comportements.

## Résultats

- La fusion n’est plus un “baseline ou LLM” silencieux sur tous les champs.
- Un conflit de codes géographiques sur la même surface textuelle ne se résout plus par “la baseline gagne parce qu’elle est explicite”.
- Les quantités ne sont “d’accord” que si toute la sémantique riche concorde (valeur, unité, échelle, rôle, approximation, bornes…).
- Les tests de non-régression des sessions précédentes restent verts, avec les nouveaux cas de conflit.

## Pourquoi c’était central

Parce que sans fusion honnête, tout le reste devient du théâtre.  
Un retrieval parfait derrière une fusion menteuse produira de belles preuves… pour la mauvaise lecture du claim.

## Analyse et interprétation

Session 3 change l’éthique du système :

- l’ambiguïté devient visible ;
- la contradiction devient visible ;
- le “complet” devient un statut **gagné**, pas un badge de passage LLM.

On a aussi volontairement **refusé** de retoucher les seuils numériques (alignement, confiance). Pourquoi ? Parce que retuner des seuils avant d’avoir une vérité terrain, c’est de l’optimisation dans le brouillard.

## Pour la suite

Une fois la sémantique plus propre, la question suivante n’est plus “comment fusionner mieux”, c’est :

> Sur de vrais claims, savons-nous même ce qu’est la bonne réponse INSEE ?

C’est exactement la Session 4 (Micro-Gold).

## Leçons tirées

- Même offsets ≠ même signification métier.
- Expliquer une décision de fusion (qui a gagné, pourquoi) est aussi important que le résultat.
- S’abstenir ou marquer ambigu est parfois plus scientifique que de trancher.
- Ne pas retuner les seuils trop tôt protège contre l’illusion de progrès.

## Où lire la version technique

[`docs/audit/session_03_fusion_c3.md`](../audit/session_03_fusion_c3.md) · [`docs/contracts/fusion_policy_v1.md`](../contracts/fusion_policy_v1.md)
