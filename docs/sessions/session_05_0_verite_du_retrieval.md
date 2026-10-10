# Session 5.0 — Quelle est la vérité du retrieval ?

## En une phrase

Avant de brancher le Micro-Gold, on a ouvert le moteur de recherche existant pour savoir ce qui est vraiment là, ce qui est démo, et ce qui ne démarre pas faute d’environnement.

## Contexte

La Session 4.1 a fini l’oracle de séries. La tentation suivante aurait été d’écrire tout de suite un `RetrievalService`. On a refusé : les vieux scripts Lot 7 pouvaient être un vrai moteur… ou seulement des prototypes.

## Ce qu’on a trouvé

- **Il n’y a pas de service retrieval dans `src/`.** Tout le pipeline est dans `scripts/etape_4` à `etape_7`.
- **Les briques utiles existent :** fusion RRF, reranker déterministe, SQL FTS français, recherche pgvector, script d’ingestion avec embeddings MiniLM, et un fichier catalogue de **222** datasets INSEE (dont le chômage BIT).
- **Les tests unitaires des algos passent** (8/8). Ce n’est pas une preuve que la recherche marche en base.
- **PostgreSQL n’a pas pu démarrer ici** : Docker est installé, mais le moteur Docker Desktop est arrêté → connexion refusée. On classe ça **ENVIRONMENT_BLOCKED**, pas « retrieval cassé ».
- **Deux mondes catalogue** : tables ORM d’ingestion d’un côté, table `search_documents` de l’autre. Ils ne sont pas branchés.
- **Contradiction de modèle d’embedding** : le schéma parle de vecteurs 1024 (BGE), le chemin réel d’ingest utilise MiniLM en 384.

## Verdict

```text
C — réutiliser les algorithmes cœur, reconstruire la couche d’intégration
```

Autrement dit : on ne jette pas RRF ni le reranker ; on ne prétend pas non plus avoir déjà un composant propre prêt à encapsuler tel quel.

## Expérience smoke

La requête prévue (« taux de chômage au sens du BIT ») **n’a pas pu être exécutée en base**. Prochaine expérience unique : allumer Docker, initialiser le schéma, ingérer le JSON catalogue, relancer cette seule requête.

## Pour la suite

On s’arrête ici.  
La prochaine session dépendra du résultat du smoke réel — pas d’un plan théorique.

## Trace technique

[`docs/audit/session_05_0_retrieval_executable_truth.md`](../audit/session_05_0_retrieval_executable_truth.md)
