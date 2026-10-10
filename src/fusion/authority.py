from enum import Enum
from typing import Any, Dict, Optional

from src.parser.claim_specification import (
    ClaimSlot,
    ClaimTime,
    ClaimedQuantity,
    PresenceStatus,
)


class DecisionType(str, Enum):
    AGREEMENT = "AGREEMENT"
    BASELINE_SELECTED = "BASELINE_SELECTED"
    LLM_SELECTED = "LLM_SELECTED"
    DETERMINISTIC_VALIDATOR_SELECTED = "DETERMINISTIC_VALIDATOR_SELECTED"
    MERGED = "MERGED"
    BOTH_RETAINED_AS_ALTERNATIVES = "BOTH_RETAINED_AS_ALTERNATIVES"
    CONFLICT_UNRESOLVED = "CONFLICT_UNRESOLVED"
    REJECTED = "REJECTED"


class ExplanationCode(str, Enum):
    EXACT_AGREEMENT = "EXACT_AGREEMENT"
    SAME_SPAN_VALUE_DISAGREEMENT = "SAME_SPAN_VALUE_DISAGREEMENT"
    NUMERIC_VALIDATOR_AUTHORITY = "NUMERIC_VALIDATOR_AUTHORITY"
    TEMPORAL_VALIDATOR_AUTHORITY = "TEMPORAL_VALIDATOR_AUTHORITY"
    COG_AUTHORITY = "COG_AUTHORITY"
    BASELINE_EXACT_LEXICON_MATCH = "BASELINE_EXACT_LEXICON_MATCH"
    LLM_SEMANTIC_DECOMPOSITION = "LLM_SEMANTIC_DECOMPOSITION"
    LLM_POST_VALIDATED_ONLY = "LLM_POST_VALIDATED_ONLY"
    BASELINE_VALID_ONLY = "BASELINE_VALID_ONLY"
    UNRESOLVED_ROLE_CONFLICT = "UNRESOLVED_ROLE_CONFLICT"
    AMBIGUOUS_GEOGRAPHY = "AMBIGUOUS_GEOGRAPHY"
    FORBIDDEN_LLM_INFERENCE = "FORBIDDEN_LLM_INFERENCE"
    UNIT_SCALE_MISMATCH = "UNIT_SCALE_MISMATCH"
    APPROXIMATION_MISMATCH = "APPROXIMATION_MISMATCH"
    BOUNDS_MISMATCH = "BOUNDS_MISMATCH"
    CANONICAL_CODE_CONFLICT = "CANONICAL_CODE_CONFLICT"
    SEMANTIC_ALTERNATIVES = "SEMANTIC_ALTERNATIVES"
    TIME_MISMATCH = "TIME_MISMATCH"
    OPERATION_MISMATCH = "OPERATION_MISMATCH"


def _llm_accepted(q) -> bool:
    status = getattr(q, "validation_status", None)
    if status in ("ACCEPTED", "ACCEPTED_WITH_WARNINGS", None):
        return q.presence != PresenceStatus.MISSING
    return False


def _norm_canon(slot: Optional[ClaimSlot]) -> Optional[str]:
    if slot is None or not slot.canonical_value:
        return None
    return slot.canonical_value.strip().upper()


def _norm_label(slot: Optional[ClaimSlot]) -> str:
    if slot is None:
        return ""
    return (slot.original_label or "").lower().strip()


def _evidence(b: Optional[ClaimSlot], l: Optional[ClaimSlot]) -> Dict[str, Any]:
    return {
        "baseline_offsets": getattr(b, "span_offsets", None) if b else None,
        "llm_offsets": getattr(l, "span_offsets", None) if l else None,
        "baseline_label": getattr(b, "original_label", None) if b else None,
        "llm_label": getattr(l, "original_label", None) if l else None,
        "baseline_canonical": getattr(b, "canonical_value", None) if b else None,
        "llm_canonical": getattr(l, "canonical_value", None) if l else None,
    }


def _decision(
    decision: DecisionType,
    explanation: ExplanationCode,
    result: Any,
    b: Optional[ClaimSlot] = None,
    l: Optional[ClaimSlot] = None,
) -> Dict[str, Any]:
    return {
        "decision": decision,
        "explanation": explanation,
        "result": result,
        "evidence": _evidence(b, l),
    }


