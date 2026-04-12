from dataclasses import dataclass
from dataclasses import field
from enum import Enum
from pathlib import Path

from diagram_testkit.geometry import BBox


class Format(Enum):
    GRAPHVIZ = "graphviz"
    MATPLOTLIB = "matplotlib"
    EXCALIDRAW = "excalidraw"


@dataclass
class TextLabel:
    id: str
    bbox: BBox
    owner: str | None = None


@dataclass
class ArrowPath:
    id: str
    path_d: str
    owner: str | None = None


@dataclass
class Shape:
    id: str
    bbox: BBox
    path_d: str


@dataclass
class Container:
    id: str
    bbox: BBox


@dataclass
class DiagramElements:
    texts: list[TextLabel] = field(default_factory=list)
    arrows: list[ArrowPath] = field(default_factory=list)
    shapes: list[Shape] = field(default_factory=list)
    containers: list[Container] = field(default_factory=list)
    source_path: Path | None = None
