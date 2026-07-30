import json
import os
import csv
from typing import Dict, List, Set

def load_gold_annotations(filepath: str) -> Dict[str, Set[str]]:
    """Charge le Gold dataset et extrait tous les dataset_ids déjà jugés par claim_id."""
    judged_datasets = {}
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            item = json.loads(line)
            cid = item['claim_id']
            ra = item.get('retrieval_annotation')
            if not ra:
                judged_datasets[cid] = set()
                continue
            
            known = set()
            # Primary
            primary = ra.get('primary_dataset')
            if primary and primary.get('dataset_id'):
                known.add(primary['dataset_id'])
            
            # Alternatives
            for alt in ra.get('acceptable_alternatives', []):
                known.add(alt['dataset_id'])
                
            for rel in ra.get('related_but_insufficient', []):
                known.add(rel['dataset_id'])
                
            # Hard negatives
            for hn in ra.get('hard_negatives', []):
                known.add(hn['dataset_id'])
                
            judged_datasets[cid] = known
            
    return judged_datasets

def generate_pooling_candidates(
    gold_path: str,
    retriever_results_paths: List[str],
    top_k: int = 50,
    output_csv: str = 'data/corpus/pooling_to_judge.csv'
):
    """
    Génère la liste d'union (Pooling) des candidats non encore annotés
    à partir de multiples sorties de moteurs de recherche.
    
    Format attendu pour les retriever_results : 
    { "claim_id": ["DATASET-1", "DATASET-2", ...] }
    """
    if not os.path.exists(gold_path):
        print(f"Erreur: {gold_path} n'existe pas.")
        return
        
    judged = load_gold_annotations(gold_path)
    
    # claim_id -> set of candidate dataset_ids
    pooled_candidates = {cid: set() for cid in judged.keys()}
    
    for res_path in retriever_results_paths:
        if not os.path.exists(res_path):
            print(f"Avertissement: Le fichier de résultats {res_path} n'existe pas encore. Ignoré.")
            continue
            
        with open(res_path, 'r', encoding='utf-8') as f:
            results = json.load(f)
            for cid, dataset_list in results.items():
                if cid in pooled_candidates:
                    # Prendre seulement le top K du moteur
                    top_datasets = dataset_list[:top_k]
                    for ds_id in top_datasets:
                        pooled_candidates[cid].add(ds_id)

    # Filtrer ceux déjà jugés et préparer l'export
    rows_to_judge = []
    total_new_candidates = 0
    
    for cid, candidates in pooled_candidates.items():
        unjudged = candidates - judged.get(cid, set())
        for ds_id in unjudged:
            rows_to_judge.append({
                'claim_id': cid,
                'unjudged_dataset_id': ds_id,
                'relevance_score_to_fill': '', # 0, 1, 2 ou 3
                'justification': ''
            })
            total_new_candidates += 1

    # Exporter en CSV
    if rows_to_judge:
        os.makedirs(os.path.dirname(output_csv), exist_ok=True)
        with open(output_csv, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=['claim_id', 'unjudged_dataset_id', 'relevance_score_to_fill', 'justification'])
            writer.writeheader()
            writer.writerows(rows_to_judge)
        print(f"Succès : {total_new_candidates} candidats non annotés exportés dans {output_csv}.")
        print("L'annotateur humain doit remplir ce CSV. Ces jugements seront ensuite réinjectés dans le Gold.")
    else:
        print("Aucun nouveau candidat à juger. Soit les fichiers de résultats sont vides, soit le Gold couvre déjà tout le Top 50.")

if __name__ == "__main__":
    # Ce script sera exécuté à l'Étape 3 et 4 quand nous aurons nos résultats de requêtes (lexical et vectoriel).
    # Exemple de chemins de fichiers simulés :
    lexical_mock_path = "results/lexical_top50_mock.json"
    vector_mock_path = "results/vector_top50_mock.json"
    
    # Créons des mocks fictifs pour démontrer que le pooling fonctionne immédiatement
    os.makedirs("results", exist_ok=True)
    with open(lexical_mock_path, 'w', encoding='utf-8') as f:
        json.dump({"MVP-018": ["NAISSANCES-ANNUEL", "DECES-MORTALITE", "POPULATION-TOTALE"]}, f)
    with open(vector_mock_path, 'w', encoding='utf-8') as f:
        json.dump({"MVP-018": ["POPULATION-TOTALE", "MARIAGES-DIVORCES", "NAISSANCES-ANNUEL"]}, f)
        
    generate_pooling_candidates(
        gold_path="data/corpus/train.jsonl",
        retriever_results_paths=[lexical_mock_path, vector_mock_path],
        top_k=50,
        output_csv="data/corpus/pooling_to_judge.csv"
    )
