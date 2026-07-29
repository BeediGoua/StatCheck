import math
from typing import List

def calculate_recall_at_k(predicted_ids: List[str], gold_ids: List[str], k: int) -> float:
    """
    Calcule le Recall@K.
    Retourne 1.0 si au moins un des documents gold est dans les K premiers de la prédiction, sinon 0.0.
    """
    if not gold_ids:
        return 0.0
    
    top_k_preds = predicted_ids[:k]
    for gid in gold_ids:
        if gid in top_k_preds:
            return 1.0
    return 0.0

def calculate_mrr(predicted_ids: List[str], gold_ids: List[str]) -> float:
    """
    Mean Reciprocal Rank (MRR)
    """
    if not gold_ids or not predicted_ids:
        return 0.0
        
    for rank, pid in enumerate(predicted_ids, start=1):
        if pid in gold_ids:
            return 1.0 / rank
    return 0.0

def calculate_ndcg(predicted_ids: List[str], gold_relevance: dict, k: int) -> float:
    """
    Normalized Discounted Cumulative Gain (nDCG@K).
    gold_relevance: dict { "dataset_id": relevance_score (0 à 3) }
    """
    if not gold_relevance:
        return 0.0
        
    def dcg(p_ids, rels, limit):
        score = 0.0
        for i, pid in enumerate(p_ids[:limit], start=1):
            rel = rels.get(pid, 0)
            score += (2**rel - 1) / math.log2(i + 1)
        return score
        
    # Calcul de l'IDCG (Idéal)
    ideal_preds = sorted(gold_relevance.keys(), key=lambda x: gold_relevance[x], reverse=True)
    idcg = dcg(ideal_preds, gold_relevance, k)
    
    if idcg == 0.0:
        return 0.0
        
    actual_dcg = dcg(predicted_ids, gold_relevance, k)
    return actual_dcg / idcg
