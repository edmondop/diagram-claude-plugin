# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest", "svgpathtools", "shapely"]
# ///
"""
Tests for SVG diagram quality — detects common Graphviz layout problems.

Run: uv run pytest test_svg_quality.py -v

Critical rules:
  1. No arrow path may cross ANY text (cluster labels, edge labels, node labels)
  2. No text may cross ANY cluster border

Uses svgpathtools for proper Bezier curve sampling and shapely for
geometric intersection tests.

Fixtures in test_fixtures/ are known-bad SVGs that MUST fail at least one
check. If a fixture passes all checks, the test suite itself is broken.
"""

import re
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path

import pytest
from shapely.geometry import LineString, box as shapely_box
from svgpathtools import parse_path

EXAMPLES_DIR = Path(__file__).parent
FIXTURES_DIR = EXAMPLES_DIR / "test_fixtures"
OUTPUT_DIR = EXAMPLES_DIR / "output"

PATH_SAMPLES = 200
ARROW_TEXT_PADDING = 2.0  # px inflation around text when checking arrow crossing
BORDER_STROKE_WIDTH = 2.0  # px stroke width for border overlap checks
MAX_CENTER_OFFSET_RATIO = 0.7


# ---------------------------------------------------------------------------
# Geometry helpers
# ---------------------------------------------------------------------------


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


def svg_path_to_linestring(d: str, num_samples: int = PATH_SAMPLES) -> LineString:
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
        return None
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


# ---------------------------------------------------------------------------
# SVG parser
# ---------------------------------------------------------------------------


@dataclass
class ParsedSVG:
    clusters: dict[str, BBox]
    cluster_labels: dict[str, tuple[str, BBox]]
    cluster_border_paths: dict[str, str]  # cluster name → raw d attribute
    node_labels: list[tuple[str, BBox]]
    edge_labels: list[tuple[str, str, BBox]]  # (display_name, edge_id, bbox)
    edge_paths: list[tuple[str, str]]  # (edge_id, raw d attribute)


def parse_svg(svg_path: Path) -> ParsedSVG:
    tree = ET.parse(svg_path)
    root = tree.getroot()

    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    graph_g = root.find(".//g[@id='graph0']")
    assert graph_g is not None, f"No graph0 group in {svg_path}"

    clusters: dict[str, BBox] = {}
    cluster_labels: dict[str, tuple[str, BBox]] = {}
    cluster_border_paths: dict[str, str] = {}

    for g in graph_g.findall(".//g[@class='cluster']"):
        title = g.find("title")
        if title is None or title.text is None:
            continue
        name = title.text
        path = g.find("path")
        if path is not None:
            d = path.get("d", "")
            bb = bbox_from_path_d(d)
            if bb:
                clusters[name] = bb
                cluster_border_paths[name] = d
        text_el = g.find("text")
        if text_el is not None:
            tb = text_bbox(text_el)
            if tb:
                cluster_labels[name] = (text_el.text or "", tb)

    node_labels: list[tuple[str, BBox]] = []
    for g in graph_g.findall(".//g[@class='node']"):
        title = g.find("title")
        node_name = title.text if title is not None and title.text else "?"
        text_el = g.find("text")
        if text_el is not None:
            tb = text_bbox(text_el)
            if tb:
                node_labels.append((node_name, tb))

    edge_labels: list[tuple[str, str, BBox]] = []
    edge_paths: list[tuple[str, str]] = []

    for g in graph_g.findall(".//g[@class='edge']"):
        title = g.find("title")
        edge_name = title.text if title is not None and title.text else "?"
        for text_el in g.findall("text"):
            tb = text_bbox(text_el)
            if tb:
                label_text = (text_el.text or "").strip()
                edge_labels.append((f"{edge_name}: '{label_text}'", edge_name, tb))
        path_el = g.find("path")
        if path_el is not None:
            d = path_el.get("d", "")
            if d:
                edge_paths.append((edge_name, d))

    return ParsedSVG(
        clusters,
        cluster_labels,
        cluster_border_paths,
        node_labels,
        edge_labels,
        edge_paths,
    )


# ---------------------------------------------------------------------------
# Quality checks — each returns a list of error strings
# ---------------------------------------------------------------------------


def check_arrow_crosses_any_text(
    svg: ParsedSVG,
    *,
    padding: float = ARROW_TEXT_PADDING,
) -> list[str]:
    """CRITICAL: No arrow path may cross ANY text."""
    errors: list[str] = []

    all_text: list[tuple[str, str | None, BBox]] = []
    for name, (text, bb) in svg.cluster_labels.items():
        all_text.append((f"cluster label '{text}'", None, bb))
    for display_name, edge_id, bb in svg.edge_labels:
        all_text.append((f"edge label {display_name}", edge_id, bb))
    for node_name, bb in svg.node_labels:
        all_text.append((f"node '{node_name}'", None, bb))

    for edge_name, d in svg.edge_paths:
        arrow_line = svg_path_to_linestring(d)
        for text_name, owner_edge, text_bb in all_text:
            if owner_edge == edge_name:
                continue
            text_poly = text_bb.to_shapely().buffer(padding)
            if arrow_line.intersects(text_poly):
                errors.append(f"Arrow {edge_name} crosses {text_name}")

    return errors


