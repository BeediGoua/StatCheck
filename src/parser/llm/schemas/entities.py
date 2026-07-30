from enum import Enum
from typing import List
from pydantic import BaseModel, ConfigDict

class SourceScope(str, Enum):
    CLAIM = "CLAIM"
    CONTEXT_BEFORE = "CONTEXT_BEFORE"
    CONTEXT_AFTER = "CONTEXT_AFTER"

class Certainty(str, Enum):
    EXPLICIT = "EXPLICIT"
    IMPLICIT = "IMPLICIT"
    AMBIGUOUS = "AMBIGUOUS"

class TerritoryHint(str, Enum):
    COUNTRY = "COUNTRY"
    REGION = "REGION"
    DEPARTMENT = "DEPARTMENT"
    COMMUNE = "COMMUNE"
    SUPRANATIONAL = "SUPRANATIONAL"
    UNKNOWN = "UNKNOWN"

class TextMentionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_text: str
    occurrence: int
    normalized_label: str
    source_scope: SourceScope
    certainty: Certainty

class IndicatorModel(TextMentionModel):
    pass

class PopulationModel(TextMentionModel):
    qualifiers: List[str]

class TerritoryModel(TextMentionModel):
    territory_hint: TerritoryHint
