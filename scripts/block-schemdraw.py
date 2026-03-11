# /// script
# requires-python = ">=3.10"
# dependencies = ["schemdraw"]
# ///
"""
Block diagram using schemdraw flow elements.

No system dependencies required.

Run: uv run block-schemdraw.py
"""
from pathlib import Path

import schemdraw
from schemdraw import flow


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    with schemdraw.Drawing(file="output/block-schemdraw.svg") as d:
        d.config(fontsize=12, unit=1.5)

        client = d.add(
            flow.Box(w=4, h=1.5).label("Web Browser").fill("#E8F5E9")
        )
        d.add(flow.Arrow().at(client.S).down().length(1.5))

        gateway = d.add(
            flow.Box(w=4, h=1.5).label("API Gateway").fill("#E3F2FD")
        )

        d.add(flow.Arrow().at(gateway.W).left().length(2))
        d.add(
            flow.Box(w=3.5, h=1.5).label("Auth\nService")
            .fill("#FFF3E0").anchor("E")
        )

        d.add(flow.Arrow().at(gateway.E).right().length(2))
        d.add(
            flow.Box(w=3.5, h=1.5).label("Redis\nCache")
            .fill("#F3E5F5").anchor("W")
        )

        d.add(flow.Arrow().at(gateway.S).down().length(1.5))
        app = d.add(
            flow.Box(w=4, h=1.5).label("App Server").fill("#E3F2FD")
        )

        d.add(flow.Arrow().at(app.S).down().length(1.5))
        d.add(
            flow.Box(w=4, h=1.5).label("PostgreSQL").fill("#FCE4EC")
        )

    print("Saved: output/block-schemdraw.svg")


if __name__ == "__main__":
    main()
