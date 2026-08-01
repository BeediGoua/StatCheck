from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class ResolutionStatus(str, Enum):
    # États de succès
    RESOLVED = "RESOLVED"
    RESOLVED_WITH_WARNING = "RESOLVED_WITH_WARNING"
    
    # États d'ambiguïté ou d'insuffisance
    AMBIGUOUS = "AMBIGUOUS"
    INSUFFICIENT_CONTEXT = "INSUFFICIENT_CONTEXT"
    
    # États de rejet technique ou structurel
    DATASET_REJECTED = "DATASET_REJECTED"
    NO_COMPATIBLE_DATASET = "NO_COMPATIBLE_DATASET"
    
    # États de disponibilité
    SERIES_NOT_AVAILABLE = "SERIES_NOT_AVAILABLE"
    AVAILABILITY_UNKNOWN = "AVAILABILITY_UNKNOWN"
    SOURCE_UNREACHABLE = "SOURCE_UNREACHABLE"
    METADATA_STALE = "METADATA_STALE"
    
    # État d'échec volontaire final
    ABSTAIN = "ABSTAIN"

# Définition des transitions autorisées (Machine à états)
# Clé : Statut courant -> Valeur : Liste des statuts suivants possibles
ALLOWED_TRANSITIONS: Dict[ResolutionStatus, List[ResolutionStatus]] = {
    # Depuis un dataset testé et rejeté, on peut chercher le suivant, ou échouer s'il n'y en a plus
    ResolutionStatus.DATASET_REJECTED: [
        ResolutionStatus.RESOLVED, 
        ResolutionStatus.RESOLVED_WITH_WARNING,
        ResolutionStatus.AMBIGUOUS,
        ResolutionStatus.DATASET_REJECTED, # Rejet du dataset suivant
        ResolutionStatus.NO_COMPATIBLE_DATASET # Plus de datasets à tester
    ],
    
    # Si la série n'est pas dispo, on peut tenter une autre combinaison ou rejeter le dataset
    ResolutionStatus.SERIES_NOT_AVAILABLE: [
        ResolutionStatus.RESOLVED,
        ResolutionStatus.DATASET_REJECTED,
        ResolutionStatus.AMBIGUOUS
    ],
    
    # Les états finaux ne peuvent généralement mener qu'à ABSTAIN s'ils bloquent le système
    ResolutionStatus.AMBIGUOUS: [ResolutionStatus.ABSTAIN],
    ResolutionStatus.INSUFFICIENT_CONTEXT: [ResolutionStatus.ABSTAIN],
    ResolutionStatus.NO_COMPATIBLE_DATASET: [ResolutionStatus.ABSTAIN],
    ResolutionStatus.SOURCE_UNREACHABLE: [ResolutionStatus.ABSTAIN],
    ResolutionStatus.METADATA_STALE: [ResolutionStatus.ABSTAIN],
    
    # États terminaux valides (ou menant au Lot 9)
    ResolutionStatus.RESOLVED: [],
    ResolutionStatus.RESOLVED_WITH_WARNING: [],
    ResolutionStatus.ABSTAIN: []
}

class StatusReason(str, Enum):
    """Motifs structurés pour chaque décision"""
    # Pour RESOLVED_WITH_WARNING
    SUBSTITUTION_GEOGRAPHIQUE = "SUBSTITUTION_GEOGRAPHIQUE"
    SERIES_NON_CORRIGEE_AU_LIEU_DE_CVS = "SERIES_NON_CORRIGEE_AU_LIEU_DE_CVS"
    
    # Pour DATASET_REJECTED
    MANDATORY_DIMENSION_MISSING = "MANDATORY_DIMENSION_MISSING"
    EXPLICIT_TERRITORY_NOT_COVERED = "EXPLICIT_TERRITORY_NOT_COVERED"
    
    # Pour AMBIGUOUS
    MULTIPLE_EQUIVALENT_ALIASES = "MULTIPLE_EQUIVALENT_ALIASES"
    SEMANTIC_COLLISION = "SEMANTIC_COLLISION"
    
    # Pour SERIES_NOT_AVAILABLE / AVAILABILITY_UNKNOWN
    COMBINATION_NOT_PUBLISHED = "COMBINATION_NOT_PUBLISHED"
    API_TIMEOUT = "API_TIMEOUT"

class ResolutionState(BaseModel):
    """
    Suit l'état courant de la résolution d'un Dataset ou d'une requête globale.
    """
    status: ResolutionStatus = Field(..., description="Statut courant")
    reason_code: Optional[StatusReason] = Field(None, description="Code motif structuré")
    reason_details: Optional[str] = Field(None, description="Détails lisibles par un humain")
    
    def can_transition_to(self, new_status: ResolutionStatus) -> bool:
        """Vérifie si la transition demandée est légale."""
        allowed = ALLOWED_TRANSITIONS.get(self.status, [])
        return new_status in allowed
