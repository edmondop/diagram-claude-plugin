# Protocol-Based Testkit Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Separate format-specific SVG extraction from format-agnostic geometric checks via a common `DiagramElements` intermediate representation.

**Architecture:** SVG files flow through `detect_format() -> extractor.extract() -> DiagramElements -> run_checks() -> errors`. Each format (Graphviz, matplotlib, Excalidraw) has its own extractor that produces the same `DiagramElements` model. Six format-agnostic check functions operate on this model.

**Tech Stack:** Python 3.10+, svgpathtools, shapely, pytest

**Worktree:** `/Users/eporcu/code/claude-plugins/diagram-claude-plugin/.worktrees/diagram-testkit/`
**Package root:** `packages/diagram-testkit/`
**Source:** `packages/diagram-testkit/src/diagram_testkit/`
**Tests:** `packages/diagram-testkit/tests/`
**Run tests:** `.venv/bin/pytest tests/ -v --tb=short` (from package root)

---

### Task 1: Add model.py with Format enum and dataclasses

**Files:**
- Create: `src/diagram_testkit/model.py`
- Test: `tests/test_model.py`

**Step 1: Write the failing test**

Create `tests/test_model.py`:

```python
from pathlib import Path

from diagram_testkit.model import (
    ArrowPath,
    Container,
    DiagramElements,
    Format,
    Shape,
    TextLabel,
)


def test_format_enum_has_three_members():
    assert Format.GRAPHVIZ.value == "graphviz"
    assert Format.MATPLOTLIB.value == "matplotlib"
    assert Format.EXCALIDRAW.value == "excalidraw"


def test_diagram_elements_defaults_to_empty_lists():
    elems = DiagramElements()
    assert elems.texts == []
    assert elems.arrows == []
    assert elems.shapes == []
    assert elems.containers == []
    assert elems.source_path is None


def test_text_label_owner_defaults_to_none():
    from diagram_testkit.geometry import BBox

    label = TextLabel(id="t1", bbox=BBox(0, 0, 10, 10))
    assert label.owner is None


def test_arrow_path_owner_defaults_to_none():
    arrow = ArrowPath(id="a1", path_d="M0,0 L10,10")
    assert arrow.owner is None


def test_shape_has_bbox_and_path():
    from diagram_testkit.geometry import BBox

    shape = Shape(id="s1", bbox=BBox(0, 0, 50, 50), path_d="M0,0 L50,0 L50,50 Z")
    assert shape.bbox.width == 50


def test_container_has_bbox():
    from diagram_testkit.geometry import BBox

    container = Container(id="c1", bbox=BBox(10, 20, 100, 200))
    assert container.bbox.cx == 55.0
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_model.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'diagram_testkit.model'`

**Step 3: Write minimal implementation**

Create `src/diagram_testkit/model.py`:

```python
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .geometry import BBox


class Format(Enum):
    GRAPHVIZ = "graphviz"
    MATPLOTLIB = "matplotlib"
    EXCALIDRAW = "excalidraw"


@dataclass
class TextLabel:
    id: str
    bbox: BBox
    owner: str | None = None


@dataclass
class ArrowPath:
    id: str
    path_d: str
    owner: str | None = None


@dataclass
class Shape:
    id: str
    bbox: BBox
    path_d: str


@dataclass
class Container:
    id: str
    bbox: BBox


@dataclass
class DiagramElements:
    texts: list[TextLabel] = field(default_factory=list)
    arrows: list[ArrowPath] = field(default_factory=list)
    shapes: list[Shape] = field(default_factory=list)
    containers: list[Container] = field(default_factory=list)
    source_path: Path | None = None
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_model.py -v`
Expected: 7 PASSED

**Step 5: Commit**

```bash
git add src/diagram_testkit/model.py tests/test_model.py
git commit -m "feat(testkit): add model.py with Format enum and DiagramElements dataclasses"
```

---

### Task 2: Add extractors package with protocol and Graphviz extractor

