# /// script
# requires-python = ">=3.10"
# dependencies = ["graphviz"]
# ///
"""
Architecture diagram with cluster subgraphs using graphviz.

Demonstrates: labeljust="l" on all clusters, black + single accent color,
nodesep for breathing room, bumped font sizes for documentation
readability, weight/constraint for layout control.

Known issue: some backbone arrows cross cluster labels. Fixing this
requires widening clusters so labels sit clear of arrow paths. Run
test_svg_quality.py to validate.

Requires graphviz system binary:
  macOS:         brew install graphviz
  Ubuntu/Debian: sudo apt-get install graphviz
  Fedora:        sudo dnf install graphviz

Run: uv run architecture-graphviz.py
"""

from pathlib import Path

import graphviz

BLACK = "#222222"
NODE_FILL = "#E3F2FD"
CLUSTER_FILL = "#F5F5F5"


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
            "forcelabels": "true",
            "pad": "0.5",
            "nodesep": "0.8",
            "ranksep": "1.5",
            "bgcolor": "white",
        },
        node_attr={
            "fontname": "Helvetica",
            "fontsize": "11",
            "shape": "box",
            "style": "filled,rounded",
            "penwidth": "1.2",
            "color": BLACK,
            "fontcolor": BLACK,
            "fillcolor": NODE_FILL,
        },
        edge_attr={
            "fontname": "Helvetica",
            "fontsize": "10",
            "color": BLACK,
            "fontcolor": BLACK,
            "arrowsize": "0.7",
        },
    )

    # --- Clusters: labeljust="l" keeps labels top-left ---
    # Invisible spacer nodes widen clusters so labels sit clear of arrow paths.
    # Spacers are declared first so DOT places them leftmost.

    with dot.subgraph(name="cluster_frontend") as c:
        c.attr(
            label="Frontend Tier",
            labeljust="l",
            style="rounded",
            color=BLACK,
            fillcolor=CLUSTER_FILL,
            fontcolor=BLACK,
            fontsize="12",
            penwidth="1.2",
            margin="30",
        )
        c.node("web_app", label="React SPA")
        c.node("mobile_bff", label="Mobile BFF")

    with dot.subgraph(name="cluster_gateway") as c:
        c.attr(
            label="API Gateway",
            labeljust="l",
            style="rounded",
            color=BLACK,
            fillcolor=CLUSTER_FILL,
            fontcolor=BLACK,
            fontsize="12",
            penwidth="1.2",
            margin="30",
        )
        # Left spacer pushes cluster border left, keeping label clear of arrows
        c.node("gw_pad", label="", style="invis",
               fixedsize="true", width="1.2", height="0.01")
        c.node("gateway", label="Kong Gateway")
        c.node("auth", label="Auth Service")
        c.edge("gateway", "auth", style="dashed", constraint="false")

    with dot.subgraph(name="cluster_backend") as c:
        c.attr(
            label="Backend Services",
            labeljust="l",
            style="rounded",
            color=BLACK,
            fillcolor=CLUSTER_FILL,
            fontcolor=BLACK,
            fontsize="12",
            penwidth="1.2",
            margin="30",
        )
        # Left spacer for "Backend Services" — wider label needs more clearance
        c.node("be_pad", label="", style="invis",
               fixedsize="true", width="1.5", height="0.01")
        c.node("order_svc", label="Order Service")
        c.node("user_svc", label="User Service")
        c.node("payment_svc", label="Payment Service")

    with dot.subgraph(name="cluster_data") as c:
        c.attr(
            label="Data Layer",
            labeljust="l",
            style="rounded",
            color=BLACK,
            fillcolor=CLUSTER_FILL,
            fontcolor=BLACK,
            fontsize="12",
            penwidth="1.2",
            margin="30",
        )
        # Left spacer keeps "Data Layer" label clear of incoming arrows
        c.node("data_pad", label="", style="invis",
               fixedsize="true", width="1.2", height="0.01")
        c.node("kafka", label="Kafka", shape="hexagon",
               fillcolor=NODE_FILL)
        c.node("postgres", label="PostgreSQL", shape="cylinder",
               fillcolor=NODE_FILL)
        c.node("redis", label="Redis Cache", shape="cylinder",
               fillcolor=NODE_FILL)

    # --- Edges ---
    # Right-column backbone (high weight) keeps vertical alignment.
    # Cross-connections use constraint=false to avoid pulling sideways.

    # Frontend → Gateway
    dot.edge("web_app", "gateway", xlabel="  HTTPS  ")
    dot.edge("mobile_bff", "auth", xlabel="  HTTPS  ", weight="10")

    # Gateway → Backend
    dot.edge("gateway", "order_svc", xlabel="  gRPC  ")
    dot.edge("auth", "user_svc", xlabel="  gRPC  ", weight="10")

    # Internal to Backend
    dot.edge("order_svc", "payment_svc", xlabel="  gRPC  ")

    # Backend → Data
    dot.edge("order_svc", "kafka", xlabel="  events  ", weight="10",
             minlen="2")
    dot.edge("user_svc", "postgres", weight="10", minlen="2")

    # Cross-connections (don't affect layout)
    dot.edge("order_svc", "postgres", constraint="false")
    dot.edge("user_svc", "redis", style="dotted", constraint="false")

    # Layout: pull data layer under backend
    dot.edge("payment_svc", "kafka", style="invis", weight="10")

    output_path = dot.render(
        filename="architecture-graphviz", directory="output", cleanup=True
    )
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
