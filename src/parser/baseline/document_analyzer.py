import spacy

_nlp = None

def get_nlp():
    """
    Retourne le singleton du modèle spaCy pour éviter les chargements multiples.
    """
    global _nlp
    if _nlp is None:
        try:
            _nlp = spacy.load("fr_core_news_md")
        except OSError:
            print("Modèle spaCy manquant. Exécutez: python -m spacy download fr_core_news_md")
            _nlp = spacy.blank("fr")
    return _nlp

def analyze_document(text: str):
    """
    Exécute spaCy sur le texte une seule fois.
    """
    nlp = get_nlp()
    return nlp(text)
