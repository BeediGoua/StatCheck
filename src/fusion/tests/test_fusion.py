from src.parser.claim_specification import (
    ClaimSpecification,
    ClaimedQuantity,
    QuantityRole,
)
from src.fusion.alignment import BipartiteAligner, AlignmentType
from src.fusion.authority import AuthorityMatrix, DecisionType
from src.fusion.engine import FusionEngine


def test_bipartite_aligner():
    aligner = BipartiteAligner()
    b1 = ClaimedQuantity(
        original_label="chômage", span_offsets=(9, 16), role=QuantityRole.CURRENT_VALUE
    )
    l1 = ClaimedQuantity(
        original_label="taux de chômage",
        span_offsets=(0, 16),
        role=QuantityRole.CURRENT_VALUE,
    )
    results = aligner.align([b1], [l1])
    assert len(results) == 1
    # Nested spans → CONTAINS / CONTAINED_BY (stricter than bare OVERLAP)
    assert results[0]["alignment_type"] in (
        AlignmentType.OVERLAP,
        AlignmentType.CONTAINS,
        AlignmentType.CONTAINED_BY,
    )


def test_bipartite_aligner_reversed():
    aligner = BipartiteAligner()
    b1 = ClaimedQuantity(original_label="A", span_offsets=(0, 1))
    b2 = ClaimedQuantity(original_label="B", span_offsets=(2, 3))
    l1 = ClaimedQuantity(original_label="B", span_offsets=(2, 3))
    l2 = ClaimedQuantity(original_label="A", span_offsets=(0, 1))
    results = aligner.align([b1, b2], [l1, l2])
    assert len(results) == 2
    types = [r["alignment_type"] for r in results]
    assert types == [AlignmentType.EXACT, AlignmentType.EXACT]


def test_authority_matrix_role_conflict():
    b = ClaimedQuantity(
        original_label="8%",
        span_offsets=(0, 2),
        numeric_value=8.0,
        role=QuantityRole.CURRENT_VALUE,
    )
    l = ClaimedQuantity(
        original_label="8%",
        span_offsets=(0, 2),
        numeric_value=8.0,
        role=QuantityRole.THRESHOLD,
    )
    res = AuthorityMatrix.fuse_measure(b, l)
    assert res["decision"] == DecisionType.BOTH_RETAINED_AS_ALTERNATIVES


def test_fusion_engine_complete():
    engine = FusionEngine()
    qty = ClaimedQuantity(
        original_label="8%",
        span_offsets=(0, 2),
        numeric_value=8.0,
        role=QuantityRole.CURRENT_VALUE,
    )
    b = ClaimSpecification(
        claim_id="t", original_text="x", claimed_quantity=qty.model_copy(deep=True)
    )
    l = ClaimSpecification(
        claim_id="t", original_text="x", claimed_quantity=qty.model_copy(deep=True)
    )
    fused, log = engine.fuse(b, l)
    from src.parser.claim_specification import ParseStatus

    assert fused.parse_status == ParseStatus.COMPLETE
    assert fused.claimed_quantity is not None
    assert len(fused.quantity_list()) == 1


def test_fusion_engine_orphan():
    engine = FusionEngine()
    qty = ClaimedQuantity(
        original_label="8%",
        span_offsets=(0, 2),
        numeric_value=8.0,
        role=QuantityRole.CURRENT_VALUE,
    )
    b = ClaimSpecification(claim_id="t", original_text="x", claimed_quantity=qty)
    l = ClaimSpecification(claim_id="t", original_text="x")
    fused, log = engine.fuse(b, l)
    assert len(fused.quantity_list()) == 1
