from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

from src.parser.claim_specification import ClaimSlot, ClaimedQuantity

try:
    from scipy.optimize import linear_sum_assignment

    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False


class AlignmentType(str, Enum):
    EXACT = "EXACT"
    SAME_OFFSETS = "SAME_OFFSETS"
    OVERLAP = "OVERLAP"
    CONTAINS = "CONTAINS"
    CONTAINED_BY = "CONTAINED_BY"
    NORMALIZED_VALUE_MATCH = "NORMALIZED_VALUE_MATCH"
    SEMANTICALLY_COMPATIBLE = "SEMANTICALLY_COMPATIBLE"
    CONFLICTING = "CONFLICTING"
    UNRELATED = "UNRELATED"
    DECOMPOSITION = "DECOMPOSITION"


class SemanticRelation(str, Enum):
    """Alignment-layer relation — not a business agreement decision."""

    SAME_MENTION = "SAME_MENTION"
    SAME_MEANING = "SAME_MEANING"
    SEMANTIC_DISAGREEMENT = "SEMANTIC_DISAGREEMENT"
    UNRELATED = "UNRELATED"


def calculate_iou(
    offsets1: Optional[Tuple[int, int]], offsets2: Optional[Tuple[int, int]]
) -> float:
    if not offsets1 or not offsets2:
        return 0.0
    s1, e1 = offsets1
    s2, e2 = offsets2
    intersection = max(0, min(e1, e2) - max(s1, s2))
    union = max(e1, e2) - min(s1, s2)
    return intersection / union if union > 0 else 0.0


def _norm_label(slot: ClaimSlot) -> str:
    return (slot.original_label or "").lower().strip()


def _quantity_rich_equal(a: ClaimedQuantity, b: ClaimedQuantity) -> bool:
    return (
        a.numeric_value == b.numeric_value
        and a.unit == b.unit
        and a.scale == b.scale
        and a.role == b.role
        and a.approximation == b.approximation
        and a.sign == b.sign
        and a.lower_bound == b.lower_bound
        and a.upper_bound == b.upper_bound
    )


def _canonical_or_label_equal(a: ClaimSlot, b: ClaimSlot) -> bool:
    if a.canonical_value and b.canonical_value:
        return a.canonical_value.strip().upper() == b.canonical_value.strip().upper()
    la, lb = _norm_label(a), _norm_label(b)
    return bool(la) and la == lb


def get_alignment_type(p1: ClaimSlot, p2: ClaimSlot, score: float) -> AlignmentType:
    if score < 0.45:
        return AlignmentType.UNRELATED

    if p1.span_offsets == p2.span_offsets and (p1.original_label or "") == (
        p2.original_label or ""
    ):
        return AlignmentType.EXACT
    if p1.span_offsets == p2.span_offsets:
        return AlignmentType.SAME_OFFSETS

    if p1.span_offsets and p2.span_offsets:
        s1, e1 = p1.span_offsets
        s2, e2 = p2.span_offsets
        if s1 <= s2 and e1 >= e2:
            return AlignmentType.CONTAINS
        if s1 >= s2 and e1 <= e2:
            return AlignmentType.CONTAINED_BY
        if calculate_iou(p1.span_offsets, p2.span_offsets) > 0:
            return AlignmentType.OVERLAP

    if isinstance(p1, ClaimedQuantity) and isinstance(p2, ClaimedQuantity):
        if (
            p1.numeric_value is not None
            and p2.numeric_value is not None
            and abs(p1.numeric_value - p2.numeric_value) < 1e-5
        ):
            return AlignmentType.NORMALIZED_VALUE_MATCH

    return AlignmentType.SEMANTICALLY_COMPATIBLE


def get_semantic_relation(
    p1: ClaimSlot, p2: ClaimSlot, score: float, align_type: AlignmentType
) -> SemanticRelation:
    """Classify mention/meaning relation. Never decides business AGREEMENT."""
    if score < 0.45 or align_type == AlignmentType.UNRELATED:
        return SemanticRelation.UNRELATED

    same_mention = align_type in (
        AlignmentType.EXACT,
        AlignmentType.SAME_OFFSETS,
        AlignmentType.CONTAINS,
        AlignmentType.CONTAINED_BY,
        AlignmentType.OVERLAP,
    )

    if isinstance(p1, ClaimedQuantity) and isinstance(p2, ClaimedQuantity):
        meaning_match = _quantity_rich_equal(p1, p2)
    else:
        meaning_match = _canonical_or_label_equal(p1, p2)

    if meaning_match:
        return SemanticRelation.SAME_MEANING
    if same_mention:
        return SemanticRelation.SAME_MENTION
    return SemanticRelation.SEMANTIC_DISAGREEMENT


class FieldAligner:
    @staticmethod
    def calculate_score(m1: ClaimSlot, m2: ClaimSlot) -> float:
        """Calcule un score d'alignement [0, 1]."""
        score = 0.0

        iou = calculate_iou(m1.span_offsets, m2.span_offsets)
        score += iou * 0.6

        t1 = (m1.original_label or "").lower().strip()
        t2 = (m2.original_label or "").lower().strip()
        if t1 and t2:
            if t1 == t2:
                score += 0.2
            elif t1 in t2 or t2 in t1:
                # e.g. "chômage" vs "taux de chômage"
                score += 0.2

        if isinstance(m1, ClaimedQuantity) and isinstance(m2, ClaimedQuantity):
            if (
                m1.numeric_value is not None
                and m2.numeric_value is not None
                and abs(m1.numeric_value - m2.numeric_value) < 1e-5
            ):
                score += 0.2
        elif m1.canonical_value and m1.canonical_value == m2.canonical_value:
            score += 0.2
        elif iou > 0:
            score += 0.15

        return min(1.0, score)


class BipartiteAligner:
    """Moteur d'appariement global optimal."""

    @staticmethod
    def align(list_baseline: List[ClaimSlot], list_llm: List[ClaimSlot]) -> List[Dict[str, Any]]:
        results = []
        if not list_baseline or not list_llm:
            return results

        if not HAS_SCIPY:
            raise RuntimeError("scipy est requis pour utiliser l'appariement optimal hongrois.")

        cost_matrix = []
        for b in list_baseline:
            row = []
            for l in list_llm:
                score = FieldAligner.calculate_score(b, l)
                row.append(-score)
            cost_matrix.append(row)

        row_ind, col_ind = linear_sum_assignment(cost_matrix)

        for r, c in zip(row_ind, col_ind):
            score = -cost_matrix[r][c]
            if score >= 0.45:
                align_type = get_alignment_type(list_baseline[r], list_llm[c], score)
                relation = get_semantic_relation(
                    list_baseline[r], list_llm[c], score, align_type
                )
                results.append(
                    {
                        "baseline_mention": list_baseline[r],
                        "llm_mention": list_llm[c],
                        "score": score,
                        "alignment_type": align_type,
                        "semantic_relation": relation,
                        "baseline_idx": r,
                        "llm_idx": c,
                    }
                )

        return results
