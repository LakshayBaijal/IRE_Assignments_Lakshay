# scripts/export_to_sqlite.py
import json
import sqlite3
from pathlib import Path
from tqdm import tqdm

def ensure_postings_table(cur):
    # Desired schema: postings(term TEXT, doc_id TEXT, info TEXT)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='postings'")
    if cur.fetchone() is None:
        cur.execute("""
            CREATE TABLE postings (
                term TEXT,
                doc_id TEXT,
                info TEXT
            )
        """)
        return

    # If table exists, check its column count — if != 3, drop & recreate
    cur.execute("PRAGMA table_info('postings')")
    cols = cur.fetchall()
    if len(cols) != 3:
        cur.execute("DROP TABLE IF EXISTS postings")
        cur.execute("""
            CREATE TABLE postings (
                term TEXT,
                doc_id TEXT,
                info TEXT
            )
        """)

def ensure_docs_table(cur):
    # Desired schema for docs: docs(doc_id TEXT PRIMARY KEY, length INT)
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='docs'")
    if cur.fetchone() is None:
        cur.execute("""
            CREATE TABLE docs (
                doc_id TEXT PRIMARY KEY,
                length INT
            )
        """)
        return

    cur.execute("PRAGMA table_info('docs')")
    cols = cur.fetchall()
    # If not matching (2 columns), drop & recreate
    if len(cols) != 2:
        cur.execute("DROP TABLE IF EXISTS docs")
        cur.execute("""
            CREATE TABLE docs (
                doc_id TEXT PRIMARY KEY,
                length INT
            )
        """)

def export_to_sqlite(index_dir, sqlite_path):
    index_dir = Path(index_dir)
    db = sqlite3.connect(sqlite_path)
    cur = db.cursor()

    # ensure tables exist and have expected schema
    ensure_postings_table(cur)
    ensure_docs_table(cur)
    db.commit()

    postings_file = index_dir / "postings.json"
    docs_file = index_dir / "docs.json"

    print(f"Loading postings from {postings_file}")
    with open(postings_file, "r", encoding="utf-8") as f:
        postings = json.load(f)

        for term, value in tqdm(postings.items(), desc="Exporting postings"):
            # Handle both formats: dict (detailed) or list/simple
            if isinstance(value, dict):
                # e.g. {term: {doc_id: {"positions": [...]} } }
                for doc_id, info in value.items():
                    cur.execute(
                        "INSERT INTO postings(term, doc_id, info) VALUES (?, ?, ?)",
                        (term, str(doc_id), json.dumps(info))
                    )
            elif isinstance(value, list):
                # e.g. {term: [{"doc_id": "...", "positions": [...]}, ...]}
                # Accept both list-of-strings OR list-of-dicts
                if len(value) > 0 and isinstance(value[0], dict):
                    for item in value:
                        doc_id = item.get("doc_id") or item.get("doc") or str(item)
                        info = item
                        cur.execute(
                            "INSERT INTO postings(term, doc_id, info) VALUES (?, ?, ?)",
                            (term, str(doc_id), json.dumps(info))
                        )
                else:
                    for doc_id in value:
                        cur.execute(
                            "INSERT INTO postings(term, doc_id, info) VALUES (?, ?, ?)",
                            (term, str(doc_id), "{}")
                        )
            else:
                # fallback: store the serialized value
                cur.execute(
                    "INSERT INTO postings(term, doc_id, info) VALUES (?, ?, ?)",
                    (term, "", json.dumps(value))
                )

    print(f"Loading docs from {docs_file}")
    with open(docs_file, "r", encoding="utf-8") as f:
        docs = json.load(f)
        # docs.json might be {"doc_lengths": {...}} or just mapping
        if "doc_lengths" in docs and isinstance(docs["doc_lengths"], dict):
            docs_map = docs["doc_lengths"]
        else:
            docs_map = docs if isinstance(docs, dict) else {}

        for doc_id, length in tqdm(docs_map.items(), desc="Exporting docs"):
            cur.execute("INSERT OR REPLACE INTO docs(doc_id, length) VALUES (?, ?)", (str(doc_id), int(length)))

    db.commit()
    db.close()
    print(f"✅ Exported index to SQLite at {sqlite_path}")

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python3 scripts/export_to_sqlite.py <index_dir> <sqlite_output>")
        sys.exit(1)
    export_to_sqlite(sys.argv[1], sys.argv[2])
