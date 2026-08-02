import logging
import itertools
from typing import List, Dict, Tuple
from sqlalchemy.orm import Session
from src.models.series import Series

LOGGER = logging.getLogger(__name__)

MAX_CANDIDATES_PER_DIMENSION = 3
MAX_TOTAL_COMBINATIONS = 10

def _truncate_candidates(candidates: List[Dict]) -> List[Dict]:
    """
    Règle 4.6 : Conserver jusqu'à trois candidats par dimension ambiguë.
    Trace les troncatures dans les logs.
    """
    if len(candidates) > MAX_CANDIDATES_PER_DIMENSION:
        LOGGER.warning(f"Troncature : {len(candidates)} candidats trouvés pour une dimension. Réduction à {MAX_CANDIDATES_PER_DIMENSION}.")
        return candidates[:MAX_CANDIDATES_PER_DIMENSION]
    return candidates

def _check_series_availability(session: Session, snapshot_id: str, dataflow_id: str, sdmx_key: str) -> bool:
    """
    Vérifie si une clé SDMX existe réellement dans la table Series.
    """
    exists = session.query(Series).filter_by(
        snapshot_id=snapshot_id,
        dataflow_id=dataflow_id,
        series_key=sdmx_key
    ).first()
    return exists is not None

def generate_bounded_combinations(
    session: Session, 
    snapshot_id: str, 
    dataflow_id: str,
    structured_dimensions: List[Dict]
) -> Tuple[List[str], str]:
    """
    Génère un nombre borné de combinaisons à partir de dimensions potentiellement ambiguës.
    Élimine les codes incompatibles en vérifiant l'index de disponibilité.
    
    Retourne un tuple : (Liste des clés SDMX valides, Status)
    Status peut être : "SUCCESS", "TOO_AMBIGUOUS", "NO_VALID_COMBINATION"
    """
    
    # Étape 1 : Troncature dimension par dimension
    lists_of_candidates = []
    for dim_group in structured_dimensions:
        candidates = dim_group.get("candidates", [])
        if not candidates:
            # Si une dimension obligatoire est totalement vide (et qu'aucun défaut n'a marché),
            # le produit cartésien donnera 0 résultat, ce qui est normal (Rejet).
            return [], "INCOMPLETE_KEY"
            
        truncated = _truncate_candidates(candidates)
        lists_of_candidates.append([c["code"] for c in truncated])
        
    # Étape 2 : Génération du produit cartésien
    # iterpool est une liste de tuples représentant toutes les combinaisons possibles.
    cartesian_product = list(itertools.product(*lists_of_candidates))
    
    # Règle 4.6 : Fixer un plafond de combinaisons
    if len(cartesian_product) > MAX_TOTAL_COMBINATIONS:
        LOGGER.error(f"Génération stoppée : {len(cartesian_product)} combinaisons possibles dépassent le plafond de {MAX_TOTAL_COMBINATIONS}.")
        return [], "TOO_AMBIGUOUS"
        
    # Étape 3 : Élimination via l'index de disponibilité
    valid_keys = []
    for combination in cartesian_product:
        # La syntaxe SDMX sépare les dimensions par des points
        sdmx_key = ".".join(combination)
        
        if _check_series_availability(session, snapshot_id, dataflow_id, sdmx_key):
            valid_keys.append(sdmx_key)
            
    # Étape 4 : Retourner plusieurs solutions si elles restent équivalentes
    if not valid_keys:
        LOGGER.warning("Aucune des combinaisons générées n'existe dans le jeu de données.")
        return [], "NO_VALID_COMBINATION"
        
    return valid_keys, "SUCCESS"
