from pathlib import Path

from diagram_testkit.model import DiagramElements


class ExcalidrawExtractor:

    def extract(self, svg_path: Path) -> DiagramElements:
        return DiagramElements(source_path=svg_path)
