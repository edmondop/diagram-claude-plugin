# /// script
# requires-python = ">=3.10"
# dependencies = ["svgwrite"]
# ///
"""Testing pyramid with computed geometry and dual axes.

Demonstrates svgwrite patterns:
- Data-driven layers from a list of dataclasses
- Computed trapezoid geometry (no hardcoded coordinates)
- Dual vertical axes with arrow markers
- Annotations positioned relative to layer edges
"""

from dataclasses import dataclass
from pathlib import Path

import svgwrite

WIDTH = 720
HEIGHT = 400
FONT = "Helvetica, Arial, sans-serif"

APEX_Y = 45
BASE_Y = 385
APEX_X = 360
LEFT_X = 70
RIGHT_X = 650

AXIS_LEFT_X = 25
AXIS_RIGHT_X = 695
AXIS_TOP_Y = 50
AXIS_BOTTOM_Y = 380


@dataclass
class Layer:
    label: str
    sublabel: str
    fill: str
    annotation: str


LAYERS = [
    Layer("E2E tests", "(production)", "#E8D5C4", "hours"),
    Layer("Integration", "(remote)", "#C9D6E3", "hours"),
    Layer("Integration", "(local)", "#D5DEDA", "minutes"),
    Layer("Unit tests", "", "#D4DACC", "seconds"),
    Layer("Static analysis", "", "#DEDAE0", "instant"),
]


def _edge_x(*, y: float, side: float) -> float:
    frac = (y - APEX_Y) / (BASE_Y - APEX_Y)
    return APEX_X + (side - APEX_X) * frac


def _draw_layers(dwg: svgwrite.Drawing) -> None:
    num = len(LAYERS)
    layer_h = (BASE_Y - APEX_Y) / num

    for i, layer in enumerate(LAYERS):
        y_top = APEX_Y + i * layer_h
        y_bot = y_top + layer_h

        if i == 0:
            points = [
                (APEX_X, y_top),
                (_edge_x(y=y_bot, side=RIGHT_X), y_bot),
                (_edge_x(y=y_bot, side=LEFT_X), y_bot),
            ]
        else:
            points = [
                (_edge_x(y=y_top, side=LEFT_X), y_top),
                (_edge_x(y=y_top, side=RIGHT_X), y_top),
                (_edge_x(y=y_bot, side=RIGHT_X), y_bot),
                (_edge_x(y=y_bot, side=LEFT_X), y_bot),
            ]

        dwg.add(dwg.polygon(points, fill=layer.fill, stroke="none"))


def _draw_outline_and_dividers(dwg: svgwrite.Drawing) -> None:
    num = len(LAYERS)
    layer_h = (BASE_Y - APEX_Y) / num

    dwg.add(
        dwg.polygon(
            [(APEX_X, APEX_Y), (LEFT_X, BASE_Y), (RIGHT_X, BASE_Y)],
            fill="none",
            stroke="black",
            stroke_width=2,
            stroke_linejoin="round",
        )
    )

    for i in range(1, num):
        y = APEX_Y + i * layer_h
        dwg.add(
            dwg.line(
                start=(_edge_x(y=y, side=LEFT_X), y),
                end=(_edge_x(y=y, side=RIGHT_X), y),
                stroke="black",
                stroke_width=1.5,
            )
        )


def _draw_labels(dwg: svgwrite.Drawing) -> None:
    num = len(LAYERS)
    layer_h = (BASE_Y - APEX_Y) / num

    for i, layer in enumerate(LAYERS):
        y_top = APEX_Y + i * layer_h
        y_bot = y_top + layer_h
        y_mid = (y_top * 0.35 + y_bot * 0.65) if i == 0 else (y_top + y_bot) / 2
        right_at_mid = _edge_x(y=y_mid, side=RIGHT_X)

        font_size = "11px" if i == 0 else "13px"

        if layer.sublabel:
            dwg.add(
                dwg.text(
                    layer.label,
                    insert=(APEX_X, y_mid - 3),
                    text_anchor="middle",
                    font_size=font_size,
                    font_family=FONT,
                    fill="black",
                )
            )
            dwg.add(
                dwg.text(
                    layer.sublabel,
                    insert=(APEX_X, y_mid + 12),
                    text_anchor="middle",
                    font_size=font_size,
                    font_family=FONT,
                    fill="black",
                )
            )
        else:
            dwg.add(
                dwg.text(
                    layer.label,
                    insert=(APEX_X, y_mid + 5),
                    text_anchor="middle",
                    font_size=font_size,
                    font_family=FONT,
                    fill="black",
                )
            )

        dwg.add(
            dwg.text(
                layer.annotation,
                insert=(right_at_mid + 10, y_mid + 4),
                text_anchor="start",
                font_size="11px",
                font_family=FONT,
                fill="#666",
            )
        )


def _draw_axis(
    dwg: svgwrite.Drawing,
    *,
    x: float,
    top_label: str,
    bottom_label: str,
) -> None:
    dwg.add(
        dwg.line(
            start=(x, AXIS_TOP_Y),
            end=(x, AXIS_BOTTOM_Y),
            stroke="black",
            stroke_width=1.5,
        )
    )
    dwg.add(
        dwg.polygon(
            [(x, AXIS_TOP_Y), (x - 6, AXIS_TOP_Y + 9.6), (x + 6, AXIS_TOP_Y + 9.6)],
            fill="black",
        )
    )
    dwg.add(
        dwg.polygon(
            [
                (x, AXIS_BOTTOM_Y),
                (x - 6, AXIS_BOTTOM_Y - 9.6),
                (x + 6, AXIS_BOTTOM_Y - 9.6),
            ],
            fill="black",
        )
    )
    dwg.add(
        dwg.text(
            top_label,
            insert=(x, AXIS_TOP_Y - 10),
            text_anchor="middle",
            font_size="11px",
            font_family=FONT,
            fill="black",
        )
    )
    dwg.add(
        dwg.text(
            bottom_label,
            insert=(x, AXIS_BOTTOM_Y + 18),
            text_anchor="middle",
            font_size="11px",
            font_family=FONT,
            fill="black",
        )
    )


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    dwg = svgwrite.Drawing(
        "output/testing-pyramid.svg",
        size=(WIDTH, HEIGHT),
        viewBox=f"0 0 {WIDTH} {HEIGHT}",
    )

    _draw_layers(dwg)
    _draw_outline_and_dividers(dwg)
    _draw_labels(dwg)
    _draw_axis(
        dwg, x=AXIS_LEFT_X, top_label="More integration", bottom_label="More isolation"
    )
    _draw_axis(dwg, x=AXIS_RIGHT_X, top_label="Slower", bottom_label="Faster")

    dwg.save()
    print("Saved: output/testing-pyramid.svg")


if __name__ == "__main__":
    main()
