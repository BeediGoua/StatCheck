# Session 1 — L’audit de vérité

## En une phrase

Avant d’améliorer StatCheck, on a voulu savoir **ce qui est réellement vrai dans le dépôt** — et non ce que les documents promettent.

## Contexte

StatCheck vise quelque chose d’ambitieux : prendre une affirmation statistique (par exemple sur le chômage ou l’inflation), la comprendre, trouver la bonne donnée officielle à l’INSEE, recalculer, puis dire si l’affirmation est soutenue, contredite, ou si on doit s’abstenir.

Le problème au départ, c’est qu’un projet comme celui-ci accumule vite :

- des documents d’architecture qui décrivent le futur idéal ;
- des scripts de démo ;
- des résultats d’évaluation qui ont l’air scientifiques ;
- du code partiellement branché.

Si on mélange tout ça, on finit par croire qu’on a déjà un pipeline fiable alors qu’on a surtout une collection de briques. La Session 1 a donc été volontairement **humble** : regarder, tester ce qu’on peut, classer, sans “réparer le monde” d’un coup.

## Ce qu’on a fait

On a passé le dépôt en revue avec une règle simple :

> Documentation ≠ vérité.  
> Ce qui compte, c’est ce que le code et les tests prouvent réellement.

Concrètement, on a :

- regardé l’état Git et le commit de référence ;
- essayé de collecter et lancer les tests pour voir ce qui casse vraiment ;
- parcouru les grandes zones (parsing, fusion, évaluation, données INSEE, scripts) ;
- écrit un tableau de statut honnête (`PROJECT_STATUS.md`) ;
- rédigé un audit technique détaillé pour garder la preuve de ce constat.

On n’a pas cherché à “faire joli”. On a cherché à **ne plus se mentir**.

## Résultats importants

Plusieurs choses sont devenues claires :

1. **Beaucoup de pièces existent**, mais elles ne forment pas encore un parcours complet claim → preuve → verdict.
2. Certaines évaluations “finales” étaient en réalité des **simulations** (résultats forcés, or non scientifique). Les garder sans les marquer comme telles aurait empoisonné toute la suite.
3. Il y avait un **décalage de contrat** : différentes parties du code n’attendaient pas le même format d’affirmation. Résultat : des tests qui n’arrivent même pas à démarrer proprement.
4. Le cœur “retrieval / résolution / observations INSEE / verdict” était encore partiel, non branché, ou dépendant d’environnements (base, clés) non garantis.

Autrement dit : le projet n’était pas “vide”. Il était **fragmenté**, et certaines “victoires” documentées n’étaient pas des victoires scientifiques.

## Pourquoi c’était nécessaire

Sans cette session, on aurait facilement :

- optimisé des paramètres sur des mocks ;
- “amélioré” un modèle alors que le vrai problème était un contrat cassé ;
- annoncé des progrès E2E alors qu’on n’avait pas d’oracle fiable.

L’audit de vérité sert de **rampe de sécurité mentale**. Il fixe le vocabulaire : TARGET, IMPLEMENTED, TESTED, VALIDATED, MOCK, BROKEN. Ce vocabulaire empêche de confondre “le code existe” avec “ça marche sur de vraies données”.

## Analyse et interprétation

Le message de fond n’est pas “tout est mauvais”. C’est plutôt :

> StatCheck a de bonnes intentions et des briques utiles,  
> mais la chaîne de preuve n’est pas encore fermée.

La bonne stratégie n’est donc pas de tout reconstruire. C’est de **fermer les trous dans le bon ordre** :

1. d’abord un langage commun pour décrire une affirmation ;
2. ensuite une fusion honnête quand plusieurs analyses existent ;
3. ensuite une vérité terrain (oracle) sur quelques claims réels ;
4. seulement ensuite le grounding INSEE / retrieval / verdict.

## Pour la suite

La Session 1 a ouvert la voie à une hygiène rapide (Session 1.5), puis à la reconstruction du contrat claim (Session 2).  
Elle reste la référence quand on hésite : *“est-ce qu’on affirme quelque chose de VALIDATED, ou seulement d’IMPLEMENTED ?”*

## Leçons tirées

- Un beau document d’architecture n’est pas une preuve.
- Un script qui “passe” peut être un mock.
- Classer honnêtement l’état du système accélère plus que de coder dans le flou.
- Il vaut mieux un petit statut vrai qu’un grand statut confortable.

## Où lire la version technique

[`docs/audit/session_01_executable_truth.md`](../audit/session_01_executable_truth.md) · [`PROJECT_STATUS.md`](../../PROJECT_STATUS.md)
