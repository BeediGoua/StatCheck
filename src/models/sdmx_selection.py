from pydantic import BaseModel, Field
from typing import List, Dict, Optional, Any
from enum import Enum

class AvailabilityStatus(str, Enum):
    SERIES_AVAILABLE = "SERIES_AVAILABLE"
    SERIES_NOT_AVAILABLE = "SERIES_NOT_AVAILABLE"
    AVAILABILITY_UNKNOWN = "AVAILABILITY_UNKNOWN"
    SOURCE_UNREACHABLE = "SOURCE_UNREACHABLE"
    METADATA_STALE = "METADATA_STALE"

class AggregationOperation(str, Enum):
    AGGREGATION_UNRESOLVED = "AGGREGATION_UNRESOLVED"
    # Le Lot 8 n'a pas le droit d'utiliser d'autres valeurs pour l'instant.
    # Les valeurs mathématiques exactes (MEAN, SUM, YoY) seront décidées par le Lot 9.

class TimeWindow(BaseModel):
    start_period: Optional[str] = Field(None, description="Période de début au format SDMX (ex: 2023-Q1)")
    end_period: Optional[str] = Field(None, description="Période de fin au format SDMX (ex: 2023-Q4)")
    aggregation_operation: AggregationOperation = Field(
        AggregationOperation.AGGREGATION_UNRESOLVED, 
        description="Opération temporelle. Par défaut UNRESOLVED car le Lot 8 ne doit jamais moyenner/sommer lui-même."
    )

class DimensionResolution(BaseModel):
    dimension_id: str = Field(..., description="L'identifiant de la dimension (ex: AGE)")
    position: int = Field(..., description="La position ordonnée de la dimension dans la clé")
    codes: List[str] = Field(..., description="Les codes retenus (ex: ['Y15T24'])")
    method: str = Field(..., description="La méthode de résolution (ex: EXACT_MATCH, CURATED_ALIAS, SAFE_TOTAL_DEFAULT)")
    provenance: str = Field(..., description="L'origine de l'information (ex: EXPLICIT_TEXT, IMPLICIT, DATASET_DEFAULT)")
    confidence: str = Field(..., description="Niveau de confiance (ex: HIGH, MEDIUM, LOW)")
    evidence: Optional[str] = Field(None, description="Le span ou la trace ayant mené à cette résolution")

class SeriesCandidate(BaseModel):
    ordered_key: str = Field(..., description="La clé de série SDMX finale (ex: Q.TAUX_CHOMAGE.T.Y15T24.FE)")
    dimensions: List[DimensionResolution] = Field(..., description="Le détail de la résolution par dimension")
    structural_status: str = Field(..., description="ex: VALID, INVALID_COMBINATION")
    availability_status: AvailabilityStatus = Field(..., description="Statut de disponibilité réelle de la série")
    idbank: Optional[str] = Field(None, description="Si la série INSEE possède un IDBANK direct")
    warnings: List[str] = Field(default_factory=list, description="Avertissements spécifiques à la série (ex: 'Substitution FE par FM')")

class SDMXSelectionPlan(BaseModel):
    """
    Contrat Lot 8 -> Lot 9.
    Représente le plan détaillé pour récupérer les données,
    SANS faire de calculs statistiques sauvages.
    """
    claim_id: str = Field(..., description="L'identifiant de l'affirmation")
    status: str = Field(..., description="Statut final du Lot 8 (RESOLVED, AMBIGUOUS, ABSTAIN, etc.)")
    
    selected_dataflow_id: str = Field(..., description="Le dataflow retenu (ex: CHOMAGE-TRIM-NATIONAL)")
    catalog_snapshot_id: str = Field(..., description="Snapshot des métadonnées utilisé")
    
    series_candidates: List[SeriesCandidate] = Field(..., description="Les clés de séries à interroger")
    time_window: TimeWindow = Field(..., description="La fenêtre temporelle extraite")
    
    unresolved_questions: List[Dict[str, str]] = Field(
        default_factory=list, 
        description="Ambiguïtés bloquantes restantes, structurées pour demander à l'utilisateur"
    )
    alternatives: List[Any] = Field(
        default_factory=list, 
        description="Choix alternatifs (ex: 15-24 ans vs 15-29 ans) si ambiguïté modérée"
    )
    
    provenance: Dict[str, str] = Field(
        default_factory=dict,
        description="Traçabilité des versions utilisées (stratégie, snapshot, nomenclatures)"
    )