**Files:**
- Create: `src/diagram_testkit/extractors/__init__.py`
- Create: `src/diagram_testkit/extractors/base.py`
- Create: `src/diagram_testkit/extractors/graphviz.py`
- Test: `tests/test_extractors.py`

**Step 1: Write the failing test**

Create `tests/test_extractors.py`:

```python
from pathlib import Path

import pytest

from diagram_testkit.extractors import detect_format, extract
from diagram_testkit.model import Format

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestDetectFormat:

    def test_detects_graphviz_svg(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs, "No architecture fixture SVGs found"
        assert detect_format(svgs[0]) == Format.GRAPHVIZ

    def test_detects_matplotlib_svg(self):
        svgs = sorted(FIXTURES_DIR.glob("matplotlib-*.svg"))
        assert svgs, "No matplotlib fixture SVGs found"
        assert detect_format(svgs[0]) == Format.MATPLOTLIB

    def test_returns_none_for_unknown_format(self, tmp_path):
        svg = tmp_path / "plain.svg"
        svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')
        assert detect_format(svg) is None


class TestGraphvizExtractor:

    def test_extracts_nodes_as_text_labels(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.texts, "Should have at least one TextLabel"
        assert all(t.id for t in elems.texts)

    def test_extracts_edges_as_arrows(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.arrows, "Should have at least one ArrowPath"

    def test_extracts_cluster_borders_as_shapes(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.shapes, "Should have at least one Shape from cluster borders"

    def test_extracts_clusters_as_containers(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.containers, "Should have at least one Container"

    def test_edge_labels_have_owner(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-arrow-crosses-label*.svg"))
        assert svgs
        elems = extract(svgs[0])
        edge_texts = [t for t in elems.texts if t.owner is not None]
        assert edge_texts, "Edge labels should have owner set"

    def test_source_path_is_set(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.source_path == svgs[0]

    def test_format_override_works(self):
        svgs = sorted(FIXTURES_DIR.glob("architecture-*.svg"))
        assert svgs
        elems = extract(svgs[0], format=Format.GRAPHVIZ)
        assert elems.texts
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_extractors.py -v`
Expected: FAIL with `ModuleNotFoundError: No module named 'diagram_testkit.extractors'`

**Step 3: Write implementation**

Create `src/diagram_testkit/extractors/base.py`:

```python
from pathlib import Path
from typing import Protocol

from ..model import DiagramElements


class DiagramExtractor(Protocol):
    def extract(self, svg_path: Path) -> DiagramElements: ...
```

Create `src/diagram_testkit/extractors/graphviz.py` — absorbs logic from `parser.py`:

```python
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
```

Create `src/diagram_testkit/extractors/__init__.py`:

```python
import xml.etree.ElementTree as ET
from pathlib import Path

from ..model import DiagramElements, Format
from .base import DiagramExtractor
from .graphviz import GraphvizExtractor

EXTRACTORS: dict[Format, DiagramExtractor] = {
    Format.GRAPHVIZ: GraphvizExtractor(),
}


def detect_format(svg_path: Path) -> Format | None:
    tree = ET.parse(svg_path)
    root = tree.getroot()
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]

    if root.find(".//*[@id='graph0']") is not None:
        return Format.GRAPHVIZ
    if root.find(".//*[@id='axes_1']") is not None:
        return Format.MATPLOTLIB
    return None


def extract(
    svg_path: Path,
    *,
    format: Format | None = None,
) -> DiagramElements:
    if format is None:
        format = detect_format(svg_path)
    if format is None:
        return DiagramElements(source_path=svg_path)
    extractor = EXTRACTORS.get(format)
    if extractor is None:
        return DiagramElements(source_path=svg_path)
    return extractor.extract(svg_path)
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_extractors.py -v`
Expected: 10 PASSED

**Step 5: Run ALL tests to verify nothing broke**

Run: `.venv/bin/pytest tests/ -v`
Expected: 26 PASSED (19 original + 7 new)

**Step 6: Commit**

```bash
git add src/diagram_testkit/extractors/ tests/test_extractors.py
git commit -m "feat(testkit): add extractors package with protocol and Graphviz extractor"
```