def check_text_crosses_border(
    svg: ParsedSVG,
    *,
    stroke_width: float = BORDER_STROKE_WIDTH,
) -> list[str]:
    """CRITICAL: No text may cross any cluster border."""
    errors: list[str] = []

    all_text: list[tuple[str, str | None, BBox]] = []
    for name, (text, bb) in svg.cluster_labels.items():
        all_text.append((f"cluster label '{text}'", name, bb))
    for display_name, _, bb in svg.edge_labels:
        all_text.append((f"edge label {display_name}", None, bb))
    for node_name, bb in svg.node_labels:
        all_text.append((f"node '{node_name}'", None, bb))

    for cluster_name, d in svg.cluster_border_paths.items():
        border_line = svg_path_to_linestring(d)
        thick_border = border_line.buffer(stroke_width / 2)
        for text_name, owner_cluster, text_bb in all_text:
            if owner_cluster == cluster_name:
                continue
            text_poly = text_bb.to_shapely()
            if text_poly.intersects(thick_border):
                errors.append(f"{text_name} crosses {cluster_name} border")

    return errors


def check_data_layer_position(svg: ParsedSVG) -> list[str]:
    """Data layer should be roughly centered below backend."""
    errors: list[str] = []
    be = svg.clusters.get("cluster_backend")
    dl = svg.clusters.get("cluster_data")
    if be is None or dl is None:
        return errors

    offset = abs(dl.cx - be.cx)
    max_offset = max(be.width, dl.width) * MAX_CENTER_OFFSET_RATIO
    if offset > max_offset:
        direction = "right" if dl.cx > be.cx else "left"
        errors.append(
            f"Data layer center (x={dl.cx:.0f}) is {offset:.0f}px from "
            f"backend center (x={be.cx:.0f}) — max {max_offset:.0f}px. "
            f"Too far to the {direction}"
        )
    return errors


def check_label_overlaps(svg: ParsedSVG) -> list[str]:
    """No two text labels should overlap each other."""
    errors: list[str] = []
    all_labels: list[tuple[str, BBox]] = []
    all_labels.extend(
        (f"cluster:{name} '{text}'", bb)
        for name, (text, bb) in svg.cluster_labels.items()
    )
    all_labels.extend((display_name, bb) for display_name, _, bb in svg.edge_labels)
    all_labels.extend(svg.node_labels)
    for i, (name_a, bb_a) in enumerate(all_labels):
        for name_b, bb_b in all_labels[i + 1 :]:
            if bb_a.overlaps(bb_b):
                errors.append(f"Labels overlap: {name_a} vs {name_b}")
    return errors


def run_all_checks(svg: ParsedSVG) -> list[str]:
    errors: list[str] = []
    errors.extend(check_arrow_crosses_any_text(svg))
    errors.extend(check_text_crosses_border(svg))
    errors.extend(check_data_layer_position(svg))
    errors.extend(check_label_overlaps(svg))
    return errors


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestOutputDiagram:
    """Tests for the generated architecture diagram."""

    @pytest.fixture
    def svg(self) -> ParsedSVG:
        svg_path = OUTPUT_DIR / "architecture-graphviz.svg"
        if not svg_path.exists():
            pytest.skip("Run architecture-graphviz.py first")
        return parse_svg(svg_path)

    def test_no_arrow_crosses_any_text(self, svg: ParsedSVG) -> None:
        errors = check_arrow_crosses_any_text(svg)
        assert not errors, "\n".join(errors)

    def test_no_text_crosses_any_border(self, svg: ParsedSVG) -> None:
        errors = check_text_crosses_border(svg)
        assert not errors, "\n".join(errors)

    def test_data_layer_centered_below_backend(self, svg: ParsedSVG) -> None:
        errors = check_data_layer_position(svg)
        assert not errors, "\n".join(errors)

    def test_no_label_overlaps(self, svg: ParsedSVG) -> None:
        errors = check_label_overlaps(svg)
        assert not errors, "\n".join(errors)


class TestFixturesMustFail:
    """Known-bad SVGs must fail at least one quality check.

    If a fixture passes all checks, either the fixture is wrong or
    the checks are too lenient.
    """

    @pytest.fixture(params=sorted(FIXTURES_DIR.glob("*.svg")))
    def fixture_svg(self, request: pytest.FixtureRequest) -> tuple[str, ParsedSVG]:
        path = request.param
        return (path.name, parse_svg(path))

    def test_fixture_fails_at_least_one_check(
        self, fixture_svg: tuple[str, ParsedSVG]
    ) -> None:
        name, svg = fixture_svg
        errors = run_all_checks(svg)
        assert errors, (
            f"Fixture {name} passed ALL checks — either the fixture "
            f"is not actually broken or the checks are too lenient"
        )


# ---------------------------------------------------------------------------
# CLI entry point for quick validation
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    import sys

    svg_path = (
        Path(sys.argv[1])
        if len(sys.argv) > 1
        else OUTPUT_DIR / "architecture-graphviz.svg"
    )
    if not svg_path.exists():
        print(f"File not found: {svg_path}")
        sys.exit(1)

    svg = parse_svg(svg_path)
    errors = run_all_checks(svg)

    print(
        f"Parsed: {len(svg.clusters)} clusters, "
        f"{len(svg.node_labels)} nodes, "
        f"{len(svg.edge_labels)} edge labels"
    )
    if errors:
        print(f"\nERRORS ({len(errors)}):")
        for e in errors:
            print(f"  ✘ {e}")
        sys.exit(1)
    else:
        print("✓ All checks passed!")
