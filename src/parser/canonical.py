from pydantic import BaseModel, Field
from typing import List, Optional, Any, Tuple
from enum import Enum

class SourceScope(str, Enum):
    CLAIM = "CLAIM"
    CONTEXT_BEFORE = "CONTEXT_BEFORE"
    CONTEXT_AFTER = "CONTEXT_AFTER"

class CanonicalMentionBase(BaseModel):
    source_text: str
    offsets: Optional[Tuple[int, int]] = None
    source_scope: SourceScope = SourceScope.CLAIM
    origin: str  # 'BASELINE', 'LLM', or 'FUSION'
    method: Optional[str] = None
    validation_status: str = "PENDING"

class CanonicalMeasure(CanonicalMentionBase):
    value: Optional[float] = None
    unit: Optional[str] = None
    scale: Optional[str] = None
    role: Optional[str] = None

class CanonicalTimeExpression(CanonicalMentionBase):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    granularity: Optional[str] = None
    is_relative: bool = False

class CanonicalTerritory(CanonicalMentionBase):
    code: Optional[str] = None
    territory_type: Optional[str] = None
    vintage: Optional[str] = None

class CanonicalIndicator(CanonicalMentionBase):
    normalized_label: Optional[str] = None
    
class CanonicalPopulation(CanonicalMentionBase):
    normalized_label: Optional[str] = None

class CanonicalParseResult(BaseModel):
    indicators: List[CanonicalIndicator] = Field(default_factory=list)
    populations: List[CanonicalPopulation] = Field(default_factory=list)
    territories: List[CanonicalTerritory] = Field(default_factory=list)
    measures: List[CanonicalMeasure] = Field(default_factory=list)
    time_expressions: List[CanonicalTimeExpression] = Field(default_factory=list)
    operation: List[CanonicalMentionBase] = Field(default_factory=list)
    frequency: List[CanonicalMentionBase] = Field(default_factory=list)
    adjustment: List[CanonicalMentionBase] = Field(default_factory=list)
    ambiguities: List[CanonicalMentionBase] = Field(default_factory=list)
    missing_context: List[CanonicalMentionBase] = Field(default_factory=list)
    parse_status: str = "ACCEPTED"  # ACCEPTED, ACCEPTED_WITH_WARNINGS, AMBIGUOUS, REJECTED
