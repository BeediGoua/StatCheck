import re
import dateparser
from typing import Dict, Any

def extract_time(normalized_text: str, doc) -> Dict[str, Any]:
    """
    Extrait les informations temporelles d'une phrase normalisée.
    Utilise dateparser pour parser des dates complexes.
    """
    result = {
        "period_explicit": "UNKNOWN",
        "period_relative": None,
        "granularity": "UNKNOWN"
    }
    
    # 1. Trimestres (ex: 1er trimestre 2022, T3 2023)
    q_match = re.search(r'([1-4])(?:er|eme)?\s*trimestre\s*(?:de\s*)?((?:19|20)\d{2})', normalized_text)
    if not q_match:
        q_match = re.search(r'(?:t|q)([1-4])\s*((?:19|20)\d{2})', normalized_text)
        
    if q_match:
        result["period_explicit"] = f"Q{q_match.group(1)} {q_match.group(2)}"
        result["granularity"] = "QUARTERLY"
        return result
        
    # 2. Mois + Année (ex: aout 2022, janvier 2024)
    months = ["janvier", "fevrier", "mars", "avril", "mai", "juin", 
              "juillet", "aout", "septembre", "octobre", "novembre", "decembre"]
    for m in months:
        m_match = re.search(rf'{m}\s+((?:19|20)\d{{2}})', normalized_text)
        if m_match:
            result["period_explicit"] = f"{m} {m_match.group(1)}"
            result["granularity"] = "MONTHLY"
            return result

    # 3. Année seule via Regex basique
    y_match = re.search(r'(?:en|annee)\s*((?:19|20)\d{2})', normalized_text)
    if y_match:
        result["period_explicit"] = y_match.group(1)
        result["granularity"] = "ANNUAL"
        return result
        
    y_raw_match = re.search(r'((?:19|20)\d{2})', normalized_text)
    if y_raw_match:
        result["period_explicit"] = y_raw_match.group(1)
        result["granularity"] = "ANNUAL"
        return result
        
    # 4. Expressions relatives avec dateparser ("le mois dernier")
    # Dateparser.search.search_dates trouve les dates dans le texte
    from dateparser.search import search_dates
    dates_found = search_dates(normalized_text, languages=['fr'])
    if dates_found:
        # Prenons la première expression qui ressemble à une date relative
        for date_str, parsed_date in dates_found:
            # On ignore les années simples qui sont souvent prises comme heures par dateparser
            if len(date_str) > 4: 
                result["period_relative"] = date_str
                # Si le mois est mentionné, c'est sûrement mensuel
                if "mois" in date_str:
                    result["granularity"] = "MONTHLY"
                elif "trimestre" in date_str:
                    result["granularity"] = "QUARTERLY"
                else:
                    result["granularity"] = "ANNUAL"
                return result

    # 5. Fallbacks simples
    if "cette annee" in normalized_text:
        result["period_relative"] = "cette année"
        result["granularity"] = "ANNUAL"
    elif "depuis" in normalized_text:
        result["period_relative"] = re.search(r'depuis[^\.]*', normalized_text).group(0)
    elif "sur un an" in normalized_text:
        result["period_relative"] = "sur un an"
        result["granularity"] = "MONTHLY"
        
    return result
