import sys
import time
import json
sys.path.insert(0, ".")

from src.parser.baseline.baseline_parser import BaselineParser
from src.parser.llm.llm_parser import StatCheckLLMParser
from src.parser.llm.schemas.envelope import LLMInputEnvelope, ValidationStatus

# Mocks pour l'expérience
CLAIMS = [
    {
        "id": "claim_1",
        "text": "Le chômage a baissé de 2 points en 2022 en France.",
        "expected_measures": [2.0],
        "expected_territories": ["France"]
    },
    {
        "id": "claim_2",
        "text": "L'inflation est de 5,5% au premier trimestre.",
        "expected_measures": [5.5],
        "expected_territories": []
    },
    {
        "id": "claim_3",
        "text": "Une hausse d'environ 3 millions de chômeurs en Île-de-France l'année dernière.",
        "expected_measures": [3.0], # L'échelle 'millions' gérée séparément
        "expected_territories": ["Île-de-France"]
    }
]

def run_experiment_e():
    print("=== DÉBUT DE L'EXPÉRIENCE E (COMPARAISON BASELINE vs LLM) ===")
    
    baseline_parser = BaselineParser()
    llm_parser = StatCheckLLMParser()
    
    results = []
    
    for claim in CLAIMS:
        print(f"\n[Traitement] {claim['id']} : {claim['text']}")
        
        # 1. Baseline
        t0 = time.time()
        try:
            baseline_res = baseline_parser.parse(claim["text"])
        except Exception:
            baseline_res = {"status": "ERROR"}
        t_baseline = time.time() - t0
        
        # 2. LLM Mode A (Pur)
        env_a = LLMInputEnvelope(claim_id=claim["id"], claim_text=claim["text"])
        res_a = llm_parser.parse_claim(env_a)
        
        # 3. LLM Mode B (Assisté)
        env_b = LLMInputEnvelope(
            claim_id=claim["id"], 
            claim_text=claim["text"],
            baseline_candidates=baseline_res # Injection des résultats de la baseline
        )
        res_b = llm_parser.parse_claim(env_b)
        
        results.append({
            "claim_id": claim["id"],
            "baseline_time_ms": int(t_baseline * 1000),
            "mode_a_time_ms": res_a.metrics.time_ms if res_a else 0,
            "mode_b_time_ms": res_b.metrics.time_ms if res_b else 0,
            "mode_a_status": res_a.status if res_a else "ERROR",
            "mode_b_status": res_b.status if res_b else "ERROR"
        })
        
        print(f"  > Baseline Time: {int(t_baseline * 1000)}ms")
        print(f"  > Mode A Time: {res_a.metrics.time_ms}ms | Status: {res_a.status.value}")
        print(f"  > Mode B Time: {res_b.metrics.time_ms}ms | Status: {res_b.status.value}")

    print("\n=== RÉSULTATS GLOBAUX ===")
    for r in results:
        print(f"{r['claim_id']}: Baseline({r['baseline_time_ms']}ms), ModeA({r['mode_a_status']}, {r['mode_a_time_ms']}ms), ModeB({r['mode_b_status']}, {r['mode_b_time_ms']}ms)")

if __name__ == "__main__":
    run_experiment_e()
