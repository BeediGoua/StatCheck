import math
from enum import Enum
from typing import List, Tuple, Dict, Any, Optional
from src.parser.canonical import (
    CanonicalMentionBase, CanonicalMeasure, CanonicalTerritory,
    CanonicalTimeExpression, CanonicalIndicator, CanonicalPopulation
)

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

def calculate_iou(offsets1: Optional[Tuple[int, int]], offsets2: Optional[Tuple[int, int]]) -> float:
    if not offsets1 or not offsets2:
        return 0.0
    s1, e1 = offsets1
    s2, e2 = offsets2
    intersection = max(0, min(e1, e2) - max(s1, s2))
    union = max(e1, e2) - min(s1, s2)
    return intersection / union if union > 0 else 0.0

def get_alignment_type(p1: CanonicalMentionBase, p2: CanonicalMentionBase, score: float) -> AlignmentType:
    if score < 0.45:
        return AlignmentType.UNRELATED
        
    if p1.offsets == p2.offsets and p1.source_text == p2.source_text:
        return AlignmentType.EXACT
    if p1.offsets == p2.offsets:
        return AlignmentType.SAME_OFFSETS
        
    if p1.offsets and p2.offsets:
        s1, e1 = p1.offsets
        s2, e2 = p2.offsets
        if s1 <= s2 and e1 >= e2:
            return AlignmentType.CONTAINS
        if s1 >= s2 and e1 <= e2:
            return AlignmentType.CONTAINED_BY
        if calculate_iou(p1.offsets, p2.offsets) > 0:
            return AlignmentType.OVERLAP
            
    # Si pas de chevauchement d'offsets mais score >= 0.45 (via valeur numérique par exemple)
    if isinstance(p1, CanonicalMeasure) and isinstance(p2, CanonicalMeasure):
        if p1.value is not None and p2.value is not None and abs(p1.value - p2.value) < 1e-5:
            return AlignmentType.NORMALIZED_VALUE_MATCH
            
    return AlignmentType.SEMANTICALLY_COMPATIBLE

class FieldAligner:
    @staticmethod
    def calculate_score(m1: CanonicalMentionBase, m2: CanonicalMentionBase) -> float:
        """Calcule un score d'alignement [0, 1]."""
        if m1.source_scope != m2.source_scope:
            return 0.0 # Règle absolue
            
        score = 0.0
        
        iou = calculate_iou(m1.offsets, m2.offsets)
        score += iou * 0.6
        
        if m1.source_text.lower().strip() == m2.source_text.lower().strip():
            score += 0.2
            
        # Poids spécifiques par champ
        if isinstance(m1, CanonicalMeasure) and isinstance(m2, CanonicalMeasure):
            if m1.value is not None and m2.value is not None and abs(m1.value - m2.value) < 1e-5:
                score += 0.2
        elif isinstance(m1, CanonicalTerritory) and isinstance(m2, CanonicalTerritory):
            if m1.code == m2.code and m1.code is not None:
                score += 0.2
        else:
            # Pour les autres, on donne un poids sémantique basique
            score += 0.2 * iou # Pour compenser
                
        return min(1.0, score)

class BipartiteAligner:
    """Moteur d'appariement global optimal."""
    
    @staticmethod
    def align(list_baseline: List[CanonicalMentionBase], list_llm: List[CanonicalMentionBase]) -> List[Dict[str, Any]]:
        results = []
        if not list_baseline or not list_llm:
            return results
            
        if not HAS_SCIPY:
            raise RuntimeError("scipy est requis pour utiliser l'appariement optimal hongrois.")
            
        n_base = len(list_baseline)
        n_llm = len(list_llm)
        cost_matrix = []
        
        for b in list_baseline:
            row = []
            for l in list_llm:
                score = FieldAligner.calculate_score(b, l)
                row.append(-score) # scipy minimise, donc on utilise des coûts négatifs
            cost_matrix.append(row)
            
        row_ind, col_ind = linear_sum_assignment(cost_matrix)
        
        for r, c in zip(row_ind, col_ind):
            score = -cost_matrix[r][c]
            if score >= 0.45: # Seuil d'alignement minimum
                align_type = get_alignment_type(list_baseline[r], list_llm[c], score)
                results.append({
                    "baseline_mention": list_baseline[r],
                    "llm_mention": list_llm[c],
                    "score": score,
                    "alignment_type": align_type,
                    "baseline_idx": r,
                    "llm_idx": c
                })
                
        return results
