from src.parser.claim_specification import (
    ClaimSlot,
    ClaimSpecification,
    ClaimedQuantity,
    PresenceStatus,
    QuantityRole,
)
from src.evaluation.router import C3Router


def _sufficient_spec(**overrides):
    base = dict(
        claim_id="t",
        original_text="L'inflation est de 5%.",
        parse_status="ACCEPTED",
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
        ),
        statistical_operation=ClaimSlot(canonical_value="VALUE", original_label="est"),
    )
    base.update(overrides)
    return ClaimSpecification(**base)


def test_router_simple_sufficient():
    b = _sufficient_spec()
    route = C3Router.should_call_llm(b, "L'inflation est de 5%.")
    assert route["trigger"] is False
    assert route["reason"] == "BASELINE_SUFFICIENT"


def test_router_complex_trigger():
    b = _sufficient_spec()
    route = C3Router.should_call_llm(b, "L'inflation est de 5% chez les jeunes.")
    assert route["trigger"] is True
    assert "COMPLEXITY" in route["reason"]


def test_router_missing_indicator_trigger():
    b = _sufficient_spec(indicator=None)
    route = C3Router.should_call_llm(b, "C'est de 5%.")
    assert route["trigger"] is True
    assert route["reason"] == "NO_INDICATOR_FOUND"


def test_control_sample():
    assert C3Router.should_trigger_control_sample(True, 0.01) is True
    assert C3Router.should_trigger_control_sample(True, 0.99) is False
