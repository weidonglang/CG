#src/algoviz/core/drawops.py
from __future__ import annotations
from dataclasses import dataclass
from typing import List, Literal, Tuple

Color = str  # hex like "#RRGGBB"
Point = Tuple[float, float]

@dataclass(frozen=True)
class DrawOp:
    kind: Literal["rect", "line", "text"]

@dataclass(frozen=True)
class Rect(DrawOp):
    x: float
    y: float
    w: float
    h: float
    fill: Color
    stroke: Color | None = None
    label: str | None = None

    def __init__(self, x: float, y: float, w: float, h: float,
                 fill: Color, stroke: Color | None = None,
                 label: str | None = None):
        object.__setattr__(self, "kind", "rect")
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)
        object.__setattr__(self, "w", w)
        object.__setattr__(self, "h", h)
        object.__setattr__(self, "fill", fill)
        object.__setattr__(self, "stroke", stroke)
        object.__setattr__(self, "label", label)

@dataclass(frozen=True)
class Line(DrawOp):
    p1: Point
    p2: Point
    stroke: Color
    width: float = 1.0

    def __init__(self, p1: Point, p2: Point, stroke: Color, width: float = 1.0):
        object.__setattr__(self, "kind", "line")
        object.__setattr__(self, "p1", p1)
        object.__setattr__(self, "p2", p2)
        object.__setattr__(self, "stroke", stroke)
        object.__setattr__(self, "width", width)

@dataclass(frozen=True)
class Text(DrawOp):
    x: float
    y: float
    content: str
    size: int = 12
    weight: Literal["normal", "bold"] = "normal"
    fill: Color = "#222222"

    def __init__(self, x: float, y: float, content: str,
                 size: int = 12, weight: Literal["normal", "bold"] = "normal",
                 fill: Color = "#222222"):
        object.__setattr__(self, "kind", "text")
        object.__setattr__(self, "x", x)
        object.__setattr__(self, "y", y)
        object.__setattr__(self, "content", content)
        object.__setattr__(self, "size", size)
        object.__setattr__(self, "weight", weight)
        object.__setattr__(self, "fill", fill)

DrawList = List[DrawOp]
