#!/usr/bin/env python3
"""
Simple Elasticsearch indexer for Docker-based ES.
Indexes a JSONL file into an index (deletes if already exists).

Usage:
    python3 es_scripts/es_build_index.py <index_name> <jsonl_path>
"""

import sys
import json
from elasticsearch import Elasticsearch, helpers

def create_index(es, index_name):
    if es.indices.exists(index=index_name):
        print(f"Index '{index_name}' already exists. Deleting and recreating it...")
        es.indices.delete(index=index_name)

    mapping = {
        "mappings": {
            "properties": {
                "doc_id": {"type": "keyword"},
                "title": {"type": "text"},
                "text": {"type": "text"}
            }
        }
    }
    es.indices.create(index=index_name, body=mapping)
    print(f"✅ Created index: {index_name}")

def index_jsonl(es, index_name, jsonl_file):
    count = 0
    actions = []
    with open(jsonl_file, "r", encoding="utf-8") as f:
        for line in f:
            doc = json.loads(line)
            doc_id = doc.get("id") or doc.get("doc_id")
            source = {
                "doc_id": doc_id,
                "title": doc.get("title", ""),
                "text": doc.get("text", "")
            }
            actions.append({
                "_index": index_name,
                "_id": doc_id,
                "_source": source
            })

            if len(actions) >= 1000:
                helpers.bulk(es, actions)
                count += len(actions)
                print(f"Indexed {count} docs...")
                actions = []
    if actions:
        helpers.bulk(es, actions)
        count += len(actions)
    print(f"✅ Done. Total indexed: {count}")

def main():
    if len(sys.argv) != 3:
        print("Usage: python3 es_scripts/es_build_index.py <index_name> <jsonl_path>")
        sys.exit(1)

    index_name = sys.argv[1]
    jsonl_file = sys.argv[2]

    # ✅ Fix: Use hosts list and disable all SSL/HTTP auto features
    es = Elasticsearch(
        hosts=[{"host": "localhost", "port": 9200, "scheme": "http"}],
        verify_certs=False,
        ssl_show_warn=False,
        request_timeout=60
    )

    try:
        info = es.info()
        print("✅ Connected to Elasticsearch:", info.body["version"]["number"])
    except Exception as e:
        print("❌ ERROR: Elasticsearch not reachable at http://localhost:9200")
        print("➡️  Check if container is running with: sudo docker ps")
        print("➡️  Or see logs: sudo docker logs --tail 30 elasticsearch-container")
        print("Error details:", e)
        sys.exit(1)

    create_index(es, index_name)
    index_jsonl(es, index_name, jsonl_file)

if __name__ == "__main__":
    main()
