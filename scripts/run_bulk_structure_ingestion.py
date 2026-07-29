import sys
import time
from pathlib import Path
from datetime import datetime

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.db.database import SessionLocal
from src.ingestion.structure_ingester import StructureIngester

import src.models.sources
import src.models.catalogue
import src.models.structure
import src.models.series
import src.models.ingestion
from src.models.catalogue import Dataset
from src.models.ingestion import IngestionRun, IngestionItem
from src.models.sources import Source

def main():
    print("=== Démarrage de la Généralisation des Structures (Lot 3C) ===")
    
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    
    try:
        source = db.query(Source).filter_by(code="INSEE_BDM").first()
        if not source:
            print("Erreur: Source INSEE_BDM introuvable.")
            return

        # 1. Création du Run global
        run = IngestionRun(
            source_id=source.id,
            ingestion_type="STRUCTURES_BULK",
            trigger_type="MANUAL",
            status="RUNNING"
        )
        db.add(run)
        db.commit()

        # 2. Récupération de tous les Datasets
        datasets = db.query(Dataset).filter_by(source_id=source.id, external_type="dataflow").all()
        total_datasets = len(datasets)
        
        print(f"Lancement de l'extraction pour l'ensemble du catalogue ({total_datasets} Datasets)...\n")
        
        ingester = StructureIngester(db)
        success_count = 0
        error_count = 0
        unchanged_count = 0
        
        for index, dataset in enumerate(datasets, start=1):
            print(f"[{index}/{total_datasets}] Traitement de {dataset.external_id}...")
            
            # Vérification de Reprise sur Erreur (a-t-on déjà réussi dans ce run ?)
            # S'il y a un plantage, l'utilisateur relance. On pourrait chercher dans les runs précédents,
            # mais ici l'idempotence via IngestionItem gère le run courant, et le "raw_hash" gère l'historique global de manière ultra-rapide.
            
            try:
                result = ingester.run_for_dataset(dataset.external_id, run.id)
                
                if result["status"] == "UNCHANGED":
                    print("  -> Idempotence (Aucun changement).")
                    unchanged_count += 1
                else:
                    print(f"  -> Succes ! {result['dimensions']} nouvelles dimensions et {result['modalities']} modalites ajoutees/mises a jour.")
                    success_count += 1
            
            except Exception as e:
                print(f"  -> [ERREUR] Echec pour {dataset.external_id} : {e}")
                error_count += 1
            
            # Délai de courtoisie API
            time.sleep(0.5)

        run.status = "SUCCESS" if error_count == 0 else "PARTIAL_SUCCESS"
        run.summary_message = f"{success_count} succes, {unchanged_count} inchanges, {error_count} erreurs."
        run.ended_at = datetime.utcnow()
        db.commit()

        print("\n=== Ingestion des structures terminee ===")
        print(run.summary_message)
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
