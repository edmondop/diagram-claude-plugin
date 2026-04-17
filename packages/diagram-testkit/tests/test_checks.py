"""Tests for SVG quality checks.

Critical: every fixture SVG must fail at least one check.
If a fixture passes all checks, the test suite itself is broken.
"""

from pathlib import Path

import pytest

from diagram_testkit.checks import check_arrow_crosses_text
from diagram_testkit.checks import check_container_alignment
from diagram_testkit.checks import check_child_rect_clips_parent
from diagram_testkit.checks import check_line_crosses_text
from diagram_testkit.checks import check_path_crosses_text
from diagram_testkit.checks import check_path_endpoint_inside_rect
from diagram_testkit.checks import check_text_on_cluster_border
from diagram_testkit.checks import check_text_outside_viewport
from diagram_testkit.checks import check_text_overlaps_text
from diagram_testkit.checks import check_text_overflows_rect
from diagram_testkit.checks import run_all_checks_with_file
from diagram_testkit.extractors import extract
from diagram_testkit.geometry import BBox
from diagram_testkit.model import ArrowPath
from diagram_testkit.model import Container
from diagram_testkit.model import DiagramElements
from diagram_testkit.model import TextLabel

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestFixturesMustFail:

    @pytest.fixture(params=sorted(FIXTURES_DIR.glob("*.svg")))
    def fixture_elems(self, request: pytest.FixtureRequest):
        path = request.param
        return (path.name, extract(path))

    def test_fixture_fails_at_least_one_check(
        self, fixture_elems: tuple[str, DiagramElements],
    ) -> None:
        name, elems = fixture_elems
        errors = run_all_checks_with_file(elems, elems.source_path)
        assert errors, (
            f"Fixture {name} passed ALL checks - either the fixture "
            f"is not actually broken or the checks are too lenient"
        )


class TestArrowCrossesText:

    def test_crossing_arrow_detected(self):
        elems = DiagramElements(
            texts=[TextLabel(id="label", bbox=BBox(5, 5, 15, 15))],
            arrows=[ArrowPath(id="arrow", path_d="M 0,10 L 20,10")],
        )
        errors = check_arrow_crosses_text(elems)
        assert errors
        assert "arrow" in errors[0].lower() or "Arrow" in errors[0]

    def test_same_owner_skipped(self):
        elems = DiagramElements(
            texts=[TextLabel(id="label", bbox=BBox(5, 5, 15, 15), owner="e1")],
            arrows=[ArrowPath(id="arrow", path_d="M 0,10 L 20,10", owner="e1")],
        )
        errors = check_arrow_crosses_text(elems)
        assert not errors


class TestTextOverlapsText:

    def test_overlapping_texts_detected(self):
        elems = DiagramElements(
            texts=[
                TextLabel(id="t1", bbox=BBox(0, 0, 20, 10)),
                TextLabel(id="t2", bbox=BBox(10, 0, 30, 10)),
            ],
        )
        errors = check_text_overlaps_text(elems)
        assert errors

    def test_same_owner_skipped(self):
        elems = DiagramElements(
            texts=[
                TextLabel(id="t1", bbox=BBox(0, 0, 20, 10), owner="e1"),
                TextLabel(id="t2", bbox=BBox(10, 0, 30, 10), owner="e1"),
            ],
        )
        errors = check_text_overlaps_text(elems)
        assert not errors

    def test_fixture_chart_labels_overlap(self):
        fixture = FIXTURES_DIR / "svgwrite-chart-labels-overlap.svg"
        assert fixture.exists()
        elems = extract(fixture)
        errors = check_text_overlaps_text(elems)
        assert len(errors) >= 2, (
            f"Expected at least 2 overlapping label pairs (threshold labels + sub-labels), "
            f"got {len(errors)}: " + "\n".join(errors)
        )


class TestContainerAlignment:

    def test_aligned_containers_pass(self):
        elems = DiagramElements(
            containers=[
                Container(id="a", bbox=BBox(100, 0, 200, 50)),
                Container(id="b", bbox=BBox(110, 60, 210, 110)),
            ],
        )
        errors = check_container_alignment(elems, src="a", dst="b")
        assert not errors

    def test_misaligned_containers_fail(self):
        elems = DiagramElements(
            containers=[
                Container(id="a", bbox=BBox(0, 0, 100, 50)),
                Container(id="b", bbox=BBox(500, 60, 600, 110)),
            ],
        )
        errors = check_container_alignment(elems, src="a", dst="b")
        assert errors
        assert "Too far" in errors[0]

    def test_missing_container_returns_empty(self):
        elems = DiagramElements()
        errors = check_container_alignment(
            elems, src="nonexistent", dst="also_nonexistent"
        )
        assert not errors


