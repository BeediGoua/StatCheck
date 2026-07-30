import json
import random

# Real datasets from our 222 snapshot
DATASETS = [
    ("CHOMAGE-TRIM-NATIONAL", "Taux de chômage"),
    ("BALANCE-PAIEMENTS", "Balance des paiements"),
    ("CLIMAT-AFFAIRES", "Climat des affaires"),
    ("IPC-2015", "Indice des prix à la consommation"),
    ("CNA-2014-PIB", "Produit intérieur brut"),
    ("CREAT-ENT", "Créations d'entreprises"),
    ("DEFAILLANCES-ENTREPRISES", "Défaillances d'entreprises"),
    ("DETTE-TRIM-APU", "Dette des administrations publiques"),
    ("IND-PROD-INDUS", "Indice de la production industrielle"),
    ("SAL-ANN-SECT-PRIVE", "Salaires dans le secteur privé")
]

QUERIES = [
    ("Quel est le taux de chômage national actuel ?", "CHOMAGE-TRIM-NATIONAL"),
    ("Le chômage des jeunes a baissé.", "CHOMAGE-TRIM-NATIONAL"),
    ("L'indice des prix a explosé cette année.", "IPC-2015"),
    ("Combien y a-t-il eu de créations de boites en 2023 ?", "CREAT-ENT"),
    ("La dette publique a atteint un niveau record.", "DETTE-TRIM-APU"),
    ("Le PIB français s'est effondré au premier trimestre.", "CNA-2014-PIB"),
    ("Le moral des patrons est au plus bas.", "CLIMAT-AFFAIRES"),
    ("La balance commerciale est déficitaire.", "BALANCE-PAIEMENTS"),
    ("Les faillites d'entreprises explosent.", "DEFAILLANCES-ENTREPRISES"),
    ("Les salaires du privé ont augmenté avec l'inflation.", "SAL-ANN-SECT-PRIVE"),
    # Add variations and hard cases
    ("Évolution du chômage sens BIT", "CHOMAGE-TRIM-NATIONAL"),
    ("Prix à la consommation hors tabac", "IPC-2015"),
    ("Produit intérieur brut en volume", "CNA-2014-PIB"),
    ("Dette trimestrielle de l'état", "DETTE-TRIM-APU"),
    ("Les salaires des femmes dans le privé", "SAL-ANN-SECT-PRIVE"),
    ("Créations d'auto-entreprises", "CREAT-ENT"),
    ("Production industrielle manufacturière", "IND-PROD-INDUS"),
    ("Climat des affaires dans le bâtiment", "CLIMAT-AFFAIRES"),
    ("Défaillances de PME", "DEFAILLANCES-ENTREPRISES"),
    ("Taux d'intérêt de la dette publique", "DETTE-TRIM-APU") # Intentional ambiguous
]

# We need 40. We will generate 20 more by paraphrasing.
EXTRA_QUERIES = [
    ("Le chômage grimpe", "CHOMAGE-TRIM-NATIONAL"),
    ("L'inflation est terrible", "IPC-2015"),
    ("La croissance du PIB", "CNA-2014-PIB"),
    ("Je veux monter ma boite", "CREAT-ENT"),
    ("La dette de la France", "DETTE-TRIM-APU"),
    ("Les usines tournent à plein régime", "IND-PROD-INDUS"),
    ("Salaire moyen en France", "SAL-ANN-SECT-PRIVE"),
    ("Dépôts de bilan", "DEFAILLANCES-ENTREPRISES"),
    ("Excédent commercial", "BALANCE-PAIEMENTS"),
    ("Confiance des entrepreneurs", "CLIMAT-AFFAIRES"),
    ("Demandeurs d'emploi catégorie A", "CHOMAGE-TRIM-NATIONAL"),
    ("Pouvoir d'achat et salaires", "SAL-ANN-SECT-PRIVE"),
    ("Création de micro entreprises", "CREAT-ENT"),
    ("Liquidation judiciaire", "DEFAILLANCES-ENTREPRISES"),
    ("Investissement et PIB", "CNA-2014-PIB"),
    ("Prix de l'énergie", "IPC-2015"),
    ("Dette au sens de Maastricht", "DETTE-TRIM-APU"),
    ("Exportations et importations", "BALANCE-PAIEMENTS"),
    ("Production des usines automobiles", "IND-PROD-INDUS"),
    ("Perspectives économiques des chefs d'entreprise", "CLIMAT-AFFAIRES")
]

ALL_QUERIES = QUERIES + EXTRA_QUERIES
random.seed(42)
random.shuffle(ALL_QUERIES)

gold_data = []
for i, (q, ds_id) in enumerate(ALL_QUERIES):
    item = {
        "claim_id": f"val_{i:03d}",
        "query": q,
        "claim_context": {
            "required_indicator": ds_id,
            "required_dimensions": [],
            "forbidden_sources": []
        },
        "ground_truth": {
            ds_id: 3 # Perfect match
        }
    }
    gold_data.append(item)

with open("data/corpus/gold_validation.json", "w", encoding="utf-8") as f:
    json.dump(gold_data, f, ensure_ascii=False, indent=2)

print(f"Generated {len(gold_data)} queries in gold_validation.json")
