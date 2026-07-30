import time
import logging
from typing import Dict, Any

from src.parser.llm.client.openai_client import get_llm_client
from src.parser.llm.client.retry_policy import (
    call_llm_with_retry, 
    RefusalError, 
    SchemaValidationError
)
from src.parser.llm.prompts.system_prompt import SYSTEM_PROMPT
from src.parser.llm.schemas.claim_parse import ClaimParseResult
from src.parser.llm.schemas.envelope import (
    LLMInputEnvelope, 
    LLMValidatedResponse, 
    ValidationStatus, 
    LLMMetrics
)
from src.parser.llm.validators.orchestrator import apply_all_validators

logger = logging.getLogger(__name__)

class StatCheckLLMParser:
    """
    Orchestrateur principal du parseur LLM.
    Assemble le Client, le Prompt, le Schéma et les Post-Validateurs.
    """
    
    def __init__(self, model_name: str = "qwen2.5:latest"):
        self.model_name = model_name
        self.client = get_llm_client()
        
    def _build_user_message(self, envelope: LLMInputEnvelope) -> str:
        msg = f"Affirmation à parser :\n{envelope.claim_text}\n"
        
        if envelope.publication_date:
            msg += f"\nDate de publication : {envelope.publication_date}"
        
        if envelope.context_before:
            msg += f"\nContexte précédent :\n{envelope.context_before}"
            
        if envelope.context_after:
            msg += f"\nContexte suivant :\n{envelope.context_after}"
            
        if envelope.baseline_candidates:
            import json
            msg += f"\n\n--- INDICE (Optionnel) ---\n"
            msg += "Voici ce qu'un analyseur basique a extrait. Sers-t'en pour t'aider, mais RESTE CRITIQUE si ces données te semblent fausses ou incomplètes :\n"
            msg += json.dumps(envelope.baseline_candidates, ensure_ascii=False, indent=2)
            
        return msg

    def parse_claim(self, envelope: LLMInputEnvelope) -> LLMValidatedResponse:
        start_time = time.time()
        
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": self._build_user_message(envelope)}
        ]
        
        raw_dict = None
        validated_dict = None
        logs = []
        status = ValidationStatus.ACCEPTED
        
        raw_api_response = None
        
        try:
            # 1. Appel API via la retry_policy stricte
            parsed_model, raw_api_response = call_llm_with_retry(
                client=self.client,
                model=self.model_name,
                messages=messages,
                response_model=ClaimParseResult
            )
            
            # 2. Sauvegarde de la version brute
            raw_dict = parsed_model.model_dump()
            
            # On fait une copie profonde pour la validation
            import copy
            validated_dict = copy.deepcopy(raw_dict)
            
            # 3. Post-validation déterministe
            try:
                validated_dict = apply_all_validators(
                    claim_text=envelope.claim_text,
                    parsed_dict=validated_dict,
                    reference_date=envelope.publication_date
                )
            except Exception as e:
                logs.append(f"Erreur critique lors de la post-validation: {str(e)}")
                status = ValidationStatus.REJECTED
                
        except RefusalError as e:
            logs.append(f"Le LLM a refusé ou la requête est invalide: {str(e)}")
            status = ValidationStatus.REFUSED
            
        except SchemaValidationError as e:
            logs.append(f"Erreur de contrat Pydantic: {str(e)}")
            status = ValidationStatus.REJECTED
            
        except Exception as e:
            logs.append(f"Erreur API inattendue: {str(e)}")
            status = ValidationStatus.API_ERROR
            
        end_time = time.time()
        
        # Extraction des métriques
        prompt_tokens = 0
        completion_tokens = 0
        
        if raw_api_response and hasattr(raw_api_response, "usage") and raw_api_response.usage:
            prompt_tokens = raw_api_response.usage.prompt_tokens or 0
            completion_tokens = raw_api_response.usage.completion_tokens or 0
            
        metrics = LLMMetrics(
            tokens_prompt=prompt_tokens, 
            tokens_completion=completion_tokens, 
            time_ms=int((end_time - start_time) * 1000),
            cost=0.0 # Peut être calculé selon model_name
        )
        
        return LLMValidatedResponse(
            raw_parsed_data=raw_dict,
            validated_data=validated_dict,
            status=status,
            validation_logs=logs,
            metrics=metrics
        )
