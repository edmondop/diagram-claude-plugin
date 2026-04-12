import xml.etree.ElementTree as ET
from pathlib import Path

from ..geometry import BBox, bbox_from_path_d, text_bbox
from ..model import ArrowPath, Container, DiagramElements, Shape, TextLabel


def _strip_namespaces(root: ET.Element) -> None:
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]


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
            texts=texts,
            arrows=arrows,
            shapes=shapes,
            containers=containers,
            source_path=svg_path,
        )

    def _extract_clusters(
        self,
        graph_g: ET.Element,
        texts: list[TextLabel],
        shapes: list[Shape],
        containers: list[Container],
    ) -> None:
        for g in graph_g.findall(".//g[@class='cluster']"):
            title = g.find("title")
            if title is None or title.text is None:
                continue
            name = title.text

            path_el = g.find("path")
            if path_el is not None:
                d = path_el.get("d", "")
                bb = bbox_from_path_d(d)
                if bb:
                    containers.append(Container(id=name, bbox=bb))
                    shapes.append(Shape(id=f"{name}_border", bbox=bb, path_d=d))

            text_el = g.find("text")
            if text_el is not None:
                tb = text_bbox(text_el)
                if tb:
                    texts.append(TextLabel(
                        id=f"cluster:{name} '{text_el.text or ''}'",
                        bbox=tb,
                    ))

    def _extract_nodes(
        self,
        graph_g: ET.Element,
        texts: list[TextLabel],
    ) -> None:
        for g in graph_g.findall(".//g[@class='node']"):
            title = g.find("title")
            node_name = title.text if title is not None and title.text else "?"
            text_el = g.find("text")
            if text_el is not None:
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
            title = g.find("title")
            edge_name = title.text if title is not None and title.text else "?"

            for text_el in g.findall("text"):
                tb = text_bbox(text_el)
                if tb:
                    label_text = (text_el.text or "").strip()
                    texts.append(TextLabel(
                        id=f"{edge_name}: '{label_text}'",
                        bbox=tb,
                        owner=edge_name,
                    ))

            path_el = g.find("path")
            if path_el is not None:
                d = path_el.get("d", "")
                if d:
                    arrows.append(ArrowPath(
                        id=edge_name,
                        path_d=d,
                        owner=edge_name,
                    ))
