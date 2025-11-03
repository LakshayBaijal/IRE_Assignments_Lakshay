# scripts/plot_latency.py
import json
import matplotlib.pyplot as plt
import numpy as np
from pathlib import Path

# === File paths ===
wiki_path = Path("wiki_latency.json")
news_path = Path("news_latency.json")
plots_dir = Path("./plots")
plots_dir.mkdir(parents=True, exist_ok=True)
out_plot = plots_dir / "latency_comparison.png"

# === Load data ===
wiki = json.load(open(wiki_path))
news = json.load(open(news_path))

wiki_times = [d["latency_ms"] for d in wiki]
news_times = [d["latency_ms"] for d in news]
queries = range(1, len(wiki_times) + 1)

# === Plot ===
plt.figure(figsize=(10,6))
plt.plot(queries, wiki_times, label="Wiki Index", marker="o", linestyle="-")
plt.plot(queries, news_times, label="News Index", marker="x", linestyle="--")

plt.title("Query Latency Comparison (Wiki vs News)")
plt.xlabel("Query Number")
plt.ylabel("Latency (ms)")
plt.legend()
plt.grid(alpha=0.3)
plt.tight_layout()
plt.savefig(out_plot)
plt.close()

print(f"✅ Latency comparison plot saved to {out_plot}")
