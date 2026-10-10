"""Adversarial fusion cases (Session 3) — in-memory Specs only."""

from src.fusion.authority import AuthorityMatrix, DecisionType, ExplanationCode
from src.fusion.engine import FusionEngine
from src.parser.claim_specification import (
    ClaimSlot,
    ClaimSpecification,
    ClaimTime,
    ClaimedQuantity,
    ParseStatus,
    PresenceStatus,
    QuantityApproximation,
    QuantityRole,
    QuantityScale,
)


def _qty(**kw):
    defaults = dict(
        original_label="8%",
        span_offsets=(0, 2),
        numeric_value=8.0,
        unit="PERCENT",
        scale=QuantityScale.NONE,
        role=QuantityRole.CURRENT_VALUE,
        approximation=QuantityApproximation.EXACT,
        sign=None,
        validation_status="ACCEPTED",
        confidence=1.0,
    )
    defaults.update(kw)
    return ClaimedQuantity(**defaults)


def _spec(qty=None, **kw):
    base = dict(
        claim_id="adv",
        original_text="Le chômage est de 8% en France.",
        indicator=ClaimSlot(
            canonical_value="UNEMPLOYMENT_RATE", original_label="chômage"
        ),
        claimed_quantity=qty,
        statistical_operation=ClaimSlot(
            canonical_value="VALUE", original_label="est"
        ),
    )
    base.update(kw)
    return ClaimSpecification(**base)


# --- 1–4 quantities ---


def test_quantity_full_agreement():
    b = _qty()
    l = _qty()
    res = AuthorityMatrix.fuse_quantity(b, l)
    assert res["decision"] == DecisionType.AGREEMENT
    assert "evidence" in res


def test_quantity_unit_mismatch_conflict():
    b = _qty(unit="PERCENT")
    l = _qty(unit="PERCENTAGE_POINT")
    res = AuthorityMatrix.fuse_quantity(b, l)
    assert res["decision"] == DecisionType.CONFLICT_UNRESOLVED
    assert res["explanation"] == ExplanationCode.UNIT_SCALE_MISMATCH


def test_quantity_scale_mismatch_conflict():
    b = _qty(scale=QuantityScale.NONE, unit=None, numeric_value=2.0, original_label="2")
    l = _qty(
        scale=QuantityScale.MILLION,
        unit=None,
        numeric_value=2.0,
        original_label="2 millions",
    )
    res = AuthorityMatrix.fuse_quantity(b, l)
    assert res["decision"] == DecisionType.CONFLICT_UNRESOLVED
    assert res["explanation"] == ExplanationCode.UNIT_SCALE_MISMATCH


def test_quantity_approximation_mismatch_conflict():
    b = _qty(approximation=QuantityApproximation.EXACT)
    l = _qty(approximation=QuantityApproximation.APPROXIMATELY)
    res = AuthorityMatrix.fuse_quantity(b, l)
    assert res["decision"] == DecisionType.CONFLICT_UNRESOLVED
    assert res["explanation"] == ExplanationCode.APPROXIMATION_MISMATCH


# --- 5–6 territories ---


def test_territory_agreement():
    b = ClaimSlot(canonical_value="FR", original_label="France", span_offsets=(20, 26))
    l = ClaimSlot(canonical_value="FR", original_label="France", span_offsets=(20, 26))
    res = AuthorityMatrix.fuse_territory(b, l)
    assert res["decision"] == DecisionType.AGREEMENT


def test_territory_same_surface_code_conflict():
    b = ClaimSlot(
        canonical_value="FR",
        original_label="France",
        span_offsets=(20, 26),
        presence=PresenceStatus.EXPLICIT,
    )
    l = ClaimSlot(
        canonical_value="FR-IDF",
        original_label="France",
        span_offsets=(20, 26),
        presence=PresenceStatus.EXPLICIT,
    )
    res = AuthorityMatrix.fuse_territory(b, l)
    assert res["decision"] == DecisionType.CONFLICT_UNRESOLVED
    assert res["explanation"] == ExplanationCode.CANONICAL_CODE_CONFLICT
    # Must NOT auto-win on EXPLICIT alone
    assert res["decision"] != DecisionType.BASELINE_SELECTED


# --- 7 population alternatives ---


def test_population_age_band_ambiguous():
    engine = FusionEngine()
    # Same span / near-identical surface so aligner pairs them; codes diverge.
    b = _spec(
        qty=_qty(),
        populations=[
            ClaimSlot(
                canonical_value="AGE_15_24",
                original_label="jeunes 15-24",
                span_offsets=(30, 42),
            )
        ],
    )
    l = _spec(
        qty=_qty(),
        populations=[
            ClaimSlot(
                canonical_value="AGE_15_29",
                original_label="jeunes 15-29",
                span_offsets=(30, 42),
            )
        ],
    )
    fused, log = engine.fuse(b, l)
    assert fused.parse_status == ParseStatus.AMBIGUOUS
    pop_decisions = [d for d in log if d["field"] == "populations"]
    assert any(
        d["decision_type"] == DecisionType.BOTH_RETAINED_AS_ALTERNATIVES.value
        for d in pop_decisions
    )


# --- 8 RELATIVE_CHANGE + percentage points ---


def test_relative_change_with_pp_contradiction():
    engine = FusionEngine()
    qty = _qty(
        unit="PERCENTAGE_POINT",
        role=QuantityRole.RELATIVE_CHANGE,
        numeric_value=2.0,
        original_label="2 points",
    )
    b = _spec(
        qty=qty.model_copy(deep=True),
        statistical_operation=ClaimSlot(
            canonical_value="RELATIVE_CHANGE", original_label="augmenté de"
        ),
    )
    l = _spec(
        qty=qty.model_copy(deep=True),
        statistical_operation=ClaimSlot(
            canonical_value="RELATIVE_CHANGE", original_label="augmenté de"
        ),
    )
    fused, log = engine.fuse(b, l)
    assert fused.parse_status == ParseStatus.CONTRADICTION
    assert any("RELATIVE_CHANGE" in w for w in fused.warnings) or any(
        a.reason == "RELATIVE_CHANGE_WITH_PERCENTAGE_POINTS" for a in fused.ambiguities
    )


# --- 9 missing indicator ---


def test_missing_indicator_partial():
    engine = FusionEngine()
    qty = _qty()
    b = ClaimSpecification(
        claim_id="adv",
        original_text="c'est 8%",
        indicator=None,
        claimed_quantity=qty.model_copy(deep=True),
    )
    l = ClaimSpecification(
        claim_id="adv",
        original_text="c'est 8%",
        indicator=None,
        claimed_quantity=qty.model_copy(deep=True),
    )
    fused, _ = engine.fuse(b, l)
    assert fused.parse_status == ParseStatus.PARTIAL