class TestTextOverflowsRect:

    def test_text_fitting_inside_rect_passes(self, tmp_path):
        svg = tmp_path / "ok.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<rect x="0" y="0" width="200" height="40" />'
            '<text x="100" y="25" text-anchor="middle" '
            'font-size="11px">Short</text>'
            '</svg>'
        )
        errors = check_text_overflows_rect(svg)
        assert not errors

    def test_text_overflowing_rect_detected(self, tmp_path):
        svg = tmp_path / "overflow.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<rect x="100" y="0" width="80" height="40" />'
            '<text x="140" y="25" text-anchor="middle" '
            'font-size="11px">This label is way too long for the box</text>'
            '</svg>'
        )
        errors = check_text_overflows_rect(svg)
        assert errors
        assert "overflows" in errors[0]

    def test_text_outside_rect_ignored(self, tmp_path):
        svg = tmp_path / "outside.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<rect x="0" y="0" width="50" height="40" />'
            '<text x="400" y="25" text-anchor="middle" '
            'font-size="11px">This text is far away from the rect</text>'
            '</svg>'
        )
        errors = check_text_overflows_rect(svg)
        assert not errors

    def test_fixture_detects_overflow(self):
        fixture = FIXTURES_DIR / "svgwrite-text-overflows-rect.svg"
        assert fixture.exists(), f"Fixture not found: {fixture}"
        errors = check_text_overflows_rect(fixture)
        assert errors, "Fixture should have at least one text overflow"
        overflow_texts = [e for e in errors if "overflows" in e]
        assert len(overflow_texts) >= 2, (
            f"Expected at least 2 overflow errors, got {len(overflow_texts)}: "
            + "\n".join(errors)
        )


class TestLineCrossesText:

    def test_line_through_text_detected(self, tmp_path):
        svg = tmp_path / "crossing.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<text x="100" y="55" text-anchor="middle" '
            'font-size="13px">Label</text>'
            '<line x1="50" y1="50" x2="150" y2="50" stroke="#333" />'
            '</svg>'
        )
        errors = check_line_crosses_text(svg)
        assert errors
        assert "Label" in errors[0]

    def test_line_far_from_text_passes(self, tmp_path):
        svg = tmp_path / "ok.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg">'
            '<text x="100" y="50" text-anchor="middle" '
            'font-size="13px">Label</text>'
            '<line x1="50" y1="200" x2="150" y2="200" stroke="#333" />'
            '</svg>'
        )
        errors = check_line_crosses_text(svg)
        assert not errors

    def test_fixture_detects_crossing(self):
        fixture = FIXTURES_DIR / "svgwrite-line-crosses-text.svg"
        assert fixture.exists()
        errors = check_line_crosses_text(fixture)
        assert len(errors) >= 3, (
            f"Expected at least 3 line-crosses-text errors (Hub + 3 spokes), "
            f"got {len(errors)}: " + "\n".join(errors)
        )


