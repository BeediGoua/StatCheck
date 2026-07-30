import random
import math
from typing import List, Dict, Tuple, Any

# =====================================================================
# DÉFINITIONS FORMELLES DES MÉTRIQUES (Lot 6C / V1)
# =====================================================================
# EXACT MATCH COMPLET :
# Une prédiction est comptée en Exact Match uniquement si tous les champs 
# obligatoires correspondent au Gold après normalisation : indicateur, 
# territoire, période, opération, mesures, unités et statut d’abstention. 
# Une erreur sur un seul champ rend l’affirmation incorrecte au niveau Exact Match.
# 
# ERREUR CRITIQUE SILENCIEUSE :
# Une erreur critique silencieuse est une sortie déclarée exploitable qui 
# modifie le sens statistique de l’affirmation sans déclencher d’abstention 
# ni de signal d’incertitude : valeur, unité, signe, période, territoire, 
# population, dénominateur ou indicateur incorrect.
# 
# ABSTENTION CORRECTE :
# Le système refuse de s'engager (statut = MISSING_CONTEXT ou REJECTED) sur 
# une phrase qui ne contient effectivement pas assez de données fiables.
# 
# TAUX D'APPEL LLM :
# Pourcentage d'affirmations pour lesquelles le routeur C3 a déclenché une
# inférence LLM.
# =====================================================================


try:
    from scipy.stats import binomtest
    HAS_SCIPY = True
except ImportError:
    HAS_SCIPY = False

def bootstrap_confidence_interval_grouped(
    group_ids: List[str], 
    data: List[float], 
    num_samples: int = 1000, 
    alpha: float = 0.05
) -> Tuple[float, float]:
    """
    Calcule l'intervalle de confiance via la méthode de Bootstrap, groupé par identifiant
    pour préserver l'indépendance des échantillons (ex: paraphrases).
    """
    if not data or len(group_ids) != len(data):
        return 0.0, 0.0
        
    groups: Dict[str, List[float]] = {}
    for gid, val in zip(group_ids, data):
        if gid not in groups:
            groups[gid] = []
        groups[gid].append(val)
        
    unique_groups = list(groups.keys())
    n_groups = len(unique_groups)
    
    means = []
    for _ in range(num_samples):
        sample_groups = [random.choice(unique_groups) for _ in range(n_groups)]
        sampled_data = []
        for gid in sample_groups:
            sampled_data.extend(groups[gid])
            
        if sampled_data:
            means.append(sum(sampled_data) / len(sampled_data))
            
    if not means:
        return 0.0, 0.0
        
    means.sort()
    lower_bound = means[int(alpha / 2 * num_samples)]
    upper_bound = means[int((1 - alpha / 2) * num_samples)]
    return lower_bound, upper_bound

def mcnemar_exact_test(preds_model_a: List[bool], preds_model_b: List[bool]) -> Dict[str, float]:
    """
    Test de McNemar utilisant le test binomial exact pour les petits échantillons.
    """
    if len(preds_model_a) != len(preds_model_b):
        raise ValueError("Les listes doivent avoir la même taille.")
        
    b_count = sum(1 for a, b in zip(preds_model_a, preds_model_b) if a and not b)
    c_count = sum(1 for a, b in zip(preds_model_a, preds_model_b) if not a and b)
    n_discordant = b_count + c_count
    
    if n_discordant == 0:
        return {"p_value": 1.0, "statistic": 0.0, "discordant_pairs": 0, "model_a_better": 0, "model_b_better": 0}
        
    if HAS_SCIPY:
        result = binomtest(b_count, n_discordant, 0.5, alternative='two-sided')
        p_value = result.pvalue
        stat = float(b_count)
    else:
        chi_square = ((abs(b_count - c_count) - 1.0) ** 2) / n_discordant
        stat = chi_square
        p_value = -1.0 # Indicateur que scipy manque pour la p-value
        
    return {
        "p_value": p_value,
        "statistic": stat,
        "discordant_pairs": n_discordant,
        "model_a_better": b_count,
        "model_b_better": c_count
    }
