import re
from typing import List, Dict, Any

def extract_populations(normalized_info: Dict[str, str], doc) -> List[Dict[str, Any]]:
    """
    Extrait les candidats de population de manière robuste.
    """
    candidates = []
    text = normalized_info["matching_normalized_text"]
    
    # 1. Tranches d'âge (ex: 15-24 ans, plus de 65 ans)
    age_matches = re.finditer(r'(?:les )?(\d{1,2}(?:\s*-\s*\d{1,2})?\s*ans)', text)
    for m in age_matches:
        candidates.append({
            "type": "AGE_GROUP",
            "span_text": m.group(1),
            "start": m.start(1),
            "end": m.end(1)
        })
        
    age_plus = re.finditer(r'(?:plus de|moins de)\s*(\d{1,2}\s*ans)', text)
    for m in age_plus:
        candidates.append({
            "type": "AGE_GROUP",
            "span_text": m.group(0),
            "start": m.start(0),
            "end": m.end(0)
        })
    
    # 2. Catégories socio-professionnelles et démographiques (dictionnaire enrichi)
    # Dans une version finale, ce lexique serait chargé depuis un JSON ou la BDM Insee
    demographics = [
        "femmes", "hommes", "jeunes", "seniors", "personnes âgées", 
        "actifs", "chômeurs", "étudiants", "retraités", 
        "ménages", "ménages modestes", "foyers",
        "salariés", "cadres", "employés", "ouvriers", "fonctionnaires", "indépendants",
        "immigrés", "étrangers"
    ]
    
    for k in demographics:
        # Match exact sur mot entier pour éviter les faux positifs (ex: "ménages" dans "aménagements")
        for m in re.finditer(rf'\b{re.escape(k)}\b', text):
            candidates.append({
                "type": "DEMOGRAPHIC",
                "span_text": m.group(0),
                "start": m.start(0),
                "end": m.end(0)
            })
            
    # Tri des candidats par position pour la lisibilité
    candidates.sort(key=lambda x: x["start"])
    return candidates
