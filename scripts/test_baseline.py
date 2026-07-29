import json
from src.parser.baseline.baseline_parser import parse_claim_baseline

def main():
    test_claims = [
        "Le chômage est passé de 8% à 6%, soit une baisse de 2 points.", # Roles
        "L'inflation a baissé de -3% l'année dernière.", # Contradiction direction/signe
        "Il semblerait que le taux d'activité des femmes soit à son record.", # Pas de territoire
        "La croissance ne baisse pas en France cette année, elle est deux fois plus forte en prix constants." # Négation, ratio, adjustment
    ]
    
    print("=== Test de la Baseline Hybride Exhaustive ===\n")
    for text in test_claims:
        print(f"Phrase : '{text}'")
        res = parse_claim_baseline(text, reference_date="2024-01-01")
        print(json.dumps(res, indent=2, ensure_ascii=False))
        print("-" * 50)

if __name__ == "__main__":
    main()