---

### Task 3: Add matplotlib extractor

**Files:**
- Modify: `src/diagram_testkit/extractors/__init__.py` (add matplotlib to EXTRACTORS)
- Create: `src/diagram_testkit/extractors/matplotlib.py`
- Modify: `tests/test_extractors.py` (add matplotlib tests)

**Step 1: Write the failing test**

Append to `tests/test_extractors.py`:

```python
class TestMatplotlibExtractor:

    def test_extracts_text_labels(self):
        svgs = sorted(FIXTURES_DIR.glob("matplotlib-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.texts, "Should have at least one TextLabel"

    def test_extracts_arrow_paths(self):
        svgs = sorted(FIXTURES_DIR.glob("matplotlib-arrow-crosses-text.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.arrows, "Should have at least one ArrowPath"

    def test_extracts_shapes(self):
        svgs = sorted(FIXTURES_DIR.glob("matplotlib-text-overlaps-shape.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.shapes, "Should have at least one Shape"

    def test_extracts_axes_container(self):
        svgs = sorted(FIXTURES_DIR.glob("matplotlib-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.containers, "Should have axes Container"

    def test_source_path_is_set(self):
        svgs = sorted(FIXTURES_DIR.glob("matplotlib-*.svg"))
        assert svgs
        elems = extract(svgs[0])
        assert elems.source_path == svgs[0]
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_extractors.py::TestMatplotlibExtractor -v`
Expected: FAIL — matplotlib not in EXTRACTORS yet, so `extract()` returns empty `DiagramElements`

**Step 3: Write implementation**

Create `src/diagram_testkit/extractors/matplotlib.py` — absorbs `_mpl_*` helpers from `checks.py`:

```python
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from ..geometry import BBox, bbox_from_path_d
from ..model import ArrowPath, Container, DiagramElements, Shape, TextLabel

GLYPH_ADVANCE_ESTIMATE = 65.0
_MPL_GLYPH_CAP_HEIGHT = 72.9
_MPL_GLYPH_DESCENT = 1.42


def _strip_namespaces(root: ET.Element) -> None:
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]


def _parse_transform(
    transform: str,
) -> tuple[float, float, float, float] | None:
    t_match = re.search(
        r"translate\(([\d.e+-]+)[\s,]+([\d.e+-]+)\)", transform
    )
    s_match = re.search(
        r"scale\(([\d.e+-]+)[\s,]+([\d.e+-]+)\)", transform
    )
    if not t_match or not s_match:
        return None
    tx = float(t_match.group(1))
    ty = float(t_match.group(2))
    sx = abs(float(s_match.group(1)))
    sy = abs(float(s_match.group(2)))
    return tx, ty, sx, sy


class MatplotlibExtractor:

    def extract(self, svg_path: Path) -> DiagramElements:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        _strip_namespaces(root)

        axes_g = None
        for elem in root.iter():
            if elem.get("id", "").startswith("axes_"):
                axes_g = elem
                break
        if axes_g is None:
            return DiagramElements(source_path=svg_path)

        texts: list[TextLabel] = []
        arrows: list[ArrowPath] = []
        shapes: list[Shape] = []
        containers: list[Container] = []

        self._extract_axes_container(axes_g, containers)
        self._extract_texts(axes_g, texts)
        self._extract_patches(axes_g, arrows, shapes)

        return DiagramElements(
            texts=texts,
            arrows=arrows,
            shapes=shapes,
            containers=containers,
            source_path=svg_path,
        )

    def _extract_axes_container(
        self,
        axes_g: ET.Element,
        containers: list[Container],
    ) -> None:
        patch_2 = axes_g.find("*[@id='patch_2']")
        if patch_2 is None:
            return
        bg_path = patch_2.find("path")
        if bg_path is None:
            return
        bb = bbox_from_path_d(bg_path.get("d", ""))
        if bb:
            containers.append(Container(id="axes_1", bbox=bb))

    def _extract_texts(
        self,
        axes_g: ET.Element,
        texts: list[TextLabel],
    ) -> None:
        for g in axes_g:
            g_id = g.get("id", "")
            if not g_id.startswith("text_"):
                continue
            for idx, inner_g in enumerate(g.findall("g")):
                transform = inner_g.get("transform", "")
                parsed = _parse_transform(transform)
                if parsed is None:
                    continue
                tx, ty, sx, sy = parsed

                max_use_x = 0.0
                for use_el in inner_g.findall("use"):
                    ut = use_el.get("transform", "")
                    ut_match = re.search(r"translate\(([\d.e+-]+)", ut)
                    if ut_match:
                        max_use_x = max(max_use_x, float(ut_match.group(1)))

                x_min = tx
                x_max = tx + (max_use_x + GLYPH_ADVANCE_ESTIMATE) * sx
                y_min = ty - _MPL_GLYPH_CAP_HEIGHT * sy
                y_max = ty + _MPL_GLYPH_DESCENT * sy
                label = f"{g_id}" if idx == 0 else f"{g_id}[{idx}]"
                texts.append(TextLabel(
                    id=label,
                    bbox=BBox(x_min, y_min, x_max, y_max),
                ))

    def _extract_patches(
        self,
        axes_g: ET.Element,
        arrows: list[ArrowPath],
        shapes: list[Shape],
    ) -> None:
        for g in axes_g:
            g_id = g.get("id", "")
            if not g_id.startswith("patch_"):
                continue
            paths = g.findall("path")
            if not paths:
                continue
            first_path = paths[0]
            style = first_path.get("style", "")
            d = first_path.get("d", "")
            if not d:
                continue

            if "fill: none" in style:
                arrows.append(ArrowPath(id=g_id, path_d=d))
            elif "#ffffff" not in style:
                bb = bbox_from_path_d(d)
                if bb:
                    shapes.append(Shape(id=g_id, bbox=bb, path_d=d))
```

