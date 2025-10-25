import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
import json
import time
import random
import psutil
import os
import matplotlib.pyplot as plt
from src.query_engine import BooleanQueryProcessor



indices = {
    "Wiki": "indices/wiki_self_index_v1.json",
    "News": "indices/news_self_index_v1.json"
}

NUM_QUERIES = 100  
RESULTS = {}


for name, path in indices.items():
    print(f"\n📘 Testing index: {name}")
    processor = BooleanQueryProcessor(path)

    all_terms = list(processor.index.keys())
    sample_terms = random.sample(all_terms, min(len(all_terms), 400))

    queries = (
        [f"{t}" for t in random.sample(sample_terms, 40)] +
        [f"{a} AND {b}" for a, b in zip(random.sample(sample_terms, 30),
                                        random.sample(sample_terms, 30))] +
        [f"{a} OR {b}" for a, b in zip(random.sample(sample_terms, 30),
                                       random.sample(sample_terms, 30))]
    )[:NUM_QUERIES]

    latencies = []
    start_time = time.time()

    for q in queries:
        t1 = time.time()
        _ = processor.evaluate(q)
        t2 = time.time()
        latencies.append((t2 - t1) * 1000) 

    total_time = time.time() - start_time
    throughput = len(queries) / total_time
    mem_usage = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)

    lat_sorted = sorted(latencies)
    p95 = lat_sorted[int(0.95 * len(lat_sorted))]
    p99 = lat_sorted[int(0.99 * len(lat_sorted))]

    RESULTS[name] = {
        "avg": sum(latencies) / len(latencies),
        "p95": p95,
        "p99": p99,
        "throughput": throughput,
        "memory": mem_usage
    }

print("\n================ PERFORMANCE SUMMARY ================")
for name, r in RESULTS.items():
    print(f"\n{name} Index:")
    print(f"  Avg latency: {r['avg']:.3f} ms")
    print(f"  p95 latency: {r['p95']:.3f} ms")
    print(f"  p99 latency: {r['p99']:.3f} ms")
    print(f"  Throughput:  {r['throughput']:.2f} queries/sec")
    print(f"  Memory:      {r['memory']:.2f} MB")


labels = list(RESULTS.keys())

# Latency plots
plt.figure(figsize=(8, 5))
width = 0.25
x = range(len(labels))
plt.bar([i - width for i in x], [RESULTS[n]["avg"] for n in labels],
        width, label="Avg Latency")
plt.bar(x, [RESULTS[n]["p95"] for n in labels],
        width, label="p95 Latency")
plt.bar([i + width for i in x], [RESULTS[n]["p99"] for n in labels],
        width, label="p99 Latency")
plt.xticks(x, labels)
plt.ylabel("Latency (ms)")
plt.title("Latency Comparison (Avg, p95, p99)")
plt.legend()
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()

# Throughput plot
plt.figure(figsize=(6, 4))
plt.bar(labels, [RESULTS[n]["throughput"] for n in labels], color="limegreen")
plt.title("Throughput (Queries per Second)")
plt.ylabel("QPS")
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()

# Memory plot
plt.figure(figsize=(6, 4))
plt.bar(labels, [RESULTS[n]["memory"] for n in labels], color="orange")
plt.title("Memory Usage (MB)")
plt.ylabel("Memory (MB)")
plt.grid(True, linestyle="--", alpha=0.5)
plt.tight_layout()
plt.show()
