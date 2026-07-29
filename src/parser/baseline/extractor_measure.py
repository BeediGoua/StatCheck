import re
from typing import Dict, Any

def extract_measure(normalized_text: str, doc) -> Dict[str, Any]:
    """
    Extrait la valeur numérique et l'unité d'une phrase normalisée.
    Utilise doc (spaCy) pour enrichir si besoin.
    """
    result = {
        "value": None,
        "unit": "UNKNOWN",
        "is_approximate": False
    }
    
    # Mots clés d'approximation
    approx_words = ["environ", "pres de", "plus de", "autour de", "semblerait", "estimee a"]
    for w in approx_words:
        if w in normalized_text:
            result["is_approximate"] = True
            break

    # Recherche de motifs : nombre suivi d'une unité
    # 1. Pourcentages (ex: 5%, 5 %)
    pct_match = re.search(r'(\d+(?:\.\d+)?)\s*%', normalized_text)
    if pct_match:
        result["value"] = float(pct_match.group(1))
        result["unit"] = "PERCENTAGE"
        return result
        
    # 2. Points de pourcentages (ex: 2 points, 2.5 points)
    pt_match = re.search(r'(\d+(?:\.\d+)?)\s*points?', normalized_text)
    if pt_match:
        result["value"] = float(pt_match.group(1))
        result["unit"] = "PERCENTAGE_POINT"
        return result
        
    # 3. Mots "millions", "milliards" (ex: 6 millions)
    mil_match = re.search(r'(\d+(?:\.\d+)?)\s*(million|milliard)s?', normalized_text)
    if mil_match:
        val = float(mil_match.group(1))
        mult = 1_000_000 if "million" in mil_match.group(2) else 1_000_000_000
        result["value"] = val * mult
        result["unit"] = "ABSOLUTE"
        return result
        
    # 4. Nombre brut (ex: 723000 ou 723 000 qui est devenu 723000 après normalisation sans espaces insécables)
    # Attention aux dates (ex: en 2022). On évite les nombres entiers entre 1900 et 2100 s'ils sont précédés de "en"
    raw_matches = re.finditer(r'(?<!en )(\d+(?:\.\d+)?)', normalized_text)
    for match in raw_matches:
        val_str = match.group(1)
        val = float(val_str)
        # Ignorer les années si c'est un entier
        if val.is_integer() and 1900 <= val <= 2100:
            continue
        # Ignorer si suivi du mot "ans"
        after_match = normalized_text[match.end():]
        if after_match.strip().startswith("an"):
            continue
            
        result["value"] = val
        result["unit"] = "ABSOLUTE"
        return result
        
    return result
