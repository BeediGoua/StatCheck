from typing import List, Dict, Any

def extract_negations(normalized_info: Dict[str, str], doc) -> bool:
    """
    Détecte la présence de négations ("ne ... pas").
    """
    text = normalized_info["matching_normalized_text"]
    if " ne " in text and " pas " in text:
        return True
    if text.startswith("ne ") and " pas " in text:
        return True
    if " n'" in text and " pas " in text:
        return True
    if text.startswith("n'") and " pas " in text:
        return True
        
    return False
