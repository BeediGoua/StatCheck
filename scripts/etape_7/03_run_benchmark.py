import os
import sys
import json
import time
import math
from pathlib import Path
import psycopg2
import numpy as np
from sentence_transformers import SentenceTransformer

root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.append(str(root_dir))

from scripts.etape_6.deterministic_reranker import apply_deterministic_reranker
from scripts.etape_7.evaluate_retrieval import evaluate_metrics

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/statcheck")
MODEL_NAME = "paraphrase-multilingual-MiniLM-L12-v2"

def compute_percentile(data, p):
    if not data: return 0.0
    return np.percentile(data, p)

def execute_fts(cur, query_text):
    # Very basic conversion to tsquery (ANDing words)
    words = [w for w in query_text.replace("'", " ").split() if len(w)>2]
    tsquery = ' & '.join(words)
    if not tsquery: tsquery = "statistique" # Fallback
    
    cur.execute("""
        SELECT dataset_id, ts_rank_cd(lexical_vector, to_tsquery('french_unaccent', %s)) AS score,
               title, description, indicator_code, dimensions, modalities
        FROM search_documents
        WHERE lexical_vector @@ to_tsquery('french_unaccent', %s)
        ORDER BY score DESC LIMIT 50;
    """, (tsquery, tsquery))
    
    results = []
    for row in cur.fetchall():
        results.append({
            'dataset': {
                'dataset_id': row[0],
                'title': row[2],
                'description': row[3],
                'indicator_code': row[4],
                'dimensions': row[5],
                'modalities': row[6]
            },
            'score': row[1]
        })
    return results

def execute_vector(cur, vec):
    # Ensure float list
    vec_list = [float(v) for v in vec]
    cur.execute("""
        SELECT dataset_id, (1 - (embedding <=> %s::vector))::NUMERIC AS similarity,
               title, description, indicator_code, dimensions, modalities
        FROM search_documents
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> %s::vector
        LIMIT 50;
    """, (vec_list, vec_list))
    
    results = []
    for row in cur.fetchall():
        results.append({
            'dataset': {
                'dataset_id': row[0],
                'title': row[2],
                'description': row[3],
                'indicator_code': row[4],
                'dimensions': row[5],
                'modalities': row[6]
            },
            'distance': 1.0 - float(row[1]) # recompute distance from similarity
        })
    return results

def get_rrf_score(rank, k=30, weight=1.0):
    if rank is None: return 0.0
    return weight * (1.0 / (k + rank))

def fuse_results(fts_results, vector_results):
    fused = {}
    for i, res in enumerate(fts_results):
        did = res['dataset']['dataset_id']
        fused[did] = {'dataset': res['dataset'], 'fts_rank': i + 1, 'vector_rank': None, 'cosine_distance': 0.5}
    for i, res in enumerate(vector_results):
        did = res['dataset']['dataset_id']
        if did not in fused:
            fused[did] = {'dataset': res['dataset'], 'fts_rank': None, 'vector_rank': i + 1, 'cosine_distance': res['distance']}
        else:
            fused[did]['vector_rank'] = i + 1
            fused[did]['cosine_distance'] = res['distance']
            
    candidates = []
    for did, data in fused.items():
        score = get_rrf_score(data['fts_rank'], k=30, weight=1.0) + get_rrf_score(data['vector_rank'], k=30, weight=1.25)
        candidates.append({
            'dataset_id': did,
            'rrf_score': score,
            'cosine_distance': data['cosine_distance'],
            'metadata': data['dataset']
        })
    candidates.sort(key=lambda x: x['rrf_score'], reverse=True)
    return candidates

def main():
    print("=== 03_run_benchmark.py : PostgreSQL E2E Benchmark ===")
    
    try:
        with open('data/corpus/gold_real.json', 'r', encoding='utf-8') as f:
            gold_queries = json.load(f)
    except Exception as e:
        print(f"Erreur chargement gold corpus: {e}")
        return
        
    print(f"Chargement de {MODEL_NAME}...")
    model = SentenceTransformer(MODEL_NAME)
    
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    
    iterations = 20
    print(f"Exécution du benchmark ({len(gold_queries)} requêtes x {iterations} itérations)...\n")
    
    times_embed = []
    times_fts = []
    times_vec = []
    times_rrf = []
    times_rerank = []
    times_total = []
    
    # Warmup
    print("Échauffement de la base...")
    execute_fts(cur, "chômage")
    execute_vector(cur, model.encode("chômage").tolist())
    
    # Benchmark
    for i in range(iterations):
        for q in gold_queries:
            t0 = time.perf_counter()
            
            # 1. Embed Query
            query_text = q['query']
            t_start = time.perf_counter()
            query_vec = model.encode(query_text).tolist()
            t_embed = time.perf_counter() - t_start
            
            # 2. FTS
            t_start = time.perf_counter()
            fts_res = execute_fts(cur, query_text)
            t_fts = time.perf_counter() - t_start
            
            # 3. Vector Search
            t_start = time.perf_counter()
            vec_res = execute_vector(cur, query_vec)
            t_vec = time.perf_counter() - t_start
            
            # 4. RRF
            t_start = time.perf_counter()
            candidates = fuse_results(fts_res, vec_res)
            t_rrf = time.perf_counter() - t_start
            
            # 5. Reranker
            t_start = time.perf_counter()
            d1_output = apply_deterministic_reranker(candidates, q['claim_context'], cosine_threshold=0.85)
            t_rerank = time.perf_counter() - t_start
            
            t_total = time.perf_counter() - t0
            
            # Store times (in ms)
            if i > 0: # Skip first iteration for pure "hot" metrics
                times_embed.append(t_embed * 1000)
                times_fts.append(t_fts * 1000)
                times_vec.append(t_vec * 1000)
                times_rrf.append(t_rrf * 1000)
                times_rerank.append(t_rerank * 1000)
                times_total.append(t_total * 1000)

    cur.close()
    conn.close()
    
    print("=== RÉSULTATS DU BENCHMARK (Latences Chaudes en ms) ===")
    components = [
        ("Embedding de requête", times_embed),
        ("FTS PostgreSQL", times_fts),
        ("Vectoriel exact pgvector", times_vec),
        ("Fusion RRF", times_rrf),
        ("Reranker Métier", times_rerank),
        ("Total Pipeline E2E", times_total)
    ]
    
    print(f"{'Composant':<25} | {'p50 (ms)':<8} | {'p95 (ms)':<8} | {'p99 (ms)':<8}")
    print("-" * 55)
    for name, data in components:
        p50 = compute_percentile(data, 50)
        p95 = compute_percentile(data, 95)
        p99 = compute_percentile(data, 99)
        print(f"{name:<25} | {p50:<8.2f} | {p95:<8.2f} | {p99:<8.2f}")
        
    print("\nConclusion : Pas besoin d'activer HNSW si le Vectoriel exact reste < 50ms.")

if __name__ == "__main__":
    main()
