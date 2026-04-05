# /// script
# requires-python = ">=3.10"
# dependencies = ["blockdiag", "setuptools<70", "Pillow<10"]
# ///
"""
Block diagram using blockdiag DSL.

No system dependencies required.

NOTE: blockdiag is unmaintained (last release 2021). Requires pinned
old versions of setuptools and Pillow.

Run: uv run block-blockdiag.py
"""

from pathlib import Path
from textwrap import dedent

import blockdiag.builder
import blockdiag.drawer
import blockdiag.parser

DIAGRAM = dedent("""\
    blockdiag {
      node_width  = 180;
      node_height = 40;
      span_width  = 80;
      span_height = 60;
      default_fontsize = 13;

      client     [label = "Web Client",   color = "#E8F5E9", shape = "roundedbox"];
      lb         [label = "Load Balancer", color = "#E3F2FD", shape = "roundedbox"];
      web1       [label = "Web Server 1",  color = "#E3F2FD"];
      web2       [label = "Web Server 2",  color = "#E3F2FD"];
      app        [label = "App Server",    color = "#FFF3E0"];
      cache      [label = "Redis Cache",   color = "#F3E5F5"];
      db_primary [label = "DB Primary",    color = "#FCE4EC"];
      db_replica [label = "DB Replica",    color = "#FCE4EC", style = "dashed"];

      client -> lb;
      lb -> web1;
      lb -> web2;
      web1 -> app;
      web2 -> app;
      app -> cache;
      app -> db_primary;
      db_primary -> db_replica [label = "replication", style = "dashed"];

      group {
        label = "DMZ";
        color = "#ECEFF1";
        client; lb;
      }
      group {
        label = "Application Tier";
        color = "#FFF8E1";
        web1; web2; app; cache;
      }
      group {
        label = "Data Tier";
        color = "#FFEBEE";
        db_primary; db_replica;
      }
    }
""")


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    output_path = "output/block-blockdiag.svg"
    tree = blockdiag.parser.parse_string(DIAGRAM)
    diagram = blockdiag.builder.ScreenNodeBuilder.build(tree)
    draw = blockdiag.drawer.DiagramDraw("SVG", diagram, filename=output_path)
    draw.draw()
    draw.save()
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
