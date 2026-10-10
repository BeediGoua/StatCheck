from typing import Any, Dict

from src.parser.claim_specification import ClaimSpecification, ParseStatus, PresenceStatus


class C3Router:
    """
    Deterministic cascade router for architecture C3 (Baseline-First).

    C3 decides **CALL_LLM vs BASELINE_ONLY** — not final answerability.
    When CALL_LLM is chosen, Fusion + post-validators produce the result,
    which may remain AMBIGUOUS / CONTRADICTION / PARTIAL.
    """

    @staticmethod
    def should_call_llm(baseline_result: ClaimSpecification, text: str) -> Dict[str, Any]:
        """
        Returns {"trigger": bool, "reason": str, "route": "CALL_LLM"|"BASELINE_ONLY"}.

        Numeric thresholds (confidence 0.9, control sample 0.05) are frozen —
        Session 3 does not retune them.
        """
        status = baseline_result.parse_status
        if status in {
            ParseStatus.AMBIGUOUS,
            ParseStatus.PARTIAL,
            ParseStatus.MISSING_CONTEXT,
            ParseStatus.REJECTED,
        }:
            return {
                "trigger": True,
                "reason": f"BASELINE_STATUS_{status.value}",
                "route": "CALL_LLM",
            }

        indicator = baseline_result.indicator
        if indicator is None:
            return {
                "trigger": True,
                "reason": "NO_INDICATOR_FOUND",
                "route": "CALL_LLM",
            }
        label = indicator.canonical_value or indicator.original_label
        if not label or label == "UNKNOWN":
            return {
                "trigger": True,
                "reason": "INDICATOR_UNRESOLVED",
                "route": "CALL_LLM",
            }
        if indicator.confidence < 0.9:
            return {
                "trigger": True,
                "reason": "LOW_CONFIDENCE_INDICATOR",
                "route": "CALL_LLM",
            }

        if not baseline_result.territories:
            return {
                "trigger": True,
                "reason": "NO_TERRITORY_FOUND",
                "route": "CALL_LLM",
            }
        for t in baseline_result.territories:
            if t.presence in (PresenceStatus.MISSING, PresenceStatus.IMPLICIT) and t.confidence < 0.9:
                return {
                    "trigger": True,
                    "reason": "AMBIGUOUS_TERRITORY",
                    "route": "CALL_LLM",
                }

        if baseline_result.claimed_quantity is None:
            return {
                "trigger": True,
                "reason": "NO_MEASURE_FOUND",
                "route": "CALL_LLM",
            }

        if baseline_result.statistical_operation is None:
            return {
                "trigger": True,
                "reason": "UNKNOWN_OPERATION",
                "route": "CALL_LLM",
            }

        te = baseline_result.time_period
        if te is not None and te.is_relative and (not te.start_date or not te.end_date):
            return {
                "trigger": True,
                "reason": "UNRESOLVED_RELATIVE_PERIOD",
                "route": "CALL_LLM",
            }

        text_lower = text.lower()
        if "point" in text_lower and "%" in text_lower:
            return {
                "trigger": True,
                "reason": "POTENTIAL_PERCENT_VS_PP_CONFUSION",
                "route": "CALL_LLM",
            }

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
                return {
                    "trigger": True,
                    "reason": "LINGUISTIC_COMPLEXITY_TRIGGER",
                    "route": "CALL_LLM",
                }

        return {
            "trigger": False,
            "reason": "BASELINE_SUFFICIENT",
            "route": "BASELINE_ONLY",
        }

    @staticmethod
    def should_trigger_control_sample(
        is_baseline_sufficient: bool, random_val: float, threshold: float = 0.05
    ) -> bool:
        if is_baseline_sufficient and random_val < threshold:
            return True
        return not is_baseline_sufficient
