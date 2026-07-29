import unicodedata
import re
from typing import Dict

def normalize_text(text: str) -> Dict[str, str]:
    """
    Normalisation non destructive de la phrase selon 3 représentations :
    - raw_text : Texte original
    - display_normalized_text : Correction des espaces insécables et guillemets (pour l'affichage propre)
    - matching_normalized_text : Minuscules, apostrophes lissées, ponctuation numérique unifiée (pour les RegEx). Les accents sont conservés.
    
    IMPORTANT: Toutes les transformations sont strictement 1:1 (même nombre de caractères)
    pour garantir que les offsets du matching_text soient identiques aux offsets du raw_text.
    """
    if not text:
        return {
            "raw_text": "",
            "display_normalized_text": "",
            "matching_normalized_text": ""
        }
        
    # display_normalized_text (1:1 replacements)
    display = text.replace('\xa0', ' ')
    display = display.replace('«', '"').replace('»', '"')
    
    # matching_normalized_text (1:1 replacements)
    matching = display.lower()
    # Unification des apostrophes
    matching = matching.replace('’', "'").replace('‘', "'")
    # Virgules entre les chiffres -> point (ex: 3,4 -> 3.4)
    matching = re.sub(r'(\d),(\d)', r'\1.\2', matching)
    
    return {
        "raw_text": text,
        "display_normalized_text": display,
        "matching_normalized_text": matching
    }
