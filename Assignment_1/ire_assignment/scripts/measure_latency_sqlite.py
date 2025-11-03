import time
import csv
import sys
import sqlite3
import json
import math

def compute_tf_idf(tf, df, N):
    return (1 + math.log10(tf)) * math.log10(N / df)

def search_time(db_path, query):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM docs")
    N = cursor.fetchone()[0]

    query_terms = query.lower().split()
    scores = {}

    for term in query_terms:
        cursor.execute("SELECT * FROM postings WHERE term=?", (term,))
        rows = cursor.fetchall()
        df = len(rows)
        if df == 0:
            continue
        for row in rows:
            _, doc_id, posting_json = row
            posting = json.loads(posting_json)
            tf = len(posting["positions"])
            score = compute_tf_idf(tf, df, N)
            scores[doc_id] = scores.get(doc_id, 0) + score
    conn.close()
    return len(scores)

def measure_latency(db_path, queries_file, output_file):
    results = []
    with open(queries_file, "r") as f:
        queries = [q.strip() for q in f.readlines() if q.strip()]

    for query in queries:
        start = time.time()
        _ = search_time(db_path, query)
        end = time.time()
        latency_ms = (end - start) * 1000
        print(f"Query: {query:30s} | Latency: {latency_ms:.3f} ms")
        results.append({"query": query, "latency_ms": latency_ms})

    # Write results to CSV
    with open(output_file, "w", newline="") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["query", "latency_ms"])
        writer.writeheader()
        writer.writerows(results)

    print(f"\n✅ Latency results saved to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 scripts/measure_latency_sqlite.py <index_db> <queries_file> <output_file>")
        sys.exit(1)

    measure_latency(sys.argv[1], sys.argv[2], sys.argv[3])
