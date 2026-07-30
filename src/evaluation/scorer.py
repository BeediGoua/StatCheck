from typing import Dict, Any, List, Tuple
from src.parser.canonical import (
    CanonicalParseResult, CanonicalMentionBase, CanonicalMeasure, 
    CanonicalTerritory, CanonicalTimeExpression
)
from src.evaluation.taxonomies import ErrorCategory, ErrorGravity

class BipartiteMatcher:
    """Implémente l'appariement optimal entre prédictions et gold."""
    @staticmethod
    def match(predictions: List[CanonicalMentionBase], golds: List[CanonicalMentionBase]) -> List[Tuple[CanonicalMentionBase, CanonicalMentionBase]]:
        matches = []
        used_golds = set()
        unmatched_preds = []
        
        # 1. Exact match strict (scope, offsets exacts, texte exact)
        for p in predictions:
            best_match = None
            for i, g in enumerate(golds):
                if i in used_golds:
                    continue
                if (p.source_scope == g.source_scope and 
                    p.offsets == g.offsets and 
                    p.source_text == g.source_text):
                    best_match = i
                    break
            if best_match is not None:
                matches.append((p, golds[best_match]))
                used_golds.add(best_match)
            else:
                unmatched_preds.append(p)
                
        # 2. Relaxed match (chevauchement d'offsets)
        # Pour une version V1 complète, un algorithme de graphe biparti pondéré (ex: Kuhn-Munkres) 
        # serait utilisé ici pour maximiser l'IoU (Intersection over Union).
        # On simule la logique en ignorant les relaxés pour cet exemple de structure.
        
        return matches

class TypedComparators:
    """Comparateurs spécifiques au type de mention (Nombre, Texte, Date)."""
    @staticmethod
    def compare_measure(p: CanonicalMeasure, g: CanonicalMeasure) -> List[ErrorCategory]:
        errors = []
        # Comparaison numérique tolérante aux flottants (ex: 3.5 vs 3.5000001)
        if p.value is not None and g.value is not None:
            if abs(p.value - g.value) > 1e-5:
                errors.append(ErrorCategory.NUMERIC_VALUE_ERROR)
        elif p.value != g.value:
            errors.append(ErrorCategory.NUMERIC_VALUE_ERROR)
            
        if p.unit != g.unit or p.scale != g.scale:
            errors.append(ErrorCategory.UNIT_ERROR)
        if p.role != g.role:
            errors.append(ErrorCategory.MEASURE_ROLE_ERROR)
        return errors
        
    @staticmethod
    def compare_territory(p: CanonicalTerritory, g: CanonicalTerritory) -> List[ErrorCategory]:
        errors = []
        if p.code != g.code or p.vintage != g.vintage:
            errors.append(ErrorCategory.TERRITORY_CODE_ERROR)
        return errors
        
    @staticmethod
    def compare_time(p: CanonicalTimeExpression, g: CanonicalTimeExpression) -> List[ErrorCategory]:
        errors = []
        if p.start_date != g.start_date or p.end_date != g.end_date:
            errors.append(ErrorCategory.TEMPORAL_ERROR)
        return errors

    @staticmethod
    def compare_base(p: CanonicalMentionBase, g: CanonicalMentionBase) -> List[ErrorCategory]:
        errors = []
        if p.source_text.lower() != g.source_text.lower():
            errors.append(ErrorCategory.INDICATOR_NORMALIZATION_ERROR) # Generic error for text mismatch
        return errors

