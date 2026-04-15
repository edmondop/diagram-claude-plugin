import xml.etree.ElementTree as ET
from pathlib import Path

from diagram_testkit.extractors.base import DiagramExtractor
from diagram_testkit.extractors.excalidraw import ExcalidrawExtractor
from diagram_testkit.extractors.graphviz import GraphvizExtractor
from diagram_testkit.extractors.matplotlib import MatplotlibExtractor
from diagram_testkit.extractors.svgwrite import SvgwriteExtractor
from diagram_testkit.model import DiagramElements
from diagram_testkit.model import Format

EXTRACTORS: dict[Format, DiagramExtractor] = {
    Format.GRAPHVIZ: GraphvizExtractor(),
    Format.MATPLOTLIB: MatplotlibExtractor(),
    Format.EXCALIDRAW: ExcalidrawExtractor(),
    Format.SVGWRITE: SvgwriteExtractor(),
}

_FORMAT_MARKERS: list[tuple[str, Format]] = [
    (".//*[@id='graph0']", Format.GRAPHVIZ),
    (".//*[@id='axes_1']", Format.MATPLOTLIB),
    (".//*[@data-id]", Format.EXCALIDRAW),
]


def _strip_namespaces(root: ET.Element) -> None:
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]


def _is_svgwrite(root: ET.Element) -> bool:
    """Detect svgwrite SVGs: flat structure with top-level <text> and <rect>."""
    has_text = root.find(".//text") is not None
    has_rect = root.find(".//rect") is not None
    return has_text and has_rect


def detect_format(svg_path: Path) -> Format | None:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    _strip_namespaces(root)
    for xpath, fmt in _FORMAT_MARKERS:
        if root.find(xpath) is not None:
            return fmt
    if _is_svgwrite(root):
        return Format.SVGWRITE
    return None


def extract(
    svg_path: Path,
    *,
    format: Format | None = None,
) -> DiagramElements:
    if format is None:
        format = detect_format(svg_path)
    if format is None:
        return DiagramElements(source_path=svg_path)
    extractor = EXTRACTORS.get(format)
    if extractor is None:
        return DiagramElements(source_path=svg_path)
    return extractor.extract(svg_path)
