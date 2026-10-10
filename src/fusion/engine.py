from typing import Any, Dict, List, Optional, Tuple

from src.fusion.alignment import BipartiteAligner
from src.fusion.authority import AuthorityMatrix
from src.fusion.post_validators import apply_post_validators
from src.parser.claim_specification import (
    CLAIMED_QUANTITY_ROLES,
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
        )

        # --- Quantities ---
        fused_quantities = self._fuse_list_field(
            field="quantities",
            baseline_items=baseline.quantity_list(),
            llm_items=llm.quantity_list(),
            fuse_fn=self.authority.fuse_quantity,
            decisions_log=decisions_log,
        )
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

        # --- Territories ---
        final_result.territories = self._fuse_list_field(
            field="territories",
            baseline_items=baseline.territories,
            llm_items=llm.territories,
            fuse_fn=self.authority.fuse_territory,
            decisions_log=decisions_log,
        )

        # --- Populations ---
        final_result.populations = self._fuse_list_field(
            field="populations",
            baseline_items=baseline.populations,
            llm_items=llm.populations,
            fuse_fn=self.authority.fuse_population,
            decisions_log=decisions_log,
        )

        # --- Singular slots ---
        final_result.indicator = self._fuse_singular(
            field="indicator",
            baseline_item=baseline.indicator,
            llm_item=llm.indicator,
            fuse_fn=self.authority.fuse_indicator,
            decisions_log=decisions_log,
        )
        final_result.time_period = self._fuse_singular(
            field="time_period",
            baseline_item=baseline.time_period,
            llm_item=llm.time_period,
            fuse_fn=self.authority.fuse_time,
            decisions_log=decisions_log,
        )
        final_result.statistical_operation = self._fuse_singular(
            field="statistical_operation",
            baseline_item=baseline.statistical_operation,
            llm_item=llm.statistical_operation,
            fuse_fn=self.authority.fuse_operation,
            decisions_log=decisions_log,
        )
        final_result.expressed_frequency = self._fuse_singular(
            field="expressed_frequency",
            baseline_item=baseline.expressed_frequency,
            llm_item=llm.expressed_frequency,
            fuse_fn=self.authority.fuse_frequency,
            decisions_log=decisions_log,
        )
        final_result.adjustment = self._fuse_singular(
            field="adjustment",
            baseline_item=baseline.adjustment,
            llm_item=llm.adjustment,
            fuse_fn=self.authority.fuse_adjustment,
            decisions_log=decisions_log,
        )

        # Preserve non-fused slots from baseline preferentially
        final_result.expected_dimensions = list(
            baseline.expected_dimensions or llm.expected_dimensions
        )
        final_result.comparison = baseline.comparison or llm.comparison

        self._apply_post_validators(final_result, decisions_log)

        return final_result, decisions_log

    def _log_decision(
        self,
        decisions_log: List[Dict],
        field: str,
        auth_res: Dict[str, Any],
        align: Optional[Dict[str, Any]] = None,
        baseline_value: Any = None,
        llm_value: Any = None,
    ) -> None:
        entry: Dict[str, Any] = {
            "field": field,
            "baseline_value": (
                baseline_value.model_dump()
                if hasattr(baseline_value, "model_dump")
                else baseline_value
            ),
            "llm_value": (
                llm_value.model_dump()
                if hasattr(llm_value, "model_dump")
                else llm_value
            ),
            "decision": auth_res["decision"].value,
            "decision_type": auth_res["decision"].value,
            "explanation": auth_res["explanation"].value,
            "reason": auth_res["explanation"].value,
            "evidence": auth_res.get("evidence"),
        }
        if align is not None:
            entry["alignment_type"] = (
                align["alignment_type"].value
                if hasattr(align["alignment_type"], "value")
                else align["alignment_type"]
            )
            entry["score"] = align.get("score")
            rel = align.get("semantic_relation")
            if rel is not None:
                entry["semantic_relation"] = (
                    rel.value if hasattr(rel, "value") else rel
                )
        else:
            entry["alignment_type"] = "NOT_ALIGNED"
        decisions_log.append(entry)

    def _fuse_list_field(
        self,
        field: str,
        baseline_items: List,
        llm_items: List,
        fuse_fn,
        decisions_log: List[Dict],
    ) -> List:
        alignments = self.aligner.align(baseline_items, llm_items)
        matched_b, matched_l = set(), set()
        fused: List = []

        for align in alignments:
            matched_b.add(align["baseline_idx"])
            matched_l.add(align["llm_idx"])
            b_m, l_m = align["baseline_mention"], align["llm_mention"]
            auth_res = fuse_fn(b_m, l_m)
            if auth_res["result"] is not None:
                fused.append(auth_res["result"])
            self._log_decision(
                decisions_log,
                field,
                auth_res,
                align=align,
                baseline_value=b_m,
                llm_value=l_m,
            )

        for i, item in enumerate(baseline_items):
            if i not in matched_b:
                auth_res = fuse_fn(item, None)
                if auth_res["result"] is not None:
                    fused.append(auth_res["result"])
                self._log_decision(
                    decisions_log, field, auth_res, baseline_value=item, llm_value=None
                )

        for i, item in enumerate(llm_items):
            if i not in matched_l:
                auth_res = fuse_fn(None, item)
                if auth_res["result"] is not None:
                    fused.append(auth_res["result"])
                self._log_decision(
                    decisions_log, field, auth_res, baseline_value=None, llm_value=item
                )

        return fused

    def _fuse_singular(
        self,
        field: str,
        baseline_item,
        llm_item,
        fuse_fn,
        decisions_log: List[Dict],
    ):
        if baseline_item is None and llm_item is None:
            return None

        # Wrap as lists for alignment when both present
        if baseline_item is not None and llm_item is not None:
            aligns = self.aligner.align([baseline_item], [llm_item])
            if aligns:
                auth_res = fuse_fn(baseline_item, llm_item)
                self._log_decision(
                    decisions_log,
                    field,
                    auth_res,
                    align=aligns[0],
                    baseline_value=baseline_item,
                    llm_value=llm_item,
                )
                return auth_res["result"]
            # Below threshold — still apply authority (treat as paired by field)
            auth_res = fuse_fn(baseline_item, llm_item)
            self._log_decision(
                decisions_log,
                field,
                auth_res,
                baseline_value=baseline_item,
                llm_value=llm_item,
            )
            return auth_res["result"]

        auth_res = fuse_fn(baseline_item, llm_item)
        self._log_decision(
            decisions_log,
            field,
            auth_res,
            baseline_value=baseline_item,
            llm_value=llm_item,
        )
        return auth_res["result"]

    def _apply_post_validators(
        self, result: ClaimSpecification, decisions_log: List[Dict]
    ) -> None:
        _, reasons = apply_post_validators(result, decisions_log)
        decisions_log.append(
            {
                "field": "_status",
                "decision": result.parse_status.value,
                "decision_type": result.parse_status.value,
                "explanation": "POST_VALIDATORS",
                "reason": ";".join(reasons),
                "evidence": {"validator_reasons": reasons},
            }
        )
