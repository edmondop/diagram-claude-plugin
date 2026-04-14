import xml.etree.ElementTree as ET
from pathlib import Path

from diagram_testkit.geometry import bbox_from_path_d
from diagram_testkit.geometry import text_bbox
from diagram_testkit.model import ArrowPath
from diagram_testkit.model import Container
from diagram_testkit.model import DiagramElements
from diagram_testkit.model import Shape
from diagram_testkit.model import TextLabel


def _strip_namespaces(root: ET.Element) -> None:
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]


def _title_text(g: ET.Element) -> str | None:
    title = g.find("title")
    if title is None or title.text is None:
        return None
    return title.text


def _cluster_geometry(
    g: ET.Element,
    name: str,
    shapes: list[Shape],
    containers: list[Container],
) -> None:
    path_el = g.find("path")
    if path_el is None:
        return
    d = path_el.get("d", "")
    bb = bbox_from_path_d(d)
    if bb:
        containers.append(Container(id=name, bbox=bb))
        shapes.append(Shape(id=f"{name}_border", bbox=bb, path_d=d))


def _cluster_label(g: ET.Element, name: str, texts: list[TextLabel]) -> None:
    text_el = g.find("text")
    if text_el is None:
        return
    tb = text_bbox(text_el)
    if tb:
        texts.append(TextLabel(id=f"cluster:{name} '{text_el.text or ''}'", bbox=tb))


class GraphvizExtractor:

    def extract(self, svg_path: Path) -> DiagramElements:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        _strip_namespaces(root)

        graph_g = root.find(".//g[@id='graph0']")
        if graph_g is None:
            return DiagramElements(source_path=svg_path)

        texts: list[TextLabel] = []
        arrows: list[ArrowPath] = []
        shapes: list[Shape] = []
        containers: list[Container] = []

        self._extract_clusters(graph_g, texts, shapes, containers)
        self._extract_nodes(graph_g, texts)
        self._extract_edges(graph_g, texts, arrows)

        return DiagramElements(
            texts=texts, arrows=arrows, shapes=shapes,
            containers=containers, source_path=svg_path,
        )

    def _extract_clusters(
        self,
        graph_g: ET.Element,
        texts: list[TextLabel],
        shapes: list[Shape],
        containers: list[Container],
    ) -> None:
        for g in graph_g.findall(".//g[@class='cluster']"):
            name = _title_text(g)
            if name is None:
                continue
            _cluster_geometry(g, name, shapes, containers)
            _cluster_label(g, name, texts)

    def _extract_nodes(
        self,
        graph_g: ET.Element,
        texts: list[TextLabel],
    ) -> None:
        for g in graph_g.findall(".//g[@class='node']"):
            node_name = _title_text(g) or "?"
            text_el = g.find("text")
            if text_el is None:
                continue
            tb = text_bbox(text_el)
            if tb:
                texts.append(TextLabel(id=node_name, bbox=tb))

    def _extract_edges(
        self,
        graph_g: ET.Element,
        texts: list[TextLabel],
        arrows: list[ArrowPath],
    ) -> None:
        for g in graph_g.findall(".//g[@class='edge']"):
            edge_name = _title_text(g) or "?"
            self._extract_edge_labels(g, edge_name, texts)
            self._extract_edge_path(g, edge_name, arrows)

    def _extract_edge_labels(
        self,
        g: ET.Element,
        edge_name: str,
        texts: list[TextLabel],
    ) -> None:
        for text_el in g.findall("text"):
            tb = text_bbox(text_el)
            if tb:
                label_text = (text_el.text or "").strip()
                texts.append(TextLabel(
                    id=f"{edge_name}: '{label_text}'", bbox=tb, owner=edge_name,
                ))

    def _extract_edge_path(
        self,
        g: ET.Element,
        edge_name: str,
        arrows: list[ArrowPath],
    ) -> None:
        path_el = g.find("path")
        if path_el is None:
            return
        d = path_el.get("d", "")
        if d:
            arrows.append(ArrowPath(id=edge_name, path_d=d, owner=edge_name))
