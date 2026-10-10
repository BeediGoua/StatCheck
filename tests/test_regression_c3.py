from src.parser.claim_specification import (
    ClaimSlot,
    ClaimSpecification,
    ClaimTime,
    ClaimedQuantity,
    ParseStatus,
    PresenceStatus,
    QuantityRole,
)
from src.evaluation.router import C3Router


def _base(
    *,
    indicator_conf=1.0,
    with_time=False,
    relative_time=False,
    parse_status=ParseStatus.ACCEPTED,
):
    kwargs = dict(
        claim_id="t",
        original_text="",
        parse_status=parse_status,
        indicator=ClaimSlot(
            canonical_value="CHOMAGE",
            original_label="chômage",
            confidence=indicator_conf,
        ),
        territories=[
            ClaimSlot(
                canonical_value="France",
                original_label="France",
                presence=PresenceStatus.EXPLICIT,
                confidence=1.0,
            )
        ],
        claimed_quantity=ClaimedQuantity(
            original_label="2",
            numeric_value=2.0,
            unit="PERCENT",
            role=QuantityRole.CURRENT_VALUE,
        ),
        statistical_operation=ClaimSlot(
            canonical_value="DECREASE", original_label="baisse"
        ),
    )
    if with_time:
        kwargs["time_period"] = ClaimTime(
            original_label="depuis 15 ans" if relative_time else "en 2024",
            is_relative=relative_time,
            start_date=None if relative_time else "2024-01-01",
            end_date=None if relative_time else "2024-12-31",
        )
    return ClaimSpecification(**kwargs)


def test_router_should_call_llm_missing_mandatory_fields():
    baseline_result = ClaimSpecification(
        claim_id="t",
        original_text="Le taux de chômage a baissé.",
        parse_status=ParseStatus.ACCEPTED,
    )
    decision = C3Router.should_call_llm(baseline_result, "Le taux de chômage a baissé.")
    assert decision["trigger"] is True
    assert decision["reason"] == "NO_INDICATOR_FOUND"


def test_router_should_call_llm_percent_vs_pp_ambiguity():
    baseline_result = _base()
    text = "Le chômage a baissé de 2 points de pourcentage, pour atteindre 7%."
    decision = C3Router.should_call_llm(baseline_result, text)
    assert decision["trigger"] is True
    assert decision["reason"] == "POTENTIAL_PERCENT_VS_PP_CONFUSION"


def test_router_should_call_llm_relative_period():
    baseline_result = _base(with_time=True, relative_time=True)
    text = "Le chômage baisse depuis 15 ans."
    decision = C3Router.should_call_llm(baseline_result, text)
    assert decision["trigger"] is True
    assert decision["reason"] == "UNRESOLVED_RELATIVE_PERIOD"


def test_router_should_call_llm_low_confidence_indicator():
    baseline_result = _base(indicator_conf=0.5)
    text = "Le chômage baisse."
    decision = C3Router.should_call_llm(baseline_result, text)
    assert decision["trigger"] is True
    assert decision["reason"] == "LOW_CONFIDENCE_INDICATOR"


def test_router_should_not_call_llm_perfect_baseline():
    baseline_result = _base(with_time=True, relative_time=False)
    text = "En 2024, le chômage en France est de 2."
    decision = C3Router.should_call_llm(baseline_result, text)
    assert decision["trigger"] is False
    assert decision["reason"] == "BASELINE_SUFFICIENT"


if __name__ == "__main__":
    test_router_should_call_llm_missing_mandatory_fields()
    test_router_should_call_llm_percent_vs_pp_ambiguity()
    test_router_should_call_llm_relative_period()
    test_router_should_call_llm_low_confidence_indicator()
    test_router_should_not_call_llm_perfect_baseline()
    print("All tests passed!")
