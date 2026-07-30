import json
from datetime import datetime
import os

def generate_manifest(run_name: str, output_path: str):
    """
    Génère un manifeste strict pour garantir la reproductibilité d'un run d'évaluation.
    (Étape B du durcissement).
    """
    manifest = {
        "run_name": run_name,
        "generated_at": datetime.now().isoformat(),
        "corpus": {
            "version": "gold-1.0.0",
            "sha256": "placeholder_hash_corpus",
            "split_manifest_sha256": "placeholder_split_hash"
        },
        "baseline": {
            "version": "6A-1.0.0",
            "spacy_model": "fr_core_news_md",
            "cog_vintage": "2024"
        },
        "llm": {
            "provider": "openai",
            "model_requested": "gpt-4o",
            "prompt_version": "v1.2"
        },
        "git_commit": "placeholder_git_commit_hash"
    }
    
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
        
    return manifest

if __name__ == "__main__":
    generate_manifest("test_run", "evaluation/manifests/test_manifest.json")
    print("Manifeste factice généré dans evaluation/manifests/test_manifest.json")
