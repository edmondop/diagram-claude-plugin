"""SVG quality checks — each returns a list of error strings."""

import re
import xml.etree.ElementTree as ET

from .geometry import BBox, bbox_from_path_d, path_to_linestring
from .parser import ParsedSVG

ARROW_TEXT_PADDING = 2.0
BORDER_STROKE_WIDTH = 2.0
MAX_CENTER_OFFSET_RATIO = 0.7
MIN_EDGE_LABEL_DISTANCE = 8.0
GLYPH_ADVANCE_ESTIMATE = 65.0


def _collect_all_text(
    svg: ParsedSVG,
) -> list[tuple[str, str | None, BBox]]:
    all_text: list[tuple[str, str | None, BBox]] = []
    for name, (text, bb) in svg.cluster_labels.items():
        all_text.append((f"cluster label '{text}'", None, bb))
    for display_name, edge_id, bb in svg.edge_labels:
        all_text.append((f"edge label {display_name}", edge_id, bb))
    for node_name, bb in svg.node_labels:
        all_text.append((f"node '{node_name}'", None, bb))
    return all_text


def check_arrow_crosses_text(
    svg: ParsedSVG,
    *,
    padding: float = ARROW_TEXT_PADDING,
) -> list[str]:
    errors: list[str] = []
    all_text = _collect_all_text(svg)
    for edge_name, d in svg.edge_paths:
        arrow_line = path_to_linestring(d)
        for text_name, owner_edge, text_bb in all_text:
            if owner_edge == edge_name:
                continue
            text_poly = text_bb.to_shapely().buffer(padding)
            if arrow_line.intersects(text_poly):
                errors.append(f"Arrow {edge_name} crosses {text_name}")
    return errors


def check_text_crosses_border(
    svg: ParsedSVG,
    *,
    stroke_width: float = BORDER_STROKE_WIDTH,
) -> list[str]:
    errors: list[str] = []
    all_text = _collect_all_text(svg)
    for cluster_name, d in svg.cluster_border_paths.items():
        border_line = path_to_linestring(d)
        thick_border = border_line.buffer(stroke_width / 2)
        for text_name, owner_cluster, text_bb in all_text:
            if owner_cluster == cluster_name:
                continue
            text_poly = text_bb.to_shapely()
            if text_poly.intersects(thick_border):
                errors.append(
                    f"{text_name} crosses {cluster_name} border"
                )
    return errors


def check_cluster_alignment(
    svg: ParsedSVG,
    *,
    src: str,
    dst: str,
    max_offset_ratio: float = MAX_CENTER_OFFSET_RATIO,
) -> list[str]:
    errors: list[str] = []
    src_bb = svg.clusters.get(src)
    dst_bb = svg.clusters.get(dst)
    if src_bb is None or dst_bb is None:
        return errors
    offset = abs(dst_bb.cx - src_bb.cx)
    max_offset = max(src_bb.width, dst_bb.width) * max_offset_ratio
    if offset > max_offset:
        direction = "right" if dst_bb.cx > src_bb.cx else "left"
        errors.append(
            f"Cluster '{dst}' center (x={dst_bb.cx:.0f}) is "
            f"{offset:.0f}px from '{src}' center "
            f"(x={src_bb.cx:.0f}) — max {max_offset:.0f}px. "
            f"Too far to the {direction}"
        )
    return errors


def check_label_overlaps(svg: ParsedSVG) -> list[str]:
    errors: list[str] = []
    all_labels: list[tuple[str, BBox]] = []
    all_labels.extend(
        (f"cluster:{name} '{text}'", bb)
        for name, (text, bb) in svg.cluster_labels.items()
    )
    all_labels.extend(
        (display_name, bb) for display_name, _, bb in svg.edge_labels
    )
    all_labels.extend(svg.node_labels)
    for i, (name_a, bb_a) in enumerate(all_labels):
        for name_b, bb_b in all_labels[i + 1 :]:
            if bb_a.overlaps(bb_b):
                errors.append(f"Labels overlap: {name_a} vs {name_b}")
    return errors


def check_edge_label_distance(
    svg: ParsedSVG,
    *,
    min_distance: float = MIN_EDGE_LABEL_DISTANCE,
) -> list[str]:
    errors: list[str] = []
    edge_path_map: dict[str, str] = {}
    for edge_name, d in svg.edge_paths:
        edge_path_map[edge_name] = d
    for display_name, edge_id, label_bb in svg.edge_labels:
        d = edge_path_map.get(edge_id)
        if d is None:
            continue
        edge_line = path_to_linestring(d)
        label_poly = label_bb.to_shapely()
        dist = edge_line.distance(label_poly)
        if dist < min_distance:
            errors.append(
                f"Edge label {display_name} is {dist:.1f}px from its "
                f"edge (minimum {min_distance:.0f}px)"
            )
    return errors


def check_matplotlib_annotation_overflow(svg: ParsedSVG) -> list[str]:
    if svg.source_path is None:
        return []

    tree = ET.parse(svg.source_path)
    root = tree.getroot()
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    axes_g = root.find(".//*[@id='axes_1']")
    if axes_g is None:
        return []

    patch_2 = axes_g.find("*[@id='patch_2']")
    if patch_2 is None:
        return []
    bg_path = patch_2.find("path")
    if bg_path is None:
        return []
    axes_bb = bbox_from_path_d(bg_path.get("d", ""))
    if axes_bb is None:
        return []

    errors: list[str] = []
    for g in axes_g:
        g_id = g.get("id", "")
        if not g_id.startswith("text_"):
            continue
        inner_g = g.find("g")
        if inner_g is None:
            continue
        transform = inner_g.get("transform", "")
        t_match = re.search(
            r"translate\(([\d.e+-]+)[\s,]+([\d.e+-]+)\)", transform
        )
        s_match = re.search(
            r"scale\(([\d.e+-]+)[\s,]+([\d.e+-]+)\)", transform
        )
        if not t_match or not s_match:
            continue
        tx = float(t_match.group(1))
        ty = float(t_match.group(2))
        sx = abs(float(s_match.group(1)))
        if ty < axes_bb.y_min or ty > axes_bb.y_max:
            continue
        max_use_x = 0.0
        for use_el in inner_g.findall("use"):
            use_transform = use_el.get("transform", "")
            ut_match = re.search(
                r"translate\(([\d.e+-]+)", use_transform
            )
            if ut_match:
                max_use_x = max(max_use_x, float(ut_match.group(1)))
        text_right = tx + (max_use_x + GLYPH_ADVANCE_ESTIMATE) * sx
        if text_right > axes_bb.x_max:
            overflow = text_right - axes_bb.x_max
            errors.append(
                f"Annotation {g_id} overflows axes area by "
                f"{overflow:.1f}px on the right (text ends at "
                f"x={text_right:.0f}, axes right edge at "
                f"x={axes_bb.x_max:.0f})"
            )
    return errors


def run_all_checks(svg: ParsedSVG) -> list[str]:
    errors: list[str] = []
    errors.extend(check_arrow_crosses_text(svg))
    errors.extend(check_text_crosses_border(svg))
    errors.extend(check_label_overlaps(svg))
    errors.extend(check_edge_label_distance(svg))
    errors.extend(check_matplotlib_annotation_overflow(svg))
    return errors
