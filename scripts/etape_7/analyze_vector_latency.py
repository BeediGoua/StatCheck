import os
import sys
import time
import psycopg2
from pathlib import Path
import numpy as np

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://postgres:postgrespassword@localhost:5432/statcheck")
VECTOR_DIM = 384
RUNS = 100

def main():
    print(f"=== Analyse Latence Vectorielle Exacte ({RUNS} runs) ===")
    
    # Generate a random normalized vector
    vec = np.random.rand(VECTOR_DIM)
    vec = vec / np.linalg.norm(vec)
    vec_str = f"[{','.join(map(str, vec))}]"
    
    conn = psycopg2.connect(DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    latencies = []
    explain_analyze = ""
    
    # Warmup
    for _ in range(5):
        cur.execute("SELECT dataset_id, (1 - (embedding <=> %s::vector))::NUMERIC as similarity FROM search_documents ORDER BY embedding <=> %s::vector LIMIT 10;", (vec_str, vec_str))
        cur.fetchall()
        
    for i in range(RUNS):
        start = time.perf_counter()
        cur.execute("SELECT dataset_id, (1 - (embedding <=> %s::vector))::NUMERIC as similarity FROM search_documents ORDER BY embedding <=> %s::vector LIMIT 10;", (vec_str, vec_str))
        cur.fetchall()
        end = time.perf_counter()
        latencies.append((end - start) * 1000)
        
    # Get EXPLAIN ANALYZE BUFFERS for one run
    cur.execute("EXPLAIN (ANALYZE, BUFFERS) SELECT dataset_id, (1 - (embedding <=> %s::vector))::NUMERIC as similarity FROM search_documents ORDER BY embedding <=> %s::vector LIMIT 10;", (vec_str, vec_str))
    explain_analyze = "\n".join([r[0] for r in cur.fetchall()])
    
    cur.close()
    conn.close()
    
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)
    avg = np.mean(latencies)
    std = np.std(latencies)
    
    print("\n--- Statistiques de latence (Python -> DB -> Python) ---")
    print(f"P50 (Médiane) : {p50:.2f} ms")
    print(f"P95          : {p95:.2f} ms")
    print(f"P99          : {p99:.2f} ms")
    print(f"Moyenne      : {avg:.2f} ms")
    print(f"Écart-type   : {std:.2f} ms")
    
    print("\n--- Les 5 plus lentes ---")
    slowest = sorted(latencies, reverse=True)[:5]
    for s in slowest:
        print(f"- {s:.2f} ms")
        
    print("\n--- Plan EXPLAIN (ANALYZE, BUFFERS) ---")
    print(explain_analyze)
    
    # Write report
    report_path = Path("docs/phase 3/lot7_latency_analysis.md")
    report_path.parent.mkdir(exist_ok=True)
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("# Analyse des Pics de Latence Vectorielle\n\n")
        f.write("## 1. Objectif\n")
        f.write("Investiguer pourquoi le p95 du benchmark E2E grimpait à ~50 ms pour la recherche vectorielle sur seulement 222 datasets.\n\n")
        f.write("## 2. Mesures (100 exécutions)\n")
        f.write(f"- **P50 (Médiane)** : {p50:.2f} ms\n")
        f.write(f"- **P95** : {p95:.2f} ms\n")
        f.write(f"- **P99** : {p99:.2f} ms\n")
        f.write(f"- **Moyenne** : {avg:.2f} ms\n")
        f.write(f"- **Écart-type** : {std:.2f} ms\n\n")
        f.write("## 3. Plan d'exécution PostgreSQL pur\n")
        f.write("```sql\n" + explain_analyze + "\n```\n\n")
        f.write("## 4. Conclusion\n")
        f.write("Si le temps PostgreSQL (Execution Time) est de l'ordre de 1 à 2 ms, alors le pic à 50 ms mesuré précédemment provenait de l'overhead réseau, de l'acquisition de connexion `psycopg2`, ou de l'ordonnancement.\n")
        
if __name__ == "__main__":
    main()
