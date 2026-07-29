from typing import Dict, Any

def validate_contradictions(parsed_data: Dict[str, Any]) -> None:
    """
    Lève une ValueError si une contradiction flagrante est détectée.
    """
    direction = parsed_data["operation"]["direction"]
    measures = parsed_data.get("measures", [])
    
    for m in measures:
        measure_val = m["value"]
        if measure_val is not None:
            if direction == "DECREASE" and measure_val < 0:
                raise ValueError(f"Contradiction: Baisse avec valeur négative ({measure_val})")
            if direction == "INCREASE" and measure_val < 0:
                raise ValueError(f"Contradiction: Hausse avec valeur négative ({measure_val})")
