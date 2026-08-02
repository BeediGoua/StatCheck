from typing import Optional, Dict, List
import logging
import re
from sqlalchemy.orm import Session
from src.models.structure import DataflowModality, DataflowDimension

LOGGER = logging.getLogger(__name__)

def get_available_frequencies(session: Session, snapshot_id: str, dataflow_id: str) -> List[str]:
    """
    Récupère toutes les fréquences disponibles pour ce dataflow (en lisant la dimension FREQ).
    """
    freq_dim = session.query(DataflowDimension).filter_by(
        snapshot_id=snapshot_id,
        dataflow_id=dataflow_id,
        canonical_concept="FREQ"
    ).first()
    
    if not freq_dim:
        # Fallback heuristique très courant à l'INSEE
        freq_dim = session.query(DataflowDimension).filter_by(
            snapshot_id=snapshot_id,
            dataflow_id=dataflow_id,
            dimension_id="FREQ"
        ).first()
        
    if not freq_dim:
        return []
        
    modalities = session.query(DataflowModality).filter_by(
        snapshot_id=snapshot_id,
        dataflow_id=dataflow_id,
        dimension_id=freq_dim.dimension_id
    ).all()
    
    return [m.code for m in modalities]

def resolve_time_and_frequency(
    session: Session, 
    snapshot_id: str, 
    dataflow_id: str, 
    extracted_time: str
) -> Dict:
    """
    Traduit une période temporelle brute (ex: '2023') en paramètres d'API SDMX
    (series_frequency, start_period, end_period) en fonction de la réalité du dataflow.
    Conformément à la R1, aucun calcul déductif complexe ('l'année dernière') n'est fait ici.
    """
    result = {
        "series_frequency": None,
        "start_period": None,
        "end_period": None,
        "AGGREGATION_UNRESOLVED": False
    }
    
    if not extracted_time:
        return result
        
    available_freqs = get_available_frequencies(session, snapshot_id, dataflow_id)
    
    # Détection basique du format de la date extraite
    is_year_only = bool(re.fullmatch(r"^\d{4}$", extracted_time.strip()))
    
    if is_year_only:
        # Si le dataflow propose de l'Annuel (A), on l'utilise directement
        if "A" in available_freqs:
            result["series_frequency"] = "A"
            result["start_period"] = extracted_time
            result["end_period"] = extracted_time
        # Si seule la fréquence Trimestrielle (Q) est dispo, on transforme l'année en fenêtre Q1->Q4
        elif "Q" in available_freqs:
            result["series_frequency"] = "Q"
            result["start_period"] = f"{extracted_time}-Q1"
            result["end_period"] = f"{extracted_time}-Q4"
            result["AGGREGATION_UNRESOLVED"] = True
            LOGGER.info(f"Transformation de l'année {extracted_time} en fenêtre trimestrielle. (Agrégation requise)")
        # Si seule la fréquence Mensuelle (M) est dispo, on transforme l'année en fenêtre M01->M12
        elif "M" in available_freqs:
            result["series_frequency"] = "M"
            result["start_period"] = f"{extracted_time}-01"
            result["end_period"] = f"{extracted_time}-12"
            result["AGGREGATION_UNRESOLVED"] = True
            LOGGER.info(f"Transformation de l'année {extracted_time} en fenêtre mensuelle. (Agrégation requise)")
        else:
            # Fallback
            result["start_period"] = extracted_time
            result["end_period"] = extracted_time
    else:
        # Période précise (ex: 2023-Q1, 2023-05) -> on garde tel quel (pas de calcul au Lot 8)
        result["start_period"] = extracted_time
        result["end_period"] = extracted_time
        
        if "-Q" in extracted_time and "Q" in available_freqs:
            result["series_frequency"] = "Q"
        elif "-" in extracted_time and len(extracted_time.split("-")[1]) == 2 and "M" in available_freqs:
            result["series_frequency"] = "M"
            
    return result
