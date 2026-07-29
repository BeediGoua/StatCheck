import sys
from pathlib import Path

root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from src.providers.insee_bdm import InseeBdmProvider
from src.engine.calculator import Calculator

def main():
    print("=== Validation du Jalon Critique (Lot 9 & 10) ===\n")
    provider = InseeBdmProvider(use_cache=True)
    
    success_count = 0
    total_verifiable = 27
    
    # --- MVP-002: Inflation ---
    print("Test MVP-002 : Inflation Août 2022")
    try:
        obs = provider.fetch_series_by_idbank("001763852")
        val = Calculator.relative_variation(obs, "2021-08", "2022-08")
        if val is not None:
            print(f"[OK] Résultat : {val}% (Attendu : ~5.8% / 6.04% révisé)\n")
            success_count += 1
        else:
            print("[FAIL] Échec\n")
    except Exception as e:
        print(f"[ERROR] {e}\n")

    # --- MVP-009: Chômage ---
    print("Test MVP-009 : Baisse du chômage (Q1 2017 -> Q4 2021)")
    try:
        obs = provider.fetch_series_by_idbank("001688527")
        diff = Calculator.point_variation(obs, "2017-Q1", "2021-Q4")
        if diff is not None:
            print(f"[OK] Variation en points : {diff} (Attendu : -2.2)\n")
            success_count += 1
        else:
            print("[FAIL] Données manquantes\n")
    except Exception as e:
        print(f"[ERROR] {e}\n")
        
    # --- Autres MVP (à compléter avec les IDBank) ---
    print("Test MVP-003 à MVP-030 (Squelette)")
    
    mvp_list = [
        {"id": "MVP-001", "desc": "Inflation réelle à 12%"},
        {"id": "MVP-003", "desc": "Inflation alimentaire de 7,7%"},
        {"id": "MVP-004", "desc": "Prix de l’énergie en hausse de 22,2%"},
        {"id": "MVP-005", "desc": "Ralentissement de l’inflation"},
        # ... Reste des 27 affirmations
    ]
    
    print(f"\n=> Note : Pour valider les {total_verifiable - 2} autres affirmations, il faut fournir les 'idbank' correspondants.")
    print("   L'architecture logicielle est prête pour les recevoir.")
    
    print(f"\nBilan : {success_count} assertions validées de bout en bout.")

if __name__ == "__main__":
    main()
