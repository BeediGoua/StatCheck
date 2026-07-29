from typing import List, Dict, Any

def extract_adjustments(normalized_info: Dict[str, str], doc) -> List[Dict[str, Any]]:
    candidates = []
    text = normalized_info["matching_normalized_text"]
    
    if "cvs" in text or "variations saisonnières" in text:
        candidates.append({"type": "SA"}) # Seasonally Adjusted
    if "brutes" in text:
        candidates.append({"type": "NSA"}) # Not Seasonally Adjusted
    if "prix constants" in text or "euros constants" in text:
        candidates.append({"type": "REAL"}) # Real prices
    if "prix courants" in text or "euros courants" in text:
        candidates.append({"type": "NOMINAL"}) # Nominal prices
        
    return candidates
