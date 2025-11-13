import sqlite3
import json
import networkx as nx
import matplotlib.pyplot as plt
import csv

def export_edges(db_path="crawl.db", csv_out="edges.csv"):
    """Extract all edges from crawl.db and save to a CSV."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("SELECT page_id, out_links FROM pages")
    rows = cursor.fetchall()
    conn.close()

    edges = []
    for src, out_links in rows:
        try:
            links = json.loads(out_links)
            for dst in links:
                edges.append((src, dst))
        except:
            pass

    # Save edges to CSV
    with open(csv_out, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["src", "dst"])
        writer.writerows(edges)

    print(f"✅ Exported {len(edges)} edges to {csv_out}")
    return edges


def plot_graph(edges, output_file="graph.png"):
    """Plot the web graph from edge list."""
    G = nx.DiGraph()
    G.add_edges_from(edges)

    plt.figure(figsize=(10, 8))
    pos = nx.spring_layout(G, seed=42, k=0.4)
    nx.draw(
        G,
        pos,
        node_size=500,
        node_color="skyblue",
        arrowsize=15,
        edge_color="gray",
        with_labels=True,
        font_size=8,
        font_weight="bold"
    )

    plt.title("Web Crawl Graph", fontsize=14)
    plt.tight_layout()
    plt.savefig(output_file, dpi=300)
    plt.close()
    print(f"📊 Graph saved as {output_file}")


def main():
    print("🔍 Extracting edges from crawl.db ...")
    edges = export_edges()
    if not edges:
        print("⚠️ No edges found! Run crawler.py first.")
        return
    print("📈 Plotting web structure ...")
    plot_graph(edges)
    print("✅ Done! Graph visualization ready.")


if __name__ == "__main__":
    main()
