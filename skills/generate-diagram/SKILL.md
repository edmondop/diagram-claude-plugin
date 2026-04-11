---
name: generate-diagram
description: Use when generating diagrams, charts, or technical illustrations.
  Triggers on "create a diagram", "draw a flowchart", "generate an ERD",
  "make an architecture diagram", "sequence diagram", "state machine diagram",
  "block diagram", "pyramid diagram", "DAG", "C4 diagram", "context map",
  "use case diagram", "activity diagram", "subdomain decomposition",
  "excalidraw", "hand-drawn diagram", "sketch diagram",
  or any request for visual/graphical output in SVG or PNG format.
allowed-tools: Read, Write, Edit, Bash, Glob, Grep
version: 0.2.0
---

# Diagram Generation

Generate professional diagrams by routing each request to the best-fit
tool. For UML, C4, and DDD diagram types, use **PlantUML** (text-based,
standard notation). For everything else, use Python libraries via `uv`
inline scripts. For editable hand-drawn diagrams, use **Excalidraw** JSON.

## Interaction Protocol

1. **Classify** the diagram type. If ambiguous, ask:
   > What kind of diagram?
   > - C4 (Context / Container / Component)
   > - UML Use Case
   > - UML Activity / BPMN-style workflow
   > - UML State Machine
   > - DDD Context Map
   > - Subdomain Decomposition (WBS)
   > - ERD (Conceptual or Logical)
   > - Flowchart / pipeline
   > - Architecture (generic boxes + arrows)
   > - Cloud/infra architecture (AWS, GCP, K8s icons)
   > - Pyramid / stacked layers
   > - Sequence diagram
   > - Network / DAG
   > - Block diagram
   > - Excalidraw (editable, hand-drawn sketch style)

2. **Pick the tool** from the routing table. For PlantUML types,
   do NOT offer Python alternatives — PlantUML is the only correct
   choice for standard notation. Skip to step 3.

3. **Ask output path**: "Where should I save the diagram?"
   Default to current directory if the user doesn't specify.

4. **Check prerequisites** based on the tool:

   For **PlantUML**:
   ```bash
   plantuml -version 2>/dev/null || docker image inspect plantuml/plantuml-cli:plantuml-cli-v1.0.1 >/dev/null 2>&1
   ```
   If neither is available, show:
   - macOS: `brew install plantuml`
   - Docker: `docker pull plantuml/plantuml-cli:plantuml-cli-v1.0.1`
   - **Do NOT fall back to a Python approximation.** Stop and ask the
     user to install one of the above.

   For **Graphviz-dependent** Python libraries:
   ```bash
   dot -V
   ```

5. **Load the relevant reference** for the tool you picked (see below).
   Generate the diagram following that reference.
   - PlantUML: write a `.puml` file, render with `plantuml -tsvg`
     or Docker. Open the SVG.
   - Python: write a `uv run`-compatible inline script. Run it. Open
     the SVG.
   - Excalidraw: write a `.excalidraw` JSON file. Open it.

