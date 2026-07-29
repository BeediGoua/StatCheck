import sys
from pathlib import Path

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from src.db.database import engine, Base
# Importer tous les modèles pour que SQLAlchemy les enregistre avant la création
import src.models.sources
import src.models.catalogue
import src.models.structure
import src.models.series
import src.models.ingestion
import src.models.corpus
import src.models.nlp_runs

def init_db():
    print(f"Création des tables dans la base PostgreSQL...")
    try:
        Base.metadata.create_all(bind=engine)
        print("[OK] Tables créées avec succès !")
    except Exception as e:
        print(f"[ERREUR] lors de la création des tables : {e}")

if __name__ == "__main__":
    init_db()
