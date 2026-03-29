# /// script
# requires-python = ">=3.10"
# dependencies = ["graphviz"]
# ///
"""FSM / state machine diagram using graphviz.

Demonstrates the pattern for embedding graphviz diagrams in notebooks
(marimo, Jupyter). Key techniques:
- HTML-like labels for bold text without bold borders
- fixedsize override for annotation nodes
- Left-aligned edge labels with \\l escape
- XML prologue stripping for notebook embedding
"""
from pathlib import Path

import graphviz


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    g = graphviz.Digraph(format="svg")
    g.attr(bgcolor="white", rankdir="TB", fontname="Helvetica", margin="0.3")
    g.attr(
        "node",
        fontname="Helvetica",
        fontsize="10",
        width="1.0",
        height="1.0",
        fixedsize="true",
        style="filled",
        penwidth="1.5",
    )
    g.attr("edge", fontname="Helvetica", fontsize="9", color="#333333", penwidth="1.2")

    # States — HTML-like labels for bold text, normal border weight
    g.node(
        "State0",
        shape="circle",
        fillcolor="#dbeafe",
        color="#2d5f8a",
        fontcolor="#333333",
        label="<<b>State0</b>>",
    )
    g.node(
        "State1",
        shape="circle",
        fillcolor="#dbeafe",
        color="#2d5f8a",
        fontcolor="#333333",
        label="<<b>State1</b>>",
    )
    g.node(
        "State2",
        shape="circle",
        fillcolor="#fecaca",
        color="#c0392b",
        fontcolor="#333333",
        label="<<b>State2</b>>",
    )
    g.node(
        "Done",
        shape="doublecircle",
        fillcolor="#dcfce7",
        color="#16a34a",
        fontcolor="#333333",
        label="<<b>Done</b>>",
        width="0.9",
        height="0.9",
    )

    # Transitions — left-aligned with \\l, padded with leading spaces
    g.edge(
        "State0",
        "State1",
        label="   poll(): allocate buf,\\l   start read,\\l   return Pending\\l",
        fontcolor="#333333",
    )
    g.edge(
        "State1",
        "State2",
        label="   poll(): read complete,\\l   transform(&buf),\\l"
        "   start write(&response),\\l   return Pending\\l",
        fontcolor="#333333",
    )
    g.edge(
        "State2",
        "Done",
        label="   poll(): write complete,\\l   return Ready\\l",
        fontcolor="#333333",
    )

    # Annotation node — override fixedsize to auto-size for long text
    g.node(
        "note",
        shape="note",
        style="filled",
        fillcolor="#fef2f2",
        color="#c0392b",
        fontcolor="#c0392b",
        fontsize="9",
        fixedsize="false",
        width="0",
        height="0",
        label="State2: write future borrows\n&response, which is a field\n"
        "of this same enum variant.\nSelf-referential struct.",
    )
    g.edge("note", "State2", style="dashed", color="#c0392b", arrowhead="vee", constraint="false")

    # Save as standalone SVG
    g.render("output/fsm-graphviz-notebook", cleanup=True)
    print("Saved: output/fsm-graphviz-notebook.svg")

    # For notebook embedding: strip XML prologue, use mo.Html(svg)
    svg_raw = g.pipe(format="svg").decode("utf-8")
    svg = svg_raw[svg_raw.index("<svg") :]
    print(f"SVG pipe length: {len(svg)} chars (ready for mo.Html())")


if __name__ == "__main__":
    main()
