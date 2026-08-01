from pydantic import BaseModel, Field
from typing import List, Optional, Any, Tuple
from enum import Enum

class ExtractionProvenance(str, Enum):
    EXPLICIT_TEXT = "EXPLICIT_TEXT"
    IMPLICIT_CONTEXT = "IMPLICIT_CONTEXT"
    INFERRED = "INFERRED"
    DEFAULTED = "DEFAULTED"

class PresenceStatus(str, Enum):
    EXPLICIT = "EXPLICIT"
    IMPLICIT = "IMPLICIT"
    MISSING = "MISSING"

class ConstraintType(str, Enum):
    HARD_CONSTRAINT = "HARD_CONSTRAINT"
    PREFERENCE = "PREFERENCE"
    UNCERTAIN_INFERENCE = "UNCERTAIN_INFERENCE"

class CanonicalSlot(BaseModel):
    """
    Contrat de base pour toute information extraite (Lot 6 -> Lot 8)
    """
    canonical_value: Optional[str] = Field(None, description="Valeur canonique ou code concept (ex: 'UNEMPLOYMENT_RATE', 'YOUTH', 'FR')")
    original_label: Optional[str] = Field(None, description="Libellé original tel qu'apparu dans le texte")
    span_offsets: Optional[Tuple[int, int]] = Field(None, description="Position (début, fin) dans le texte d'origine")
    provenance: ExtractionProvenance = Field(ExtractionProvenance.EXPLICIT_TEXT, description="Méthode d'obtention de cette information")
    presence: PresenceStatus = Field(PresenceStatus.EXPLICIT, description="Caractère explicite, implicite ou manquant")
    constraint_type: ConstraintType = Field(ConstraintType.HARD_CONSTRAINT, description="S'agit-il d'une contrainte dure ou d'une préférence ?")
    confidence: float = Field(1.0, description="Niveau de confiance de l'extraction (0.0 à 1.0)")
    alternatives: List[Any] = Field(default_factory=list, description="Autres interprétations possibles en cas d'incertitude")

class CanonicalTime(CanonicalSlot):
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    precision: Optional[str] = Field(None, description="ex: 'YEAR', 'MONTH', 'QUARTER'")
    is_relative: bool = False

class CanonicalMeasure(CanonicalSlot):
    numeric_value: Optional[float] = None
    unit: Optional[str] = None

class CanonicalParseResult(BaseModel):
    """
    Résultat complet de l'extraction par le Lot 6, utilisé par le Lot 8 pour résoudre les requêtes SDMX.
    """
    claim_id: str = Field(..., description="Identifiant unique de l'affirmation")
    original_text: str = Field(..., description="Le texte brut de l'affirmation")
    
    # Entités principales
    indicator: Optional[CanonicalSlot] = Field(None, description="L'indicateur statistique principal (ex: taux de chômage)")
    populations: List[CanonicalSlot] = Field(default_factory=list, description="Les populations visées (ex: jeunes, cadres)")
    territories: List[CanonicalSlot] = Field(default_factory=list, description="Les territoires géographiques (ex: France, Bretagne)")
    time_period: Optional[CanonicalTime] = Field(None, description="La période concernée")
    
    # Attributs statistiques
    expressed_frequency: Optional[CanonicalSlot] = Field(None, description="La fréquence de publication mentionnée (ex: trimestriel)")
    unit: Optional[CanonicalSlot] = Field(None, description="L'unité de la valeur (ex: %, points, euros)")
    expected_dimensions: List[CanonicalSlot] = Field(default_factory=list, description="Dimensions supplémentaires explicitement attendues")
    
    # Opérations
    statistical_operation: Optional[CanonicalSlot] = Field(None, description="L'opération mathématique décrite (ex: baisse, variation, seuil)")
    comparison: Optional[CanonicalSlot] = Field(None, description="Base de comparaison éventuelle (ex: 'par rapport à l'an dernier')")
    
    # Méta
    parse_status: str = Field("ACCEPTED", description="Statut global du parsing: ACCEPTED, AMBIGUOUS, REJECTED")
    warnings: List[str] = Field(default_factory=list, description="Avertissements sur des inférences fragiles")
