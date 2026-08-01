from pydantic import BaseModel, Field
from typing import List, Optional, Any

class RetrievalCandidate(BaseModel):
    """
    Représente un jeu de données ou dataflow candidat remonté par le Lot 7,
    à évaluer par le Lot 8.
    """
    dataflow_id: str = Field(..., description="L'identifiant de ressource (ex: CHOMAGE-TRIM-NATIONAL)")
    catalog_snapshot_id: str = Field(..., description="Le snapshot du catalogue utilisé (ex: insee-2026-07-31)")
    metadata_version: Optional[str] = Field(None, description="La version spécifique des métadonnées SDMX pour ce dataflow")
    
    retrieval_rank: int = Field(..., description="Le rang du candidat dans la liste de résultats (1 = meilleur)")
    retrieval_score: float = Field(..., description="Le score final (RRF ou Reranker) attribué par le Lot 7")
    retrieval_architecture: str = Field(..., description="L'architecture utilisée pour ce score (ex: R1, R2, RRF_CROSS_ENCODER)")
    
    reasons: List[str] = Field(default_factory=list, description="Raisons textuelles expliquant ce classement (ex: 'Match exact sur l'indicateur')")

class RetrievalTopK(BaseModel):
    """
    Contrat Lot 7 -> Lot 8.
    Contient le Top K des candidats, permettant au Lot 8 de rejeter un candidat
    et de tester le suivant de la liste.
    """
    claim_id: str = Field(..., description="L'identifiant de l'affirmation d'origine")
    candidates: List[RetrievalCandidate] = Field(..., description="La liste ordonnée des candidats à évaluer")
    
    def get_next_candidate(self, current_rank: int) -> Optional[RetrievalCandidate]:
        """
        Permet au Lot 8 de tester le candidat suivant si le précédent a été rejeté.
        """
        for candidate in self.candidates:
            if candidate.retrieval_rank > current_rank:
                return candidate
        return None
