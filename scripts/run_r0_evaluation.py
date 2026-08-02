import json
import logging
from collections import defaultdict
from src.db.database import SessionLocal
from src.models.corpus import Claim
from src.models.evaluation import GoldAnnotation, GoldAnnotationKey
from src.models.structure import DataflowDimension
from src.models.catalogue import Dataset
from src.models.sources import Source
from src.models.series import Series
from src.models.ingestion import IngestionRun
from sqlalchemy.orm import configure_mappers
configure_mappers()

# R0 Modules
from src.parser.baseline.baseline_parser import parse_claim_baseline
from src.parser.baseline.resolvers.exact_matcher import match_modality_exact
from src.parser.baseline.validators.structural_validator import validate_structural_integrity
from src.parser.baseline.key_builder import build_sdmx_key

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
LOGGER = logging.getLogger(__name__)

def run_r0_evaluation():
    with SessionLocal() as session:
        claims = session.query(Claim).filter_by(split_name="VALIDATION").all()
        
        metrics = {
            "total_claims": len(claims),
            "perfect_matches": 0,
            "expected_rejections": 0,
            "failures": {
                "nlp_extraction_failed": 0,
                "exact_match_failed": 0,
                "structural_validation_failed": 0,
                "wrong_key_generated": 0,
                "ambiguous_failure": 0
            }
        }
        
        failure_details = []

        for claim in claims:
            # Récupérer la vérité terrain
            gold = session.query(GoldAnnotation).filter_by(claim_id=claim.id).first()
            if not gold:
                continue
                
            expected_keys = [k.expected_ordered_key for k in session.query(GoldAnnotationKey).filter_by(annotation_id=gold.id).all()]
            dataflow_id = gold.dataflow_id
            snapshot_id = gold.metadata_snapshot_id
            
            # Étape 1 : Parseur Baseline
            # Note: The baseline parser might be imperfect. We extract terms.
            parsed = parse_claim_baseline(claim.text)
            
            # Si le parseur Baseline rejette la phrase pour ambiguïté ou manque de contexte
            if parsed["status"].get("answerability") in ["MISSING_CONTEXT", "AMBIGUOUS"]:
                if gold.expected_status in ["NOT_FOUND", "AMBIGUOUS"]:
                    metrics["expected_rejections"] += 1
                else:
                    metrics["failures"]["nlp_extraction_failed"] += 1
                    failure_details.append({
                        "claim_id": str(claim.id),
                        "text": claim.text,
                        "reason": "NLP Parser returned MISSING_CONTEXT or AMBIGUOUS unexpectedly."
                    })
                continue
                
            # Extraire les termes bruts trouvés par la baseline
            terms_to_match = []
            subj = parsed.get("subject", {})
            if subj.get("indicator") and subj["indicator"] != "UNKNOWN":
                terms_to_match.append(subj["indicator"])
            if subj.get("territory_main"):
                terms_to_match.append(subj["territory_main"])
            if subj.get("population") and subj["population"] != "UNKNOWN":
                terms_to_match.append(subj["population"])

            # Étape 2 : Exact Matcher (3.2)
            # On cherche ces termes sur toutes les dimensions du dataflow ciblé
            dimensions = session.query(DataflowDimension).filter_by(snapshot_id=snapshot_id, dataflow_id=dataflow_id).all()
            
            extracted_candidates = []
            for dim in dimensions:
                for term in terms_to_match:
                    matches = match_modality_exact(session, term, snapshot_id, dataflow_id, dim.dimension_id)
                    for m in matches:
                        m["dimension_id"] = dim.dimension_id
                        extracted_candidates.append(m)

            if not extracted_candidates and gold.expected_status == "FOUND":
                metrics["failures"]["exact_match_failed"] += 1
                failure_details.append({
                    "claim_id": str(claim.id),
                    "text": claim.text,
                    "reason": "Exact Matcher n'a trouvé aucun code pour les termes extraits."
                })
                continue

            # Étape 3 : Structural Validator (3.4)
            is_valid, rejection_reasons, structured_dims = validate_structural_integrity(
                session, snapshot_id, dataflow_id, extracted_candidates
            )
            
            if not is_valid:
                if gold.expected_status in ["NOT_FOUND", "AMBIGUOUS"]:
                    metrics["expected_rejections"] += 1
                else:
                    metrics["failures"]["structural_validation_failed"] += 1
                    failure_details.append({
                        "claim_id": str(claim.id),
                        "text": claim.text,
                        "reason": f"Validation Structurelle échouée : {rejection_reasons}"
                    })
                continue
                
            # Étape 4 : Key Builder (3.3)
            generated_key = build_sdmx_key(session, snapshot_id, dataflow_id, structured_dims)
            
            # Évaluation
            if gold.expected_status == "FOUND":
                if generated_key in expected_keys:
                    metrics["perfect_matches"] += 1
                else:
                    metrics["failures"]["wrong_key_generated"] += 1
                    failure_details.append({
                        "claim_id": str(claim.id),
                        "text": claim.text,
                        "expected": expected_keys,
                        "generated": generated_key,
                        "reason": "La clé générée ne correspond pas à la clé attendue."
                    })
            else:
                # La baseline a réussi à générer une clé alors qu'elle aurait dû échouer ou s'abstenir
                metrics["failures"]["ambiguous_failure"] += 1
                failure_details.append({
                    "claim_id": str(claim.id),
                    "text": claim.text,
                    "expected_status": gold.expected_status,
                    "generated": generated_key,
                    "reason": "Une clé a été générée alors que l'annotation attendait un rejet."
                })
                
        # Export du rapport
        report = {
            "metrics": metrics,
            "failure_details": failure_details
        }
        
        with open("docs/r0_evaluation_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, indent=4, ensure_ascii=False)
            
        LOGGER.info(f"Évaluation terminée. Perfect Matches: {metrics['perfect_matches']}, Échecs: {sum(metrics['failures'].values())}, Rejets attendus: {metrics['expected_rejections']}")

if __name__ == "__main__":
    run_r0_evaluation()
