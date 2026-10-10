# Session 2.1 — Rendre le contrat plus strict (et plus honnête)

## En une phrase

Après avoir créé le format unique du claim, on l’a **durci** : plus strict sur les champs, plus riche sur les quantités, plus cohérent sur la provenance.

## Contexte

Un premier contrat est souvent un peu trop tolérant : il accepte des champs inattendus, laisse des statuts flous, ou simplifie trop une quantité (“8 %” sans dire si c’est exact, approximatif, entre deux bornes, en milliers, etc.).

Or StatCheck a besoin de nuances. “Environ 68,6 millions” n’est pas la même chose que “exactement 68 605 600”. “+0,2 point” n’est pas “+2,7 %”. Si le contrat oublie ces nuances, la fusion et le verdict futurs mentiront sans le vouloir.

## Ce qu’on a fait

On a renforcé le contrat sans changer encore la logique métier de fusion :

- interdiction des champs inconnus (plus de “sac fourre-tout” silencieux) ;
- statut de parsing typé et clair ;
- quantités plus riches (bornes, échelle, approximation, signe) ;
- meilleure lecture de la provenance (ce qui est explicite dans le texte vs ce qui est déduit).

Des tests ont été ajoutés pour vérifier que le contrat rejette bien ce qu’il doit rejeter, et accepte ce qu’il doit accepter.

## Résultats

- Le contrat est plus robuste comme interface interne.
- Les adapters baseline/LLM respectent mieux les nuances de présence et de provenance.
- On n’a **pas** encore “réparé la sémantique de fusion” : c’était volontairement hors scope.

## Pourquoi ce durcissement

Parce que plus tard, quand on fusionne deux analyses ou qu’on annote un Micro-Gold, on a besoin que le format porte assez d’information. Sinon on découvre trop tard qu’il manquait un champ critique.

## Analyse

Session 2 = “un seul langage”.  
Session 2.1 = “ce langage dit assez de choses, et refuse de faire semblant”.

C’est une session de maturité. Peu spectaculaire. Très utile.

## Pour la suite

Le terrain était prêt pour Session 3 : fusionner sans inventer une troisième vérité, et refuser d’afficher “complet” quand le cas est ambigu ou contradictoire.

## Leçons tirées

- Tolérer n’importe quel champ “pour aller plus vite” crée de la dette sémantique.
- Les quantités statistiques ont besoin de richesse (échelle, approximation, bornes), pas seulement d’un nombre.
- Durcir un contrat tôt coûte moins cher que de le changer après un benchmark.

## Où lire la version technique

[`docs/audit/session_02_1_contract_hardening.md`](../audit/session_02_1_contract_hardening.md)
