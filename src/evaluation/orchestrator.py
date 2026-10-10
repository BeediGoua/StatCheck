import random
from typing import List, Dict, Any
from src.parser.claim_specification import ClaimSpecification
from src.fusion.engine import FusionEngine
from src.evaluation.router import C3Router

class EvaluationOrchestrator:
    """
    Orchestrateur garantissant une comparaison équitable (Phase A du protocole).
    Utilise des pré-calculs LLM pour figer la variance de l'IA entre les architectures.

    C3 route: CALL_LLM vs BASELINE_ONLY. Final answerability comes from the
    Spec itself (or Fusion+post-validators), never from "LLM was called".
    """
    
    def __init__(self):
        self.fusion = FusionEngine()
        self.router = C3Router()
        
    def evaluate_c0_baseline(self, baseline_outputs: List[ClaimSpecification]) -> List[ClaimSpecification]:
        """C0 : Baseline seule. Aucun appel LLM."""
        return baseline_outputs

    def evaluate_c1_llm(self, precomputed_llm_outputs: List[ClaimSpecification]) -> List[ClaimSpecification]:
        """C1 : LLM seul (post-validé)."""
        return precomputed_llm_outputs
        
    def evaluate_c2_fusion(self, baseline_outputs: List[ClaimSpecification], precomputed_llm_outputs: List[ClaimSpecification]) -> List[ClaimSpecification]:
        """C2 : Fusion toujours active sur 100% des affirmations."""
        fused_results = []
        for b, l in zip(baseline_outputs, precomputed_llm_outputs):
            fused, _ = self.fusion.fuse(b, l)
            fused_results.append(fused)
        return fused_results
        
    def evaluate_c3_cascade(self, texts: List[str], baseline_outputs: List[ClaimSpecification], precomputed_llm_outputs: List[ClaimSpecification]) -> Dict[str, Any]:
        """
        C3 : Cascade déterministe. Baseline -> Routeur -> (LLM + Fusion si nécessaire).

        When LLM is called, the returned Spec is Fusion+validators output and may
        remain AMBIGUOUS / CONTRADICTION / PARTIAL — never promoted to COMPLETE
        just because the LLM path ran.
        """
        c3_results = []
        llm_calls_count = 0
        control_sample_count = 0
        route_log: List[Dict[str, Any]] = []
        
        for i, (text, b, l) in enumerate(zip(texts, baseline_outputs, precomputed_llm_outputs)):
            route_decision = self.router.should_call_llm(b, text)
            
            random.seed(i) # Seed stable pour reproductibilité
            is_control = self.router.should_trigger_control_sample(not route_decision["trigger"], random.random())
            
            if route_decision["trigger"] or is_control:
                llm_calls_count += 1
                if is_control and not route_decision["trigger"]:
                    control_sample_count += 1
                
                # Fusion + post-validators decide status (may stay non-COMPLETE)
                fused, fusion_log = self.fusion.fuse(b, l)
                c3_results.append(fused)
                route_log.append(
                    {
                        "index": i,
                        "route": "CALL_LLM",
                        "reason": route_decision["reason"],
                        "control_sample": bool(is_control and not route_decision["trigger"]),
                        "final_status": fused.parse_status.value,
                        "fusion_exit_reason": next(
                            (
                                d.get("reason")
                                for d in reversed(fusion_log)
                                if d.get("field") == "_status"
                            ),
                            None,
                        ),
                    }
                )
            else:
                c3_results.append(b)
                route_log.append(
                    {
                        "index": i,
                        "route": "BASELINE_ONLY",
                        "reason": route_decision["reason"],
                        "control_sample": False,
                        "final_status": b.parse_status.value,
                        "fusion_exit_reason": None,
                    }
                )
                
        return {
            "results": c3_results,
            "metrics": {
                "total_claims": len(texts),
                "llm_calls_count": llm_calls_count,
                "llm_call_rate": llm_calls_count / max(1, len(texts)),
                "control_sample_count": control_sample_count
            },
            "route_log": route_log,
        }
