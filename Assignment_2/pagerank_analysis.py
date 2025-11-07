import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# -----------------------------
# Step 1: Load Crawl Data
# -----------------------------
df = pd.read_csv("crawl_results.csv")

# -----------------------------
# Step 2: Build Directed Graph
# -----------------------------
G = nx.DiGraph()

for _, row in df.iterrows():
    src = row["PageID"]
    links = str(row["OutgoingLinks"]).split(", ")
    for link in links:
        if "page_" in link:
            dest = link.split("/")[-1]
            G.add_edge(src, dest)

# -----------------------------
# Step 3: Compute PageRank
# -----------------------------
pagerank = nx.pagerank(G, alpha=0.85)
pagerank_df = pd.DataFrame(pagerank.items(), columns=["PageID", "PageRank"])
pagerank_df = pagerank_df.sort_values(by="PageRank", ascending=False)
pagerank_df.to_csv("pagerank_results.csv", index=False)

print("✅ PageRank calculated successfully!")
print(pagerank_df.head(10))

# -----------------------------
# Step 4: Visualization
# -----------------------------
plt.figure(figsize=(12, 9))

# Layout for nodes (deterministic for reproducibility)
pos = nx.spring_layout(G, k=0.4, iterations=40, seed=42)

# Node sizes and colors based on PageRank
node_sizes = [v * 8000 for v in pagerank.values()]
node_colors = [v for v in pagerank.values()]

# Draw edges (curved to reduce overlap)
nx.draw_networkx_edges(
    G, pos,
    edge_color="gray",
    arrows=True,
    arrowsize=15,
    connectionstyle="arc3,rad=0.08",
    width=1.2,
    alpha=0.6
)

# Draw nodes (color intensity = PageRank)
nodes = nx.draw_networkx_nodes(
    G, pos,
    node_size=node_sizes,
    node_color=node_colors,
    cmap=plt.cm.Blues,
    alpha=0.9
)

# Add labels
nx.draw_networkx_labels(
    G, pos,
    font_size=8,
    font_weight="bold",
    verticalalignment="center",
    horizontalalignment="center"
)

# Add colorbar
# Add colorbar safely
sm = plt.cm.ScalarMappable(cmap=plt.cm.Blues, norm=plt.Normalize(vmin=min(node_colors), vmax=max(node_colors)))
sm.set_array([])

# Get current Axes for colorbar placement
ax = plt.gca()
cbar = plt.colorbar(sm, ax=ax, fraction=0.046, pad=0.04)
cbar.set_label("PageRank Value", rotation=270, labelpad=15)

# Title and legend
plt.title("Crawled Website Link Graph (Node Size & Color = PageRank Importance)", fontsize=13, fontweight='bold', pad=15)
plt.axis("off")
legend_patch = mpatches.Patch(color='lightblue', label='Each node represents a crawled page')
plt.legend(handles=[legend_patch], loc='lower right')

# Save as PNG and show
plt.tight_layout()
plt.savefig("pagerank_graph.png", dpi=300)
print("📊 Visualization saved as pagerank_graph.png")
plt.show()
