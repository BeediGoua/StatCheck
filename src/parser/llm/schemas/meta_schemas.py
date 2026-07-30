from enum import Enum
from typing import List
from pydantic import BaseModel, ConfigDict

class MissingContextType(str, Enum):
    PUBLICATION_DATE = "PUBLICATION_DATE"
    GEOGRAPHY = "GEOGRAPHY"
    REFERENCE_PERIOD = "REFERENCE_PERIOD"
    COMPARISON_TARGET = "COMPARISON_TARGET"
    INDICATOR_DEFINITION = "INDICATOR_DEFINITION"
    POPULATION_DEFINITION = "POPULATION_DEFINITION"
    UNIT = "UNIT"
    DENOMINATOR = "DENOMINATOR"
    OTHER = "OTHER"

class AmbiguityModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    field: str
    source_text: str
    reason: str
    alternatives: List[str]
    requires_human_validation: bool

class MissingContextModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: MissingContextType
    reason: str
