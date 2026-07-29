import re
from typing import List, Dict, Any

def extract_territory_candidates(normalized_info: Dict[str, str], doc) -> List[Dict[str, Any]]:
    """
    Extrait les candidats géographiques via NER et mots-clés de manière robuste.
    """
    candidates = []
    text = normalized_info["matching_normalized_text"]
    
    # 1. Candidats issus de spaCy NER
    for ent in doc.ents:
        if ent.label_ == "LOC":
            candidates.append({
                "type": "NER_LOC",
                "span_text": ent.text,
                "start": ent.start_char,
                "end": ent.end_char
            })
            
    # 2. Candidats issus de règles directes (Zones non-communales qui peuvent échapper au NER)
    # Les régions, pays et zones supra/infra-nationales
    keywords = [
        "france", "france metropolitaine", "france entiere", "metropole", "outre-mer", "dom-tom",
        "union europeenne", "zone euro",
        "ile-de-france", "bretagne", "normandie", "occitanie", "nouvelle-aquitaine",
        "auvergne-rhone-alpes", "bourgogne-franche-comte", "centre-val de loire",
        "corse", "grand est", "hauts-de-france", "pays de la loire", "provence-alpes-cote d'azur",
        "allemagne", "royaume-uni", "etats-unis", "espagne", "italie"
    ]
    
    keywords.sort(key=len, reverse=True)
    
    for k in keywords:
        for m in re.finditer(rf'\b{re.escape(k)}\b', text):
            # On ajoute le mot-clé. S'il chevauche le NER, le résolveur gèrera le doublon.
            candidates.append({
                "type": "KEYWORD",
                "span_text": m.group(0),
                "start": m.start(0),
                "end": m.end(0)
            })
            
    candidates.sort(key=lambda x: x["start"])
    return candidates
