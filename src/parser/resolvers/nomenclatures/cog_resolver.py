from typing import Optional, List
from sqlalchemy.orm import Session
from src.models.structure import DataflowModality
from src.parser.baseline.normalizer import normalize_text
import logging

LOGGER = logging.getLogger(__name__)

class NomenclatureVersion:
    """Structure de métadonnées pour le versioning des nomenclatures."""
    def __init__(self, name: str, version: str, description: str):
        self.name = name
        self.version = version
        self.description = description

# Versioning du pont géographique
COG_2023 = NomenclatureVersion("COG", "2023", "Code Officiel Géographique 2023")

# Dictionnaire statique pivot : Forme normalisée -> Code Canonique COG
# Ce dictionnaire est une maquette d'architecture R1.
COG_MAPPING = {
    "france": "FXX",
    "france metropolitaine": "FXX",
    "metropole": "FXX",
    "hexagone": "FXX",
    "france entiere": "FE",
    "guadeloupe": "971",
    "martinique": "972",
    "guyane": "973",
    "la reunion": "974",
    "mayotte": "976",
}

def resolve_to_cog(text: str) -> Optional[str]:
    """
    Traduit un texte libre en code canonique COG.
    """
    if not text:
        return None
        
    norm = normalize_text(text)["matching_normalized_text"]
    
    # Matching strict sur le dictionnaire pivot
    if norm in COG_MAPPING:
        return COG_MAPPING[norm]
        
    # Heuristiques de secours ou fuzzy matching (à étoffer)
    for key, val in COG_MAPPING.items():
        if key in norm:
            return val
            
    return None

def translate_cog_to_dataflow(
    session: Session, 
    cog_code: str, 
    dataflow_id: str, 
    dimension_id: str,
    snapshot_id: str
) -> List[DataflowModality]:
    """
    Traduit le code canonique COG vers la modalité spécifique du dataflow ciblé.
    Ex: Le COG 'FXX' (France métropolitaine) se traduit souvent par 'FM' dans l'API INSEE.
    """
    
    # 1. Vérification si le code COG est directement utilisé dans le dataflow (parfois INSEE utilise le COG brut)
    direct_match = session.query(DataflowModality).filter(
        DataflowModality.snapshot_id == snapshot_id,
        DataflowModality.dataflow_id == dataflow_id,
        DataflowModality.dimension_id == dimension_id,
        DataflowModality.code == cog_code
    ).all()
    
    if direct_match:
        return direct_match
        
    # 2. Dictionnaire de traduction COG -> Modèles courants INSEE (Maquette)
    # L'INSEE utilise très souvent FE (France entière) et FM (France métropolitaine)
    INSEE_GEO_VARIANTS = {
        "FXX": ["FM", "F_METRO"],
        "FE": ["FE", "F_ENTIERE"]
    }
    
    variants = INSEE_GEO_VARIANTS.get(cog_code, [])
    if not variants:
        return []
        
    # On cherche ces variantes dans la base
    variant_matches = session.query(DataflowModality).filter(
        DataflowModality.snapshot_id == snapshot_id,
        DataflowModality.dataflow_id == dataflow_id,
        DataflowModality.dimension_id == dimension_id,
        DataflowModality.code.in_(variants)
    ).all()
    
    return variant_matches
