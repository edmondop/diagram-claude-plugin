# /// script
# requires-python = ">=3.10"
# dependencies = ["drawsvg~=2.0"]
# ///
"""
Pyramid / stacked layers diagram using drawsvg.

No system dependencies required.

Run: uv run pyramid-drawsvg.py
"""
from pathlib import Path

import drawsvg as draw

WIDTH = 500
HEIGHT = 400
PADDING = 20
OUTPUT = "output/pyramid-drawsvg.svg"

LAYERS: list[tuple[str, str, str]] = [
    ("E2E Tests",         "#e74c3c", "white"),
    ("Integration Tests", "#e67e22", "white"),
    ("Component Tests",   "#3498db", "white"),
    ("Unit Tests",        "#2ecc71", "white"),
]


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    d = draw.Drawing(WIDTH, HEIGHT)
    d.append(draw.Rectangle(0, 0, WIDTH, HEIGHT, fill="white"))

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

        p = draw.Path(fill=fill, stroke="white", stroke_width=2, fill_opacity=0.9)
        p.M(cx - w_top / 2, y_top)
        p.L(cx + w_top / 2, y_top)
        p.L(cx + w_bot / 2, y_bot)
        p.L(cx - w_bot / 2, y_bot)
        p.Z()
        d.append(p)

        d.append(draw.Text(
            label, 16, cx, y_top + layer_h / 2 + 6,
            fill=text_color, text_anchor="middle",
            font_weight="bold", font_family="Helvetica, Arial, sans-serif",
        ))

    d.append(draw.Text(
        "Testing Pyramid", 12, cx, HEIGHT - 5,
        fill="#666", text_anchor="middle",
        font_family="Helvetica, Arial, sans-serif",
    ))

    d.save_svg(OUTPUT)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
