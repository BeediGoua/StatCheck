import logging
from src.db.database import SessionLocal
from src.models.evaluation import GoldAnnotationKey, GoldAnnotation
from src.models.structure import AvailableSeriesKey
import src.models.catalogue
import src.models.sources
import src.models.series
import src.models.observation
import src.models.resolution_status
import src.models.retrieval_candidate
import src.models.sdmx_selection
import src.models.ingestion

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s — %(message)s")
LOGGER = logging.getLogger(__name__)

def validate_gold_corpus():
    with SessionLocal() as session:
        annotations = session.query(GoldAnnotation).all()
        invalid_keys = []
        valid_count = 0
        
        for annot in annotations:
            # On ne valide que si le statut attendu est "FOUND", car si c'est NOT_FOUND ou AMBIGUOUS,
            # la clé peut très bien ne pas exister.
            if annot.expected_status != "FOUND":
                continue
                
            keys = session.query(GoldAnnotationKey).filter_by(annotation_id=annot.id).all()
            for key in keys:
                # Vérifier si la clé existe dans available_series_keys pour ce snapshot et dataflow
                exists = session.query(AvailableSeriesKey).filter_by(
                    snapshot_id=annot.metadata_snapshot_id,
                    dataflow_id=annot.dataflow_id,
                    ordered_key=key.expected_ordered_key
                ).first()
                
                if exists:
                    valid_count += 1
                else:
                    invalid_keys.append({
                        "claim_id": str(annot.claim_id),
                        "dataflow_id": annot.dataflow_id,
                        "key": key.expected_ordered_key
                    })
                    
        LOGGER.info(f"Validation terminée. {valid_count} clés valides trouvées dans le snapshot.")
        if invalid_keys:
            LOGGER.warning(f"{len(invalid_keys)} clés invalides ou introuvables :")
            for inv in invalid_keys:
                LOGGER.warning(f" - {inv['dataflow_id']} | {inv['key']} (Claim: {inv['claim_id']})")
        else:
            LOGGER.info("Toutes les clés annotées avec le statut 'FOUND' existent dans le snapshot actuel !")

if __name__ == "__main__":
    validate_gold_corpus()