def _quantity_core_equal(b: ClaimedQuantity, l: ClaimedQuantity) -> bool:
    return (
        b.numeric_value == l.numeric_value
        and b.unit == l.unit
        and b.scale == l.scale
        and b.role == l.role
        and b.approximation == l.approximation
        and b.sign == l.sign
        and b.lower_bound == l.lower_bound
        and b.upper_bound == l.upper_bound
    )


def _unit_scale_approx_bounds_agree(b: ClaimedQuantity, l: ClaimedQuantity) -> bool:
    return (
        b.unit == l.unit
        and b.scale == l.scale
        and b.approximation == l.approximation
        and b.sign == l.sign
        and b.lower_bound == l.lower_bound
        and b.upper_bound == l.upper_bound
    )


def _slot_meaning_equal(b: ClaimSlot, l: ClaimSlot) -> bool:
    bc, lc = _norm_canon(b), _norm_canon(l)
    if bc and lc:
        return bc == lc
    bl, ll = _norm_label(b), _norm_label(l)
    return bool(bl) and bl == ll


def _attach_alternative(primary: ClaimSlot, other: ClaimSlot) -> ClaimSlot:
    merged = primary.model_copy(deep=True)
    alt = other.model_dump()
    alts = list(merged.alternatives or [])
    alts.append(alt)
    merged.alternatives = alts
    return merged


