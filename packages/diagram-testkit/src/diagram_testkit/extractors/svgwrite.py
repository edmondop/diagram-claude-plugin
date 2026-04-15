import xml.etree.ElementTree as ET
from pathlib import Path

from diagram_testkit.geometry import BBox
from diagram_testkit.geometry import text_bbox
from diagram_testkit.model import DiagramElements
from diagram_testkit.model import TextLabel


def _strip_namespaces(root: ET.Element) -> None:
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]


def _rect_bbox(elem: ET.Element) -> BBox | None:
    x = elem.get("x")
    y = elem.get("y")
    w = elem.get("width")
    h = elem.get("height")
    if any(v is None for v in (x, y, w, h)):
        return None
    return BBox(float(x), float(y), float(x) + float(w), float(y) + float(h))


class SvgwriteExtractor:

    def extract(self, svg_path: Path) -> DiagramElements:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        _strip_namespaces(root)

        texts: list[TextLabel] = []

        for text_el in root.iter("text"):
            content = text_el.text or ""
            if not content.strip():
                continue
            tb = text_bbox(text_el)
            if tb:
                texts.append(TextLabel(
                    id=f"'{content.strip()}'",
                    bbox=tb,
                ))

        return DiagramElements(texts=texts, source_path=svg_path)
