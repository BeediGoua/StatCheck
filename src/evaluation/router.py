from typing import Dict, Any
from src.parser.canonical import CanonicalParseResult

class C3Router:
    """Routeur déterministe pour l'architecture en cascade C3 (Baseline-First)."""
    
    @staticmethod
    def should_call_llm(baseline_result: CanonicalParseResult, text: str) -> Dict[str, Any]:
        """
        Détermine de façon déterministe s'il faut faire appel au LLM 
        ou si la baseline suffit pour traiter l'affirmation.
        """
        # 1. Vérification des statuts d'incertitude
        if baseline_result.parse_status in ["AMBIGUOUS", "PARTIAL"]:
            return {"trigger": True, "reason": "BASELINE_STATUS_INCOMPLETE"}
            
        # 2. Vérification structurelle : manque d'éléments essentiels
        if not baseline_result.indicators:
            return {"trigger": True, "reason": "NO_INDICATOR_FOUND"}
            
        if not baseline_result.operation:
            # Même une phrase simple devrait avoir une opération de type "SIMPLE_VALUE"
            return {"trigger": True, "reason": "UNKNOWN_OPERATION"}
            
        # Mesures sans rôle explicite (risque de confusion sémantique)
        measures_without_roles = sum(1 for m in baseline_result.measures if m.role is None)
        if measures_without_roles > 0:
            return {"trigger": True, "reason": "MISSING_MEASURE_ROLES"}
            
        # 3. Vérification de la complexité linguistique (Superlatifs, comparaisons complexes, négations)
        text_lower = text.lower()
        complex_triggers = [
            "deux fois plus", "plus bas historique", "n'a pas diminué",
            "moins élevé que", "depuis que", "par rapport à", "chez les jeunes"
        ]
        
        for trigger in complex_triggers:
            if trigger in text_lower:
                return {"trigger": True, "reason": f"LINGUISTIC_COMPLEXITY_TRIGGER"}
                
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
