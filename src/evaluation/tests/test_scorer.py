import pytest
from src.parser.canonical import (
    CanonicalParseResult, CanonicalMeasure, SourceScope
)
from src.evaluation.scorer import Scorer
from src.evaluation.taxonomies import ErrorCategory

def create_base_measure(val: float, role: str, start: int=0, end: int=5) -> CanonicalMeasure:
    return CanonicalMeasure(
        source_text="test",
        offsets=(start, end),
        source_scope=SourceScope.CLAIM,
        origin="BASELINE",
        value=val,
        unit="%",
        scale=None,
        role=role
    )

def test_perfect_match():
    scorer = Scorer()
    m1 = create_base_measure(5.0, "CURRENT")
    pred = CanonicalParseResult(measures=[m1], parse_status="ACCEPTED")
    gold = CanonicalParseResult(measures=[m1])
    
    result = scorer.evaluate_prediction(pred, gold)
    assert result["is_exact_match"] is True
    assert result["silent_critical_error"] is False
    assert result["metrics"]["measures"]["exact_span"]["tp"] == 1
    assert result["metrics"]["measures"]["exact_span"]["fp"] == 0
    assert result["metrics"]["measures"]["exact_span"]["fn"] == 0

def test_reversed_order():
    scorer = Scorer()
    m1 = create_base_measure(5.0, "CURRENT", 0, 5)
    m2 = create_base_measure(10.0, "PREVIOUS", 10, 15)
    
    pred = CanonicalParseResult(measures=[m2, m1], parse_status="ACCEPTED")
    gold = CanonicalParseResult(measures=[m1, m2])
    
    result = scorer.evaluate_prediction(pred, gold)
    assert result["is_exact_match"] is True

def test_missing_mention():
    scorer = Scorer()
    m1 = create_base_measure(5.0, "CURRENT")
    pred = CanonicalParseResult(measures=[], parse_status="ACCEPTED")
    gold = CanonicalParseResult(measures=[m1])
    
    result = scorer.evaluate_prediction(pred, gold)
    assert result["is_exact_match"] is False
    assert result["metrics"]["measures"]["exact_span"]["fn"] == 1

def test_extra_mention():
    scorer = Scorer()
    m1 = create_base_measure(5.0, "CURRENT")
    pred = CanonicalParseResult(measures=[m1], parse_status="ACCEPTED")
    gold = CanonicalParseResult(measures=[])
    
    result = scorer.evaluate_prediction(pred, gold)
    assert result["is_exact_match"] is False
    assert result["metrics"]["measures"]["exact_span"]["fp"] == 1

def test_same_text_bad_offset():
    scorer = Scorer()
    m1 = create_base_measure(5.0, "CURRENT", 0, 5)
    m2 = create_base_measure(5.0, "CURRENT", 10, 15)
    
    pred = CanonicalParseResult(measures=[m1], parse_status="ACCEPTED")
    gold = CanonicalParseResult(measures=[m2])
    
    result = scorer.evaluate_prediction(pred, gold)
    assert result["is_exact_match"] is False
    assert result["metrics"]["measures"]["exact_span"]["fp"] == 1
    assert result["metrics"]["measures"]["exact_span"]["fn"] == 1

def test_good_span_bad_value():
    scorer = Scorer()
    pred_m = create_base_measure(10.0, "CURRENT")
    gold_m = create_base_measure(5.0, "CURRENT")
    
    pred = CanonicalParseResult(measures=[pred_m], parse_status="ACCEPTED")
    gold = CanonicalParseResult(measures=[gold_m])
    
    result = scorer.evaluate_prediction(pred, gold)
    assert result["is_exact_match"] is False
    assert ErrorCategory.NUMERIC_VALUE_ERROR.value in result["detected_errors"]
    assert result["silent_critical_error"] is True

def test_good_value_bad_role():
    scorer = Scorer()
    pred_m = create_base_measure(5.0, "PREVIOUS")
    gold_m = create_base_measure(5.0, "CURRENT")
    
    pred = CanonicalParseResult(measures=[pred_m], parse_status="ACCEPTED")
    gold = CanonicalParseResult(measures=[gold_m])
    
    result = scorer.evaluate_prediction(pred, gold)
    assert result["is_exact_match"] is False
    assert ErrorCategory.MEASURE_ROLE_ERROR.value in result["detected_errors"]
    assert result["silent_critical_error"] is False 

def test_rejected_result_is_not_silent_error():
    scorer = Scorer()
    pred_m = create_base_measure(10.0, "CURRENT")
    gold_m = create_base_measure(5.0, "CURRENT")
    
    pred = CanonicalParseResult(measures=[pred_m], parse_status="REJECTED")
    gold = CanonicalParseResult(measures=[gold_m])
    
    result = scorer.evaluate_prediction(pred, gold)
    assert result["is_exact_match"] is False
    assert result["silent_critical_error"] is False 

def test_accepted_but_false_is_silent_error():
    scorer = Scorer()
    pred_m = create_base_measure(10.0, "CURRENT")
    gold_m = create_base_measure(5.0, "CURRENT")
    
    pred = CanonicalParseResult(measures=[pred_m], parse_status="ACCEPTED_WITH_WARNINGS")
    gold = CanonicalParseResult(measures=[gold_m])
    
    result = scorer.evaluate_prediction(pred, gold)
    assert result["silent_critical_error"] is True

def test_empty_fields():
    scorer = Scorer()
    pred = CanonicalParseResult(parse_status="ACCEPTED")
    gold = CanonicalParseResult()
    
    result = scorer.evaluate_prediction(pred, gold)
    assert result["is_exact_match"] is True
    assert result["silent_critical_error"] is False
    assert result["metrics"]["measures"]["exact_span"]["tp"] == 0
