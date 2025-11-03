# scripts/rebuild_index.py
import sys, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # add ire_assignment to path
from self_index import SelfIndex, INDICES_DIR

def usage():
    print("Usage: python rebuild_index.py <index_id> <path_to_jsonl>")
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) != 3:
        usage()
    index_id = sys.argv[1]
    src = Path(sys.argv[2])
    if not src.exists():
        print("Input JSONL not found:", src); sys.exit(1)
    idx_dir = INDICES_DIR / index_id
    if idx_dir.exists():
        print("Removing existing index:", idx_dir)
        shutil.rmtree(idx_dir)
    docs=[]
    with src.open("r", encoding="utf-8", errors="ignore") as f:
        for line in f:
            line=line.strip()
            if not line: continue
            try:
                j = __import__("json").loads(line)
            except Exception:
                continue
            doc_id = j.get("id") or j.get("doc_id") or j.get("uuid") or None
            text = (j.get("title") or "") + " " + (j.get("text") or j.get("content") or "")
            if doc_id is None:
                continue
            docs.append((str(doc_id), text))
    print(f"Creating index {index_id} from {len(docs)} docs.")
    si = SelfIndex()
    si.create_index(index_id, docs)
    print("Rebuild complete.")
