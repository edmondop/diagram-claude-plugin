from diagram_testkit.geometry import BBox
from diagram_testkit.model import ArrowPath
from diagram_testkit.model import Container
from diagram_testkit.model import DiagramElements
from diagram_testkit.model import Format
from diagram_testkit.model import Shape
from diagram_testkit.model import TextLabel


def test_format_enum_has_three_members():
    assert Format.GRAPHVIZ.value == "graphviz"
    assert Format.MATPLOTLIB.value == "matplotlib"
    assert Format.EXCALIDRAW.value == "excalidraw"


def test_diagram_elements_defaults_to_empty_lists():
    elems = DiagramElements()
    assert elems.texts == []
    assert elems.arrows == []
    assert elems.shapes == []
    assert elems.containers == []
    assert elems.source_path is None


def test_text_label_owner_defaults_to_none():
    label = TextLabel(id="t1", bbox=BBox(0, 0, 10, 10))
    assert label.owner is None


def test_arrow_path_owner_defaults_to_none():
    arrow = ArrowPath(id="a1", path_d="M0,0 L10,10")
    assert arrow.owner is None


def test_shape_has_bbox_and_path():
    shape = Shape(id="s1", bbox=BBox(0, 0, 50, 50), path_d="M0,0 L50,0 L50,50 Z")
    assert shape.bbox.width == 50


def test_container_has_bbox():
    container = Container(id="c1", bbox=BBox(10, 20, 100, 200))
    assert container.bbox.cx == 55.0
