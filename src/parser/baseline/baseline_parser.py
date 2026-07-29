from typing import Dict, Any

from src.parser.baseline.normalizer import normalize_text
from src.parser.baseline.document_analyzer import analyze_document

from src.parser.baseline.extractors.measure import extract_measures
from src.parser.baseline.extractors.time import extract_times
from src.parser.baseline.extractors.territory import extract_territory_candidates
from src.parser.baseline.extractors.indicator import extract_indicators
from src.parser.baseline.extractors.population import extract_populations
from src.parser.baseline.extractors.negation import extract_negations
from src.parser.baseline.extractors.comparison import extract_comparisons
from src.parser.baseline.extractors.frequency import extract_frequencies
from src.parser.baseline.extractors.adjustment import extract_adjustments

from src.parser.baseline.resolvers.geographic_candidates import resolve_territory
from src.parser.baseline.resolvers.operation_direction import resolve_operation_direction
from src.parser.baseline.resolvers.temporal_relations import resolve_time
from src.parser.baseline.resolvers.measure_roles import resolve_measure

from src.parser.baseline.validators.contradiction import validate_contradictions
from src.parser.baseline.validators.numeric import validate_numeric_consistency
from src.parser.baseline.validators.temporal import validate_temporal_consistency
from src.parser.baseline.confidence import compute_confidence

def parse_claim_baseline(text: str, reference_date: str = None) -> Dict[str, Any]:
    """
    Orchestrateur Exhaustif de la Baseline Hybride (Version 6A-V).
    """
    norm_info = normalize_text(text)
    doc = analyze_document(norm_info["raw_text"])
    
    # 1. Extraction des candidats
    meas_cands = extract_measures(norm_info, doc)
    time_cands = extract_times(norm_info, doc, reference_date)
    terr_cands = extract_territory_candidates(norm_info, doc)
    ind_cands = extract_indicators(norm_info, doc)
    pop_cands = extract_populations(norm_info, doc)
    comp_cands = extract_comparisons(norm_info, doc)
    freq_cands = extract_frequencies(norm_info, doc)
    adj_cands = extract_adjustments(norm_info, doc)
    
    # 2. Résolution des rôles et entités
    final_territory = resolve_territory(terr_cands)
    final_operation = resolve_operation_direction(doc)
    final_time = resolve_time(time_cands)
    resolved_measures = resolve_measure(meas_cands, norm_info, doc)
    
    indicator = ind_cands[0]["span_text"] if ind_cands else "UNKNOWN"
    population = pop_cands[0]["span_text"] if pop_cands else "UNKNOWN"
    
    # Gestion du statut global d'ambiguïté
    global_status = "VERIFIABLE"
    if indicator == "UNKNOWN":
        global_status = "MISSING_CONTEXT"
    if final_territory.get("status") == "AMBIGUOUS":
        global_status = "AMBIGUOUS"
        
    # 3. Assemblage final
    result = {
        "identity": {
            "text": norm_info["raw_text"],
            "language": "fr",
            "reference_date": reference_date
        },
        "subject": {
            "indicator": indicator,
            "territory_main": final_territory.get("value") if final_territory.get("status") in ["SUCCESS", "FOUND", "PARTIAL"] else None,
            "territory_status": final_territory.get("status"),
            "territory_method": final_territory.get("method"),
            "territory_alternatives": final_territory.get("alternatives", []),
            "population": population
        },
        "time": {
            "period_explicit": final_time["period_explicit"],
            "period_relative": final_time["period_relative"],
            "granularity": final_time["granularity"],
            "frequency": freq_cands[0]["type"] if freq_cands else "UNKNOWN"
        },
        "measures": resolved_measures, # Liste avec rôles
        "operation": {
            "type": final_operation["type"],
            "direction": final_operation["direction"],
            "polarity": final_operation["polarity"]
        },
        "modifiers": {
            "comparisons": comp_cands,
            "adjustments": adj_cands
        },
        "status": {
            "answerability": global_status
        }
    }
    
    # Validation
    if global_status not in ["MISSING_CONTEXT", "AMBIGUOUS"]:
        try:
            validate_contradictions(result)
            validate_numeric_consistency(result)
            validate_temporal_consistency(result)
        except ValueError as e:
            result["status"]["answerability"] = "CONTRADICTION"
            result["status"]["error"] = str(e)
        
    compute_confidence(result)
    
    return result
