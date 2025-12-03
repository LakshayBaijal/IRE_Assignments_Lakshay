#!/usr/bin/env python3
"""
pagerank_crawl.py

Standalone script to:
 1) Crawl the assignment server starting from a seed page
 2) Build a directed graph (page -> outgoing links)
 3) Run PageRank on that graph
 4) Save scores to CSV/JSON

Does NOT touch your run_crawler.py or the staleness assignment code.
"""

import argparse
import time
import requests
import re
import json
from collections import deque

# ----------------------------
# Simple HTML link parser
# ----------------------------

# links look like: href="/page_xxxxx"
LINK_RE = re.compile(r'href="/?(page_[A-Za-z0-9]+)"')

def extract_links(html: str):
    """Return unique list of page_* links from HTML."""
    links = LINK_RE.findall(html)
    # dedupe while preserving order
    seen = set()
    result = []
    for l in links:
        if l not in seen:
            seen.add(l)
            result.append(l)
    return result

# ----------------------------
# Simple BFS crawl just for graph
# ----------------------------

def crawl_graph(base_url: str, seed: str, window: float, rps: float, max_nodes: int = 200):
    """
    BFS crawl to build adjacency list.
    Stops when time window exceeded or max_nodes reached.
    """
    session = requests.Session()
    base_url = base_url.rstrip("/")

    graph = {}
    visited = set()
    q = deque([seed])

    start = time.time()
    delay = 1.0 / rps if rps > 0 else 0

    while q and time.time() - start < window and len(visited) < max_nodes:
        pid = q.popleft()
        if pid in visited:
            continue

        url = f"{base_url}/{pid}"
        try:
            resp = session.get(url, timeout=3)
            if resp.status_code != 200 or "Page not found" in resp.text:
                visited.add(pid)
                graph.setdefault(pid, [])
                continue
        except Exception:
            visited.add(pid)
            graph.setdefault(pid, [])
            continue

        links = extract_links(resp.text)
        graph[pid] = links
        visited.add(pid)

        # enqueue new nodes
        for l in links:
            if l not in visited:
                q.append(l)

        if delay > 0:
            time.sleep(delay)

    return graph

# ----------------------------
# PageRank implementation
# ----------------------------

def pagerank(graph, d=0.85, eps=1e-6, max_iter=100):
    nodes = list(graph.keys())
    if not nodes:
        return {}

    N = len(nodes)
    pr = {n: 1.0 / N for n in nodes}
    outdeg = {n: len(graph.get(n, [])) for n in nodes}

    for _ in range(max_iter):
        new_pr = {n: (1.0 - d) / N for n in nodes}
        # total sink PR (nodes with no outgoing edges)
        sink_mass = sum(pr[n] for n in nodes if outdeg[n] == 0)

        for n in nodes:
            if outdeg[n] > 0:
                share = pr[n] / outdeg[n]
                for v in graph[n]:
                    if v in new_pr:       # ignore links outside known graph
                        new_pr[v] += d * share

        # distribute sink mass
        sink_share = d * sink_mass / N
        for n in nodes:
            new_pr[n] += sink_share

        diff = sum(abs(new_pr[n] - pr[n]) for n in nodes)
        pr = new_pr
        if diff < eps:
            break

    return pr

# ----------------------------
# CLI main
# ----------------------------

def main():
    ap = argparse.ArgumentParser(description="Standalone PageRank on crawl graph")
    ap.add_argument("--base-url", default="http://localhost:3000")
    ap.add_argument("--seed", default="page_s1ns46p4")
    ap.add_argument("--window", type=float, default=60.0,
                    help="crawl time budget in seconds (for graph building)")
    ap.add_argument("--rps", type=float, default=2.0,
                    help="max requests per second during crawl")
    ap.add_argument("--max-nodes", type=int, default=200,
                    help="max number of nodes to discover during crawl")
    ap.add_argument("--top", type=int, default=10,
                    help="how many top pages to print")
    args = ap.parse_args()

    print(f"Crawling graph from seed={args.seed} with window={args.window}s, rps={args.rps}, max_nodes={args.max_nodes} ...")
    graph = crawl_graph(args.base_url, args.seed, args.window, args.rps, max_nodes=args.max_nodes)
    print(f"Discovered {len(graph)} nodes.")

    # Save graph
    with open("pagerank_graph.json", "w") as f:
        json.dump(graph, f, indent=2)
    print("Saved pagerank_graph.json")

    # Run PageRank
    pr = pagerank(graph)
    if not pr:
        print("Graph is empty, nothing to rank.")
        return

    # Normalize scores
    s = sum(pr.values()) or 1.0
    pr_norm = {k: v / s for k, v in pr.items()}

    # Sort & print
    sorted_pr = sorted(pr_norm.items(), key=lambda x: x[1], reverse=True)

    print("\n===== Top PageRank Pages =====")
    for pid, score in sorted_pr[:args.top]:
        print(f"{pid:20s}  {score:.6f}")

    # Save to CSV + JSON
    with open("pagerank_sorted.csv", "w") as f:
        for pid, score in sorted_pr:
            f.write(f"{pid},{score}\n")

    with open("pagerank_scores.json", "w") as f:
        json.dump(pr_norm, f, indent=2)

    print("\nSaved pagerank_sorted.csv and pagerank_scores.json")

if __name__ == "__main__":
    main()
