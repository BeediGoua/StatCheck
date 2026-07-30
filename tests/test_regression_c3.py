from src.parser.canonical import CanonicalParseResult, CanonicalIndicator, CanonicalTerritory, CanonicalMeasure, CanonicalTimeExpression
from src.evaluation.router import C3Router

def test_router_should_call_llm_missing_mandatory_fields():
    # Baseline finds nothing
    baseline_result = CanonicalParseResult(parse_status="ACCEPTED")
    text = "Le taux de chômage a baissé."
    
    decision = C3Router.should_call_llm(baseline_result, text)
    assert decision["trigger"] is True
    assert decision["reason"] == "NO_INDICATOR_FOUND"

def test_router_should_call_llm_percent_vs_pp_ambiguity():
    # Baseline finds a measure but the text contains "point" and "%"
    baseline_result = CanonicalParseResult(
        parse_status="ACCEPTED",
        indicators=[CanonicalIndicator(source_text="chômage", normalized_label="CHOMAGE", origin="BASELINE")],
        territories=[CanonicalTerritory(source_text="France", status="EXPLICIT", origin="BASELINE")],
        measures=[CanonicalMeasure(source_text="2", value=2.0, origin="BASELINE")],
        operation=[{"source_text": "baisse", "origin": "BASELINE"}]
    )
    text = "Le chômage a baissé de 2 points de pourcentage, pour atteindre 7%."
    
    decision = C3Router.should_call_llm(baseline_result, text)
    assert decision["trigger"] is True
    assert decision["reason"] == "POTENTIAL_PERCENT_VS_PP_CONFUSION"

def test_router_should_call_llm_relative_period():
    # Baseline finds relative period but no absolute dates
    baseline_result = CanonicalParseResult(
        parse_status="ACCEPTED",
        indicators=[CanonicalIndicator(source_text="chômage", normalized_label="CHOMAGE", origin="BASELINE")],
        territories=[CanonicalTerritory(source_text="France", status="EXPLICIT", origin="BASELINE")],
        measures=[CanonicalMeasure(source_text="2", value=2.0, origin="BASELINE")],
        operation=[{"source_text": "baisse", "origin": "BASELINE"}],
        time_expressions=[CanonicalTimeExpression(source_text="depuis 15 ans", is_relative=True, origin="BASELINE")]
    )
    text = "Le chômage baisse depuis 15 ans."
    
    decision = C3Router.should_call_llm(baseline_result, text)
    assert decision["trigger"] is True
    assert decision["reason"] == "UNRESOLVED_RELATIVE_PERIOD"

def test_router_should_call_llm_low_confidence_indicator():
    # Baseline finds indicator but with low confidence
    baseline_result = CanonicalParseResult(
        parse_status="ACCEPTED",
        indicators=[CanonicalIndicator(source_text="chômage", normalized_label="CHOMAGE", origin="BASELINE", confidence=0.5)],
        territories=[CanonicalTerritory(source_text="France", status="EXPLICIT", origin="BASELINE")],
        measures=[CanonicalMeasure(source_text="2", value=2.0, origin="BASELINE")],
        operation=[{"source_text": "baisse", "origin": "BASELINE"}],
    )
    text = "Le chômage baisse."
    
    decision = C3Router.should_call_llm(baseline_result, text)
    assert decision["trigger"] is True
    assert decision["reason"] == "LOW_CONFIDENCE_INDICATOR"

def test_router_should_not_call_llm_perfect_baseline():
    # Baseline is perfect
    baseline_result = CanonicalParseResult(
        parse_status="ACCEPTED",
        indicators=[CanonicalIndicator(source_text="chômage", normalized_label="CHOMAGE", origin="BASELINE", confidence=1.0)],
        territories=[CanonicalTerritory(source_text="France", status="EXPLICIT", origin="BASELINE", confidence=1.0)],
        measures=[CanonicalMeasure(source_text="2", value=2.0, origin="BASELINE", role="VALUE")],
        operation=[{"source_text": "baisse", "origin": "BASELINE"}],
        time_expressions=[CanonicalTimeExpression(source_text="en 2024", start_date="2024-01-01", end_date="2024-12-31", is_relative=False, origin="BASELINE")]
    )
    text = "En 2024, le chômage en France est de 2."
    
    decision = C3Router.should_call_llm(baseline_result, text)
    assert decision["trigger"] is False
    assert decision["reason"] == "BASELINE_SUFFICIENT"

if __name__ == '__main__':
    test_router_should_call_llm_missing_mandatory_fields()
    test_router_should_call_llm_percent_vs_pp_ambiguity()
    test_router_should_call_llm_relative_period()
    test_router_should_call_llm_low_confidence_indicator()
    test_router_should_not_call_llm_perfect_baseline()
    print("All tests passed!")
