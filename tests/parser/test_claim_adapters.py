"""Semantic adapter tests for ClaimSpecification V1."""
from src.parser.adapters.baseline_to_canonical import baseline_dict_to_claim_specification
from src.parser.adapters.llm_to_canonical import llm_result_to_claim_specification
from src.parser.claim_specification import (
    ExtractionProvenance,
    ParseStatus,
    QuantityApproximation,
    QuantityRole,
    QuantityScale,
)


def test_inflation_is_5_percent_baseline():
    baseline = {
        "claim_id": "c1",
        "identity": {"text": "L'inflation est de 5 %."},
        "subject": {"indicator": "inflation", "territory_main": "France"},
        "time": {},
        "measures": [
            {
                "value": 5.0,
                "unit": "PERCENT",
                "role": "CURRENT_VALUE",
                "span_text": "5 %",
                "start": 18,
                "end": 21,
            }
        ],
        "operation": {"type": "VALUE", "direction": "NONE", "polarity": "NONE"},
        "status": {"answerability": "VERIFIABLE"},
    }
    spec = baseline_dict_to_claim_specification(baseline)
    assert spec.indicator is not None
    assert "inflation" in (spec.indicator.original_label or "").lower()
    assert spec.claimed_quantity is not None
    assert spec.claimed_quantity.numeric_value == 5.0
    assert spec.claimed_quantity.unit in ("PERCENT", "%")
    assert spec.claimed_quantity.role == QuantityRole.CURRENT_VALUE
    assert spec.statistical_operation is not None
    assert spec.statistical_operation.canonical_value == "VALUE"
    assert spec.parse_status == ParseStatus.ACCEPTED


def test_unemployment_down_20_percent_since_2020():
    baseline = {
        "claim_id": "c2",
        "identity": {"text": "Le chômage a baissé de 20 % depuis 2020."},
        "subject": {"indicator": "chômage", "territory_main": "France"},
        "time": {
            "period_relative": "depuis 2020",
            "period_explicit": None,
            "granularity": "YEAR",
            "start_date": "2020",
        },
        "measures": [
            {
                "value": 20.0,
                "unit": "PERCENT",
                "role": "RELATIVE_CHANGE",
                "span_text": "20 %",
            }
        ],
        "operation": {"type": "RELATIVE_CHANGE", "direction": "DOWN", "polarity": "NEGATIVE"},
        "status": {"answerability": "VERIFIABLE"},
    }
    spec = baseline_dict_to_claim_specification(baseline)
    assert spec.claimed_quantity is not None
    assert spec.claimed_quantity.numeric_value == 20.0
    assert spec.claimed_quantity.role == QuantityRole.RELATIVE_CHANGE
    assert spec.time_period is not None
    assert spec.time_period.is_relative is True
    assert spec.statistical_operation is not None
    assert spec.statistical_operation.canonical_value == "RELATIVE_CHANGE"


def test_rate_from_8_to_7_reference_quantities():
    baseline = {
        "claim_id": "c3",
        "identity": {"text": "Le taux est passé de 8 % à 7 %."},
        "subject": {"indicator": "taux", "territory_main": "France"},
        "measures": [
            {"value": 8.0, "unit": "PERCENT", "role": "START_VALUE", "span_text": "8 %"},
            {"value": 7.0, "unit": "PERCENT", "role": "END_VALUE", "span_text": "7 %"},
        ],
        "operation": {"type": "POINT_CHANGE", "direction": "DOWN", "polarity": "NEGATIVE"},
        "status": {"answerability": "VERIFIABLE"},
    }
    spec = baseline_dict_to_claim_specification(baseline)
    roles = {q.role for q in spec.reference_quantities}
    assert QuantityRole.START_VALUE in roles
    assert QuantityRole.END_VALUE in roles
    values = {q.role: q.numeric_value for q in spec.reference_quantities}
    assert values[QuantityRole.START_VALUE] == 8.0
    assert values[QuantityRole.END_VALUE] == 7.0


