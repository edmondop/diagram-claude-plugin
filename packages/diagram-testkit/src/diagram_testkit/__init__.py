"""diagram-testkit - SVG quality linter for generated diagrams."""

from diagram_testkit.checks import (
    check_annotation_overflow,
    check_arrow_crosses_text,
    check_container_alignment,
    check_text_crosses_shape,
    check_text_overlaps_shape,
    check_text_overlaps_text,
    run_all_checks,
)
from diagram_testkit.extractors import detect_format, extract
from diagram_testkit.geometry import BBox
from diagram_testkit.model import (
    ArrowPath,
    Container,
    DiagramElements,
    Format,
    Shape,
    TextLabel,
)

__all__ = [
    "ArrowPath",
    "BBox",
    "Container",
    "DiagramElements",
    "Format",
    "Shape",
    "TextLabel",
    "check_annotation_overflow",
    "check_arrow_crosses_text",
    "check_container_alignment",
    "check_text_crosses_shape",
    "check_text_overlaps_shape",
    "check_text_overlaps_text",
    "detect_format",
    "extract",
    "run_all_checks",
]
