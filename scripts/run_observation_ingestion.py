import sys
from pathlib import Path
from datetime import datetime

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.db.database import SessionLocal
from src.ingestion.observation_ingester import ObservationIngester

import src.models.sources
import src.models.catalogue
import src.models.structure
import src.models.series
import src.models.ingestion

from src.models.ingestion import IngestionRun
from src.models.sources import Source

PILOTS = [
    "CHOMAGE-TRIM-NATIONAL",
    "NAISSANCES-FECONDITE",
    "IPC-2025",
    "POPULATION-STRUCTURE",
    "CREATIONS-ENTREPRISES-METHODE-2022"
]

def main():
    print("=== Démarrage de l'Ingestion des Observations (Lot 3D - Pilotes) ===")
    
    Path("data/normalized/INSEE_BDM").mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    
    try:
        source = db.query(Source).filter_by(code="INSEE_BDM").first()
        
        run = IngestionRun(
            source_id=source.id,
            ingestion_type="DATA_PILOT",
            trigger_type="MANUAL",
            status="RUNNING"
        )
        db.add(run)
        db.commit()

        ingester = ObservationIngester(db)
        print(f"Lancement de l'extraction pour les {len(PILOTS)} Datasets Pilotes...\n")
        
        for index, dataset_id in enumerate(PILOTS, start=1):
            print(f"[{index}/{len(PILOTS)}] Traitement de {dataset_id}...")
            
            try:
                result = ingester.run_for_dataset(dataset_id, run.id)
                print(f"  -> Succes ! {result['series']} series et {result['observations']} observations integrees.")
            except Exception as e:
                print(f"  -> [ERREUR] Echec pour {dataset_id} : {e}")

        run.status = "SUCCESS"
        run.ended_at = datetime.utcnow()
        db.commit()

        print("\n=== Ingestion des observations terminee ===")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
