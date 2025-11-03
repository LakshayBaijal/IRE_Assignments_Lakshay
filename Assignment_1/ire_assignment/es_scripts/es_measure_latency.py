#!/usr/bin/env python3
"""
es_measure_latency.py

Usage:
    python3 es_measure_latency.py <index_name> <queries_file> <output_csv>

queries_file: plain text file, one query per line
output_csv: will contain columns: query,latency_ms
"""
import sys
import time
import csv
from elasticsearch import Elasticsearch

def measure_latency(index_name, queries_file, output_file):
    es = Elasticsearch("http://localhost:9200")
    if not es.ping():
        print("ERROR: Elasticsearch not reachable at http://localhost:9200")
        return

    with open(queries_file, "r", encoding="utf-8") as f:
        queries = [q.strip() for q in f if q.strip()]

    results = []
    for q in queries:
        start = time.time()
        es.search(index=index_name, body={
            "query": {"multi_match": {"query": q, "fields": ["title", "text"]}}
        }, size=10)
        end = time.time()
        latency_ms = (end - start) * 1000.0
        print(f"Query: {q:30s} | Latency: {latency_ms:.3f} ms")
        results.append({"query": q, "latency_ms": latency_ms})

    # write csv
    with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["query", "latency_ms"])
        writer.writeheader()
        for r in results:
            writer.writerow(r)
    print(f"\nSaved results to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python3 es_measure_latency.py <index_name> <queries_file> <output_csv>")
        sys.exit(1)
    measure_latency(sys.argv[1], sys.argv[2], sys.argv[3])
