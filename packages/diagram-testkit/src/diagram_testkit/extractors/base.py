from pathlib import Path
from typing import Protocol

from ..model import DiagramElements


class DiagramExtractor(Protocol):
    def extract(self, svg_path: Path) -> DiagramElements: ...
