from src.parser.claim_specification import (
    ClaimSpecification,
    ClaimedQuantity,
    ParseStatus,
    QuantityRole,
)
from src.evaluation.scorer import Scorer
from src.evaluation.taxonomies import ErrorCategory


def _qty(val: float, role: QuantityRole, start: int = 0, end: int = 5) -> ClaimedQuantity:
    return ClaimedQuantity(
        original_label="test",
        span_offsets=(start, end),
        numeric_value=val,
        unit="%",
        role=role,
    )


def _spec_claimed(
    qty: ClaimedQuantity, status: ParseStatus = ParseStatus.ACCEPTED
) -> ClaimSpecification:
    return ClaimSpecification(
        claim_id="t",
        original_text="x",
        parse_status=status,
        claimed_quantity=qty,
    )


def test_perfect_match():
    scorer = Scorer()
    m1 = _qty(5.0, QuantityRole.CURRENT_VALUE)
    result = scorer.evaluate_prediction(_spec_claimed(m1), _spec_claimed(m1))
    assert result["is_exact_match"] is True
    assert result["silent_critical_error"] is False
    assert result["metrics"]["measures"]["exact_span"]["tp"] == 1
    assert result["metrics"]["measures"]["exact_span"]["fp"] == 0
    assert result["metrics"]["measures"]["exact_span"]["fn"] == 0


def test_reversed_order():
    scorer = Scorer()
    m1 = _qty(5.0, QuantityRole.CURRENT_VALUE, 0, 5)
    m2 = _qty(10.0, QuantityRole.START_VALUE, 10, 15)
    pred = ClaimSpecification(
        claim_id="t",
        original_text="x",
        parse_status=ParseStatus.ACCEPTED,
        claimed_quantity=m1,
        reference_quantities=[m2],
    )
    gold = ClaimSpecification(
        claim_id="t",
        original_text="x",
        claimed_quantity=m1,
        reference_quantities=[m2],
    )
    result = scorer.evaluate_prediction(pred, gold)
    assert result["is_exact_match"] is True


def test_missing_mention():
    scorer = Scorer()
    m1 = _qty(5.0, QuantityRole.CURRENT_VALUE)
    pred = ClaimSpecification(
        claim_id="t", original_text="x", parse_status=ParseStatus.ACCEPTED
    )
    result = scorer.evaluate_prediction(pred, _spec_claimed(m1))
    assert result["is_exact_match"] is False
    assert result["metrics"]["measures"]["exact_span"]["fn"] == 1


def test_extra_mention():
    scorer = Scorer()
    m1 = _qty(5.0, QuantityRole.CURRENT_VALUE)
    gold = ClaimSpecification(claim_id="t", original_text="x")
    result = scorer.evaluate_prediction(_spec_claimed(m1), gold)
    assert result["is_exact_match"] is False
    assert result["metrics"]["measures"]["exact_span"]["fp"] == 1


def test_same_text_bad_offset():
    scorer = Scorer()
    m1 = _qty(5.0, QuantityRole.CURRENT_VALUE, 0, 5)
    m2 = _qty(5.0, QuantityRole.CURRENT_VALUE, 10, 15)
    result = scorer.evaluate_prediction(_spec_claimed(m1), _spec_claimed(m2))
    assert result["is_exact_match"] is False
    assert result["metrics"]["measures"]["exact_span"]["fp"] == 1
    assert result["metrics"]["measures"]["exact_span"]["fn"] == 1


def test_good_span_bad_value():
    scorer = Scorer()
    result = scorer.evaluate_prediction(
        _spec_claimed(_qty(10.0, QuantityRole.CURRENT_VALUE)),
        _spec_claimed(_qty(5.0, QuantityRole.CURRENT_VALUE)),
    )
    assert result["is_exact_match"] is False
    assert ErrorCategory.NUMERIC_VALUE_ERROR.value in result["detected_errors"]
    assert result["silent_critical_error"] is True


def test_good_value_bad_role():
    scorer = Scorer()
    pred = ClaimSpecification(
        claim_id="t",
        original_text="x",
        parse_status=ParseStatus.ACCEPTED,
        reference_quantities=[_qty(5.0, QuantityRole.START_VALUE)],
    )
    gold = _spec_claimed(_qty(5.0, QuantityRole.CURRENT_VALUE))
    result = scorer.evaluate_prediction(pred, gold)
    assert result["is_exact_match"] is False
    assert ErrorCategory.MEASURE_ROLE_ERROR.value in result["detected_errors"]
    assert result["silent_critical_error"] is False


def test_rejected_result_is_not_silent_error():
    scorer = Scorer()
    result = scorer.evaluate_prediction(
        _spec_claimed(_qty(10.0, QuantityRole.CURRENT_VALUE), status=ParseStatus.REJECTED),
        _spec_claimed(_qty(5.0, QuantityRole.CURRENT_VALUE)),
    )
    assert result["is_exact_match"] is False
    assert result["silent_critical_error"] is False


def test_accepted_but_false_is_silent_error():
    scorer = Scorer()
    result = scorer.evaluate_prediction(
        _spec_claimed(
            _qty(10.0, QuantityRole.CURRENT_VALUE), status=ParseStatus.ACCEPTED
        ),
        _spec_claimed(_qty(5.0, QuantityRole.CURRENT_VALUE)),
    )
    assert result["silent_critical_error"] is True


def test_empty_fields():
    scorer = Scorer()
    pred = ClaimSpecification(
        claim_id="t", original_text="x", parse_status=ParseStatus.ACCEPTED
    )
    gold = ClaimSpecification(claim_id="t", original_text="x")
    result = scorer.evaluate_prediction(pred, gold)
    assert result["is_exact_match"] is True
    assert result["silent_critical_error"] is False
    assert result["metrics"]["measures"]["exact_span"]["tp"] == 0
