"""Strict IR tests for ClaimSpecification V1 hardening."""
import pytest
from pydantic import ValidationError

from src.parser.claim_specification import (
    ClaimSpecification,
    ClaimedQuantity,
    ParseStatus,
    QuantityApproximation,
    QuantityRole,
    QuantityScale,
)


def test_rejects_legacy_indicators_field():
    with pytest.raises(ValidationError):
        ClaimSpecification(
            claim_id="t",
            original_text="x",
            indicators=[{"source_text": "inflation"}],  # type: ignore[call-arg]
        )


def test_rejects_legacy_measures_field():
    with pytest.raises(ValidationError):
        ClaimSpecification(
            claim_id="t",
            original_text="x",
            measures=[],  # type: ignore[call-arg]
        )


def test_rejects_typo_field():
    with pytest.raises(ValidationError):
        ClaimSpecification(
            claim_id="t",
            original_text="x",
            indicatros="typo",  # type: ignore[call-arg]
        )


def test_rejects_invalid_parse_status():
    with pytest.raises(ValidationError):
        ClaimSpecification(
            claim_id="t",
            original_text="x",
            parse_status="NOT_A_STATUS",  # type: ignore[arg-type]
        )


def test_claimed_quantity_rejects_extra_field():
    with pytest.raises(ValidationError):
        ClaimedQuantity(
            numeric_value=5.0,
            role=QuantityRole.CURRENT_VALUE,
            official_observation=8.0,  # type: ignore[call-arg]
        )


def test_rich_quantity_fields_accepted():
    q = ClaimedQuantity(
        original_label="environ 20 %",
        numeric_value=20.0,
        lower_bound=18.0,
        upper_bound=22.0,
        unit="PERCENT",
        scale=QuantityScale.NONE,
        role=QuantityRole.CURRENT_VALUE,
        approximation=QuantityApproximation.APPROXIMATELY,
        sign="+",
    )
    assert q.approximation == QuantityApproximation.APPROXIMATELY
    assert q.lower_bound == 18.0
    assert q.upper_bound == 22.0
