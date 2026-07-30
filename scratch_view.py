import json

with open('data/corpus/train.jsonl', encoding='utf-8') as f:
    for i in range(15):
        line = f.readline()
        if not line: break
        item = json.loads(line)
        print(f"{item['claim_id']}: {item['annotation']['identity']['text']}")
