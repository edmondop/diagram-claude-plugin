# Python Diagram Libraries

Specialized libraries for specific diagram types.

## diagrams (pip: diagrams) -- REQUIRES SYSTEM BINARY

Cloud/infra architecture with provider icon sets (AWS, GCP, K8s, Azure).
41k GitHub stars.

- `with Diagram(name, outformat="svg", show=False):`
- `with Cluster("name"):` for grouping
- Operators: `>>` (connect), `-` (undirected)
- Supports SVG, PNG, PDF, JPG output
- Example: `scripts/cloud-arch-diagrams.py` | Output: `scripts/output/cloud-arch-diagrams.svg`

## seqdiag (pip: seqdiag, setuptools<70, Pillow<10)

Sequence diagrams from text DSL. Auto-layout.

**WARNING**: Unmaintained since 2021. Requires pinned old dependencies.

- DSL: `actor -> actor [label = "msg"];` / `<--` for dashed returns
- Separators: `=== label ===`
- Parse + build + draw pattern
- Example: `scripts/sequence-seqdiag.py` | Output: `scripts/output/sequence-seqdiag.svg`

## blockdiag (pip: blockdiag, setuptools<70, Pillow<10)

Block/grid diagrams from text DSL. Auto-layout.

**WARNING**: Unmaintained since 2021. Same dependency constraints as seqdiag.

- DSL: `A -> B -> C;` with `group { }` for visual grouping
- Shapes: box, roundedbox, diamond, ellipse, note, cloud
- Example: `scripts/block-blockdiag.py` | Output: `scripts/output/block-blockdiag.svg`

## networkx + matplotlib (pip: networkx, matplotlib)

Graph-theory layouts. Best for DAGs with `topological_generations` +
`multipartite_layout`.

- `nx.DiGraph(edge_list)` -> compute layers -> `multipartite_layout`
- `nx.draw_networkx_nodes/edges/labels(G, pos, ax=ax)`
- `fig.savefig("file.svg", format="svg", bbox_inches="tight")`
- Use `matplotlib.use("Agg")` before importing pyplot in scripts
- Example: `scripts/network-networkx.py` | Output: `scripts/output/network-networkx.svg`

## erdantic (pip: erdantic) -- REQUIRES SYSTEM BINARY (graphviz)

ERD generation from Pydantic/dataclass/attrs models. Auto-discovers
relationships from type annotations.

- `erd.to_dot(Model)` returns DOT source (post-processable)
- `erd.draw(Model, out="file.svg")` for direct rendering
- Color entity headers via DOT post-processing: inject `bgcolor` on
  header `<td>` elements using regex on node definition lines
- On macOS with homebrew graphviz, may need:
  `CFLAGS="-I/opt/homebrew/opt/graphviz/include" LDFLAGS="-L/opt/homebrew/opt/graphviz/lib"`
- Example: `scripts/erd-erdantic.py` | Output: `scripts/output/erd-erdantic.svg`

## grandalf + drawsvg (pip: grandalf, drawsvg~=2.0)

Pure Python graph layout (Sugiyama algorithm) + SVG rendering. No system
dependencies. Best for block diagrams and network graphs when Graphviz
is not available.

- `grandalf.layouts.SugiyamaLayout` for hierarchical layout
- Combine with drawsvg for SVG output
- Supports cycles (unlike pure svgwrite manual layout)
- Examples: `scripts/network-grandalf.py`, `scripts/block-grandalf.py`

## Draw.io (native XML)

For Draw.io diagrams, prefer the **`drawio` skill** which generates
native mxGraphModel XML directly (no Python dependency). It supports
CLI export to PNG/SVG/PDF with embedded XML so the output stays
editable. See `skills/drawio/SKILL.md`.

The `drawpyo` Python library (`scripts/block-drawpyo.py`) is an
alternative when you need programmatic generation in a `uv run` script.
