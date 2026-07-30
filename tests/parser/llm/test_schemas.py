import pytest
from pydantic import ValidationError
from src.parser.llm.schemas.claim_parse import ClaimParseResult

def test_schema_blocks_extra_properties():
    """Vérifie que le schéma Pydantic bloque les propriétés supplémentaires."""
    
    # JSON avec un champ inventé 'invented_field'
    invalid_data = {
        "schema_version": "1.0",
        "parse_status": "COMPLETE",
        "invented_field": "Ceci ne doit pas passer",
        "indicators": [],
        "populations": [],
        "territories": [],
        "time_expressions": [],
        "measures": [],
        "operation": None,
        "frequency": None,
        "adjustment": None,
        "comparisons": [],
        "ambiguities": [],
        "missing_context": []
    }
    
    with pytest.raises(ValidationError) as exc_info:
        ClaimParseResult(**invalid_data)
    
    assert "invented_field" in str(exc_info.value)
    assert "Extra inputs are not permitted" in str(exc_info.value)

def test_schema_handles_nulls():
    """Vérifie que le schéma accepte les nulls pour les champs optionnels (Union[T, None])."""
    
    valid_data = {
        "schema_version": "1.0",
        "parse_status": "COMPLETE",
        "indicators": [],
        "populations": [],
        "territories": [],
        "time_expressions": [],
        "measures": [
            {
                "source_text": "3.5",
                "occurrence": 1,
                "numeric_value": 3.5,
                "lower_bound": None,  # Test null
                "upper_bound": None,  # Test null
                "unit": "UNKNOWN",
                "scale": "NONE",
                "role": "START_VALUE",
                "approximation": "EXACT",
                "sign": None,         # Test null
                "source_scope": "CLAIM"
            }
        ],
        "operation": None,  # Test null
        "frequency": None,  # Test null
        "adjustment": None, # Test null
        "comparisons": [],
        "ambiguities": [],
        "missing_context": []
    }
    
    # Doit passer sans erreur
    model = ClaimParseResult(**valid_data)
    assert model.operation is None
    assert model.measures[0].lower_bound is None
