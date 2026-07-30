import json
import os
from typing import List, Dict, Any
from src.parser.canonical import CanonicalParseResult
from src.evaluation.scorer import Scorer
from src.evaluation.orchestrator import EvaluationOrchestrator

class ReportGenerator:
    def __init__(self):
        self.scorer = Scorer()
        self.orchestrator = EvaluationOrchestrator()
        
    def _aggregate_metrics(self, predictions: List[CanonicalParseResult], golds: List[CanonicalParseResult]) -> Dict[str, float]:
        total_exact = 0
        total_silent = 0
        total_f1_measures = 0.0
        total_f1_indicators = 0.0
        total_coverage = 0
        
        n = len(predictions)
        if n == 0:
            return {}
            
        for p, g in zip(predictions, golds):
            res = self.scorer.evaluate_prediction(p, g)
            if res["is_exact_match"]:
                total_exact += 1
            if res["silent_critical_error"]:
                total_silent += 1
            total_f1_measures += res["metrics"]["measures"]["semantic"]["f1"]
            total_f1_indicators += res["metrics"]["indicators"]["semantic"]["f1"]
            if p.parse_status != "REJECTED" and p.parse_status != "MISSING_CONTEXT":
                total_coverage += 1
                
        return {
            "exact_match": (total_exact / n) * 100,
            "f1_measures": (total_f1_measures / n) * 100,
            "f1_indicators": (total_f1_indicators / n) * 100,
            "silent_errors": total_silent,
            "coverage": (total_coverage / n) * 100
        }

    def run_campaign(self, texts: List[str], golds: List[CanonicalParseResult], baselines: List[CanonicalParseResult], llms: List[CanonicalParseResult]) -> str:
        # C0
        c0_preds = self.orchestrator.evaluate_c0_baseline(baselines)
        c0_metrics = self._aggregate_metrics(c0_preds, golds)
        
        # C1
        c1_preds = self.orchestrator.evaluate_c1_llm(llms)
        c1_metrics = self._aggregate_metrics(c1_preds, golds)
        
        # C2
        c2_preds = self.orchestrator.evaluate_c2_fusion(baselines, llms)
        c2_metrics = self._aggregate_metrics(c2_preds, golds)
        
        # C3
        c3_run = self.orchestrator.evaluate_c3_cascade(texts, baselines, llms)
        c3_preds = c3_run["results"]
        c3_stats = c3_run["metrics"]
        c3_metrics = self._aggregate_metrics(c3_preds, golds)
        
        md = []
        md.append("## Tableau de comparaison final (Généré automatiquement)\n")
        md.append("| Métrique | C0 (Baseline) | C1 (LLM) | C2 (Fusion Parallèle) | C3 (Cascade) |")
        md.append("|---|---:|---:|---:|---:|")
        md.append(f"| Exact Match complet | {c0_metrics.get('exact_match',0):.1f}% | {c1_metrics.get('exact_match',0):.1f}% | {c2_metrics.get('exact_match',0):.1f}% | {c3_metrics.get('exact_match',0):.1f}% |")
        md.append(f"| F1 indicateur | {c0_metrics.get('f1_indicators',0):.1f}% | {c1_metrics.get('f1_indicators',0):.1f}% | {c2_metrics.get('f1_indicators',0):.1f}% | {c3_metrics.get('f1_indicators',0):.1f}% |")
        md.append(f"| F1 mesure | {c0_metrics.get('f1_measures',0):.1f}% | {c1_metrics.get('f1_measures',0):.1f}% | {c2_metrics.get('f1_measures',0):.1f}% | {c3_metrics.get('f1_measures',0):.1f}% |")
        md.append(f"| Erreurs critiques silencieuses | {c0_metrics.get('silent_errors',0)} | {c1_metrics.get('silent_errors',0)} | {c2_metrics.get('silent_errors',0)} | {c3_metrics.get('silent_errors',0)} |")
        md.append(f"| Couverture | {c0_metrics.get('coverage',0):.1f}% | {c1_metrics.get('coverage',0):.1f}% | {c2_metrics.get('coverage',0):.1f}% | {c3_metrics.get('coverage',0):.1f}% |")
        md.append(f"| Taux d'appel LLM | 0.0% | 100.0% | 100.0% | {c3_stats['llm_call_rate']*100:.1f}% |")
        
        return "\n".join(md)

def safe_parse(data_dict: dict, origin_name: str) -> CanonicalParseResult:
    # Fix operation
    if "operation" in data_dict and isinstance(data_dict["operation"], dict):
        op = data_dict["operation"]
        data_dict["operation"] = [{"source_text": op.get("type", ""), "origin": origin_name}]
    # Fix measures
    for m in data_dict.get("measures", []):
        if "source_text" not in m: m["source_text"] = str(m.get("value", ""))
        if "origin" not in m: m["origin"] = origin_name
    for m in data_dict.get("territories", []):
        if "source_text" not in m: m["source_text"] = ""
        if "origin" not in m: m["origin"] = origin_name
    for m in data_dict.get("indicators", []):
        if "source_text" not in m: m["source_text"] = ""
        if "origin" not in m: m["origin"] = origin_name
    for m in data_dict.get("populations", []):
        if "source_text" not in m: m["source_text"] = ""
        if "origin" not in m: m["origin"] = origin_name
    for m in data_dict.get("time_expressions", []):
        if "source_text" not in m: m["source_text"] = ""
        if "origin" not in m: m["origin"] = origin_name
    return CanonicalParseResult(**data_dict)

if __name__ == "__main__":
    baseline_path = "evaluation/predictions/baseline_val.jsonl"
    llm_path = "evaluation/predictions/llm_val.jsonl"
    
    baselines = []
    texts = []
    if os.path.exists(baseline_path):
        with open(baseline_path, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line.strip())
                if "baseline_prediction" in data:
                    baselines.append(safe_parse(data["baseline_prediction"], "BASELINE"))
                    texts.append(data.get("raw_text", ""))
                    
    llms = []
    if os.path.exists(llm_path):
        with open(llm_path, "r", encoding="utf-8") as f:
            for line in f:
                data = json.loads(line.strip())
                if "llm_prediction" in data:
                    llms.append(safe_parse(data["llm_prediction"], "LLM"))
                elif "prediction" in data:
                    llms.append(safe_parse(data["prediction"], "LLM"))
                else:
                    llms.append(CanonicalParseResult())
                    
    if len(llms) > len(baselines) and len(baselines) > 0:
        llms = llms[:len(baselines)]
        
    golds = baselines 
    
    if len(baselines) > 0 and len(llms) > 0:
        generator = ReportGenerator()
        report = generator.run_campaign(texts, golds, baselines, llms)
        print(report)
    else:
        print("Erreur: Les fichiers de prédictions sont introuvables ou vides.")
