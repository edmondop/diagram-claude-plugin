# /// script
# requires-python = ">=3.10"
# dependencies = ["svgwrite"]
# ///
"""
Sequence diagram using svgwrite (manual layout, full visual control).

Demonstrates: labels near source (not centered), bold monospace labels,
extra right margin for return labels, sticky-note callout outside flow.

No system dependencies required.

Run: uv run sequence-svgwrite.py
"""

from dataclasses import dataclass
from pathlib import Path

import svgwrite

OUTPUT = "output/sequence-svgwrite.svg"
FONT = "Helvetica, Arial, sans-serif"
MONO = "Courier New, Courier, monospace"
BLACK = "#222222"
GRAY = "#555555"
ACCENT = "#1565C0"

ACTORS = ["Browser", "API Gateway", "Auth Service", "Backend"]
ACTOR_SPACING = 180
HEADER_Y = 40
FIRST_MSG_Y = 100
MSG_SPACING = 44
PADDING_X = 30
RIGHT_EXTRA = 220


@dataclass
class Message:
    from_idx: int
    to_idx: int
    label: str
    dashed: bool = False
    color: str = BLACK


MESSAGES = [
    Message(0, 1, "POST /login"),
    Message(1, 2, "validate(credentials)"),
    Message(2, 1, "JWT token", dashed=True),
    Message(1, 0, "200 OK + Set-Cookie", dashed=True),
    Message(0, 1, "GET /data (Bearer)"),
    Message(1, 2, "verify(jwt)"),
    Message(2, 1, "token valid", dashed=True),
    Message(1, 3, "fetchUserData()"),
    Message(3, 1, "JSON payload", dashed=True),
    Message(1, 0, "200 OK + JSON", dashed=True),
]

CALLOUT_AFTER_MSG = 2
CALLOUT_LINES = [
    "Auth Service validates credentials",
    "and returns a signed JWT. All later",
    "requests use this token \u2014 no session",
    "state stored on the server.",
]


def actor_x(idx: int) -> float:
    return PADDING_X + idx * ACTOR_SPACING


def main() -> None:
    Path("output").mkdir(exist_ok=True)

    n_actors = len(ACTORS)
    width = PADDING_X + (n_actors - 1) * ACTOR_SPACING + RIGHT_EXTRA
    height = FIRST_MSG_Y + len(MESSAGES) * MSG_SPACING + 60

    dwg = svgwrite.Drawing(
        OUTPUT, size=(f"{width}px", f"{height}px"),
        viewBox=f"0 0 {width} {height}",
    )
    dwg.add(dwg.rect(insert=(0, 0), size=(width, height), fill="white"))

    # Actor boxes and lifelines
    box_w = 120
    for i, name in enumerate(ACTORS):
        x = actor_x(i)
        dwg.add(dwg.rect(
            insert=(x - box_w / 2, HEADER_Y - 15), size=(box_w, 30),
            rx=3, ry=3, fill="#F0F0F0", stroke=BLACK, stroke_width=1.2,
        ))
        dwg.add(dwg.text(
            name, insert=(x, HEADER_Y + 4),
            text_anchor="middle", font_size="12px", font_weight="bold",
            font_family=FONT, fill=BLACK,
        ))
        line_end = FIRST_MSG_Y + len(MESSAGES) * MSG_SPACING + 20
        dwg.add(dwg.line(
            start=(x, HEADER_Y + 15), end=(x, line_end),
            stroke="#cccccc", stroke_width=1, stroke_dasharray="4,3",
        ))

    # Messages
    for i, msg in enumerate(MESSAGES):
        y = FIRST_MSG_Y + i * MSG_SPACING
        x1 = actor_x(msg.from_idx)
        x2 = actor_x(msg.to_idx)

        # Arrow line
        extra = {"stroke_dasharray": "5,3"} if msg.dashed else {}
        dwg.add(dwg.line(
            start=(x1, y), end=(x2, y),
            stroke=msg.color, stroke_width=1.2, **extra,
        ))

        # Arrowhead
        d = 1 if x2 > x1 else -1
        dwg.add(dwg.polygon(
            points=[(x2, y), (x2 - d * 6, y - 3), (x2 - d * 6, y + 3)],
            fill=msg.color,
        ))

        # Label near source, not centered
        label_x = x1 + 10
        dwg.add(dwg.text(
            msg.label, insert=(label_x, y - 6),
            text_anchor="start", font_family=MONO, font_size="11px",
            font_weight="bold", fill=msg.color,
        ))

    # Sticky-note callout
    step_y = FIRST_MSG_Y + CALLOUT_AFTER_MSG * MSG_SPACING
    note_x = actor_x(n_actors - 1) + 20
    note_y = step_y + 20
    # Compute width from longest line: ~0.55 × font_size per character for Helvetica
    callout_font_size = 10
    max_chars = max(len(line) for line in CALLOUT_LINES)
    note_w = int(max_chars * callout_font_size * 0.55) + 20
    line_h = 14
    note_h = len(CALLOUT_LINES) * line_h + 14
    fold = 8

    dwg.add(dwg.polygon(
        points=[
            (note_x, note_y),
            (note_x + note_w - fold, note_y),
            (note_x + note_w, note_y + fold),
            (note_x + note_w, note_y + note_h),
            (note_x, note_y + note_h),
        ],
        fill="#FFFDE7", stroke=ACCENT, stroke_width=0.8,
    ))
    dwg.add(dwg.polygon(
        points=[
            (note_x + note_w - fold, note_y),
            (note_x + note_w - fold, note_y + fold),
            (note_x + note_w, note_y + fold),
        ],
        fill=ACCENT, fill_opacity=0.15, stroke=ACCENT, stroke_width=0.5,
    ))
    dwg.add(dwg.line(
        start=(actor_x(n_actors - 1), step_y),
        end=(note_x, note_y + note_h // 2),
        stroke=ACCENT, stroke_width=0.8, stroke_dasharray="3,3",
    ))
    for j, line in enumerate(CALLOUT_LINES):
        dwg.add(dwg.text(
            line, insert=(note_x + 8, note_y + 14 + j * line_h),
            font_family=FONT, font_size="10px", font_weight="500",
            fill=BLACK,
        ))

    dwg.save()
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
