from src.parser.adapters.baseline_to_canonical import baseline_dict_to_claim_specification
from src.parser.adapters.llm_to_canonical import llm_result_to_claim_specification

__all__ = [
    "baseline_dict_to_claim_specification",
    "llm_result_to_claim_specification",
]
