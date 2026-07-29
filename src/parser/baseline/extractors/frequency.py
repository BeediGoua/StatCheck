from typing import List, Dict, Any

def extract_frequencies(normalized_info: Dict[str, str], doc) -> List[Dict[str, Any]]:
    candidates = []
    text = normalized_info["matching_normalized_text"]
    
    if "mensuel" in text:
        candidates.append({"type": "MONTHLY"})
    elif "trimestriel" in text:
        candidates.append({"type": "QUARTERLY"})
    elif "annuel" in text or "en moyenne annuelle" in text:
        candidates.append({"type": "ANNUAL"})
    elif "en glissement annuel" in text:
        candidates.append({"type": "YEAR_OVER_YEAR"})
        
    return candidates
