from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, List, Union
from enum import Enum
import datetime

class LLMInputEnvelope(BaseModel):
    """
    Données d'entrée nécessaires au LLM pour parser une affirmation.
    """
    model_config = ConfigDict(extra="forbid")
    claim_id: str
    claim_text: str
    publication_date: Union[str, None] = None
    context_before: Union[str, None] = None
    context_after: Union[str, None] = None
    language: str = "fr"
    baseline_candidates: Union[Dict[str, Any], None] = None

class ValidationStatus(str, Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    API_ERROR = "API_ERROR"
    REFUSED = "REFUSED"

class LLMMetrics(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tokens_prompt: int
    tokens_completion: int
    time_ms: int
    cost: float = 0.0

class LLMValidatedResponse(BaseModel):
    """
    Enveloppe de sortie finale de l'orchestrateur.
    """
    model_config = ConfigDict(extra="forbid")
    raw_parsed_data: Union[Dict[str, Any], None]
    validated_data: Union[Dict[str, Any], None]
    status: ValidationStatus
    validation_logs: List[str]
    metrics: LLMMetrics
