# scripts/preprocess_wiki.py
import json
import re
from pathlib import Path
from collections import Counter
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from tqdm import tqdm
import matplotlib.pyplot as plt
import nltk
nltk.download('stopwords', quiet=True)

# ==== Paths ====
inp = Path("../Dataset/Wiki_Dataset/data/processed/wiki_for_index.jsonl")
out = Path("../Dataset/Wiki_Dataset/data/processed/wiki_preprocessed.jsonl")
plots_dir = Path("./plots")
plots_dir.mkdir(parents=True, exist_ok=True)
plot_before = plots_dir / "wiki_before.png"
plot_after = plots_dir / "wiki_after.png"

# ==== Setup ====
WORD_RE = re.compile(r"[A-Za-z0-9]+")
stopset = set(stopwords.words('english'))
stemmer = PorterStemmer()

ctr_before = Counter()
ctr_after = Counter()

# ==== Process ====
with inp.open("r", encoding="utf-8", errors="ignore") as fin, \
     out.open("w", encoding="utf-8") as fout:
    for line in tqdm(fin, desc="Processing Wiki docs"):
        if not line.strip():
            continue
        j = json.loads(line)
        text = (j.get("title") or "") + " " + (j.get("text") or j.get("content") or "")
        doc_id = j.get("id") or j.get("doc_id") or j.get("uuid")
        tokens = [m.group(0).lower() for m in WORD_RE.finditer(text)]
        for t in tokens:
            ctr_before[t] += 1
        cleaned = [stemmer.stem(t) for t in tokens if t not in stopset]
        for t in cleaned:
            ctr_after[t] += 1
        fout.write(json.dumps({"id": doc_id, "text": " ".join(cleaned)}) + "\n")

# ==== Plot top words ====
def plot_top(counter, path, title):
    top = counter.most_common(30)
    if not top:
        return
    words, freqs = zip(*top)
    plt.figure(figsize=(10, 6))
    plt.barh(words[::-1], freqs[::-1])
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()

plot_top(ctr_before, plot_before, "Before Preprocessing (Wiki)")
plot_top(ctr_after, plot_after, "After Preprocessing (Wiki)")

print("\n✅ Done!")
print(f"Processed file saved to: {out}")
print(f"Plots saved to:\n → {plot_before}\n → {plot_after}")
