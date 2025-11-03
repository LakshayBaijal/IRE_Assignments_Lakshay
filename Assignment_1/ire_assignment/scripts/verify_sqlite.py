# scripts/verify_sqlite.py
import sqlite3
import sys
from pathlib import Path

def verify_sqlite(db_path):
    db = sqlite3.connect(db_path)
    cur = db.cursor()

    print(f"🔍 Checking {db_path} ...")

    # Count rows in postings and docs
    cur.execute("SELECT COUNT(*) FROM postings")
    postings_count = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM docs")
    docs_count = cur.fetchone()[0]

    print(f"✅ Postings entries: {postings_count:,}")
    print(f"✅ Docs entries: {docs_count:,}")

    # Show sample terms
    print("\n🧠 Sample rows from postings:")
    for row in cur.execute("SELECT term, doc_id, SUBSTR(info, 1, 60) FROM postings LIMIT 5"):
        print(row)

    db.close()
    print("Done.\n")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python3 scripts/verify_sqlite.py <db_path>")
        sys.exit(1)
    verify_sqlite(sys.argv[1])
