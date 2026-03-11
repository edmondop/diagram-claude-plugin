---
name: generate-diagram
description: Use when generating diagrams, charts, or technical illustrations.
  Triggers on "create a diagram", "draw a flowchart", "generate an ERD",
  "make an architecture diagram", "sequence diagram", "state machine diagram",
  "block diagram", "pyramid diagram", "DAG", or any request for visual/graphical
  output in SVG or PNG format.
---

# Diagram Generation

Generate professional diagrams by routing each request to the best-fit
Python library. All diagrams are produced as `uv` inline scripts that
output SVG (or PNG where noted).

## Interaction Protocol

1. **Classify** the diagram type. If ambiguous, ask:
   > What kind of diagram?
   > - Flowchart / pipeline
   > - Architecture (generic boxes + arrows)
   > - Cloud/infra architecture (AWS, GCP, K8s icons)
   > - ERD (entities + relationships)
   > - Pyramid / stacked layers
   > - Sequence diagram
   > - Network / DAG
   > - Block diagram
   > - State machine / FSM

2. **Present library options** with trade-offs for that type. Ask the
   user to pick.

3. **Ask output path**: "Where should I save the script and SVG?"
   Default to current directory if the user doesn't specify.

4. **Check prerequisites** for Graphviz-dependent libraries:
   ```bash
   dot -V
   ```
   If not installed, show:
   - macOS: `brew install graphviz`
   - Ubuntu/Debian: `sudo apt-get install graphviz`
   - Fedora: `sudo dnf install graphviz`

5. **Generate** a `uv run`-compatible inline script. Run it. Open the SVG.

6. **Iterate** on user feedback.

## Routing Table

| Diagram type             | Primary                   | Alternative    | When to pick alternative                        |
|--------------------------|---------------------------|----------------|-------------------------------------------------|
| Flowchart / pipeline     | graphviz                  | schemdraw      | No Graphviz installed; simple linear flow        |
| Generic architecture     | graphviz                  | --             | --                                               |
| Cloud/infra architecture | diagrams (mingrammer)     | graphviz       | Don't need cloud provider icons                  |
| ERD                      | graphviz                  | --             | --                                               |
| Pyramid / stacked layers | svgwrite                  | drawsvg        | Prefer cleaner API, less precise control needed  |
| Sequence diagram         | seqdiag                   | svgwrite       | seqdiag for speed; svgwrite for full control     |
| Network / DAG            | networkx + matplotlib     | graphviz       | graphviz for DOT-style output                    |
| Block diagram            | blockdiag                 | schemdraw      | schemdraw for flow-style blocks                  |
| State machine / FSM      | graphviz                  | --             | --                                               |

## Library Quick Reference

### graphviz (pip: graphviz) -- REQUIRES SYSTEM BINARY

Thin Python wrapper around Graphviz DOT. Best for anything with
nodes + edges + auto-layout.

- `graphviz.Digraph` (directed) / `graphviz.Graph` (undirected)
- Engines: `dot` (hierarchical), `neato` (force-directed), `circo` (circular)
- Clusters via `with dot.subgraph(name="cluster_xxx"):`
- Record nodes for ERDs: `shape="record"`, `<port> field` syntax
- Output: `dot.render(filename, directory, cleanup=True)` or `dot.pipe(encoding="utf-8")`
- Example: `scripts/flowchart-graphviz.py`

### diagrams (pip: diagrams) -- REQUIRES SYSTEM BINARY

Cloud/infra architecture with provider icon sets (AWS, GCP, K8s, Azure).
41k GitHub stars.

- `with Diagram(name, outformat="svg", show=False):`
- `with Cluster("name"):` for grouping
- Operators: `>>` (connect), `-` (undirected)
- Supports SVG, PNG, PDF, JPG output
- Example: `scripts/cloud-arch-diagrams.py`

### svgwrite (pip: svgwrite)

Low-level SVG generation with full coordinate control. Best for custom
geometry (pyramids, stacked layers, custom illustrations).

- `svgwrite.Drawing(path, size, viewBox)`
- All geometry must be computed -- never hardcode coordinates
- Configuration constants at the top of the script
- Per-element nudges via `y_nudge`/`x_nudge` fields
- Example: `scripts/pyramid-svgwrite.py`

### drawsvg (pip: drawsvg~=2.0)

Nicer API than svgwrite for freeform SVG. Snake_case kwargs auto-convert
to SVG attributes (`fill_opacity` -> `fill-opacity`).

- `draw.Drawing(width, height)`
- `draw.Path()` with `.M()`, `.L()`, `.Z()` methods
- `d.save_svg("file.svg")`
- Note: v2 has y-axis pointing down (SVG convention)
- Example: `scripts/pyramid-drawsvg.py`

### schemdraw (pip: schemdraw)

Pure Python flowcharts via `schemdraw.flow` module. No system deps.

- Elements: `Start`, `Box`, `RoundBox`, `Decision`, `Data`, `Arrow`
- Positioning: `.drop("S")`, `.at(element.S).down()`
- Decision branches: `Decision(W="No", S="Yes")`
- Avoid `&`, `<`, `>` in labels (no XML escaping)
- Example: `scripts/flowchart-schemdraw.py`

### seqdiag (pip: seqdiag, setuptools<70, Pillow<10)

Sequence diagrams from text DSL. Auto-layout.

**WARNING**: Unmaintained since 2021. Requires pinned old dependencies.

- DSL: `actor -> actor [label = "msg"];` / `<--` for dashed returns
- Separators: `=== label ===`
- Parse + build + draw pattern
- Example: `scripts/sequence-seqdiag.py`

### blockdiag (pip: blockdiag, setuptools<70, Pillow<10)

Block/grid diagrams from text DSL. Auto-layout.

**WARNING**: Unmaintained since 2021. Same dependency constraints as seqdiag.

- DSL: `A -> B -> C;` with `group { }` for visual grouping
- Shapes: box, roundedbox, diamond, ellipse, note, cloud
- Example: `scripts/block-blockdiag.py`

### networkx + matplotlib (pip: networkx, matplotlib)

Graph-theory layouts. Best for DAGs with `topological_generations` +
`multipartite_layout`.

- `nx.DiGraph(edge_list)` -> compute layers -> `multipartite_layout`
- `nx.draw_networkx_nodes/edges/labels(G, pos, ax=ax)`
- `fig.savefig("file.svg", format="svg", bbox_inches="tight")`
- Use `matplotlib.use("Agg")` before importing pyplot in scripts
- Example: `scripts/network-networkx.py`

## Script Template

All scripts use `uv` inline metadata:

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

## Style Defaults

Unless the user specifies otherwise:

- **Font**: Helvetica, Arial, sans-serif
- **Stroke**: #333-#555, 1.2-2px
- **Fills**: muted material-design tones (not neon, not pastel candy)
- **Text**: black/#333 for labels, #666 for annotations
- **No gradients, no decorative elements**

## svgwrite Patterns (Custom Geometry)

For diagrams that need precise coordinate control (pyramids, custom shapes):

1. **Never write raw SVG by hand.** Always generate from a Python script.
2. **All geometry must be computed.** Write functions for intersections.
3. **Configuration at the top.** Dimensions, padding, colors, fonts, labels
   in module-level constants.
4. **Per-element nudges OK.** Add `y_nudge`/`x_nudge` to config when needed.
5. **Keep the script in the repo** next to the output SVG.
6. **Iterate visually.** Open the SVG, ask for feedback, adjust constants.
