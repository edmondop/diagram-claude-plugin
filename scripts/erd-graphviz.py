# /// script
# requires-python = ">=3.10"
# dependencies = ["graphviz"]
# ///
"""
Entity-Relationship Diagram using graphviz record-shaped nodes.

Requires graphviz system binary:
  macOS:         brew install graphviz
  Ubuntu/Debian: sudo apt-get install graphviz
  Fedora:        sudo dnf install graphviz

Run: uv run erd-graphviz.py
"""
from pathlib import Path

import graphviz


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    dot = graphviz.Digraph(
        name="erd",
        format="svg",
        engine="dot",
        graph_attr={
            "fontname": "Helvetica",
            "rankdir": "LR",
            "bgcolor": "white",
            "pad": "0.4",
            "nodesep": "1.0",
            "ranksep": "1.5",
            "label": "E-Commerce ERD",
            "labelloc": "t",
            "fontsize": "18",
        },
        node_attr={
            "fontname": "Helvetica",
            "fontsize": "10",
            "shape": "record",
            "style": "filled",
            "fillcolor": "#F5F5F5",
            "color": "#333333",
            "penwidth": "1.2",
        },
        edge_attr={
            "fontname": "Helvetica",
            "fontsize": "9",
            "color": "#555555",
            "penwidth": "1.0",
        },
    )

    dot.node("user", fillcolor="#DCEEFB", color="#2196F3", label=(
        "{User"
        "|<pk> PK  id : uuid"
        "|      email : varchar"
        "|      name : varchar"
        "|      created_at : timestamp}"
    ))
    dot.node("order", fillcolor="#E8F5E9", color="#4CAF50", label=(
        "{Order"
        "|<pk> PK  id : uuid"
        "|<fk_user> FK  user_id : uuid"
        "|      status : enum"
        "|      total_cents : integer"
        "|      placed_at : timestamp}"
    ))
    dot.node("order_item", fillcolor="#FFF3E0", color="#FF9800", label=(
        "{OrderItem"
        "|<pk> PK  id : uuid"
        "|<fk_order> FK  order_id : uuid"
        "|<fk_product> FK  product_id : uuid"
        "|      quantity : integer"
        "|      unit_price_cents : integer}"
    ))
    dot.node("product", fillcolor="#F3E5F5", color="#9C27B0", label=(
        "{Product"
        "|<pk> PK  id : uuid"
        "|<fk_category> FK  category_id : uuid"
        "|      name : varchar"
        "|      price_cents : integer}"
    ))
    dot.node("category", fillcolor="#FFEBEE", color="#F44336", label=(
        "{Category"
        "|<pk> PK  id : uuid"
        "|<fk_parent> FK  parent_id : uuid (nullable)"
        "|      name : varchar"
        "|      slug : varchar}"
    ))

    dot.edge("order:fk_user", "user:pk", label="belongs to",
             arrowhead="none", arrowtail="crow", dir="both")
    dot.edge("order_item:fk_order", "order:pk", label="line item of",
             arrowhead="none", arrowtail="crow", dir="both")
    dot.edge("order_item:fk_product", "product:pk", label="references",
             arrowhead="none", arrowtail="crow", dir="both")
    dot.edge("product:fk_category", "category:pk", label="categorised as",
             arrowhead="none", arrowtail="crow", dir="both")
    dot.edge("category:fk_parent", "category:pk", label="parent",
             style="dashed", arrowhead="normal", constraint="false")

    output_path = dot.render(filename="erd-graphviz",
                             directory="output", cleanup=True)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
