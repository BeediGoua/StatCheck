import json
from collections import Counter

def generate_gold_distribution_report(*corpus_paths: str):
    """
    Analyse les fichiers JSONL et génère le rapport officiel 
    des distributions d'annotations du Gold Retrieval 1.0.
    """
    total_claims = 0
    statuses = Counter()
    failure_reasons = Counter()
    answerabilities = Counter()
    dataset_frequencies = Counter()
    
    for path in corpus_paths:
        try:
            with open(path, 'r', encoding='utf-8') as f:
                for line in f:
                    item = json.loads(line)
                    total_claims += 1
                    ra = item.get('retrieval_annotation', {})
                    
                    status = ra.get('expected_status', 'UNANNOTATED')
                    statuses[status] += 1
                    
                    answer = ra.get('answerability', {}).get('status', 'UNKNOWN')
                    answerabilities[answer] += 1
                    
                    for fr in ra.get('failure_reasons', []):
                        failure_reasons[fr] += 1
                        
                    primary = ra.get('primary_dataset')
                    if primary and primary.get('dataset_id'):
                        dataset_frequencies[primary['dataset_id']] += 1
                        
        except FileNotFoundError:
            print(f"Avertissement : {path} introuvable.")

    print("==================================================")
    print("      RAPPORT DE DISTRIBUTION GOLD RETRIEVAL      ")
    print("==================================================")
    print(f"Total des affirmations analysées : {total_claims}")
    print("\n--- STATUTS ATTENDUS ---")
    for st, count in statuses.most_common():
        print(f"  {st}: {count} ({round(count/total_claims*100, 1)}%)")
        
    print("\n--- RÉPONDABILITÉ (Answerability) ---")
    for ans, count in answerabilities.most_common():
        print(f"  {ans}: {count}")
        
    print("\n--- MOTIFS D'ABSTENTION ---")
    for fr, count in failure_reasons.most_common():
        print(f"  {fr}: {count}")
        
    print("\n--- TOP 5 DES DATASETS LES PLUS SOLLICITÉS ---")
    for ds, count in dataset_frequencies.most_common(5):
        if ds != "TO_BE_FILLED_BY_LLM_OR_HUMAN" and ds != "":
            print(f"  {ds}: {count} occurrences")
            
    print("==================================================")
    print("Une fois tous les statuts UNANNOTATED résolus, le Gold 1.0 pourra être gelé.")

if __name__ == "__main__":
    generate_gold_distribution_report(
        'data/corpus/train.jsonl',
        'data/corpus/validation.jsonl'
    )
