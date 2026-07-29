import csv
import os
import unicodedata
from typing import Dict, Any, List

# Chargement du COG au démarrage
COG_PATH = os.path.join(os.path.dirname(__file__), "..", "resources", "cog_2024.csv")

def load_cog() -> List[Dict[str, str]]:
    cog = []
    if os.path.exists(COG_PATH):
        with open(COG_PATH, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cog.append(row)
    return cog

COG_DATA = load_cog()

def normalize_for_match(text: str) -> str:
    """Retire les accents et met en minuscules pour faciliter le matching COG"""
    text = unicodedata.normalize('NFD', text).encode('ascii', 'ignore').decode("utf-8")
    return text.lower().strip()

def resolve_territory(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Croise les candidats avec le vrai COG et gère l'ambiguïté (ex: Vienne).
    """
    if not candidates:
        return {"status": "MISSING", "value": None}
        
    resolved_options = []
    seen_keys = set()
    
    for cand in candidates:
        span_clean = normalize_for_match(cand["span_text"])
        
        # Recherche dans le COG
        for entry in COG_DATA:
            if normalize_for_match(entry["label"]) == span_clean:
                unique_key = f"{entry['code_system']}_{entry['code']}"
                if unique_key not in seen_keys:
                    resolved_options.append({
                        "value": entry["label"],
                        "code": entry["code"],
                        "code_system": entry["code_system"],
                        "territory_type": entry["territory_type"],
                        "cog_vintage": entry["vintage"],
                        "method": "COG_EXACT_LABEL",
                        "confidence": "HIGH",
                        "span_text": cand["span_text"]
                    })
                    seen_keys.add(unique_key)
                
    if len(resolved_options) == 1:
        return {"status": "SUCCESS", "value": resolved_options[0]}
        
    elif len(resolved_options) > 1:
        # Homonymie détectée (ex: Vienne = 86 (DEPARTEMENT) ou 38544 (COMMUNE))
        return {
            "status": "AMBIGUOUS",
            "value": None,
            "alternatives": resolved_options
        }
        
    else:
        # Aucun match dans le COG, on fait confiance au NER (dégradé)
        return {
            "status": "PARTIAL",
            "value": candidates[0]["span_text"],
            "method": "NER_ONLY",
            "confidence": "LOW",
            "span_text": candidates[0]["span_text"]
        }
