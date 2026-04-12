from pathlib import Path

import pytest

from diagram_testkit.extractors import detect_format, extract
from diagram_testkit.model import Format

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestDetectFormat:

    def test_detects_graphviz_svg(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs, "No architecture fixture SVGs found"
        assert detect_format(svgs[0]) == Format.GRAPHVIZ

    def test_detects_matplotlib_svg(self):
        svgs = sorted(FIXTURES_DIR.glob("matplotlib-*.svg"))
        assert svgs, "No matplotlib fixture SVGs found"
        assert detect_format(svgs[0]) == Format.MATPLOTLIB

    def test_returns_none_for_unknown_format(self, tmp_path):
        svg = tmp_path / "plain.svg"
        svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')
        assert detect_format(svg) is None


class TestGraphvizExtractor:

    def test_extracts_nodes_as_text_labels(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.texts, "Should have at least one TextLabel"
        assert all(t.id for t in elems.texts)

    def test_extracts_edges_as_arrows(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.arrows, "Should have at least one ArrowPath"

    def test_extracts_cluster_borders_as_shapes(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.shapes, "Should have at least one Shape from cluster borders"

    def test_extracts_clusters_as_containers(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.containers, "Should have at least one Container"

    def test_edge_labels_have_owner(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-arrow-crosses-label*.svg"))
        assert svgs
        elems = extract(svgs[0])
        edge_texts = [t for t in elems.texts if t.owner is not None]
        assert edge_texts, "Edge labels should have owner set"

    def test_source_path_is_set(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.source_path == svgs[0]

    def test_format_override_works(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs
        elems = extract(svgs[0], format=Format.GRAPHVIZ)
        assert elems.texts
