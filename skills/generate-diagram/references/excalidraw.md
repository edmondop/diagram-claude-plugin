# Excalidraw (hand-drawn sketch style)

Generate valid `.excalidraw` JSON files directly. No Python dependency.

## File Format

```json
{
  "type": "excalidraw",
  "version": 2,
  "source": "https://excalidraw.com",
  "elements": [],
  "appState": {
    "viewBackgroundColor": "#ffffff"
  },
  "files": {}
}
```

| Field      | Type   | Description                           |
| ---------- | ------ | ------------------------------------- |
| `type`     | string | Always `"excalidraw"`                 |
| `version`  | number | Schema version (currently `2`)        |
| `source`   | string | Origin URL                            |
| `elements` | array  | All diagram elements                  |
| `appState` | object | Canvas settings (background, etc.)    |
| `files`    | object | Binary files keyed by fileId (images) |

## Workflow

1. **Plan** - Choose diagram type, layout, colors
2. **Generate** - Create elements with proper structure
3. **Validate** - Check bindings and structure before writing
4. **Write** - Save as `.excalidraw` file, open with `open -a "Google Chrome"` or Excalidraw desktop

## Validation Checklist

Before writing a diagram, verify:

### Bindings

- Arrows connecting shapes have both `startBinding` and `endBinding` set
- Arrow `x,y` sits at the source shape's edge, not floating in space
- Shapes list connected arrows in their `boundElements` (bidirectional)
- Text labels have `containerId` pointing to their container
- Containers have `boundElements` referencing their text

### Polygons

- Polygon labels use `groupIds` (not `containerId`)
- Text positioned manually at polygon center
- **Polygons cannot have arrow bindings** - bind to grouped text label instead
- Polygon's `boundElements` must be `null`

### Layout

- Elements don't overlap unexpectedly
- Arrows route around shapes, not through them
- Minimum 40px between sibling elements
- All IDs are unique
- Label text matches actual names (verify spelling)

### Text

- Use standard font sizes: S (16), M (20), L (28), XL (36)
- Bound text: set `containerId`, `textAlign: "center"`, `verticalAlign: "middle"`
- Position bound text at container center; Excalidraw adjusts automatically

### Frames (presentations only)

- Frames are slides/artboards, not for grouping elements in a single diagram

## Detailed Element and Styling References

Load progressively based on need:

### Elements

| Reference                                              | Load When                            |
| ------------------------------------------------------ | ------------------------------------ |
| @references/excalidraw-elements/elements/shapes.md     | Using rectangles, diamonds, ellipses |
| @references/excalidraw-elements/elements/text.md       | Adding labels, fonts, text styling   |
| @references/excalidraw-elements/elements/linear.md     | Creating arrows, lines, bindings     |
| @references/excalidraw-elements/elements/freedraw.md   | Hand-drawn paths                     |
| @references/excalidraw-elements/elements/images.md     | Embedding images                     |
| @references/excalidraw-elements/elements/frames.md     | Slides/artboards for presentations   |
| @references/excalidraw-elements/elements/polygons.md   | Custom polygon shapes                |

### Styling

| Reference                                               | Load When                  |
| ------------------------------------------------------- | -------------------------- |
| @references/excalidraw-elements/styling/fill-stroke.md  | Fill patterns, strokes     |
| @references/excalidraw-elements/styling/colors.md       | Color palette selection    |
| @references/excalidraw-elements/styling/positioning.md  | Layout, alignment, spacing |
| @references/excalidraw-elements/styling/grouping.md     | Groups, z-ordering         |
