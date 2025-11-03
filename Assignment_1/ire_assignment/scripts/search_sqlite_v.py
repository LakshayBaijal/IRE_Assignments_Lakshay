import sqlite3
import json
import time
import argparse
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from common.version import parse_version

# -------------------------------
# Helper: Extract term frequency
# -------------------------------
def tf_from_blob(blob):
    try:
        data = json.loads(blob)
        return len(data.get("positions", []))
    except Exception:
        return 1

# -------------------------------
# Fetch postings list from DB
# -------------------------------
def fetch_postings(conn, term):
    cur = conn.cursor()
    cur.execute("PRAGMA table_info(postings)")
    cols = [c[1] for c in cur.fetchall()]

    if "info" in cols:
        col_name = "info"
    elif "json" in cols:
        col_name = "json"
    elif "value" in cols:
        col_name = "value"
    elif "json_blob" in cols:
        col_name = "json_blob"
    else:
        raise Exception(f"❌ Could not find JSON column in postings table. Found: {cols}")

    cur.execute(f"SELECT doc_id, {col_name} FROM postings WHERE term=?", (term,))
    return [(doc_id, tf_from_blob(info)) for doc_id, info in cur.fetchall()]

# -------------------------------
# Ranking logic: Boolean / TF / TF-IDF
# -------------------------------
def search(conn, query_terms, mode, total_docs):
    results = {}

    for term in query_terms:
        postings = fetch_postings(conn, term)
        df = len(postings)
        idf = 0
        if mode == 3 and df > 0:  # TF-IDF
            from math import log
            idf = log(total_docs / (1 + df))

        for doc_id, tf in postings:
            if mode == 1:  # Boolean
                results[doc_id] = 1.0
            elif mode == 2:  # TF
                results[doc_id] = results.get(doc_id, 0) + tf
            elif mode == 3:  # TF-IDF
                results[doc_id] = results.get(doc_id, 0) + tf * idf

    sorted_results = sorted(results.items(), key=lambda x: x[1], reverse=True)
    return sorted_results

# -------------------------------
# Main Execution
# -------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("db_path", help="Path to SQLite index database")
    parser.add_argument("--version", required=True, help="Version string like v1.32000")
    parser.add_argument("--query", required=True, help="Query text")
    parser.add_argument("--topk", type=int, default=10)
    args = parser.parse_args()

    x, y, z, i, q = parse_version(args.version)
    conn = sqlite3.connect(args.db_path)
    query_terms = args.query.lower().split()
    total_docs = 10000  # Adjust if needed

    print(f"\n🔎 Version={args.version} | x={x} | y={y} | z={z} | i={i} | q={q} | Query='{args.query}'")

    # -------------------------------
    # Placeholder info for z and i
    # -------------------------------
    if z == 1:
        print("🗜️ Compression: Simple delta encoding (placeholder)")
    elif z == 2:
        print("🧩 Compression: Using external compression library (placeholder)")

    if i == 1:
        print("⚙️ Index optimization: Skipping pointers enabled (placeholder)")

    # -------------------------------
    # Placeholder for query mode q
    # -------------------------------
    if q == 1:
        print("🔁 Query mode: Term-at-a-time (TAAT, placeholder)")
    elif q == 2:
        print("🧠 Query mode: Document-at-a-time (DAAT, placeholder)")
    else:
        print("⚙️ Query mode: Default sequential evaluation")

    start_time = time.time()
    results = search(conn, query_terms, x, total_docs)
    latency = (time.time() - start_time) * 1000

    print(f"\nDocs: {total_docs} | Returned: {len(results)} | Latency: {latency:.2f} ms\n")

    for i, (doc, score) in enumerate(results[:args.topk], start=1):
        print(f"{i}. doc_id={doc}  score={score:.4f}")

    conn.close()

if __name__ == "__main__":
    main()
