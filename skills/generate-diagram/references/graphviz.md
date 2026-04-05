# Graphviz (Python wrapper)

**pip**: `graphviz` — REQUIRES SYSTEM BINARY (`dot`)

Thin Python wrapper around Graphviz DOT. Best for anything with
nodes + edges + auto-layout.

- `graphviz.Digraph` (directed) / `graphviz.Graph` (undirected)
- Engines: `dot` (hierarchical), `neato` (force-directed), `circo` (circular)
- Clusters via `with dot.subgraph(name="cluster_xxx"):`
- Record nodes for ERDs: `shape="record"`, `<port> field` syntax
- Output: `dot.render(filename, directory, cleanup=True)` or `dot.pipe(encoding="utf-8")`

## Examples

| Diagram type | Script | Output |
|---|---|---|
| Flowchart | `scripts/flowchart-graphviz.py` | `scripts/output/flowchart-graphviz.svg` |
| Architecture | `scripts/architecture-graphviz.py` | `scripts/output/architecture-graphviz.svg` |
| ERD | `scripts/erd-graphviz.py` | `scripts/output/erd-graphviz.svg` |
| FSM / State machine | `scripts/fsm-graphviz.py` | `scripts/output/fsm-graphviz.svg` |
| Network graph | `scripts/network-graphviz.py` | `scripts/output/network-graphviz.svg` |

## Label & Layout Tips

1. **Use `xlabel` instead of `label` for edge labels near vertical arrows.**
   The default `label` places text at the edge midpoint, which sits directly
   on vertical arrows. `xlabel` places it beside the arrow:
   ```python
   dot.edge("a", "b", xlabel="  HTTP  ")   # beside the arrow
   dot.edge("a", "b", label="  HTTP  ")    # ON the arrow (bad for vertical)
   ```
   Note: `xlabel` requires `forcelabels="true"` in graph attributes.
   Pad with leading/trailing spaces to push the label further from the line.

2. **Always left-align cluster labels with `labeljust="l"`.** Graphviz
   centers cluster labels by default. In top-down (`rankdir="TB"`) layouts,
   arrows entering a cluster from above pass through the horizontal center
   — exactly where the centered label sits. Left-aligning the label pushes
   it out of the arrow path:
   ```python
   # BAD: centered label collides with vertical arrows entering the cluster
   c.attr(label="Python Process (one per worker)")

   # GOOD: left-aligned label stays clear of center arrows
   c.attr(label="Python Process (one per worker)", labeljust="l")
   ```
   Apply `labeljust="l"` to **every cluster** in the diagram, not just
   the ones that visibly overlap — it prevents the problem before it appears.
   Combine with generous margins (see tip 3) for best results.

3. **Cluster `margin` adds padding *inside* the container.** A larger
   margin pushes the border further from the internal nodes — but that
   means the border moves *closer* to the next external node. Do NOT
   increase margins to fix tight spacing between a container border and
   an outside node; that makes it worse. Use `minlen` on border-crossing
   edges instead (see tip 9). Keep margins moderate (14-24) for internal
   breathing room:
   ```python
   outer.attr(margin="24")   # outermost cluster
   middle.attr(margin="20")  # middle cluster
   inner.attr(margin="14")   # innermost cluster
   ```

4. **Cluster labels overlap node content when the cluster is narrow.**
   Fix by padding the cluster label or setting a minimum margin:
   ```python
   c.attr(label="  Behavior  ", margin="20")
   ```
   This forces the cluster to be wider, giving the label room.

5. **Use `compound=true` + `lhead`/`ltail` to point arrows at cluster
   borders** instead of individual nodes inside them:
   ```python
   dot.attr(compound="true")
   dot.edge("client", "api", lhead="cluster_backend")  # arrow stops at cluster border
   ```

6. **Force cluster ordering** with invisible edges between nodes in
   different clusters:
   ```python
   dot.edge("node_in_cluster_a", "node_in_cluster_c", style="invis")
   ```

7. **Avoid long multi-line labels** on edges — they create large bounding
   boxes that distort layout. Keep edge labels to 1-2 short lines max.
   Move detailed descriptions into node labels or annotations instead.

8. **Increase `nodesep` for wider layouts.** When nodes in a cluster are
   horizontally cramped, increase `nodesep` (default 0.25) in graph
   attributes:
   ```python
   dot.attr(nodesep="0.7")  # more horizontal space between siblings
   ```

9. **Use `minlen` on edges that cross container borders.** When an arrow
   exits a cluster, the cluster border, the xlabel, and the target node
   all compete for the same tight vertical gap. Increasing `ranksep`
   fixes this but wastes space on *every* rank transition. Instead, add
   `minlen="2"` only on edges that cross a container border:
   ```python
   # Crosses Gunicorn cluster border — needs extra space
   dot.edge("greenlet", "registry", xlabel="  session_factory()  ", minlen="2")

   # Stays inside the same cluster — default distance is fine
   dot.edge("registry", "session", xlabel="  returns Session  ")
   ```
   This doubles the rank distance for that specific edge while keeping
   all other transitions compact. Apply to every edge whose source and
   target are in different clusters.

10. **Use invisible spacer nodes to widen clusters.** When `labeljust="l"`
    labels still overlap with arrows entering from the top, the cluster
    isn't wide enough. Add an invisible node declared *before* visible
    nodes — DOT places it leftmost, extending the cluster border left
    so the label sits clear of arrow paths:
    ```python
    with dot.subgraph(name="cluster_gateway") as c:
        c.attr(label="API Gateway", labeljust="l", margin="30", ...)
        # Left spacer — pushes cluster border left of arrow entry points
        c.node("gw_pad", label="", style="invis",
               fixedsize="true", width="1.2", height="0.01")
        c.node("gateway", label="Kong Gateway")
        c.node("auth", label="Auth Service")
    ```

## Automated Quality Validation

After rendering, validate the SVG with the test suite:

```bash
uv run --with svgpathtools --with shapely --with pytest -- \
  pytest references/examples/test_svg_quality.py -v
```

The tests use proper Bezier curve sampling (not just control points)
to detect arrows crossing text and text crossing cluster borders.
See `references/examples/test_fixtures/` for anti-pattern examples.