Modify `src/diagram_testkit/extractors/__init__.py` — add matplotlib to EXTRACTORS dict:

```python
# Add import at top:
from .matplotlib import MatplotlibExtractor

# Update EXTRACTORS:
EXTRACTORS: dict[Format, DiagramExtractor] = {
    Format.GRAPHVIZ: GraphvizExtractor(),
    Format.MATPLOTLIB: MatplotlibExtractor(),
}
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_extractors.py -v`
Expected: 15 PASSED

**Step 5: Run ALL tests**

Run: `.venv/bin/pytest tests/ -v`
Expected: 31 PASSED

**Step 6: Commit**

```bash
git add src/diagram_testkit/extractors/matplotlib.py src/diagram_testkit/extractors/__init__.py tests/test_extractors.py
git commit -m "feat(testkit): add matplotlib extractor"
```

---

### Task 4: Rewrite checks.py to operate on DiagramElements

**Files:**
- Rewrite: `src/diagram_testkit/checks.py`
- Rewrite: `tests/test_checks.py`

This is the core migration: checks become format-agnostic, operating on `DiagramElements` instead of `ParsedSVG`.

**Step 1: Write the failing tests**

Rewrite `tests/test_checks.py`:

```python
from pathlib import Path

import pytest

from diagram_testkit.checks import (
    check_annotation_overflow,
    check_arrow_crosses_text,
    check_container_alignment,
    check_text_crosses_shape,
    check_text_overlaps_shape,
    check_text_overlaps_text,
    run_all_checks,
)
from diagram_testkit.extractors import extract
from diagram_testkit.geometry import BBox
from diagram_testkit.model import (
    ArrowPath,
    Container,
    DiagramElements,
    Shape,
    TextLabel,
)

FIXTURES_DIR = Path(__file__).parent / "fixtures"


class TestFixturesMustFail:

    @pytest.fixture(params=sorted(FIXTURES_DIR.glob("*.svg")))
    def fixture_elems(self, request: pytest.FixtureRequest):
        path = request.param
        return (path.name, extract(path))

    def test_fixture_fails_at_least_one_check(
        self, fixture_elems: tuple[str, DiagramElements],
    ) -> None:
        name, elems = fixture_elems
        errors = run_all_checks(elems)
        assert errors, (
            f"Fixture {name} passed ALL checks - either the fixture "
            f"is not actually broken or the checks are too lenient"
        )


class TestArrowCrossesText:

    def test_crossing_arrow_detected(self):
        elems = DiagramElements(
            texts=[TextLabel(id="label", bbox=BBox(5, 5, 15, 15))],
            arrows=[ArrowPath(id="arrow", path_d="M 0,10 L 20,10")],
        )
        errors = check_arrow_crosses_text(elems)
        assert errors
        assert "arrow" in errors[0].lower() or "Arrow" in errors[0]

    def test_same_owner_skipped(self):
        elems = DiagramElements(
            texts=[TextLabel(id="label", bbox=BBox(5, 5, 15, 15), owner="e1")],
            arrows=[ArrowPath(id="arrow", path_d="M 0,10 L 20,10", owner="e1")],
        )
        errors = check_arrow_crosses_text(elems)
        assert not errors


class TestTextOverlapsText:

    def test_overlapping_texts_detected(self):
        elems = DiagramElements(
            texts=[
                TextLabel(id="t1", bbox=BBox(0, 0, 20, 10)),
                TextLabel(id="t2", bbox=BBox(10, 0, 30, 10)),
            ],
        )
        errors = check_text_overlaps_text(elems)
        assert errors

    def test_same_owner_skipped(self):
        elems = DiagramElements(
            texts=[
                TextLabel(id="t1", bbox=BBox(0, 0, 20, 10), owner="e1"),
                TextLabel(id="t2", bbox=BBox(10, 0, 30, 10), owner="e1"),
            ],
        )
        errors = check_text_overlaps_text(elems)
        assert not errors


class TestContainerAlignment:

    def test_aligned_containers_pass(self):
        elems = DiagramElements(
            containers=[
                Container(id="a", bbox=BBox(100, 0, 200, 50)),
                Container(id="b", bbox=BBox(110, 60, 210, 110)),
            ],
        )
        errors = check_container_alignment(elems, src="a", dst="b")
        assert not errors

    def test_misaligned_containers_fail(self):
        elems = DiagramElements(
            containers=[
                Container(id="a", bbox=BBox(0, 0, 100, 50)),
                Container(id="b", bbox=BBox(500, 60, 600, 110)),
            ],
        )
        errors = check_container_alignment(elems, src="a", dst="b")
        assert errors
        assert "Too far" in errors[0]

    def test_missing_container_returns_empty(self):
        elems = DiagramElements()
        errors = check_container_alignment(
            elems, src="nonexistent", dst="also_nonexistent"
        )
        assert not errors
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_checks.py -v`
Expected: FAIL — `check_text_overlaps_text`, `check_text_crosses_shape`, etc. don't exist yet

