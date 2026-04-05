# /// script
# requires-python = ">=3.10"
# dependencies = ["graphviz"]
# ///
"""
State machine / FSM diagram using graphviz.

Requires graphviz system binary:
  macOS:         brew install graphviz
  Ubuntu/Debian: sudo apt-get install graphviz
  Fedora:        sudo dnf install graphviz

Run: uv run fsm-graphviz.py
"""

from pathlib import Path

import graphviz


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    dot = graphviz.Digraph(
        name="order_fsm",
        format="svg",
        engine="dot",
        graph_attr={
            "rankdir": "LR",
            "fontname": "Helvetica",
            "bgcolor": "white",
            "pad": "0.5",
            "label": "Order Lifecycle FSM",
            "labelloc": "t",
            "fontsize": "18",
        },
        node_attr={
            "fontname": "Helvetica",
            "fontsize": "11",
            "style": "filled",
            "penwidth": "1.5",
        },
        edge_attr={
            "fontname": "Helvetica",
            "fontsize": "9",
            "color": "#444444",
            "arrowsize": "0.8",
            "penwidth": "1.2",
        },
    )

    dot.node("start", label="", shape="point", width="0.2", fillcolor="black")

    dot.attr("node", shape="doublecircle", fillcolor="#C8E6C9", color="#388E3C")
    dot.node("delivered", label="Delivered")
    dot.node("refunded", label="Refunded")

    dot.attr("node", shape="doublecircle", fillcolor="#FFCDD2", color="#D32F2F")
    dot.node("cancelled", label="Cancelled")

    dot.attr("node", shape="circle", fillcolor="#E3F2FD", color="#1976D2")
    dot.node("pending", label="Pending")
    dot.node("confirmed", label="Confirmed")
    dot.node("processing", label="Processing")
    dot.node("shipped", label="Shipped")

    dot.edge("start", "pending", label="create_order()")
    dot.edge("pending", "confirmed", label="payment_ok")
    dot.edge(
        "pending", "cancelled", label="timeout", color="#D32F2F", fontcolor="#D32F2F"
    )
    dot.edge("confirmed", "processing", label="warehouse_ack")
    dot.edge(
        "confirmed",
        "cancelled",
        label="fraud_detected",
        style="dashed",
        color="#D32F2F",
        fontcolor="#D32F2F",
    )
    dot.edge("processing", "shipped", label="tracking_assigned")
    dot.edge("shipped", "delivered", label="delivery_confirmed")
    dot.edge(
        "shipped", "processing", label="returned", style="dotted", constraint="false"
    )
    dot.edge(
        "delivered",
        "refunded",
        label="refund_requested",
        style="dashed",
        color="#FF9800",
        fontcolor="#FF9800",
    )

    output_path = dot.render(filename="fsm-graphviz", directory="output", cleanup=True)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
