from src.parser.llm.client.retry_policy import call_llm_with_retry
from src.parser.llm.client.openai_client import get_llm_client
from pydantic import BaseModel

class TestModel(BaseModel):
    name: str

client = get_llm_client()
print("Client et retry policy importés avec succès.")
