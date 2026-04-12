"""SVG parser — extracts clusters, nodes, edges from Graphviz SVGs."""

import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from pathlib import Path

from .geometry import BBox, bbox_from_path_d, text_bbox


@dataclass
class ParsedSVG:
    clusters: dict[str, BBox] = field(default_factory=dict)
    cluster_labels: dict[str, tuple[str, BBox]] = field(default_factory=dict)
    cluster_border_paths: dict[str, str] = field(default_factory=dict)
    node_labels: list[tuple[str, BBox]] = field(default_factory=list)
    edge_labels: list[tuple[str, str, BBox]] = field(default_factory=list)
    edge_paths: list[tuple[str, str]] = field(default_factory=list)
    source_path: Path | None = None


def parse_svg(svg_path: Path) -> ParsedSVG:
    tree = ET.parse(svg_path)
    root = tree.getroot()

    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    graph_g = root.find(".//g[@id='graph0']")
    if graph_g is None:
        return ParsedSVG(source_path=svg_path)

    clusters: dict[str, BBox] = {}
    cluster_labels: dict[str, tuple[str, BBox]] = {}
    cluster_border_paths: dict[str, str] = {}

    for g in graph_g.findall(".//g[@class='cluster']"):
        title = g.find("title")
        if title is None or title.text is None:
            continue
        name = title.text
        path = g.find("path")
        if path is not None:
            d = path.get("d", "")
            bb = bbox_from_path_d(d)
            if bb:
                clusters[name] = bb
                cluster_border_paths[name] = d
        text_el = g.find("text")
        if text_el is not None:
            tb = text_bbox(text_el)
            if tb:
                cluster_labels[name] = (text_el.text or "", tb)

    node_labels: list[tuple[str, BBox]] = []
    for g in graph_g.findall(".//g[@class='node']"):
        title = g.find("title")
        node_name = title.text if title is not None and title.text else "?"
        text_el = g.find("text")
        if text_el is not None:
            tb = text_bbox(text_el)
            if tb:
                node_labels.append((node_name, tb))

    edge_labels: list[tuple[str, str, BBox]] = []
    edge_paths: list[tuple[str, str]] = []

    for g in graph_g.findall(".//g[@class='edge']"):
        title = g.find("title")
        edge_name = title.text if title is not None and title.text else "?"
        for text_el in g.findall("text"):
            tb = text_bbox(text_el)
            if tb:
                label_text = (text_el.text or "").strip()
                edge_labels.append(
                    (f"{edge_name}: '{label_text}'", edge_name, tb)
                )
        path_el = g.find("path")
        if path_el is not None:
            d = path_el.get("d", "")
            if d:
                edge_paths.append((edge_name, d))

    return ParsedSVG(
        clusters=clusters,
        cluster_labels=cluster_labels,
        cluster_border_paths=cluster_border_paths,
        node_labels=node_labels,
        edge_labels=edge_labels,
        edge_paths=edge_paths,
        source_path=svg_path,
    )