**Step 3: Rewrite checks.py**

Replace `src/diagram_testkit/checks.py` entirely:

```python
"""Format-agnostic SVG quality checks operating on DiagramElements."""

from .geometry import BBox, path_to_linestring
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
```

**Step 4: Run test to verify it passes**

Run: `.venv/bin/pytest tests/test_checks.py -v`
Expected: ALL PASSED

**Step 5: Run ALL tests**

Run: `.venv/bin/pytest tests/ -v`
Expected: `test_parser.py` and `test_cli.py` will fail because they still import old API. That's fine — Task 5 fixes them.

**Step 6: Commit**

```bash
git add src/diagram_testkit/checks.py tests/test_checks.py
git commit -m "feat(testkit): rewrite checks to operate on DiagramElements"
```

---

### Task 5: Update CLI, __init__.py exports, fix remaining tests, delete parser.py

**Files:**
- Rewrite: `src/diagram_testkit/__init__.py`
- Rewrite: `src/diagram_testkit/cli.py`
- Rewrite: `tests/test_cli.py`
- Delete: `tests/test_parser.py`
- Delete: `src/diagram_testkit/parser.py`

**Step 1: Write the failing tests**

Rewrite `tests/test_cli.py`:

```python
import subprocess
import sys
from pathlib import Path

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def _run_cli(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, "-m", "diagram_testkit", *args],
        capture_output=True,
        text=True,
    )


def test_cli_lint_bad_fixture_exits_1():
    bad_svgs = list(FIXTURES_DIR.glob("architecture-arrow-*.svg"))
    assert bad_svgs, "No arrow-crossing fixture found"
    result = _run_cli("lint", str(bad_svgs[0]))
    assert result.returncode == 1
    assert "FAIL" in result.stdout


def test_cli_lint_matplotlib_fixture_exits_1():
    mpl_svgs = list(FIXTURES_DIR.glob("matplotlib-*.svg"))
    assert mpl_svgs
    result = _run_cli("lint", str(mpl_svgs[0]))
    assert result.returncode == 1
    assert "FAIL" in result.stdout


def test_cli_lint_format_override():
    svgs = list(FIXTURES_DIR.glob("architecture-*.svg"))
    assert svgs
    result = _run_cli("lint", "--format", "graphviz", str(svgs[0]))
    assert result.returncode in (0, 1)


def test_cli_lint_nonexistent_file_exits_1():
    result = _run_cli("lint", "/nonexistent/file.svg")
    assert result.returncode == 1
    assert "File not found" in result.stdout


def test_cli_no_command_exits_1():
    result = _run_cli()
    assert result.returncode == 1
```

