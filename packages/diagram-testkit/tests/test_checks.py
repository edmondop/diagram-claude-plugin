"""Tests for SVG quality checks.

Critical: every fixture SVG must fail at least one check.
If a fixture passes all checks, the test suite itself is broken.
"""

from pathlib import Path

import pytest

from diagram_testkit.checks import check_arrow_crosses_text
from diagram_testkit.checks import check_container_alignment
from diagram_testkit.checks import check_line_crosses_text
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
            f"Expected at least 2 overlapping label pairs (VaR labels + z-values), "
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
