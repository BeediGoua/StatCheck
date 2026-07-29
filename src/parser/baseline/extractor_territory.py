def extract_territory(normalized_text: str, doc) -> str:
    """
    Identifie le territoire mentionné (ex: France métropolitaine).
    Retourne "France" par défaut.
    Utilise spaCy pour détecter les entités nommées (LOC).
    """
    if "metropole" in normalized_text or "metropolitaine" in normalized_text:
        return "France métropolitaine"
        
    regions_keywords = ["ile-de-france", "bretagne", "normandie", "occitanie", "nouvelle-aquitaine",
                        "auvergne-rhone-alpes", "bourgogne-franche-comte", "centre-val de loire",
                        "corse", "grand est", "hauts-de-france", "pays de la loire", "provence-alpes-cote d'azur"]
               
    # On regarde les entités LOC détectées par spaCy
    for ent in doc.ents:
        if ent.label_ == "LOC":
            loc_lower = ent.text.lower()
            if "france" in loc_lower:
                continue # On laisse la logique par défaut ou la métropole
            return ent.text.title()

    # Fallback par mots-clés
    for r in regions_keywords:
        if r in normalized_text:
            return r.title()
            
    return "France"
