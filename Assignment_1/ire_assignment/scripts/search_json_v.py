import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import json
import time
import argparse
from common.version import parse_version

def load_index(json_path):
    with open(json_path, "r", encoding="utf-8") as f:
        index = {}
        for line in f:
            data = json.loads(line.strip())
            term = data["term"]
            index[term] = data["postings"]
        return index

def boolean_search(index, query_terms):
    results = set()
    for term in query_terms:
        if term in index:
            docs = set(index[term].keys())
            results = results.union(docs)
    return list(results)

def tfidf_search(index, query_terms, N):
    from math import log
    scores = {}
    for term in query_terms:
        if term not in index:
            continue
        df = len(index[term])
        idf = log(N / (1 + df))
        for doc, tf in index[term].items():
            scores[doc] = scores.get(doc, 0) + tf * idf
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("json_file", help="Path to JSONL index file")
    parser.add_argument("--version", required=True)
    parser.add_argument("--query", required=True)
    parser.add_argument("--topk", type=int, default=10)
    args = parser.parse_args()

    x, y, z, i, q = parse_version(args.version)
    index = load_index(args.json_file)
    query_terms = args.query.lower().split()
    N = 10000

    start = time.time()
    if x == 1:
        results = boolean_search(index, query_terms)
        results = [(doc, 1.0) for doc in results]
    elif x == 3:
        results = tfidf_search(index, query_terms, N)
    else:
        print("Ranking mode not implemented for this version.")
        return
    latency = (time.time() - start) * 1000

    print(f"\n🔎 Version={args.version} | y=1 | Query={args.query}")
    print(f"Docs: {N} | Returned: {len(results)} | Latency: {latency:.2f} ms\n")
    for i, (doc, score) in enumerate(results[:args.topk], start=1):
        print(f"{i}. doc_id={doc}  score={score:.4f}")

if __name__ == "__main__":
    main()
