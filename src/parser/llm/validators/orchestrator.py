from typing import Dict, Any

from src.parser.llm.validators.provenance import validate_provenance
from src.parser.llm.validators.numeric import validate_numeric_values
from src.parser.llm.validators.temporal import validate_temporal_values
from src.parser.llm.validators.geography import validate_geography
from src.parser.llm.validators.coherence import validate_coherence
from src.parser.llm.validators.inference_dedup import validate_inference_and_deduplication

def apply_all_validators(claim_text: str, parsed_dict: Dict[str, Any], reference_date: str = None) -> Dict[str, Any]:
    """
    Orchestre le passage du dictionnaire Pydantic (issu du LLM) 
    à travers les 8 niveaux de post-validation déterministe.
    Modifie le dictionnaire en place.
    """
    
    # Niveau 1 : Provenance et calcul des offsets
    validate_provenance(claim_text, parsed_dict)
    
    # Niveau 2 : Valeurs Numériques (anti-hallucinations mathématiques)
    validate_numeric_values(parsed_dict)
    
    # Niveau 3 : Temporalité (vérification avec extracteur baseline)
    validate_temporal_values(parsed_dict, reference_date)
    
    # Niveau 4 : Géographie (rejet de codes inventés)
    validate_geography(parsed_dict)
    
    # Niveaux 5 & 6 : Cohérences Mathématiques et Opérationnelles
    validate_coherence(parsed_dict)
    
    # Niveaux 7 & 8 : Déduplication et Inférence
    validate_inference_and_deduplication(parsed_dict)
    
    return parsed_dict
