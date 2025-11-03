#!/usr/bin/env python3
"""
Exports full wiki docs from SQLite to JSONL for Elasticsearch indexing.
Handles both inline text and file paths (like /documents/wiki/...)
"""

import sqlite3, json, sys, os

if len(sys.argv) != 3:
    print("Usage: python3 scripts/sqlite_to_jsonl.py <input_db> <output.jsonl>")
    sys.exit(1)

input_db = sys.argv[1]
output_jsonl = sys.argv[2]

conn = sqlite3.connect(input_db)
cur = conn.cursor()

# Inspect columns dynamically
cur.execute("PRAGMA table_info(docs)")
cols = [c[1] for c in cur.fetchall()]
col_index = {name: i for i, name in enumerate(cols)}

print("📘 Found columns:", cols)

# Identify likely columns
doc_id_col = "doc_id" if "doc_id" in col_index else cols[0]
title_col = "title" if "title" in col_index else None
text_col = None
path_col = None

for c in cols:
    if "text" in c.lower() or "content" in c.lower():
        text_col = c
    if "path" in c.lower() or "file" in c.lower():
        path_col = c

cur.execute("SELECT * FROM docs")
rows = cur.fetchall()
count = 0

with open(output_jsonl, "w", encoding="utf-8") as f:
    for row in rows:
        doc_id = str(row[col_index[doc_id_col]])
        title = row[col_index[title_col]] if title_col else ""
        text = ""

        # 1️⃣ If DB has text column, use it
        if text_col:
            text = row[col_index[text_col]] or ""

        # 2️⃣ Otherwise, if there’s a file path, read from file
        elif path_col:
            path = row[col_index[path_col]]
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as tf:
                        text = tf.read()
                except Exception:
                    text = ""
            else:
                text = ""

        obj = {"id": doc_id, "title": title, "text": text}
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")
        count += 1

print(f"✅ Exported {count} documents to {output_jsonl}")
conn.close()
