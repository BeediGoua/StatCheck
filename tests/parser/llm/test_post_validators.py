import pytest
from src.parser.llm.validators.orchestrator import apply_all_validators

def test_provenance_rejects_hallucinated_span():
    """Niveau 1: Rejette une entité si source_text n'est pas dans le texte brut."""
    claim_text = "Le chômage a baissé."
    
    parsed_dict = {
        "indicators": [
            {
                "source_text": "inflation", # N'est pas dans le texte
                "occurrence": 1,
                "normalized_label": "Inflation",
                "source_scope": "CLAIM",
                "certainty": "EXPLICIT"
            }
        ]
    }
    
    validated = apply_all_validators(claim_text, parsed_dict)
    # L'indicateur doit être supprimé car introuvable
    assert len(validated["indicators"]) == 0

def test_numeric_corrects_hallucinated_math():
    """Niveau 2: Corrige la valeur si le LLM s'est trompé dans la conversion."""
    claim_text = "Une hausse de 3,5 points."
    
    parsed_dict = {
        "measures": [
            {
                "source_text": "3,5 points",
                "occurrence": 1,
                "numeric_value": 35.0, # Hallucination (35 au lieu de 3.5)
                "unit": "PERCENTAGE_POINT",
                "scale": "NONE",
                "role": "ABSOLUTE_CHANGE"
            }
        ]
    }
    
    validated = apply_all_validators(claim_text, parsed_dict)
    # Le validateur doit corriger via la baseline
    assert validated["measures"][0]["numeric_value"] == 3.5

def test_geography_rejects_invented_cog():
    """Niveau 4: Rejette un territoire déduit avec un code COG non mentionné."""
    claim_text = "Le maire de Paris a parlé."
    
    parsed_dict = {
        "territories": [
            {
                "source_text": "Paris",
                "occurrence": 1,
                "normalized_label": "75056", # Le LLM a inventé le code COG
                "source_scope": "CLAIM",
                "certainty": "EXPLICIT"
            }
        ]
    }
    
    validated = apply_all_validators(claim_text, parsed_dict)
    # Le territoire doit être rejeté car "75056" est un code pur
    assert len(validated["territories"]) == 0

def test_inference_rejects_unproven_territory():
    """Niveau 8: Rejette un territoire implicite sans texte source."""
    claim_text = "Le chômage augmente."
    
    parsed_dict = {
        "territories": [
            {
                "source_text": "", # Aucune preuve
                "occurrence": 1,
                "normalized_label": "France",
                "source_scope": "CLAIM",
                "certainty": "IMPLICIT"
            }
        ]
    }
    
    validated = apply_all_validators(claim_text, parsed_dict)
    assert len(validated["territories"]) == 0
