from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)

def validate_inference_and_deduplication(parsed_dict: Dict[str, Any]) -> None:
    """
    Niveaux 7 & 8 : Élimine les déduplications exactes et rejette les territoires/unités déduits sans preuve.
    """
    
    # 7. Déduplication
    for list_key in ["indicators", "populations", "territories", "time_expressions", "measures"]:
        if list_key not in parsed_dict:
            continue
            
        unique_items = []
        seen = set()
        
        for item in parsed_dict[list_key]:
            # Pour comparer des dictionnaires, on les transforme en tuple de (clé, valeur)
            # On ignore les champs potentiellement non hachables ou sans importance pour la déduplication
            hashable_repr = tuple(
                (k, v) for k, v in sorted(item.items()) 
                if type(v) in [str, int, float, bool] and k not in ["raw_start", "raw_end"]
            )
            
            if hashable_repr not in seen:
                seen.add(hashable_repr)
                unique_items.append(item)
                
        parsed_dict[list_key] = unique_items

    # 8. Rejet des inférences non prouvées
    # Rejet des territoires déduits sans preuve textuelle
    valid_territories = []
    for terr in parsed_dict.get("territories", []):
        if terr.get("certainty") == "IMPLICIT" and not terr.get("source_text"):
            logger.warning(f"Rejet du territoire (inférence non prouvée): {terr.get('normalized_label')}")
            continue
        valid_territories.append(terr)
    if "territories" in parsed_dict:
        parsed_dict["territories"] = valid_territories
        
    # Rejet des unités déduites sans preuve (si l'unité est devinée mais pas de source_text)
    # Dans les mesures, si c'est implicite, on pourrait forcer l'unité à UNKNOWN
    for m in parsed_dict.get("measures", []):
        if not m.get("source_text") and m.get("unit") != "UNKNOWN":
            logger.warning(f"Réinitialisation de l'unité (inférence non prouvée): {m.get('unit')} -> UNKNOWN")
            m["unit"] = "UNKNOWN"
