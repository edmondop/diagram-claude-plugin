"""Geometry primitives for SVG quality checks."""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from shapely.geometry import LineString
from shapely.geometry import box as shapely_box
from svgpathtools import parse_path

PATH_SAMPLES = 200


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
    coords = re.findall(r"(-?\d+\.?\d*),(-?\d+\.?\d*)", d)
    if not coords:
        nums = re.findall(r"(-?\d+\.?\d*)", d)
        nums = [float(n) for n in nums]
        if len(nums) < 2:
            return None
        xs = nums[0::2]
        ys = nums[1::2]
        return BBox(min(xs), min(ys), max(xs), max(ys))
    xs = [float(c[0]) for c in coords]
    ys = [float(c[1]) for c in coords]
    return BBox(min(xs), min(ys), max(xs), max(ys))


def text_bbox(elem: ET.Element) -> BBox | None:
    x_str = elem.get("x")
    y_str = elem.get("y")
    if x_str is None or y_str is None:
        return None
    x, y = float(x_str), float(y_str)
    text = elem.text or ""
    font_size = 10.0
    fs_attr = elem.get("font-size", "10")
    fs_match = re.match(r"(\d+\.?\d*)", fs_attr)
    if fs_match:
        font_size = float(fs_match.group(1))
    char_w = font_size * 0.6
    text_w = len(text) * char_w
    anchor = elem.get("text-anchor", "start")
    if anchor == "middle":
        x_min = x - text_w / 2
    elif anchor == "end":
        x_min = x - text_w
    else:
        x_min = x
    return BBox(x_min, y - font_size, x_min + text_w, y)
