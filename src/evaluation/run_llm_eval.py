import json
import os
import time
from datetime import datetime
try:
    from openai import OpenAI
    HAS_OPENAI = True
except ImportError:
    HAS_OPENAI = False
    import requests

def extract_json_from_llm_response(text: str) -> dict:
    """Extrait le JSON depuis la réponse du LLM (si entouré de backticks markdown)."""
    text = text.strip()
    if text.startswith("```json"):
        text = text[7:]
    elif text.startswith("```"):
        text = text[3:]
    if text.endswith("```"):
        text = text[:-3]
    return json.loads(text.strip())

def call_qwen_api(prompt: str, model: str = "qwen2.5:latest") -> str:
    """Appelle l'API Ollama locale hébergeant Qwen."""
    system_prompt = "Tu es un extracteur d'information. Réponds TOUJOURS avec un JSON valide suivant le format CanonicalParseResult."
    
    if HAS_OPENAI:
        client = OpenAI(
            api_key="ollama", # Clé fictive requise par le SDK
            base_url="http://localhost:11434/v1",
        )
        completion = client.chat.completions.create(
            model=model,
            messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            temperature=0.2 # Légère température pour mesurer la stabilité sur 3 runs
        )
        return completion.choices[0].message.content
    else:
        data = {
            "model": model,
            "messages": [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': prompt}
            ],
            "temperature": 0.2,
            "stream": False
        }
        resp = requests.post("http://localhost:11434/api/chat", json=data)
        resp.raise_for_status()
        return resp.json()["message"]["content"]

def main():
    print("Démarrage de l'évaluation LLM (Lot 6C - Étape 5) - API Qwen via Ollama")
    
    # La vérification de la clé API Dashscope a été retirée puisque nous sommes en local sur Ollama.

    validation_path = "data/corpus/validation_split.jsonl"
    if not os.path.exists(validation_path):
        print(f"Erreur : Corpus de validation introuvable ({validation_path})")
        return
        
    validation_claims = []
    with open(validation_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                validation_claims.append(json.loads(line))
                
    predictions_path = "evaluation/predictions/llm_val.jsonl"
    report_path = "evaluation/reports/llm_post_validation_report.json"
    
    os.makedirs(os.path.dirname(predictions_path), exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    predictions = []
    
    stats_post_validation = {
        "total_mentions_modified": 0,
        "total_claims_rejected_by_validator": 0,
        "total_claims_repaired": 0
    }
    
    # Prompt simple pour la démo - En V1 il inclura le schéma JSONSchema attendu.
    prompt_template = """Extrais les informations de la phrase suivante au format JSON (indicateurs, measures, territories, time).
Phrase: "{claim_text}"
Date de référence: "{reference_date}"
"""
    
    with open(predictions_path, "w", encoding="utf-8") as f_out:
        for claim in validation_claims:
            claim_text = claim["text"]
            reference_date = claim.get("gold_annotation", {}).get("identity", {}).get("reference_date", "")
            
            prompt = prompt_template.format(claim_text=claim_text, reference_date=reference_date)
            
            # Lancer 3 exécutions pour mesurer la variabilité (stabilité)
            for run_idx in range(3):
                start_time = time.time()
                try:
                    raw_response = call_qwen_api(prompt)
                    parsed_json = extract_json_from_llm_response(raw_response)
                    
                    # Simulation du validateur déterministe qui prend le JSON LLM et le nettoie
                    validated_data = parsed_json.copy() # TODO: Pydantic Validation & Normalization
                    
                    duration = int((time.time() - start_time) * 1000)
                    
                    output = {
                        "claim_id": claim["id"],
                        "run_index": run_idx + 1,
                        "raw_text": claim_text,
                        "llm_prediction_raw": parsed_json,
                        "llm_prediction_validated": validated_data,
                        "status": "ACCEPTED",
                        "metrics": {"time_ms": duration}
                    }
                except Exception as e:
                    output = {
                        "claim_id": claim["id"],
                        "run_index": run_idx + 1,
                        "raw_text": claim_text,
                        "error": str(e),
                        "status": "ERROR"
                    }
                    
                predictions.append(output)
                f_out.write(json.dumps(output, ensure_ascii=False) + "\n")
                
                # Sleep pour limiter le rate limit de l'API
                time.sleep(1.0)
                
    print(f"Prédictions LLM Qwen sauvegardées dans {predictions_path} (3 runs par affirmation)")
    
    # Sauvegarde du rapport
    with open(report_path, "w", encoding="utf-8") as f_err:
        json.dump({
            "run_name": "llm_val_qwen_run_1",
            "model": "qwen2.5:latest (Ollama)",
            "timestamp": datetime.now().isoformat(),
            "runs_per_claim": 3,
            "post_validation_impact": stats_post_validation
        }, f_err, ensure_ascii=False, indent=2)
        
    print(f"Rapport d'apport des post-validateurs produit dans {report_path}")
    print("Évaluation terminée.")

if __name__ == "__main__":
    main()
