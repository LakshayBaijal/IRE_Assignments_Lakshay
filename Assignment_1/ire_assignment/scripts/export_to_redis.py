# scripts/export_to_redis.py
import sys, json
from pathlib import Path
import redis

def usage():
    print("Usage: python export_to_redis.py <index_dir> [host] [port]")
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        usage()
    idx_dir = Path(sys.argv[1])
    host = sys.argv[2] if len(sys.argv) > 2 else "localhost"
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 6379
    postings_path = idx_dir / "postings.json"
    if not postings_path.exists():
        print("postings.json not found:", postings_path); sys.exit(1)
    r = redis.Redis(host=host, port=port, decode_responses=True)
    with postings_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    pipe = r.pipeline()
    for term, plist in data.items():
        pipe.set(term, json.dumps(plist))
    pipe.execute()
    print(f"Pushed {len(data)} terms to Redis @ {host}:{port}")
