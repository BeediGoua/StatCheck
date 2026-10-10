"""Compatibility re-export of ClaimSpecification V1.

Prefer importing from ``src.parser.claim_specification`` in new code.
Legacy mention types (CanonicalIndicator, SourceScope, …) are intentionally absent.
"""
from src.parser.claim_specification import (
    Ambiguity,
    CLAIMED_QUANTITY_ROLES,
    ClaimSlot,
    ClaimSpecification,
    ClaimTime,
    ClaimedQuantity,
    ConstraintType,
    ExtractionProvenance,
    ParseStatus,
    PresenceStatus,
    QuantityApproximation,
    QuantityRole,
    QuantityScale,
    REFERENCE_QUANTITY_ROLES,
)

__all__ = [
    "Ambiguity",
    "CLAIMED_QUANTITY_ROLES",
    "ClaimSlot",
    "ClaimSpecification",
    "ClaimTime",
    "ClaimedQuantity",
    "ConstraintType",
    "ExtractionProvenance",
    "ParseStatus",
    "PresenceStatus",
    "QuantityApproximation",
    "QuantityRole",
    "QuantityScale",
    "REFERENCE_QUANTITY_ROLES",
]
