from pathlib import Path

from ..model import DiagramElements


class ExcalidrawExtractor:

    def extract(self, svg_path: Path) -> DiagramElements:
        return DiagramElements(source_path=svg_path)
