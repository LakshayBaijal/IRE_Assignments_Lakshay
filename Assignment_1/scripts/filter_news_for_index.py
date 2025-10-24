#!/usr/bin/env python3
"""
Rebuild cleaned news_for_index.jsonl (v2) with stricter filtering.
Keeps only news items that contain real text content (not URLs or short tags).
"""
import json, re, hashlib
from pathlib import Path

RAW = Path("Dataset/webhose-news/data/raw/news_combined.jsonl")
OUT = Path("Dataset/webhose-news/data/processed/news_for_index.jsonl")
OUT.parent.mkdir(parents=True, exist_ok=True)

url_re = re.compile(r'https?://|www\.', re.IGNORECASE)
alpha_word_re = re.compile(r'[a-zA-Z]{2,}')
non_ascii_re = re.compile(r'[^ -~]')

def good_text(txt):
    t = txt.strip()
    if len(t) < 50:
        return False
    if url_re.match(t):
        return False
    if url_re.search(t) and len(t.split()) < 10:
        return False
    words = alpha_word_re.findall(t)
    if len(words) < 8:
        return False
    if len(set(words)) < 5:
        return False
    return True

seen = set()
count_in = 0
count_out = 0
with RAW.open("r", encoding="utf-8") as fin, OUT.open("w", encoding="utf-8") as fout:
    for i, line in enumerate(fin):
        if not line.strip():
            continue
        count_in += 1
        try:
            obj = json.loads(line)
        except Exception:
            continue
        text = (obj.get("text") or obj.get("body") or obj.get("content") or obj.get("article") or obj.get("title") or "").strip()
        if not good_text(text):
            continue
        tnorm = " ".join(text.split())[:4000]
        h = hashlib.sha1(tnorm.encode("utf-8")).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        fout.write(json.dumps({"id": obj.get("id", i), "title": obj.get("title", ""), "text": text}, ensure_ascii=False) + "\n")
        count_out += 1

print(f"News v2: scanned={count_in}, kept={count_out}, out_file={OUT}")
