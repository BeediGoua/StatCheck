import pytest
from src.parser.llm.llm_parser import StatCheckLLMParser
from src.parser.llm.schemas.envelope import LLMInputEnvelope, ValidationStatus

# On simule un test avec le vrai LLM, mais on le "skip" s'il n'y a pas Ollama actif
# Pour la CI, ces tests pourraient nécessiter un mock.

@pytest.fixture
def parser():
    return StatCheckLLMParser(model_name="qwen2.5:latest")

@pytest.mark.skip(reason="Nécessite Ollama local en cours d'exécution.")
def test_prompt_negation_separee(parser):
    """Teste que le prompt gère bien la différence entre baisse et ne baisse pas."""
    env = LLMInputEnvelope(
        claim_id="test_1",
        claim_text="Le chômage ne baisse pas cette année.",
        language="fr"
    )
    result = parser.parse_claim(env)
    assert result.status == ValidationStatus.ACCEPTED
    
    # La polarité doit être NEGATED
    op = result.validated_data.get("operation")
    assert op is not None
    assert op.get("polarity") == "NEGATED"
    assert op.get("direction") == "DECREASE" # "baisse" -> DECREASE + NEGATED

@pytest.mark.skip(reason="Nécessite Ollama local en cours d'exécution.")
def test_prompt_absence_territoire(parser):
    """Teste que le prompt n'invente pas 'France' par défaut."""
    env = LLMInputEnvelope(
        claim_id="test_2",
        claim_text="L'inflation a atteint 5%.",
        language="fr"
    )
    result = parser.parse_claim(env)
    assert result.status == ValidationStatus.ACCEPTED
    assert len(result.validated_data.get("territories", [])) == 0

@pytest.mark.skip(reason="Nécessite Ollama local en cours d'exécution.")
def test_prompt_ratio(parser):
    """Teste la distinction d'un ratio."""
    env = LLMInputEnvelope(
        claim_id="test_3",
        claim_text="Un étudiant sur cinq est pauvre.",
        language="fr"
    )
    result = parser.parse_claim(env)
    assert result.status == ValidationStatus.ACCEPTED
    op = result.validated_data.get("operation")
    assert op is not None
    assert op.get("type") == "RATIO"
