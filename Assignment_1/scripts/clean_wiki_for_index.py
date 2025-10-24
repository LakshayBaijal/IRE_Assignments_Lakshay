#!/usr/bin/env python3
"""
Clean wiki_sample.jsonl and emit wiki_for_index.jsonl with fields: id, title, text
Basic cleaning: remove repeated whitespace, strip, normalize newlines.
"""
import json, re
from pathlib import Path

RAW = Path("Dataset/Wiki_Dataset/data/raw/wiki_sample.jsonl")
OUT = Path("Dataset/Wiki_Dataset/data/processed/wiki_for_index.jsonl")
OUT.parent.mkdir(parents=True, exist_ok=True)

whitespace_re = re.compile(r'\s+')

count_in = 0
count_out = 0
with RAW.open("r", encoding="utf-8") as fin, OUT.open("w", encoding="utf-8") as fout:
    for i, line in enumerate(fin):
        line = line.strip()
        if not line:
            continue
        count_in += 1
        try:
            obj = json.loads(line)
        except Exception:
            continue
        idv = obj.get("id", i)
        title = obj.get("title","") or ""
        text = obj.get("text") or obj.get("body") or ""
        # normalize whitespace
        text = whitespace_re.sub(" ", text).strip()
        if not text:
            continue
        out = {"id": idv, "title": title, "text": text}
        fout.write(json.dumps(out, ensure_ascii=False) + "\n")
        count_out += 1

print(f"Wiki: scanned={count_in}, written={count_out}, out_file={OUT}")
