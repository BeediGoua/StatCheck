import json
import os

def main():
    input_path = "data/corpus/pilotes_20.json"
    output_path = "data/corpus/validation_split.jsonl"
    
    if not os.path.exists(input_path):
        print(f"File not found: {input_path}")
        return
        
    with open(input_path, "r", encoding="utf-8") as f:
        data = json.load(f)
        
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    count = 0
    with open(output_path, "w", encoding="utf-8") as f_out:
        for item in data:
            claim_id = item["claim_id"]
            text = item["annotation"]["identity"]["text"]
            
            output_obj = {
                "id": claim_id,
                "text": text,
                "gold_annotation": item["annotation"]
            }
            f_out.write(json.dumps(output_obj, ensure_ascii=False) + "\n")
            count += 1
            
    print(f"Successfully converted {count} items to {output_path}")

if __name__ == "__main__":
    main()
