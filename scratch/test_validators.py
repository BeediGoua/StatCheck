import sys
sys.path.insert(0, ".")

from src.parser.llm.schemas.claim_parse import ClaimParseResult
from src.parser.llm.validators.orchestrator import apply_all_validators

def test_validators():
    claim_text = "Le chômage a baissé de 3,5 points au premier trimestre 2022 en France métropolitaine pour atteindre 7%."
    
    # Simulation du JSON extrait par le LLM (avec hallucinations)
    raw_llm_output = {
        "schema_version": "1.0",
        "parse_status": "COMPLETE",
        "indicators": [
            {"source_text": "chômage", "occurrence": 1, "normalized_label": "Taux de chômage", "source_scope": "CLAIM", "certainty": "EXPLICIT"}
        ],
        "populations": [],
        "territories": [
            {"source_text": "France métropolitaine", "occurrence": 1, "normalized_label": "France métropolitaine", "source_scope": "CLAIM", "certainty": "EXPLICIT", "territory_hint": "UNKNOWN"},
            {"source_text": "75", "occurrence": 1, "normalized_label": "75", "source_scope": "CLAIM", "certainty": "IMPLICIT", "territory_hint": "UNKNOWN"} # Hallucination COG (le texte source "75" n'existe pas)
        ],
        "time_expressions": [
            {"source_text": "premier trimestre 2022", "occurrence": 1, "temporal_type": "EXPLICIT_QUARTER", "granularity": "QUARTERLY", "is_relative": False, "normalized_start": "2022-01-01", "normalized_end": "2022-03-31", "reference_date_used": False, "source_scope": "CLAIM", "certainty": "EXPLICIT"}
        ],
        "measures": [
            {"source_text": "3,5", "occurrence": 1, "numeric_value": 35.0, "lower_bound": None, "upper_bound": None, "unit": "PERCENTAGE_POINT", "scale": "NONE", "role": "ABSOLUTE_CHANGE", "approximation": "EXACT", "sign": None, "source_scope": "CLAIM"}, # Erreur mathématique du LLM (35 au lieu de 3.5)
            {"source_text": "7%", "occurrence": 1, "numeric_value": 7.0, "lower_bound": None, "upper_bound": None, "unit": "PERCENTAGE", "scale": "NONE", "role": "END_VALUE", "approximation": "EXACT", "sign": None, "source_scope": "CLAIM"}
        ],
        "operation": {
            "type": "VALUE", "direction": "DECREASE", "polarity": "AFFIRMED", "comparator": "EQUAL", "is_explicit": True, "trigger_text": "a baissé", "trigger_occurrence": 1
        },
        "frequency": None,
        "adjustment": None,
        "comparisons": [],
        "ambiguities": [],
        "missing_context": []
    }
    
    # 1. Validation Pydantic (le modèle LLM)
    parsed_model = ClaimParseResult(**raw_llm_output)
    parsed_dict = parsed_model.model_dump()
    
    print(f"Nombre de territoires avant: {len(parsed_dict['territories'])}")
    print(f"Valeur de la variation avant: {parsed_dict['measures'][0]['numeric_value']}")
    
    # 2. Application des validateurs
    validated_dict = apply_all_validators(claim_text, parsed_dict)
    
    print("-" * 50)
    print(f"Nombre de territoires après: {len(validated_dict['territories'])} (le territoire halluciné sans source texte valide doit disparaitre)")
    print(f"Valeur de la variation après: {validated_dict['measures'][0]['numeric_value']} (doit être corrigée à 3.5)")
    print(f"Raw start de chômage: {validated_dict['indicators'][0].get('raw_start')}")

if __name__ == '__main__':
    test_validators()
