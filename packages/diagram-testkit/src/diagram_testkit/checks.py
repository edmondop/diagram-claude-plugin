"""Format-agnostic SVG quality checks operating on DiagramElements."""

import xml.etree.ElementTree as ET
from pathlib import Path

from shapely.geometry import LineString

from svgpathtools import parse_path

from diagram_testkit.geometry import BBox
from diagram_testkit.geometry import path_to_linestring
from diagram_testkit.geometry import text_bbox
from diagram_testkit.model import DiagramElements

ARROW_TEXT_PADDING = 2.0
LINE_TEXT_PADDING = 2.0
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


def check_line_crosses_text(
    svg_path: Path,
    *,
    padding: float = LINE_TEXT_PADDING,
) -> list[str]:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    lines: list[LineString] = []
    for line_el in root.iter("line"):
        coords = (
            line_el.get("x1"), line_el.get("y1"),
            line_el.get("x2"), line_el.get("y2"),
        )
        if any(v is None for v in coords):
            continue
        x1, y1, x2, y2 = (float(v) for v in coords)
        lines.append(LineString([(x1, y1), (x2, y2)]))

    errors: list[str] = []
    for text_el in root.iter("text"):
        content = text_el.text or ""
        if not content.strip():
            continue
        tb = text_bbox(text_el)
        if tb is None:
            continue
        text_poly = tb.to_shapely().buffer(padding)
        for line in lines:
            if line.intersects(text_poly):
                errors.append(
                    f"Line crosses text '{content.strip()}'"
                )
                break
    return errors


def check_path_crosses_text(
    svg_path: Path,
    *,
    padding: float = LINE_TEXT_PADDING,
) -> list[str]:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    parent_map = {child: parent for parent in root.iter() for child in parent}

    text_labels: list[tuple[str, BBox]] = []
    for text_el in root.iter("text"):
        content = text_el.text or ""
        if not content.strip():
            continue
        tb = text_bbox(text_el)
        if tb is not None:
            text_labels.append((content.strip(), tb))

    # Collect solid rects (skip dashed cluster borders and canvas backgrounds)
    rect_boxes: list[tuple[BBox, list[str]]] = []
    for rect_el in root.iter("rect"):
        if rect_el.get("stroke-dasharray"):
            continue
        rb = _parse_rect_bbox(rect_el)
        if rb is None:
            continue
        contained: list[str] = []
        for label, tb in text_labels:
            if (rb.x_min <= tb.cx <= rb.x_max
                    and rb.y_min <= (tb.y_min + tb.y_max) / 2 <= rb.y_max):
                contained.append(label)
        if contained:
            rect_boxes.append((rb, contained))

    errors: list[str] = []
    for path_el in root.iter("path"):
        d = path_el.get("d", "")
        if not d:
            continue
        if _is_inside_defs(path_el, parent_map):
            continue
        try:
            parsed = parse_path(d)
            line = path_to_linestring(d)
        except Exception:
            continue

        start_pt = parsed.point(0)
        end_pt = parsed.point(1)
        start_x, start_y = start_pt.real, start_pt.imag
        end_x, end_y = end_pt.real, end_pt.imag

        for label, tb in text_labels:
            if _point_in_bbox(start_x, start_y, tb) or _point_in_bbox(end_x, end_y, tb):
                continue
            text_poly = tb.to_shapely().buffer(padding)
            if line.intersects(text_poly):
                errors.append(f"Path crosses text '{label}'")

        for rb, contained_labels in rect_boxes:
            if _point_in_bbox(start_x, start_y, rb) or _point_in_bbox(end_x, end_y, rb):
                continue
            rect_poly = rb.to_shapely()
            if line.intersects(rect_poly):
                label_desc = contained_labels[0] if contained_labels else "unlabeled"
                errors.append(f"Path crosses rect '{label_desc}'")

    return errors


def _parse_rect_bbox(
    rect_el: ET.Element,
    *,
    max_area: float = 500_000,
) -> BBox | None:
    x = rect_el.get("x")
    y = rect_el.get("y")
    w = rect_el.get("width")
    h = rect_el.get("height")
    if any(v is None for v in (x, y, w, h)):
        return None
    fx, fy, fw, fh = float(x), float(y), float(w), float(h)  # type: ignore[arg-type]
    if fw * fh > max_area:
        return None
    return BBox(fx, fy, fx + fw, fy + fh)


def _is_inside_defs(
    elem: ET.Element,
    parent_map: dict[ET.Element, ET.Element],
) -> bool:
    current = elem
    for _ in range(10):
        parent = parent_map.get(current)
        if parent is None:
            return False
        if parent.tag in ("defs", "marker"):
            return True
        current = parent
    return False


def _point_in_bbox(x: float, y: float, bb: BBox) -> bool:
    return bb.x_min <= x <= bb.x_max and bb.y_min <= y <= bb.y_max


