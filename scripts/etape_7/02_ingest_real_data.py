import os
import sys
import json
import hashlib
from pathlib import Path
import psycopg2
from sentence_transformers import SentenceTransformer

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/statcheck")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"
VECTOR_DIM = 384

def compute_text_hash(text: str) -> str:
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

def main():
    print(f"=== 02_ingest_real_data.py : Ingestion E2E ===")
    
    # 1. Load JSON
    try:
        with open('data/catalog/search_documents_real.json', 'r', encoding='utf-8') as f:
            datasets = json.load(f)
    except Exception as e:
        print(f"Erreur chargement datasets: {e}")
        return
        
    print(f"[{len(datasets)}] Datasets à ingérer.")
    
    # 2. Connect DB
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    # 3. Alter vector columns to match 384 instead of 1024
    print(f"Adaptation du schéma pour dimension {VECTOR_DIM}...")
    cur.execute(f"ALTER TABLE search_documents ALTER COLUMN embedding TYPE vector({VECTOR_DIM});")
    cur.execute(f"ALTER TABLE entity_embeddings ALTER COLUMN embedding TYPE vector({VECTOR_DIM});")
    
    # Drop and recreate search_vectorial function
    cur.execute(f"""
        CREATE OR REPLACE FUNCTION search_vectorial(query_embedding vector({VECTOR_DIM}), match_limit INT DEFAULT 50)
        RETURNS TABLE (dataset_id VARCHAR(100), similarity NUMERIC) AS $$
        BEGIN
            RETURN QUERY
            SELECT sd.dataset_id, (1 - (sd.embedding <=> query_embedding))::NUMERIC AS similarity
            FROM search_documents sd
            WHERE sd.embedding IS NOT NULL
            ORDER BY sd.embedding <=> query_embedding
            LIMIT match_limit;
        END;
        $$ LANGUAGE plpgsql;
    """)
    conn.commit()
    
    # 4. Load ML Model
    print(f"Chargement de {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    # 5. Ingest
    print("Ingestion et vectorisation en cours...")
    
    for doc in datasets:
        # Insert or update search_documents
        cur.execute("""
            INSERT INTO search_documents 
            (dataset_id, indicator_code, title, description, dimensions, embedding_text)
            VALUES (%s, %s, %s, %s, %s, %s)
            ON CONFLICT (dataset_id) DO UPDATE SET
            indicator_code = EXCLUDED.indicator_code,
            title = EXCLUDED.title,
            description = EXCLUDED.description,
            dimensions = EXCLUDED.dimensions,
            embedding_text = EXCLUDED.embedding_text;
        """, (
            doc['dataset_id'], doc['indicator_code'], doc['title'],
            doc['description'], doc['dimensions'], doc['embedding_text']
        ))
        
        text = doc['embedding_text']
        if text:
            h = compute_text_hash(text)
            
            # Check cache
            cur.execute("SELECT 1 FROM entity_embeddings WHERE model_id = %s AND text_hash = %s", (MODEL_NAME, h))
            if not cur.fetchone():
                # Encode
                vec = model.encode(text).tolist()
                cur.execute("""
                    INSERT INTO entity_embeddings (model_id, text_hash, original_text, embedding)
                    VALUES (%s, %s, %s, %s)
                """, (MODEL_NAME, h, text, vec))
                
            # Bind to search_documents
            cur.execute("""
                UPDATE search_documents 
                SET embedding = (SELECT embedding FROM entity_embeddings WHERE model_id = %s AND text_hash = %s)
                WHERE dataset_id = %s
            """, (MODEL_NAME, h, doc['dataset_id']))
            
    conn.commit()
    cur.close()
    conn.close()
    print("Ingestion réussie.")

if __name__ == "__main__":
    main()
