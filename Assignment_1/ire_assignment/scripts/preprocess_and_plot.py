# scripts/preprocess_and_plot.py
import json, sys
from pathlib import Path
from collections import Counter
import matplotlib.pyplot as plt
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
import re

nltk.download('stopwords', quiet=True)

WORD_RE = re.compile(r"[A-Za-z0-9]+")

def tokenize(text):
    return [m.group(0).lower() for m in WORD_RE.finditer(text or "")]

def preprocess_text(text, stopset, stemmer):
    toks = [t for t in tokenize(text) if t not in stopset]
    toks = [stemmer.stem(t) for t in toks]
    return " ".join(toks), toks

def wordfreq_plot(counter, outpath, topk=50, title="Word frequency"):
    most = counter.most_common(topk)
    words = [w for w,_ in most][::-1]
    freqs = [f for _,f in most][::-1]
    plt.figure(figsize=(10, max(4, topk/6)))
    plt.barh(words, freqs)
    plt.title(title)
    plt.tight_layout()
    plt.savefig(str(outpath))
    plt.close()

def process(input_jsonl: Path, output_jsonl: Path, plot_before: Path, plot_after: Path, sample_limit=None):
    stopset = set(stopwords.words('english'))
    stemmer = PorterStemmer()
    ctr_before = Counter()
    ctr_after = Counter()
    total = 0
    with input_jsonl.open('r', encoding='utf8', errors='ignore') as fin, \
         output_jsonl.open('w', encoding='utf8') as fout:
        for line in fin:
            if not line.strip(): continue
            j = json.loads(line)
            doc_id = j.get("id") or j.get("doc_id") or j.get("uuid")
            title = j.get("title","") or ""
            text = j.get("text","") or j.get("content","") or ""
            full = (title + " " + text).strip()
            toks = tokenize(full)
            for t in toks: ctr_before[t]+=1
            processed_text, toks_after = preprocess_text(full, stopset, stemmer)
            for t in toks_after: ctr_after[t]+=1
            out = {"id": doc_id, "text": processed_text}
            fout.write(json.dumps(out) + "\n")
            total += 1
            if sample_limit and total >= sample_limit:
                break
    wordfreq_plot(ctr_before, plot_before, title="Before preprocessing")
    wordfreq_plot(ctr_after, plot_after, title="After preprocessing")
    print(f"Processed {total} docs -> {output_jsonl}; plots saved: {plot_before}, {plot_after}")

if __name__ == "__main__":
    if len(sys.argv) < 5:
        print("Usage: python preprocess_and_plot.py <input.jsonl> <output.jsonl> <plot_before.png> <plot_after.png> [sample_limit]")
        sys.exit(1)
    inp = Path(sys.argv[1])
    out = Path(sys.argv[2])
    pb = Path(sys.argv[3])
    pa = Path(sys.argv[4])
    lim = int(sys.argv[5]) if len(sys.argv) > 5 else None
    process(inp, out, pb, pa, lim)
