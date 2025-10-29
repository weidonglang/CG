from __future__ import annotations
from dataclasses import dataclass
from typing import List, Optional, Tuple
import svgwrite

from ..core.scene import Scene
from ..core.timeline import Timeline, Frame
from ..core.drawops import DrawOp, Rect, Line, Text as TextOp

@dataclass
class SvgOptions:
    size: Optional[Tuple[int, int]] = None      # (w,h) 像素；None=只用 viewBox
    background: str = "white"
    crisp_edges: bool = True                    # 矩形像素对齐
    non_scaling_stroke: bool = True             # 线条缩放不变粗细

def _emit_ops(dwg: svgwrite.Drawing, scene: Scene, ops: List[DrawOp], opt: SvgOptions) -> None:
    if opt.background:
        dwg.add(dwg.rect(insert=(0, 0), size=("100%", "100%"), fill=opt.background))

    for op in ops:
        if isinstance(op, Rect):
            attrs = dict(insert=(op.x, op.y), size=(op.w, op.h), fill=op.fill or "#000")
            if opt.crisp_edges:
                attrs["shape-rendering"] = "crispEdges"
            if op.stroke:
                attrs["stroke"] = op.stroke
            dwg.add(dwg.rect(**attrs))

        elif isinstance(op, Line):
            attrs = dict(start=op.p1, end=op.p2, stroke=op.stroke or "#000", stroke_width=op.width)
            if opt.non_scaling_stroke:
                attrs["vector-effect"] = "non-scaling-stroke"   # 线宽不随缩放变化
            dwg.add(dwg.line(**attrs))

        elif isinstance(op, TextOp):
            t = dwg.text(
                op.content,
                insert=(op.x, op.y),
                fill=op.fill or "#222",
                font_size=op.size,
                font_weight=("bold" if op.weight == "bold" else "normal"),
                text_anchor="middle",
                dominant_baseline="text-before-edge",           # 用上边缘对齐
            )
            dwg.add(t)

def export_svg(scene: Scene, timeline: Timeline, outfile: str, *, frame_index: int = -1, options: SvgOptions | None = None) -> None:
    opt = options or SvgOptions()
    frames = timeline.build_frames(scene)
    if not frames:
        raise ValueError("timeline has no frames")

    idx = (len(frames) - 1) if frame_index < 0 else frame_index
    if not (0 <= idx < len(frames)):
        raise IndexError("frame_index out of range")

    ops = scene.render(frames[idx].states)

    # 用 viewBox 对齐到场景坐标；可选的 size 控制像素尺寸
    # svgwrite 的 Drawing 支持 size 与 viewBox 混用。:contentReference[oaicite:1]{index=1}
    size = opt.size if opt.size else None
    dwg = svgwrite.Drawing(filename=outfile, size=size, viewBox=f"0 0 {scene.width} {scene.height}")
    _emit_ops(dwg, scene, ops, opt)
    dwg.save()
