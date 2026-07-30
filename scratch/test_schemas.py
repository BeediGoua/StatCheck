import sys
sys.path.insert(0, ".")
from src.parser.llm.schemas.claim_parse import ClaimParseResult

def test_schema_generation():
    print("Test de la génération du schéma JSON Pydantic...")
    try:
        schema = ClaimParseResult.model_json_schema()
        print("Succès ! Schéma généré.")
        print(f"Nombre de champs racine : {len(schema['properties'])}")
        assert schema["additionalProperties"] is False, "additionalProperties n'est pas False !"
        print("La règle additionalProperties: false est bien respectée à la racine.")
    except Exception as e:
        print(f"Erreur lors de la génération du schéma : {e}")

if __name__ == '__main__':
    test_schema_generation()
