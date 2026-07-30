import sys
import time
sys.path.insert(0, ".")

from src.parser.llm.llm_parser import StatCheckLLMParser
from src.parser.llm.schemas.envelope import LLMInputEnvelope, ValidationStatus

def run_experiment_f_repair():
    """
    Expérience F (Optionnelle) :
    Montre la capacité du système à faire une "Self-Correction" en cas d'erreur Pydantic.
    """
    print("=== DÉBUT DE L'EXPÉRIENCE F (RÉPARATION SÉMANTIQUE) ===")
    
    llm_parser = StatCheckLLMParser()
    
    # Simulation d'un claim complexe
    claim_text = "Le PIB a cru de 2%, ou baissé selon d'autres sources."
    env = LLMInputEnvelope(claim_id="exp_f_1", claim_text=claim_text)
    
    # 1er passage
    print("\n[Passage 1] Tentative de parse...")
    res = llm_parser.parse_claim(env)
    
    print(f"Statut : {res.status.value}")
    if res.validation_logs:
        print("Erreurs remontées :", res.validation_logs)
        
    if res.status != ValidationStatus.ACCEPTED:
        # 2eme passage avec injection de l'erreur dans le prompt
        print("\n[Passage 2] Tentative de réparation...")
        # Pour une vraie implémentation, on enrichirait l'enveloppe avec un champ 'previous_errors'.
        # Ici on simule en ajoutant au contexte.
        error_context = "Attention, ta précédente tentative a échoué avec l'erreur : " + " ; ".join(res.validation_logs)
        env_repair = LLMInputEnvelope(
            claim_id="exp_f_1_retry",
            claim_text=claim_text,
            context_before=error_context
        )
        res_repair = llm_parser.parse_claim(env_repair)
        print(f"Nouveau statut : {res_repair.status.value}")
        
    print("\n=== FIN DE L'EXPÉRIENCE ===")

if __name__ == "__main__":
    run_experiment_f_repair()
