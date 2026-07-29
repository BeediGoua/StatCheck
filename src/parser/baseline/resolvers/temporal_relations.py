from typing import List, Dict, Any

def resolve_time(candidates: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Choisit le meilleur candidat temporel.
    """
    if not candidates:
        return {
            "period_explicit": "UNKNOWN",
            "period_relative": None,
            "granularity": "UNKNOWN"
        }
        
    # Priorité : EXPLICIT_QUARTER > EXPLICIT_YEAR > RELATIVE_DATE
    best = None
    for cand_type in ["EXPLICIT_QUARTER", "EXPLICIT_YEAR", "RELATIVE_DATE"]:
        best = next((c for c in candidates if c["type"] == cand_type), None)
        if best:
            break
            
    if not best:
        best = candidates[0]
        
    res = {
        "period_explicit": "UNKNOWN",
        "period_relative": None,
        "granularity": best["granularity"]
    }
    
    if best["type"] == "EXPLICIT_QUARTER":
        res["period_explicit"] = f"Q{best['quarter']} {best['start_year']}"
    elif best["type"] == "EXPLICIT_YEAR":
        res["period_explicit"] = str(best['start_year'])
    elif best["type"] == "RELATIVE_DATE":
        res["period_relative"] = best["span_text"]
        
    return res
