"""Claim-level post-validators for fused ClaimSpecification (Session 3)."""

from typing import List, Optional, Tuple

from src.fusion.authority import DecisionType
from src.parser.claim_specification import (
    Ambiguity,
    ClaimSpecification,
    ParseStatus,
    QuantityApproximation,
    QuantityRole,
)


_PERCENT_UNITS = {"PERCENT", "PERCENTAGE", "%"}
_PP_UNITS = {"PERCENTAGE_POINT", "PP", "POINT", "POINTS"}


def _unit_upper(unit: Optional[str]) -> str:
    return (unit or "").strip().upper()


def _op_upper(spec: ClaimSpecification) -> str:
    op = spec.statistical_operation
    if op is None:
        return ""
    return (op.canonical_value or op.original_label or "").strip().upper()


def apply_post_validators(
    result: ClaimSpecification,
    decisions_log: List[dict],
) -> Tuple[ClaimSpecification, List[str]]:
    """
    Enforce claim-level invariants and finalize parse_status.

    Never forces COMPLETE merely because an LLM was called.
    Returns (mutated result, list of validator reason codes applied).
    """
    reasons: List[str] = []
    qty = result.claimed_quantity
    op = _op_upper(result)

    # RELATIVE_CHANGE ↔ % (not percentage points)
    if op in {"RELATIVE_CHANGE", "RELATIVE"} or (
        qty is not None and qty.role == QuantityRole.RELATIVE_CHANGE
    ):
        unit = _unit_upper(qty.unit if qty else None)
        if unit in _PP_UNITS:
            reasons.append("RELATIVE_CHANGE_WITH_PERCENTAGE_POINTS")
            result.warnings.append(
                "RELATIVE_CHANGE incompatible with percentage-point unit"
            )
            result.ambiguities.append(
                Ambiguity(
                    field="claimed_quantity.unit",
                    reason="RELATIVE_CHANGE_WITH_PERCENTAGE_POINTS",
                    alternatives=[unit],
                )
            )

    # POINT_CHANGE / absolute change in points ↔ PERCENTAGE_POINT
    if op in {
        "POINT_CHANGE",
        "PERCENTAGE_POINT_CHANGE",
        "ABSOLUTE_CHANGE",
    } or (qty is not None and qty.role == QuantityRole.ABSOLUTE_CHANGE):
        unit = _unit_upper(qty.unit if qty else None)
        if unit in _PERCENT_UNITS and "POINT" in (result.original_text or "").upper():
            reasons.append("POINT_CHANGE_WITH_PLAIN_PERCENT")
            result.warnings.append(
                "POINT_CHANGE / absolute change expected percentage points"
            )
            result.ambiguities.append(
                Ambiguity(
                    field="claimed_quantity.unit",
                    reason="POINT_CHANGE_WITH_PLAIN_PERCENT",
                    alternatives=[unit],
                )
            )

    # BETWEEN → both bounds
    if qty is not None and qty.approximation == QuantityApproximation.BETWEEN:
        if qty.lower_bound is None or qty.upper_bound is None:
            reasons.append("BETWEEN_MISSING_BOUNDS")
            result.warnings.append("BETWEEN approximation requires lower and upper bounds")

    # START_VALUE + END_VALUE roles distinct
    roles = [q.role for q in result.quantity_list()]
    if QuantityRole.START_VALUE in roles and QuantityRole.END_VALUE in roles:
        starts = [q for q in result.quantity_list() if q.role == QuantityRole.START_VALUE]
        ends = [q for q in result.quantity_list() if q.role == QuantityRole.END_VALUE]
        if starts and ends and starts[0].span_offsets == ends[0].span_offsets:
            reasons.append("START_END_ROLE_COLLISION")
            result.ambiguities.append(
                Ambiguity(
                    field="reference_quantities",
                    reason="START_END_ROLE_COLLISION",
                    alternatives=[],
                )
            )

    # Relative period without dates → PARTIAL
    te = result.time_period
    if te is not None and te.is_relative and (not te.start_date or not te.end_date):
        reasons.append("UNRESOLVED_RELATIVE_PERIOD")
        result.warnings.append("Relative time period without resolved dates")

    # Missing indicator → PARTIAL
    if result.indicator is None:
        reasons.append("MISSING_INDICATOR")

    # Decision-driven status (honest)
    has_rejected_override = any(
        d.get("decision_type") == DecisionType.REJECTED.value
        and d.get("field") == "claimed_quantity"
        for d in decisions_log
    )
    has_conflict = any(
        d.get("decision_type") == DecisionType.CONFLICT_UNRESOLVED.value
        for d in decisions_log
    )
    has_both = any(
        d.get("decision_type") == DecisionType.BOTH_RETAINED_AS_ALTERNATIVES.value
        for d in decisions_log
    )
    has_ambiguities = bool(result.ambiguities)

    if has_rejected_override and result.claimed_quantity is None and result.indicator is None:
        result.parse_status = ParseStatus.REJECTED
        reasons.append("STATUS_REJECTED")
        return result, reasons

    if has_conflict or "RELATIVE_CHANGE_WITH_PERCENTAGE_POINTS" in reasons:
        result.parse_status = ParseStatus.CONTRADICTION
        reasons.append("STATUS_CONTRADICTION")
        return result, reasons

    if has_both or has_ambiguities:
        result.parse_status = ParseStatus.AMBIGUOUS
        reasons.append("STATUS_AMBIGUOUS")
        return result, reasons

    if (
        "MISSING_INDICATOR" in reasons
        or "UNRESOLVED_RELATIVE_PERIOD" in reasons
        or "BETWEEN_MISSING_BOUNDS" in reasons
        or result.claimed_quantity is None
    ):
        result.parse_status = ParseStatus.PARTIAL
        reasons.append("STATUS_PARTIAL")
        return result, reasons

    result.parse_status = ParseStatus.COMPLETE
    reasons.append("STATUS_COMPLETE")
    return result, reasons
