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


def _table(
    name: str,
    *,
    header_bg: str,
    header_fg: str = "white",
    fields: list[tuple[str, str, str]],
) -> str:
    """Build an HTML-like label for an ERD entity.

    Each field is (key_badge, name, type) where key_badge is "PK", "FK", or "".
    """
    rows = []
    for badge, fname, ftype in fields:
        badge_cell = (
            f'<TD ALIGN="LEFT"><FONT COLOR="#888888"><B>{badge}</B></FONT></TD>'
            if badge
            else "<TD></TD>"
        )
        rows.append(
            f"<TR>"
            f"{badge_cell}"
            f'<TD ALIGN="LEFT">{fname}</TD>'
            f'<TD ALIGN="LEFT"><FONT COLOR="#888888">{ftype}</FONT></TD>'
            f"</TR>"
        )
    field_rows = "\n".join(rows)
    return (
        f"<<TABLE BORDER='0' CELLBORDER='0' CELLSPACING='0' CELLPADDING='4'>"
        f"<TR><TD COLSPAN='3' BGCOLOR='{header_bg}'>"
        f"<FONT COLOR='{header_fg}'><B>{name}</B></FONT></TD></TR>"
        f"<HR/>{field_rows}</TABLE>>"
    )


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
            "nodesep": "0.8",
            "ranksep": "1.5",
            "label": "E-Commerce ERD",
            "labelloc": "t",
            "fontsize": "18",
        },
        node_attr={
            "fontname": "Helvetica",
            "fontsize": "10",
            "shape": "plain",
        },
        edge_attr={
            "fontname": "Helvetica",
            "fontsize": "9",
            "color": "#555555",
            "penwidth": "1.0",
        },
    )

    dot.node(
        "user",
        label=_table(
            "User",
            header_bg="#2196F3",
            fields=[
                ("PK", "id", "uuid"),
                ("", "email", "varchar"),
                ("", "name", "varchar"),
                ("", "created_at", "timestamp"),
            ],
        ),
    )
    dot.node(
        "order",
        label=_table(
            "Order",
            header_bg="#4CAF50",
            fields=[
                ("PK", "id", "uuid"),
                ("FK", "user_id", "uuid"),
                ("", "status", "enum"),
                ("", "total_cents", "integer"),
                ("", "placed_at", "timestamp"),
            ],
        ),
    )
    dot.node(
        "order_item",
        label=_table(
            "OrderItem",
            header_bg="#FF9800",
            fields=[
                ("PK", "id", "uuid"),
                ("FK", "order_id", "uuid"),
                ("FK", "product_id", "uuid"),
                ("", "quantity", "integer"),
                ("", "unit_price_cents", "integer"),
            ],
        ),
    )
    dot.node(
        "product",
        label=_table(
            "Product",
            header_bg="#9C27B0",
            fields=[
                ("PK", "id", "uuid"),
                ("FK", "category_id", "uuid"),
                ("", "name", "varchar"),
                ("", "price_cents", "integer"),
            ],
        ),
    )
    dot.node(
        "category",
        label=_table(
            "Category",
            header_bg="#F44336",
            fields=[
                ("PK", "id", "uuid"),
                ("FK", "parent_id", "uuid (nullable)"),
                ("", "name", "varchar"),
                ("", "slug", "varchar"),
            ],
        ),
    )

    dot.edge(
        "order",
        "user",
        label="belongs to",
        arrowhead="none",
        arrowtail="crow",
        dir="both",
    )
    dot.edge(
        "order_item",
        "order",
        label="line item of",
        arrowhead="none",
        arrowtail="crow",
        dir="both",
    )
    dot.edge(
        "order_item",
        "product",
        label="references",
        arrowhead="none",
        arrowtail="crow",
        dir="both",
    )
    dot.edge(
        "product",
        "category",
        label="categorised as",
        arrowhead="none",
        arrowtail="crow",
        dir="both",
    )
    dot.edge(
        "category",
        "category",
        label="parent",
        style="dashed",
        arrowhead="normal",
        constraint="false",
    )

    output_path = dot.render(filename="erd-graphviz", directory="output", cleanup=True)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
