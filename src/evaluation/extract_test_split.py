import json
import os

def create_test_split():
    # Load validation IDs to exclude them
    validation_ids = set()
    with open("data/corpus/pilotes_20.json", "r", encoding="utf-8") as f:
        pilotes = json.load(f)
        for p in pilotes:
            validation_ids.add(p.get("claim_id"))
            
    test_items = []
    with open("data/corpus/corpus_complet.json", "r", encoding="utf-8") as f:
        corpus = json.load(f)
        for item in corpus:
            if item.get("claim_id") not in validation_ids:
                test_items.append(item)
                if len(test_items) == 40:
                    break
                    
    with open("data/corpus/test_split.jsonl", "w", encoding="utf-8") as f:
        for item in test_items:
            f.write(json.dumps(item, ensure_ascii=False) + "\n")
            
    print(f"Extraction terminée: {len(test_items)} items écrits dans data/corpus/test_split.jsonl")

if __name__ == "__main__":
    create_test_split()
