import json
import os
from src.parser.baseline.baseline_parser import parse_claim_baseline

def evaluate_baseline():
    corpus_path = os.path.join(os.path.dirname(__file__), "..", "data", "corpus", "pilote_6A_V.json")
    with open(corpus_path, "r", encoding="utf-8") as f:
        cases = json.load(f)
        
    results = []
    correct = 0
    total = len(cases)
    
    for case in cases:
        text = case["text"]
        expected = case["expected"]
        
        parsed = parse_claim_baseline(text, reference_date="2024-01-01")
        
        status_match = parsed["status"]["answerability"] == expected["answerability"]
        
        is_correct = status_match
        
        results.append({
            "id": case["id"],
            "text": text,
            "parsed_status": parsed["status"]["answerability"],
            "expected_status": expected["answerability"],
            "is_correct": is_correct
        })
        
        if is_correct:
            correct += 1

    accuracy = correct / total if total > 0 else 0
    
    report = f"# Évaluation Baseline 6A-V\n\n- **Exact Match Global (Statut)** : {accuracy:.2%}\n- **Total** : {total} cas\n\n## Détails\n"
    for r in results:
        icon = "✅" if r["is_correct"] else "❌"
        report += f"- {icon} [{r['id']}] {r['text']}\n  - Attendu : {r['expected_status']} | Reçu : {r['parsed_status']}\n"
        
    report_path = os.path.join(os.path.dirname(__file__), "..", "baseline_metrics_frozen.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
        
    print(f"Évaluation terminée : {accuracy:.2%}. Rapport généré: {report_path}")

if __name__ == "__main__":
    evaluate_baseline()
