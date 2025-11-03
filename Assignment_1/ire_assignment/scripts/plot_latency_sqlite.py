import pandas as pd
import matplotlib.pyplot as plt
import sys
import numpy as np

def plot_latency(csv_file, output_image):
    # Read CSV data
    df = pd.read_csv(csv_file)
    df = df.sort_values(by="latency_ms", ascending=True)

    queries = df["query"].tolist()
    latencies = df["latency_ms"].tolist()

    # Compute average, p95, and p99
    avg_latency = np.mean(latencies)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)

    # Plot
    plt.figure(figsize=(10, 6))
    bars = plt.barh(queries, latencies)

    plt.title(f"Query Latency for {csv_file.split('/')[-1].replace('.csv','')}")
    plt.xlabel("Latency (ms)")
    plt.ylabel("Query")

    # Annotate each bar with latency value
    for bar, latency in zip(bars, latencies):
        plt.text(bar.get_width() + 3, bar.get_y() + bar.get_height()/3,
                 f"{latency:.1f} ms", fontsize=9)

    # Add average, p95, p99 reference lines
    plt.axvline(avg_latency, color='blue', linestyle='--', label=f"Average = {avg_latency:.2f} ms")
    plt.axvline(p95, color='orange', linestyle='--', label=f"P95 = {p95:.2f} ms")
    plt.axvline(p99, color='red', linestyle='--', label=f"P99 = {p99:.2f} ms")

    plt.legend()
    plt.tight_layout()
    plt.savefig(output_image, dpi=300)
    plt.close()
    print(f"✅ Plot saved as {output_image}")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python3 scripts/plot_latency_sqlite.py <input_csv> <output_image>")
        sys.exit(1)

    plot_latency(sys.argv[1], sys.argv[2])
