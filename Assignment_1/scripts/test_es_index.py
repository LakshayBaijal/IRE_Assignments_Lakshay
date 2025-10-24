#!/usr/bin/env python3
"""
Index Wiki and News datasets into ElasticSearch (Docker container).
"""

from elasticsearch import Elasticsearch
import json
import time

es = Elasticsearch("http://localhost:9200")

def index_dataset(index_name, path):
    print(f"📦 Creating index: {index_name}")
    es.indices.delete(index=index_name, ignore_unavailable=True)
    es.indices.create(index=index_name)

    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            obj = json.loads(line)
            doc_id = str(obj.get("id", i))
            text = f"{obj.get('title', '')} {obj.get('text', '')}".strip()
            if not text:
                continue
            es.index(index=index_name, id=doc_id, document={"text": text})
            if i % 1000 == 0 and i != 0:
                print(f"  Indexed {i} docs...")

    print(f"✅ Done indexing {index_name}")

if __name__ == "__main__":
    start = time.time()
    index_dataset("wiki_es", "Dataset/Wiki_Dataset/data/processed/wiki_for_index.jsonl")
    index_dataset("news_es", "Dataset/webhose-news/data/processed/news_for_index.jsonl")
    print(f"⏱️ Total time: {time.time() - start:.2f}s")