class Scorer:
    """Moteur principal d'évaluation local durci."""
    def __init__(self):
        self.matcher = BipartiteMatcher()
        self.comparators = TypedComparators()

    def evaluate_prediction(self, prediction: CanonicalParseResult, gold_canonical: CanonicalParseResult) -> Dict[str, Any]:
        all_errors = []
        silent_critical_error = False
        
        # Evaluation par famille (Exemple sur les mesures)
        measure_matches = self.matcher.match(prediction.measures, gold_canonical.measures)
        
        # F1 Variables
        tp_exact = len(measure_matches)
        fp_exact = len(prediction.measures) - len(measure_matches)
        fn_exact = len(gold_canonical.measures) - len(measure_matches)
        
        tp_semantic = {"measures": 0, "territories": 0, "indicators": 0, "populations": 0, "time_expressions": 0}
        
        # 1. Measures
        for p, g in measure_matches:
            errors = self.comparators.compare_measure(p, g)
            if not errors:
                tp_semantic["measures"] += 1
            all_errors.extend(errors)
            
        # 2. Territories
        territory_matches = self.matcher.match(prediction.territories, gold_canonical.territories)
        for p, g in territory_matches:
            errors = self.comparators.compare_territory(p, g)
            if not errors:
                tp_semantic["territories"] += 1
            all_errors.extend(errors)
            
        # 3. Time
        time_matches = self.matcher.match(prediction.time_expressions, gold_canonical.time_expressions)
        for p, g in time_matches:
            errors = self.comparators.compare_time(p, g)
            if not errors:
                tp_semantic["time_expressions"] += 1
            all_errors.extend(errors)
            
        # 4. Indicators
        ind_matches = self.matcher.match(prediction.indicators, gold_canonical.indicators)
        for p, g in ind_matches:
            errors = self.comparators.compare_base(p, g)
            if not errors:
                tp_semantic["indicators"] += 1
            all_errors.extend(errors)
            
        # 5. Populations
        pop_matches = self.matcher.match(prediction.populations, gold_canonical.populations)
        for p, g in pop_matches:
            errors = self.comparators.compare_base(p, g)
            if not errors:
                tp_semantic["populations"] += 1
            all_errors.extend(errors)
            
        # Détection rigoureuse de l'erreur silencieuse :
        if prediction.parse_status in ["ACCEPTED", "ACCEPTED_WITH_WARNINGS", "ACCEPTED_WITH_CORRECTIONS"]:
            critical_error_types = [
                ErrorCategory.NUMERIC_VALUE_ERROR, 
                ErrorCategory.TERRITORY_CODE_ERROR,
                ErrorCategory.INDICATOR_NORMALIZATION_ERROR
            ]
            if any(e in all_errors for e in critical_error_types):
                silent_critical_error = True
                all_errors.append(ErrorCategory.SILENT_CRITICAL_ERROR)
                
        # Le F1 est un peu plus complexe (Précision/Rappel)
        def calc_f1(tp, fp, fn):
            p = tp / (tp + fp) if (tp + fp) > 0 else 0
            r = tp / (tp + fn) if (tp + fn) > 0 else 0
            return 2 * (p * r) / (p + r) if (p + r) > 0 else 0
            
        metrics = {}
        for field, matches, pred_list, gold_list in [
            ("measures", measure_matches, prediction.measures, gold_canonical.measures),
            ("territories", territory_matches, prediction.territories, gold_canonical.territories),
            ("time_expressions", time_matches, prediction.time_expressions, gold_canonical.time_expressions),
            ("indicators", ind_matches, prediction.indicators, gold_canonical.indicators),
            ("populations", pop_matches, prediction.populations, gold_canonical.populations)
        ]:
            tp_ex = len(matches)
            fp_ex = len(pred_list) - len(matches)
            fn_ex = len(gold_list) - len(matches)
            
            metrics[field] = {
                "exact_span": {"tp": tp_ex, "fp": fp_ex, "fn": fn_ex, "f1": calc_f1(tp_ex, fp_ex, fn_ex)},
                "semantic": {
                    "tp": tp_semantic[field], 
                    "fp": fp_ex + (tp_ex - tp_semantic[field]), 
                    "fn": fn_ex + (tp_ex - tp_semantic[field]),
                    "f1": calc_f1(tp_semantic[field], fp_ex + (tp_ex - tp_semantic[field]), fn_ex + (tp_ex - tp_semantic[field]))
                }
            }

        is_exact_match = (len(all_errors) == 0) and all(m["exact_span"]["fp"] == 0 and m["exact_span"]["fn"] == 0 for m in metrics.values())
        
        return {
            "is_exact_match": is_exact_match,
            "silent_critical_error": silent_critical_error,
            "detected_errors": [e.value for e in all_errors],
            "metrics": metrics
        }

