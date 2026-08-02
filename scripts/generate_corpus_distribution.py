import json
import logging
from collections import Counter
from src.db.database import SessionLocal
from src.models.evaluation import GoldAnnotation

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
LOGGER = logging.getLogger(__name__)

def generate_report():
    with SessionLocal() as session:
        annotations = session.query(GoldAnnotation).all()
        
        status_counts = Counter(a.expected_status for a in annotations)
        dataflow_counts = Counter(a.dataflow_id for a in annotations)
        
        has_allowed_defaults = sum(1 for a in annotations if a.allowed_defaults)
        has_forbidden_subs = sum(1 for a in annotations if a.forbidden_substitutions)
        has_ambiguities = sum(1 for a in annotations if a.ambiguities)
        has_limitations = sum(1 for a in annotations if a.limitations)
        has_time_window = sum(1 for a in annotations if a.time_window)
        
        report = {
            "total_annotations": len(annotations),
            "distribution_by_status": dict(status_counts),
            "distribution_by_dataflow": dict(dataflow_counts),
            "phenomenon_frequencies": {
                "allowed_defaults": has_allowed_defaults,
                "forbidden_substitutions": has_forbidden_subs,
                "ambiguities": has_ambiguities,
                "limitations": has_limitations,
                "time_window": has_time_window
            }
        }
        
        report_path = "docs/corpus_distribution_report.json"
        with open(report_path, "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
            
        LOGGER.info(f"Rapport de distribution généré dans {report_path}")

if __name__ == "__main__":
    generate_report()
