import re
import xml.etree.ElementTree as ET
from pathlib import Path

from diagram_testkit.geometry import BBox, bbox_from_path_d
from diagram_testkit.model import ArrowPath, Container, DiagramElements, Shape, TextLabel

GLYPH_ADVANCE_ESTIMATE = 65.0
_MPL_GLYPH_CAP_HEIGHT = 72.9
_MPL_GLYPH_DESCENT = 1.42


def _strip_namespaces(root: ET.Element) -> None:
    for elem in root.iter():
        if "}" in elem.tag:
            elem.tag = elem.tag.split("}", 1)[1]


def _parse_transform(
    transform: str,
) -> tuple[float, float, float, float] | None:
    t_match = re.search(
        r"translate\(([\d.e+-]+)[\s,]+([\d.e+-]+)\)", transform
    )
    s_match = re.search(
        r"scale\(([\d.e+-]+)[\s,]+([\d.e+-]+)\)", transform
    )
    if not t_match or not s_match:
        return None
    tx = float(t_match.group(1))
    ty = float(t_match.group(2))
    sx = abs(float(s_match.group(1)))
    sy = abs(float(s_match.group(2)))
    return tx, ty, sx, sy


class MatplotlibExtractor:

    def extract(self, svg_path: Path) -> DiagramElements:
        tree = ET.parse(svg_path)
        root = tree.getroot()
        _strip_namespaces(root)

        axes_g = None
        for elem in root.iter():
            if elem.get("id", "").startswith("axes_"):
                axes_g = elem
                break
        if axes_g is None:
            return DiagramElements(source_path=svg_path)

        texts: list[TextLabel] = []
        arrows: list[ArrowPath] = []
        shapes: list[Shape] = []
        containers: list[Container] = []

        self._extract_axes_container(axes_g, containers)
        self._extract_texts(axes_g, texts)
        self._extract_patches(axes_g, arrows, shapes)

        return DiagramElements(
            texts=texts,
            arrows=arrows,
            shapes=shapes,
            containers=containers,
            source_path=svg_path,
        )

    def _extract_axes_container(
        self,
        axes_g: ET.Element,
        containers: list[Container],
    ) -> None:
        patch_2 = axes_g.find("*[@id='patch_2']")
        if patch_2 is None:
            return
        bg_path = patch_2.find("path")
        if bg_path is None:
            return
        bb = bbox_from_path_d(bg_path.get("d", ""))
        if bb:
            containers.append(Container(id="axes_1", bbox=bb))

    def _extract_texts(
        self,
        axes_g: ET.Element,
        texts: list[TextLabel],
    ) -> None:
        for g in axes_g:
            g_id = g.get("id", "")
            if not g_id.startswith("text_"):
                continue
            for idx, inner_g in enumerate(g.findall("g")):
                transform = inner_g.get("transform", "")
                parsed = _parse_transform(transform)
                if parsed is None:
                    continue
                tx, ty, sx, sy = parsed

                max_use_x = 0.0
                for use_el in inner_g.findall("use"):
                    ut = use_el.get("transform", "")
                    ut_match = re.search(r"translate\(([\d.e+-]+)", ut)
                    if ut_match:
                        max_use_x = max(max_use_x, float(ut_match.group(1)))

                x_min = tx
                x_max = tx + (max_use_x + GLYPH_ADVANCE_ESTIMATE) * sx
                y_min = ty - _MPL_GLYPH_CAP_HEIGHT * sy
                y_max = ty + _MPL_GLYPH_DESCENT * sy
                label = f"{g_id}" if idx == 0 else f"{g_id}[{idx}]"
                texts.append(TextLabel(
                    id=label,
                    bbox=BBox(x_min, y_min, x_max, y_max),
                ))

    def _extract_patches(
        self,
        axes_g: ET.Element,
        arrows: list[ArrowPath],
        shapes: list[Shape],
    ) -> None:
        for g in axes_g:
            g_id = g.get("id", "")
            if not g_id.startswith("patch_"):
                continue
            paths = g.findall("path")
            if not paths:
                continue
            first_path = paths[0]
            style = first_path.get("style", "")
            d = first_path.get("d", "")
            if not d:
                continue

            if "fill: none" in style:
                arrows.append(ArrowPath(id=g_id, path_d=d))
            elif "#ffffff" not in style:
                bb = bbox_from_path_d(d)
                if bb:
                    shapes.append(Shape(id=g_id, bbox=bb, path_d=d))
