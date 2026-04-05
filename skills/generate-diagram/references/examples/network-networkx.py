# /// script
# requires-python = ">=3.10"
# dependencies = ["networkx", "matplotlib"]
# ///
"""
Network / DAG visualization using networkx + matplotlib.

No system dependencies required.

Run: uv run network-networkx.py
"""

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import networkx as nx


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    G = nx.DiGraph(
        [
            ("Data Source", "Ingest"),
            ("Config", "Ingest"),
            ("Ingest", "Validate"),
            ("Validate", "Transform"),
            ("Transform", "Enrich"),
            ("Transform", "Aggregate"),
            ("Enrich", "Load"),
            ("Aggregate", "Load"),
            ("Load", "Notify"),
        ]
    )

    for layer, nodes in enumerate(nx.topological_generations(G)):
        for node in nodes:
            G.nodes[node]["layer"] = layer

    pos = nx.multipartite_layout(G, subset_key="layer")

    layer_colors: dict[int, str] = {
        0: "#3498db",
        1: "#2ecc71",
        2: "#f39c12",
        3: "#e74c3c",
        4: "#9b59b6",
        5: "#1abc9c",
        6: "#34495e",
    }
    node_colors = [layer_colors.get(G.nodes[n]["layer"], "#95a5a6") for n in G.nodes()]

    fig, ax = plt.subplots(figsize=(12, 7))

    nx.draw_networkx_nodes(
        G,
        pos,
        ax=ax,
        node_color=node_colors,
        node_size=2800,
        edgecolors="white",
        linewidths=2,
    )
    nx.draw_networkx_labels(
        G, pos, ax=ax, font_size=9, font_weight="bold", font_color="white"
    )
    nx.draw_networkx_edges(
        G,
        pos,
        ax=ax,
        edge_color="#7f8c8d",
        width=2,
        arrowstyle="-|>",
        arrowsize=20,
        connectionstyle="arc3,rad=0.1",
        min_source_margin=25,
        min_target_margin=25,
    )

    ax.set_title("Data Pipeline DAG", fontsize=16, fontweight="bold", pad=20)
    ax.set_axis_off()
    fig.tight_layout()

    fig.savefig("output/network-networkx.svg", format="svg", bbox_inches="tight")
    print("Saved: output/network-networkx.svg")
    plt.close(fig)


if __name__ == "__main__":
    main()
