# /// script
# requires-python = ">=3.10"
# dependencies = ["svgwrite"]
# ///
"""
Sequence diagram using svgwrite (manual layout, full visual control).

No system dependencies required.

Run: uv run sequence-svgwrite.py
"""

from pathlib import Path
from dataclasses import dataclass

import svgwrite

OUTPUT = "output/sequence-svgwrite.svg"
FONT = "Helvetica, Arial, sans-serif"

ACTORS = ["Browser", "API Gateway", "Auth Service", "Backend"]
ACTOR_SPACING = 200
HEADER_Y = 40
FIRST_MSG_Y = 100
MSG_SPACING = 50
PADDING_X = 30


@dataclass
class Message:
    from_idx: int
    to_idx: int
    label: str
    dashed: bool = False


MESSAGES = [
    Message(0, 1, "POST /login"),
    Message(1, 2, "Validate credentials"),
    Message(2, 1, "JWT token", dashed=True),
    Message(1, 0, "200 OK + Set-Cookie", dashed=True),
    Message(0, 1, "GET /data (Bearer)"),
    Message(1, 2, "Verify JWT"),
    Message(2, 1, "Token valid", dashed=True),
    Message(1, 3, "Fetch user data"),
    Message(3, 1, "JSON payload", dashed=True),
    Message(1, 0, "200 OK + JSON", dashed=True),
]


def actor_x(idx: int) -> float:
    return PADDING_X + idx * ACTOR_SPACING


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    width = PADDING_X * 2 + (len(ACTORS) - 1) * ACTOR_SPACING
    height = FIRST_MSG_Y + len(MESSAGES) * MSG_SPACING + 60

    dwg = svgwrite.Drawing(
        OUTPUT, size=(width, height), viewBox=f"0 0 {width} {height}"
    )
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill="white"))

    # Actor boxes and lifelines
    for i, name in enumerate(ACTORS):
        x = actor_x(i)
        box_w = 120
        dwg.add(
            dwg.rect(
                insert=(x - box_w / 2, HEADER_Y - 15),
                size=(box_w, 30),
                rx=4,
                ry=4,
                fill="#E3F2FD",
                stroke="#1976D2",
                stroke_width=1.5,
            )
        )
        dwg.add(
            dwg.text(
                name,
                insert=(x, HEADER_Y + 4),
                text_anchor="middle",
                font_size="11px",
                font_weight="bold",
                font_family=FONT,
                fill="#333",
            )
        )
        # Lifeline
        line_end = FIRST_MSG_Y + len(MESSAGES) * MSG_SPACING + 20
        dwg.add(
            dwg.line(
                start=(x, HEADER_Y + 15),
                end=(x, line_end),
                stroke="#BDBDBD",
                stroke_width=1,
                stroke_dasharray="4,4",
            )
        )

    # Arrowhead marker
    marker = dwg.marker(
        id="arrow", insert=(6, 3), size=(6, 6), orient="auto", markerUnits="strokeWidth"
    )
    marker.add(dwg.polygon([(0, 0), (6, 3), (0, 6)], fill="#444"))
    dwg.defs.add(marker)

    # Messages
    for i, msg in enumerate(MESSAGES):
        y = FIRST_MSG_Y + i * MSG_SPACING
        x1 = actor_x(msg.from_idx)
        x2 = actor_x(msg.to_idx)

        line = dwg.line(start=(x1, y), end=(x2, y), stroke="#444", stroke_width=1.5)
        line["marker-end"] = "url(#arrow)"
        if msg.dashed:
            line["stroke-dasharray"] = "6,3"
        dwg.add(line)

        label_x = (x1 + x2) / 2
        dwg.add(
            dwg.text(
                msg.label,
                insert=(label_x, y - 8),
                text_anchor="middle",
                font_size="10px",
                font_family=FONT,
                fill="#333",
            )
        )

    dwg.save()
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
