from typing import Any, Dict, List, Optional, Tuple

from src.evaluation.taxonomies import ErrorCategory
from src.parser.claim_specification import (
    ClaimSlot,
    ClaimSpecification,
    ClaimTime,
    ClaimedQuantity,
)


class BipartiteMatcher:
    """Appariement simple entre slots (offsets + label)."""

    @staticmethod
    def match(
        predictions: List[ClaimSlot], golds: List[ClaimSlot]
    ) -> List[Tuple[ClaimSlot, ClaimSlot]]:
        matches = []
        used_golds = set()

        for p in predictions:
            best_match = None
            for i, g in enumerate(golds):
                if i in used_golds:
                    continue
                if p.span_offsets == g.span_offsets and (p.original_label or "") == (
                    g.original_label or ""
                ):
                    best_match = i
                    break
            if best_match is not None:
                matches.append((p, golds[best_match]))
                used_golds.add(best_match)

        return matches


class TypedComparators:
    @staticmethod
    def compare_quantity(p: ClaimedQuantity, g: ClaimedQuantity) -> List[ErrorCategory]:
        errors = []
        if p.numeric_value is not None and g.numeric_value is not None:
            if abs(p.numeric_value - g.numeric_value) > 1e-5:
                errors.append(ErrorCategory.NUMERIC_VALUE_ERROR)
        elif p.numeric_value != g.numeric_value:
            errors.append(ErrorCategory.NUMERIC_VALUE_ERROR)

        if p.unit != g.unit:
            errors.append(ErrorCategory.UNIT_ERROR)
        if p.role != g.role:
            errors.append(ErrorCategory.MEASURE_ROLE_ERROR)
        return errors

    @staticmethod
    def compare_territory(p: ClaimSlot, g: ClaimSlot) -> List[ErrorCategory]:
        errors = []
        if p.canonical_value != g.canonical_value:
            errors.append(ErrorCategory.TERRITORY_CODE_ERROR)
        return errors

    @staticmethod
    def compare_time(p: ClaimTime, g: ClaimTime) -> List[ErrorCategory]:
        errors = []
        if p.start_date != g.start_date or p.end_date != g.end_date:
            errors.append(ErrorCategory.TEMPORAL_ERROR)
        return errors

    @staticmethod
    def compare_slot(p: ClaimSlot, g: ClaimSlot) -> List[ErrorCategory]:
        errors = []
        pl = (p.original_label or p.canonical_value or "").lower()
        gl = (g.original_label or g.canonical_value or "").lower()
        if pl != gl:
            errors.append(ErrorCategory.INDICATOR_NORMALIZATION_ERROR)
        return errors


class Scorer:
    """Moteur d'évaluation local sur ClaimSpecification V1."""

    def __init__(self):
        self.matcher = BipartiteMatcher()
        self.comparators = TypedComparators()

    def evaluate_prediction(
        self, prediction: ClaimSpecification, gold_canonical: ClaimSpecification
    ) -> Dict[str, Any]:
        all_errors: List[ErrorCategory] = []
        silent_critical_error = False

        pred_qty = prediction.quantity_list()
        gold_qty = gold_canonical.quantity_list()
        quantity_matches = self.matcher.match(pred_qty, gold_qty)

        tp_semantic = {
            "quantities": 0,
            "territories": 0,
            "indicator": 0,
            "populations": 0,
            "time_period": 0,
        }

        for p, g in quantity_matches:
            errors = self.comparators.compare_quantity(p, g)  # type: ignore[arg-type]
            if not errors:
                tp_semantic["quantities"] += 1
            all_errors.extend(errors)

        territory_matches = self.matcher.match(
            prediction.territories, gold_canonical.territories
        )
        for p, g in territory_matches:
            errors = self.comparators.compare_territory(p, g)
            if not errors:
                tp_semantic["territories"] += 1
            all_errors.extend(errors)

        pred_times = [prediction.time_period] if prediction.time_period else []
        gold_times = [gold_canonical.time_period] if gold_canonical.time_period else []
        time_matches = self.matcher.match(pred_times, gold_times)  # type: ignore[arg-type]
        for p, g in time_matches:
            errors = self.comparators.compare_time(p, g)  # type: ignore[arg-type]
            if not errors:
                tp_semantic["time_period"] += 1
            all_errors.extend(errors)

        pred_inds = [prediction.indicator] if prediction.indicator else []
        gold_inds = [gold_canonical.indicator] if gold_canonical.indicator else []
        ind_matches = self.matcher.match(pred_inds, gold_inds)  # type: ignore[arg-type]
        for p, g in ind_matches:
            errors = self.comparators.compare_slot(p, g)
            if not errors:
                tp_semantic["indicator"] += 1
            all_errors.extend(errors)

        pop_matches = self.matcher.match(
            prediction.populations, gold_canonical.populations
        )
        for p, g in pop_matches:
            errors = self.comparators.compare_slot(p, g)
            if not errors:
                tp_semantic["populations"] += 1
            all_errors.extend(errors)

        if prediction.parse_status in [
            "ACCEPTED",
            "ACCEPTED_WITH_WARNINGS",
            "ACCEPTED_WITH_CORRECTIONS",
            "COMPLETE",
        ]:
            critical_error_types = [
                ErrorCategory.NUMERIC_VALUE_ERROR,
                ErrorCategory.TERRITORY_CODE_ERROR,
                ErrorCategory.INDICATOR_NORMALIZATION_ERROR,
            ]
            if any(e in all_errors for e in critical_error_types):
                silent_critical_error = True
                all_errors.append(ErrorCategory.SILENT_CRITICAL_ERROR)

        def calc_f1(tp, fp, fn):
            p = tp / (tp + fp) if (tp + fp) > 0 else 0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0
            return 2 * (p * r) / (p + r) if (p + r) > 0 else 0

        metrics = {}
        for field, matches, pred_list, gold_list in [
            ("quantities", quantity_matches, pred_qty, gold_qty),
            ("territories", territory_matches, prediction.territories, gold_canonical.territories),
            ("time_period", time_matches, pred_times, gold_times),
            ("indicator", ind_matches, pred_inds, gold_inds),
            ("populations", pop_matches, prediction.populations, gold_canonical.populations),
        ]:
            tp_ex = len(matches)
            fp_ex = len(pred_list) - len(matches)
            fn_ex = len(gold_list) - len(matches)
            metrics[field] = {
                "exact_span": {
                    "tp": tp_ex,
                    "fp": fp_ex,
                    "fn": fn_ex,
                    "f1": calc_f1(tp_ex, fp_ex, fn_ex),
                },
                "semantic": {
                    "tp": tp_semantic[field],
                    "fp": fp_ex + (tp_ex - tp_semantic[field]),
                    "fn": fn_ex + (tp_ex - tp_semantic[field]),
                    "f1": calc_f1(
                        tp_semantic[field],
                        fp_ex + (tp_ex - tp_semantic[field]),
                        fn_ex + (tp_ex - tp_semantic[field]),
                    ),
                },
            }

        # Back-compat alias for older report code looking at "measures"
        metrics["measures"] = metrics["quantities"]

        is_exact_match = (len(all_errors) == 0) and all(
            m["exact_span"]["fp"] == 0 and m["exact_span"]["fn"] == 0
            for k, m in metrics.items()
            if k != "measures"
        )

        return {
            "is_exact_match": is_exact_match,
            "silent_critical_error": silent_critical_error,
            "detected_errors": [e.value for e in all_errors],
            "metrics": metrics,
        }
