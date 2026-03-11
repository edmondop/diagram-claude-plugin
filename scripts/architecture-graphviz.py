# /// script
# requires-python = ">=3.10"
# dependencies = ["graphviz"]
# ///
"""
Architecture diagram with cluster subgraphs using graphviz.

Requires graphviz system binary:
  macOS:         brew install graphviz
  Ubuntu/Debian: sudo apt-get install graphviz
  Fedora:        sudo dnf install graphviz

Run: uv run architecture-graphviz.py
"""
from pathlib import Path

import graphviz


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    dot = graphviz.Digraph(
        name="microservices_arch",
        format="svg",
        engine="dot",
        graph_attr={
            "fontname": "Helvetica",
            "fontsize": "14",
            "rankdir": "TB",
            "compound": "true",
            "pad": "0.5",
            "bgcolor": "#FAFAFA",
        },
        node_attr={
            "fontname": "Helvetica",
            "fontsize": "10",
            "shape": "box",
            "style": "filled,rounded",
            "penwidth": "1.2",
        },
        edge_attr={
            "fontname": "Helvetica",
            "fontsize": "9",
            "color": "#666666",
            "arrowsize": "0.7",
        },
    )

    with dot.subgraph(name="cluster_frontend") as c:
        c.attr(label="Frontend Tier", style="filled,rounded",
               color="#2196F3", fillcolor="#E3F2FD",
               fontcolor="#1565C0", fontsize="12", penwidth="2")
        c.node("web_app", label="React SPA", fillcolor="#BBDEFB")
        c.node("mobile_bff", label="Mobile BFF", fillcolor="#BBDEFB")

    with dot.subgraph(name="cluster_gateway") as c:
        c.attr(label="API Gateway", style="filled,rounded",
               color="#FF9800", fillcolor="#FFF3E0",
               fontcolor="#E65100", fontsize="12", penwidth="2")
        c.node("gateway", label="Kong Gateway", fillcolor="#FFE0B2")
        c.node("auth", label="Auth Service", fillcolor="#FFE0B2")

    with dot.subgraph(name="cluster_backend") as c:
        c.attr(label="Backend Services", style="filled,rounded",
               color="#4CAF50", fillcolor="#E8F5E9",
               fontcolor="#2E7D32", fontsize="12", penwidth="2")
        c.node("user_svc", label="User Service", fillcolor="#C8E6C9")
        c.node("order_svc", label="Order Service", fillcolor="#C8E6C9")
        c.node("payment_svc", label="Payment Service", fillcolor="#C8E6C9")

    with dot.subgraph(name="cluster_data") as c:
        c.attr(label="Data Layer", style="filled,rounded",
               color="#9C27B0", fillcolor="#F3E5F5",
               fontcolor="#6A1B9A", fontsize="12", penwidth="2")
        c.node("postgres", label="PostgreSQL", shape="cylinder", fillcolor="#CE93D8")
        c.node("redis", label="Redis Cache", shape="cylinder", fillcolor="#CE93D8")
        c.node("kafka", label="Kafka", shape="hexagon", fillcolor="#CE93D8")

    dot.edge("web_app", "gateway", label="HTTPS")
    dot.edge("mobile_bff", "gateway", label="HTTPS")
    dot.edge("gateway", "auth", style="dashed")
    dot.edge("gateway", "user_svc", label="gRPC")
    dot.edge("gateway", "order_svc", label="gRPC")
    dot.edge("order_svc", "payment_svc", label="gRPC")
    dot.edge("user_svc", "postgres")
    dot.edge("order_svc", "postgres")
    dot.edge("user_svc", "redis", style="dotted", label="cache")
    dot.edge("order_svc", "kafka", label="events")

    output_path = dot.render(filename="architecture-graphviz",
                             directory="output", cleanup=True)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