PATH_ENDPOINT_INSET = 4.0  # px — endpoint must be this far inside to count
CLUSTER_BORDER_TEXT_PADDING = 3.0  # px buffer around dashed border
SOLID_BORDER_TEXT_PADDING = 3.0  # px buffer around solid border
CHILD_RECT_MIN_MARGIN = 2.0  # px minimum gap between child and parent rect


def check_path_endpoint_inside_rect(
    svg_path: Path,
    *,
    inset: float = PATH_ENDPOINT_INSET,
) -> list[str]:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    parent_map = {child: parent for parent in root.iter() for child in parent}

    text_labels: list[tuple[str, BBox]] = []
    for text_el in root.iter("text"):
        content = text_el.text or ""
        if not content.strip():
            continue
        tb = text_bbox(text_el)
        if tb is not None:
            text_labels.append((content.strip(), tb))

    solid_rects: list[tuple[BBox, str]] = []
    for rect_el in root.iter("rect"):
        if rect_el.get("stroke-dasharray"):
            continue
        rb = _parse_rect_bbox(rect_el, max_area=50_000)
        if rb is None:
            continue
        label = ""
        for name, tb in text_labels:
            if (rb.x_min <= tb.cx <= rb.x_max
                    and rb.y_min <= (tb.y_min + tb.y_max) / 2 <= rb.y_max):
                label = name
                break
        solid_rects.append((rb, label))

    errors: list[str] = []
    for path_el in root.iter("path"):
        d = path_el.get("d", "")
        if not d:
            continue
        if _is_inside_defs(path_el, parent_map):
            continue
        try:
            parsed = parse_path(d)
        except Exception:
            continue

        for t_val in (0.0, 1.0):
            pt = parsed.point(t_val)
            px, py = pt.real, pt.imag
            for rb, label in solid_rects:
                if (rb.x_min + inset < px < rb.x_max - inset
                        and rb.y_min + inset < py < rb.y_max - inset):
                    desc = f"'{label}'" if label else "unlabeled"
                    end = "start" if t_val == 0.0 else "end"
                    errors.append(
                        f"Path {end}point inside rect {desc} "
                        f"at ({px:.0f}, {py:.0f})"
                    )

    return errors


def check_text_on_cluster_border(
    svg_path: Path,
    *,
    padding: float = CLUSTER_BORDER_TEXT_PADDING,
) -> list[str]:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    cluster_rects: list[tuple[BBox, float]] = []
    for rect_el in root.iter("rect"):
        if not rect_el.get("stroke-dasharray"):
            continue
        rb = _parse_rect_bbox(rect_el)
        if rb is None:
            continue
        stroke_w = float(rect_el.get("stroke-width", "2"))
        cluster_rects.append((rb, stroke_w))

    text_labels: list[tuple[str, BBox]] = []
    for text_el in root.iter("text"):
        content = text_el.text or ""
        if not content.strip():
            continue
        tb = text_bbox(text_el)
        if tb is not None:
            text_labels.append((content.strip(), tb))

    errors: list[str] = []
    for label, tb in text_labels:
        text_poly = tb.to_shapely()
        for rb, stroke_w in cluster_rects:
            border = rb.to_shapely().boundary.buffer(stroke_w / 2 + padding)
            if text_poly.intersects(border):
                # Skip cluster's own title label (positioned inside, near top-left)
                if (rb.x_min < tb.cx < rb.x_min + rb.width * 0.4
                        and rb.y_min < (tb.y_min + tb.y_max) / 2 < rb.y_min + 30):
                    continue
                errors.append(
                    f"Text '{label}' overlaps cluster border"
                )

    return errors


def check_child_rect_clips_parent(
    svg_path: Path,
    *,
    min_margin: float = CHILD_RECT_MIN_MARGIN,
) -> list[str]:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    text_labels: list[tuple[str, BBox]] = []
    for text_el in root.iter("text"):
        content = text_el.text or ""
        if not content.strip():
            continue
        tb = text_bbox(text_el)
        if tb is not None:
            text_labels.append((content.strip(), tb))

    parent_rects: list[BBox] = []
    child_rects: list[tuple[BBox, str]] = []
    for rect_el in root.iter("rect"):
        if rect_el.get("stroke-dasharray"):
            rb = _parse_rect_bbox(rect_el)
            if rb is not None:
                parent_rects.append(rb)
            continue
        rb = _parse_rect_bbox(rect_el, max_area=50_000)
        if rb is None:
            continue
        label = ""
        for name, tb in text_labels:
            if (rb.x_min <= tb.cx <= rb.x_max
                    and rb.y_min <= (tb.y_min + tb.y_max) / 2 <= rb.y_max):
                label = name
                break
        child_rects.append((rb, label))

    errors: list[str] = []
    for cb, label in child_rects:
        for pb in parent_rects:
            # Check if child center is inside parent (it's a child)
            if not (pb.x_min < cb.cx < pb.x_max
                    and pb.y_min < (cb.y_min + cb.y_max) / 2 < pb.y_max):
                continue
            clips: list[str] = []
            if cb.x_min < pb.x_min + min_margin:
                clips.append("left")
            if cb.x_max > pb.x_max - min_margin:
                clips.append("right")
            if cb.y_min < pb.y_min + min_margin:
                clips.append("top")
            if cb.y_max > pb.y_max - min_margin:
                clips.append("bottom")
            if clips:
                desc = f"'{label}'" if label else "unlabeled"
                errors.append(
                    f"Child rect {desc} clips parent border "
                    f"on {', '.join(clips)}"
                )

    return errors


