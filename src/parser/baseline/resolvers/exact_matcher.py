from typing import List, Dict
from sqlalchemy.orm import Session
from src.parser.baseline.normalizer import normalize_text
from src.models.structure import DataflowModality, DimensionAlias

def match_modality_exact(
    session: Session, 
    text: str, 
    snapshot_id: str, 
    dataflow_id: str, 
    dimension_id: str
) -> List[Dict]:
    """
    Recherche exacte d'un fragment de texte parmi les codes, libellés officiels, et alias
    pour une dimension spécifique.
    Retourne une liste de candidats.
    """
    if not text.strip():
        return []

    norm_dict = normalize_text(text)
    matching_text = norm_dict["matching_normalized_text"]
    
    candidates = []
    
    # 1. Recherche par CODE exact (insensible à la casse)
    code_matches = session.query(DataflowModality).filter(
        DataflowModality.snapshot_id == snapshot_id,
        DataflowModality.dataflow_id == dataflow_id,
        DataflowModality.dimension_id == dimension_id,
        # le champ code est souvent en majuscule dans la base, on gère l'insensibilité via ilike
        DataflowModality.code.ilike(matching_text)
    ).all()
    
    if code_matches:
        for match in code_matches:
            candidates.append({
                "target_code": match.code,
                "provenance": "EXACT_CODE",
                "original_text": norm_dict["raw_text"],
                "normalized_text": matching_text
            })
        return candidates

    # 2. Recherche par LIBELLÉ OFFICIEL exact
    label_matches = session.query(DataflowModality).filter(
        DataflowModality.snapshot_id == snapshot_id,
        DataflowModality.dataflow_id == dataflow_id,
        DataflowModality.dimension_id == dimension_id,
        DataflowModality.normalized_label == matching_text
    ).all()
    
    if label_matches:
        for match in label_matches:
            candidates.append({
                "target_code": match.code,
                "provenance": "EXACT_LABEL",
                "original_text": norm_dict["raw_text"],
                "normalized_text": matching_text
            })
        return candidates

    # 3. Recherche par ALIAS
    alias_matches = session.query(DimensionAlias).filter(
        DimensionAlias.alias_text == matching_text,
        DimensionAlias.scope_type.in_(["GLOBAL", "DIMENSION"])
    ).all()
    
    valid_aliases = []
    for am in alias_matches:
        if am.scope_type == "DIMENSION" and am.scope_value != dimension_id:
            continue
        valid_aliases.append(am)
        
    if valid_aliases:
        for match in valid_aliases:
            # Vérifier si la modalité ciblée existe bien pour ce dataflow (éviter les alias morts)
            mod_exists = session.query(DataflowModality).filter(
                DataflowModality.snapshot_id == snapshot_id,
                DataflowModality.dataflow_id == dataflow_id,
                DataflowModality.dimension_id == dimension_id,
                DataflowModality.code == match.target_code
            ).first()
            
            if mod_exists:
                candidates.append({
                    "target_code": match.target_code,
                    "provenance": "EXACT_ALIAS",
                    "original_text": norm_dict["raw_text"],
                    "normalized_text": matching_text
                })

    return candidates
