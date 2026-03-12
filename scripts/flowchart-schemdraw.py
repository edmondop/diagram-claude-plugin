# /// script
# requires-python = ">=3.10"
# dependencies = ["schemdraw"]
# ///
"""
Flowchart using schemdraw flow module (no Graphviz needed).

No system dependencies required.

Run: uv run flowchart-schemdraw.py
"""

from pathlib import Path

import schemdraw
from schemdraw import flow


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    flow.Box.defaults["fill"] = "#E3F2FD"
    flow.Start.defaults["fill"] = "#E8F5E9"
    flow.Decision.defaults["fill"] = "#FFF9C4"

    with schemdraw.Drawing(file="output/flowchart-schemdraw.svg") as d:
        d.config(fontsize=11, unit=0.75)

        flow.Start(h=1.5).label("Receive\nRequest").drop("S")
        flow.Arrow().down()
        flow.Box().label("Parse and\nValidate Input")
        flow.Arrow()

        valid = flow.Decision(W="No", S="Yes").label("Valid?").drop("W")
        flow.Arrow().left().length(2)
        flow.Box(fill="#FFCDD2").label("Return\n400 Error")

        flow.Arrow().at(valid.S).down()
        flow.Box().label("Query\nDatabase")
        flow.Arrow()

        found = flow.Decision(W="No", S="Yes").label("Found?").drop("W")
        flow.Arrow().left().length(2)
        flow.Box(fill="#FFCDD2").label("Return\n404 Error")

        flow.Arrow().at(found.S).down()
        flow.Box().label("Format\nResponse")
        flow.Arrow()
        flow.Start(h=1.5).label("Return\n200 OK")

    print("Saved: output/flowchart-schemdraw.svg")


if __name__ == "__main__":
    main()
