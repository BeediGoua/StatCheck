from typing import Dict, Any, List

def validate_numeric_consistency(parsed_data: Dict[str, Any]) -> None:
    """
    Vérifie la cohérence mathématique des mesures.
    Ex: 8% (START) - 6% (END) = 2 points (CHANGE) DECREASE
    Lève une exception si incohérent.
    """
    measures = parsed_data.get("measures", [])
    operation = parsed_data.get("operation", {})
    
    start_val = None
    end_val = None
    change_val = None
    
    for m in measures:
        role = m.get("role")
        val = m.get("value")
        if val is None:
            continue
        if role == "START_VALUE":
            start_val = val
        elif role == "END_VALUE":
            end_val = val
        elif role in ["ABSOLUTE_CHANGE", "CLAIMED_CHANGE"]:
            change_val = val

    # Si on a les 3, on peut vérifier mathématiquement
    if start_val is not None and end_val is not None and change_val is not None:
        calc_diff = round(abs(start_val - end_val), 4)
        claim_diff = round(abs(change_val), 4)
        if calc_diff != claim_diff:
            raise ValueError(f"Incohérence mathématique: {start_val} - {end_val} != {change_val}")

    # Si on a START et END, on vérifie que la direction correspond
    if start_val is not None and end_val is not None:
        direction = operation.get("direction")
        if direction == "DECREASE" and end_val > start_val:
            raise ValueError(f"Incohérence: DECREASE déclaré mais {end_val} > {start_val}")
        if direction == "INCREASE" and end_val < start_val:
            raise ValueError(f"Incohérence: INCREASE déclaré mais {end_val} < {start_val}")
