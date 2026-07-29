from typing import List, Dict, Any

def extract_comparisons(normalized_info: Dict[str, str], doc) -> List[Dict[str, Any]]:
    """
    Extrait les comparaisons. (Ex: "deux fois plus", "plus élevé que")
    """
    candidates = []
    text = normalized_info["matching_normalized_text"]
    
    if "deux fois plus" in text:
        candidates.append({"type": "RATIO", "value": 2})
    elif "moitie moins" in text or "moitié moins" in text:
        candidates.append({"type": "RATIO", "value": 0.5})
    
    return candidates
