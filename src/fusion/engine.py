from typing import Any, Dict, List, Optional, Tuple

from src.fusion.alignment import BipartiteAligner
from src.fusion.authority import AuthorityMatrix, DecisionType
from src.parser.claim_specification import (
    ClaimSpecification,
    ClaimedQuantity,
    ParseStatus,
)


class FusionEngine:
    """Orchestrateur central du pipeline de fusion (ClaimSpecification V1)."""

    def __init__(self):
        self.aligner = BipartiteAligner()
        self.authority = AuthorityMatrix()

    def fuse(
        self,
        baseline: ClaimSpecification,
        llm: ClaimSpecification,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[ClaimSpecification, List[Dict]]:
        decisions_log: List[Dict] = []
        final_result = ClaimSpecification(
            claim_id=baseline.claim_id or llm.claim_id,
            original_text=baseline.original_text or llm.original_text,
            parse_status=ParseStatus.PENDING,
            indicator=baseline.indicator or llm.indicator,
            populations=list(baseline.populations or llm.populations),
            territories=list(baseline.territories),
            time_period=baseline.time_period or llm.time_period,
            statistical_operation=baseline.statistical_operation
            or llm.statistical_operation,
        )

        b_qty = baseline.quantity_list()
        l_qty = llm.quantity_list()
        measure_alignments = self.aligner.align(b_qty, l_qty)

        matched_base_indices = set()
        matched_llm_indices = set()
        fused_quantities: List[ClaimedQuantity] = []

        for align in measure_alignments:
            b_idx = align["baseline_idx"]
            l_idx = align["llm_idx"]
            matched_base_indices.add(b_idx)
            matched_llm_indices.add(l_idx)

            b_mention = align["baseline_mention"]
            l_mention = align["llm_mention"]

            auth_res = self.authority.fuse_measure(b_mention, l_mention)
            if auth_res["result"]:
                fused_quantities.append(auth_res["result"])

            decisions_log.append(
                {
                    "field": "quantities",
                    "alignment_type": align["alignment_type"].value,
                    "score": align["score"],
                    "baseline_value": b_mention.model_dump(),
                    "llm_value": l_mention.model_dump(),
                    "decision_type": auth_res["decision"].value,
                    "explanation": auth_res["explanation"].value,
                }
            )

        for i, b_mention in enumerate(b_qty):
            if i not in matched_base_indices:
                auth_res = self.authority.fuse_measure(b_mention, None)
                if auth_res["result"]:
                    fused_quantities.append(auth_res["result"])
                decisions_log.append(
                    {
                        "field": "quantities",
                        "alignment_type": "NOT_ALIGNED",
                        "decision_type": auth_res["decision"].value,
                        "explanation": auth_res["explanation"].value,
                    }
                )

        for i, l_mention in enumerate(l_qty):
            if i not in matched_llm_indices:
                auth_res = self.authority.fuse_measure(None, l_mention)
                if auth_res["result"]:
                    fused_quantities.append(auth_res["result"])
                decisions_log.append(
                    {
                        "field": "quantities",
                        "alignment_type": "NOT_ALIGNED",
                        "decision_type": auth_res["decision"].value,
                        "explanation": auth_res["explanation"].value,
                    }
                )

        # Re-split into claimed vs reference using roles
        from src.parser.claim_specification import CLAIMED_QUANTITY_ROLES

        claimed = None
        references: List[ClaimedQuantity] = []
        for q in fused_quantities:
            if q.role in CLAIMED_QUANTITY_ROLES and claimed is None:
                claimed = q
            else:
                references.append(q)
        if claimed is None and fused_quantities:
            claimed = fused_quantities[0]
            references = fused_quantities[1:]

        final_result.claimed_quantity = claimed
        final_result.reference_quantities = references

        # Territory fuse (simple first-pair / orphans) — full rewrite in Session 3
        terr_align = self.aligner.align(baseline.territories, llm.territories)
        matched_bt, matched_lt = set(), set()
        fused_terr = []
        for align in terr_align:
            matched_bt.add(align["baseline_idx"])
            matched_lt.add(align["llm_idx"])
            auth_res = self.authority.fuse_territory(
                align["baseline_mention"], align["llm_mention"]
            )
            if auth_res["result"]:
                fused_terr.append(auth_res["result"])
            decisions_log.append(
                {
                    "field": "territories",
                    "alignment_type": align["alignment_type"].value,
                    "decision_type": auth_res["decision"].value,
                    "explanation": auth_res["explanation"].value,
                }
            )
        for i, t in enumerate(baseline.territories):
            if i not in matched_bt:
                auth_res = self.authority.fuse_territory(t, None)
                if auth_res["result"]:
                    fused_terr.append(auth_res["result"])
        for i, t in enumerate(llm.territories):
            if i not in matched_lt:
                auth_res = self.authority.fuse_territory(None, t)
                if auth_res["result"]:
                    fused_terr.append(auth_res["result"])
        if fused_terr:
            final_result.territories = fused_terr

        self._apply_post_validators(final_result)

        if final_result.parse_status != ParseStatus.REJECTED:
            has_ambiguity = any(
                d["decision_type"] == DecisionType.BOTH_RETAINED_AS_ALTERNATIVES.value
                for d in decisions_log
            )
            has_conflict = any(
                d["decision_type"] == DecisionType.CONFLICT_UNRESOLVED.value
                for d in decisions_log
            )
            if has_conflict:
                final_result.parse_status = ParseStatus.CONTRADICTION
            elif has_ambiguity:
                final_result.parse_status = ParseStatus.AMBIGUOUS
            else:
                final_result.parse_status = ParseStatus.COMPLETE

        return final_result, decisions_log

    def _apply_post_validators(self, result: ClaimSpecification) -> None:
        """Placeholder — Session 3 will wire real post-validators."""
        pass
