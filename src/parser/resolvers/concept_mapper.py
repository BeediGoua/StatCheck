import logging
from typing import List
from sqlalchemy.orm import Session
from src.models.structure import DataflowDimension

LOGGER = logging.getLogger(__name__)

# Fallback dict : si le champ 'canonical_concept' n'a pas pu être résolu lors de l'ingestion,
# on peut utiliser ce dictionnaire pour tenter de deviner le concept à partir de l'ID de dimension INSEE.
FALLBACK_MAPPING = {
    "AGE": ["AGE", "CL_AGE", "TRANCHE_AGE", "AGE_2", "AGE_6"],
    "GEO": ["REF_AREA", "GEO", "TERRITOIRE"],
    "SEX": ["SEXE", "SEX"],
    "UNIT": ["UNIT_MEASURE", "UNITE"],
    "FREQ": ["FREQ", "FREQUENCE"],
    "INDICATOR": ["INDICATEUR", "NATURE", "INDICE"],
    "SECTOR": ["SECT-ACT", "SECT_ENT", "NAF"],
}

def map_concept_to_dimensions(
    session: Session, 
    snapshot_id: str, 
    dataflow_id: str, 
    canonical_concept: str
) -> List[DataflowDimension]:
    """
    Traduit un concept canonique générique (ex: 'AGE') en une liste de DataflowDimension 
    spécifiques à un jeu de données (ex: 'CL_AGE', 'AGE').
    
    Retourne la liste des dimensions correspondantes (les objets complets pour avoir accès au 'role').
    """
    canonical_concept = canonical_concept.upper()
    
    # 1. Recherche primaire via la modélisation SDMX stockée
    matched_dims = session.query(DataflowDimension).filter(
        DataflowDimension.snapshot_id == snapshot_id,
        DataflowDimension.dataflow_id == dataflow_id,
        DataflowDimension.canonical_concept == canonical_concept
    ).all()
    
    if matched_dims:
        return matched_dims
        
    # 2. Stratégie de repli (Fallback) si la base n'a pas de canonical_concept fiable
    LOGGER.info(f"Concept '{canonical_concept}' non trouvé dans canonical_concept, tentative via fallback.")
    fallback_ids = FALLBACK_MAPPING.get(canonical_concept, [])
    
    if not fallback_ids:
        return []
        
    # On cherche si l'une des dimensions INSEE appartient à notre liste de fallback
    fallback_matched_dims = session.query(DataflowDimension).filter(
        DataflowDimension.snapshot_id == snapshot_id,
        DataflowDimension.dataflow_id == dataflow_id,
        DataflowDimension.dimension_id.in_(fallback_ids)
    ).all()
    
    return fallback_matched_dims
