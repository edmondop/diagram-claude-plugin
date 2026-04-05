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

1. **Edge labels overlap arrows by default.** Pad labels with spaces to
   shift them away from the arrow line:
   ```python
   dot.edge("a", "b", label="   HTTP   ")  # spaces push label right
   ```
   Graphviz centers labels on the edge midpoint. Leading/trailing spaces
   shift the rendered text without affecting layout computation.

2. **Cluster labels overlap node content when the cluster is narrow.**
   Fix by padding the cluster label or setting a minimum margin:
   ```python
   c.attr(label="  Behavior  ", margin="20")
   ```
   This forces the cluster to be wider, giving the label room.

3. **Use `compound=true` + `lhead`/`ltail` to point arrows at cluster
   borders** instead of individual nodes inside them:
   ```python
   dot.attr(compound="true")
   dot.edge("client", "api", lhead="cluster_backend")  # arrow stops at cluster border
   ```

4. **Force cluster ordering** with invisible edges between nodes in
   different clusters:
   ```python
   dot.edge("node_in_cluster_a", "node_in_cluster_c", style="invis")
   ```

5. **Avoid long multi-line labels** on edges — they create large bounding
   boxes that distort layout. Keep edge labels to 1-2 short lines max.
   Move detailed descriptions into node labels or annotations instead.
