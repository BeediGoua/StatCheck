import random
from typing import List, Dict, Any
from src.parser.canonical import CanonicalParseResult
from src.fusion.engine import FusionEngine
from src.evaluation.router import C3Router

class EvaluationOrchestrator:
    """
    Orchestrateur garantissant une comparaison équitable (Phase A du protocole).
    Utilise des pré-calculs LLM pour figer la variance de l'IA entre les architectures.
    """
    
    def __init__(self):
        self.fusion = FusionEngine()
        self.router = C3Router()
        
    def evaluate_c0_baseline(self, baseline_outputs: List[CanonicalParseResult]) -> List[CanonicalParseResult]:
        """C0 : Baseline seule. Aucun appel LLM."""
        return baseline_outputs

    def evaluate_c1_llm(self, precomputed_llm_outputs: List[CanonicalParseResult]) -> List[CanonicalParseResult]:
        """C1 : LLM seul (post-validé)."""
        return precomputed_llm_outputs
        
    def evaluate_c2_fusion(self, baseline_outputs: List[CanonicalParseResult], precomputed_llm_outputs: List[CanonicalParseResult]) -> List[CanonicalParseResult]:
        """C2 : Fusion toujours active sur 100% des affirmations."""
        fused_results = []
        for b, l in zip(baseline_outputs, precomputed_llm_outputs):
            fused, _ = self.fusion.fuse(b, l)
            fused_results.append(fused)
        return fused_results
        
    def evaluate_c3_cascade(self, texts: List[str], baseline_outputs: List[CanonicalParseResult], precomputed_llm_outputs: List[CanonicalParseResult]) -> Dict[str, Any]:
        """
        C3 : Cascade déterministe. Baseline -> Routeur -> (LLM + Fusion si nécessaire).
        """
        c3_results = []
        llm_calls_count = 0
        control_sample_count = 0
        
        for i, (text, b, l) in enumerate(zip(texts, baseline_outputs, precomputed_llm_outputs)):
            # 1. Analyse par le routeur
            route_decision = self.router.should_call_llm(b, text)
            
            # 2. Injection déterministe pour l'échantillon de contrôle
            random.seed(i) # Seed stable pour reproductibilité
            is_control = self.router.should_trigger_control_sample(not route_decision["trigger"], random.random())
            
            # 3. Exécution
            if route_decision["trigger"] or is_control:
                llm_calls_count += 1
                if is_control and not route_decision["trigger"]:
                    control_sample_count += 1
                
                # Le LLM est appelé, on fusionne
                fused, _ = self.fusion.fuse(b, l)
                c3_results.append(fused)
            else:
                # La baseline suffit
                c3_results.append(b)
                
        return {
            "results": c3_results,
            "metrics": {
                "total_claims": len(texts),
                "llm_calls_count": llm_calls_count,
                "llm_call_rate": llm_calls_count / max(1, len(texts)),
                "control_sample_count": control_sample_count
            }
        }
