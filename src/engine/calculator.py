from typing import List, Optional
from ..models.observation import Observation

class Calculator:
    """
    Moteur de calcul déterministe. 
    Prend en entrée une liste d'observations et effectue des opérations statistiques.
    """
    
    @staticmethod
    def get_value(observations: List[Observation], period: str) -> Optional[float]:
        """
        Retourne la valeur exacte pour une période donnée.
        """
        for obs in observations:
            if obs.period == period:
                return obs.value
        return None
        
    @staticmethod
    def relative_variation(observations: List[Observation], start_period: str, end_period: str) -> Optional[float]:
        """
        Calcule la variation relative (en pourcentage) entre deux périodes.
        Formule : ((Valeur_Arrivée - Valeur_Départ) / Valeur_Départ) * 100
        """
        start_val = Calculator.get_value(observations, start_period)
        end_val = Calculator.get_value(observations, end_period)
        
        if start_val is None or end_val is None:
            return None
            
        if start_val == 0:
            raise ZeroDivisionError("La valeur de départ est 0, impossible de calculer un taux de variation.")
            
        variation = ((end_val - start_val) / start_val) * 100
        return round(variation, 2)
        
    @staticmethod
    def point_variation(observations: List[Observation], start_period: str, end_period: str) -> Optional[float]:
        """
        Calcule la variation en points entre deux périodes. (Souvent utilisé pour les Taux de chômage).
        Formule : Valeur_Arrivée - Valeur_Départ
        """
        start_val = Calculator.get_value(observations, start_period)
        end_val = Calculator.get_value(observations, end_period)
        
        if start_val is None or end_val is None:
            return None
            
        variation = end_val - start_val
        return round(variation, 2)

    @staticmethod
    def ratio(observations: List[Observation], numerator_period: str, denominator_period: str) -> Optional[float]:
        """
        Calcule le ratio entre deux périodes (ex: "deux fois plus").
        Formule : Valeur_Numérateur / Valeur_Dénominateur
        """
        num_val = Calculator.get_value(observations, numerator_period)
        den_val = Calculator.get_value(observations, denominator_period)
        
        if num_val is None or den_val is None:
            return None
            
        if den_val == 0:
            raise ZeroDivisionError("Le dénominateur est 0, impossible de calculer le ratio.")
            
        return round(num_val / den_val, 2)
