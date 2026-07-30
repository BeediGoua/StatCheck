import json
import sys

def validate_gold_file(filepath):
    errors = []
    with open(filepath, 'r', encoding='utf-8') as f:
        for idx, line in enumerate(f):
            item = json.loads(line)
            cid = item['claim_id']
            ra = item.get('retrieval_annotation')
            
            if not ra:
                errors.append(f"{cid}: Missing retrieval_annotation")
                continue
                
            status = ra.get('expected_status')
            primary = ra.get('primary_dataset')
            
            # Skip empty skeletons (unannotated)
            if primary and primary.get('dataset_id') == '' and status == 'MATCH_FOUND':
                continue
                
            if status == 'NO_RELEVANT_DATASET':
                if primary is not None:
                    errors.append(f"{cid}: NO_RELEVANT_DATASET but primary_dataset is not null")
                if not ra.get('failure_reasons'):
                    errors.append(f"{cid}: NO_RELEVANT_DATASET but missing failure_reasons")
                    
            elif status == 'MATCH_FOUND':
                if not primary or not primary.get('dataset_id'):
                    errors.append(f"{cid}: MATCH_FOUND but primary_dataset_id is empty")
                if primary and primary.get('relevance') != 3:
                    errors.append(f"{cid}: primary_dataset relevance should be 3, got {primary.get('relevance')}")
            
            # Check alternatives relevance
            for alt in ra.get('acceptable_alternatives', []):
                if alt.get('relevance') not in [2, 3]:
                    errors.append(f"{cid}: acceptable alternative must have relevance 2 or 3")
                    
            for alt in ra.get('related_but_insufficient', []):
                if alt.get('relevance') != 1:
                    errors.append(f"{cid}: related_but_insufficient must have relevance 1")
                    
    return errors

all_errors = []
all_errors.extend(validate_gold_file('data/corpus/train.jsonl'))
all_errors.extend(validate_gold_file('data/corpus/validation.jsonl'))

if all_errors:
    print("Gold Validation Failed:")
    for e in all_errors:
        print(f" - {e}")
    sys.exit(1)
else:
    print("Gold Validation Passed! No logical inconsistencies found.")
