import re
from typing import List, Dict, Any

def extract_measures(normalized_info: Dict[str, str], doc) -> List[Dict[str, Any]]:
    """
    Extrait tous les candidats de mesure.
    Retourne une liste de mesures potentielles.
    """
    candidates = []
    text = normalized_info["matching_normalized_text"]
    
    # Matches basiques pour nombres
    # (?<!en ) évite de prendre les années basiques comme "en 2022" mais c'est l'extracteur temporel qui gérera ça mieux.
    # Pour l'instant on extrait tout nombre qui semble être une mesure.
    raw_matches = re.finditer(r'(-?\d+(?:\.\d+)?)', text)
    
    for match in raw_matches:
        val_str = match.group(1)
        val = float(val_str)
        span = match.span()
        
        # Ignorer les années si c'est un entier isolé (simplification)
        if val.is_integer() and 1900 <= val <= 2100:
            # On vérifie le contexte
            before = text[max(0, span[0]-5):span[0]]
            if "en " in before or "annee" in before or "année" in before:
                continue
                
        # Détermination de l'unité
        after_match = text[span[1]:span[1]+15].strip()
        unit = "ABSOLUTE"
        if after_match.startswith("%") or after_match.startswith("pour cent"):
            unit = "PERCENTAGE"
        elif after_match.startswith("point"):
            unit = "PERCENTAGE_POINT"
        elif after_match.startswith("million"):
            unit = "MILLIONS"
        elif after_match.startswith("milliard"):
            unit = "BILLIONS"
            
        candidates.append({
            "value": val,
            "unit": unit,
            "span_text": val_str,
            "start": span[0],
            "end": span[1]
        })
        
    return candidates
