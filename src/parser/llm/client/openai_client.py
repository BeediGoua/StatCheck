import openai
import instructor

def get_llm_client(base_url: str = "http://localhost:11434/v1", api_key: str = "ollama"):
    """
    Initialise le client OpenAI pointant vers l'API locale (Ollama par défaut),
    et l'encapsule avec Instructor pour gérer les Structured Outputs.
    """
    return instructor.from_openai(
        openai.OpenAI(
            base_url=base_url,
            api_key=api_key,
        ),
        mode=instructor.Mode.JSON,
    )
