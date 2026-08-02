from typing import Optional, Dict
from sqlalchemy.orm import Session
from src.models.structure import DimensionDefaultPolicy, DataflowModality
import logging

LOGGER = logging.getLogger(__name__)

# Liste des codes universels considérés comme "NON_APPLICABLE" par l'INSEE.
# Selon les règles, ils ne doivent jamais être utilisés comme Total générique.
FORBIDDEN_DEFAULT_CODES = ["_Z", "Z", "NAP", "NON_APPLICABLE"]

def apply_dimension_default(
    session: Session, 
    snapshot_id: str, 
    dataflow_id: str, 
    dimension_id: str,
    extracted_candidates: list
) -> Optional[Dict]:
    """
    Tente de résoudre une dimension vide (sans candidat extrait) en appliquant une politique par défaut.
    Ne s'applique QUE SI `extracted_candidates` est vide.
    Retourne un candidat formatté ou None si on doit s'abstenir.
    """
    # Règle 1: Appliquer un défaut uniquement si aucune mention n'a été extraite.
    if extracted_candidates:
        return None
        
    # Règle 2: Vérifier que la politique est valide pour le dataflow et le snapshot.
    policy = session.query(DimensionDefaultPolicy).filter_by(
        snapshot_id=snapshot_id,
        dataflow_id=dataflow_id,
        dimension_id=dimension_id
    ).first()
    
    # Règle 4: S'abstenir lorsqu'aucun défaut sûr n'existe
    if not policy or policy.policy_type == "NO_DEFAULT" or not policy.target_code:
        return None
        
    target_code = policy.target_code
    
    # Règle 5: Ne jamais utiliser NON_APPLICABLE comme total générique
    if target_code in FORBIDDEN_DEFAULT_CODES:
        LOGGER.warning(f"La politique par défaut cible '{target_code}' (Non Applicable). Rejeté pour éviter un biais.")
        return None
        
    # On vérifie que la modalité de défaut existe réellement dans la dimension
    modality = session.query(DataflowModality).filter_by(
        snapshot_id=snapshot_id,
        dataflow_id=dataflow_id,
        dimension_id=dimension_id,
        code=target_code
    ).first()
    
    if not modality:
        LOGGER.error(f"La politique de défaut cible un code inexistant: {target_code}")
        return None
        
    # Règle 3: Tracer DATASET_DEFAULT comme provenance.
    return {
        "dimension_id": dimension_id,
        "code": modality.code,
        "label": modality.normalized_label,
        "provenance": "DATASET_DEFAULT",
        "confidence": "HIGH"
    }
