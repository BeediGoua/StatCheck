import logging
import requests
from requests.exceptions import RequestException
from typing import Optional
from datetime import datetime
from sqlalchemy.orm import Session
from src.models.series import Series

LOGGER = logging.getLogger(__name__)

# Cache en mémoire pour les requêtes API (évite de spammer l'INSEE pour la même clé)
_API_AVAILABILITY_CACHE = {}

class SDMXNetworkError(Exception):
    """Exception levée en cas de défaillance réseau, pour ne pas confondre avec une absence de série."""
    pass

def _check_local_db(session: Session, snapshot_id: str, dataflow_id: str, sdmx_key: str, start_period: Optional[str], end_period: Optional[str]) -> Optional[bool]:
    """
    Vérifie l'existence de la série et sa couverture temporelle dans la base de données locale.
    Retourne True si dispo, False si indispo (prouvé), ou None si la base manque d'informations.
    """
    series = session.query(Series).filter_by(
        snapshot_id=snapshot_id,
        dataflow_id=dataflow_id,
        series_key=sdmx_key
    ).first()
    
    if not series:
        return None # Inconnu en base, il faudra peut-être vérifier via l'API
        
    # Vérification de la couverture temporelle si elle est demandée
    if start_period and end_period and series.start_period and series.end_period:
        try:
            # Simplification : On suppose ici un format YYYY pour la démo R1. 
            # (Un vrai comparateur de dates SDMX gèrerait les trimestres Q1, M01 etc.)
            req_start = int(start_period[:4])
            req_end = int(end_period[:4])
            db_start = int(series.start_period[:4])
            db_end = int(series.end_period[:4])
            
            if req_end < db_start or req_start > db_end:
                LOGGER.info(f"Série {sdmx_key} existe, mais la période {start_period}-{end_period} est hors couverture ({series.start_period}-{series.end_period}).")
                return False
        except ValueError:
            pass # Si le format de date est trop complexe pour cette heuristique, on passe.
            
    return True

def _check_api_fallback(dataflow_id: str, sdmx_key: str) -> bool:
    """
    Requête SDMX API INSEE en dernier recours, bornée et mise en cache.
    """
    cache_key = f"{dataflow_id}/{sdmx_key}"
    if cache_key in _API_AVAILABILITY_CACHE:
        return _API_AVAILABILITY_CACHE[cache_key]
        
    url = f"https://bdm.insee.fr/series/sdmx/data/{dataflow_id}/{sdmx_key}?lastNObservations=1"
    
    try:
        response = requests.get(url, timeout=3.0) # Timeout très court
        
        if response.status_code == 404:
            _API_AVAILABILITY_CACHE[cache_key] = False
            return False
        elif response.status_code == 200:
            _API_AVAILABILITY_CACHE[cache_key] = True
            return True
        else:
            raise SDMXNetworkError(f"HTTP {response.status_code} sur l'API SDMX")
            
    except RequestException as e:
        # Ne JAMAIS traduire une erreur réseau en "absence de série" (Règle 4.7)
        LOGGER.error(f"Erreur réseau lors de la vérification de la série {sdmx_key}: {str(e)}")
        raise SDMXNetworkError(f"Connexion impossible à l'INSEE pour {sdmx_key}") from e

def verify_series_availability(
    session: Session, 
    snapshot_id: str, 
    dataflow_id: str, 
    sdmx_key: str,
    start_period: Optional[str] = None,
    end_period: Optional[str] = None
) -> bool:
    """
    Vérifie qu'une clé de série existe et couvre la période demandée.
    Processus en cascade : Base locale -> (Contraintes Officielles) -> Appel API INSEE.
    """
    # 1. Vérification Base Locale
    local_status = _check_local_db(session, snapshot_id, dataflow_id, sdmx_key, start_period, end_period)
    if local_status is not None:
        return local_status
        
    # 2. Vérification Contraintes Officielles
    # (Non implémenté pour le moment, on passe directement au repli réseau)
    
    # 3. Vérification Réseau (Dernier recours)
    LOGGER.info(f"Série {sdmx_key} introuvable en base. Appel API de repli déclenché.")
    return _check_api_fallback(dataflow_id, sdmx_key)