6. **MANDATORY: Run quality validation** on every Graphviz-generated SVG
   before showing the result to the user. See
   [Quality Validation](#quality-validation) below. Do NOT skip this step.
   Do NOT present a diagram as finished until it passes validation.

7. **Iterate** on user feedback.

## Routing Table

### PlantUML (standard notation — no alternatives)

| Diagram type                    | Template                           |
|---------------------------------|------------------------------------|
| C4 Context Diagram              | `templates/c4-context.puml`        |
| C4 Container Diagram            | `templates/c4-container.puml`      |
| UML Use Case                    | `templates/use-case.puml`          |
| UML Use Case (detailed)         | `templates/use-case-detailed.puml` |
| UML Activity Diagram            | `templates/activity-diagram.puml`  |
| UML Activity (with decisions)   | `templates/activity-diagram-decision.puml` |
| UML State Machine               | `templates/state-machine.puml`     |
| DDD Context Map                 | `templates/context-map.puml`       |
| Subdomain Decomposition (WBS)   | `templates/subdomain-decomposition.puml` |
| Conceptual ERD                  | `templates/conceptual-erd.puml`    |
| Logical ERD                     | `templates/logical-erd.puml`       |
| Logical ERD (changelog pattern) | `templates/logical-erd-changelog.puml` |
| Logical ERD (users/roles)       | `templates/logical-erd-users.puml` |

**Reference:** @references/plantuml.md

### Python libraries (custom diagrams)

| Diagram type             | Primary                   | Alternative(s)              | When to pick alternative                          |
|--------------------------|---------------------------|-----------------------------|---------------------------------------------------|
| Flowchart / pipeline     | graphviz                  | schemdraw                   | No Graphviz installed; simple linear flow          |
| Generic architecture     | graphviz                  | grandalf + drawsvg          | No Graphviz installed; pure Python                 |
| Cloud/infra architecture | diagrams (mingrammer)     | graphviz                    | Don't need cloud provider icons                    |
| Pyramid / stacked layers | svgwrite                  | drawsvg                     | Prefer cleaner API, less precise control needed    |
| Sequence diagram         | seqdiag                   | svgwrite                    | seqdiag for speed; svgwrite for full control       |
| Network / graph (cyclic) | networkx + matplotlib     | grandalf + drawsvg          | Pure Python auto-layout without matplotlib         |
| DAG (acyclic pipeline)   | svgwrite                  | graphviz                    | graphviz for auto-layout; svgwrite for precision   |
| Block diagram            | grandalf + drawsvg        | blockdiag, schemdraw, draw.io | blockdiag for DSL; schemdraw for flow; draw.io for editable |
| Subdomain -> BC mapping  | drawsvg                   | --                            | `@references/examples/subdomain-bc-mapping.py` — bipartite layout |

**References:**
- @references/graphviz.md — graphviz Python wrapper + layout tips
- @references/python-svg-libraries.md — svgwrite, drawsvg, schemdraw + coordinate patterns
- @references/python-diagram-libraries.md — diagrams, seqdiag, blockdiag, networkx, erdantic, grandalf, draw.io

### Excalidraw (editable, hand-drawn sketch)

| Diagram type             | Tool                      |
|--------------------------|---------------------------|
| Any (editable, sketch)   | Excalidraw JSON           |

**Reference:** @references/excalidraw.md

### Draw.io (editable, precise)

| Diagram type             | Tool                      |
|--------------------------|---------------------------|
| Any (editable, precise)  | draw.io (drawio skill)    |

## Example Scripts

Working examples for each diagram type are in `@references/examples/`.
Read the relevant example before generating a new diagram:

| Diagram type             | Example script                              |
|--------------------------|---------------------------------------------|
| Architecture (generic)   | `@references/examples/architecture-graphviz.py` |
| Block diagram (blockdiag)| `@references/examples/block-blockdiag.py`       |
| Block diagram (schemdraw)| `@references/examples/block-schemdraw.py`       |
| Cloud/infra architecture | `@references/examples/cloud-arch-diagrams.py`   |
| ERD                      | `@references/examples/erd-graphviz.py`           |
| Flowchart (graphviz)     | `@references/examples/flowchart-graphviz.py`     |
| Flowchart (schemdraw)    | `@references/examples/flowchart-schemdraw.py`    |
| FSM / state machine      | `@references/examples/fsm-graphviz.py`           |
| Network (graphviz)       | `@references/examples/network-graphviz.py`       |
| Network (networkx)       | `@references/examples/network-networkx.py`       |
| Pyramid (drawsvg)        | `@references/examples/pyramid-drawsvg.py`        |
| Pyramid (svgwrite)       | `@references/examples/pyramid-svgwrite.py`       |
| Sequence (seqdiag)       | `@references/examples/sequence-seqdiag.py`       |
| Sequence (svgwrite)      | `@references/examples/sequence-svgwrite.py`      |
| Subdomain -> BC mapping  | `@references/examples/subdomain-bc-mapping.py`   |

## Script Template (Python libraries only)

All Python scripts use `uv` inline metadata:

```python
# /// script
# requires-python = ">=3.10"
# dependencies = ["library-name"]
# ///
"""Description of what this diagram shows."""
from pathlib import Path
# ... imports ...

def main() -> None:
    Path("output").mkdir(exist_ok=True)
    # ... build diagram ...
    # ... save to output/ ...
    print(f"Saved: output/filename.svg")

if __name__ == "__main__":
    main()
```

## Quality Validation

**This is a hard requirement, not a suggestion.** Every Graphviz-generated
SVG must pass `test_svg_quality.py` before the diagram is considered done.
Graphviz auto-layout frequently produces overlapping text, arrows crossing
labels, and nodes bleeding outside cluster borders — problems that are
invisible when you only look at the DOT source but immediately visible in
the rendered SVG.

### What the validator checks

| Check | What it detects |
|-------|----------------|
| Arrow crosses text | An edge path (Bezier curve) intersects a cluster label, edge label, or node label that does not belong to that edge |
| Text crosses border | A text label overlaps a cluster border path |
| Label overlaps | Two text labels occupy the same bounding box |
| Layout centering | Clusters that should be centered are not drifting off-axis |

### How to run

```bash
# Validate a single SVG (CLI mode — no pytest needed at runtime)
uv run @references/examples/test_svg_quality.py output/my-diagram.svg
```

Output on success:
```
Parsed: 3 clusters, 12 nodes, 5 edge labels
✓ All checks passed!
```

Output on failure:
```
Parsed: 3 clusters, 12 nodes, 5 edge labels

ERRORS (2):
  ✘ Arrow apply->target_token crosses node 'target_token'
  ✘ node 'enc_secrets' crosses cluster_repo border
```

### When validation fails — how to fix

| Error | Common fix |
|-------|-----------|
| Arrow crosses cluster/node label | Increase `ranksep`, `nodesep`, or add `minlen` on the offending edge. Move annotation nodes to a different rank. |
| Node crosses cluster border | Add `margin="16"` or `margin="20"` to the cluster `c.attr()`. |
| Arrow crosses destination node text | Increase node `margin` (e.g., `"0.3,0.2"`) so the text bounding box is well inside the node border. |
| Labels overlap | Shorten labels, increase `nodesep`, or use `rank="same"` constraints. |

Re-generate the SVG and re-run validation after every fix. Do not
guess — the validator uses proper Bezier curve sampling and Shapely
geometric intersection, which is more accurate than visual inspection.

### Scope

The validator parses Graphviz SVG structure (it looks for a `graph0`
group element). It does **not** apply to:
- svgwrite / drawsvg diagrams (no `graph0` group)
- PlantUML diagrams
- Excalidraw files

For non-Graphviz diagrams, visual inspection is the only verification.

### Source linting (edge label padding)

**Also a hard requirement.** Every graphviz diagram script must pass
`lint_diagram_source.py` before the diagram is considered done.

On vertical edges, graphviz places `label` text flush against the arrow
line — making it hard to read. Every edge `label`, `xlabel`, `headlabel`,
and `taillabel` must have at least 2 spaces of padding on each side of
every line. For multi-line labels, each line must be padded independently.

```bash
# Lint a single script
uv run @references/examples/lint_diagram_source.py my-diagram.py

# Lint all scripts in a directory
uv run @references/examples/lint_diagram_source.py docs/diagrams/
```

The linter uses Python's AST to find `.edge()` calls and check string
literal arguments. It only scans files that `import graphviz`.

```python
# BAD — label hugs the arrow line
dot.edge("a", "b", label="shared\nsecret")

# GOOD — padded with spaces
dot.edge("a", "b", label="  shared  \n  secret  ")
```

## Style Defaults

Unless the user specifies otherwise:

- **Font**: Helvetica, Arial, sans-serif
- **Stroke**: #333-#555, 1.2-2px
- **Fills**: material-design 300/400 weight tones (soft, easy on the eyes).
  **Avoid 700-900 weight fills** (`#C62828`, `#1a5ad7`, `#2E7D32`, `#6A1B9A`)
  — they are too saturated for large node/cluster fills and strain the reader's
  eyes. Use lighter variants instead:
  - Red: `#E57373` (300) instead of `#C62828` (800)
  - Blue: `#5C6BC0` (400) or `#90CAF9` (200) instead of `#1a5ad7`
  - Green: `#66BB6A` (400) or `#81C784` (300) instead of `#2E7D32`
  - Purple: `#BA68C8` (300) instead of `#6A1B9A`
  - Reserve 700+ weights only for small accents (thin borders, edge colors)
- **Text**: `#333` for labels on light fills, white for labels on 400+ weight
  fills. `#555` for annotations
- **No gradients, no decorative elements**
- **PlantUML theme**: transparent background, `#5C6BC0` borders, `#0b2147` text

### Cluster Labels and Borders (Graphviz)

Always set `labeljust="l"` on every cluster. Centered labels (the
default) sit in the path of vertical arrows entering the container from
above. Left-aligning moves the label to the top-left corner, out of the
arrow path. This should be applied unconditionally to all clusters.

When edges cross cluster borders, add `minlen="2"` to give the arrow,
xlabel, and border enough vertical space. Do NOT increase cluster
`margin` for this — margin adds internal padding, which pushes the
border *closer* to external nodes and makes the problem worse.

### Color Restraint

Limit each diagram to **black + one accent color**. Multiple accent
colors (e.g., blue boxes, orange borders, green highlights, red warnings)
create visual noise that distracts from the content. When comparing two
states (bug vs fix, before vs after), use separate diagrams with
different single accents (e.g., red for the bug, green for the fix)
rather than mixing both colors in one diagram.

### Font Sizing for Documentation

Default font sizes in diagram libraries are often too small when the
diagram is embedded in documentation. Bump all text up ~2px from library
defaults for readability:

- **Titles**: 14-16px, bold
- **Node / participant labels**: 11-12px, bold
- **Arrow / edge labels**: 11px, bold (especially monospace labels like
  function calls — normal weight monospace is hard to read at small sizes)
- **Callout / annotation text**: 10px, weight 500
- **Secondary text** (separators, hints): 10px, use #555 not #888 for
  sufficient contrast

### Complexity Reduction

When a diagram has repeated similar elements (e.g., multiple workers,
multiple servers), show **one expanded example** with full detail and
collapse the rest into a single placeholder node (e.g.,
`"Worker 2 ... Worker N"` with dashed style). This conveys the pattern
without cluttering the diagram.

### Split Over Combine

When comparing two states or scenarios (bug vs fix, before vs after),
prefer **two separate diagrams** over one combined side-by-side diagram.
Combined diagrams double the visual complexity and force the reader to
parse both scenarios simultaneously.

## SVG Quality Validation (Graphviz)

After generating a Graphviz diagram, validate the SVG with the quality
test suite. The tests use `svgpathtools` for proper Bezier curve sampling
and `shapely` for geometric intersection tests.

```bash
# Run all quality checks against a rendered SVG
uv run --with svgpathtools --with shapely --with pytest -- \
  pytest references/examples/test_svg_quality.py -v

# Quick CLI check against a specific SVG
uv run --with svgpathtools --with shapely --with pytest -- \
  python references/examples/test_svg_quality.py path/to/diagram.svg
```

**Critical rules enforced:**

1. **No arrow crosses any text** — arrow Bezier curves must not pass
   through cluster labels, edge labels, or node labels
2. **No text crosses any border** — no text element may overlap a
   cluster border line
3. **No label overlaps** — no two text elements may overlap each other

**Anti-pattern fixtures** in `references/examples/test_fixtures/` show
common layout problems that the tests catch:

| Fixture | Anti-pattern |
|---|---|
| `architecture-arrow-crosses-label.svg` | Arrows through cluster labels (naive regex missed these) |
| `architecture-arrow-crosses-data-layer.svg` | Bezier curve crosses label (only caught by svgpathtools) |
| `architecture-centered-labels.svg` | Centered labels + rainbow colors + off-center data layer |
| `labels-overlap.svg` | Multiple edge labels overlapping each other |
| `text-on-border.svg` | Edge label sitting on a cluster border |
| `rainbow-colors.svg` | Multi-color clusters with centered labels colliding with arrows |
| `data-layer-off-center.svg` | Data cluster positioned far from backend |

When iterating on diagram layout, use the test suite as an objective
function — keep adjusting the Graphviz source until all checks pass.

**Fix patterns for common failures:**
- Arrow crosses cluster label → add invisible spacer node to widen
  cluster, pushing the left-justified label away from arrow entry points
- Text crosses border → remove `xlabel` from cross-connection edges,
  or add `minlen` to create clearance
- Labels overlap → increase `nodesep`, use `constraint="false"` on
  cross-connections, or remove redundant labels

## Additional References

- @references/bounded-context-naming.md — rules for naming bounded contexts in DDD diagrams
