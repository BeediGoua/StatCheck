from typing import Dict, Any
import logging

from src.parser.baseline.validators.contradiction import validate_contradictions
from src.parser.baseline.validators.numeric import validate_numeric_consistency

logger = logging.getLogger(__name__)

def validate_coherence(parsed_dict: Dict[str, Any]) -> None:
    """
    Niveaux 5 & 6 : Applique les validateurs de contradiction de la Baseline.
    On doit adapter le format du dict Pydantic vers le format attendu par la Baseline.
    """
    
    # La baseline attend :
    # result["measures"] = [{"role": "START_VALUE", "value": 10}, ...]
    # result["operation"] = {"direction": "INCREASE"}
    
    llm_measures = parsed_dict.get("measures", [])
    llm_operation = parsed_dict.get("operation")
    
    if not llm_operation or not llm_measures:
        return
        
    baseline_format = {
        "operation": {
            "direction": llm_operation.get("direction", "UNKNOWN")
        },
        "measures": []
    }
    
    for m in llm_measures:
        baseline_format["measures"].append({
            "role": m.get("role"),
            "value": m.get("numeric_value")
        })
        
    try:
        validate_contradictions(baseline_format)
    except ValueError as e:
        logger.error(f"Niveau 5 (Contradiction) échoué: {e}")
        parsed_dict["parse_status"] = "UNSUPPORTED"
        
    try:
        validate_numeric_consistency(baseline_format)
    except ValueError as e:
        logger.error(f"Niveau 6 (Incohérence Numérique) échoué: {e}")
        parsed_dict["parse_status"] = "UNSUPPORTED"
