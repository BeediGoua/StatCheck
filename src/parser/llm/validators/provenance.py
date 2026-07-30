import re
from typing import Dict, Any

def find_nth_occurrence(text: str, sub: str, occurrence: int) -> tuple[int, int]:
    """Trouve le start/end de la n-ième occurrence d'une sous-chaîne."""
    if not sub:
        return -1, -1
        
    start_index = 0
    count = 0
    
    while True:
        idx = text.find(sub, start_index)
        if idx == -1:
            return -1, -1
            
        count += 1
        if count == occurrence:
            return idx, idx + len(sub)
            
        start_index = idx + len(sub)


def validate_provenance(raw_text: str, parsed_dict: Dict[str, Any]) -> None:
    """
    Niveau 1 : Vérifie que le source_text de chaque entité existe dans le texte brut.
    Calcule raw_start et raw_end. Supprime l'entité si le texte est introuvable.
    """
    
    # Les listes d'entités qui possèdent source_text et occurrence
    entity_lists = [
        "indicators", "populations", "territories", 
        "time_expressions", "measures", "ambiguities"
    ]
    
    for list_key in entity_lists:
        if list_key not in parsed_dict:
            continue
            
        valid_entities = []
        for entity in parsed_dict[list_key]:
            source_text = entity.get("source_text")
            occurrence = entity.get("occurrence", 1)
            
            if not source_text:
                # S'il n'y a pas de source_text, on ignore (ça ne devrait pas arriver vu le schéma, sauf si optionnel)
                valid_entities.append(entity)
                continue
                
            start, end = find_nth_occurrence(raw_text, source_text, occurrence)
            
            if start != -1:
                entity["raw_start"] = start
                entity["raw_end"] = end
                valid_entities.append(entity)
            else:
                # L'entité est une hallucination textuelle, on la rejette
                pass
                
        parsed_dict[list_key] = valid_entities
        
    # Cas particulier : operation, frequency, adjustment (qui peuvent être des objets uniques ou nuls)
    for single_key in ["operation", "frequency", "adjustment"]:
        if single_key not in parsed_dict or parsed_dict[single_key] is None:
            continue
            
        entity = parsed_dict[single_key]
        
        # Pour operation, le champ s'appelle trigger_text et trigger_occurrence
        if single_key == "operation":
            source_text = entity.get("trigger_text")
            occurrence = entity.get("trigger_occurrence", 1)
        else:
            source_text = entity.get("source_text")
            occurrence = entity.get("occurrence", 1)
            
        if source_text:
            start, end = find_nth_occurrence(raw_text, source_text, occurrence)
            if start != -1:
                entity["raw_start"] = start
                entity["raw_end"] = end
            else:
                # Hallucination
                parsed_dict[single_key] = None
                
    # Cas particulier : comparisons (liste d'opérations)
    if "comparisons" in parsed_dict:
        valid_comps = []
        for comp in parsed_dict["comparisons"]:
            source_text = comp.get("trigger_text")
            occurrence = comp.get("trigger_occurrence", 1)
            if source_text:
                start, end = find_nth_occurrence(raw_text, source_text, occurrence)
                if start != -1:
                    comp["raw_start"] = start
                    comp["raw_end"] = end
                    valid_comps.append(comp)
            else:
                # Si implicit_comparison, pas de texte, on garde
                valid_comps.append(comp)
        parsed_dict["comparisons"] = valid_comps
