import re
from typing import List, Dict, Any

def extract_indicators(normalized_info: Dict[str, str], doc) -> List[Dict[str, Any]]:
    """
    Extrait les candidats d'indicateurs statistiques de manière robuste.
    """
    candidates = []
    text = normalized_info["matching_normalized_text"]
    
    # Lexique étendu des indicateurs Insee classiques (AVEC accents car conservés par normalizer)
    indicators = [
        "chômage", "taux de chômage", "inflation", "naissances", "taux de natalité",
        "entreprises", "création d'entreprises", "défaillances d'entreprises",
        "pouvoir d'achat", "croissance", "pib", "produit intérieur brut",
        "dette", "dette publique", "déficit", "déficit public",
        "espérance de vie", "mortalité", "taux de pauvreté", "pauvreté",
        "smic", "salaire moyen", "emploi", "taux d'emploi"
    ]
    
    # On trie du plus long au plus court
    indicators.sort(key=len, reverse=True)
    
    found_spans = [] 
    
    for k in indicators:
        # Match exact sur mot entier pour éviter les faux positifs
        for m in re.finditer(rf'\b{re.escape(k)}\b', text, re.IGNORECASE):
            overlap = False
            for (s, e) in found_spans:
                if m.start(0) >= s and m.end(0) <= e:
                    overlap = True
                    break
            
            if not overlap:
                candidates.append({
                    "type": "INDICATOR",
                    "span_text": m.group(0),
                    "start": m.start(0),
                    "end": m.end(0)
                })
                found_spans.append((m.start(0), m.end(0)))
            
    # Tri des candidats par position pour la lisibilité
    candidates.sort(key=lambda x: x["start"])
    return candidates
