from dataclasses import dataclass, field
from typing import Dict, Any

@dataclass
class Observation:
    """
    Format interne commun pour une observation statistique.
    Sert de pivot entre les différentes sources (INSEE, Eurostat, etc.) et le moteur de calcul.
    """
    period: str                     # Période (ex: "2022-08", "2022-Q1", "2022")
    value: float                    # La valeur numérique observée
    dataflow_id: str                # Identifiant du jeu de données source (ex: "IPC-2025")
    dimensions: Dict[str, str]      # Les dimensions exactes (ex: {"FREQ": "M", "COICOP2018": "01"})
    is_provisional: bool = False    # True si la donnée est marquée comme provisoire/estimée
    metadata: Dict[str, Any] = field(default_factory=dict) # Métadonnées supplémentaires (unités, etc.)
