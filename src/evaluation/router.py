from typing import Dict, Any
from src.parser.canonical import CanonicalParseResult

class C3Router:
    """Routeur déterministe pour l'architecture en cascade C3 (Baseline-First)."""
    
    @staticmethod
    def should_call_llm(baseline_result: CanonicalParseResult, text: str) -> Dict[str, Any]:
        """
        Détermine de façon déterministe s'il faut faire appel au LLM.
        Le LLM est appelé lorsque la baseline est incomplète, ambiguë, incohérente ou insuffisamment fiable.
        """
        # 1. Statut global de la baseline
        if baseline_result.parse_status in ["AMBIGUOUS", "PARTIAL", "MISSING_CONTEXT", "REJECTED"]:
            return {"trigger": True, "reason": f"BASELINE_STATUS_{baseline_result.parse_status}"}
            
        # 2. Vérification des champs obligatoires et de leur fiabilité
        if not baseline_result.indicators:
            return {"trigger": True, "reason": "NO_INDICATOR_FOUND"}
        for ind in baseline_result.indicators:
            if not ind.normalized_label or ind.normalized_label == "UNKNOWN":
                return {"trigger": True, "reason": "INDICATOR_UNRESOLVED"}
            if ind.confidence < 0.9:
                return {"trigger": True, "reason": "LOW_CONFIDENCE_INDICATOR"}
                
        if not baseline_result.territories:
            return {"trigger": True, "reason": "NO_TERRITORY_FOUND"}
        for t in baseline_result.territories:
            if t.status in ["MISSING", "INFERRED"] and t.confidence < 0.9:
                return {"trigger": True, "reason": "AMBIGUOUS_TERRITORY"}
                
        if not baseline_result.measures:
            return {"trigger": True, "reason": "NO_MEASURE_FOUND"}
            
        if not baseline_result.operation:
            return {"trigger": True, "reason": "UNKNOWN_OPERATION"}
            
        # 3. Périodes relatives non résolues
        for te in baseline_result.time_expressions:
            if te.is_relative and (not te.start_date or not te.end_date):
                return {"trigger": True, "reason": "UNRESOLVED_RELATIVE_PERIOD"}
                
        # 4. Ambiguïtés textuelles potentielles (ex: % vs pp)
        text_lower = text.lower()
        if "point" in text_lower and "%" in text_lower:
            return {"trigger": True, "reason": "POTENTIAL_PERCENT_VS_PP_CONFUSION"}
            
        complex_triggers = [
            "deux fois plus", "plus bas historique", "n'a pas diminué",
            "moins élevé que", "depuis que", "par rapport à", "chez les jeunes",
            "entre", "à partir de"
        ]
        for trigger in complex_triggers:
            if trigger in text_lower:
                return {"trigger": True, "reason": "LINGUISTIC_COMPLEXITY_TRIGGER"}
                
        # Si aucun déclencheur, la baseline est jugée suffisante
        return {"trigger": False, "reason": "BASELINE_SUFFICIENT"}
        
    @staticmethod
    def should_trigger_control_sample(is_baseline_sufficient: bool, random_val: float, threshold: float = 0.05) -> bool:
        """
        Échantillon de contrôle : Force l'appel au LLM sur un petit pourcentage (ex: 5%)
        des cas jugés 'faciles' par la baseline pour auditer ses erreurs silencieuses.
        `random_val` doit être déterministe (généré avec un seed lié à l'ID de l'affirmation).
        """
        if is_baseline_sufficient and random_val < threshold:
            return True
        return not is_baseline_sufficient
