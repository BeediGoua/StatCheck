from typing import Dict, Any
import logging

from src.parser.baseline.extractors.time import extract_times

logger = logging.getLogger(__name__)

def validate_temporal_values(parsed_dict: Dict[str, Any], reference_date: str = None) -> None:
    """
    Niveau 3 : Vérifie que le LLM n'a pas inventé de dates non justifiées par le texte.
    Repasse le source_text dans l'extracteur temporel de la baseline.
    """
    time_expressions = parsed_dict.get("time_expressions", [])
    
    for time_expr in time_expressions:
        source_text = time_expr.get("source_text", "")
        if not source_text:
            continue
            
        norm_text = source_text.lower()
        baseline_candidates = extract_times({"matching_normalized_text": norm_text}, None, reference_date)
        
        if not baseline_candidates:
            # L'extracteur temporel ne trouve rien, on ajoute un flag
            time_expr["validation_warning"] = "BASELINE_NO_MATCH"
            continue
            
        # On pourrait être très strict et forcer l'écrasement de normalized_start par 
        # la valeur calculée par la baseline, notamment si is_relative est vrai.
        # Pour le MVP de la validation : si le LLM a normalisé alors que la baseline trouve autre chose.
        b_cand = baseline_candidates[0]
        
        # Si c'est une date relative, la baseline a la référence.
        if b_cand["type"] == "RELATIVE_DATE" and "parsed_date" in b_cand:
            baseline_date = b_cand["parsed_date"]
            llm_start = time_expr.get("normalized_start")
            
            # Si le LLM a donné une date différente (ou s'est trompé dans le calcul mental)
            # (Note: Le LLM donne des ISO 8601 YYYY-MM-DD)
            if llm_start and llm_start != baseline_date:
                logger.warning(f"Correction temporelle: {llm_start} corrigé en {baseline_date} via '{source_text}'")
                time_expr["normalized_start"] = baseline_date
                time_expr["normalized_end"] = baseline_date # Par simplification
