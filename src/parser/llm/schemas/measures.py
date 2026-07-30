from enum import Enum
from typing import Union
from pydantic import BaseModel, ConfigDict
from .entities import SourceScope

class Unit(str, Enum):
    PERCENT = "PERCENT"
    PERCENTAGE_POINT = "PERCENTAGE_POINT"
    COUNT = "COUNT"
    EURO = "EURO"
    INDEX_POINT = "INDEX_POINT"
    RATIO = "RATIO"
    RANK = "RANK"
    DURATION = "DURATION"
    UNKNOWN = "UNKNOWN"

class Scale(str, Enum):
    UNIT = "UNIT"
    THOUSAND = "THOUSAND"
    MILLION = "MILLION"
    BILLION = "BILLION"
    TRILLION = "TRILLION"
    NONE = "NONE"

class Role(str, Enum):
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

class Approximation(str, Enum):
    EXACT = "EXACT"
    APPROXIMATELY = "APPROXIMATELY"
    AT_LEAST = "AT_LEAST"
    AT_MOST = "AT_MOST"
    MORE_THAN = "MORE_THAN"
    LESS_THAN = "LESS_THAN"
    BETWEEN = "BETWEEN"

class MeasureModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_text: str
    occurrence: int
    numeric_value: Union[float, None]
    lower_bound: Union[float, None]
    upper_bound: Union[float, None]
    unit: Unit
    scale: Scale
    role: Role
    approximation: Approximation
    sign: Union[str, None]
    source_scope: SourceScope
