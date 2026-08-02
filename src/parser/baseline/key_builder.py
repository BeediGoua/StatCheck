from typing import Dict, List
from sqlalchemy.orm import Session
from src.models.structure import DataflowDimension

def build_sdmx_key(session: Session, snapshot_id: str, dataflow_id: str, structured_dimensions: Dict[str, List[str]]) -> str:
    """
    Construit la clé de série SDMX ordonnée à partir des dimensions validées.
    - Exclut la dimension temporelle et les attributs.
    - Gère les dimensions multiples avec le '+' (syntaxe SDMX OR).
    - Laisse vide les dimensions facultatives non trouvées.
    """
    
    # 1. Récupérer uniquement les dimensions qui forment la clé (SERIES) pour ce dataflow
    series_dims = session.query(DataflowDimension).filter(
        DataflowDimension.snapshot_id == snapshot_id,
        DataflowDimension.dataflow_id == dataflow_id,
        DataflowDimension.role == "SERIES"
    ).order_by(DataflowDimension.position).all()
    
    if not series_dims:
        return ""
        
    key_parts = []
    
    # 2. Construire la clé dans l'ordre strict
    for dim in series_dims:
        codes = structured_dimensions.get(dim.dimension_id, [])
        if codes:
            # S'il y a plusieurs codes, on les joint par un '+'
            # On trie les codes alphabétiquement pour garantir l'unicité de la représentation de la clé
            joined_codes = "+".join(sorted(codes))
            key_parts.append(joined_codes)
        else:
            # Si aucune valeur n'est trouvée (c'est forcément une dimension facultative si on a passé la validation)
            # On laisse le champ vide.
            key_parts.append("")
            
    # 3. Assembler avec des points
    # Si les derniers éléments sont vides, l'API SDMX permet souvent de les omettre, 
    # mais il est plus sûr (et standard) de garder tous les points intermédiaires
    sdmx_key = ".".join(key_parts)
    
    return sdmx_key
