# /// script
# requires-python = ">=3.10"
# dependencies = ["graphviz"]
# ///
"""
Flowchart / pipeline diagram using graphviz.

Requires graphviz system binary:
  macOS:         brew install graphviz
  Ubuntu/Debian: sudo apt-get install graphviz
  Fedora:        sudo dnf install graphviz

Run: uv run flowchart-graphviz.py
"""
from pathlib import Path

import graphviz


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    dot = graphviz.Digraph(
        name="data_pipeline",
        format="svg",
        engine="dot",
        graph_attr={
            "rankdir": "LR",
            "fontname": "Helvetica",
            "fontsize": "14",
            "bgcolor": "white",
            "pad": "0.5",
            "nodesep": "0.8",
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
            "color": "#555555",
            "arrowsize": "0.8",
        },
    )

    dot.node("ingest", label="Ingest\nRaw Data", shape="parallelogram",
             fillcolor="#4A90D9", fontcolor="white")
    dot.node("validate", label="Validate\nSchema", shape="box",
             fillcolor="#7B68EE", fontcolor="white", style="filled,rounded")
    dot.node("transform", label="Transform\n& Enrich", shape="box",
             fillcolor="#50C878", fontcolor="white", style="filled,rounded")
    dot.node("dedupe", label="Deduplicate", shape="diamond",
             fillcolor="#FFB347", fontcolor="#333333", width="1.6", height="1.0")
    dot.node("load", label="Load to\nWarehouse", shape="cylinder",
             fillcolor="#DE6FA1", fontcolor="white")
    dot.node("notify", label="Send\nNotification", shape="note",
             fillcolor="#A0A0A0", fontcolor="white")

    dot.edge("ingest", "validate", label="raw JSON")
    dot.edge("validate", "transform", label="valid rows")
    dot.edge("validate", "notify", label="errors",
             style="dashed", color="#CC3333", fontcolor="#CC3333")
    dot.edge("transform", "dedupe", label="enriched")
    dot.edge("dedupe", "load", label="unique")
    dot.edge("dedupe", "transform", label="retry",
             style="dotted", constraint="false", color="#999999", fontcolor="#999999")
    dot.edge("load", "notify", label="done", style="bold")

    output_path = dot.render(filename="flowchart-graphviz",
                             directory="output", cleanup=True)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
