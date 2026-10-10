from typing import Any, Dict

from src.parser.claim_specification import ClaimSpecification, PresenceStatus


class C3Router:
    """Routeur déterministe pour l'architecture en cascade C3 (Baseline-First)."""

    @staticmethod
    def should_call_llm(baseline_result: ClaimSpecification, text: str) -> Dict[str, Any]:
        """
        Détermine de façon déterministe s'il faut faire appel au LLM.
        Le LLM est appelé lorsque la baseline est incomplète, ambiguë, incohérente ou insuffisamment fiable.
        """
        if baseline_result.parse_status in [
            "AMBIGUOUS",
            "PARTIAL",
            "MISSING_CONTEXT",
            "REJECTED",
        ]:
            return {
                "trigger": True,
                "reason": f"BASELINE_STATUS_{baseline_result.parse_status}",
            }

        indicator = baseline_result.indicator
        if indicator is None:
            return {"trigger": True, "reason": "NO_INDICATOR_FOUND"}
        label = indicator.canonical_value or indicator.original_label
        if not label or label == "UNKNOWN":
            return {"trigger": True, "reason": "INDICATOR_UNRESOLVED"}
        if indicator.confidence < 0.9:
            return {"trigger": True, "reason": "LOW_CONFIDENCE_INDICATOR"}

        if not baseline_result.territories:
            return {"trigger": True, "reason": "NO_TERRITORY_FOUND"}
        for t in baseline_result.territories:
            if t.presence in (PresenceStatus.MISSING, PresenceStatus.IMPLICIT) and t.confidence < 0.9:
                return {"trigger": True, "reason": "AMBIGUOUS_TERRITORY"}

        if baseline_result.claimed_quantity is None:
            return {"trigger": True, "reason": "NO_MEASURE_FOUND"}

        if baseline_result.statistical_operation is None:
            return {"trigger": True, "reason": "UNKNOWN_OPERATION"}

        te = baseline_result.time_period
        if te is not None and te.is_relative and (not te.start_date or not te.end_date):
            return {"trigger": True, "reason": "UNRESOLVED_RELATIVE_PERIOD"}

        text_lower = text.lower()
        if "point" in text_lower and "%" in text_lower:
            return {"trigger": True, "reason": "POTENTIAL_PERCENT_VS_PP_CONFUSION"}

        complex_triggers = [
            "deux fois plus",
            "plus bas historique",
            "n'a pas diminué",
            "moins élevé que",
            "depuis que",
            "par rapport à",
            "chez les jeunes",
            "entre",
            "à partir de",
        ]
        for trigger in complex_triggers:
            if trigger in text_lower:
                return {"trigger": True, "reason": "LINGUISTIC_COMPLEXITY_TRIGGER"}

        return {"trigger": False, "reason": "BASELINE_SUFFICIENT"}

    @staticmethod
    def should_trigger_control_sample(
        is_baseline_sufficient: bool, random_val: float, threshold: float = 0.05
    ) -> bool:
        """
        Échantillon de contrôle : Force l'appel au LLM sur un petit pourcentage (ex: 5%)
        des cas jugés 'faciles' par la baseline pour auditer ses erreurs silencieuses.
        `random_val` doit être déterministe (généré avec un seed lié à l'ID de l'affirmation).
        """
        if is_baseline_sufficient and random_val < threshold:
            return True
        return not is_baseline_sufficient
