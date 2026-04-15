"""Format-agnostic SVG quality checks operating on DiagramElements."""

import xml.etree.ElementTree as ET
from pathlib import Path

from diagram_testkit.geometry import BBox
from diagram_testkit.geometry import path_to_linestring
from diagram_testkit.geometry import text_bbox
from diagram_testkit.model import DiagramElements

ARROW_TEXT_PADDING = 2.0
BORDER_STROKE_WIDTH = 2.0
MAX_CENTER_OFFSET_RATIO = 0.7
TEXT_OVERFLOW_MARGIN = 4.0  # px tolerance for text-in-rect checks


def check_arrow_crosses_text(
    elems: DiagramElements,
    *,
    padding: float = ARROW_TEXT_PADDING,
) -> list[str]:
    errors: list[str] = []
    for arrow in elems.arrows:
        arrow_line = path_to_linestring(arrow.path_d)
        for text in elems.texts:
            if arrow.owner and text.owner == arrow.owner:
                continue
            text_poly = text.bbox.to_shapely().buffer(padding)
            if arrow_line.intersects(text_poly):
                errors.append(f"Arrow {arrow.id} crosses {text.id}")
    return errors


def check_text_overlaps_text(
    elems: DiagramElements,
) -> list[str]:
    errors: list[str] = []
    texts = elems.texts
    for i, a in enumerate(texts):
        for b in texts[i + 1 :]:
            if a.owner and a.owner == b.owner:
                continue
            if a.bbox.overlaps(b.bbox):
                errors.append(f"Text overlap: {a.id} vs {b.id}")
    return errors


def check_text_crosses_shape(
    elems: DiagramElements,
    *,
    stroke_width: float = BORDER_STROKE_WIDTH,
) -> list[str]:
    errors: list[str] = []
    for text in elems.texts:
        text_poly = text.bbox.to_shapely()
        for shape in elems.shapes:
            border_line = path_to_linestring(shape.path_d)
            thick_border = border_line.buffer(stroke_width / 2)
            if text_poly.intersects(thick_border):
                errors.append(f"{text.id} crosses {shape.id} border")
    return errors


def check_text_overlaps_shape(
    elems: DiagramElements,
    *,
    stroke_width: float = BORDER_STROKE_WIDTH,
) -> list[str]:
    errors: list[str] = []
    for text in elems.texts:
        text_poly = text.bbox.to_shapely()
        for shape in elems.shapes:
            shape_poly = shape.bbox.to_shapely()
            shape_border = shape_poly.boundary.buffer(stroke_width / 2)
            if text_poly.intersects(shape_border):
                errors.append(f"{text.id} overlaps {shape.id} border")
    return errors


def check_annotation_overflow(
    elems: DiagramElements,
) -> list[str]:
    errors: list[str] = []
    for container in elems.containers:
        for text in elems.texts:
            bb = text.bbox
            if bb.y_min < container.bbox.y_min or bb.y_max > container.bbox.y_max:
                continue
            if bb.x_max > container.bbox.x_max:
                overflow = bb.x_max - container.bbox.x_max
                errors.append(
                    f"Annotation {text.id} overflows container {container.id} "
                    f"by {overflow:.1f}px on the right"
                )
    return errors


def check_container_alignment(
    elems: DiagramElements,
    *,
    src: str,
    dst: str,
    max_offset_ratio: float = MAX_CENTER_OFFSET_RATIO,
) -> list[str]:
    containers_by_id = {c.id: c for c in elems.containers}
    src_c = containers_by_id.get(src)
    dst_c = containers_by_id.get(dst)
    if src_c is None or dst_c is None:
        return []
    offset = abs(dst_c.bbox.cx - src_c.bbox.cx)
    max_offset = max(src_c.bbox.width, dst_c.bbox.width) * max_offset_ratio
    if offset > max_offset:
        direction = "right" if dst_c.bbox.cx > src_c.bbox.cx else "left"
        return [
            f"Container '{dst}' center (x={dst_c.bbox.cx:.0f}) is "
            f"{offset:.0f}px from '{src}' center "
            f"(x={src_c.bbox.cx:.0f}) - max {max_offset:.0f}px. "
            f"Too far to the {direction}"
        ]
    return []


def check_text_overflows_rect(
    svg_path: Path,
    *,
    margin: float = TEXT_OVERFLOW_MARGIN,
) -> list[str]:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    rects: list[BBox] = []
    for rect_el in root.iter("rect"):
        x = rect_el.get("x")
        y = rect_el.get("y")
        w = rect_el.get("width")
        h = rect_el.get("height")
        if any(v is None for v in (x, y, w, h)):
            continue
        rects.append(BBox(
            float(x), float(y), float(x) + float(w), float(y) + float(h),
        ))

    errors: list[str] = []
    for text_el in root.iter("text"):
        content = text_el.text or ""
        if not content.strip():
            continue
        tb = text_bbox(text_el)
        if tb is None:
            continue

        text_cx = tb.cx
        text_cy = (tb.y_min + tb.y_max) / 2

        # Find the smallest containing rect (skip full-canvas backgrounds)
        best_rect: BBox | None = None
        best_area = float("inf")
        for rect_bb in rects:
            if (
                rect_bb.x_min <= text_cx <= rect_bb.x_max
                and rect_bb.y_min <= text_cy <= rect_bb.y_max
            ):
                area = rect_bb.width * (rect_bb.y_max - rect_bb.y_min)
                if area < best_area:
                    best_area = area
                    best_rect = rect_bb

        if best_rect is not None:
            overflow = tb.width - (best_rect.width - margin)
            if overflow > 0:
                errors.append(
                    f"Text '{content.strip()}' overflows its rect "
                    f"by {overflow:.0f}px "
                    f"(text width: {tb.width:.0f}px, "
                    f"rect width: {best_rect.width:.0f}px)"
                )

    return errors


def run_all_checks(elems: DiagramElements) -> list[str]:
    errors: list[str] = []
    errors.extend(check_arrow_crosses_text(elems))
    errors.extend(check_text_overlaps_text(elems))
    errors.extend(check_text_crosses_shape(elems))
    errors.extend(check_text_overlaps_shape(elems))
    errors.extend(check_annotation_overflow(elems))
    return errors


def run_all_checks_with_file(
    elems: DiagramElements,
    svg_path: Path | None = None,
) -> list[str]:
    errors = run_all_checks(elems)
    if svg_path is not None:
        errors.extend(check_text_overflows_rect(svg_path))
    return errors
