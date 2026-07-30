import json
import os
import time
from datetime import datetime
from src.parser.baseline.baseline_parser import parse_claim_baseline

def main():
    print("Démarrage de l'évaluation Baseline (Lot 6C - Étape 4) - Exécution Réelle")
    
    validation_path = "data/corpus/validation_split.jsonl"
    if not os.path.exists(validation_path):
        print(f"Erreur: Fichier {validation_path} introuvable.")
        return
        
    validation_claims = []
    with open(validation_path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                validation_claims.append(json.loads(line))
                
    predictions_path = "evaluation/predictions/baseline_val.jsonl"
    report_path = "evaluation/reports/baseline_errors.json"
    
    os.makedirs(os.path.dirname(predictions_path), exist_ok=True)
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    
    predictions = []
    
    print(f"Lancement de la Baseline sur {len(validation_claims)} affirmations...")
    
    with open(predictions_path, "w", encoding="utf-8") as f_out:
        for claim in validation_claims:
            start_time = time.time()
            try:
                # La baseline n'a besoin d'aucune API
                reference_date = claim.get("gold_annotation", {}).get("identity", {}).get("reference_date")
                result = parse_claim_baseline(claim["text"], reference_date=reference_date)
                
                duration_ms = int((time.time() - start_time) * 1000)
                output = {
                    "claim_id": claim["id"],
                    "raw_text": claim["text"],
                    "baseline_prediction": result,
                    "status": "SUCCESS",
                    "metrics": {"time_ms": duration_ms}
                }
            except Exception as e:
                output = {
                    "claim_id": claim["id"],
                    "raw_text": claim["text"],
                    "error": str(e),
                    "status": "ERROR"
                }
                
            predictions.append(output)
            f_out.write(json.dumps(output, ensure_ascii=False) + "\n")
            
    print(f"Prédictions sauvegardées dans {predictions_path}")
    
    # Rapport générique d'exécution
    error_report = {
        "run_name": "baseline_val_run_1",
        "timestamp": datetime.now().isoformat(),
        "total_claims": len(validation_claims),
        "success_count": sum(1 for p in predictions if p["status"] == "SUCCESS"),
        "error_count": sum(1 for p in predictions if p["status"] == "ERROR")
    }
    
    with open(report_path, "w", encoding="utf-8") as f_err:
        json.dump(error_report, f_err, ensure_ascii=False, indent=2)
        
    print(f"Rapport d'exécution produit dans {report_path}")
    print("Évaluation terminée.")

if __name__ == "__main__":
    main()
