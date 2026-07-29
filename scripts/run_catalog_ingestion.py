import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.db.database import SessionLocal
from src.ingestion.catalog_ingester import CatalogIngester

# Importer tous les modeles pour la resolution des relations SQLAlchemy
import src.models.sources
import src.models.catalogue
import src.models.structure
import src.models.series
import src.models.ingestion

def main():
    print("=== Démarrage de l'Ingestion du Catalogue (Lot 3A) ===")
    
    # S'assurer que les dossiers de stockage existent
    Path("data/raw").mkdir(parents=True, exist_ok=True)
    
    db = SessionLocal()
    try:
        ingester = CatalogIngester(db)
        print("Lancement de la recuperation SDMX...")
        
        run = ingester.run()
        
        print("\n--- Resultat de l'Ingestion ---")
        print(f"Statut : {run.status}")
        print(f"Message : {run.summary_message}")
        print(f"Taille telechargee : {run.download_size_bytes} octets")
        print(f"Datasets decouverts : {run.items_discovered}")
        print(f" - Nouveaux ajoutes : {run.items_created}")
        print(f" - Mis a jour : {run.items_updated}")
        print(f" - Inchanges : {run.items_unchanged}")
        print("-------------------------------")
        
    except Exception as e:
        print(f"[ERREUR CRITIQUE] L'ingestion a echoue : {e}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