def test_ambiguous_territory_via_adapter():
    baseline = {
        "claim_id": "c4",
        "identity": {"text": "Le chômage a baissé en Bourgogne."},
        "subject": {
            "indicator": "chômage",
            "territory_main": "Bourgogne",
            "territory_alternatives": ["Bourgogne", "Bourgogne-Franche-Comté"],
            "territory_status": "AMBIGUOUS",
        },
        "measures": [{"value": 1.0, "unit": "PERCENT", "role": "CURRENT_VALUE"}],
        "operation": {"type": "VALUE", "direction": "NONE"},
        "status": {"answerability": "VERIFIABLE"},
    }
    spec = baseline_dict_to_claim_specification(baseline)
    assert any(a.field == "territories" for a in spec.ambiguities)
    assert spec.parse_status == ParseStatus.AMBIGUOUS


def test_ambiguous_population_via_adapter():
    baseline = {
        "claim_id": "c5",
        "identity": {"text": "Le chômage des jeunes a baissé."},
        "subject": {
            "indicator": "chômage",
            "population": "jeunes",
            "population_alternatives": ["15-24", "15-29"],
            "territory_main": "France",
        },
        "measures": [{"value": 1.0, "unit": "PERCENT", "role": "CURRENT_VALUE"}],
        "operation": {"type": "VALUE", "direction": "NONE"},
        "status": {"answerability": "VERIFIABLE"},
    }
    spec = baseline_dict_to_claim_specification(baseline)
    assert any(a.field == "populations" for a in spec.ambiguities)
    assert spec.parse_status == ParseStatus.AMBIGUOUS
    assert len(spec.populations) == 1


def test_missing_indicator_not_accepted():
    baseline = {
        "claim_id": "c6",
        "identity": {"text": "Ça a augmenté de 3 %."},
        "subject": {"indicator": None, "territory_main": "France"},
        "measures": [{"value": 3.0, "unit": "PERCENT", "role": "CURRENT_VALUE"}],
        "operation": {"type": "VALUE", "direction": "UP"},
        "status": {"answerability": "VERIFIABLE"},
    }
    spec = baseline_dict_to_claim_specification(baseline)
    assert spec.indicator is None
    assert spec.parse_status != ParseStatus.ACCEPTED
    assert any(a.field == "indicator" for a in spec.ambiguities)


def test_llm_adapter_maps_measures_and_indicator():
    llm = {
        "schema_version": "1",
        "parse_status": "COMPLETE",
        "indicators": [
            {"source_text": "inflation", "normalized_label": "INFLATION", "certainty": "EXPLICIT"}
        ],
        "populations": [],
        "territories": [
            {"source_text": "France", "normalized_label": "FR", "certainty": "EXPLICIT"}
        ],
        "time_expressions": [],
        "measures": [
            {
                "source_text": "5 %",
                "numeric_value": 5.0,
                "unit": "PERCENT",
                "role": "CURRENT_VALUE",
            }
        ],
        "operation": {"type": "VALUE", "direction": None, "polarity": None},
        "frequency": None,
        "adjustment": None,
        "comparisons": [],
        "ambiguities": [],
        "missing_context": [],
    }
    spec = llm_result_to_claim_specification(
        llm, claim_id="llm1", original_text="L'inflation est de 5 %."
    )
    assert spec.indicator is not None
    assert spec.indicator.canonical_value == "INFLATION"
    assert spec.claimed_quantity is not None
    assert spec.claimed_quantity.numeric_value == 5.0
    assert spec.parse_status == ParseStatus.ACCEPTED


def test_approx_20_percent_preserved():
    llm = {
        "parse_status": "COMPLETE",
        "indicators": [{"source_text": "inflation", "normalized_label": "INFLATION", "certainty": "EXPLICIT"}],
        "populations": [],
        "territories": [],
        "time_expressions": [],
        "measures": [
            {
                "source_text": "environ 20 %",
                "numeric_value": 20.0,
                "unit": "PERCENT",
                "role": "CURRENT_VALUE",
                "approximation": "APPROXIMATELY",
                "scale": "NONE",
                "certainty": "EXPLICIT",
            }
        ],
        "operation": None,
        "comparisons": [],
        "ambiguities": [],
        "missing_context": [],
    }
    spec = llm_result_to_claim_specification(llm, "c", "L'inflation est environ 20 %.")
    assert spec.claimed_quantity is not None
    assert spec.claimed_quantity.approximation == QuantityApproximation.APPROXIMATELY


