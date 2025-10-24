#!/usr/bin/env python3
"""
Plot performance comparison graph using metrics.csv
---------------------------------------------------
Reads metrics.csv (created by performance_compare_es_vs_self.py)
and visualizes Elasticsearch vs SelfIndex query times.
"""

import pandas as pd
import matplotlib.pyplot as plt
import os

def plot_performance():
    if not os.path.exists("metrics.csv"):
        print("❌ metrics.csv not found! Please run performance_compare_es_vs_self.py first.")
        return

    df = pd.read_csv("metrics.csv")
    print(f"✅ Loaded metrics.csv with {len(df)} entries.\n")

    print("📊 Performance Summary:")
    print(df.to_string(index=False))

    df.columns = [c.strip().lower() for c in df.columns]

    required = ["query", "es_time_ms", "self_time_ms"]
    for col in required:
        if col not in df.columns:
            print(f"❌ Missing column: {col}")
            return

    plt.figure(figsize=(8, 4))
    plt.plot(df["query"], df["es_time_ms"], marker="o", label="Elasticsearch", color="tab:blue")
    plt.plot(df["query"], df["self_time_ms"], marker="o", label="SelfIndex", color="tab:orange")

    plt.title("Performance Comparison: Elasticsearch vs SelfIndex", fontsize=12)
    plt.xlabel("Query", fontsize=11)
    plt.ylabel("Time (ms)", fontsize=11)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()

    output_path = "performance_comparison.png"
    plt.savefig(output_path)
    plt.show()
    print(f"\n📈 Graph saved as {output_path}")

if __name__ == "__main__":
    plot_performance()
