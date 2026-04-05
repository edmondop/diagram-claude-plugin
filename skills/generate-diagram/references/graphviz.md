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

3. **Use generous margins on nested clusters (20+).** Nested clusters
   with tight margins cause child content to clip the container border.
   Deeper nesting needs progressively larger margins:
   ```python
   # Outer cluster
   outer.attr(margin="24")
   # Inner cluster
   inner.attr(margin="20")
   # Innermost cluster
   innermost.attr(margin="14")
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
