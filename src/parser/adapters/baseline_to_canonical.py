"""Adapt legacy baseline nested dict → ClaimSpecification V1."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

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

_ANSWERABILITY_TO_STATUS = {
    "VERIFIABLE": "ACCEPTED",
    "AMBIGUOUS": "AMBIGUOUS",
    "MISSING_CONTEXT": "MISSING_CONTEXT",
    "CONTRADICTION": "REJECTED",
}


def _role_from_str(raw: Any) -> QuantityRole:
    if raw is None:
        return QuantityRole.UNKNOWN
    text = str(raw).upper()
    # Baseline sometimes uses VALUE for a current level
    if text in ("VALUE", "CURRENT", "CURRENT_VALUE"):
        return QuantityRole.CURRENT_VALUE
    try:
        return QuantityRole(text)
    except ValueError:
        return QuantityRole.UNKNOWN


def _offsets(m: Dict[str, Any]) -> Optional[Tuple[int, int]]:
    if "span_offsets" in m and m["span_offsets"]:
        return tuple(m["span_offsets"])  # type: ignore[return-value]
    if "start" in m and "end" in m and m["start"] is not None and m["end"] is not None:
        return (int(m["start"]), int(m["end"]))
    return None


def _slot_from_label(
    label: Optional[str],
    *,
    canonical: Optional[str] = None,
    confidence: float = 1.0,
    presence: PresenceStatus = PresenceStatus.EXPLICIT,
) -> Optional[ClaimSlot]:
    if label is None or (isinstance(label, str) and not label.strip()):
        return None
    return ClaimSlot(
        canonical_value=canonical or label,
        original_label=label,
        provenance=ExtractionProvenance.EXPLICIT_TEXT,
        presence=presence,
        confidence=confidence,
    )


def _measure_to_quantity(m: Dict[str, Any]) -> ClaimedQuantity:
    role = _role_from_str(m.get("role"))
    value = m.get("value", m.get("numeric_value"))
    unit = m.get("unit")
    if unit == "PERCENTAGE":
        unit = "PERCENT"
    label = m.get("span_text") or m.get("source_text") or m.get("original_label")
    return ClaimedQuantity(
        canonical_value=str(value) if value is not None else None,
        original_label=label,
        span_offsets=_offsets(m),
        numeric_value=float(value) if value is not None else None,
        unit=unit,
        role=role,
        confidence=float(m.get("confidence", 1.0)),
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
        if q.role in CLAIMED_QUANTITY_ROLES or (
            q.role == QuantityRole.UNKNOWN and q.numeric_value is not None and not references
        ):
            # UNKNOWN with a bare level → treat as CURRENT if no claimed yet
            if q.role == QuantityRole.UNKNOWN:
                q.role = QuantityRole.CURRENT_VALUE
            claimed_candidates.append(q)
        elif q.role in REFERENCE_QUANTITY_ROLES:
            references.append(q)
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


def baseline_dict_to_claim_specification(
    baseline: Dict[str, Any],
    claim_id: Optional[str] = None,
) -> ClaimSpecification:
    identity = baseline.get("identity") or {}
    subject = baseline.get("subject") or {}
    time = baseline.get("time") or {}
    operation = baseline.get("operation") or {}
    status = baseline.get("status") or {}
    modifiers = baseline.get("modifiers") or {}

    text = identity.get("text") or baseline.get("raw_text") or ""
    cid = claim_id or baseline.get("claim_id") or identity.get("claim_id") or "unknown"

    answerability = status.get("answerability")
    parse_status = _ANSWERABILITY_TO_STATUS.get(answerability, "ACCEPTED")
    if answerability is None and status.get("error"):
        parse_status = "REJECTED"

    ambiguities: List[Ambiguity] = []
    warnings: List[str] = []

    indicator = _slot_from_label(subject.get("indicator"))
    if indicator is None:
        if parse_status == "ACCEPTED":
            parse_status = "PARTIAL"
        ambiguities.append(
            Ambiguity(field="indicator", reason="NO_INDICATOR", alternatives=[])
        )

    territories: List[ClaimSlot] = []
    terr_main = subject.get("territory_main")
    terr_status = subject.get("territory_status")
    presence = PresenceStatus.EXPLICIT
    if terr_status in ("MISSING", "INFERRED", "AMBIGUOUS"):
        presence = (
            PresenceStatus.MISSING
            if terr_status == "MISSING"
            else PresenceStatus.IMPLICIT
        )
    if terr_main:
        territories.append(
            _slot_from_label(terr_main, presence=presence)  # type: ignore[arg-type]
        )
    alts = subject.get("territory_alternatives") or []
    if alts:
        ambiguities.append(
            Ambiguity(
                field="territories",
                reason="TERRITORY_ALTERNATIVES",
                alternatives=alts,
            )
        )
        if parse_status == "ACCEPTED":
            parse_status = "AMBIGUOUS"

    populations: List[ClaimSlot] = []
    pop = subject.get("population")
    if pop:
        populations.append(_slot_from_label(pop))  # type: ignore[arg-type]
    pop_alts = subject.get("population_alternatives") or []
    if pop_alts:
        ambiguities.append(
            Ambiguity(
                field="populations",
                reason="POPULATION_ALTERNATIVES",
                alternatives=pop_alts,
            )
        )
        if parse_status == "ACCEPTED":
            parse_status = "AMBIGUOUS"

    period_rel = time.get("period_relative")
    period_exp = time.get("period_explicit")
    time_period = None
    if period_exp or period_rel or time.get("granularity"):
        time_period = ClaimTime(
            canonical_value=period_exp or period_rel,
            original_label=period_exp or period_rel,
            start_date=time.get("start_date"),
            end_date=time.get("end_date"),
            precision=time.get("granularity"),
            is_relative=bool(period_rel) and not period_exp,
        )

    freq = time.get("frequency")
    expressed_frequency = _slot_from_label(freq) if freq else None

    claimed, references, meas_amb = _partition_measures(baseline.get("measures") or [])
    ambiguities.extend(meas_amb)
    if meas_amb and parse_status == "ACCEPTED":
        parse_status = "AMBIGUOUS"

    # Singular gold-style measure
    if claimed is None and baseline.get("measure"):
        claimed = _measure_to_quantity({**baseline["measure"], "role": "CURRENT_VALUE"})

    op_type = operation.get("type")
    op_dir = operation.get("direction")
    op_pol = operation.get("polarity")
    statistical_operation = None
    if op_type or op_dir:
        statistical_operation = ClaimSlot(
            canonical_value=op_type,
            original_label=op_type,
            alternatives=[{"direction": op_dir, "polarity": op_pol}],
        )

    adjustment = None
    adjustments = modifiers.get("adjustments")
    if adjustments:
        if isinstance(adjustments, list) and adjustments:
            first = adjustments[0]
            label = first if isinstance(first, str) else str(first)
            adjustment = _slot_from_label(label)
        elif isinstance(adjustments, str):
            adjustment = _slot_from_label(adjustments)

    return ClaimSpecification(
        claim_id=str(cid),
        original_text=text,
        indicator=indicator,
        populations=populations,
        territories=territories,
        time_period=time_period,
        expressed_frequency=expressed_frequency,
        adjustment=adjustment,
        claimed_quantity=claimed,
        reference_quantities=references,
        statistical_operation=statistical_operation,
        parse_status=parse_status,
        ambiguities=ambiguities,
        warnings=warnings,
    )
