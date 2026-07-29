import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.db.database import SessionLocal
from src.ingestion.structure_ingester import StructureIngester

# Importation de tous les modèles pour la résolution des relations SQLAlchemy
import src.models.sources
import src.models.catalogue
import src.models.structure
import src.models.series
import src.models.ingestion

PILOTS = [
    "CHOMAGE-TRIM-NATIONAL",
    "NAISSANCES-FECONDITE",
    "IPC-2025",
    "POPULATION-STRUCTURE",
    "CREATIONS-ENTREPRISES-METHODE-2022"
]

def main():
    print("=== Démarrage de l'Ingestion des Structures (Lot 3B - Pilote) ===")
    
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    db = SessionLocal()
    
    try:
        ingester = StructureIngester(db)
        print(f"Lancement de l'extraction pour les {len(PILOTS)} Datasets Pilotes...\n")
        
        for index, dataset_id in enumerate(PILOTS, start=1):
            print(f"[{index}/{len(PILOTS)}] Traitement de {dataset_id}...")
            
            try:
                result = ingester.run_for_dataset(dataset_id)
                
                if result["status"] == "UNCHANGED":
                    print("  -> Idempotence (Aucun changement depuis la derniere execution).")
                else:
                    print(f"  -> Succes ! {result['dimensions']} nouvelles dimensions et {result['modalities']} modalites ajoutees/mises a jour.")
            
            except Exception as e:
                print(f"  -> [ERREUR] Echec pour {dataset_id} : {e}")

        print("\n=== Ingestion des structures terminee ===")
        
    finally:
        db.close()

if __name__ == "__main__":
    main()
