# /// script
# requires-python = ">=3.10"
# dependencies = ["graphviz"]
# ///
"""
Network topology diagram using graphviz neato engine (force-directed layout).

Requires graphviz system binary:
  macOS:         brew install graphviz
  Ubuntu/Debian: sudo apt-get install graphviz
  Fedora:        sudo dnf install graphviz

Run: uv run network-graphviz.py
"""
from pathlib import Path

import graphviz


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    dot = graphviz.Graph(
        name="network_topology",
        format="svg",
        engine="neato",
        graph_attr={
            "fontname": "Helvetica",
            "bgcolor": "white",
            "overlap": "false",
            "splines": "true",
            "pad": "0.5",
            "label": "Data Center Network Topology",
            "labelloc": "t",
            "fontsize": "18",
        },
        node_attr={
            "fontname": "Helvetica",
            "fontsize": "9",
            "style": "filled",
            "penwidth": "1.5",
        },
        edge_attr={
            "fontname": "Helvetica",
            "fontsize": "8",
            "color": "#888888",
        },
    )

    for name in ["core1", "core2"]:
        dot.node(name, label=name.replace("core", "Core "),
                 shape="hexagon", fillcolor="#EF5350",
                 fontcolor="white", width="1.4")
    dot.edge("core1", "core2", label="10 Gbps", penwidth="3", color="#D32F2F")

    for sw in ["dist_a", "dist_b", "dist_c"]:
        dot.node(sw, label=sw.replace("dist_", "Switch ").upper(),
                 shape="box", fillcolor="#42A5F5",
                 fontcolor="white", style="filled,rounded")
        dot.edge(sw, "core1", penwidth="2", color="#1976D2")
        dot.edge(sw, "core2", penwidth="2", color="#1976D2", style="dashed")

    servers = {
        "dist_a": ["web1", "web2", "web3"],
        "dist_b": ["app1", "app2"],
        "dist_c": ["db1", "db2", "cache1"],
    }
    colors = {"web": "#66BB6A", "app": "#FFA726", "db": "#AB47BC", "cache": "#26C6DA"}

    for switch, nodes in servers.items():
        for srv in nodes:
            prefix = srv.rstrip("0123456789")
            dot.node(srv, label=srv, shape="ellipse",
                     fillcolor=colors.get(prefix, "#BDBDBD"), fontcolor="white")
            dot.edge(switch, srv)

    dot.edge("db1", "db2", label="replication", style="dotted", color="#7B1FA2")

    output_path = dot.render(filename="network-graphviz",
                             directory="output", cleanup=True)
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
