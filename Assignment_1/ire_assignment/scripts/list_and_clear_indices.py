# scripts/list_and_clear_indices.py
import sys, shutil
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from self_index import INDICES_DIR

def usage():
    print("Usage: python list_and_clear_indices.py [--clear-all]")
    sys.exit(1)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--clear-all":
        for d in INDICES_DIR.iterdir():
            if d.is_dir():
                print("Removing", d)
                shutil.rmtree(d)
        (INDICES_DIR / "registry.json").write_text('{"indices":{}}')
        print("All indices removed.")
    else:
        print("Indices present:")
        for d in INDICES_DIR.iterdir():
            if d.is_dir():
                print(" -", d.name)
