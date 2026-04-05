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
3. **Color palette: black + one accent.** Define `BLACK` and one `ACCENT`
   color as constants. Use black for all structural elements (arrows,
   boxes, lifelines) and the accent only for highlights. Multiple accent
   colors create visual noise. When comparing scenarios (bug vs fix),
   generate separate SVGs with different accents rather than mixing colors.
4. **Configuration at the top.** Dimensions, padding, colors, fonts, labels
   in module-level constants.
5. **Per-element nudges OK.** Add `y_nudge`/`x_nudge` to config when needed.
6. **Keep the script in the repo** next to the output SVG.
7. **Iterate visually.** Open the SVG, ask for feedback, adjust constants.
8. **Edge labels must not overlap arrows.** When placing text near an
   arrow, offset the label by at least 8-12px perpendicular to the arrow
   direction. For horizontal arrows, place labels above (`my - 10`).
   For vertical arrows, place labels to the right (`mx + 10`). Never
   place a label at the exact midpoint of an arrow without an offset.
9. **Container labels need breathing room.** When a cluster/group label
   is short (e.g., "State"), pad the container with extra margin so the
   label doesn't visually collide with the child nodes inside it.
10. **Arrows to curved shapes need per-edge nudging.** When arrows target
    elliptical shapes (cylinders, ellipses), the visual border varies by
    where the arrow hits. Arrows hitting the side of an ellipse need more
    inward nudge than arrows hitting the center. Compute separate
    `target_top`/`target_bot` values and add 5-8px nudge toward the shape
    center. Always render and visually verify — math alone won't match
    perception.
11. **Labels on vertical arrows go to the side, not centered.** A label
    centered on a vertical arrow's midpoint sits directly on the line.
    Use `label_dx=+-40` to push it left or right. For diagonal arrows,
    offset labels perpendicular to the line with both `label_dx` and
    `label_dy` — typically 15-20px in each direction.
12. **svgwrite `style=""` (empty string) is invalid.** When building
    optional style attributes (e.g., dashed lines), use a dict and only
    add the `style` key when the value is non-empty:
    ```python
    extra = {"style": "stroke-dasharray:4,3"} if dashed else {}
    dwg.add(dwg.line(..., **extra))
    ```
13. **Cylinder shapes need generous height.** A cylinder's top ellipse
    overlaps the label text if `ry` is too small or the body too short.
    Use `ry >= 10` and `h >= 70` for readable cylinders. Place the label
    text below center (`cy + 2`) to clear the top ellipse lid.
14. **Symmetry through equal spacing.** In multi-row layouts, ensure the
    vertical gap between the center element and the rows above/below it
    is roughly equal. Visually verify and adjust — the bottom row often
    needs to be pushed 10-20px further down than the math suggests.

## Sequence Diagram Patterns (svgwrite)

When building sequence diagrams with svgwrite:

1. **Arrow labels near the source, not centered.** Centering a label
   between source and target columns causes it to cross intermediate
   lifelines. Instead, position labels just past the source lifeline
   (`x1 + 10`) with `text_anchor="start"`. This keeps labels clear of
   all intermediate vertical lines, regardless of arrow direction.

2. **Widen the diagram for return labels.** Return arrows (right-to-left)
   need labels to the right of the rightmost lifeline — outside the flow
   area. Add extra right margin (150-240px) beyond the last column to
   fit these labels without overflow.

3. **No boxes on inline annotations.** Bordered note boxes around text
   like "user.balance = 500" add visual clutter with no benefit. Use
   plain text annotations instead. Reserve bordered shapes for callout
   notes that sit outside the main flow.

4. **Explanatory callouts as sticky notes outside the flow.** Instead of
   inline editorial notes ("SAME session!", "data corruption!"), draw a
   single sticky note (folded-corner rectangle) to the side of the
   diagram with a dashed connector to the relevant arrow. This keeps the
   sequence flow clean and puts the explanation where it doesn't compete
   with the arrows.

5. **Compute callout note width from text, never hardcode.** Hardcoded
   widths break when text changes. Compute from the longest line:
   ```python
   font_size = 10  # px
   max_chars = max(len(line) for line in callout_lines)
   # Helvetica/sans-serif: ~0.55 × font_size per character
   # Courier/monospace: ~0.6 × font_size per character
   note_w = int(max_chars * font_size * 0.55) + 20  # 20px padding
   ```
   Then size `RIGHT_EXTRA` (the diagram's right margin) to fit:
   `RIGHT_EXTRA = note_w + 40` (20px gap from lifeline + 20px right pad).

6. **Bold monospace at 11px+ for arrow labels.** Default 10px normal
   weight is too thin for documentation. Use `font_size="11px"` and
   `font_weight="bold"` on all arrow labels. Callout text should be at
   least 10px with weight 500.

7. **Separator text at #555, not #888.** Light gray separators
   ("Greenlet A yields...") become unreadable in documentation. Use
   `#555555` for sufficient contrast on white backgrounds.
