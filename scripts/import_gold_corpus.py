import json
import os
from datetime import datetime
from sqlalchemy.orm import Session
from src.db.database import SessionLocal, engine
import src.models.sources    # noqa
import src.models.catalogue  # noqa
import src.models.structure  # noqa
import src.models.series     # noqa
import src.models.ingestion  # noqa
from src.models.corpus import Claim, ClaimSemantic

def parse_date(date_str):
    if not date_str:
        return None
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return None

def import_gold_corpus():
    file_path = "data/corpus/corpus_complet.json"
    if not os.path.exists(file_path):
        print(f"Erreur : le fichier {file_path} n'existe pas.")
        return

    print("Chargement du corpus Gold...")
    with open(file_path, "r", encoding="utf-8") as f:
        corpus = json.load(f)

    db: Session = SessionLocal()
    
    # Pour s'assurer de l'idempotence, on pourrait vider les tables avant 
    # ou vérifier l'existence, on va vérifier par `original_claim_id` ou via text
    try:
        existing_claims = {c.text: c for c in db.query(Claim).all()}
        inserted_count = 0
        updated_count = 0

        for item in corpus:
            ann = item.get("annotation", {})
            identity = ann.get("identity", {})
            text = identity.get("text")
            
            if not text:
                continue
                
            claim = existing_claims.get(text)
            
            ref_date = parse_date(identity.get("reference_date"))
            split = item.get("split", "test")
            
            if not claim:
                claim = Claim(
                    text=text,
                    published_at=ref_date,
                    is_synthetic=item.get("claim_id", "").startswith("SYNTH-"),
                    url=None,
                    split_name=split
                )
                db.add(claim)
                db.flush() # pour avoir l'id
                existing_claims[text] = claim
                inserted_count += 1
            else:
                claim.published_at = ref_date
                claim.split_name = split
                updated_count += 1

            # On met à jour ClaimSemantic
            existing_semantic = db.query(ClaimSemantic).filter_by(claim_id=claim.id).first()
            if not existing_semantic:
                semantic = ClaimSemantic(
                    claim_id=claim.id,
                    full_json=ann
                )
                db.add(semantic)
            else:
                existing_semantic.full_json = ann

        db.commit()
        print(f"Import terminé ! Insérés: {inserted_count}, Mis à jour: {updated_count}.")

    except Exception as e:
        db.rollback()
        print(f"Erreur lors de l'import: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    import_gold_corpus()
