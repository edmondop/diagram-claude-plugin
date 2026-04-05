# /// script
# requires-python = ">=3.10"
# dependencies = ["svgwrite"]
# ///
"""
Pyramid / stacked layers diagram using svgwrite.

No system dependencies required.

Run: uv run pyramid-svgwrite.py
"""

from pathlib import Path

import svgwrite


WIDTH = 500
HEIGHT = 400
PADDING = 20
OUTPUT = "output/pyramid-svgwrite.svg"
FONT = "Helvetica, Arial, sans-serif"

LAYERS: list[tuple[str, str, str]] = [
    ("E2E Tests", "#e74c3c", "white"),
    ("Integration Tests", "#e67e22", "white"),
    ("Component Tests", "#3498db", "white"),
    ("Unit Tests", "#2ecc71", "white"),
]


def x_at_y(
    *,
    y: float,
    center_x: float,
    top_width: float,
    bottom_width: float,
    top_y: float,
    bottom_y: float,
) -> float:
    frac = (y - top_y) / (bottom_y - top_y)
    half_w = (top_width + (bottom_width - top_width) * frac) / 2
    return center_x - half_w


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    dwg = svgwrite.Drawing(
        OUTPUT, size=(WIDTH, HEIGHT), viewBox=f"0 0 {WIDTH} {HEIGHT}"
    )
    dwg.add(dwg.rect(insert=(0, 0), size=(WIDTH, HEIGHT), fill="white"))

    num = len(LAYERS)
    layer_h = (HEIGHT - 2 * PADDING) / num
    top_w = 140
    bottom_w = WIDTH - 2 * PADDING
    cx = WIDTH / 2

    for i, (label, fill, text_color) in enumerate(LAYERS):
        frac_top = i / num
        frac_bot = (i + 1) / num

        w_top = top_w + (bottom_w - top_w) * frac_top
        w_bot = top_w + (bottom_w - top_w) * frac_bot
        y_top = PADDING + i * layer_h
        y_bot = y_top + layer_h

        points = [
            (cx - w_top / 2, y_top),
            (cx + w_top / 2, y_top),
            (cx + w_bot / 2, y_bot),
            (cx - w_bot / 2, y_bot),
        ]
        dwg.add(
            dwg.polygon(
                points, fill=fill, stroke="white", stroke_width=2, fill_opacity=0.9
            )
        )
        dwg.add(
            dwg.text(
                label,
                insert=(cx, y_top + layer_h / 2 + 5),
                text_anchor="middle",
                font_size="16px",
                font_weight="bold",
                font_family=FONT,
                fill=text_color,
            )
        )

    dwg.add(
        dwg.text(
            "Testing Pyramid",
            insert=(cx, HEIGHT - 5),
            text_anchor="middle",
            font_size="12px",
            font_family=FONT,
            fill="#666",
        )
    )

    dwg.save()
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
