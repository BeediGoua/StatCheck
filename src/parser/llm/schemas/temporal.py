from enum import Enum
from typing import Union
from pydantic import BaseModel, ConfigDict
from .entities import SourceScope, Certainty

class TemporalType(str, Enum):
    POINT = "POINT"
    INTERVAL = "INTERVAL"
    RELATIVE_POINT = "RELATIVE_POINT"
    RELATIVE_INTERVAL = "RELATIVE_INTERVAL"
    DURATION = "DURATION"
    COMPARISON_PERIOD = "COMPARISON_PERIOD"
    UNKNOWN = "UNKNOWN"

class Granularity(str, Enum):
    DAY = "DAY"
    WEEK = "WEEK"
    MONTH = "MONTH"
    QUARTER = "QUARTER"
    SEMESTER = "SEMESTER"
    YEAR = "YEAR"
    MULTI_YEAR = "MULTI_YEAR"
    UNKNOWN = "UNKNOWN"

class TimeExpressionModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_text: str
    occurrence: int
    temporal_type: TemporalType
    granularity: Granularity
    is_relative: bool
    normalized_start: Union[str, None]
    normalized_end: Union[str, None]
    reference_date_used: Union[str, None]
    source_scope: SourceScope
    certainty: Certainty