class TestPathCrossesText:

    def test_bezier_through_text_detected(self, tmp_path):
        svg = tmp_path / "crossing.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">'
            '<rect x="0" y="0" width="400" height="300" fill="#fff" />'
            '<text x="200" y="150" text-anchor="middle" font-size="10">Label</text>'
            '<path d="M100,50 C100,150,300,150,300,250" stroke="#666" '
            'stroke-width="1.2" fill="none" />'
            '</svg>'
        )
        errors = check_path_crosses_text(svg)
        assert errors
        assert "Label" in errors[0]

    def test_bezier_through_rect_detected(self, tmp_path):
        svg = tmp_path / "rect-crossing.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
            '<rect x="0" y="0" width="400" height="200" fill="#fff" />'
            '<rect x="150" y="50" width="100" height="40" fill="#eee" stroke="#999" />'
            '<text x="200" y="74" text-anchor="middle" font-size="10">Box</text>'
            '<path d="M50,70 L350,70" stroke="#666" stroke-width="1.2" fill="none" />'
            '</svg>'
        )
        errors = check_path_crosses_text(svg)
        rect_errors = [e for e in errors if "rect" in e.lower()]
        assert rect_errors, f"Expected path-crosses-rect error, got: {errors}"

    def test_path_not_crossing_passes(self, tmp_path):
        svg = tmp_path / "ok.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">'
            '<rect x="0" y="0" width="400" height="300" fill="#fff" />'
            '<text x="200" y="50" text-anchor="middle" font-size="10">Label</text>'
            '<path d="M50,200 L350,200" stroke="#666" stroke-width="1.2" fill="none" />'
            '</svg>'
        )
        errors = check_path_crosses_text(svg)
        assert not errors

    def test_marker_paths_in_defs_skipped(self, tmp_path):
        svg = tmp_path / "marker.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="300">'
            '<defs><marker id="arrow"><path d="M0,-2.5 L6,0 L0,2.5" /></marker></defs>'
            '<text x="200" y="150" text-anchor="middle" font-size="10">Label</text>'
            '</svg>'
        )
        errors = check_path_crosses_text(svg)
        assert not errors

    def test_fixture_detects_crossings(self):
        fixture = FIXTURES_DIR / "svgwrite-path-crosses-text-and-rect.svg"
        assert fixture.exists()
        errors = check_path_crosses_text(fixture)
        text_errors = [e for e in errors if "text" in e.lower()]
        rect_errors = [e for e in errors if "rect" in e.lower()]
        assert text_errors, (
            f"Expected path-crosses-text errors, got: {errors}"
        )
        assert rect_errors, (
            f"Expected path-crosses-rect errors, got: {errors}"
        )


class TestTextOutsideViewport:

    def test_text_inside_viewport_passes(self, tmp_path):
        svg = tmp_path / "ok.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400px" height="200px">'
            '<text x="200" y="100" text-anchor="middle" '
            'font-size="10px">Centered</text>'
            '</svg>'
        )
        errors = check_text_outside_viewport(svg)
        assert not errors

    def test_text_clipped_right_detected(self, tmp_path):
        svg = tmp_path / "clip-right.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="200px" height="100px">'
            '<text x="180" y="50" font-size="10px">'
            'This text runs way past the right edge</text>'
            '</svg>'
        )
        errors = check_text_outside_viewport(svg)
        assert errors
        assert "right" in errors[0]

    def test_text_clipped_left_detected(self, tmp_path):
        svg = tmp_path / "clip-left.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="200px" height="100px">'
            '<text x="10" y="50" text-anchor="end" font-size="10px">'
            'Right-aligned text that extends left</text>'
            '</svg>'
        )
        errors = check_text_outside_viewport(svg)
        assert errors
        assert "left" in errors[0]

    def test_fixture_detects_clipping(self):
        fixture = FIXTURES_DIR / "svgwrite-text-outside-viewport.svg"
        assert fixture.exists()
        errors = check_text_outside_viewport(fixture)
        assert len(errors) >= 2, (
            f"Expected at least 2 viewport clipping errors, "
            f"got {len(errors)}: " + "\n".join(errors)
        )


class TestPathEndpointInsideRect:

    def test_endpoint_inside_rect_detected(self, tmp_path):
        svg = tmp_path / "overflow.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
            '<rect x="0" y="0" width="400" height="200" fill="#fff" />'
            '<rect x="250" y="70" width="100" height="40" fill="#E8EAF6" stroke="#7986CB" />'
            '<text x="300" y="94" text-anchor="middle" font-size="10">Dest</text>'
            '<path d="M150,90 C200,90,240,90,280,90" stroke="#666" fill="none" />'
            '</svg>'
        )
        errors = check_path_endpoint_inside_rect(svg)
        assert errors
        assert "inside rect" in errors[0]

    def test_endpoint_on_border_passes(self, tmp_path):
        svg = tmp_path / "ok.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
            '<rect x="0" y="0" width="400" height="200" fill="#fff" />'
            '<rect x="250" y="70" width="100" height="40" fill="#E8EAF6" stroke="#7986CB" />'
            '<text x="300" y="94" text-anchor="middle" font-size="10">Dest</text>'
            '<path d="M150,90 L250,90" stroke="#666" fill="none" />'
            '</svg>'
        )
        errors = check_path_endpoint_inside_rect(svg)
        assert not errors

    def test_marker_paths_skipped(self, tmp_path):
        svg = tmp_path / "marker.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
            '<rect x="0" y="0" width="400" height="200" fill="#fff" />'
            '<defs><marker id="arrow">'
            '<path d="M0,-2.5 L6,0 L0,2.5" fill="#666" />'
            '</marker></defs>'
            '<rect x="250" y="70" width="100" height="40" fill="#E8EAF6" stroke="#7986CB" />'
            '</svg>'
        )
        errors = check_path_endpoint_inside_rect(svg)
        assert not errors

    def test_fixture_detects_overflow(self):
        fixture = FIXTURES_DIR / "svgwrite-path-endpoint-inside-rect.svg"
        assert fixture.exists()
        errors = check_path_endpoint_inside_rect(fixture)
        assert errors, "Fixture should detect arrow endpoint inside rect"
        assert any("inside rect" in e for e in errors)


