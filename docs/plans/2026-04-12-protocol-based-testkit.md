# Protocol-Based Testkit Redesign

## Problem

The testkit has 10 check functions in a single `checks.py`. Half only work on
Graphviz SVGs, half only on matplotlib. They silently return `[]` when fed the
wrong format. Extraction logic (XML parsing, transform decoding) is tangled
with geometric checking. Adding a new format means adding more `check_<format>_*`
functions and remembering to wire them into `run_all_checks`.

## Design

Separate **extraction** (format-specific SVG parsing) from **validation**
(format-agnostic geometric checks) via a common intermediate representation.

```
SVG file -> detect_format() -> extractor.extract() -> DiagramElements -> run_checks() -> errors
```

### Model (`model.py`)

```python
class Format(Enum):
    GRAPHVIZ = "graphviz"
    MATPLOTLIB = "matplotlib"
    EXCALIDRAW = "excalidraw"

@dataclass
class TextLabel:
    id: str
    bbox: BBox
    owner: str | None = None  # parent element id, for skip-self logic

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
    texts: list[TextLabel]
    arrows: list[ArrowPath]
    shapes: list[Shape]
    containers: list[Container]
    source_path: Path | None = None
```

### Extractor protocol (`extractors/base.py`)

```python
class DiagramExtractor(Protocol):
    def extract(self, svg_path: Path) -> DiagramElements: ...
```

### Extractor implementations

| File | Absorbs | Markers |
|---|---|---|
| `extractors/graphviz.py` | `parser.py` | `<g id="graph0">` |
| `extractors/matplotlib.py` | `_mpl_*` helpers from `checks.py` | `<g id="axes_1">` |
| `extractors/excalidraw.py` | new (stub initially) | Excalidraw-specific attrs |

### Dispatcher (`extractors/__init__.py`)

```python
def detect_format(svg_path: Path) -> Format | None: ...
def extract(svg_path: Path, *, format: Format | None = None) -> DiagramElements: ...
```

Auto-detects by parsing XML once and checking markers. `format` parameter
overrides detection.

### Mapping: Graphviz elements -> model

- Node/edge/cluster text -> `TextLabel` (edge labels get `owner=edge_id`)
- Edge paths -> `ArrowPath` (with `owner=edge_id`)
- Cluster border paths -> `Shape`
- Clusters -> `Container`

### Mapping: matplotlib elements -> model

- `text_N` groups (translate/scale transform) -> `TextLabel`
- `patch_N` with `fill: none` -> `ArrowPath`
- `patch_N` with colored fill -> `Shape`
- `axes_N` background -> `Container`

### Checks (`checks.py`)

Six format-agnostic functions operating on `DiagramElements`:

| Function | Inputs | Skip-self rule |
|---|---|---|
| `check_arrow_crosses_text` | arrows x texts | same owner |
| `check_text_overlaps_text` | texts x texts | same non-None owner |
| `check_text_crosses_shape` | texts x shapes (boundary) | - |
| `check_text_overlaps_shape` | texts x shapes (fill area) | - |
| `check_annotation_overflow` | texts x containers | - |
| `check_container_alignment` | containers x containers | caller-invoked with src/dst |

`run_all_checks(elems)` calls the first five. `check_container_alignment`
stays caller-invoked (requires arguments).

### CLI

```
diagram-testkit lint file.svg                          # auto-detect
diagram-testkit lint --format matplotlib file.svg      # override
diagram-testkit lint --cluster-align src=X,dst=Y f.svg
```

### File structure

```
src/diagram_testkit/
  __init__.py
  __main__.py
  model.py
  geometry.py
  extractors/
    __init__.py       # extract(), detect_format(), EXTRACTORS registry
    base.py           # DiagramExtractor protocol
    graphviz.py
    matplotlib.py
    excalidraw.py
  checks.py           # 6 format-agnostic functions
  cli.py
```

Deleted: `parser.py` (absorbed into `extractors/graphviz.py`).

## Migration steps

1. Add `model.py` with Format enum and dataclasses
2. Add `extractors/` package with protocol, three implementations, dispatcher
3. Rewrite `checks.py` to operate on `DiagramElements`
4. Update CLI and `__init__.py` exports, delete `parser.py`
5. Add Excalidraw fixtures, flesh out extractor

Each step keeps all existing tests green.
