#!/usr/bin/env python3
"""
Test script for building and querying SelfIndex on the News dataset.
Parallels test_wiki_index.py but for Dataset/webhose-news/data/processed/news_for_index.jsonl.
"""

import sys, os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.self_index import SelfIndex

if __name__ == "__main__":
    index = SelfIndex()

    dataset_path = "Dataset/webhose-news/data/processed/news_for_index.jsonl"
    docs = []

    print(f"📖 Loading news dataset from {dataset_path}")
    with open(dataset_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except Exception:
                continue
            doc_id = str(obj.get("id", f"news_{i}"))
            text = f"{obj.get('title', '')} {obj.get('text', '')}".strip()
            if text:
                docs.append((doc_id, text))

    print(f"✅ Loaded {len(docs)} news documents for indexing.")

    index.create_index("news_index", docs)

    index.load_index("indices/news_index.json")

    index.query("climate change")
    index.query("economic growth")
    index.query("criminal justice")

    index.list_indices()
    index.list_indexed_files("news_index")
