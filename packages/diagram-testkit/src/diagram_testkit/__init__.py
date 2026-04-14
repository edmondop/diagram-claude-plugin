"""diagram-testkit - SVG quality linter for generated diagrams."""

from diagram_testkit.checks import check_annotation_overflow
from diagram_testkit.checks import check_arrow_crosses_text
from diagram_testkit.checks import check_container_alignment
from diagram_testkit.checks import check_text_crosses_shape
from diagram_testkit.checks import check_text_overlaps_shape
from diagram_testkit.checks import check_text_overlaps_text
from diagram_testkit.checks import run_all_checks
from diagram_testkit.extractors import detect_format
from diagram_testkit.extractors import extract
from diagram_testkit.geometry import BBox
from diagram_testkit.model import ArrowPath
from diagram_testkit.model import Container
from diagram_testkit.model import DiagramElements
from diagram_testkit.model import Format
from diagram_testkit.model import Shape
from diagram_testkit.model import TextLabel

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
