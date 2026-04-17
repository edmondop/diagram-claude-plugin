from pathlib import Path

from diagram_testkit.extractors import detect_format
from diagram_testkit.extractors import extract
from diagram_testkit.model import Format

FIXTURES_DIR = Path(__file__).parent / "fixtures"
PASSING_DIR = FIXTURES_DIR / "passing"


class TestDetectFormat:

    def test_detects_graphviz_svg(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs, "No architecture fixture SVGs found"
        assert detect_format(svgs[0]) == Format.GRAPHVIZ

    def test_detects_matplotlib_svg(self):
        svgs = sorted(FIXTURES_DIR.glob("matplotlib-*.svg"))
        assert svgs, "No matplotlib fixture SVGs found"
        assert detect_format(svgs[0]) == Format.MATPLOTLIB

    def test_returns_none_for_unknown_format(self):
        assert detect_format(PASSING_DIR / "plain-unknown-format.svg") is None


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


class TestMatplotlibExtractor:

    def test_extracts_text_labels(self):
        svgs = sorted(FIXTURES_DIR.glob("matplotlib-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.texts, "Should have at least one TextLabel"

    def test_extracts_arrow_paths(self):
        svgs = sorted(FIXTURES_DIR.glob("matplotlib-arrow-crosses-text.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.arrows, "Should have at least one ArrowPath"

    def test_extracts_shapes(self):
        svgs = sorted(FIXTURES_DIR.glob("matplotlib-text-overlaps-shape.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.shapes, "Should have at least one Shape"

    def test_extracts_axes_container(self):
        svgs = sorted(FIXTURES_DIR.glob("matplotlib-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.containers, "Should have axes Container"

    def test_axis_off_skips_colored_patch_2_as_container(self):
        fixture = PASSING_DIR / "matplotlib-axis-off-colored-patch.svg"
        elems = extract(fixture, format=Format.MATPLOTLIB)
        assert not elems.containers, (
            "Colored patch_2 (user content, not axes background) "
            "should not be treated as a container"
        )

    def test_source_path_is_set(self):
        svgs = sorted(FIXTURES_DIR.glob("matplotlib-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.source_path == svgs[0]


class TestSvgwriteExtractor:

    def test_detects_svgwrite_format(self):
        svgs = sorted(FIXTURES_DIR.glob("svgwrite-*.svg"))
        assert svgs, "No svgwrite fixture SVGs found"
        assert detect_format(svgs[0]) == Format.SVGWRITE

    def test_extracts_text_labels(self):
        svgs = sorted(FIXTURES_DIR.glob("svgwrite-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.texts, "Should have at least one TextLabel"

    def test_source_path_is_set(self):
        svgs = sorted(FIXTURES_DIR.glob("svgwrite-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.source_path == svgs[0]

    def test_extracts_correct_text_count(self):
        svgs = sorted(FIXTURES_DIR.glob("svgwrite-text-overflows-rect.svg"))
        assert svgs
        elems = extract(svgs[0])
        text_ids = [t.id for t in elems.texts]
        assert len(text_ids) >= 8, (
            f"Expected at least 8 text labels, got {len(text_ids)}"
        )


class TestExcalidrawExtractor:

    def test_unknown_svg_returns_empty_elements(self):
        fixture = PASSING_DIR / "plain-unknown-format.svg"
        elems = extract(fixture)
        assert not elems.texts
        assert not elems.arrows
        assert not elems.shapes
        assert not elems.containers
        assert elems.source_path == fixture
