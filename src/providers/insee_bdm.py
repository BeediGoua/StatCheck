import requests
import xml.etree.ElementTree as ET
import json
import os
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from ..models.observation import Observation

class InseeBdmProvider:
    """
    Connecteur pour l'API SDMX de la Banque de Données Macroéconomiques de l'INSEE.
    Inclut un système de cache JSON local pour ne pas surcharger l'API.
    """
    BASE_URL = "https://bdm.insee.fr/series/sdmx/data"
    CACHE_DIR = Path(".cache/bdm")
    
    def __init__(self, use_cache: bool = True):
        self.session = requests.Session()
        self.use_cache = use_cache
        if self.use_cache:
            self.CACHE_DIR.mkdir(parents=True, exist_ok=True)
            
    def _get_cache_path(self, url: str) -> Path:
        # Création d'un nom de fichier unique basé sur l'URL
        url_hash = hashlib.md5(url.encode()).hexdigest()
        return self.CACHE_DIR / f"{url_hash}.json"
    
    def fetch_series_by_idbank(self, idbank: str) -> List[Observation]:
        url = f"{self.BASE_URL}/SERIES_BDM/{idbank}"
        return self._fetch_and_parse(url, dataflow_id="SERIES_BDM")
    
    def fetch_series_by_dimensions(self, dataflow: str, dimensions_key: str) -> List[Observation]:
        url = f"{self.BASE_URL}/{dataflow}/{dimensions_key}"
        return self._fetch_and_parse(url, dataflow_id=dataflow)
        
    def _fetch_and_parse(self, url: str, dataflow_id: str) -> List[Observation]:
        cache_path = self._get_cache_path(url)
        
        # 1. Vérification du cache JSON
        if self.use_cache and cache_path.exists():
            with open(cache_path, 'r', encoding='utf-8') as f:
                cached_data = json.load(f)
            # Reconstruire les objets Observation
            return [Observation(**obs) for obs in cached_data]
            
        # 2. Appel API si non en cache
        response = self.session.get(url, timeout=30)
        
        if response.status_code == 404:
            raise ValueError(f"Série introuvable ou erreur de dimension à l'URL : {url}")
        
        response.raise_for_status()
        
        root = ET.fromstring(response.content)
        observations = []
        
        for obs in root.iter():
            if 'Obs' in obs.tag:
                period = obs.get('TIME_PERIOD')
                value_str = obs.get('OBS_VALUE')
                status = obs.get('OBS_STATUS', 'A')
                
                if period and value_str is not None:
                    try:
                        val = float(value_str)
                        is_provisional = (status == 'P')
                        
                        observations.append(Observation(
                            period=period,
                            value=val,
                            dataflow_id=dataflow_id,
                            dimensions={}, 
                            is_provisional=is_provisional,
                            metadata={"OBS_STATUS": status}
                        ))
                    except ValueError:
                        continue
        
        # 3. Sauvegarde de la réponse au format JSON pour le cache
        if self.use_cache:
            # On convertit les dataclasses en dictionnaires natifs pour JSON
            obs_dicts = [vars(o) for o in observations]
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(obs_dicts, f, indent=2)
                
        return observations
