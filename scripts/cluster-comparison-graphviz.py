# /// script
# requires-python = ">=3.10"
# dependencies = ["graphviz"]
# ///
"""Side-by-side cluster comparison diagram.

Demonstrates graphviz patterns for comparing two approaches:
- Named clusters (cluster_ prefix required for border rendering)
- Cluster styling: label, fillcolor, fontname
- Labeled edges within clusters
- Top-to-bottom flow within each cluster
"""

from pathlib import Path

import graphviz


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    dot = graphviz.Digraph(format="svg")
    dot.attr(rankdir="TB")
    dot.attr(
        "graph",
        fontname="Helvetica",
        fontsize="11",
        nodesep="0.6",
        ranksep="0.6",
    )
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
        fontname="Helvetica",
        fontsize="10",
        color="#555555",
        arrowsize="0.8",
    )

    # Approach A: runtime execution
    with dot.subgraph(name="cluster_runtime") as c:
        c.attr(
            label="Approach A: runtime execution",
            style="filled",
            fillcolor="#FFFDE7",
            fontname="Helvetica",
            fontsize="11",
        )
        c.node("a_scheduler", "Scheduler", fillcolor="#F5F5F5")
        c.node("a_task", "Task per model", fillcolor="#F5F5F5")
        c.node("a_compile", "Compile\nat runtime", fillcolor="#FFF3CD")
        c.node("a_execute", "Execute", fillcolor="#E2E3E5")
        c.edge("a_scheduler", "a_task", label="  parse project  ")
        c.edge("a_task", "a_compile", label="  at runtime  ")
        c.edge("a_compile", "a_execute")

    # Approach B: compile-time rendering
    with dot.subgraph(name="cluster_compiletime") as s:
        s.attr(
            label="Approach B: compile-time rendering",
            style="filled",
            fillcolor="#E3F2FD",
            fontname="Helvetica",
            fontsize="11",
        )
        s.node("b_compile", "Compile\n(offline)", fillcolor="#F5F5F5")
        s.node("b_render", "Renderer\n(generate artifacts)", fillcolor="#CCE5FF")
        s.node("b_artifacts", "Static artifacts\n(SQL + config)", fillcolor="#D4EDDA")
        s.node("b_execute", "Execute\n(submit SQL)", fillcolor="#F5F5F5")
        s.edge("b_compile", "b_render")
        s.edge("b_render", "b_artifacts")
        s.edge("b_artifacts", "b_execute", label="  at runtime  ")

    dot.render(filename="cluster-comparison", directory="output", cleanup=True)
    print("Saved: output/cluster-comparison.svg")


if __name__ == "__main__":
    main()
