# /// script
# requires-python = ">=3.10"
# dependencies = ["pytest", "diagram-testkit"]
# ///
"""
Tests for the generated architecture diagram — uses diagram-testkit.

Run: uv run pytest test_svg_quality.py -v
"""

from pathlib import Path

import pytest

from diagram_testkit import (
    check_cluster_alignment,
    parse_svg,
    run_all_checks,
)

EXAMPLES_DIR = Path(__file__).parent
OUTPUT_DIR = EXAMPLES_DIR / "output"


class TestOutputDiagram:
    """Tests for the generated architecture diagram."""

    @pytest.fixture
    def svg(self):
        svg_path = OUTPUT_DIR / "architecture-graphviz.svg"
        if not svg_path.exists():
            pytest.skip("Run architecture-graphviz.py first")
        return parse_svg(svg_path)

    def test_no_quality_errors(self, svg) -> None:
        errors = run_all_checks(svg)
        assert not errors, "\n".join(errors)

    def test_data_layer_centered_below_backend(self, svg) -> None:
        errors = check_cluster_alignment(
            svg, src="cluster_backend", dst="cluster_data"
        )
        assert not errors, "\n".join(errors)
