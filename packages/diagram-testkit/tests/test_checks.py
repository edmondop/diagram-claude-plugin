"""Tests for SVG quality checks.

Critical: every fixture SVG must fail at least one check.
If a fixture passes all checks, the test suite itself is broken.
"""

from pathlib import Path

import pytest

from diagram_testkit.checks import check_arrow_crosses_text
from diagram_testkit.checks import check_container_alignment
from diagram_testkit.checks import check_text_overlaps_text
from diagram_testkit.checks import run_all_checks
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
        errors = run_all_checks(elems)
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
