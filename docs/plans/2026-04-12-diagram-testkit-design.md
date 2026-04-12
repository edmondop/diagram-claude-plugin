# Diagram Testkit — Design Document

## Goal

Extract the SVG quality test suite from `test_svg_quality.py` into an
installable Python package (`diagram-testkit`) that can be used in
pre-commit hooks and CI from any project.

## Constraints

- No existing behavior may be lost. Every fixture SVG that fails today
  must still fail after extraction.
- The package lives inside the plugin repo (not a separate repo) at
  `packages/diagram-testkit/`. Extract to its own repo later if needed.
- File-based CLI: `diagram-testkit lint file1.svg file2.svg`.

---

## Package Structure

```
diagram-claude-plugin/
  packages/diagram-testkit/
    src/diagram_testkit/
      __init__.py              # public API re-exports
      geometry.py              # BBox, bbox_from_svg_path, text_bbox, path_to_linestring
      parser.py                # ParsedSVG dataclass, parse_svg()
      checks.py                # 6 check functions + run_all_checks()
      cli.py                   # CLI entrypoint
    tests/
      fixtures/*.svg           # moved from current test_fixtures/
      test_parser.py           # parse_svg on graphviz / matplotlib / empty
      test_checks.py           # fixture-must-fail + per-check unit tests
      test_cli.py              # CLI smoke tests (exit 0 / exit 1)
    pyproject.toml
    README.md
  skills/generate-diagram/references/examples/
    test_svg_quality.py        # thin wrapper importing from diagram_testkit
    output/*.svg               # stays here
```

## Dependencies

| Dependency | Purpose | Replaces |
|:---|:---|:---|
| `svgelements` | Path/shape bbox, transform resolution, point sampling | `svgpathtools` |
| `shapely` | Bezier-rectangle intersection for arrow-crosses-text | (stays) |
| `pytest` | Test runner | (stays) |

**Dropped:** `svgpathtools` — `svgelements` handles path parsing and
`.bbox()` natively with zero hard dependencies.

**Text bbox heuristic stays.** No lightweight library handles text
measurement without a font engine. The `font_size * 0.6 * char_count`
approximation is battle-tested against 8 fixture SVGs.

## Module Design

### `geometry.py` (~80 lines)

```python
@dataclass
class BBox:
    x_min: float
    y_min: float
    x_max: float
    y_max: float

    def overlaps(self, other: BBox) -> bool
    def to_shapely(self) -> shapely.geometry.box
    cx: float       # property
    width: float    # property

def bbox_from_svg_path(d: str) -> BBox | None
    # Uses svgelements.Path(d).bbox() instead of regex

def text_bbox(elem: ET.Element) -> BBox | None
    # Same font_size * 0.6 * char_count heuristic

def path_to_linestring(d: str, samples: int = 200) -> LineString
    # Uses svgelements.Path for point sampling
```

### `parser.py` (~80 lines)

```python
@dataclass
class ParsedSVG:
    clusters: dict[str, BBox]
    cluster_labels: dict[str, tuple[str, BBox]]
    cluster_border_paths: dict[str, str]
    node_labels: list[tuple[str, BBox]]
    edge_labels: list[tuple[str, str, BBox]]
    edge_paths: list[tuple[str, str]]
    source_path: Path | None = None

def parse_svg(svg_path: Path) -> ParsedSVG
    # Strip namespaces, find graph0, extract clusters/nodes/edges
    # Returns empty ParsedSVG for non-Graphviz SVGs (matplotlib etc.)
```

### `checks.py` (~100 lines)

Six check functions, each `ParsedSVG -> list[str]`:

1. **`check_arrow_crosses_text()`** — arrow path intersects any text
   bbox. Uses shapely for curve-rectangle intersection.
2. **`check_text_crosses_border()`** — text bbox intersects cluster
   border. Uses shapely.
