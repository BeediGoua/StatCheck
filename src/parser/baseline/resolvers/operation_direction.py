from typing import Dict, Any, List

def resolve_operation_direction(doc) -> Dict[str, Any]:
    """
    Croise l'analyse linguistique (lemmes) et la négation pour déduire la direction et la polarité.
    Ne crée pas de fausses directions type "NOT_DECREASE".
    """
    lemmas = [token.lemma_.lower() for token in doc if token.pos_ in ["VERB", "NOUN", "ADJ"]]
    
    # 1. Détection de la Direction de base
    direction = "STABLE"
    if any(l in lemmas for l in ["augmenter", "hausse", "croître", "croissance", "bondir", "progresser", "haut"]):
        direction = "INCREASE"
    elif any(l in lemmas for l in ["baisser", "diminuer", "reculer", "baisse", "chute", "perdre", "faible", "bas"]):
        direction = "DECREASE"
        
    # 2. Détection de la Polarité (Négation)
    polarity = "POSITIVE"
    negation_words = ["ne", "n'", "pas", "aucun", "jamais"]
    has_negation = False
    
    # Heuristique simple: on cherche "ne...pas" dans le texte original
    text_lower = doc.text.lower()
    if " pas " in text_lower or "n'" in text_lower or "ne " in text_lower:
        # Simplification: si la phrase contient une négation, on l'attribue à l'opération
        polarity = "NEGATED"

    return {
        "type": "CHANGE",
        "direction": direction,
        "polarity": polarity
    }
