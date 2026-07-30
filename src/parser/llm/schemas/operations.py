from enum import Enum
from typing import Union
from pydantic import BaseModel, ConfigDict
from .entities import Certainty

class OperationType(str, Enum):
    VALUE = "VALUE"
    THRESHOLD_COMPARISON = "THRESHOLD_COMPARISON"
    ABSOLUTE_CHANGE = "ABSOLUTE_CHANGE"
    RELATIVE_CHANGE = "RELATIVE_CHANGE"
    PERCENTAGE_POINT_CHANGE = "PERCENTAGE_POINT_CHANGE"
    RATIO = "RATIO"
    SHARE = "SHARE"
    COUNT = "COUNT"
    SUM = "SUM"
    AVERAGE = "AVERAGE"
    RANK = "RANK"
    MINIMUM = "MINIMUM"
    MAXIMUM = "MAXIMUM"
    TREND = "TREND"
    CROSS_TIME_COMPARISON = "CROSS_TIME_COMPARISON"
    CROSS_GEO_COMPARISON = "CROSS_GEO_COMPARISON"
    CROSS_POPULATION_COMPARISON = "CROSS_POPULATION_COMPARISON"
    UNKNOWN = "UNKNOWN"

class Direction(str, Enum):
    INCREASE = "INCREASE"
    DECREASE = "DECREASE"
    STABLE = "STABLE"
    ABOVE = "ABOVE"
    BELOW = "BELOW"
    EQUAL = "EQUAL"
    HIGHEST = "HIGHEST"
    LOWEST = "LOWEST"
    NONE = "NONE"
    UNKNOWN = "UNKNOWN"

class Polarity(str, Enum):
    AFFIRMED = "AFFIRMED"
    NEGATED = "NEGATED"
    UNCERTAIN = "UNCERTAIN"

class Comparator(str, Enum):
    GREATER_THAN = "GREATER_THAN"
    GREATER_OR_EQUAL = "GREATER_OR_EQUAL"
    LESS_THAN = "LESS_THAN"
    LESS_OR_EQUAL = "LESS_OR_EQUAL"
    EQUAL = "EQUAL"
    NOT_EQUAL = "NOT_EQUAL"
    NONE = "NONE"

class FrequencyEnum(str, Enum):
    DAILY = "DAILY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"
    QUARTERLY = "QUARTERLY"
    SEMESTER = "SEMESTER"
    ANNUAL = "ANNUAL"
    ROLLING_YEAR = "ROLLING_YEAR"
    YEAR_ON_YEAR = "YEAR_ON_YEAR"
    UNKNOWN = "UNKNOWN"

class AdjustmentEnum(str, Enum):
    RAW = "RAW"
    SEASONALLY_ADJUSTED = "SEASONALLY_ADJUSTED"
    SEASONALLY_AND_WORKING_DAY_ADJUSTED = "SEASONALLY_AND_WORKING_DAY_ADJUSTED"
    CURRENT_PRICES = "CURRENT_PRICES"
    CONSTANT_PRICES = "CONSTANT_PRICES"
    CHAINED_VOLUME = "CHAINED_VOLUME"
    UNKNOWN = "UNKNOWN"

class OperationModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    type: OperationType
    direction: Direction
    polarity: Polarity
    comparator: Comparator
    is_explicit: bool
    trigger_text: Union[str, None]
    trigger_occurrence: Union[int, None]

class FrequencyModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_text: str
    occurrence: int
    value: FrequencyEnum
    certainty: Certainty

class AdjustmentModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
    value: AdjustmentEnum
