#!/usr/bin/env python3
"""
Validate raw dataset JSONL files and print quick stats and samples.
Usage: python scripts/validate_datasets.py
"""
import json, os, sys, statistics
from pathlib import Path

FILES = [
    ("Wiki", "Dataset/Wiki_Dataset/data/raw/wiki_sample.jsonl"),
    ("News", "Dataset/webhose-news/data/raw/news_combined.jsonl"),
]

def analyze(path, sample_limit=200000):
    path = Path(path)
    if not path.exists():
        print(f"File not found: {path}")
        return None
    lengths = []
    count = 0
    short_examples = []
    long_examples = []
    try:
        with path.open("r", encoding="utf-8") as f:
            for i, line in enumerate(f):
                if not line.strip():
                    continue
                try:
                    obj = json.loads(line)
                except Exception:
                    continue
                text = obj.get("text") or obj.get("body") or obj.get("content") or obj.get("article") or obj.get("title") or ""
                L = len(text.strip())
                lengths.append(L)
                if L < 40 and len(short_examples) < 10:
                    short_examples.append((i, L, text.strip()[:200]))
                if L >= 200 and len(long_examples) < 10:
                    long_examples.append((i, L, text.strip()[:400]))
                count += 1
                if i >= sample_limit-1:
                    break
    except Exception as e:
        print("Error reading file:", e)
        return None

    stats = {}
    stats['count'] = count
    stats['avg_len'] = statistics.mean(lengths) if lengths else 0
    stats['median'] = statistics.median(lengths) if lengths else 0
    stats['min'] = min(lengths) if lengths else 0
    stats['max'] = max(lengths) if lengths else 0
    def pct(p):
        if not lengths: return 0
        arr = sorted(lengths)
        idx = min(int(p * len(arr)), len(arr)-1)
        return arr[idx]
    stats['p50'] = pct(0.50)
    stats['p75'] = pct(0.75)
    stats['p90'] = pct(0.90)
    stats['p95'] = pct(0.95)
    stats['p99'] = pct(0.99)
    stats['short_examples'] = short_examples
    stats['long_examples'] = long_examples
    return stats

def main():
    print("=== Dataset validation ===\n")
    for name, path in FILES:
        print(f"--- {name} : {path} ---")
        s = analyze(path)
        if s is None:
            print("  (missing or unreadable)\n")
            continue
        print(f"  Documents scanned: {s['count']}")
        print(f"  Avg len (chars): {s['avg_len']:.2f}")
        print(f"  Median: {s['median']}, Min: {s['min']}, Max: {s['max']}")
        print(f"  p50: {s['p50']}, p75: {s['p75']}, p90: {s['p90']}, p95: {s['p95']}, p99: {s['p99']}")
        print("  Sample SHORT examples (idx,len,head):")
        for ex in s['short_examples']:
            print("   ", ex)
        print("  Sample LONG examples (idx,len,head):")
        for ex in s['long_examples']:
            print("   ", ex)
        print()
    print("Validation complete. If files are missing, move your raw jsonl files to the paths above.")
    print("If the news file contains many short tags/URLs, we'll filter and rebuild the processed version in the next step.")

if __name__ == '__main__':
    main()
