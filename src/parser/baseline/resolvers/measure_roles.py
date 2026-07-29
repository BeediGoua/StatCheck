from typing import List, Dict, Any

def resolve_measure(candidates: List[Dict[str, Any]], normalized_info: Dict[str, str], doc) -> List[Dict[str, Any]]:
    """
    Assigne des rôles aux mesures extraites (START_VALUE, END_VALUE, CLAIMED_CHANGE, CURRENT_VALUE).
    Ex: 'est passé de 8% à 6%'
    """
    if not candidates:
        return []
        
    text = normalized_info["matching_normalized_text"]
    resolved = []
    
    for cand in candidates:
        role = "CURRENT_VALUE"
        
        # On regarde juste avant le span pour trouver des prépositions
        start_idx = cand["start"]
        context_before = text[max(0, start_idx-6):start_idx].strip()
        context_after = text[cand["end"]:min(len(text), cand["end"]+10)].strip()
        
        if context_before.endswith("de"):
            # "baisse de 2 points" ou "passé de 8%"
            if "point" in cand["unit"].lower():
                role = "ABSOLUTE_CHANGE"
            else:
                # S'il y a un 'à' après, c'est probablement START_VALUE
                if "à" in context_after or "a " in context_after:
                    role = "START_VALUE"
                else:
                    role = "CLAIMED_CHANGE"
        elif context_before.endswith("à") or context_before.endswith("a"):
            role = "END_VALUE"
        elif context_before.endswith("soit") or context_before.endswith("soit une hausse de"):
            role = "CLAIMED_CHANGE"
            
        cand["role"] = role
        resolved.append(cand)
        
    return resolved
