# /// script
# requires-python = ">=3.10"
# dependencies = ["seqdiag", "setuptools<70", "Pillow<10"]
# ///
"""
Sequence diagram using seqdiag.

No system dependencies required.

NOTE: seqdiag is unmaintained (last release 2021). It requires pinned
old versions of setuptools and Pillow. Consider svgwrite alternative
for new projects.

Run: uv run sequence-seqdiag.py
"""

from pathlib import Path
from textwrap import dedent

import seqdiag.builder
import seqdiag.drawer
import seqdiag.parser

DIAGRAM = dedent("""\
    seqdiag {
      edge_length = 260;
      span_height = 12;
      default_fontsize = 13;

      browser  [label = "Browser"];
      gateway  [label = "API Gateway"];
      auth     [label = "Auth Service"];
      backend  [label = "Backend API"];

      browser  ->  gateway [label = "POST /login"];
      gateway  ->  auth    [label = "Validate credentials"];
      auth    -->  gateway [label = "JWT token"];
      gateway -->  browser [label = "200 OK + Set-Cookie"];

      === Authentication complete ===

      browser  ->  gateway [label = "GET /data (Bearer)"];
      gateway  ->  auth    [label = "Verify JWT"];
      auth    -->  gateway [label = "Token valid"];
      gateway  ->  backend [label = "Fetch user data"];
      backend -->  gateway [label = "JSON payload"];
      gateway -->  browser [label = "200 OK + JSON"];
    }
""")


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    output_path = "output/sequence-seqdiag.svg"
    tree = seqdiag.parser.parse_string(DIAGRAM)
    diagram = seqdiag.builder.ScreenNodeBuilder.build(tree)
    draw = seqdiag.drawer.DiagramDraw("SVG", diagram, filename=output_path)
    draw.draw()
    draw.save()
    print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()
