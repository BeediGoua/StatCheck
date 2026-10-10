"""C3 cascade: CALL_LLM vs BASELINE_ONLY; fusion may stay non-COMPLETE."""

from src.evaluation.orchestrator import EvaluationOrchestrator
from src.evaluation.router import C3Router
from src.parser.claim_specification import (
    ClaimSlot,
    ClaimSpecification,
    ClaimedQuantity,
    ParseStatus,
    PresenceStatus,
    QuantityRole,
)


def _sufficient(**overrides):
    base = dict(
        claim_id="c3",
        original_text="L'inflation est de 5%.",
        parse_status=ParseStatus.ACCEPTED,
        indicator=ClaimSlot(canonical_value="inflation", original_label="inflation"),
        territories=[
            ClaimSlot(
                canonical_value="France",
                original_label="France",
                presence=PresenceStatus.EXPLICIT,
            )
        ],
        claimed_quantity=ClaimedQuantity(
            original_label="5%",
            numeric_value=5.0,
            unit="PERCENT",
            role=QuantityRole.CURRENT_VALUE,
            span_offsets=(18, 20),
        ),
        statistical_operation=ClaimSlot(canonical_value="VALUE", original_label="est"),
    )
    base.update(overrides)
    return ClaimSpecification(**base)


def test_c3_baseline_sufficient_no_llm():
    """Case 10 — baseline sufficient → BASELINE_ONLY."""
    b = _sufficient()
    route = C3Router.should_call_llm(b, "L'inflation est de 5%.")
    assert route["trigger"] is False
    assert route["route"] == "BASELINE_ONLY"

    orch = EvaluationOrchestrator()
    out = orch.evaluate_c3_cascade(
        ["L'inflation est de 5%."],
        [b],
        [_sufficient()],  # LLM unused when baseline-only
    )
    # Control sample may still call LLM (~5%); check route_log for non-control
    non_control = [r for r in out["route_log"] if not r["control_sample"]]
    assert non_control[0]["route"] == "BASELINE_ONLY"
    assert out["results"][0].parse_status == ParseStatus.ACCEPTED


def test_c3_ambiguous_baseline_calls_llm():
    """Case 11 — ambiguous baseline → CALL_LLM."""
    b = _sufficient(parse_status=ParseStatus.AMBIGUOUS)
    route = C3Router.should_call_llm(b, "L'inflation est de 5%.")
    assert route["trigger"] is True
    assert route["route"] == "CALL_LLM"


def test_c3_fusion_remains_non_complete():
    """Case 12 — CALL_LLM + conflicting fusion → not promoted to COMPLETE."""
    b = _sufficient(
        parse_status=ParseStatus.PARTIAL,
        claimed_quantity=ClaimedQuantity(
            original_label="5%",
            numeric_value=5.0,
            unit="PERCENT",
            role=QuantityRole.CURRENT_VALUE,
            span_offsets=(18, 20),
            validation_status="ACCEPTED",
            confidence=1.0,
        ),
    )
    l = _sufficient(
        claimed_quantity=ClaimedQuantity(
            original_label="5%",
            numeric_value=5.0,
            unit="PERCENTAGE_POINT",
            role=QuantityRole.CURRENT_VALUE,
            span_offsets=(18, 20),
            validation_status="ACCEPTED",
            confidence=1.0,
        ),
    )
    orch = EvaluationOrchestrator()
    out = orch.evaluate_c3_cascade(
        ["L'inflation est de 5%."],
        [b],
        [l],
    )
    assert out["route_log"][0]["route"] == "CALL_LLM"
    assert out["results"][0].parse_status != ParseStatus.COMPLETE
    assert out["results"][0].parse_status == ParseStatus.CONTRADICTION
    assert out["route_log"][0]["fusion_exit_reason"] is not None
