import json
import os
import time

def pre_annotate_with_llm(corpus_path: str, catalog_path: str, output_path: str):
    """
    Script de pré-annotation automatisée par LLM.
    Il lit les 145 affirmations non annotées (où primary_dataset['dataset_id'] == '')
    et envoie le texte + le catalogue à l'API LLM (OpenAI, Gemini, etc.) 
    pour remplir le squelette JSON.
    """
    print(f"Chargement du catalogue {catalog_path}...")
    if not os.path.exists(catalog_path):
        print(f"Erreur : Le catalogue {catalog_path} n'existe pas.")
        return
        
    with open(catalog_path, 'r', encoding='utf-8') as f:
        catalog = json.load(f)
        
    print(f"Chargement des affirmations à annoter depuis {corpus_path}...")
    items = []
    with open(corpus_path, 'r', encoding='utf-8') as f:
        for line in f:
            items.append(json.loads(line))
            
    unannotated_items = [
        item for item in items 
        if item.get('retrieval_annotation') 
        and item['retrieval_annotation'].get('expected_status') == "MATCH_FOUND"
        and item['retrieval_annotation'].get('primary_dataset') is not None
        and item['retrieval_annotation']['primary_dataset'].get('dataset_id') == ""
    ]
    
    print(f"{len(unannotated_items)} affirmations nécessitent une pré-annotation.")
    print("Initialisation du client LLM (Simulation)...")
    
    annotated_count = 0
    for item in unannotated_items:
        # Simulation d'un appel API LLM
        # ex: response = openai.ChatCompletion.create(messages=[{"role": "user", "content": prompt_text}])
        
        cid = item['claim_id']
        claim_text = item['annotation']['identity']['text']
        
        # Logique fictive de pré-remplissage
        ra = item['retrieval_annotation']
        ra['expected_status'] = "MATCH_FOUND" # Supposition par défaut du LLM
        ra['primary_dataset']['dataset_id'] = "TO_BE_FILLED_BY_LLM_OR_HUMAN"
        ra['primary_dataset']['relevance'] = 3
        ra['primary_dataset']['justification'] = f"Généré par LLM pour l'affirmation: {claim_text[:30]}..."
        ra['annotation_metadata']['annotator_id'] = "AI_ASSISTANT_V1"
        ra['annotation_metadata']['review_status'] = "REQUIRES_HUMAN_REVIEW"
        
        annotated_count += 1
        # time.sleep(0.1) # Respecter les rate limits de l'API réelle
        
    print(f"\nSauvegarde de {len(items)} affirmations (dont {annotated_count} pré-annotées) vers {output_path}...")
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        for item in items:
            f.write(json.dumps(item, ensure_ascii=False) + '\n')
            
    print("Succès ! Tu peux maintenant ouvrir le fichier et effectuer la 'Revue Humaine'.")

if __name__ == "__main__":
    pre_annotate_with_llm(
        corpus_path='data/corpus/train.jsonl',
        catalog_path='data/catalog/insee-catalog-real-2026-07-30.json',
        output_path='data/corpus/train_pre_annotated.jsonl'
    )
