# scripts/measure_latency.py
import json
import time
import sys
from pathlib import Path

# --- FIX: add parent folder to Python path ---
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from self_index import SelfIndex

def measure_latency(index_name, queries_file, out_file):
    si = SelfIndex()                      # create instance (no args)
    si.load_index(index_name)             # load the correct index from disk
    results = []

    with open(queries_file, "r", encoding="utf-8") as f:
        for q in f:
            q = q.strip()
            if not q:
                continue
            t0 = time.perf_counter()
            _ = si.query(q)               # run the query
            t1 = time.perf_counter()
            results.append({
                "query": q,
                "latency_ms": round((t1 - t0) * 1000, 3)
            })

    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    print(f"✅ Latency results saved to {out_file}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python3 scripts/measure_latency.py <index_name> <queries_file> <output_file>")
        sys.exit(1)
    measure_latency(sys.argv[1], sys.argv[2], sys.argv[3])
