from typing import Dict, Any

def validate_temporal_consistency(parsed_data: Dict[str, Any]) -> None:
    """
    Vérifie la cohérence temporelle.
    Par exemple, s'il y a un intervalle de date, le début doit être avant la fin.
    """
    time_info = parsed_data.get("time", {})
    if not time_info:
        return
        
    start_date = time_info.get("start_date")
    end_date = time_info.get("end_date")
    
    if start_date and end_date:
        if start_date > end_date:
            raise ValueError(f"Incohérence temporelle: la date de début ({start_date}) est postérieure à la date de fin ({end_date}).")
