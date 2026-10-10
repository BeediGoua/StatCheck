"""Adapt LLM ClaimParseResult (or dict) → ClaimSpecification V1."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple, Union

from src.parser.claim_specification import (
    Ambiguity,
    CLAIMED_QUANTITY_ROLES,
    ClaimSlot,
    ClaimSpecification,
    ClaimTime,
    ClaimedQuantity,
    ExtractionProvenance,
    PresenceStatus,
    QuantityRole,
    REFERENCE_QUANTITY_ROLES,
)

_LLM_STATUS = {
    "COMPLETE": "ACCEPTED",
    "PARTIAL": "PARTIAL",
    "AMBIGUOUS": "AMBIGUOUS",
    "UNSUPPORTED": "REJECTED",
}


def _as_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "dict"):
        return obj.dict()
    return {}


def _role_from_str(raw: Any) -> QuantityRole:
    if raw is None:
        return QuantityRole.UNKNOWN
    text = str(raw).upper()
    if text in ("VALUE", "CURRENT", "CURRENT_VALUE"):
        return QuantityRole.CURRENT_VALUE
    try:
        return QuantityRole(text)
    except ValueError:
        return QuantityRole.UNKNOWN


def _offsets(m: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    occ = m.get("occurrence") or {}
    if isinstance(occ, dict) and occ.get("start") is not None and occ.get("end") is not None:
        return (int(occ["start"]), int(occ["end"]))
    if m.get("span_offsets"):
        return tuple(m["span_offsets"])  # type: ignore[return-value]
    if m.get("offsets"):
        return tuple(m["offsets"])  # type: ignore[return-value]
    return None


def _mention_to_slot(m: Dict[str, Any]) -> ClaimSlot:
    certainty = str(m.get("certainty") or "EXPLICIT").upper()
    presence = PresenceStatus.EXPLICIT
    if certainty == "IMPLICIT":
        presence = PresenceStatus.IMPLICIT
    elif certainty == "AMBIGUOUS":
        presence = PresenceStatus.IMPLICIT
    return ClaimSlot(
        canonical_value=m.get("normalized_label") or m.get("canonical_value"),
        original_label=m.get("source_text") or m.get("original_label"),
        span_offsets=_offsets(m),
        provenance=ExtractionProvenance.EXPLICIT_TEXT,
        presence=presence,
        confidence=float(m.get("confidence", 1.0)),
        alternatives=list(m.get("alternatives") or []),
    )


def _measure_to_quantity(m: Dict[str, Any]) -> ClaimedQuantity:
    role = _role_from_str(m.get("role"))
    value = m.get("numeric_value", m.get("value"))
    unit = m.get("unit")
    if hasattr(unit, "value"):
        unit = unit.value
    if unit == "PERCENTAGE":
        unit = "PERCENT"
    slot = _mention_to_slot(m)
    return ClaimedQuantity(
        canonical_value=slot.canonical_value or (str(value) if value is not None else None),
        original_label=slot.original_label,
        span_offsets=slot.span_offsets,
        provenance=slot.provenance,
        presence=slot.presence,
        confidence=slot.confidence,
        alternatives=slot.alternatives,
        numeric_value=float(value) if value is not None else None,
        unit=str(unit) if unit is not None else None,
        role=role,
        validation_status=m.get("validation_status", "ACCEPTED"),
    )


def _partition_measures(
    measures: List[Dict[str, Any]],
) -> Tuple[Optional[ClaimedQuantity], List[ClaimedQuantity], List[Ambiguity]]:
    claimed_candidates: List[ClaimedQuantity] = []
    references: List[ClaimedQuantity] = []
    ambiguities: List[Ambiguity] = []

    for m in measures:
        q = _measure_to_quantity(m)
        if q.role in CLAIMED_QUANTITY_ROLES:
            claimed_candidates.append(q)
        elif q.role in REFERENCE_QUANTITY_ROLES:
            references.append(q)
        elif q.numeric_value is not None:
            q.role = QuantityRole.CURRENT_VALUE
            claimed_candidates.append(q)
        else:
            references.append(q)

    claimed: Optional[ClaimedQuantity] = None
    if len(claimed_candidates) == 1:
        claimed = claimed_candidates[0]
    elif len(claimed_candidates) > 1:
        claimed = claimed_candidates[0]
        ambiguities.append(
            Ambiguity(
                field="claimed_quantity",
                reason="MULTIPLE_CLAIMED_QUANTITY_CANDIDATES",
                alternatives=[c.model_dump() for c in claimed_candidates[1:]],
            )
        )
    return claimed, references, ambiguities


def llm_result_to_claim_specification(
    llm_result: Union[Any, Dict[str, Any]],
    claim_id: str,
    original_text: str,
) -> ClaimSpecification:
    data = _as_dict(llm_result)
    # Envelope with validated_data / raw_parsed_data
    if "validated_data" in data and data["validated_data"]:
        data = _as_dict(data["validated_data"])
    elif "raw_parsed_data" in data and data["raw_parsed_data"]:
        data = _as_dict(data["raw_parsed_data"])

    raw_status = data.get("parse_status")
    if hasattr(raw_status, "value"):
        raw_status = raw_status.value
    parse_status = _LLM_STATUS.get(str(raw_status or "COMPLETE").upper(), "ACCEPTED")

    ambiguities: List[Ambiguity] = []
    for a in data.get("ambiguities") or []:
        ad = _as_dict(a)
        ambiguities.append(
            Ambiguity(
                field=str(ad.get("field") or "unknown"),
                reason=str(ad.get("reason") or ""),
                alternatives=list(ad.get("alternatives") or []),
                requires_human_validation=bool(ad.get("requires_human_validation", True)),
            )
        )
    for mc in data.get("missing_context") or []:
        md = _as_dict(mc)
        ambiguities.append(
            Ambiguity(
                field=str(md.get("type") or "missing_context"),
                reason=str(md.get("reason") or "MISSING_CONTEXT"),
                alternatives=[],
            )
        )
        if parse_status == "ACCEPTED":
            parse_status = "MISSING_CONTEXT"

    indicators = [_as_dict(x) for x in (data.get("indicators") or [])]
    indicator = _mention_to_slot(indicators[0]) if indicators else None
    if len(indicators) > 1:
        ambiguities.append(
            Ambiguity(
                field="indicator",
                reason="MULTIPLE_INDICATORS",
                alternatives=indicators[1:],
            )
        )
        if parse_status == "ACCEPTED":
            parse_status = "AMBIGUOUS"

    populations = [_mention_to_slot(_as_dict(x)) for x in (data.get("populations") or [])]
    territories = [_mention_to_slot(_as_dict(x)) for x in (data.get("territories") or [])]

    time_exprs = [_as_dict(x) for x in (data.get("time_expressions") or [])]
    time_period = None
    if time_exprs:
        t0 = time_exprs[0]
        time_period = ClaimTime(
            canonical_value=t0.get("normalized_label") or t0.get("source_text"),
            original_label=t0.get("source_text"),
            span_offsets=_offsets(t0),
            start_date=t0.get("normalized_start") or t0.get("start_date"),
            end_date=t0.get("normalized_end") or t0.get("end_date"),
            precision=t0.get("granularity"),
            is_relative=bool(t0.get("is_relative")),
            confidence=float(t0.get("confidence", 1.0)),
        )
        if len(time_exprs) > 1:
            ambiguities.append(
                Ambiguity(
                    field="time_period",
                    reason="MULTIPLE_TIME_EXPRESSIONS",
                    alternatives=time_exprs[1:],
                )
            )

    claimed, references, meas_amb = _partition_measures(
        [_as_dict(x) for x in (data.get("measures") or [])]
    )
    ambiguities.extend(meas_amb)

    op = _as_dict(data.get("operation"))
    statistical_operation = None
    if op:
        statistical_operation = ClaimSlot(
            canonical_value=op.get("type") or op.get("canonical_value"),
            original_label=op.get("trigger_text") or op.get("source_text") or op.get("type"),
            span_offsets=_offsets(op),
            alternatives=[
                {
                    "direction": op.get("direction"),
                    "polarity": op.get("polarity"),
                    "comparator": op.get("comparator"),
                }
            ],
        )

    comparison = None
    comparisons = data.get("comparisons") or []
    if comparisons:
        c0 = _as_dict(comparisons[0])
        comparison = ClaimSlot(
            canonical_value=c0.get("type"),
            original_label=c0.get("trigger_text") or c0.get("source_text"),
            alternatives=[_as_dict(c) for c in comparisons[1:]],
        )

    freq = _as_dict(data.get("frequency")) if data.get("frequency") else {}
    expressed_frequency = (
        ClaimSlot(
            canonical_value=freq.get("value") or freq.get("canonical_value") or freq.get("type"),
            original_label=freq.get("source_text") or freq.get("value"),
        )
        if freq
        else None
    )

    adj = _as_dict(data.get("adjustment")) if data.get("adjustment") else {}
    adjustment = (
        ClaimSlot(
            canonical_value=adj.get("value") or adj.get("type"),
            original_label=adj.get("source_text") or adj.get("value"),
        )
        if adj
        else None
    )

    if indicator is None and parse_status == "ACCEPTED":
        parse_status = "PARTIAL"

    return ClaimSpecification(
        claim_id=claim_id,
        original_text=original_text,
        indicator=indicator,
        populations=populations,
        territories=territories,
        time_period=time_period,
        expressed_frequency=expressed_frequency,
        adjustment=adjustment,
        claimed_quantity=claimed,
        reference_quantities=references,
        statistical_operation=statistical_operation,
        comparison=comparison,
        parse_status=parse_status,
        ambiguities=ambiguities,
        warnings=[],
    )
