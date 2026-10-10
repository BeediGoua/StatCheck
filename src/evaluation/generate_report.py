import json
import os
from typing import List, Dict, Any

from src.parser.adapters.baseline_to_canonical import baseline_dict_to_claim_specification
from src.parser.adapters.llm_to_canonical import llm_result_to_claim_specification
from src.parser.claim_specification import ClaimSpecification
from src.evaluation.scorer import Scorer
from src.evaluation.orchestrator import EvaluationOrchestrator


class ReportGenerator:
    def __init__(self):
        self.scorer = Scorer()
        self.orchestrator = EvaluationOrchestrator()

    def _aggregate_metrics(
        self, predictions: List[ClaimSpecification], golds: List[ClaimSpecification]
    ) -> Dict[str, float]:
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
            ind_key = "indicator" if "indicator" in res["metrics"] else "indicators"
            total_f1_indicators += res["metrics"][ind_key]["semantic"]["f1"]
            if p.parse_status != "REJECTED" and p.parse_status != "MISSING_CONTEXT":
                total_coverage += 1

        return {
            "exact_match": (total_exact / n) * 100,
            "f1_measures": (total_f1_measures / n) * 100,
            "f1_indicators": (total_f1_indicators / n) * 100,
            "silent_errors": total_silent,
            "coverage": (total_coverage / n) * 100,
        }

    def run_campaign(
        self,
        texts: List[str],
        golds: List[ClaimSpecification],
        baselines: List[ClaimSpecification],
        llms: List[ClaimSpecification],
    ) -> str:
        c0_preds = self.orchestrator.evaluate_c0_baseline(baselines)
        c0_metrics = self._aggregate_metrics(c0_preds, golds)

        c1_preds = self.orchestrator.evaluate_c1_llm(llms)
        c1_metrics = self._aggregate_metrics(c1_preds, golds)

        c2_preds = self.orchestrator.evaluate_c2_fusion(baselines, llms)
        c2_metrics = self._aggregate_metrics(c2_preds, golds)

        c3_out = self.orchestrator.evaluate_c3_cascade(texts, baselines, llms)
        c3_preds = c3_out["results"]
        c3_metrics = self._aggregate_metrics(c3_preds, golds)
        c3_stats = c3_out["metrics"]

        md = []
        md.append("# Rapport d'évaluation")
        md.append(
            f"| Métrique | C0 | C1 | C2 | C3 |"
        )
        md.append("|---|---|---|---|---|")
        md.append(
            f"| Exact Match | {c0_metrics.get('exact_match',0):.1f}% | {c1_metrics.get('exact_match',0):.1f}% | {c2_metrics.get('exact_match',0):.1f}% | {c3_metrics.get('exact_match',0):.1f}% |"
        )
        md.append(
            f"| F1 Measures | {c0_metrics.get('f1_measures',0):.1f}% | {c1_metrics.get('f1_measures',0):.1f}% | {c2_metrics.get('f1_measures',0):.1f}% | {c3_metrics.get('f1_measures',0):.1f}% |"
        )
        md.append(
            f"| F1 Indicators | {c0_metrics.get('f1_indicators',0):.1f}% | {c1_metrics.get('f1_indicators',0):.1f}% | {c2_metrics.get('f1_indicators',0):.1f}% | {c3_metrics.get('f1_indicators',0):.1f}% |"
        )
        md.append(
            f"| Erreurs silencieuses | {c0_metrics.get('silent_errors',0)} | {c1_metrics.get('silent_errors',0)} | {c2_metrics.get('silent_errors',0)} | {c3_metrics.get('silent_errors',0)} |"
        )
        md.append(
            f"| Couverture | {c0_metrics.get('coverage',0):.1f}% | {c1_metrics.get('coverage',0):.1f}% | {c2_metrics.get('coverage',0):.1f}% | {c3_metrics.get('coverage',0):.1f}% |"
        )
        md.append(
            f"| Taux d'appel LLM | 0.0% | 100.0% | 100.0% | {c3_stats['llm_call_rate']*100:.1f}% |"
        )

        return "\n".join(md)


def safe_parse(data_dict: dict, origin_name: str) -> ClaimSpecification:
    """Best-effort parse of legacy prediction dicts into ClaimSpecification V1."""
    if not data_dict:
        return ClaimSpecification(
            claim_id="unknown", original_text="", parse_status="PARTIAL"
        )

    if "subject" in data_dict or "identity" in data_dict:
        return baseline_dict_to_claim_specification(data_dict)

    if "indicators" in data_dict or "measures" in data_dict or "time_expressions" in data_dict:
        return llm_result_to_claim_specification(
            data_dict,
            claim_id=str(data_dict.get("claim_id") or "unknown"),
            original_text=str(data_dict.get("original_text") or ""),
        )

    # Already Spec-shaped (or close)
    payload = dict(data_dict)
    payload.setdefault("claim_id", "unknown")
    payload.setdefault("original_text", "")
    allowed = set(ClaimSpecification.model_fields.keys())
    filtered = {k: v for k, v in payload.items() if k in allowed}
    try:
        return ClaimSpecification(**filtered)
    except Exception:
        return ClaimSpecification(
            claim_id="unknown",
            original_text="",
            parse_status="PARTIAL",
            warnings=[f"safe_parse_failed_for_{origin_name}"],
        )


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
                    llms.append(
                        ClaimSpecification(claim_id="unknown", original_text="")
                    )

    if len(llms) > len(baselines) and len(baselines) > 0:
        llms = llms[: len(baselines)]

    golds = baselines

    if len(baselines) > 0 and len(llms) > 0:
        generator = ReportGenerator()
        report = generator.run_campaign(texts, golds, baselines, llms)
        print(report)