def test_scale_millions_preserved():
    llm = {
        "parse_status": "COMPLETE",
        "indicators": [{"source_text": "emplois", "normalized_label": "EMPLOIS", "certainty": "EXPLICIT"}],
        "populations": [],
        "territories": [],
        "time_expressions": [],
        "measures": [
            {
                "source_text": "5 millions",
                "numeric_value": 5.0,
                "unit": "COUNT",
                "role": "CURRENT_VALUE",
                "scale": "MILLION",
                "approximation": "EXACT",
                "certainty": "EXPLICIT",
            }
        ],
        "operation": None,
        "comparisons": [],
        "ambiguities": [],
        "missing_context": [],
    }
    spec = llm_result_to_claim_specification(llm, "c", "Il y a 5 millions d'emplois.")
    assert spec.claimed_quantity is not None
    assert spec.claimed_quantity.scale == QuantityScale.MILLION


def test_at_least_10_percent_preserved():
    llm = {
        "parse_status": "COMPLETE",
        "indicators": [{"source_text": "inflation", "normalized_label": "INFLATION", "certainty": "EXPLICIT"}],
        "populations": [],
        "territories": [],
        "time_expressions": [],
        "measures": [
            {
                "source_text": "au moins 10 %",
                "numeric_value": 10.0,
                "unit": "PERCENT",
                "role": "CURRENT_VALUE",
                "approximation": "AT_LEAST",
                "certainty": "EXPLICIT",
            }
        ],
        "operation": None,
        "comparisons": [],
        "ambiguities": [],
        "missing_context": [],
    }
    spec = llm_result_to_claim_specification(llm, "c", "L'inflation est d'au moins 10 %.")
    assert spec.claimed_quantity is not None
    assert spec.claimed_quantity.approximation == QuantityApproximation.AT_LEAST


def test_bounded_quantity_preserved():
    llm = {
        "parse_status": "COMPLETE",
        "indicators": [{"source_text": "inflation", "normalized_label": "INFLATION", "certainty": "EXPLICIT"}],
        "populations": [],
        "territories": [],
        "time_expressions": [],
        "measures": [
            {
                "source_text": "entre 4 et 6 %",
                "numeric_value": None,
                "lower_bound": 4.0,
                "upper_bound": 6.0,
                "unit": "PERCENT",
                "role": "CURRENT_VALUE",
                "approximation": "BETWEEN",
                "certainty": "EXPLICIT",
            }
        ],
        "operation": None,
        "comparisons": [],
        "ambiguities": [],
        "missing_context": [],
    }
    spec = llm_result_to_claim_specification(llm, "c", "L'inflation est entre 4 et 6 %.")
    assert spec.claimed_quantity is not None
    assert spec.claimed_quantity.lower_bound == 4.0
    assert spec.claimed_quantity.upper_bound == 6.0
    assert spec.claimed_quantity.approximation == QuantityApproximation.BETWEEN


def test_inferred_territory_provenance_not_explicit():
    baseline = {
        "claim_id": "g",
        "identity": {"text": "Le chômage a baissé."},
        "subject": {
            "indicator": "chômage",
            "territory_main": "France",
            "territory_status": "INFERRED",
        },
        "measures": [{"value": 1.0, "unit": "PERCENT", "role": "CURRENT_VALUE"}],
        "operation": {"type": "VALUE", "direction": "NONE"},
        "status": {"answerability": "VERIFIABLE"},
    }
    spec = baseline_dict_to_claim_specification(baseline)
    assert len(spec.territories) == 1
    assert spec.territories[0].provenance != ExtractionProvenance.EXPLICIT_TEXT
    assert spec.territories[0].provenance == ExtractionProvenance.INFERRED


def test_explicit_territory_provenance():
    baseline = {
        "claim_id": "h",
        "identity": {"text": "Le chômage a baissé en France."},
        "subject": {
            "indicator": "chômage",
            "territory_main": "France",
            "territory_status": "EXPLICIT",
        },
        "measures": [{"value": 1.0, "unit": "PERCENT", "role": "CURRENT_VALUE"}],
        "operation": {"type": "VALUE", "direction": "NONE"},
        "status": {"answerability": "VERIFIABLE"},
    }
    spec = baseline_dict_to_claim_specification(baseline)
    assert spec.territories[0].provenance == ExtractionProvenance.EXPLICIT_TEXT

