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

## Résultats (vue simple)

- **Chômage (MG001–MG003)** : série `001688527` confirmée (BIT, ensemble, France hors Mayotte, CVS). On garde le snapshot de publication à 7,5 %, et on documente l’histoire des révisions sans l’écraser.
- **Jeunes / BIT×catégorie A (MG004–MG005)** : l’abstention reste la bonne réponse. Une série « moins de 25 ans » existe et donne 19 %, mais le claim dit seulement « jeunes » → ambigu. BIT ≠ catégorie A → insuffisant.
- **IPC (MG006–MG008)** : idbanks trouvés et branchés (`011814632` annuel, `011814631` mensuel). Les valeurs 1,2 % et −1,0 % sont confirmées. MG008 reste juste : bonne série, mauvaise valeur affirmée.
- **Population (MG009, MG011)** : série `001760077` confirmée ; les effectifs BDM actuels diffèrent un peu de la table « portrait social » initiale → correction, mais « environ 68,6 millions » reste soutenu. La hausse de population n’égale toujours pas les naissances.
- **Naissances (MG010)** : série mensuelle France `001641601` ; la somme 2025 fait exactement 643 905.
- **Créations d’entreprises (MG012)** : le chiffre annuel SIDE (1 165 800) est confirmé en publication, mais **aucune série BDM nationale « Ensemble – France » active** n’a été trouvée (les anciennes sont arrêtées) → cas **non résolu** pour l’idbank.

## Verdict

```text
PARTIAL — il reste 1 cas non résolu (MG012)
FIX NEEDED — on a dû corriger plusieurs annotations (surtout IPC / pop / naissances)
```

Autrement dit : le Micro-Gold est **beaucoup plus fiable** qu’en fin de Session 4 pour servir d’oracle de grounding sur chômage, prix, population et naissances. Il n’est **pas encore DONE** tant que MG012 n’a pas d’identifiant de série machine, ou qu’on n’accepte pas explicitement un oracle « publication seule » pour ce cas.

## Pourquoi c’était important

Sans cette session, on aurait testé le retrieval sur des poignées fictives (`IPC_YOY_ENSEMBLE_FR`, idbanks vides). On aurait pu « réussir » en trouvant n’importe quelle série au bon chiffre. Maintenant, pour 11 claims sur 12, on sait ce qu’on cherche vraiment.

## Leçons tirées

- Une publication et une série BDM peuvent diverger après révision : il faut stocker les deux histoires.
- « Moins de 25 ans » n’est pas une licence pour résoudre « jeunes ».
- Certaines statistiques annuelles (créations) peuvent être solides en publication et absentes comme série BDM active.
- Corriger un Gold n’est pas un échec : c’est exactement le travail de Session 4.1.

## Pour la suite

On s’arrête ici jusqu’à lecture du verdict.  
Ensuite seulement : décider du sort de MG012, puis éventuellement brancher le retrieval contre cet oracle.

## Trace technique

[`docs/audit/session_04_1_micro_gold_series.md`](../audit/session_04_1_micro_gold_series.md)
