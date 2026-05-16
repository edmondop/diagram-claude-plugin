"""Geometry primitives for SVG quality checks."""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from shapely.geometry import LineString
from shapely.geometry import box as shapely_box
from svgpathtools import parse_path

PATH_SAMPLES = 200
DEFAULT_FONT_SIZE = 10.0
CHAR_WIDTH_RATIO = 0.6

_TRANSLATE_RE = re.compile(
    r"translate\(\s*([^,\s]+)[\s,]+([^)]+)\)"
)
_SCALE_RE = re.compile(
    r"scale\(\s*([^,\s)]+)(?:[\s,]+([^)]+))?\)"
)


@dataclass
class BBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    @property
    def cx(self) -> float:
        return (self.x_min + self.x_max) / 2

    @property
    def width(self) -> float:
        return self.x_max - self.x_min

    def overlaps(self, other: "BBox") -> bool:
        return (
            self.x_min < other.x_max
            and self.x_max > other.x_min
            and self.y_min < other.y_max
            and self.y_max > other.y_min
        )

    def to_shapely(self):
        return shapely_box(self.x_min, self.y_min, self.x_max, self.y_max)


def path_to_linestring(
    d: str,
    *,
    num_samples: int = PATH_SAMPLES,
) -> LineString:
    path = parse_path(d)
    points = []
    for i in range(num_samples + 1):
        t = i / num_samples
        pt = path.point(t)
        points.append((pt.real, pt.imag))
    return LineString(points)


def bbox_from_path_d(d: str) -> BBox | None:
    try:
        path = parse_path(d)
        x_min, x_max, y_min, y_max = path.bbox()
        return BBox(x_min, y_min, x_max, y_max)
    except Exception:
        return None


def _parse_transform(transform: str) -> tuple[float, float, float, float]:
    """Parse a transform attribute and return (tx, ty, sx, sy)."""
    tx, ty = 0.0, 0.0
    sx, sy = 1.0, 1.0
    m = _TRANSLATE_RE.search(transform)
    if m:
        tx = float(m.group(1))
        ty = float(m.group(2))
    m = _SCALE_RE.search(transform)
    if m:
        sx = float(m.group(1))
        sy = float(m.group(2)) if m.group(2) else sx
    return tx, ty, sx, sy


def resolve_ancestor_transform(
    elem: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> tuple[float, float, float, float]:
    """Walk up the tree accumulating translate and scale transforms.

    Returns (total_tx, total_ty, total_sx, total_sy).
    """
    total_tx, total_ty = 0.0, 0.0
    total_sx, total_sy = 1.0, 1.0
    current = elem
    for _ in range(20):
        parent = parent_map.get(current)
        if parent is None:
            break
        transform = parent.get("transform")
        if transform:
            tx, ty, sx, sy = _parse_transform(transform)
            # The translate applies after the parent's scale
            total_tx = total_tx * sx + tx
            total_ty = total_ty * sy + ty
            total_sx *= sx
            total_sy *= sy
        current = parent
    return total_tx, total_ty, total_sx, total_sy


def text_bbox(
    elem: ET.Element,
    parent_map: dict[ET.Element, ET.Element] | None = None,
) -> BBox | None:
    x_str = elem.get("x")
    y_str = elem.get("y")
    if x_str is None or y_str is None:
        return None
    x, y = float(x_str), float(y_str)
    text = elem.text or ""
    fs_raw = elem.get("font-size", str(DEFAULT_FONT_SIZE))
    font_size = float(fs_raw.replace("px", "").replace("pt", ""))
    char_w = font_size * CHAR_WIDTH_RATIO
    text_w = len(text) * char_w
    anchor = elem.get("text-anchor", "start")
    if anchor == "middle":
        x_min = x - text_w / 2
    elif anchor == "end":
        x_min = x - text_w
    else:
        x_min = x

    y_min = y - font_size
    y_max = y
    x_max = x_min + text_w

    # Apply ancestor transforms if parent_map is provided
    if parent_map is not None:
        tx, ty, sx, sy = resolve_ancestor_transform(elem, parent_map)
        x_min = x_min * sx + tx
        x_max = x_max * sx + tx
        y_min = y_min * sy + ty
        y_max = y_max * sy + ty

    return BBox(x_min, y_min, x_max, y_max)
