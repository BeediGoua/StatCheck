from enum import Enum
from typing import Any, Dict, Optional

from src.parser.claim_specification import ClaimSlot, ClaimedQuantity, PresenceStatus


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


def _llm_accepted(q) -> bool:
    status = getattr(q, "validation_status", None)
    if status in ("ACCEPTED", "ACCEPTED_WITH_WARNINGS", None):
        return q.presence != PresenceStatus.MISSING
    return False


class AuthorityMatrix:
    """Applique les règles de résolution par sous-champ (ClaimSpecification V1)."""

    @staticmethod
    def fuse_measure(
        b: Optional[ClaimedQuantity], l: Optional[ClaimedQuantity]
    ) -> Dict[str, Any]:
        if not b and not l:
            return {
                "decision": DecisionType.REJECTED,
                "explanation": ExplanationCode.FORBIDDEN_LLM_INFERENCE,
                "result": None,
            }

        if not b and l:
            if _llm_accepted(l):
                merged_l = l.model_copy(deep=True)
                return {
                    "decision": DecisionType.LLM_SELECTED,
                    "explanation": ExplanationCode.LLM_POST_VALIDATED_ONLY,
                    "result": merged_l,
                }
            return {
                "decision": DecisionType.REJECTED,
                "explanation": ExplanationCode.FORBIDDEN_LLM_INFERENCE,
                "result": None,
            }

        if b and not l:
            merged_b = b.model_copy(deep=True)
            return {
                "decision": DecisionType.BASELINE_SELECTED,
                "explanation": ExplanationCode.BASELINE_VALID_ONLY,
                "result": merged_b,
            }

        merged = b.model_copy(deep=True)

        if (
            b.numeric_value == l.numeric_value
            and b.unit == l.unit
            and b.role == l.role
        ):
            return {
                "decision": DecisionType.AGREEMENT,
                "explanation": ExplanationCode.EXACT_AGREEMENT,
                "result": merged,
            }

        if b.span_offsets == l.span_offsets and b.numeric_value != l.numeric_value:
            if b.confidence >= 0.9 and (b.validation_status or "ACCEPTED") == "ACCEPTED":
                return {
                    "decision": DecisionType.DETERMINISTIC_VALIDATOR_SELECTED,
                    "explanation": ExplanationCode.NUMERIC_VALIDATOR_AUTHORITY,
                    "result": merged,
                }
            return {
                "decision": DecisionType.BOTH_RETAINED_AS_ALTERNATIVES,
                "explanation": ExplanationCode.UNRESOLVED_ROLE_CONFLICT,
                "result": merged,
            }

        if b.role != l.role:
            return {
                "decision": DecisionType.BOTH_RETAINED_AS_ALTERNATIVES,
                "explanation": ExplanationCode.UNRESOLVED_ROLE_CONFLICT,
                "result": merged,
            }

        if b.confidence >= 0.9 and (b.validation_status or "ACCEPTED") == "ACCEPTED":
            return {
                "decision": DecisionType.BASELINE_SELECTED,
                "explanation": ExplanationCode.NUMERIC_VALIDATOR_AUTHORITY,
                "result": merged,
            }
        return {
            "decision": DecisionType.BOTH_RETAINED_AS_ALTERNATIVES,
            "explanation": ExplanationCode.UNRESOLVED_ROLE_CONFLICT,
            "result": merged,
        }

    @staticmethod
    def fuse_territory(b: Optional[ClaimSlot], l: Optional[ClaimSlot]) -> Dict[str, Any]:
        if not b and not l:
            return {
                "decision": DecisionType.REJECTED,
                "explanation": ExplanationCode.FORBIDDEN_LLM_INFERENCE,
                "result": None,
            }

        if not b and l:
            if _llm_accepted(l) and l.canonical_value:
                return {
                    "decision": DecisionType.LLM_SELECTED,
                    "explanation": ExplanationCode.LLM_POST_VALIDATED_ONLY,
                    "result": l.model_copy(deep=True),
                }
            return {
                "decision": DecisionType.REJECTED,
                "explanation": ExplanationCode.FORBIDDEN_LLM_INFERENCE,
                "result": None,
            }

        if b and not l:
            return {
                "decision": DecisionType.BASELINE_SELECTED,
                "explanation": ExplanationCode.BASELINE_VALID_ONLY,
                "result": b.model_copy(deep=True),
            }

        merged = b.model_copy(deep=True)
        if b.canonical_value != l.canonical_value:
            if b.presence == PresenceStatus.EXPLICIT:
                return {
                    "decision": DecisionType.BASELINE_SELECTED,
                    "explanation": ExplanationCode.COG_AUTHORITY,
                    "result": merged,
                }
            return {
                "decision": DecisionType.BOTH_RETAINED_AS_ALTERNATIVES,
                "explanation": ExplanationCode.AMBIGUOUS_GEOGRAPHY,
                "result": merged,
            }

        return {
            "decision": DecisionType.AGREEMENT,
            "explanation": ExplanationCode.EXACT_AGREEMENT,
            "result": merged,
        }