**Step 2: Run test to verify it fails**

Run: `.venv/bin/pytest tests/test_cli.py -v`
Expected: FAIL — `test_cli_lint_format_override` fails because `--format` not yet supported

**Step 3: Write implementation**

Rewrite `src/diagram_testkit/cli.py`:

```python
"""CLI entrypoint for diagram-testkit."""

import argparse
import sys
from pathlib import Path

from .checks import check_container_alignment, run_all_checks
from .extractors import extract
from .model import Format


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="diagram-testkit",
        description="Lint SVG diagrams for quality issues",
    )
    sub = parser.add_subparsers(dest="command")

    lint_parser = sub.add_parser("lint", help="Check SVG files")
    lint_parser.add_argument("files", nargs="+", type=Path)
    lint_parser.add_argument(
        "--format",
        choices=[f.value for f in Format],
        help="Override format auto-detection",
    )
    lint_parser.add_argument(
        "--cluster-align",
        metavar="src=X,dst=Y",
        help="Check that container dst is centered below container src",
    )

    args = parser.parse_args()
    if args.command != "lint":
        parser.print_help()
        sys.exit(1)

    fmt = Format(args.format) if args.format else None

    cluster_src = None
    cluster_dst = None
    if args.cluster_align:
        parts = dict(p.split("=") for p in args.cluster_align.split(","))
        cluster_src = parts.get("src")
        cluster_dst = parts.get("dst")
        if not cluster_src or not cluster_dst:
            print("Error: --cluster-align requires src=X,dst=Y")
            sys.exit(1)

    failed = False
    for svg_path in args.files:
        if not svg_path.exists():
            print(f"File not found: {svg_path}")
            failed = True
            continue

        elems = extract(svg_path, format=fmt)
        errors = run_all_checks(elems)

        if cluster_src and cluster_dst:
            errors.extend(
                check_container_alignment(
                    elems, src=cluster_src, dst=cluster_dst
                )
            )

        if errors:
            print(f"FAIL: {svg_path}")
            for e in errors:
                print(f"  {e}")
            failed = True
        else:
            print(f"OK: {svg_path}")

    sys.exit(1 if failed else 0)
```

Rewrite `src/diagram_testkit/__init__.py`:

```python
"""diagram-testkit - SVG quality linter for generated diagrams."""

from .checks import (
    check_annotation_overflow,
    check_arrow_crosses_text,
    check_container_alignment,
    check_text_crosses_shape,
    check_text_overlaps_shape,
    check_text_overlaps_text,
    run_all_checks,
)
from .extractors import detect_format, extract
from .geometry import BBox
from .model import (
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
```