3. **`check_cluster_alignment(svg, *, src, dst, max_offset_ratio)`** —
   generalized from `check_data_layer_position`. Takes cluster names as
   parameters instead of hardcoding `cluster_backend`/`cluster_data`.
4. **`check_label_overlaps()`** — any two text labels overlap. Pure
   BBox rectangle math.
5. **`check_edge_label_distance(min_distance)`** — edge label too close
   to its own edge path.
6. **`check_matplotlib_annotation_overflow()`** — text annotations
   extend past the axes boundary.

`run_all_checks(svg)` runs checks 1, 2, 4, 5, 6 — the universal ones.
Check 3 (cluster alignment) requires project-specific cluster names,
so callers invoke it separately.

### `cli.py` (~60 lines)

```
diagram-testkit lint file1.svg file2.svg [--cluster-align src=X,dst=Y]
```

- Exit 0 = clean, exit 1 = errors.
- Prints errors per file.
- `--cluster-align` is optional; without it only universal checks run.

### `__init__.py` (~10 lines)

Re-exports: `parse_svg`, `ParsedSVG`, `BBox`, `run_all_checks`, and
individual check functions.

## Migration of Existing Code

After extraction, `test_svg_quality.py` becomes a thin wrapper (~30 lines):

```python
from diagram_testkit import parse_svg, run_all_checks, check_cluster_alignment

class TestOutputDiagram:
    def test_no_quality_errors(self, svg):
        errors = run_all_checks(svg)
        assert not errors

    def test_data_layer_centered(self, svg):
        errors = check_cluster_alignment(
            svg, src="cluster_backend", dst="cluster_data"
        )
        assert not errors
```

Fixture SVGs move from `skills/.../test_fixtures/` to
`packages/diagram-testkit/tests/fixtures/`.

### Development Installation

The plugin's development setup uses editable install:

```toml
[tool.uv.sources]
diagram-testkit = { path = "packages/diagram-testkit", editable = true }
```

### Consumer Installation

From git (e.g. for pkm repo):

```
pip install "diagram-testkit @ git+https://github.com/edmondop/diagram-claude-plugin#subdirectory=packages/diagram-testkit"
```

## Test Strategy

### `test_parser.py` (~60 lines)

- Graphviz SVG: clusters, nodes, edges populated
- Matplotlib SVG: empty ParsedSVG, source_path set
- Malformed/empty SVG: empty ParsedSVG, no crash

### `test_checks.py` (~80 lines)

- **`TestFixturesMustFail`** — parametrized over all `fixtures/*.svg`.
  Each known-bad SVG must fail at least one check. This is the safety
  net guaranteeing no behavior regression.
- One positive test per check using a known-good SVG.
- `test_cluster_alignment_with_custom_names` — verifies the generalized
  check works with arbitrary cluster names.

### `test_cli.py` (~40 lines)

- Clean SVG: exit code 0
- Bad fixture SVG: exit code 1 with error output
- Nonexistent file: exit code 1 with file-not-found message

## Migration Safety

Two-commit approach:

1. **Extract as-is** — move code into package structure with no logic
   changes. Run fixtures to confirm identical results.
2. **Swap internals** — replace `svgpathtools` with `svgelements`,
   generalize `check_data_layer_position`. Run fixtures again.

## Pre-commit Hook Integration

In `pyproject.toml`:

```toml
[project.scripts]
diagram-testkit = "diagram_testkit.cli:main"
```

In a consumer's `.pre-commit-config.yaml`:

```yaml
- repo: https://github.com/edmondop/diagram-claude-plugin
  rev: v0.4.0
  hooks:
    - id: diagram-testkit
      name: Lint SVG diagrams
      entry: diagram-testkit lint
      types: [svg]
      language: python
      additional_dependencies: [svgelements, shapely]
```

For CI, same file-based pattern:

```bash
for svg in path/to/diagrams/*.svg; do
  diagram-testkit lint "$svg"
done
```
