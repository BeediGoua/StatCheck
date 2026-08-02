import unicodedata
import re
from typing import Dict

def _remove_accents_1_to_1(text: str) -> str:
    """Supprime les accents tout en garantissant strictement 1 caractère en entrée = 1 en sortie."""
    # En NFD, 'é' devient 'e' + '´'. On filtre les caractères de type Mn (Mark, Nonspacing).
    # Cela fonctionne parfaitement pour le français car la base fait 1 car et on drop l'accent.
    nfd_form = unicodedata.normalize('NFD', text)
    return ''.join(c for c in nfd_form if unicodedata.category(c) != 'Mn')

def normalize_text(text: str) -> Dict[str, str]:
    """
    Normalisation non destructive de la phrase selon 3 représentations :
    - raw_text : Texte original
    - display_normalized_text : Correction Unicode basique
    - matching_normalized_text : Minuscules, sans accents, tirets unifiés.
    
    Toutes les transformations doivent impérativement conserver la longueur exacte de la chaîne (1:1)
    pour que les offsets trouvés sur 'matching' soient valides sur 'raw_text'.
    """
    if not text:
        return {
            "raw_text": "",
            "display_normalized_text": "",
            "matching_normalized_text": ""
        }
        
    # ========================================================
    # 1. Display Normalized (Corrections sûres pour l'affichage)
    # ========================================================
    # Normalisation Unicode basique (NFC) pour éviter les caractères décomposés bizarres
    # Note: NFC peut parfois changer la longueur si on part d'un NFD, on assume que l'input
    # est déjà standard ou on accepte que raw_text soit la seule vraie source de vérité offset.
    # Pour garantir le 1:1 absolu par rapport au display, on fait du replace.
    display = text.replace('\xa0', ' ')
    display = display.replace('«', '"').replace('»', '"')
    
    # ========================================================
    # 2. Matching Normalized (Pour les Regex et dictionnaires)
    # ========================================================
    matching = display.lower()
    
    # Neutraliser les accents uniquement pour la comparaison
    matching = _remove_accents_1_to_1(matching)
    
    # Unification des apostrophes
    matching = matching.replace('’', "'").replace('‘', "'")
    
    # Unification des différents tirets (hyphen, en-dash, em-dash, minus) en tiret standard '-'
    # \u2010 à \u2015, \u2212
    tirets = ['\u2010', '\u2011', '\u2012', '\u2013', '\u2014', '\u2015', '\u2212']
    for t in tirets:
        matching = matching.replace(t, '-')
    
    # Décimales : Virgules entre les chiffres -> point (ex: 3,4 -> 3.4) pour préserver les décimales
    matching = re.sub(r'(\d),(\d)', r'\1.\2', matching)
    
    # Note: Les tranches comme "15-24" et les périodes "2023-Q1" sont naturellement préservées
    # car nous n'avons pas supprimé les tirets, nous les avons juste normalisés.
    # Les espaces et la casse ont été normalisés (minuscule).

    return {
        "raw_text": text,
        "display_normalized_text": display,
        "matching_normalized_text": matching
    }
