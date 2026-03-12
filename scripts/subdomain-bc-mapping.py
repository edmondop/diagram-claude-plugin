# /// script
# requires-python = ">=3.10"
# dependencies = ["drawsvg~=2.0"]
# ///
"""
Subdomain-to-Bounded Context mapping diagram.

Shows problem space (nested subdomains) on the left, solution space
(bounded contexts) on the right, with colored curves connecting them.

Patterns visible at a glance:
- 1:1 mapping  = clean single curve (healthy default)
- 1:N mapping  = subdomains fan out to multiple BCs (intentional decomposition)
- N:1 mapping  = multiple subdomains converge into one BC (anti-pattern)

Run: uv run subdomain-bc-mapping.py
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import drawsvg as draw

# ── Layout constants ──────────────────────────────────────────────
INNER_BOX_W = 240
INNER_BOX_H = 42
INNER_GAP = 10
GROUP_PAD_X = 16
GROUP_PAD_TOP = 36
GROUP_PAD_BOTTOM = 14
GROUP_GAP = 20

BC_BOX_W = 260
BC_BOX_H = 48
BC_GAP = 14

COLUMN_GAP = 300
LEFT_X = 50
TOP_PADDING = 80
CORNER_R = 7

OUTPUT = "output/subdomain-bc-mapping.svg"

# ── Colors ────────────────────────────────────────────────────────
GROUP_FILLS = ["#c4d4eb", "#d1c2eb", "#ebd1b8", "#b8e6cd"]
GROUP_BORDERS = ["#3b5d8f", "#6a4290", "#9a6530", "#2d8760"]
INNER_FILL = "#ffffff"
INNER_BORDER_DEFAULT = "#5a7fbf"
INNER_TEXT = "#1e3a5f"

BC_FILL = "#1b3a5c"
BC_BORDER = "#0f2740"
BC_TEXT = "#ffffff"

BAND_NORMAL = "#5a7fbf"
BAND_GOOD = "#1a8a4a"
BAND_BAD = "#c0392b"

HEADING_COLOR = "#0f1b2d"
LABEL_COLOR = "#1e3a5f"
ANNOTATION_COLOR = "#444444"
BG_COLOR = "#ffffff"
FONT = "Helvetica, Arial, sans-serif"


# ── Data ──────────────────────────────────────────────────────────

@dataclass
class SubdomainGroup:
    name: str
    children: list[str]


GROUPS = [
    SubdomainGroup("Order Management", [
        "Order Fulfillment",
        "Inventory Management",
        "Shipping & Logistics",
    ]),
    SubdomainGroup("Commerce", [
        "Product Catalog",
        "Pricing & Promotions",
    ]),
    SubdomainGroup("Customer Experience", [
        "Customer Management",
        "Returns & Refunds",
    ]),
    SubdomainGroup("Financial Operations", [
        "Payment Processing",
    ]),
]

BOUNDED_CONTEXTS = [
    "Order Fulfillment",
    "Warehouse Management",
    "Product Catalog",
    "Pricing",
    "Promotion Management",
    "Customer Management",
    "Returns & Refunds Handling",
    "Payment Processing",
]


@dataclass
class Mapping:
    subdomain: str
    bounded_context: str
    pattern: str  # "normal", "good", "bad"


MAPPINGS = [
    Mapping("Order Fulfillment", "Order Fulfillment", "normal"),
    Mapping("Inventory Management", "Warehouse Management", "bad"),
    Mapping("Shipping & Logistics", "Warehouse Management", "bad"),
    Mapping("Product Catalog", "Product Catalog", "normal"),
    Mapping("Pricing & Promotions", "Pricing", "good"),
    Mapping("Pricing & Promotions", "Promotion Management", "good"),
    Mapping("Customer Management", "Customer Management", "normal"),
    Mapping("Returns & Refunds", "Returns & Refunds Handling", "normal"),
    Mapping("Payment Processing", "Payment Processing", "normal"),
]


@dataclass
class Annotation:
    lines: list[str]
    pattern: str
    target_bc: str
    y_nudge: float = 0


ANNOTATIONS = [
    Annotation(
        ["N:1 — Two subdomains merged",
         "into one BC. Risk of coupled,",
         "tangled logic across concerns."],
        "bad",
        "Warehouse Management",
    ),
    Annotation(
        ["1:N — One subdomain split into",
         "focused systems. Independent teams",
         "can evolve pricing and campaigns",
         "at different speeds."],
        "good",
        "Pricing",
        y_nudge=14,
    ),
]


# ── Geometry: compute positions ───────────────────────────────────

@dataclass
class BoxPos:
    x: float
    y: float
    w: float
    h: float

    @property
    def cy(self) -> float:
        return self.y + self.h / 2

    @property
    def right(self) -> float:
        return self.x + self.w


def _compute_left_layout() -> tuple[dict[str, BoxPos], list[tuple[str, BoxPos]]]:
    """Returns (subdomain_positions, group_rects)."""
    sd_pos: dict[str, BoxPos] = {}
    group_rects: list[tuple[str, BoxPos]] = []
    cursor_y = TOP_PADDING

    group_w = INNER_BOX_W + 2 * GROUP_PAD_X

    for gi, group in enumerate(GROUPS):
        group_top = cursor_y
        inner_y = cursor_y + GROUP_PAD_TOP

        for child in group.children:
            sd_pos[child] = BoxPos(
                LEFT_X + GROUP_PAD_X, inner_y,
                INNER_BOX_W, INNER_BOX_H,
            )
            inner_y += INNER_BOX_H + INNER_GAP

        group_h = GROUP_PAD_TOP + len(group.children) * (INNER_BOX_H + INNER_GAP) - INNER_GAP + GROUP_PAD_BOTTOM
        group_rects.append((group.name, BoxPos(LEFT_X, group_top, group_w, group_h)))
        cursor_y += group_h + GROUP_GAP

    return sd_pos, group_rects


def _compute_right_layout(
    *,
    left_total_h: float,
) -> dict[str, BoxPos]:
    """Center BC column vertically to match left column height."""
    bc_pos: dict[str, BoxPos] = {}
    n = len(BOUNDED_CONTEXTS)
    total_bc_h = n * BC_BOX_H + (n - 1) * BC_GAP
    right_x = LEFT_X + (INNER_BOX_W + 2 * GROUP_PAD_X) + COLUMN_GAP
    start_y = TOP_PADDING + (left_total_h - total_bc_h) / 2

    for i, name in enumerate(BOUNDED_CONTEXTS):
        bc_pos[name] = BoxPos(right_x, start_y + i * (BC_BOX_H + BC_GAP), BC_BOX_W, BC_BOX_H)

    return bc_pos


# ── Drawing helpers ───────────────────────────────────────────────

def _draw_rounded_rect(
    d: draw.Drawing,
    pos: BoxPos,
    *,
    fill: str,
    stroke: str,
    stroke_width: float = 1.5,
    stroke_dasharray: str | None = None,
) -> None:
    kwargs: dict = dict(
        rx=CORNER_R, ry=CORNER_R,
        fill=fill, stroke=stroke, stroke_width=stroke_width,
    )
    if stroke_dasharray:
        kwargs["stroke_dasharray"] = stroke_dasharray
    d.append(draw.Rectangle(pos.x, pos.y, pos.w, pos.h, **kwargs))


def _draw_label(
    d: draw.Drawing,
    text: str,
    *,
    x: float,
    y: float,
    size: float = 13,
    color: str = LABEL_COLOR,
    weight: str = "bold",
    anchor: str = "middle",
) -> None:
    d.append(draw.Text(
        text, size, x, y,
        fill=color, text_anchor=anchor,
        font_family=FONT, font_weight=weight,
    ))


def _draw_curve(
    d: draw.Drawing,
    *,
    x1: float, y1: float,
    x2: float, y2: float,
    color: str,
    thickness: float,
) -> None:
    ctrl_x = (x1 + x2) / 2
    p = draw.Path(fill="none", stroke=color, stroke_width=thickness, stroke_opacity=0.55)
    p.M(x1, y1)
    p.C(ctrl_x, y1, ctrl_x, y2, x2, y2)
    d.append(p)


# ── Main ──────────────────────────────────────────────────────────

def main() -> None:
    Path("output").mkdir(exist_ok=True)

    sd_pos, group_rects = _compute_left_layout()
    last_group = group_rects[-1][1]
    left_total_h = (last_group.y + last_group.h) - TOP_PADDING
    bc_pos = _compute_right_layout(left_total_h=left_total_h)

    # compute canvas size
    rightmost_bc = max(bc_pos.values(), key=lambda b: b.right)
    ann_extra = 260  # space for annotations
    width = int(rightmost_bc.right + ann_extra)
    bottom = max(
        last_group.y + last_group.h,
        max(b.y + b.h for b in bc_pos.values()),
    )
    height = int(bottom + 80)

    d = draw.Drawing(width, height)
    d.append(draw.Rectangle(0, 0, width, height, fill=BG_COLOR))

    # ── Column headings ───────────────────────────────────────────
    left_cx = LEFT_X + (INNER_BOX_W + 2 * GROUP_PAD_X) / 2
    right_cx = list(bc_pos.values())[0].x + BC_BOX_W / 2

    _draw_label(d, "Problem Space", x=left_cx, y=30, size=20, color=HEADING_COLOR)
    _draw_label(d, "(Subdomains)", x=left_cx, y=50, size=12, color=ANNOTATION_COLOR, weight="normal")
    _draw_label(d, "Solution Space", x=right_cx, y=30, size=20, color=HEADING_COLOR)
    _draw_label(d, "(Bounded Contexts / Distinct Systems)", x=right_cx, y=50, size=12, color=ANNOTATION_COLOR, weight="normal")

    # ── Draw subdomain groups ─────────────────────────────────────
    for gi, (gname, gpos) in enumerate(group_rects):
        ci = gi % len(GROUP_FILLS)
        _draw_rounded_rect(d, gpos, fill=GROUP_FILLS[ci], stroke=GROUP_BORDERS[ci],
                           stroke_width=1.8, stroke_dasharray="6,3")
        _draw_label(d, gname, x=gpos.x + 12, y=gpos.y + 22,
                    size=12, color=GROUP_BORDERS[ci], weight="bold", anchor="start")

    # ── Draw inner subdomain boxes ────────────────────────────────
    # map each subdomain to its group's border color for a tinted left accent
    sd_group_color: dict[str, str] = {}
    for gi, group in enumerate(GROUPS):
        for child in group.children:
            sd_group_color[child] = GROUP_BORDERS[gi % len(GROUP_BORDERS)]

    for name, pos in sd_pos.items():
        accent = sd_group_color.get(name, INNER_BORDER_DEFAULT)
        _draw_rounded_rect(d, pos, fill=INNER_FILL, stroke=accent, stroke_width=1.8)
        # colored left accent bar
        bar_h = pos.h - 12
        d.append(draw.Rectangle(
            pos.x + 1, pos.y + 6, 4, bar_h,
            rx=2, ry=2, fill=accent,
        ))
        _draw_label(d, name, x=pos.x + pos.w / 2 + 4, y=pos.cy + 5,
                    size=12.5, color=INNER_TEXT)

    # ── Draw BC boxes ─────────────────────────────────────────────
    for name, pos in bc_pos.items():
        _draw_rounded_rect(d, pos, fill=BC_FILL, stroke=BC_BORDER, stroke_width=1.6)
        _draw_label(d, name, x=pos.x + pos.w / 2, y=pos.cy + 5,
                    size=12.5, color=BC_TEXT)

    # ── Draw connection curves ────────────────────────────────────
    color_map = {"normal": BAND_NORMAL, "good": BAND_GOOD, "bad": BAND_BAD}
    thickness_map = {"normal": 2.2, "good": 3.0, "bad": 3.0}

    for m in MAPPINGS:
        sp = sd_pos[m.subdomain]
        bp = bc_pos[m.bounded_context]
        _draw_curve(d,
                    x1=sp.right, y1=sp.cy,
                    x2=bp.x, y2=bp.cy,
                    color=color_map[m.pattern],
                    thickness=thickness_map[m.pattern])

    # ── Draw annotations ──────────────────────────────────────────
    for ann in ANNOTATIONS:
        bp = bc_pos[ann.target_bc]
        ax = bp.right + 18
        line_h = 15
        cy = bp.cy + ann.y_nudge

        start_y = cy - (len(ann.lines) - 1) * line_h / 2
        pill_w = 220
        pill_h = len(ann.lines) * line_h + 14
        pill_y = start_y - line_h + 1
        ann_color = color_map[ann.pattern]

        _draw_rounded_rect(d, BoxPos(ax - 8, pill_y - 3, pill_w, pill_h),
                           fill=ann_color, stroke=ann_color, stroke_width=1.0)
        # override fill opacity via a white underlay + transparent colored overlay
        d.append(draw.Rectangle(ax - 8, pill_y - 3, pill_w, pill_h,
                                rx=CORNER_R, ry=CORNER_R,
                                fill=BG_COLOR, fill_opacity=0.92,
                                stroke=ann_color, stroke_width=1.0, stroke_opacity=0.3))

        for j, line in enumerate(ann.lines):
            _draw_label(d, line, x=ax, y=start_y + j * line_h,
                        size=11, color=ann_color, weight="600", anchor="start")

    # ── Legend ─────────────────────────────────────────────────────
    legend_y = height - 30
    legend_items = [
        ("1 : 1 — clean alignment", BAND_NORMAL),
        ("1 : N — intentional split", BAND_GOOD),
        ("N : 1 — conflation risk", BAND_BAD),
    ]

    lx = LEFT_X
    for label, color in legend_items:
        d.append(draw.Line(lx, legend_y, lx + 30, legend_y,
                           stroke=color, stroke_width=3, stroke_opacity=0.6))
        _draw_label(d, label, x=lx + 38, y=legend_y + 4,
                    size=11, color=ANNOTATION_COLOR, weight="normal", anchor="start")
        lx += 260

    d.save_svg(OUTPUT)
    print(f"Saved: {OUTPUT}")


if __name__ == "__main__":
    main()
