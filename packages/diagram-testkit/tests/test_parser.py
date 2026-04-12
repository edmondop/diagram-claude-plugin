"""Tests for SVG parsing."""

from pathlib import Path

from diagram_testkit import ParsedSVG, parse_svg

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def test_parse_graphviz_svg_has_structure():
    svgs = list(FIXTURES_DIR.glob("architecture-*.svg"))
    assert svgs, "No architecture fixture SVGs found"
    svg = parse_svg(svgs[0])
    assert svg.source_path == svgs[0]
    has_content = (
        svg.clusters or svg.node_labels or svg.edge_paths
    )
    assert has_content, "Graphviz SVG should have clusters, nodes, or edges"


def test_parse_matplotlib_svg_returns_empty_parsed():
    mpl_svgs = list(FIXTURES_DIR.glob("matplotlib-*.svg"))
    assert mpl_svgs, "No matplotlib fixture SVGs found"
    svg = parse_svg(mpl_svgs[0])
    assert svg.source_path is not None
    assert not svg.clusters
    assert not svg.node_labels
    assert not svg.edge_paths


def test_parse_nonexistent_file_raises():
    import pytest

    with pytest.raises(FileNotFoundError):
        parse_svg(Path("/nonexistent/file.svg"))
