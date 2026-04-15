"""Geometry primitives for SVG quality checks."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass

from shapely.geometry import LineString
from shapely.geometry import box as shapely_box
from svgpathtools import parse_path

PATH_SAMPLES = 200
DEFAULT_FONT_SIZE = 10.0
CHAR_WIDTH_RATIO = 0.6


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


def text_bbox(elem: ET.Element) -> BBox | None:
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
    return BBox(x_min, y - font_size, x_min + text_w, y)
