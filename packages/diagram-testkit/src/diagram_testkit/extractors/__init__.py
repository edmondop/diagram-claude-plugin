import xml.etree.ElementTree as ET
from pathlib import Path

from ..model import DiagramElements, Format
from .base import DiagramExtractor
from .graphviz import GraphvizExtractor
from .matplotlib import MatplotlibExtractor

EXTRACTORS: dict[Format, DiagramExtractor] = {
    Format.GRAPHVIZ: GraphvizExtractor(),
    Format.MATPLOTLIB: MatplotlibExtractor(),
}


def detect_format(svg_path: Path) -> Format | None:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    if root.find(".//*[@id='graph0']") is not None:
        return Format.GRAPHVIZ
    if root.find(".//*[@id='axes_1']") is not None:
        return Format.MATPLOTLIB
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