Delete `src/diagram_testkit/parser.py` and `tests/test_parser.py`.

**Step 4: Run ALL tests**

Run: `.venv/bin/pytest tests/ -v`
Expected: ALL PASSED (tests from test_model, test_extractors, test_checks, test_cli)

**Step 5: Commit**

```bash
git rm src/diagram_testkit/parser.py tests/test_parser.py
git add src/diagram_testkit/__init__.py src/diagram_testkit/cli.py tests/test_cli.py
git commit -m "feat(testkit): update CLI with --format flag, clean up exports, delete parser.py"
```

---

### Task 6: Add Excalidraw extractor stub

**Files:**
- Create: `src/diagram_testkit/extractors/excalidraw.py`
- Modify: `src/diagram_testkit/extractors/__init__.py` (add to EXTRACTORS and detect_format)
- Modify: `tests/test_extractors.py` (add Excalidraw tests)

**Step 1: Write the failing test**

Append to `tests/test_extractors.py`:

```python
class TestExcalidrawExtractor:

    def test_unknown_svg_returns_empty_elements(self, tmp_path):
        svg = tmp_path / "plain.svg"
        svg.write_text('<svg xmlns="http://www.w3.org/2000/svg"><rect/></svg>')
        elems = extract(svg)
        assert not elems.texts
        assert not elems.arrows
        assert not elems.shapes
        assert not elems.containers
        assert elems.source_path == svg
```

**Step 2: Run test to verify it fails (or passes trivially)**

Run: `.venv/bin/pytest tests/test_extractors.py::TestExcalidrawExtractor -v`
Expected: PASS (since unknown format already returns empty). This test documents the expected stub behavior.

**Step 3: Write implementation**

Create `src/diagram_testkit/extractors/excalidraw.py`:

```python
from pathlib import Path

from ..model import DiagramElements


class ExcalidrawExtractor:

    def extract(self, svg_path: Path) -> DiagramElements:
        return DiagramElements(source_path=svg_path)
```

Modify `src/diagram_testkit/extractors/__init__.py` — add Excalidraw to EXTRACTORS and detection:

Add import: `from .excalidraw import ExcalidrawExtractor`

Update EXTRACTORS:
```python
EXTRACTORS: dict[Format, DiagramExtractor] = {
    Format.GRAPHVIZ: GraphvizExtractor(),
    Format.MATPLOTLIB: MatplotlibExtractor(),
    Format.EXCALIDRAW: ExcalidrawExtractor(),
}
```

Add Excalidraw detection in `detect_format()` before the `return None`:
```python
    # Excalidraw SVGs have data-id attributes on elements
    if root.find(".//*[@data-id]") is not None:
        return Format.EXCALIDRAW
```

**Step 4: Run ALL tests**

Run: `.venv/bin/pytest tests/ -v`
Expected: ALL PASSED

**Step 5: Commit**

```bash
git add src/diagram_testkit/extractors/excalidraw.py src/diagram_testkit/extractors/__init__.py tests/test_extractors.py
git commit -m "feat(testkit): add Excalidraw extractor stub"
```

---

### Task 7: Final verification and cleanup

**Step 1: Run full test suite**

Run: `.venv/bin/pytest tests/ -v`
Expected: ALL PASSED

**Step 2: Verify no leftover imports of old API**

Run: `grep -r "ParsedSVG\|from.*parser import\|check_label_overlaps\|check_edge_label_distance\|check_matplotlib_" src/ tests/`
Expected: No matches (all old references removed)

**Step 3: Verify clean file structure**

```
src/diagram_testkit/
  __init__.py
  __main__.py
  model.py
  geometry.py
  extractors/
    __init__.py
    base.py
    graphviz.py
    matplotlib.py
    excalidraw.py
  checks.py
  cli.py
```

No `parser.py`.

**Step 4: Run pre-commit hooks**

Run pre-commit hooks if configured.

**Step 5: Push and update PR**

Push to remote and update the PR description to reflect the protocol-based architecture.
