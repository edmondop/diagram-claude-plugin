# /// script
# requires-python = ">=3.10"
# dependencies = ["graphviz"]
# ///
"""Layered DAG with color-coded tiers.

Demonstrates graphviz patterns for data pipeline / ETL DAGs:
- Color-coded node tiers (sources, staging, intermediate, output)
- White text on dark fills for readability
- Multi-line labels with \\n for compact nodes
- Top-to-bottom flow (rankdir="TB")
"""
from pathlib import Path

import graphviz


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    dot = graphviz.Digraph(format="svg")
    dot.attr(rankdir="TB")
    dot.attr("graph", fontname="Helvetica", fontsize="11")
    dot.attr(
        "node",
        fontname="Helvetica",
        fontsize="11",
        penwidth="1.5",
        style="filled,rounded",
        shape="box",
    )
    dot.attr(
        "edge",
        color="#555555",
        arrowsize="0.8",
        fontname="Helvetica",
        fontsize="11",
    )

    # Sources (gray)
    dot.node("raw_events", "source:\nraw_events", fillcolor="#78909C", fontcolor="white")
    dot.node("raw_users", "source:\nraw_users", fillcolor="#78909C", fontcolor="white")

    # Staging (blue)
    dot.node("stg_events", "stg_events", fillcolor="#1E88E5", fontcolor="white")
    dot.node("stg_users", "stg_users", fillcolor="#1E88E5", fontcolor="white")

    # Intermediate (amber)
    dot.node("int_events_enriched", "int_events_\nenriched", fillcolor="#F9A825", fontcolor="white")
    dot.node("int_daily_metrics", "int_daily_\nmetrics", fillcolor="#F9A825", fontcolor="white")

    # Output (green)
    dot.node("fct_user_activity", "fct_user_\nactivity", fillcolor="#2E7D32", fontcolor="white")
    dot.node("fct_daily_summary", "fct_daily_\nsummary", fillcolor="#2E7D32", fontcolor="white")
    dot.node("fct_executive_report", "fct_executive_\nreport", fillcolor="#2E7D32", fontcolor="white")

    # Edges
    dot.edge("raw_events", "stg_events")
    dot.edge("raw_users", "stg_users")
    dot.edge("stg_events", "int_events_enriched")
    dot.edge("stg_users", "int_events_enriched")
    dot.edge("int_events_enriched", "int_daily_metrics")
    dot.edge("int_daily_metrics", "fct_user_activity")
    dot.edge("int_daily_metrics", "fct_daily_summary")
    dot.edge("fct_user_activity", "fct_executive_report")
    dot.edge("fct_daily_summary", "fct_executive_report")

    dot.render(filename="layered-dag", directory="output", cleanup=True)
    print("Saved: output/layered-dag.svg")


if __name__ == "__main__":
    main()
