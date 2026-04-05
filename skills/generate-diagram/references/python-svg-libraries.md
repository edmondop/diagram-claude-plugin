# Python SVG Libraries

Libraries for direct SVG generation with coordinate control.

## svgwrite (pip: svgwrite)

Low-level SVG generation with full coordinate control. Best for custom
geometry (pyramids, stacked layers, custom illustrations).

- `svgwrite.Drawing(path, size, viewBox)`
- All geometry must be computed -- never hardcode coordinates
- Configuration constants at the top of the script
- Per-element nudges via `y_nudge`/`x_nudge` fields

### svgwrite Examples

| Diagram type | Script | Output |
|---|---|---|
| Pyramid | `scripts/pyramid-svgwrite.py` | `scripts/output/pyramid-svgwrite.svg` |
| Sequence | `scripts/sequence-svgwrite.py` | `scripts/output/sequence-svgwrite.svg` |

## drawsvg (pip: drawsvg~=2.0)

Nicer API than svgwrite for freeform SVG. Snake_case kwargs auto-convert
to SVG attributes (`fill_opacity` -> `fill-opacity`).

- `draw.Drawing(width, height)`
- `draw.Path()` with `.M()`, `.L()`, `.Z()` methods
- `d.save_svg("file.svg")`
- Note: v2 has y-axis pointing down (SVG convention)

### drawsvg Examples

| Diagram type | Script | Output |
|---|---|---|
| Pyramid | `scripts/pyramid-drawsvg.py` | `scripts/output/pyramid-drawsvg.svg` |
| Subdomain-BC mapping | `scripts/subdomain-bc-mapping.py` | `scripts/output/subdomain-bc-mapping.svg` |

## schemdraw (pip: schemdraw)

Pure Python flowcharts via `schemdraw.flow` module. No system deps.

- Elements: `Start`, `Box`, `RoundBox`, `Decision`, `Data`, `Arrow`
- Positioning: `.drop("S")`, `.at(element.S).down()`
- Decision branches: `Decision(W="No", S="Yes")`
- Avoid `&`, `<`, `>` in labels (no XML escaping)

### schemdraw Examples

| Diagram type | Script | Output |
|---|---|---|
| Flowchart | `scripts/flowchart-schemdraw.py` | `scripts/output/flowchart-schemdraw.svg` |
| Block diagram | `scripts/block-schemdraw.py` | `scripts/output/block-schemdraw.svg` |

## svgwrite Patterns (Custom Geometry)

For diagrams that need precise coordinate control (pyramids, custom shapes):

1. **Never write raw SVG by hand.** Always generate from a Python script.
2. **All geometry must be computed.** Write functions for intersections.
3. **Configuration at the top.** Dimensions, padding, colors, fonts, labels
   in module-level constants.
4. **Per-element nudges OK.** Add `y_nudge`/`x_nudge` to config when needed.
5. **Keep the script in the repo** next to the output SVG.
6. **Iterate visually.** Open the SVG, ask for feedback, adjust constants.
7. **Edge labels must not overlap arrows.** When placing text near an
   arrow, offset the label by at least 8-12px perpendicular to the arrow
   direction. For horizontal arrows, place labels above (`my - 10`).
   For vertical arrows, place labels to the right (`mx + 10`). Never
   place a label at the exact midpoint of an arrow without an offset.
8. **Container labels need breathing room.** When a cluster/group label
   is short (e.g., "State"), pad the container with extra margin so the
   label doesn't visually collide with the child nodes inside it.
9. **Arrows to curved shapes need per-edge nudging.** When arrows target
   elliptical shapes (cylinders, ellipses), the visual border varies by
   where the arrow hits. Arrows hitting the side of an ellipse need more
   inward nudge than arrows hitting the center. Compute separate
   `target_top`/`target_bot` values and add 5-8px nudge toward the shape
   center. Always render and visually verify — math alone won't match
   perception.
10. **Labels on vertical arrows go to the side, not centered.** A label
    centered on a vertical arrow's midpoint sits directly on the line.
    Use `label_dx=+-40` to push it left or right. For diagonal arrows,
    offset labels perpendicular to the line with both `label_dx` and
    `label_dy` — typically 15-20px in each direction.
11. **svgwrite `style=""` (empty string) is invalid.** When building
    optional style attributes (e.g., dashed lines), use a dict and only
    add the `style` key when the value is non-empty:
    ```python
    extra = {"style": "stroke-dasharray:4,3"} if dashed else {}
    dwg.add(dwg.line(..., **extra))
    ```
12. **Cylinder shapes need generous height.** A cylinder's top ellipse
    overlaps the label text if `ry` is too small or the body too short.
    Use `ry >= 10` and `h >= 70` for readable cylinders. Place the label
    text below center (`cy + 2`) to clear the top ellipse lid.
13. **Symmetry through equal spacing.** In multi-row layouts, ensure the
    vertical gap between the center element and the rows above/below it
    is roughly equal. Visually verify and adjust — the bottom row often
    needs to be pushed 10-20px further down than the math suggests.
