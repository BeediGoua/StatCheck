import os
import json

def get_rrf_score(rank, k=60, weight=1.0):
    if rank is None:
        return 0.0
    return weight * (1.0 / (k + rank))

def perform_rrf(lexical_results, vector_results, k=60, lexical_weight=1.0, vector_weight=1.0, consensus_bonus=0.0):
    """
    Combine les résultats lexicaux et vectoriels via l'algorithme Reciprocal Rank Fusion (RRF).
    lexical_results, vector_results: listes de dataset_ids ordonnées (Top 50 attendu).
    Retourne le Top 20 combiné.
    """
    scores = {}
    
    # Process Lexical Results
    for rank_idx, dataset_id in enumerate(lexical_results):
        rank = rank_idx + 1 # 1-indexed rank
        if dataset_id not in scores:
            scores[dataset_id] = {'lexical_rank': rank, 'vector_rank': None}
        else:
            scores[dataset_id]['lexical_rank'] = rank
            
    # Process Vectorial Results
    for rank_idx, dataset_id in enumerate(vector_results):
        rank = rank_idx + 1 # 1-indexed rank
        if dataset_id not in scores:
            scores[dataset_id] = {'lexical_rank': None, 'vector_rank': rank}
        else:
            scores[dataset_id]['vector_rank'] = rank

    # Compute Final RRF Score
    final_results = []
    for dataset_id, ranks in scores.items():
        lex_rank = ranks['lexical_rank']
        vec_rank = ranks['vector_rank']
        
        lex_score = get_rrf_score(lex_rank, k, lexical_weight)
        vec_score = get_rrf_score(vec_rank, k, vector_weight)
        
        rrf_score = lex_score + vec_score
        
        # Bonus de consensus : si présent dans les deux listes
        if lex_rank is not None and vec_rank is not None:
            rrf_score += consensus_bonus
            
        final_results.append({
            'dataset_id': dataset_id,
            'rrf_score': rrf_score,
            'lexical_rank': lex_rank,
            'vector_rank': vec_rank
        })
        
    # Sort by RRF score descending
    final_results.sort(key=lambda x: x['rrf_score'], reverse=True)
    
    # Return Top 20
    return final_results[:20]


def optimize_rrf_parameters():
    print("Début de l'optimisation RRF sur le set de Validation...")
    
    # Paramètres à tester
    k_values = [30, 60, 100]
    weights = [
        (1.0, 1.0),   # Egal
        (1.25, 1.0),  # Lexical favorisé
        (1.0, 1.25)   # Vectoriel favorisé
    ]
    
    # On simule ici les résultats des requêtes SQL pour 1 affirmation de validation
    # (Dans la vraie implémentation, on itère sur data/corpus/validation.jsonl 
    # et on fait les requêtes DB pour de vrai)
    
    mock_lexical = [f"DATASET_{i}" for i in range(1, 51)]
    mock_vector = [f"DATASET_{i*2}" for i in range(1, 26)] + [f"VEC_ONLY_{i}" for i in range(25)]
    
    best_config = None
    best_score_metric = -1.0
    
    for k in k_values:
        for lw, vw in weights:
            # print(f"Test config -> k={k}, Lexical_Weight={lw}, Vector_Weight={vw}")
            
            top_20 = perform_rrf(
                lexical_results=mock_lexical, 
                vector_results=mock_vector, 
                k=k, 
                lexical_weight=lw, 
                vector_weight=vw
            )
            
            # Simulation d'une métrique d'évaluation (Ex: Recall@20)
            # Normalement, on vérifierait si la vérité terrain est dans le top 20
            mock_recall = sum(item['rrf_score'] for item in top_20) # Dummy score for illustration
            
            if mock_recall > best_score_metric:
                best_score_metric = mock_recall
                best_config = (k, lw, vw)

    print(f"\n[OPTIMISATION TERMINÉE]")
    print(f"Meilleurs paramètres trouvés : k={best_config[0]}, Poids Lexical={best_config[1]}, Poids Vectoriel={best_config[2]}")
    print("Le Top 20 est maintenant conservé pour passer au Reranker (Étape 6).")

if __name__ == "__main__":
    optimize_rrf_parameters()
