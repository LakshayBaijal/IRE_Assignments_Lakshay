#!/usr/bin/env python3
"""
Interactive search engine CLI. Looks for JSON index files in the `indices/` folder.

Usage:
  python -m scripts.search_engine
"""
import sys
from pathlib import Path
from src.self_index import SelfIndex

INDICES_FOLDER = Path("indices")

def find_indices():
    if not INDICES_FOLDER.exists():
        return []
    return sorted([p.name for p in INDICES_FOLDER.glob("*.json")])

def load_index_file(fname):
    p = INDICES_FOLDER / fname
    idx = SelfIndex()
    info = idx.load(str(p))
    return idx

def interactive():
    print("🧠 === Interactive Search Engine (Enhanced) ===")
    available = find_indices()
    if not available:
        print("No index files found in 'indices/'. Create indices first (see scripts).")
        return

    print("Available indices:")
    for n in available:
        print(" -", n.replace(".json", ""))
    print("--------------------------------------\n")

    current_idx = None
    current_name = None

    while True:
        if current_idx is None:
            choice = input("Enter index to use (name or 'list', 'q' to quit): ").strip()
            if choice.lower() in ("q", "quit"):
                print("Exiting.")
                return
            if choice.lower() == "list":
                print("Indices:", ", ".join(available))
                continue
            fname = None
            for n in available:
                if n.startswith(choice):
                    fname = n
                    break
            if fname is None:
                print(f"Index '{choice}' not found. Try one of:", ", ".join(available))
                continue
            try:
                print(f"📂 Loading index: {fname} ...")
                current_idx = load_index_file(fname)
                current_name = fname.replace(".json", "")
                print("✅ Loaded index:", current_name)
            except Exception as e:
                print("❌ Failed to load index:", e)
                current_idx = None
                continue

        q = input("\n🔍 Enter query (or 'back' to change index, 'quit' to exit): ").strip()
        if q.lower() in ("quit", "q", "exit"):
            print("Exiting search engine.")
            return
        if q.lower() in ("back", "b"):
            current_idx = None
            current_name = None
            continue
        if not q:
            continue
        try:
            results = current_idx.query(q)
            if not isinstance(results, list):
                print("⚠️ Unexpected result format from query().")
            else:
                print(f"✅ Returned {len(results)} results.\n")
        except Exception as e:
            print("❌ Error running query:", e)

if __name__ == "__main__":
    interactive()
