# run_selfindex.py
import sys
import json
from pathlib import Path
from self_index import SelfIndex

USAGE = """Usage:
  python3 run_selfindex.py create <index_id> <path_to_jsonl>
  python3 run_selfindex.py query  <index_id> "<QUERY>"
  python3 run_selfindex.py list
  python3 run_selfindex.py listfiles <index_id>
  python3 run_selfindex.py delete <index_id>
"""

def read_jsonl(path):
    docs = []
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(path)
    with p.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                j = json.loads(line)
            except json.JSONDecodeError:
                continue
            doc_id = j.get("id") or j.get("doc_id") or j.get("uuid") or j.get("news_id") or None
            text = (j.get("title") or "") + " " + (j.get("text") or j.get("content") or "")
            if doc_id is None:
                continue
            docs.append((str(doc_id), text))
    return docs

def main(argv):
    if len(argv) < 2:
        print(USAGE); sys.exit(1)
    cmd = argv[1].lower()
    si = SelfIndex()

    if cmd == "create":
        if len(argv) != 4:
            print(USAGE); sys.exit(1)
        index_id = argv[2]
        path = argv[3]
        print(f"[ACTION] Creating index '{index_id}' from {path} ...")
        docs = read_jsonl(path)
        si.create_index(index_id, docs)
    elif cmd == "query":
        if len(argv) < 4:
            print(USAGE); sys.exit(1)
        index_id = argv[2]
        query = " ".join(argv[3:])
        si.load_index(index_id)
        out = si.query(query)
        print(out)
    elif cmd == "list":
        for idx in si.list_indices():
            print(idx)
    elif cmd == "listfiles":
        if len(argv) != 3:
            print(USAGE); sys.exit(1)
        for d in si.list_indexed_files(argv[2]):
            print(d)
    elif cmd == "delete":
        if len(argv) != 3:
            print(USAGE); sys.exit(1)
        si.delete_index(argv[2])
    else:
        print(USAGE); sys.exit(1)

if __name__ == "__main__":
    main(sys.argv)
