from typing import Dict, Any

def compute_confidence(parsed_data: Dict[str, Any]) -> None:
    """
    Calcule les scores de confiance par composant.
    """
    # 1. Territoire
    terr = parsed_data["subject"]
    terr_method = terr.get("territory_method")
    if terr_method == "COG_MATCH":
        terr["confidence"] = "HIGH"
    elif terr_method == "NER_ONLY":
        terr["confidence"] = "MEDIUM"
    else:
        terr["confidence"] = "HIGH" # pour MISSING par exemple
        
    # 2. Mesure
    measures = parsed_data.get("measures", [])
    for m in measures:
        m["confidence"] = "HIGH" # Les RegEx numériques sont très fiables
        
    # 3. Temps
    time = parsed_data["time"]
    if time.get("period_explicit") != "UNKNOWN":
        time["confidence"] = "HIGH"
    elif time.get("period_relative"):
        time["confidence"] = "MEDIUM"
    else:
        time["confidence"] = "LOW"
        
    # 4. Global
    parsed_data["overall_confidence"] = "MEDIUM" # Simplification
