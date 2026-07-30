import os
import hashlib
import json
from datetime import datetime

# TODO: pip install sentence-transformers psycopg2-binary
try:
    from sentence_transformers import SentenceTransformer
    import psycopg2
    HAS_DEPS = True
except ImportError:
    HAS_DEPS = False
    print("Dependencies 'sentence-transformers' or 'psycopg2' are missing.")
    print("Falling back to mock mode for embeddings generation.")

# Model multilingue recommandé (BGE-M3 produit des vecteurs de dimension 1024)
MODEL_NAME = "BAAI/bge-m3"

def compute_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def generate_embeddings():
    print(f"Chargement du modèle d'embedding : {MODEL_NAME}...")
    if HAS_DEPS:
        model = SentenceTransformer(MODEL_NAME)
    else:
        model = None
        
    # Ici, nous devrions nous connecter à PostgreSQL pour récupérer les textes
    # de search_documents (colonne embedding_text) qui n'ont pas encore d'embedding.
    # Pour l'exemple, nous simulons la récupération :
    
    documents_to_embed = [
        {"dataset_id": "CHOMAGE-TRIM", "embedding_text": "Taux de chômage trimestriel au sens du BIT. Dimensions: Sexe, Âge."},
        {"dataset_id": "PIB-ANNUEL", "embedding_text": "Produit Intérieur Brut (PIB) annuel en volume. Dimensions: Secteur d'activité."}
    ]
    
    print(f"{len(documents_to_embed)} documents nécessitent un embedding.")
    
    for doc in documents_to_embed:
        text = doc['embedding_text']
        text_hash = compute_text_hash(text)
        
        print(f"\nTraitement du document {doc['dataset_id']} (hash: {text_hash[:8]}...)")
        
        # Hachage incrémental : on vérifierait d'abord dans entity_embeddings si text_hash existe.
        # Si non, on calcule l'embedding :
        if model:
            # Génération du vecteur réel (dimension 1024)
            embedding_vector = model.encode(text).tolist()
            print(f"Vecteur généré avec succès (dimension: {len(embedding_vector)}).")
        else:
            # Vecteur factice pour le mock
            embedding_vector = [0.0] * 1024
            embedding_vector[0] = 1.0
            print("Vecteur factice généré (mode MOCK).")
            
        # Ensuite, on insérerait dans entity_embeddings :
        # INSERT INTO entity_embeddings (text_hash, original_text, embedding) VALUES (...)
        
        # Et on mettrait à jour search_documents :
        # UPDATE search_documents SET embedding = ... WHERE dataset_id = doc['dataset_id']
        
    print("\nGénération des vecteurs terminée avec succès.")

if __name__ == "__main__":
    generate_embeddings()
