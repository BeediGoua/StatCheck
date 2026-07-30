import json
from src.parser.llm.schemas.claim_parse import ClaimParseResult

def dump():
    schema = ClaimParseResult.model_json_schema()
    with open("scratch/schema_dump.json", "w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)

if __name__ == "__main__":
    dump()
