def apply_deterministic_reranker(candidates, claim_context, cosine_threshold=None):
    """
    Reranker Déterministe : Applique des règles métier strictes sur le Top issu du RRF
    via un tri lexicographique (Solution A).
    
    candidates: Liste de dictionnaires contenant {'dataset_id': str, 'rrf_score': float, 'metadata': dict, 'cosine_distance': float}
    claim_context: Dictionnaire contenant les contraintes extraites de l'affirmation 
                   (ex: {'required_indicator': 'CHOMAGE', 'required_dimensions': ['AGE'], 'forbidden_sources': []})
    cosine_threshold: Seuil dynamique d'abstention (ex: 0.4). Si le meilleur candidat a une distance > seuil, le système s'abstient.
    """
    results = []
    
    # Variables pour évaluer l'abstention globale
    valid_candidates_count = 0
    all_missing_required_dim = True
    
    for candidate in candidates:
        dataset_id = candidate['dataset_id']
        meta = candidate['metadata']
        base_score = candidate['rrf_score']
        cosine_dist = candidate.get('cosine_distance', 0.5)
        
        is_rejected = False
        rejection_reason = None
        has_exact_indicator = False
        satisfied_dimensions_count = 0
        
        # 1. Contraintes Dures (Rejet immédiat)
        if not meta.get('is_active', True):
            is_rejected = True
            rejection_reason = "Dataset inactif"
            
        elif meta.get('source') in claim_context.get('forbidden_sources', []):
            is_rejected = True
            rejection_reason = f"Source interdite ({meta.get('source')})"
            
        elif not all(dim in meta.get('dimensions', []) for dim in claim_context.get('required_dimensions', [])):
            is_rejected = True
            rejection_reason = "Dimension indispensable absente"
        
        justification = [f"Score RRF initial: {base_score:.4f}"]
        
        if not is_rejected:
            valid_candidates_count += 1
            all_missing_required_dim = False
            
            # 2. Analyse des attributs métier (pour le tri lexicographique)
            if meta.get('indicator_code') == claim_context.get('required_indicator'):
                has_exact_indicator = True
                justification.append("Niveau 2: Indicateur exact")
            
            for req_dim in claim_context.get('required_dimensions', []):
                if req_dim in meta.get('dimensions', []):
                    satisfied_dimensions_count += 1
                    
            if satisfied_dimensions_count > 0:
                justification.append(f"Niveau 3: {satisfied_dimensions_count} dimension(s) satisfaite(s)")
                
            justification.append(f"Niveau 4: Départage RRF ({base_score:.4f})")
            
            # Le tuple magique du tri lexicographique
            final_score = (1, int(has_exact_indicator), satisfied_dimensions_count, base_score)
        else:
            final_score = (0, 0, 0, base_score)
            justification.append(f"REJETÉ: {rejection_reason}")
            
        results.append({
            'dataset_id': dataset_id,
            'rrf_score': base_score,
            'deterministic_score': final_score, # C'est maintenant un TUPLE
            'is_rejected': is_rejected,
            'justification': "\n  ".join(justification),
            'cosine_distance': cosine_dist
        })
        
    # Tri par le nouveau score déterministe (Le tuple gère naturellement les priorités 1, 2, 3 puis 4)
    results.sort(key=lambda x: x['deterministic_score'], reverse=True)
    
    # 3. Logique d'Abstention Sécurisée
    abstention = False
    abstention_reason = None
    
    if valid_candidates_count == 0:
        abstention = True
        if all_missing_required_dim:
            abstention_reason = "Dimension indispensable manquante dans TOUS les candidats et/ou conflits de contraintes dures."
        else:
            abstention_reason = "Conflit de contraintes dures sur tous les candidats."
    elif valid_candidates_count > 0 and cosine_threshold is not None:
        # On vérifie si la distance cosinus du *meilleur* candidat n'est pas aberrante
        top_candidate = results[0]
        if top_candidate['cosine_distance'] > cosine_threshold:
            abstention = True
            abstention_reason = f"Meilleur candidat ({top_candidate['dataset_id']}) rejeté car distance cosinus aberrante ({top_candidate['cosine_distance']:.4f} > {cosine_threshold})."

    return {
        'abstention': abstention,
        'abstention_reason': abstention_reason,
        'ranked_results': results
    }


def demo_reranker():
    print("--- DÉMO : RERANKER DÉTERMINISTE (TRi LEXICOGRAPHIQUE) ---\n")
    
    # Contexte métier d'une affirmation utilisateur
    claim_context = {
        'required_indicator': 'CHOMAGE_BIT',
        'required_dimensions': ['AGE', 'SEXE'],
        'forbidden_sources': ['SOURCE_OBSOLETE']
    }
    print(f"Contraintes de l'affirmation : {claim_context}\n")
    
    # Candidats mockés sortant de l'étape 5 (RRF)
    candidates = [
        {
            'dataset_id': 'DATASET_A', 
            'rrf_score': 0.05, 
            'cosine_distance': 0.15,
            'metadata': {'indicator_code': 'CHOMAGE_BIT', 'dimensions': ['AGE', 'SEXE', 'REG'], 'is_active': True, 'source': 'INSEE'}
        },
        {
            'dataset_id': 'DATASET_B', 
            'rrf_score': 0.045, 
            'cosine_distance': 0.2,
            'metadata': {'indicator_code': 'CHOMAGE_BIT', 'dimensions': ['AGE'], 'is_active': True, 'source': 'INSEE'} # Manque SEXE -> REJETÉ
        },
        {
            'dataset_id': 'DATASET_C', 
            'rrf_score': 0.04, 
            'cosine_distance': 0.1,
            'metadata': {'indicator_code': 'POPULATION', 'dimensions': ['AGE', 'SEXE'], 'is_active': True, 'source': 'INSEE'} # Mauvais indicateur mais valide
        }
    ]
    
    output = apply_deterministic_reranker(candidates, claim_context, cosine_threshold=0.4)
    
    print(f"ABSTENTION : {output['abstention']}")
    if output['abstention']:
        print(f"Raison : {output['abstention_reason']}")
        
    print("\nCLASSEMENT FINAL JUSTIFIÉ :")
    for i, res in enumerate(output['ranked_results']):
        print(f"\nRang {i+1} : {res['dataset_id']}")
        print(f"  Tuple de score : {res['deterministic_score']}")
        print(f"  {res['justification']}")

if __name__ == "__main__":
    demo_reranker()
