"""ClaimSpecification V1 — single claim contract (see docs/contracts/claim_specification_v1.md)."""
from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional, Tuple

from pydantic import BaseModel, Field


class ExtractionProvenance(str, Enum):
    EXPLICIT_TEXT = "EXPLICIT_TEXT"
    IMPLICIT_CONTEXT = "IMPLICIT_CONTEXT"
    INFERRED = "INFERRED"
    DEFAULTED = "DEFAULTED"


class PresenceStatus(str, Enum):
    EXPLICIT = "EXPLICIT"
    IMPLICIT = "IMPLICIT"
    MISSING = "MISSING"


class ConstraintType(str, Enum):
    HARD_CONSTRAINT = "HARD_CONSTRAINT"
    PREFERENCE = "PREFERENCE"
    UNCERTAIN_INFERENCE = "UNCERTAIN_INFERENCE"


class QuantityRole(str, Enum):
    CURRENT_VALUE = "CURRENT_VALUE"
    START_VALUE = "START_VALUE"
    END_VALUE = "END_VALUE"
    THRESHOLD = "THRESHOLD"
    CLAIMED_CHANGE = "CLAIMED_CHANGE"
    ABSOLUTE_CHANGE = "ABSOLUTE_CHANGE"
    RELATIVE_CHANGE = "RELATIVE_CHANGE"
    NUMERATOR = "NUMERATOR"
    DENOMINATOR = "DENOMINATOR"
    RATIO_VALUE = "RATIO_VALUE"
    RANK_VALUE = "RANK_VALUE"
    UNKNOWN = "UNKNOWN"


CLAIMED_QUANTITY_ROLES = {
    QuantityRole.CURRENT_VALUE,
    QuantityRole.CLAIMED_CHANGE,
    QuantityRole.RELATIVE_CHANGE,
    QuantityRole.ABSOLUTE_CHANGE,
}

REFERENCE_QUANTITY_ROLES = {
    QuantityRole.START_VALUE,
    QuantityRole.END_VALUE,
    QuantityRole.THRESHOLD,
    QuantityRole.NUMERATOR,
    QuantityRole.DENOMINATOR,
    QuantityRole.RATIO_VALUE,
    QuantityRole.RANK_VALUE,
}


class ClaimSlot(BaseModel):
    canonical_value: Optional[str] = Field(
        None, description="Normalized code or concept (e.g. UNEMPLOYMENT_RATE, FR)"
    )
    original_label: Optional[str] = Field(
        None, description="Surface form as it appeared in the claim text"
    )
    span_offsets: Optional[Tuple[int, int]] = Field(
        None, description="Character offsets (start, end) in original_text"
    )
    provenance: ExtractionProvenance = ExtractionProvenance.EXPLICIT_TEXT
    presence: PresenceStatus = PresenceStatus.EXPLICIT
    constraint_type: ConstraintType = ConstraintType.HARD_CONSTRAINT
    confidence: float = Field(1.0, ge=0.0, le=1.0)
    alternatives: List[Any] = Field(default_factory=list)


class ClaimTime(ClaimSlot):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    precision: Optional[str] = Field(None, description="YEAR | MONTH | QUARTER | …")
    is_relative: bool = False


class ClaimedQuantity(ClaimSlot):
    numeric_value: Optional[float] = None
    unit: Optional[str] = None
    role: QuantityRole = QuantityRole.UNKNOWN
    # Optional fusion/eval metadata (not observation data)
    validation_status: Optional[str] = Field(
        default="ACCEPTED",
        description="Local validation flag used by fusion authority rules",
    )


class Ambiguity(BaseModel):
    field: str
    reason: str
    alternatives: List[Any] = Field(default_factory=list)
    requires_human_validation: bool = True


class ClaimSpecification(BaseModel):
    """Unique claim representation after baseline/LLM adapters."""

    claim_id: str
    original_text: str

    indicator: Optional[ClaimSlot] = None
    populations: List[ClaimSlot] = Field(default_factory=list)
    territories: List[ClaimSlot] = Field(default_factory=list)
    time_period: Optional[ClaimTime] = None
    expressed_frequency: Optional[ClaimSlot] = None
    adjustment: Optional[ClaimSlot] = None
    expected_dimensions: List[ClaimSlot] = Field(default_factory=list)

    claimed_quantity: Optional[ClaimedQuantity] = None
    reference_quantities: List[ClaimedQuantity] = Field(default_factory=list)
    statistical_operation: Optional[ClaimSlot] = None
    comparison: Optional[ClaimSlot] = None

    parse_status: str = "ACCEPTED"
    ambiguities: List[Ambiguity] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)

    def quantity_list(self) -> List[ClaimedQuantity]:
        """Flatten claimed + reference quantities for alignment/scoring."""
        items: List[ClaimedQuantity] = []
        if self.claimed_quantity is not None:
            items.append(self.claimed_quantity)
        items.extend(self.reference_quantities)
        return items
