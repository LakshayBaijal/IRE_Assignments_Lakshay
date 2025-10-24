#!/usr/bin/env python3
import sys, os, json
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.self_index import SelfIndex

if __name__ == "__main__":
    # Initialize
    index = SelfIndex()

    # Step 1: Load dataset
    dataset_path = "Dataset/Wiki_Dataset/data/processed/wiki_for_index.jsonl"
    docs = []
    with open(dataset_path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            obj = json.loads(line)
            doc_id = str(obj.get("id", f"doc_{i}"))
            text = f"{obj.get('title', '')} {obj.get('text', '')}"
            docs.append((doc_id, text))

    # Step 2: Create index
    index.create_index("wiki_index", docs)

    # Step 3: Load and query
    index.load_index("indices/wiki_index.json")
    index.query("ancient greek philosophy")

    # Step 4: List
    index.list_indices()
    index.list_indexed_files("wiki_index")
