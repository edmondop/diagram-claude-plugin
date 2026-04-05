# /// script
# requires-python = ">=3.10"
# dependencies = ["graphviz"]
# ///
"""
Generate known-bad SVG fixtures for test_svg_quality.py.

Each fixture demonstrates a specific anti-pattern that the quality
tests must catch. Run this once to populate test_fixtures/.

Run: uv run generate_fixtures.py
"""

from pathlib import Path

import graphviz

FIXTURES_DIR = Path(__file__).parent / "test_fixtures"
BLACK = "#222222"
NODE_FILL = "#E3F2FD"


def fixture_labels_overlap() -> None:
    """Two edge labels land on top of each other."""
    dot = graphviz.Digraph(
        format="svg",
        engine="dot",
        graph_attr={"rankdir": "TB", "nodesep": "0.3", "ranksep": "0.8"},
        node_attr={
            "shape": "box",
            "style": "filled,rounded",
            "fillcolor": NODE_FILL,
            "color": BLACK,
        },
        edge_attr={"color": BLACK},
    )

    with dot.subgraph(name="cluster_svc") as c:
        c.attr(label="Services", labeljust="l", color=BLACK, fontsize="12")
        c.node("A", label="Service A")
        c.node("B", label="Service B")

    with dot.subgraph(name="cluster_db") as c:
        c.attr(label="Databases", labeljust="l", color=BLACK, fontsize="12")
        c.node("db1", label="PostgreSQL", shape="cylinder")
        c.node("db2", label="MySQL", shape="cylinder")

    # Both edges go to nearby targets with labels — they'll overlap
    dot.edge("A", "db1", xlabel="  read  ")
    dot.edge("B", "db2", xlabel="  write  ")
    # Force them close together
    dot.edge("A", "db2", xlabel="  read  ", constraint="false")
    dot.edge("B", "db1", xlabel="  write  ", constraint="false")

    dot.render(filename="labels-overlap", directory=str(FIXTURES_DIR), cleanup=True)


def fixture_text_on_border() -> None:
    """Edge label sits right on a cluster border."""
    dot = graphviz.Digraph(
        format="svg",
        engine="dot",
        graph_attr={"rankdir": "TB", "nodesep": "0.5"},
        node_attr={
            "shape": "box",
            "style": "filled,rounded",
            "fillcolor": NODE_FILL,
            "color": BLACK,
        },
        edge_attr={"color": BLACK},
    )

    with dot.subgraph(name="cluster_inner") as c:
        c.attr(
            label="Inner Cluster",
            labeljust="l",
            color=BLACK,
            fontsize="12",
            margin="10",
        )  # tight margin
        c.node("X", label="Node X")
        c.node("Y", label="Node Y")

    dot.node("external", label="External")
    # Short edge with label — label will land near the cluster border
    dot.edge("external", "X", xlabel="  HTTP  ")
    dot.edge("X", "Y", xlabel="  gRPC  ")

    dot.render(filename="text-on-border", directory=str(FIXTURES_DIR), cleanup=True)


def fixture_rainbow_colors() -> None:
    """Multiple accent colors — visual noise anti-pattern.

    Also has centered labels (default) which overlap with arrows.
    """
    dot = graphviz.Digraph(
        format="svg",
        engine="dot",
        graph_attr={"rankdir": "TB"},
        node_attr={"shape": "box", "style": "filled,rounded"},
        edge_attr={"arrowsize": "0.7"},
    )

    # Each cluster uses a different color — anti-pattern
    with dot.subgraph(name="cluster_web") as c:
        c.attr(
            label="Web Tier",
            style="filled,rounded",
            color="#2196F3",
            fillcolor="#E3F2FD",
            fontcolor="#1565C0",
            penwidth="2",
        )
        # No labeljust — centered label (anti-pattern)
        c.node("web", label="React App", fillcolor="#BBDEFB")

    with dot.subgraph(name="cluster_api") as c:
        c.attr(
            label="API Tier",
            style="filled,rounded",
            color="#FF9800",
            fillcolor="#FFF3E0",
            fontcolor="#E65100",
            penwidth="2",
        )
        c.node("api", label="REST API", fillcolor="#FFE0B2")

    with dot.subgraph(name="cluster_db") as c:
        c.attr(
            label="Data Tier",
            style="filled,rounded",
            color="#4CAF50",
            fillcolor="#E8F5E9",
            fontcolor="#2E7D32",
            penwidth="2",
        )
        c.node("db", label="PostgreSQL", shape="cylinder", fillcolor="#C8E6C9")

    dot.edge("web", "api", label="HTTPS")
    dot.edge("api", "db", label="SQL")

    dot.render(filename="rainbow-colors", directory=str(FIXTURES_DIR), cleanup=True)


def fixture_data_layer_off_center() -> None:
    """Data layer positioned far to the right of backend."""
    dot = graphviz.Digraph(
        format="svg",
        engine="dot",
        graph_attr={"rankdir": "TB", "nodesep": "0.8"},
        node_attr={
            "shape": "box",
            "style": "filled,rounded",
            "fillcolor": NODE_FILL,
            "color": BLACK,
        },
        edge_attr={"color": BLACK},
    )

    with dot.subgraph(name="cluster_backend") as c:
        c.attr(label="Backend Services", labeljust="l", color=BLACK, fontsize="12")
        c.node("svc1", label="Service 1")
        c.node("svc2", label="Service 2")

    with dot.subgraph(name="cluster_data") as c:
        c.attr(label="Data Layer", labeljust="l", color=BLACK, fontsize="12")
        c.node("db", label="PostgreSQL", shape="cylinder")
        c.node("cache", label="Redis", shape="cylinder")
        c.node("queue", label="Kafka", shape="hexagon")
        # Extra nodes push the cluster far right
        c.node("search", label="Elasticsearch", shape="cylinder")
        c.node("s3", label="S3 Bucket", shape="cylinder")

    dot.edge("svc1", "db")
    # Pull data layer far right with a long cross-connection
    dot.edge("svc2", "s3", weight="10")
    dot.edge("svc1", "cache", constraint="false")

    dot.render(
        filename="data-layer-off-center", directory=str(FIXTURES_DIR), cleanup=True
    )


def main() -> None:
    FIXTURES_DIR.mkdir(exist_ok=True)
    fixture_labels_overlap()
    fixture_text_on_border()
    fixture_rainbow_colors()
    fixture_data_layer_off_center()
    print(f"Generated fixtures in {FIXTURES_DIR}/")
    for f in sorted(FIXTURES_DIR.glob("*.svg")):
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
