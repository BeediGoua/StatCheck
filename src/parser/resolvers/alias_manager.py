import logging
from typing import List
from sqlalchemy.orm import Session
from src.models.structure import DimensionAlias, DataflowModality
from src.parser.baseline.normalizer import normalize_text

LOGGER = logging.getLogger(__name__)

def seed_initial_aliases(session: Session):
    """
    Peuple la base de données avec des alias de départ contrôlés (source = MANUAL, review_status = APPROVED).
    Ceci permet de résoudre l'ambiguïté des notions vagues.
    """
    initial_aliases = [
        # Notion "jeunes"
        {"alias_text": "jeunes", "target_code": "Y15T24", "scope_type": "CONCEPT", "scope_value": "AGE"},
        {"alias_text": "jeunes", "target_code": "Y15T29", "scope_type": "CONCEPT", "scope_value": "AGE"},
        
        # Notion "seniors"
        {"alias_text": "seniors", "target_code": "Y55T64", "scope_type": "CONCEPT", "scope_value": "AGE"},
        {"alias_text": "seniors", "target_code": "Y50T64", "scope_type": "CONCEPT", "scope_value": "AGE"},
        
        # Notion "total"
        {"alias_text": "total", "target_code": "_T", "scope_type": "GLOBAL", "scope_value": None},
        {"alias_text": "total", "target_code": "T", "scope_type": "GLOBAL", "scope_value": None},
        {"alias_text": "ensemble", "target_code": "_T", "scope_type": "GLOBAL", "scope_value": None},
        {"alias_text": "ensemble", "target_code": "T", "scope_type": "GLOBAL", "scope_value": None}
    ]
    
    # On insère s'ils n'existent pas encore
    for alias_data in initial_aliases:
        exists = session.query(DimensionAlias).filter_by(
            alias_text=alias_data["alias_text"],
            target_code=alias_data["target_code"]
        ).first()
        
        if not exists:
            new_alias = DimensionAlias(
                scope_type=alias_data["scope_type"],
                scope_value=alias_data["scope_value"],
                alias_text=alias_data["alias_text"],
                target_code=alias_data["target_code"],
                source="MANUAL",
                review_status="APPROVED",
                confidence="HIGH"
            )
            session.add(new_alias)
            
    session.commit()
    LOGGER.info("Alias contrôlés initiaux seedés avec succès.")

def resolve_alias(
    session: Session, 
    text: str, 
    snapshot_id: str, 
    dataflow_id: str, 
    dimension_id: str
) -> List[DataflowModality]:
    """
    Traduit un texte flou (alias) vers les modalités réelles du dataflow.
    Si le dataflow propose plusieurs modalités valides pour l'alias (ex: Y15T24 ET Y15T29),
    cette fonction renvoie les deux, signalant ainsi une ambiguïté irréductible.
    """
    if not text:
        return []
        
    norm_text = normalize_text(text)["matching_normalized_text"]
    
    # 1. Chercher tous les target_codes liés à cet alias (approuvés uniquement)
    aliases = session.query(DimensionAlias).filter(
        DimensionAlias.alias_text == norm_text,
        DimensionAlias.review_status == "APPROVED"
    ).all()
    
    if not aliases:
        return []
        
    target_codes = [a.target_code for a in aliases]
    
    # 2. Filtrage actif : on ne garde que les codes qui existent réellement dans le jeu de données interrogé
    matched_modalities = session.query(DataflowModality).filter(
        DataflowModality.snapshot_id == snapshot_id,
        DataflowModality.dataflow_id == dataflow_id,
        DataflowModality.dimension_id == dimension_id,
        DataflowModality.code.in_(target_codes)
    ).all()
    
    return matched_modalities
