"""Structural validation for Micro-Gold V0 (Session 4)."""

from __future__ import annotations

from src.engine.calculator import Calculator
from src.gold.micro_gold_v0 import (
    EXPECTED_CLAIM_IDS,
    FROZEN_CLAIMS,
    AnswerabilityStatus,
    ComputationOperation,
    ExpectedVerdict,
    GoldStatus,
    VerificationStatus,
    load_micro_gold_v0,
)
from src.models.observation import Observation


TOLERANCE = 0.05


def _cases():
    return load_micro_gold_v0()


def test_exactly_twelve_unique_ids():
    cases = _cases()
    ids = [c.claim_id for c in cases]
    assert len(ids) == 12
    assert len(set(ids)) == 12
    assert tuple(sorted(ids)) == tuple(sorted(EXPECTED_CLAIM_IDS))


def test_frozen_claim_texts():
    for case in _cases():
        assert case.claim == FROZEN_CLAIMS[case.claim_id]


def test_all_candidate_never_validated():
    for case in _cases():
        assert case.gold_status == GoldStatus.CANDIDATE
        assert case.gold_status.value != "VALIDATED"


def test_answerability_distribution():
    statuses = {c.claim_id: c.answerability.status for c in _cases()}
    assert statuses["MG004"] == AnswerabilityStatus.AMBIGUOUS
    assert statuses["MG005"] == AnswerabilityStatus.INSUFFICIENT
    found = [c for c in _cases() if c.answerability.status == AnswerabilityStatus.FOUND]
    assert len(found) >= 8


def test_found_requires_grounding_obs_computation_verdict():
    for case in _cases():
        if case.answerability.status != AnswerabilityStatus.FOUND:
            continue
        g = case.expected_grounding
        assert g.dataset_id
        assert g.idbank or g.series_id
        assert case.expected_observations
        assert case.expected_computation.operation != ComputationOperation.NONE
        assert case.expected_computation.result is not None
        assert case.expected_verdict in (
            ExpectedVerdict.SUPPORTED,
            ExpectedVerdict.REFUTED,
        )


def test_ambiguous_and_insufficient_have_ambiguities():
    for case in _cases():
        if case.answerability.status in (
            AnswerabilityStatus.AMBIGUOUS,
            AnswerabilityStatus.INSUFFICIENT,
        ):
            assert case.ambiguities
            assert case.expected_verdict in (
                ExpectedVerdict.INSUFFICIENT_EVIDENCE,
                None,
            )


def test_mg001_mg002_have_revision_notes():
    by_id = {c.claim_id: c for c in _cases()}
    assert by_id["MG001"].provenance.revision_note
    assert by_id["MG002"].provenance.revision_note


def test_verdict_targets():
    by_id = {c.claim_id: c for c in _cases()}
    assert by_id["MG008"].expected_verdict == ExpectedVerdict.REFUTED
    assert by_id["MG011"].expected_verdict == ExpectedVerdict.REFUTED
    for cid in ("MG001", "MG002", "MG003", "MG006", "MG007", "MG009", "MG010", "MG012"):
        assert by_id[cid].expected_verdict == ExpectedVerdict.SUPPORTED


def _to_observations(case):
    return [
        Observation(
            period=o.period,
            value=o.value,
            dataflow_id=case.expected_grounding.dataset_id or "UNKNOWN",
            dimensions=dict(case.expected_dimensions or {}),
        )
        for o in case.expected_observations
    ]


def test_calculator_coherence_for_found():
    for case in _cases():
        if case.answerability.status != AnswerabilityStatus.FOUND:
            continue
        op = case.expected_computation.operation
        if op == ComputationOperation.NONE:
            continue
        obs = _to_observations(case)
        comp = case.expected_computation
        if op == ComputationOperation.VALUE:
            got = Calculator.get_value(obs, comp.period or "")
        elif op == ComputationOperation.POINT_CHANGE:
            got = Calculator.point_variation(
                obs, comp.start_period or "", comp.end_period or ""
            )
        elif op == ComputationOperation.RELATIVE_CHANGE:
            got = Calculator.relative_variation(
                obs, comp.start_period or "", comp.end_period or ""
            )
        elif op == ComputationOperation.RATIO:
            got = Calculator.ratio(
                obs, comp.start_period or "", comp.end_period or ""
            )
        elif op == ComputationOperation.SUM:
            got = Calculator.sum(obs)
        else:
            continue
        assert got is not None, f"{case.claim_id}: Calculator returned None"
        assert abs(got - float(comp.result)) <= TOLERANCE, (
            f"{case.claim_id}: Calculator {got} vs gold {comp.result}"
        )


def test_families_covered():
    families = {c.family for c in _cases()}
    assert "unemployment" in families
    assert "inflation" in families
    assert "population" in families or "births" in families
    assert "business_creation" in families


def test_every_case_has_verification_status():
    allowed = {s.value for s in VerificationStatus}
    for case in _cases():
        assert case.annotation.verification_status is not None
        assert case.annotation.verification_status.value in allowed
        assert case.annotation.verification_notes


def test_confirmed_or_corrected_found_require_idbank():
    for case in _cases():
        vs = case.annotation.verification_status
        if vs not in (
            VerificationStatus.CONFIRMED,
            VerificationStatus.CORRECTED,
        ):
            continue
        if case.answerability.status != AnswerabilityStatus.FOUND:
            continue
        assert case.expected_grounding.idbank, case.claim_id


def test_mg012_corrected_dual_vintage():
    by_id = {c.claim_id: c for c in _cases()}
    c = by_id["MG012"]
    assert c.gold_status == GoldStatus.CANDIDATE
    assert c.claim == FROZEN_CLAIMS["MG012"]
    assert c.annotation.verification_status == VerificationStatus.CORRECTED
    assert c.expected_grounding.idbank == "010755537"
    assert c.expected_grounding.series_id == "010755537"
    assert c.provenance.replaced_idbank == "001564301"
    assert c.expected_computation.operation == ComputationOperation.SUM
    assert c.expected_computation.result == 1165795
    monthly = [o for o in c.expected_observations if o.period.startswith("2025-")]
    assert len(monthly) == 12
    assert abs(sum(o.value for o in monthly) - 1165795) <= TOLERANCE
    pub = c.provenance.publication_value or ""
    assert "1165800" in pub
    assert "1165795" in pub
    rev = c.provenance.revised_series_value or ""
    assert "1165795" in rev
    assert float(c.expected_computation.result) != 1165800
