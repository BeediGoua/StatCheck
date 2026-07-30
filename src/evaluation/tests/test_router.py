import pytest
from src.parser.canonical import CanonicalParseResult, CanonicalIndicator, CanonicalMeasure
from src.evaluation.router import C3Router

def test_router_simple_sufficient():
    b = CanonicalParseResult(
        indicators=[CanonicalIndicator(source_text="inflation", origin="B")],
        measures=[CanonicalMeasure(source_text="5%", origin="B", role="CURRENT")],
        operation=[CanonicalMeasure(source_text="est", origin="B")] # Mock 
    )
    route = C3Router.should_call_llm(b, "L'inflation est de 5%.")
    assert route["trigger"] is False
    assert route["reason"] == "BASELINE_SUFFICIENT"

def test_router_complex_trigger():
    b = CanonicalParseResult(
        indicators=[CanonicalIndicator(source_text="inflation", origin="B")],
        measures=[CanonicalMeasure(source_text="5%", origin="B", role="CURRENT")],
        operation=[CanonicalMeasure(source_text="est", origin="B")]
    )
    route = C3Router.should_call_llm(b, "L'inflation est de 5% chez les jeunes.")
    assert route["trigger"] is True
    assert "COMPLEXITY" in route["reason"]
    
def test_router_missing_indicator_trigger():
    b = CanonicalParseResult(
        indicators=[],
        measures=[CanonicalMeasure(source_text="5%", origin="B", role="CURRENT")],
        operation=[CanonicalMeasure(source_text="est", origin="B")]
    )
    route = C3Router.should_call_llm(b, "C'est de 5%.")
    assert route["trigger"] is True
    assert route["reason"] == "NO_INDICATOR_FOUND"

def test_control_sample():
    # Avec un déclencheur false, l'échantillon de contrôle peut s'activer si random < threshold
    assert C3Router.should_trigger_control_sample(True, 0.01) is True
    assert C3Router.should_trigger_control_sample(True, 0.99) is False
