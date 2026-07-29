import re
from typing import List, Dict, Any
from dateparser.search import search_dates

def extract_times(normalized_info: Dict[str, str], doc, reference_date: str) -> List[Dict[str, Any]]:
    """
    Extrait les candidats temporels.
    """
    candidates = []
    text = normalized_info["matching_normalized_text"]
    
    # 1. Trimestres (Q1 2023)
    q_matches = re.finditer(r'([1-4])(?:er|eme)?\s*trimestre\s*(?:de\s*)?((?:19|20)\d{2})', text)
    for m in q_matches:
        candidates.append({
            "type": "EXPLICIT_QUARTER",
            "granularity": "QUARTERLY",
            "start_year": int(m.group(2)),
            "quarter": int(m.group(1)),
            "span_text": m.group(0)
        })
        
    # 2. Années (si on trouve des années explicites)
    y_matches = re.finditer(r'(?:en|annee)\s*((?:19|20)\d{2})', text)
    for m in y_matches:
        candidates.append({
            "type": "EXPLICIT_YEAR",
            "granularity": "ANNUAL",
            "start_year": int(m.group(1)),
            "span_text": m.group(0)
        })
        
    # 3. Dateparser pour le temps relatif, contraint par la reference_date
    import datetime
    base_date = datetime.datetime.now()
    if reference_date:
        try:
            base_date = datetime.datetime.strptime(reference_date, "%Y-%m-%d")
        except ValueError:
            pass
            
    dates_found = search_dates(text, languages=['fr'], settings={'RELATIVE_BASE': base_date})
    if dates_found:
        for date_str, parsed_date in dates_found:
            if len(date_str) > 4: # Filtrer les simples nombres
                candidates.append({
                    "type": "RELATIVE_DATE",
                    "granularity": "MONTHLY" if "mois" in date_str else "ANNUAL",
                    "parsed_date": parsed_date.strftime("%Y-%m-%d"),
                    "span_text": date_str
                })
                
    return candidates
