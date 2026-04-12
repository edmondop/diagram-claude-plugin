"""Format-agnostic SVG quality checks operating on DiagramElements."""

from .geometry import path_to_linestring
from .model import DiagramElements

ARROW_TEXT_PADDING = 2.0
BORDER_STROKE_WIDTH = 2.0
MAX_CENTER_OFFSET_RATIO = 0.7


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


def run_all_checks(elems: DiagramElements) -> list[str]:
    errors: list[str] = []
    errors.extend(check_arrow_crosses_text(elems))
    errors.extend(check_text_overlaps_text(elems))
    errors.extend(check_text_crosses_shape(elems))
    errors.extend(check_text_overlaps_shape(elems))
    errors.extend(check_annotation_overflow(elems))
    return errors