def check_text_on_solid_border(
    svg_path: Path,
    *,
    padding: float = SOLID_BORDER_TEXT_PADDING,
) -> list[str]:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    solid_rects: list[tuple[BBox, float]] = []
    for rect_el in root.iter("rect"):
        if rect_el.get("stroke-dasharray"):
            continue
        rb = _parse_rect_bbox(rect_el)
        if rb is None:
            continue
        stroke = rect_el.get("stroke")
        if not stroke or stroke == "none":
            continue
        stroke_w = float(rect_el.get("stroke-width", "2"))
        solid_rects.append((rb, stroke_w))

    text_labels: list[tuple[str, BBox]] = []
    for text_el in root.iter("text"):
        content = text_el.text or ""
        if not content.strip():
            continue
        tb = text_bbox(text_el)
        if tb is not None:
            text_labels.append((content.strip(), tb))

    errors: list[str] = []
    for label, tb in text_labels:
        text_poly = tb.to_shapely()
        text_cy = (tb.y_min + tb.y_max) / 2
        for rb, stroke_w in solid_rects:
            # Skip text whose center is clearly inside the rect (it's a label)
            if (rb.x_min + padding < tb.cx < rb.x_max - padding
                    and rb.y_min + padding < text_cy < rb.y_max - padding):
                continue
            border = rb.to_shapely().boundary.buffer(stroke_w / 2 + padding)
            if text_poly.intersects(border):
                errors.append(
                    f"Text '{label}' overlaps solid rect border"
                )

    return errors


def check_text_occluded_by_rect(
    svg_path: Path,
) -> list[str]:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    # Walk elements in document order, tracking text elements seen so far
    preceding_texts: list[tuple[str, BBox]] = []
    errors: list[str] = []

    for elem in root.iter():
        if elem.tag == "text":
            content = elem.text or ""
            if not content.strip():
                continue
            tb = text_bbox(elem)
            if tb is not None:
                preceding_texts.append((content.strip(), tb))
        elif elem.tag == "rect":
            fill = elem.get("fill", "")
            if not fill or fill == "none" or fill == "transparent":
                continue
            rb = _parse_rect_bbox(elem)
            if rb is None:
                continue
            for label, tb in preceding_texts:
                if (rb.x_min <= tb.x_min
                        and rb.y_min <= tb.y_min
                        and rb.x_max >= tb.x_max
                        and rb.y_max >= tb.y_max):
                    errors.append(
                        f"Text '{label}' occluded by later rect "
                        f"(fill={fill})"
                    )

    return errors


def check_text_outside_viewport(
    svg_path: Path,
    *,
    margin: float = 0.0,
) -> list[str]:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    # Parse viewport dimensions from the root <svg> element
    w_str = root.get("width")
    h_str = root.get("height")
    if w_str is None or h_str is None:
        return []
    vp_w = float(w_str.replace("px", "").replace("pt", ""))
    vp_h = float(h_str.replace("px", "").replace("pt", ""))

    errors: list[str] = []
    for text_el in root.iter("text"):
        content = text_el.text or ""
        if not content.strip():
            continue
        tb = text_bbox(text_el)
        if tb is None:
            continue

        clipped_sides: list[str] = []
        if tb.x_min < margin:
            clipped_sides.append(f"left by {margin - tb.x_min:.0f}px")
        if tb.x_max > vp_w - margin:
            clipped_sides.append(f"right by {tb.x_max - (vp_w - margin):.0f}px")
        if tb.y_min < margin:
            clipped_sides.append(f"top by {margin - tb.y_min:.0f}px")
        if tb.y_max > vp_h - margin:
            clipped_sides.append(f"bottom by {tb.y_max - (vp_h - margin):.0f}px")

        if clipped_sides:
            errors.append(
                f"Text '{content.strip()}' extends outside viewport "
                f"({', '.join(clipped_sides)})"
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
        errors.extend(check_line_crosses_text(svg_path))
        errors.extend(check_path_crosses_text(svg_path))
        errors.extend(check_text_outside_viewport(svg_path))
        errors.extend(check_path_endpoint_inside_rect(svg_path))
        errors.extend(check_text_on_cluster_border(svg_path))
        errors.extend(check_child_rect_clips_parent(svg_path))
        errors.extend(check_text_on_solid_border(svg_path))
        errors.extend(check_text_occluded_by_rect(svg_path))
    return errors