class AuthorityMatrix:
    """Applique les règles de résolution par sous-champ (ClaimSpecification V1)."""

    @staticmethod
    def fuse_quantity(
        b: Optional[ClaimedQuantity], l: Optional[ClaimedQuantity]
    ) -> Dict[str, Any]:
        if not b and not l:
            return _decision(
                DecisionType.REJECTED,
                ExplanationCode.FORBIDDEN_LLM_INFERENCE,
                None,
            )

        if not b and l:
            if _llm_accepted(l):
                return _decision(
                    DecisionType.LLM_SELECTED,
                    ExplanationCode.LLM_POST_VALIDATED_ONLY,
                    l.model_copy(deep=True),
                    None,
                    l,
                )
            return _decision(
                DecisionType.REJECTED,
                ExplanationCode.FORBIDDEN_LLM_INFERENCE,
                None,
                None,
                l,
            )

        if b and not l:
            return _decision(
                DecisionType.BASELINE_SELECTED,
                ExplanationCode.BASELINE_VALID_ONLY,
                b.model_copy(deep=True),
                b,
                None,
            )

        merged = b.model_copy(deep=True)

        if _quantity_core_equal(b, l):
            return _decision(
                DecisionType.AGREEMENT,
                ExplanationCode.EXACT_AGREEMENT,
                merged,
                b,
                l,
            )

        if b.unit != l.unit or b.scale != l.scale:
            return _decision(
                DecisionType.CONFLICT_UNRESOLVED,
                ExplanationCode.UNIT_SCALE_MISMATCH,
                merged,
                b,
                l,
            )

        if b.approximation != l.approximation:
            return _decision(
                DecisionType.CONFLICT_UNRESOLVED,
                ExplanationCode.APPROXIMATION_MISMATCH,
                merged,
                b,
                l,
            )

        if b.lower_bound != l.lower_bound or b.upper_bound != l.upper_bound:
            return _decision(
                DecisionType.CONFLICT_UNRESOLVED,
                ExplanationCode.BOUNDS_MISMATCH,
                merged,
                b,
                l,
            )

        if b.span_offsets == l.span_offsets and b.numeric_value != l.numeric_value:
            if (
                _unit_scale_approx_bounds_agree(b, l)
                and b.confidence >= 0.9
                and (b.validation_status or "ACCEPTED") == "ACCEPTED"
            ):
                return _decision(
                    DecisionType.DETERMINISTIC_VALIDATOR_SELECTED,
                    ExplanationCode.NUMERIC_VALIDATOR_AUTHORITY,
                    merged,
                    b,
                    l,
                )
            return _decision(
                DecisionType.CONFLICT_UNRESOLVED,
                ExplanationCode.SAME_SPAN_VALUE_DISAGREEMENT,
                merged,
                b,
                l,
            )

        if b.role != l.role:
            return _decision(
                DecisionType.BOTH_RETAINED_AS_ALTERNATIVES,
                ExplanationCode.UNRESOLVED_ROLE_CONFLICT,
                _attach_alternative(merged, l),
                b,
                l,
            )

        if b.sign != l.sign:
            return _decision(
                DecisionType.CONFLICT_UNRESOLVED,
                ExplanationCode.UNIT_SCALE_MISMATCH,
                merged,
                b,
                l,
            )

        if b.confidence >= 0.9 and (b.validation_status or "ACCEPTED") == "ACCEPTED":
            return _decision(
                DecisionType.BASELINE_SELECTED,
                ExplanationCode.NUMERIC_VALIDATOR_AUTHORITY,
                merged,
                b,
                l,
            )
        return _decision(
            DecisionType.BOTH_RETAINED_AS_ALTERNATIVES,
            ExplanationCode.UNRESOLVED_ROLE_CONFLICT,
            _attach_alternative(merged, l),
            b,
            l,
        )

    @staticmethod
    def fuse_measure(
        b: Optional[ClaimedQuantity], l: Optional[ClaimedQuantity]
    ) -> Dict[str, Any]:
        """Alias historique — délègue à fuse_quantity (sémantique riche)."""
        return AuthorityMatrix.fuse_quantity(b, l)

    @staticmethod
    def fuse_territory(b: Optional[ClaimSlot], l: Optional[ClaimSlot]) -> Dict[str, Any]:
        if not b and not l:
            return _decision(
                DecisionType.REJECTED,
                ExplanationCode.FORBIDDEN_LLM_INFERENCE,
                None,
            )

        if not b and l:
            if _llm_accepted(l) and l.canonical_value:
                return _decision(
                    DecisionType.LLM_SELECTED,
                    ExplanationCode.LLM_POST_VALIDATED_ONLY,
                    l.model_copy(deep=True),
                    None,
                    l,
                )
            return _decision(
                DecisionType.REJECTED,
                ExplanationCode.FORBIDDEN_LLM_INFERENCE,
                None,
                None,
                l,
            )

        if b and not l:
            return _decision(
                DecisionType.BASELINE_SELECTED,
                ExplanationCode.BASELINE_VALID_ONLY,
                b.model_copy(deep=True),
                b,
                None,
            )

        bc, lc = _norm_canon(b), _norm_canon(l)
        if bc and lc and bc == lc:
            return _decision(
                DecisionType.AGREEMENT,
                ExplanationCode.EXACT_AGREEMENT,
                b.model_copy(deep=True),
                b,
                l,
            )

        same_surface = (
            bool(_norm_label(b))
            and _norm_label(b) == _norm_label(l)
        ) or (
            b.span_offsets is not None
            and b.span_offsets == l.span_offsets
        )

        if same_surface and bc and lc and bc != lc:
            # Explicit text ≠ correct code — never baseline auto-win
            return _decision(
                DecisionType.CONFLICT_UNRESOLVED,
                ExplanationCode.CANONICAL_CODE_CONFLICT,
                b.model_copy(deep=True),
                b,
                l,
            )

        if bc and lc and bc != lc:
            return _decision(
                DecisionType.BOTH_RETAINED_AS_ALTERNATIVES,
                ExplanationCode.AMBIGUOUS_GEOGRAPHY,
                _attach_alternative(b.model_copy(deep=True), l),
                b,
                l,
            )

        # One side missing canonical — retain alternatives
        return _decision(
            DecisionType.BOTH_RETAINED_AS_ALTERNATIVES,
            ExplanationCode.AMBIGUOUS_GEOGRAPHY,
            _attach_alternative(b.model_copy(deep=True), l),
            b,
            l,
        )

    @staticmethod
    def _fuse_canonical_slot(
        b: Optional[ClaimSlot],
        l: Optional[ClaimSlot],
        mismatch_explanation: ExplanationCode = ExplanationCode.SEMANTIC_ALTERNATIVES,
    ) -> Dict[str, Any]:
        if not b and not l:
            return _decision(
                DecisionType.REJECTED,
                ExplanationCode.FORBIDDEN_LLM_INFERENCE,
                None,
            )
        if not b and l:
            if l.presence == PresenceStatus.MISSING:
                return _decision(
                    DecisionType.REJECTED,
                    ExplanationCode.FORBIDDEN_LLM_INFERENCE,
                    None,
                    None,
                    l,
                )
            return _decision(
                DecisionType.LLM_SELECTED,
                ExplanationCode.LLM_POST_VALIDATED_ONLY,
                l.model_copy(deep=True),
                None,
                l,
            )
        if b and not l:
            return _decision(
                DecisionType.BASELINE_SELECTED,
                ExplanationCode.BASELINE_VALID_ONLY,
                b.model_copy(deep=True),
                b,
                None,
            )
        if _slot_meaning_equal(b, l):
            return _decision(
                DecisionType.AGREEMENT,
                ExplanationCode.EXACT_AGREEMENT,
                b.model_copy(deep=True),
                b,
                l,
            )
        return _decision(
            DecisionType.BOTH_RETAINED_AS_ALTERNATIVES,
            mismatch_explanation,
            _attach_alternative(b.model_copy(deep=True), l),
            b,
            l,
        )

    @staticmethod
    def fuse_indicator(b: Optional[ClaimSlot], l: Optional[ClaimSlot]) -> Dict[str, Any]:
        return AuthorityMatrix._fuse_canonical_slot(b, l)

    @staticmethod
    def fuse_population(b: Optional[ClaimSlot], l: Optional[ClaimSlot]) -> Dict[str, Any]:
        return AuthorityMatrix._fuse_canonical_slot(b, l)

    @staticmethod
    def fuse_frequency(b: Optional[ClaimSlot], l: Optional[ClaimSlot]) -> Dict[str, Any]:
        return AuthorityMatrix._fuse_canonical_slot(b, l)

    @staticmethod
    def fuse_adjustment(b: Optional[ClaimSlot], l: Optional[ClaimSlot]) -> Dict[str, Any]:
        return AuthorityMatrix._fuse_canonical_slot(b, l)

    @staticmethod
    def fuse_operation(b: Optional[ClaimSlot], l: Optional[ClaimSlot]) -> Dict[str, Any]:
        return AuthorityMatrix._fuse_canonical_slot(
            b, l, mismatch_explanation=ExplanationCode.OPERATION_MISMATCH
        )

    @staticmethod
    def fuse_time(b: Optional[ClaimTime], l: Optional[ClaimTime]) -> Dict[str, Any]:
        if not b and not l:
            return _decision(
                DecisionType.REJECTED,
                ExplanationCode.FORBIDDEN_LLM_INFERENCE,
                None,
            )
        if not b and l:
            return _decision(
                DecisionType.LLM_SELECTED,
                ExplanationCode.LLM_POST_VALIDATED_ONLY,
                l.model_copy(deep=True),
                None,
                l,
            )
        if b and not l:
            return _decision(
                DecisionType.BASELINE_SELECTED,
                ExplanationCode.BASELINE_VALID_ONLY,
                b.model_copy(deep=True),
                b,
                None,
            )

        same = (
            b.start_date == l.start_date
            and b.end_date == l.end_date
            and b.precision == l.precision
            and b.is_relative == l.is_relative
        )
        if same:
            return _decision(
                DecisionType.AGREEMENT,
                ExplanationCode.EXACT_AGREEMENT,
                b.model_copy(deep=True),
                b,
                l,
            )

        # Absolute incompatible dates → conflict; otherwise alternatives
        if (
            not b.is_relative
            and not l.is_relative
            and b.start_date
            and l.start_date
            and (b.start_date != l.start_date or b.end_date != l.end_date)
        ):
            return _decision(
                DecisionType.CONFLICT_UNRESOLVED,
                ExplanationCode.TIME_MISMATCH,
                b.model_copy(deep=True),
                b,
                l,
            )

        return _decision(
            DecisionType.BOTH_RETAINED_AS_ALTERNATIVES,
            ExplanationCode.TIME_MISMATCH,
            _attach_alternative(b.model_copy(deep=True), l),
            b,
            l,
        )