class TestTextOnClusterBorder:

    def test_text_on_dashed_border_detected(self, tmp_path):
        svg = tmp_path / "on-border.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
            '<rect x="0" y="0" width="400" height="200" fill="#fff" />'
            '<rect x="50" y="50" width="200" height="100" fill="none" '
            'stroke="#7986CB" stroke-width="2" stroke-dasharray="8,4" />'
            '<text x="230" y="105" font-size="9">[D] GraphQL</text>'
            '</svg>'
        )
        errors = check_text_on_cluster_border(svg)
        assert errors
        assert "cluster border" in errors[0]

    def test_text_far_from_border_passes(self, tmp_path):
        svg = tmp_path / "ok.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
            '<rect x="0" y="0" width="400" height="200" fill="#fff" />'
            '<rect x="50" y="50" width="200" height="100" fill="none" '
            'stroke="#7986CB" stroke-width="2" stroke-dasharray="8,4" />'
            '<text x="150" y="105" text-anchor="middle" font-size="9">Inside</text>'
            '</svg>'
        )
        errors = check_text_on_cluster_border(svg)
        assert not errors

    def test_cluster_title_skipped(self, tmp_path):
        svg = tmp_path / "title.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
            '<rect x="0" y="0" width="400" height="200" fill="#fff" />'
            '<rect x="50" y="50" width="200" height="100" fill="none" '
            'stroke="#7986CB" stroke-width="2" stroke-dasharray="8,4" />'
            '<text x="62" y="68" font-size="12" font-weight="bold">IBT</text>'
            '</svg>'
        )
        errors = check_text_on_cluster_border(svg)
        assert not errors

    def test_fixture_detects_border_overlap(self):
        fixture = FIXTURES_DIR / "svgwrite-text-on-cluster-border.svg"
        assert fixture.exists()
        errors = check_text_on_cluster_border(fixture)
        assert len(errors) >= 2, (
            f"Expected at least 2 text-on-border errors, "
            f"got {len(errors)}: " + "\n".join(errors)
        )


class TestChildRectClipsParent:

    def test_clipping_child_detected(self, tmp_path):
        svg = tmp_path / "clip.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
            '<rect x="0" y="0" width="400" height="200" fill="#fff" />'
            '<rect x="50" y="50" width="200" height="100" fill="none" '
            'stroke="#81C784" stroke-width="2" stroke-dasharray="8,4" />'
            '<rect x="48" y="70" width="100" height="40" fill="#E8F5E9" stroke="#81C784" />'
            '<text x="98" y="94" text-anchor="middle" font-size="10">Clip</text>'
            '</svg>'
        )
        errors = check_child_rect_clips_parent(svg)
        assert errors
        assert "clips parent" in errors[0]
        assert "left" in errors[0]

    def test_well_placed_child_passes(self, tmp_path):
        svg = tmp_path / "ok.svg"
        svg.write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" width="400" height="200">'
            '<rect x="0" y="0" width="400" height="200" fill="#fff" />'
            '<rect x="50" y="50" width="200" height="100" fill="none" '
            'stroke="#81C784" stroke-width="2" stroke-dasharray="8,4" />'
            '<rect x="70" y="70" width="100" height="40" fill="#E8F5E9" stroke="#81C784" />'
            '<text x="120" y="94" text-anchor="middle" font-size="10">OK</text>'
            '</svg>'
        )
        errors = check_child_rect_clips_parent(svg)
        assert not errors

    def test_fixture_detects_clipping(self):
        fixture = FIXTURES_DIR / "svgwrite-child-rect-clips-parent.svg"
        assert fixture.exists()
        errors = check_child_rect_clips_parent(fixture)
        assert len(errors) >= 2, (
            f"Expected at least 2 clipping errors, "
            f"got {len(errors)}: " + "\n".join(errors)
        )
