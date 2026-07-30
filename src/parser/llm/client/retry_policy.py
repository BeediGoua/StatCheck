import time
import logging
from typing import Type, TypeVar, Any
from pydantic import BaseModel, ValidationError
import openai
from instructor.exceptions import InstructorRetryException

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class RefusalError(Exception):
    """Exception levée lorsque le LLM refuse de traiter la requête."""
    pass

class SchemaValidationError(Exception):
    """Exception levée lorsque le LLM ne respecte pas le schéma Pydantic."""
    pass

class IncompleteResponseError(Exception):
    """Exception levée lorsque le LLM s'arrête avant la fin (limite de tokens)."""
    pass

def call_llm_with_retry(
    client: Any,
    model: str,
    messages: list[dict],
    response_model: Type[T],
    max_retries: int = 3,
    initial_max_tokens: int = 2000
) -> tuple[T, Any]:
    """
    Appelle le LLM avec une politique de retry spécialisée.
    Retourne un tuple (objet_pydantic, reponse_brute_openai) pour lire les tokens.
    """
    attempt = 0
    current_max_tokens = initial_max_tokens

    while attempt < max_retries:
        attempt += 1
        try:
            # Appel API via Instructor
            response, raw = client.chat.completions.create_with_completion(
                model=model,
                messages=messages,
                response_model=response_model,
                max_tokens=current_max_tokens,
                max_retries=0, # Désactive le retry interne
            )
            return response, raw
            
        except IncompleteResponseError as e:
            logger.warning(f"Réponse incomplète (budget {current_max_tokens} tokens). Augmentation du budget.")
            current_max_tokens += 1000
            if attempt == max_retries:
                raise Exception("Réponse toujours incomplète après plusieurs tentatives.") from e
            continue
            
        except (openai.InternalServerError, openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError) as e:
            logger.warning(f"Erreur d'infrastructure API ({type(e).__name__}). Tentative {attempt}/{max_retries}.")
            if attempt == max_retries:
                raise e
            time.sleep(2 ** attempt) # Backoff exponentiel
            
        except openai.BadRequestError as e:
            logger.error("Requête invalide ou refusée par le modèle.")
            raise RefusalError("Le modèle a refusé de répondre.") from e
            
        except InstructorRetryException as e:
            # Instructor wrap l'erreur de validation.
            # Vérifions si c'est parce que la réponse était coupée.
            completion = getattr(e, "last_completion", None)
            if completion and hasattr(completion, "choices") and completion.choices:
                if completion.choices[0].finish_reason == "length":
                    # On relance la boucle principale en augmentant les tokens
                    logger.warning(f"Réponse incomplète (interceptée via Instructor). Augmentation du budget.")
                    current_max_tokens += 1000
                    if attempt == max_retries:
                        raise Exception("Réponse toujours incomplète après retries.")
                    continue
            
            logger.error("Erreur de schéma : le modèle n'a pas respecté le contrat Pydantic.")
            raise SchemaValidationError("Échec de la validation du schéma.") from e
            
        except ValidationError as e:
            logger.error("Erreur de schéma : le modèle n'a pas respecté le contrat Pydantic.")
            raise SchemaValidationError("Échec de la validation du schéma.") from e

    raise Exception("Nombre maximum de tentatives atteint.")
