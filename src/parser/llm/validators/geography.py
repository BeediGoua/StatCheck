from typing import Dict, Any
import logging
import re

logger = logging.getLogger(__name__)

def validate_geography(parsed_dict: Dict[str, Any]) -> None:
    """
    Niveau 4 : S'assure que le span territorial ne contient pas de codes COG inventés.
    """
    territories = parsed_dict.get("territories", [])
    
    valid_territories = []
    for terr in territories:
        source_text = terr.get("source_text", "")
        if not source_text:
            valid_territories.append(terr)
            continue
            
        # Si le texte source est juste un nombre à 2 ou 5 chiffres (ex: 75, 75001) 
        # et que le label normalisé est une ville, il est fort probable que le LLM 
        # a halluciné un code COG ou postal sans preuve explicite s'il l'a converti.
        # Mais le plus important : le `source_text` ne doit pas être "75" si le texte original ne contient que "75"
        # mais que le LLM l'a normalisé en "Paris" sans que Paris soit écrit. 
        # En fait le vrai garde-fou c'est : rejeter les labels normalisés qui ressemblent à des codes INSEE/COG s'ils ne sont pas dans le texte.
        # Mais le LLM a l'interdiction de générer des codes COG (règle 6).
        
        normalized = terr.get("normalized_label", "")
        # Vérification si le LLM a transgressé la règle 6 (COG)
        if re.match(r'^\d{2,5}$', normalized):
            logger.warning(f"Rejet du territoire: Le LLM a généré un code numérique '{normalized}'.")
            continue
            
        valid_territories.append(terr)
        
    parsed_dict["territories"] = valid_territories
