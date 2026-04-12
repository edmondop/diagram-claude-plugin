"""diagram-testkit — SVG quality linter for generated diagrams."""

from .checks import (
    check_arrow_crosses_text,
    check_cluster_alignment,
    check_edge_label_distance,
    check_label_overlaps,
    check_matplotlib_annotation_overflow,
    check_matplotlib_arrow_crosses_text,
    check_matplotlib_text_overlaps_shape,
    check_matplotlib_text_overlaps_text,
    check_text_crosses_border,
    run_all_checks,
)
from .geometry import BBox
from .parser import ParsedSVG, parse_svg

__all__ = [
    "BBox",
    "ParsedSVG",
    "check_arrow_crosses_text",
    "check_cluster_alignment",
    "check_edge_label_distance",
    "check_label_overlaps",
    "check_matplotlib_annotation_overflow",
    "check_matplotlib_arrow_crosses_text",
    "check_matplotlib_text_overlaps_shape",
    "check_matplotlib_text_overlaps_text",
    "check_text_crosses_border",
    "parse_svg",
    "run_all_checks",
]
