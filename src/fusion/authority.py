from enum import Enum
from typing import Dict, Any, Optional
from src.parser.canonical import (
    CanonicalMentionBase, CanonicalMeasure, CanonicalTerritory, CanonicalTimeExpression
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

class AuthorityMatrix:
    """
    Applique les règles de résolution par sous-champ.
    """
    @staticmethod
    def fuse_measure(b: Optional[CanonicalMeasure], l: Optional[CanonicalMeasure]) -> Dict[str, Any]:
        """Règles spécifiques aux mesures (valeur numérique déterministe)."""
        if not b and not l:
            return {"decision": DecisionType.REJECTED, "explanation": ExplanationCode.FORBIDDEN_LLM_INFERENCE, "result": None}
            
        if not b and l:
            # LLM only (doit être post-validé)
            if l.validation_status in ["ACCEPTED", "ACCEPTED_WITH_WARNINGS"]:
                merged_l = CanonicalMeasure(**l.dict())
                merged_l.origin = "FUSION"
                return {"decision": DecisionType.LLM_SELECTED, "explanation": ExplanationCode.LLM_POST_VALIDATED_ONLY, "result": merged_l}
            return {"decision": DecisionType.REJECTED, "explanation": ExplanationCode.FORBIDDEN_LLM_INFERENCE, "result": None}
            
        if b and not l:
            merged_b = CanonicalMeasure(**b.dict())
            merged_b.origin = "FUSION"
            return {"decision": DecisionType.BASELINE_SELECTED, "explanation": ExplanationCode.BASELINE_VALID_ONLY, "result": merged_b}
            
        # b et l sont présents (ils ont été alignés)
        merged = CanonicalMeasure(**b.dict())
        merged.origin = "FUSION"
        
        # 1. Accord exact
        if b.value == l.value and b.unit == l.unit and b.role == l.role:
            return {"decision": DecisionType.AGREEMENT, "explanation": ExplanationCode.EXACT_AGREEMENT, "result": merged}
            
        # 2. Même span, mais valeur différente -> L'extracteur déterministe (Baseline) l'emporte sur l'IA
        if b.offsets == l.offsets and b.value != l.value:
            return {"decision": DecisionType.DETERMINISTIC_VALIDATOR_SELECTED, "explanation": ExplanationCode.NUMERIC_VALIDATOR_AUTHORITY, "result": merged}
            
        # 3. Conflit de rôle
        if b.role != l.role:
            return {"decision": DecisionType.BOTH_RETAINED_AS_ALTERNATIVES, "explanation": ExplanationCode.UNRESOLVED_ROLE_CONFLICT, "result": merged}
            
        # Par défaut, on favorise la logique déterministe
        return {"decision": DecisionType.BASELINE_SELECTED, "explanation": ExplanationCode.NUMERIC_VALIDATOR_AUTHORITY, "result": merged}

    @staticmethod
    def fuse_territory(b: Optional[CanonicalTerritory], l: Optional[CanonicalTerritory]) -> Dict[str, Any]:
        """Règles spécifiques aux territoires (COG)."""
        if not b and not l:
            return {"decision": DecisionType.REJECTED, "explanation": ExplanationCode.FORBIDDEN_LLM_INFERENCE, "result": None}
            
        # Si seul le LLM a trouvé, on accepte uniquement s'il est validé (ce qui implique que le code existe dans le COG)
        if not b and l:
            if l.validation_status in ["ACCEPTED", "ACCEPTED_WITH_WARNINGS"] and l.code:
                merged_l = CanonicalTerritory(**l.dict())
                merged_l.origin = "FUSION"
                return {"decision": DecisionType.LLM_SELECTED, "explanation": ExplanationCode.LLM_POST_VALIDATED_ONLY, "result": merged_l}
            return {"decision": DecisionType.REJECTED, "explanation": ExplanationCode.FORBIDDEN_LLM_INFERENCE, "result": None}
            
        if b and not l:
            merged_b = CanonicalTerritory(**b.dict())
            merged_b.origin = "FUSION"
            return {"decision": DecisionType.BASELINE_SELECTED, "explanation": ExplanationCode.BASELINE_VALID_ONLY, "result": merged_b}
            
        merged = CanonicalTerritory(**b.dict())
        merged.origin = "FUSION"
        
        # Conflit de codes validés (ex: ambigüité non résolue par le COG)
        if b.code != l.code:
            return {"decision": DecisionType.BOTH_RETAINED_AS_ALTERNATIVES, "explanation": ExplanationCode.AMBIGUOUS_GEOGRAPHY, "result": merged}
            
        return {"decision": DecisionType.AGREEMENT, "explanation": ExplanationCode.EXACT_AGREEMENT, "result": merged}
