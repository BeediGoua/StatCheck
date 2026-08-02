import logging
from typing import List, Dict
from sqlalchemy.orm import Session

from src.parser.resolvers.joint_resolver import generate_bounded_combinations
from src.parser.resolvers.availability_checker import verify_series_availability, SDMXNetworkError

LOGGER = logging.getLogger(__name__)

def orchestrate_resolution(session: Session, top_k_candidates: List[Dict], structured_dimensions_from_text: List[Dict]) -> Dict:
    """
    Tente de résoudre les mentions textuelles contre les jeux de données candidats (Top K du Lot 7).
    Retourne le résultat de la résolution ou l'erreur appropriée.
    """
    if not top_k_candidates:
        return {"status": "NO_COMPATIBLE_DATASET", "resolved_keys": []}
        
    all_valid_keys_across_datasets = []
    
    for candidate in top_k_candidates:
        dataset_id = candidate.get("dataflow_id")
        snapshot_id = candidate.get("snapshot_id")
        
        LOGGER.info(f"Tentative de résolution sur le candidat rang {candidate.get('rank', '?')} : {dataset_id}")
        
        # 1. Génération conjointe et filtre de disponibilité (implique les modules 4.1 à 4.6)
        valid_keys, joint_status = generate_bounded_combinations(
            session=session,
            snapshot_id=snapshot_id,
            dataflow_id=dataset_id,
            structured_dimensions=structured_dimensions_from_text
        )
        
        if joint_status == "TOO_AMBIGUOUS":
            # L'ambiguïté excessive stoppe l'orchestration pour ce candidat, mais on continue sur le suivant
            LOGGER.warning(f"Le dataset {dataset_id} génère trop de combinaisons. Rejeté.")
            candidate["resolution_status"] = "TOO_AMBIGUOUS"
            continue
            
        if joint_status in ["INCOMPLETE_KEY", "NO_VALID_COMBINATION"]:
            # Le dataset n'a pas les dimensions requises, ou les clés générées n'existent pas
            LOGGER.info(f"Candidat {dataset_id} incompatible. Statut : DATASET_REJECTED")
            candidate["resolution_status"] = "DATASET_REJECTED"
            continue
            
        # 2. Vérification réseau finale (4.7) sur les clés survivantes
        surviving_keys = []
        for key in valid_keys:
            try:
                # Dans la vraie vie, on extrairait le start/end period depuis la requête texte (time_resolver)
                is_available = verify_series_availability(session, snapshot_id, dataset_id, key)
                if is_available:
                    surviving_keys.append({"dataflow_id": dataset_id, "sdmx_key": key})
            except SDMXNetworkError:
                LOGGER.error(f"Erreur réseau sur {key}, on l'écarte par précaution technique.")
                pass
                
        if surviving_keys:
            LOGGER.info(f"Résolution réussie pour {dataset_id} ! {len(surviving_keys)} clés trouvées.")
            all_valid_keys_across_datasets.extend(surviving_keys)
            
    # Évaluation finale (4.8)
    if not all_valid_keys_across_datasets:
        LOGGER.error("Aucune résolution n'a abouti sur l'ensemble du Top K.")
        return {"status": "NO_COMPATIBLE_DATASET", "resolved_keys": []}
        
    return {
        "status": "SUCCESS", 
        "resolved_keys": all_valid_keys_across_datasets
    }
