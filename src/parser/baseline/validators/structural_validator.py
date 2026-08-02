from typing import List, Dict, Any, Tuple
from sqlalchemy.orm import Session
from src.models.structure import DataflowDimension, DataflowModality

def validate_structural_integrity(
    session: Session, 
    snapshot_id: str, 
    dataflow_id: str, 
    extracted_candidates: List[Dict[str, Any]]
) -> Tuple[bool, List[str], Dict[str, Any]]:
    """
    Vérifie l'intégrité structurelle des candidats extraits pour un dataflow donné.
    Retourne (is_valid, rejection_reasons, structured_dimensions).
    """
    rejection_reasons = []
    
    # 1. Charger toutes les dimensions pour ce dataflow
    dimensions = session.query(DataflowDimension).filter(
        DataflowDimension.snapshot_id == snapshot_id,
        DataflowDimension.dataflow_id == dataflow_id
    ).all()
    
    if not dimensions:
        return False, [f"Dataflow {dataflow_id} inconnu ou sans dimensions dans le snapshot {snapshot_id}"], {}
        
    dim_map = {d.dimension_id: d for d in dimensions}
    
    # 2. Regrouper les candidats par dimension
    # Format: structured_dimensions[dimension_id] = [code1, code2, ...]
    structured_dimensions = {}
    
    for cand in extracted_candidates:
        dim_id = cand.get("dimension_id")
        code = cand.get("target_code")
        
        if not dim_id or not code:
            continue
            
        # Rejeter les dimensions inconnues
        if dim_id not in dim_map:
            rejection_reasons.append(f"Dimension inconnue rejetée : {dim_id}")
            continue
            
        # Vérifier que le code appartient bien à la codelist
        mod_exists = session.query(DataflowModality).filter(
            DataflowModality.snapshot_id == snapshot_id,
            DataflowModality.dataflow_id == dataflow_id,
            DataflowModality.dimension_id == dim_id,
            DataflowModality.code == code
        ).first()
        
        if not mod_exists:
            rejection_reasons.append(f"Code '{code}' invalide pour la dimension {dim_id}")
            continue
            
        if dim_id not in structured_dimensions:
            structured_dimensions[dim_id] = set()
        structured_dimensions[dim_id].add(code)
        
    # 3. Vérifier les obligations (is_mandatory) pour les dimensions de type SERIES
    for dim_id, dim in dim_map.items():
        if dim.role == "SERIES" and dim.is_mandatory:
            if dim_id not in structured_dimensions or not structured_dimensions[dim_id]:
                rejection_reasons.append(f"Dimension obligatoire manquante : {dim_id} ({dim.canonical_concept})")
                
    # On convertit les sets en listes pour la sortie
    output_dims = {k: list(v) for k, v in structured_dimensions.items()}
    
    is_valid = len(rejection_reasons) == 0
    return is_valid, rejection_reasons, output_dims
