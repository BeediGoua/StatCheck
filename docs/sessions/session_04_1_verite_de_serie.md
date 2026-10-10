# Session 4.1 — Vérifier la vraie série derrière le Gold

## En une phrase

On a repris les douze claims du Micro-Gold pour vérifier, case par case, si le dataset INSEE, la série (idbank), les dimensions et les observations étaient vraiment les bons — sans développer de nouvelle feature.

## Contexte

La Session 4 avait produit un oracle **candidat** : beaucoup de chiffres venaient de publications officielles, mais plusieurs idbanks manquaient (IPC, population, naissances, créations). Or un oracle de grounding ne peut pas se contenter d’un chiffre plausible : il faut la **bonne série**, avec les **bonnes métadonnées**.

La règle qu’on s’est imposée :

> On ne choisit jamais une série parce que le chiffre colle.

## Ce qu’on a fait

Pour chaque claim, on a :

1. relu l’annotation actuelle ;
2. ouvert la publication INSEE et/ou l’API BDM ;
3. inspecté le libellé et les dimensions de la série ;
4. comparé aux observations du Gold ;
5. classé : CONFIRMED / CORRECTED / NEEDS_HUMAN_REVIEW / UNRESOLVED ;
6. corrigé le YAML quand c’était nécessaire ;
7. documenté publication vs révision pour le chômage.

**Addendum 4.1bis :** on a rouvert MG012 après découverte de la série active `010755537` (successeur de `001564301` arrêtée).

## Résultats (vue simple)

- **Chômage (MG001–MG003)** : série `001688527` confirmée (BIT, ensemble, France hors Mayotte, CVS). On garde le snapshot de publication à 7,5 %, et on documente l’histoire des révisions sans l’écraser.
- **Jeunes / BIT×catégorie A (MG004–MG005)** : l’abstention reste la bonne réponse. Une série « moins de 25 ans » existe et donne 19 %, mais le claim dit seulement « jeunes » → ambigu. BIT ≠ catégorie A → insuffisant.
- **IPC (MG006–MG008)** : idbanks trouvés et branchés (`011814632` annuel, `011814631` mensuel). Les valeurs 1,2 % et −1,0 % sont confirmées. MG008 reste juste : bonne série, mauvaise valeur affirmée.
- **Population (MG009, MG011)** : série `001760077` confirmée ; les effectifs BDM actuels diffèrent un peu de la table « portrait social » initiale → correction, mais « environ 68,6 millions » reste soutenu. La hausse de population n’égale toujours pas les naissances.
- **Naissances (MG010)** : série mensuelle France `001641601` ; la somme 2025 fait exactement 643 905.
- **Créations d’entreprises (MG012)** : série BDM active `010755537` (Ensemble – France – mensuel brut), successeur de `001564301`. Snapshot publication : claim arrondi **1 165 800** / SIDE exact **1 165 795**. Somme live des 12 mois 2025 = **1 165 795** (égale au SIDE exact). Dual vintage conservé ; statut **CORRECTED**.

## Verdict

```text
DONE — tous les FOUND ont série+dims+obs CONFIRMED/CORRECTED
FIX NEEDED — corrections matérielles (dont MG012 idbank + dual vintage)
```

Autrement dit : le Micro-Gold est maintenant un oracle de grounding **série-pinné** pour les cas FOUND. Il reste **CANDIDATE** (pas VALIDATED) : on n’a toujours pas branché le retrieval dessus.

## Pourquoi c’était important

Sans cette session, on aurait testé le retrieval sur des poignées fictives (`IPC_YOY_ENSEMBLE_FR`, idbanks vides). On aurait pu « réussir » en trouvant n’importe quelle série au bon chiffre. Maintenant, pour les 12 claims, on sait ce qu’on cherche vraiment — y compris le successeur national des créations d’entreprises.

## Leçons tirées

- Une publication et une série BDM peuvent diverger après révision : il faut stocker les deux histoires.
- « Moins de 25 ans » n’est pas une licence pour résoudre « jeunes ».
- Une série « arrêtée » peut avoir un successeur actif au titre équivalent : il faut le chercher avant de conclure UNRESOLVED.
- Corriger un Gold n’est pas un échec : c’est exactement le travail de Session 4.1.

## Pour la suite

On s’arrête ici jusqu’à lecture du verdict.  
Ensuite seulement : éventuellement brancher le retrieval contre cet oracle (Session 5) — **pas avant acceptation**.

## Trace technique

[`docs/audit/session_04_1_micro_gold_series.md`](../audit/session_04_1_micro_gold_series.md)
