#!/usr/bin/env python3
"""
Simple search interface for Elasticsearch (Docker).
Usage:
    python3 es_scripts/es_search.py <index_name> "<query text>"
"""

import sys
from elasticsearch import Elasticsearch

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 es_scripts/es_search.py <index_name> \"<query text>\"")
        sys.exit(1)

    index_name = sys.argv[1]
    query_text = sys.argv[2]

    es = Elasticsearch(
        hosts=[{"host": "localhost", "port": 9200, "scheme": "http"}],
        verify_certs=False
    )

    if not es.ping():
        print("❌ Elasticsearch not reachable at http://localhost:9200")
        sys.exit(1)

    # ✅ Modern 8.x syntax — no deprecated body
    response = es.search(
        index=index_name,
        size=10,
        query={
            "multi_match": {
                "query": query_text,
                "fields": ["title^2", "text"],  # boosts title matches
                "fuzziness": "AUTO"
            }
        }
    )

    print(f"\n🔍 Query Results for: {query_text}")
    print("-" * 80)

    hits = response["hits"]["hits"]
    if not hits:
        print("No results found.")
    else:
        for i, hit in enumerate(hits, 1):
            title = hit["_source"].get("title", "(no title)")
            score = hit["_score"]
            snippet = hit["_source"].get("text", "")[:100].replace("\n", " ")
            print(f"{i}. {title[:80]}...  (Score: {score:.4f})")
            print(f"   → {snippet}...")
            print("-" * 80)

    print(f"Total hits: {response['hits']['total']['value']}")

if __name__ == "__main__":
    main()
