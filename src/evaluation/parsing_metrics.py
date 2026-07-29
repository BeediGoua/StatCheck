def calculate_exact_match(prediction_json: dict, gold_json: dict) -> bool:
    """
    Vérifie si la prédiction JSON est strictement identique au JSON Gold.
    """
    return prediction_json == gold_json

def calculate_field_f1(prediction_json: dict, gold_json: dict) -> dict:
    """
    Calcule un pseudo F1-score au niveau des champs.
    Retourne un dictionnaire avec { "precision": p, "recall": r, "f1": f1 }
    """
    def flatten_dict(d, parent_key='', sep='.'):
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    flat_pred = flatten_dict(prediction_json)
    flat_gold = flatten_dict(gold_json)
    
    tp = 0
    fp = 0
    fn = 0
    
    for k, v in flat_pred.items():
        if k in flat_gold and flat_gold[k] == v:
            tp += 1
        else:
            fp += 1
            
    for k, v in flat_gold.items():
        if k not in flat_pred or flat_pred[k] != v:
            fn += 1
            
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0.0
    
    return {
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "tp": tp,
        "fp": fp,
        "fn": fn
    }
