#!/usr/bin/env python3
"""
graph_visualize.py

Reads pagerank_graph.json (adjacency list produced from pagerank_crawl.py)
Builds a directed graph using NetworkX
Visualizes the graph with node size proportional to PageRank score
"""

import json
import argparse
import networkx as nx
import matplotlib.pyplot as plt

def load_graph(graph_file):
    with open(graph_file, "r") as f:
        return json.load(f)

def load_pagerank(pr_file):
    with open(pr_file, "r") as f:
        return json.load(f)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--graph", default="pagerank_graph.json")
    ap.add_argument("--pr", default="pagerank_scores.json")
    args = ap.parse_args()

    graph = load_graph(args.graph)
    pr_scores = load_pagerank(args.pr)

    G = nx.DiGraph()

    # Add edges
    for node, links in graph.items():
        for l in links:
            G.add_edge(node, l)

    # Convert PageRank dict to sizes
    sizes = [3000 * pr_scores.get(n, 0.01) for n in G.nodes()]  # scale up for visibility

    plt.figure(figsize=(16, 10))
    pos = nx.spring_layout(G, k=0.25, seed=42)  # nice layout

    nx.draw_networkx_nodes(G, pos, node_size=sizes, node_color="skyblue", alpha=0.9)
    nx.draw_networkx_edges(G, pos, arrowstyle="->", arrowsize=10, edge_color="gray")
    nx.draw_networkx_labels(G, pos, font_size=8)

    plt.title("PageRank Graph Visualization")
    plt.axis("off")
    plt.tight_layout()
    plt.show()

if __name__ == "__main__":
    main()
