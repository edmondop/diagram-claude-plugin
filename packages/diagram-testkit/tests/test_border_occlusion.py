"""Tests for solid-border text overlap and z-order occlusion checks."""

from pathlib import Path

from diagram_testkit.checks import check_text_occluded_by_rect
from diagram_testkit.checks import check_text_on_solid_border

FIXTURES_DIR = Path(__file__).parent / "fixtures"
PASSING_DIR = FIXTURES_DIR / "passing"


class TestTextOnSolidBorder:

    def test_text_on_solid_border_detected(self):
        errors = check_text_on_solid_border(
            FIXTURES_DIR / "border-and-occlusion-faults.svg",
        )
        border_errors = [e for e in errors if "Border Label" in e]
        assert border_errors, (
            f"Expected 'Border Label' to overlap solid rect border, "
            f"got: {errors}"
        )

    def test_text_inside_rect_not_flagged(self):
        errors = check_text_on_solid_border(
            FIXTURES_DIR / "border-and-occlusion-faults.svg",
        )
        inside_errors = [e for e in errors if "Component A" in e]
        assert not inside_errors, (
            f"'Component A' is inside the rect and should not be flagged, "
            f"got: {errors}"
        )

    def test_text_far_from_solid_border_passes(self):
        errors = check_text_on_solid_border(
            PASSING_DIR / "text-inside-viewport.svg",
        )
        assert not errors


class TestTextOccludedByRect:

    def test_occluded_text_detected(self):
        errors = check_text_occluded_by_rect(
            FIXTURES_DIR / "border-and-occlusion-faults.svg",
        )
        occluded_errors = [e for e in errors if "Hidden Title" in e]
        assert occluded_errors, (
            f"Expected 'Hidden Title' to be flagged as occluded, "
            f"got: {errors}"
        )

    def test_text_after_rect_not_flagged(self):
        errors = check_text_occluded_by_rect(
            FIXTURES_DIR / "border-and-occlusion-faults.svg",
        )
        after_errors = [e for e in errors if "Component B" in e]
        assert not after_errors, (
            f"'Component B' is drawn after its rect and should not be "
            f"flagged as occluded, got: {errors}"
        )

    def test_unfilled_rect_does_not_occlude(self):
        errors = check_text_occluded_by_rect(
            PASSING_DIR / "text-inside-viewport.svg",
        )
        assert not errors
