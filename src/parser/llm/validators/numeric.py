from typing import Dict, Any
import logging

from src.parser.baseline.extractors.measure import extract_measures

logger = logging.getLogger(__name__)

def validate_numeric_values(parsed_dict: Dict[str, Any]) -> None:
    """
    Niveau 2 : Vérifie que le LLM n'a pas fait d'hallucination mathématique 
    (ex: renvoyer 35 au lieu de 3.5). 
    Repasse le source_text dans l'extracteur de la baseline.
    """
    measures = parsed_dict.get("measures", [])
    
    for measure in measures:
        source_text = measure.get("source_text", "")
        llm_value = measure.get("numeric_value")
        
        if llm_value is None or not source_text:
            continue
            
        # Normalisation basique pour la baseline (virgules -> points)
        norm_text = source_text.replace(",", ".").lower()
        
        baseline_candidates = extract_measures({"matching_normalized_text": norm_text}, None)
        
        if not baseline_candidates:
            # La baseline ne trouve aucun nombre dans le texte source
            logger.warning(f"La baseline ne trouve pas de nombre dans '{source_text}'. Valeur LLM: {llm_value}.")
            # On pourrait rejeter, mais on va plutôt marquer avec un flag
            measure["validation_warning"] = "BASELINE_NO_MATCH"
            continue
            
        # On prend la première valeur extraite par la baseline
        baseline_val = baseline_candidates[0]["value"]
        
        # Gestion des millions/milliards. 
        # Si le texte contient "million", la baseline peut retourner x ou x * 1M selon la version.
        # Dans l'extracteur vu, "million" donne unit="MILLIONS" mais la valeur est x.
        # Comparons simplement les chiffres bruts significatifs si besoin, 
        # ou appliquons une tolérance stricte.
        
        # Pour faire simple, on vérifie si la baseline_val est dans llm_value (ex: 3.5 vs 3.5M)
        # Mais le cahier des charges dit qu'on doit empêcher les erreurs type "3,5" -> 35.
        
        if abs(baseline_val - llm_value) > 0.0001:
            # Incohérence trouvée !
            # Est-ce un problème d'échelle (million) ?
            if baseline_val > 0 and (llm_value / baseline_val in [1000, 1000000, 1000000000]):
                # C'est juste une résolution d'échelle, on accepte.
                pass
            elif llm_value > 0 and (baseline_val / llm_value in [1000, 1000000, 1000000000]):
                pass
            else:
                logger.warning(f"Correction numérique: {llm_value} corrigé en {baseline_val} via '{source_text}'")
                measure["numeric_value"] = baseline_val
