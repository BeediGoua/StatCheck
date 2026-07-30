import pytest
from src.parser.canonical import CanonicalMeasure, CanonicalParseResult, SourceScope
from src.fusion.alignment import BipartiteAligner, AlignmentType
from src.fusion.authority import AuthorityMatrix, DecisionType
from src.fusion.engine import FusionEngine

def test_bipartite_aligner():
    aligner = BipartiteAligner()
    b1 = CanonicalMeasure(source_text="chômage", offsets=(9, 16), origin="BASELINE")
    l1 = CanonicalMeasure(source_text="taux de chômage", offsets=(0, 16), origin="LLM")
    
    results = aligner.align([b1], [l1])
    assert len(results) == 1
    assert results[0]["alignment_type"] == AlignmentType.OVERLAP

def test_bipartite_aligner_reversed():
    aligner = BipartiteAligner()
    b1 = CanonicalMeasure(source_text="A", offsets=(0, 1), origin="B")
    b2 = CanonicalMeasure(source_text="B", offsets=(2, 3), origin="B")
    
    l1 = CanonicalMeasure(source_text="B", offsets=(2, 3), origin="L")
    l2 = CanonicalMeasure(source_text="A", offsets=(0, 1), origin="L")
    
    results = aligner.align([b1, b2], [l1, l2])
    assert len(results) == 2
    # Ensure they matched exactly despite reverse order
    types = [r["alignment_type"] for r in results]
    assert types == [AlignmentType.EXACT, AlignmentType.EXACT]

def test_authority_matrix_role_conflict():
    b = CanonicalMeasure(source_text="8%", offsets=(0, 2), origin="BASELINE", value=8.0, role="CURRENT")
    l = CanonicalMeasure(source_text="8%", offsets=(0, 2), origin="LLM", value=8.0, role="THRESHOLD")
    
    res = AuthorityMatrix.fuse_measure(b, l)
    assert res["decision"] == DecisionType.BOTH_RETAINED_AS_ALTERNATIVES
    
def test_fusion_engine_complete():
    engine = FusionEngine()
    b = CanonicalParseResult(measures=[CanonicalMeasure(source_text="8%", offsets=(0, 2), origin="B", value=8.0, role="C")])
    l = CanonicalParseResult(measures=[CanonicalMeasure(source_text="8%", offsets=(0, 2), origin="L", value=8.0, role="C")])
    
    fused, log = engine.fuse(b, l)
    assert fused.parse_status == "COMPLETE"
    assert len(fused.measures) == 1
    
def test_fusion_engine_orphan():
    engine = FusionEngine()
    b = CanonicalParseResult(measures=[CanonicalMeasure(source_text="8%", offsets=(0, 2), origin="B", value=8.0, role="C")])
    l = CanonicalParseResult(measures=[])
    
    fused, log = engine.fuse(b, l)
    assert len(fused.measures) == 1 # Baseline orphan is kept
