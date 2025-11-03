import sqlite3
import json
import os

def export_postings(sqlite_db, output_jsonl):
    if not os.path.exists(sqlite_db):
        print(f"❌ Database not found: {sqlite_db}")
        return

    conn = sqlite3.connect(sqlite_db)
    cur = conn.cursor()

    # Detect correct column name
    cur.execute("PRAGMA table_info(postings)")
    cols = [c[1] for c in cur.fetchall()]
    col_name = None
    for c in ["info", "json", "value", "json_blob"]:
        if c in cols:
            col_name = c
            break

    if not col_name:
        print(f"❌ Could not detect JSON column in postings. Found columns: {cols}")
        return

    print(f"📘 Using column '{col_name}' from 'postings' table.")

    cur.execute(f"SELECT term, doc_id, {col_name} FROM postings")
    index_data = {}

    for term, doc_id, blob in cur.fetchall():
        try:
            data = json.loads(blob)
            tf = len(data.get("positions", []))
        except Exception:
            tf = 1  # fallback if parsing fails

        if term not in index_data:
            index_data[term] = {}
        index_data[term][doc_id] = tf

    print(f"✅ Collected {len(index_data)} unique terms. Writing to {output_jsonl} ...")

    with open(output_jsonl, "w", encoding="utf-8") as f:
        for term, postings in index_data.items():
            f.write(json.dumps({"term": term, "postings": postings}) + "\n")

    print(f"✅ Export complete → {output_jsonl}")

    conn.close()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("Usage: python3 scripts/sqlite_to_jsonl_v2.py <sqlite_db> <output_jsonl>")
        sys.exit(1)

    export_postings(sys.argv[1], sys.argv[2])
