import sqlite3
import numpy as np
import json
import csv

def compute_pagerank(edges, d=0.85, max_iter=100, tol=1e-6):
    """Compute PageRank using power iteration."""
    nodes = sorted(set([src for src, _ in edges] + [dst for _, dst in edges]))
    N = len(nodes)
    node_index = {n: i for i, n in enumerate(nodes)}

    # Build adjacency matrix
    M = np.zeros((N, N))
    for src, dst in edges:
        if src in node_index and dst in node_index:
            i, j = node_index[dst], node_index[src]
            M[i, j] = 1

    # Normalize columns
    for j in range(N):
        col_sum = np.sum(M[:, j])
        if col_sum > 0:
            M[:, j] /= col_sum
        else:
            M[:, j] = 1 / N  # dangling node fix

    # Initialize rank vector
    v = np.ones(N) / N

    for iteration in range(max_iter):
        v_new = d * M @ v + (1 - d) / N
        if np.linalg.norm(v_new - v, 1) < tol:
            print(f"Converged after {iteration} iterations.")
            break
        v = v_new

    pagerank = {node: float(score) for node, score in zip(nodes, v)}
    return pagerank


def extract_edges_from_db(db_path="crawl.db"):
    """Extract all edges (src, dst) from crawl.db."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    edges = []
    cursor.execute("SELECT page_id, out_links FROM pages")
    for page_id, out_links in cursor.fetchall():
        try:
            links = json.loads(out_links)
            for link in links:
                edges.append((page_id, link))
        except Exception:
            continue

    conn.close()
    return edges


def save_pagerank_to_csv(pagerank, filename="pagerank.csv"):
    """Save PageRank values to CSV."""
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["page_id", "pagerank"])
        for page, score in sorted(pagerank.items(), key=lambda x: x[1], reverse=True):
            writer.writerow([page, score])
    print(f"✅ PageRank saved to {filename}")


def main():
    print("🔍 Extracting edges from crawl.db ...")
    edges = extract_edges_from_db()
    print(f"Total edges found: {len(edges)}")

    if not edges:
        print("⚠️ No edges found. Make sure crawl.db is populated.")
        return

    print("⚙️ Computing PageRank ...")
    pagerank = compute_pagerank(edges)

    print("📄 Saving PageRank results ...")
    save_pagerank_to_csv(pagerank)

    print("✅ Done! Check pagerank.csv for results.")


if __name__ == "__main__":
    main()
