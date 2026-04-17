"""Tests for SVG quality checks.

Critical: every fixture SVG in FIXTURES_DIR must fail at least one check.
If a fixture passes all checks, the test suite itself is broken.

Passing fixtures (no expected errors) live in PASSING_DIR and are NOT
included in TestFixturesMustFail.
"""

from pathlib import Path

from diagram_testkit.checks import check_arrow_crosses_text
from diagram_testkit.checks import check_child_rect_clips_parent
from diagram_testkit.checks import check_container_alignment
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

import pytest

FIXTURES_DIR = Path(__file__).parent / "fixtures"
PASSING_DIR = FIXTURES_DIR / "passing"


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

    def test_text_fitting_inside_rect_passes(self):
        errors = check_text_overflows_rect(PASSING_DIR / "text-fits-inside-rect.svg")
        assert not errors

    def test_text_overflowing_rect_detected(self):
        errors = check_text_overflows_rect(FIXTURES_DIR / "inline-text-overflows-rect.svg")
        assert errors
        assert "overflows" in errors[0]

    def test_text_outside_rect_ignored(self):
        errors = check_text_overflows_rect(PASSING_DIR / "text-outside-rect.svg")
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

    def test_line_through_text_detected(self):
        errors = check_line_crosses_text(FIXTURES_DIR / "inline-line-crosses-text.svg")
        assert errors
        assert "Label" in errors[0]

    def test_line_far_from_text_passes(self):
        errors = check_line_crosses_text(PASSING_DIR / "line-far-from-text.svg")
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

    def test_bezier_through_text_detected(self):
        errors = check_path_crosses_text(FIXTURES_DIR / "inline-path-crosses-text.svg")
        assert errors
        assert "Label" in errors[0]

    def test_bezier_through_rect_detected(self):
        errors = check_path_crosses_text(FIXTURES_DIR / "inline-path-crosses-rect.svg")
        rect_errors = [e for e in errors if "rect" in e.lower()]
        assert rect_errors, f"Expected path-crosses-rect error, got: {errors}"

    def test_path_not_crossing_passes(self):
        errors = check_path_crosses_text(PASSING_DIR / "path-not-crossing.svg")
        assert not errors

    def test_marker_paths_in_defs_skipped(self):
        errors = check_path_crosses_text(PASSING_DIR / "marker-paths-in-defs.svg")
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

    def test_text_inside_viewport_passes(self):
        errors = check_text_outside_viewport(PASSING_DIR / "text-inside-viewport.svg")
        assert not errors

    def test_text_clipped_right_detected(self):
        errors = check_text_outside_viewport(FIXTURES_DIR / "inline-viewport-clip-right.svg")
        assert errors
        assert "right" in errors[0]

    def test_text_clipped_left_detected(self):
        errors = check_text_outside_viewport(FIXTURES_DIR / "inline-viewport-clip-left.svg")
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

    def test_endpoint_inside_rect_detected(self):
        errors = check_path_endpoint_inside_rect(FIXTURES_DIR / "inline-endpoint-inside-rect.svg")
        assert errors
        assert "inside rect" in errors[0]

    def test_endpoint_on_border_passes(self):
        errors = check_path_endpoint_inside_rect(PASSING_DIR / "endpoint-on-border.svg")
        assert not errors

    def test_marker_paths_skipped(self):
        errors = check_path_endpoint_inside_rect(PASSING_DIR / "marker-paths-skipped.svg")
        assert not errors

    def test_fixture_detects_overflow(self):
        fixture = FIXTURES_DIR / "svgwrite-path-endpoint-inside-rect.svg"
        assert fixture.exists()
        errors = check_path_endpoint_inside_rect(fixture)
        assert errors, "Fixture should detect arrow endpoint inside rect"
        assert any("inside rect" in e for e in errors)


class TestTextOnClusterBorder:

    def test_text_on_dashed_border_detected(self):
        errors = check_text_on_cluster_border(FIXTURES_DIR / "inline-text-on-cluster-border.svg")
        assert errors
        assert "cluster border" in errors[0]

    def test_text_far_from_border_passes(self):
        errors = check_text_on_cluster_border(PASSING_DIR / "text-far-from-cluster-border.svg")
        assert not errors

    def test_cluster_title_skipped(self):
        errors = check_text_on_cluster_border(PASSING_DIR / "cluster-title-on-border.svg")
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

    def test_clipping_child_detected(self):
        errors = check_child_rect_clips_parent(FIXTURES_DIR / "inline-child-clips-parent.svg")
        assert errors
        assert "clips parent" in errors[0]
        assert "left" in errors[0]

    def test_well_placed_child_passes(self):
        errors = check_child_rect_clips_parent(PASSING_DIR / "child-rect-well-placed.svg")
        assert not errors

    def test_fixture_detects_clipping(self):
        fixture = FIXTURES_DIR / "svgwrite-child-rect-clips-parent.svg"
        assert fixture.exists()
        errors = check_child_rect_clips_parent(fixture)
        assert len(errors) >= 2, (
            f"Expected at least 2 clipping errors, "
            f"got {len(errors)}: " + "\n".join(errors)
        )
