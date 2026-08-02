from typing import Optional, List
from sqlalchemy.orm import Session
from src.models.structure import DataflowModality
from src.parser.resolvers.nomenclatures.cog_resolver import NomenclatureVersion
from src.parser.baseline.normalizer import normalize_text
import logging

LOGGER = logging.getLogger(__name__)

# Versioning des nomenclatures thématiques
NAF_REV2 = NomenclatureVersion("NAF", "rev2", "Nomenclature d'Activités Française Rév. 2")
PCS_2020 = NomenclatureVersion("PCS", "2020", "Professions et Catégories Socioprofessionnelles 2020")
AGE_DEFAULT = NomenclatureVersion("AGE", "standard", "Référentiel d'âge standardisé")

# Dictionnaire statique pivot (Maquette R1)
# Ce dictionnaire unifie les nomenclatures d'âge, NAF, PCS, etc.
THEMATIC_MAPPING = {
    # NAF
    "agriculture": ("NAF", "AZ"),
    "industrie": ("NAF", "BE"),
    "construction": ("NAF", "FZ"),
    "commerce": ("NAF", "GZ"),
    "services": ("NAF", "GU"),
    
    # PCS
    "agriculteur": ("PCS", "10"),
    "artisan": ("PCS", "20"),
    "cadre": ("PCS", "30"),
    "employe": ("PCS", "50"),
    "ouvrier": ("PCS", "60"),
    
    # AGE (Groupements standards)
    "jeunes": ("AGE", "Y15T24"),
    "seniors": ("AGE", "Y55T64"),
    "actifs": ("AGE", "Y15T64"),
}

def resolve_to_thematic_concept(text: str, nomenclature_type: str) -> Optional[str]:
    """
    Traduit un texte libre en code pivot d'une nomenclature thématique (ex: 'agriculture' -> 'AZ' pour la NAF).
    """
    if not text:
        return None
        
    norm = normalize_text(text)["matching_normalized_text"]
    
    # Matching strict
    if norm in THEMATIC_MAPPING:
        nom_type, code = THEMATIC_MAPPING[norm]
        if nom_type == nomenclature_type:
            return code
            
    # Heuristique basique (fallback)
    for key, (nom_type, code) in THEMATIC_MAPPING.items():
        if nom_type == nomenclature_type and key in norm:
            return code
            
    return None

def translate_thematic_to_dataflow(
    session: Session, 
    pivot_code: str, 
    dataflow_id: str, 
    dimension_id: str,
    snapshot_id: str
) -> List[DataflowModality]:
    """
    Traduit le code pivot thématique vers la modalité spécifique du dataflow.
    En général, pour NAF et PCS, l'INSEE utilise les mêmes codes que la nomenclature.
    """
    
    # Vérification directe (dans 90% des cas, l'INSEE utilise le code pivot directement)
    direct_match = session.query(DataflowModality).filter(
        DataflowModality.snapshot_id == snapshot_id,
        DataflowModality.dataflow_id == dataflow_id,
        DataflowModality.dimension_id == dimension_id,
        DataflowModality.code == pivot_code
    ).all()
    
    if direct_match:
        return direct_match
        
    return []
