"""Micro-Gold V0 schema + loader (Session 4)."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


MICRO_GOLD_V0_PATH = (
    Path(__file__).resolve().parents[2]
    / "data"
    / "gold"
    / "micro_gold_v0"
    / "micro_gold_v0.yaml"
)

EXPECTED_CLAIM_IDS = tuple(f"MG{i:03d}" for i in range(1, 13))

FROZEN_CLAIMS: Dict[str, str] = {
    "MG001": (
        "Au deuxième trimestre 2025, le taux de chômage au sens du BIT "
        "en France hors Mayotte était de 7,5 %."
    ),
    "MG002": (
        "Entre le deuxième trimestre 2024 et le deuxième trimestre 2025, "
        "le taux de chômage au sens du BIT en France hors Mayotte a augmenté de 0,2 point."
    ),
    "MG003": (
        "Entre le deuxième trimestre 2024 et le deuxième trimestre 2025, "
        "le taux de chômage au sens du BIT en France hors Mayotte a augmenté de 2,7 %."
    ),
    "MG004": (
        "Au deuxième trimestre 2025, le chômage des jeunes en France était de 19 %."
    ),
    "MG005": (
        "Au deuxième trimestre 2025, 3,3 millions de chômeurs au sens du BIT "
        "étaient inscrits en catégorie A à France Travail."
    ),
    "MG006": (
        "En septembre 2025, les prix à la consommation en France entière "
        "ont augmenté de 1,2 % sur un an."
    ),
    "MG007": (
        "En septembre 2025, les prix à la consommation en France entière "
        "ont baissé de 1,0 % par rapport à août 2025."
    ),
    "MG008": "En septembre 2025, l’inflation en France était de 1,0 %.",
    "MG009": (
        "Au 1er janvier 2025, la France comptait environ 68,6 millions d’habitants."
    ),
    "MG010": "En 2025, 643 905 bébés sont nés en France.",
    "MG011": (
        "En 2025, la population française a augmenté de 643 905 personnes "
        "grâce aux naissances."
    ),
    "MG012": "En 2025, 1 165 800 entreprises ont été créées en France.",
}


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class AnswerabilityStatus(str, Enum):
    FOUND = "FOUND"
    AMBIGUOUS = "AMBIGUOUS"
    NOT_FOUND = "NOT_FOUND"
    INSUFFICIENT = "INSUFFICIENT"


class ExpectedVerdict(str, Enum):
    SUPPORTED = "SUPPORTED"
    REFUTED = "REFUTED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"


class GoldStatus(str, Enum):
    CANDIDATE = "CANDIDATE"


class ReviewStatus(str, Enum):
    DRAFT = "DRAFT"
    SOURCE_CHECKED = "SOURCE_CHECKED"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"


class VerificationStatus(str, Enum):
    """Session 4.1 series-grounding check."""

    CONFIRMED = "CONFIRMED"
    CORRECTED = "CORRECTED"
    NEEDS_HUMAN_REVIEW = "NEEDS_HUMAN_REVIEW"
    UNRESOLVED = "UNRESOLVED"


class ComputationOperation(str, Enum):
    VALUE = "VALUE"
    POINT_CHANGE = "POINT_CHANGE"
    RELATIVE_CHANGE = "RELATIVE_CHANGE"
    RATIO = "RATIO"
    SUM = "SUM"
    NONE = "NONE"


class Answerability(StrictModel):
    status: AnswerabilityStatus
    reason: str


class ClaimSpecSubtree(StrictModel):
    """Expected ClaimSpecification-like slots (oracle, not runtime Spec dump)."""

    indicator: Optional[Dict[str, Any]] = None
    populations: List[Dict[str, Any]] = Field(default_factory=list)
    territories: List[Dict[str, Any]] = Field(default_factory=list)
    time_period: Optional[Dict[str, Any]] = None
    claimed_quantity: Optional[Dict[str, Any]] = None
    statistical_operation: Optional[Dict[str, Any]] = None
    expressed_frequency: Optional[Dict[str, Any]] = None
    adjustment: Optional[Dict[str, Any]] = None


class ExpectedGrounding(StrictModel):
    provider: Optional[str] = None
    dataset_id: Optional[str] = None
    dataset_title: Optional[str] = None
    series_id: Optional[str] = None
    idbank: Optional[str] = None
    series_key: Optional[str] = None


class ObservationRow(StrictModel):
    period: str
    value: float
    unit: Optional[str] = None
    note: Optional[str] = None


class ExpectedComputation(StrictModel):
    operation: ComputationOperation
    result: Optional[float] = None
    unit: Optional[str] = None
    start_period: Optional[str] = None
    end_period: Optional[str] = None
    period: Optional[str] = None
    formula_note: Optional[str] = None


class AmbiguityItem(StrictModel):
    field: str
    reason: str
    alternatives: List[Any] = Field(default_factory=list)


class Provenance(StrictModel):
    sources: List[str] = Field(default_factory=list)
    as_of_date: Optional[str] = None
    revision_note: Optional[str] = None
    snapshot_kind: Optional[str] = Field(
        None,
        description="publication_snapshot | revised_series | mixed",
    )
    data_version: Optional[str] = Field(
        None, description="BDM LAST_UPDATE or publication version label"
    )
    observed_at: Optional[str] = Field(
        None, description="ISO date when Series/BDM values were inspected"
    )
    publication_value: Optional[str] = Field(
        None, description="Value as published at as_of_date (MG001–MG003)"
    )
    revised_series_value: Optional[str] = Field(
        None, description="Later revised series value if different"
    )
    discrepancy_cause: Optional[str] = Field(
        None,
        description="Cause of publication vs live BDM gap (UNKNOWN or documented)",
    )
    replaced_idbank: Optional[str] = Field(
        None, description="Stopped predecessor idbank when a successor is pinned"
    )


class AnnotationMeta(StrictModel):
    source_checked: bool = False
    review_status: ReviewStatus = ReviewStatus.DRAFT
    verification_status: Optional[VerificationStatus] = None
    verification_notes: Optional[str] = None
    notes: Optional[str] = None
    rejected_candidates: List[str] = Field(default_factory=list)


class MicroGoldCase(StrictModel):
    claim_id: str
    claim: str
    family: str
    gold_status: GoldStatus = GoldStatus.CANDIDATE
    answerability: Answerability
    claim_specification: ClaimSpecSubtree
    expected_grounding: ExpectedGrounding = Field(default_factory=ExpectedGrounding)
    expected_dimensions: Dict[str, Optional[str]] = Field(default_factory=dict)
    expected_observations: List[ObservationRow] = Field(default_factory=list)
    expected_computation: ExpectedComputation
    expected_verdict: Optional[ExpectedVerdict] = None
    ambiguities: List[AmbiguityItem] = Field(default_factory=list)
    provenance: Provenance = Field(default_factory=Provenance)
    annotation: AnnotationMeta = Field(default_factory=AnnotationMeta)

    @model_validator(mode="after")
    def _enforce_status_rules(self) -> "MicroGoldCase":
        if self.gold_status != GoldStatus.CANDIDATE:
            raise ValueError("Session 4 allows only gold_status=CANDIDATE")

        st = self.answerability.status
        if st == AnswerabilityStatus.FOUND:
            g = self.expected_grounding
            if not g.dataset_id:
                raise ValueError(f"{self.claim_id}: FOUND requires dataset_id")
            if not (g.idbank or g.series_id):
                raise ValueError(f"{self.claim_id}: FOUND requires idbank or series_id")
            if not self.expected_observations:
                raise ValueError(f"{self.claim_id}: FOUND requires observations")
            if self.expected_computation.operation == ComputationOperation.NONE:
                raise ValueError(f"{self.claim_id}: FOUND forbids operation NONE")
            if self.expected_computation.result is None:
                raise ValueError(f"{self.claim_id}: FOUND requires computation.result")
            if self.expected_verdict not in (
                ExpectedVerdict.SUPPORTED,
                ExpectedVerdict.REFUTED,
            ):
                raise ValueError(
                    f"{self.claim_id}: FOUND requires SUPPORTED or REFUTED verdict"
                )
            vs = self.annotation.verification_status
            if vs in (
                VerificationStatus.CONFIRMED,
                VerificationStatus.CORRECTED,
            ) and not g.idbank:
                raise ValueError(
                    f"{self.claim_id}: CONFIRMED/CORRECTED FOUND requires idbank"
                )
        else:
            if not self.ambiguities and not (self.answerability.reason or "").strip():
                raise ValueError(
                    f"{self.claim_id}: non-FOUND requires ambiguities or reason"
                )
            if st in (
                AnswerabilityStatus.AMBIGUOUS,
                AnswerabilityStatus.INSUFFICIENT,
            ) and not self.ambiguities:
                raise ValueError(
                    f"{self.claim_id}: {st.value} requires non-empty ambiguities"
                )
        return self


def load_micro_gold_v0(
    path: Optional[Path] = None,
) -> List[MicroGoldCase]:
    target = path or MICRO_GOLD_V0_PATH
    raw = yaml.safe_load(target.read_text(encoding="utf-8"))
    if not isinstance(raw, list):
        raise ValueError("micro_gold_v0.yaml must be a YAML list of cases")
    return [MicroGoldCase.model_validate(item) for item in raw]
