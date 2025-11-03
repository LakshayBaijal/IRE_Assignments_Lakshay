#!/usr/bin/env python3
"""
Compare query performance between SelfIndex and ElasticSearch.
"""
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import time
import json
from elasticsearch import Elasticsearch
from src.self_index import SelfIndex

queries = ["india", "finance", "technology", "war", "health"]

# Connect to ES
es = Elasticsearch("http://localhost:9200")

def query_es(index, q):
    start = time.time()
    body = {"query": {"multi_match": {"query": q, "fields": ["text"]}}}
    res = es.search(index=index, body=body, size=5)
    t = (time.time() - start) * 1000
    hits = len(res["hits"]["hits"])
    return t, hits

def query_self(index_path, q):
    s = SelfIndex()
    s.load(index_path)
    start = time.time()
    results = s.query(q)
    t = (time.time() - start) * 1000
    return t, len(results)

if __name__ == "__main__":
    metrics = []

    for q in queries:
        print(f"\n🔍 Query: {q}")

        t_es, h_es = query_es("wiki_es", q)
        print(f"  ES (wiki): {t_es:.2f} ms, {h_es} hits")

        t_self, h_self = query_self("indices/wiki_index.json", q)
        print(f"  SelfIndex (wiki): {t_self:.2f} ms, {h_self} hits")

        metrics.append({
            "query": q,
            "es_time_ms": t_es,
            "es_hits": h_es,
            "self_time_ms": t_self,
            "self_hits": h_self
        })

    with open("metrics.csv", "w", encoding="utf-8") as f:
        f.write("query,es_time_ms,es_hits,self_time_ms,self_hits\n")
        for m in metrics:
            f.write(f"{m['query']},{m['es_time_ms']},{m['es_hits']},{m['self_time_ms']},{m['self_hits']}\n")

    print("\n✅ Results saved to metrics.csv")


