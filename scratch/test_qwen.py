import openai
import instructor
from pydantic import BaseModel

# Définition d'un schéma simple pour le test
class UserInfo(BaseModel):
    name: str
    age: int

# Configuration du client OpenAI pour pointer vers l'API locale d'Ollama
# (On suppose ici que Qwen2.5 tourne localement sur le port 11434 via Ollama)
client = instructor.from_openai(
    openai.OpenAI(
        base_url="http://localhost:11434/v1",
        api_key="ollama", # Clé arbitraire requise par le client OpenAI
    ),
    mode=instructor.Mode.JSON,
)

def test_qwen():
    print("Envoi de la requête à Qwen2.5 via Ollama...")
    try:
        resp = client.chat.completions.create(
            model="qwen2.5:latest", # Nom typique du modèle dans Ollama
            messages=[
                {"role": "user", "content": "Extrais les informations de la phrase suivante : Jean a 35 ans."}
            ],
            response_model=UserInfo,
        )
        print("\nSuccès ! L'objet Pydantic a été retourné correctement :")
        print(resp.model_dump_json(indent=2))
    except Exception as e:
        print(f"\nErreur lors de l'appel : {e}")
        print("Vérifiez que Ollama tourne bien avec 'qwen2.5:7b-instruct' et que le port 11434 est accessible.")

if __name__ == "__main__":
    test_qwen()
