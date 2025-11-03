#!/usr/bin/env python3
"""
es_plot_latency.py

Usage:
    python3 es_plot_latency.py <input_csv> <output_png>

Input CSV must have columns: query,latency_ms
"""
import sys
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def plot_csv(input_csv, output_png):
    df = pd.read_csv(input_csv)
    # maintain original order or sort by latency (choose as needed)
    queries = df["query"].tolist()
    lat = df["latency_ms"].tolist()

    avg = np.mean(lat)
    p95 = np.percentile(lat, 95)
    p99 = np.percentile(lat, 99)

    plt.figure(figsize=(10, 6))
    bars = plt.barh(queries, lat)
    plt.xlabel("Latency (ms)")
    plt.title(f"Latency: {input_csv}")
    for bar, v in zip(bars, lat):
        plt.text(v + 3, bar.get_y() + bar.get_height()*0.3, f"{v:.1f} ms", fontsize=9)
    plt.axvline(avg, color="blue", linestyle="--", label=f"avg={avg:.2f}ms")
    plt.axvline(p95, color="orange", linestyle="--", label=f"p95={p95:.2f}ms")
    plt.axvline(p99, color="red", linestyle="--", label=f"p99={p99:.2f}ms")
    plt.legend()
    plt.tight_layout()
    plt.savefig(output_png, dpi=300)
    plt.close()
    print(f"Saved plot to {output_png}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 es_plot_latency.py <input_csv> <output_png>")
        sys.exit(1)
    plot_csv(sys.argv[1], sys.argv[2])
