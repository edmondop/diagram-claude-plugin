"""Tests for SVG quality checks.

Critical: every fixture SVG must fail at least one check.
If a fixture passes all checks, the test suite itself is broken.
"""

from pathlib import Path

import pytest

from diagram_testkit import (
    check_cluster_alignment,
    parse_svg,
    run_all_checks,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestFixturesMustFail:

    @pytest.fixture(params=sorted(FIXTURES_DIR.glob("*.svg")))
    def fixture_svg(self, request: pytest.FixtureRequest):
        path = request.param
        return (path.name, parse_svg(path))

    def test_fixture_fails_at_least_one_check(
        self, fixture_svg: tuple[str, ...],
    ) -> None:
        name, svg = fixture_svg
        errors = run_all_checks(svg)
        assert errors, (
            f"Fixture {name} passed ALL checks — either the fixture "
            f"is not actually broken or the checks are too lenient"
        )


class TestClusterAlignment:

    def test_aligned_clusters_pass(self):
        from diagram_testkit.geometry import BBox
        from diagram_testkit.parser import ParsedSVG

        svg = ParsedSVG(
            clusters={
                "a": BBox(100, 0, 200, 50),
                "b": BBox(110, 60, 210, 110),
            },
        )
        errors = check_cluster_alignment(svg, src="a", dst="b")
        assert not errors

    def test_misaligned_clusters_fail(self):
        from diagram_testkit.geometry import BBox
        from diagram_testkit.parser import ParsedSVG

        svg = ParsedSVG(
            clusters={
                "a": BBox(0, 0, 100, 50),
                "b": BBox(500, 60, 600, 110),
            },
        )
        errors = check_cluster_alignment(svg, src="a", dst="b")
        assert errors
        assert "Too far" in errors[0]

    def test_missing_cluster_returns_empty(self):
        from diagram_testkit.parser import ParsedSVG

        svg = ParsedSVG()
        errors = check_cluster_alignment(
            svg, src="nonexistent", dst="also_nonexistent"
        )
        assert not errors
