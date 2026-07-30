from enum import Enum
from typing import List, Union
from pydantic import BaseModel, ConfigDict

from .entities import IndicatorModel, PopulationModel, TerritoryModel
from .measures import MeasureModel
from .temporal import TimeExpressionModel
from .operations import OperationModel, FrequencyModel, AdjustmentModel
from .meta_schemas import AmbiguityModel, MissingContextModel

class ParseStatus(str, Enum):
    COMPLETE = "COMPLETE"
    PARTIAL = "PARTIAL"
    AMBIGUOUS = "AMBIGUOUS"
    UNSUPPORTED = "UNSUPPORTED"

class ClaimParseResult(BaseModel):
    model_config = ConfigDict(extra="forbid")
    schema_version: str
    parse_status: ParseStatus
    indicators: List[IndicatorModel]
    populations: List[PopulationModel]
    territories: List[TerritoryModel]
    time_expressions: List[TimeExpressionModel]
    measures: List[MeasureModel]
    operation: Union[OperationModel, None]
    frequency: Union[FrequencyModel, None]
    adjustment: Union[AdjustmentModel, None]
    comparisons: List[OperationModel]
    ambiguities: List[AmbiguityModel]
    missing_context: List[MissingContextModel]
