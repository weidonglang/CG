#src/algoviz/backends/svg_svgwrite.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, List, Optional, Tuple

from ..core.timeline import Timeline
from ..core.drawops import Rect, Text


@dataclass
class SvgOptions:
    size: Tuple[int, int] = (640, 360)
    # None = 取最后一帧；>=0 = 指定索引
    frame: Optional[int] = None
    background: Optional[str] = None


def _esc(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def _rect_to_svg(r: Rect) -> str:
    style = []
    if r.fill:
        style.append(f'fill:{r.fill}')
    else:
        style.append('fill:none')
    stroke = r.stroke or 'none'
    style.append(f'stroke:{stroke}')
    # 关键属性：线宽不随缩放
    style.append('vector-effect:non-scaling-stroke')
    return (
        f'<rect x="{r.x:.2f}" y="{r.y:.2f}" width="{r.w:.2f}" height="{r.h:.2f}" '
        f'style="{";".join(style)}" />'
    )


def _text_to_svg(t: Text) -> str:
    attrs = [
        f'x="{t.x:.2f}"',
        f'y="{t.y:.2f}"',
        f'font-size="{t.size if t.size else 12}"',
        f'font-weight="{t.weight if t.weight else "normal"}"',
        f'fill="{t.fill if t.fill else "#000"}"',
        'text-anchor="middle"',
        'dominant-baseline="central"',
    ]
    return f'<text {" ".join(attrs)}>{_esc(t.content)}</text>'


def _ops_to_svg(ops: List[Any]) -> str:
    parts = []
    for op in ops:
        if isinstance(op, Rect):
            parts.append(_rect_to_svg(op))
        elif isinstance(op, Text):
            parts.append(_text_to_svg(op))
        # 其他形状可以在此扩展
    return "\n".join(parts)


def export_svg(
    scene: Any,
    tl: Timeline,
    outfile: str,
    frame_index: Optional[int] = None,
    options: Optional[SvgOptions] = None,
) -> None:
    """
    导出指定帧（或最后一帧）的 SVG。
    兼容两种指定帧的方式：
      - frame_index: 传 -1 表示最后一帧；>=0 表示具体索引
      - options.frame: None 表示最后一帧；>=0 表示具体索引
    两者同时提供时，以 frame_index 优先。
    """
    opt = options or SvgOptions()
    W, H = opt.size

    frames = tl.build_frames(scene)
    if not frames:
        raise RuntimeError("no frames to export")

    # 选择帧索引：frame_index 优先，其次 opt.frame，默认最后一帧
    if frame_index is not None:
        idx = len(frames) - 1 if int(frame_index) < 0 else int(frame_index)
    elif opt.frame is not None:
        idx = len(frames) - 1 if int(opt.frame) < 0 else int(opt.frame)
    else:
        idx = len(frames) - 1

    if idx < 0 or idx >= len(frames):
        raise IndexError(f"frame index out of range: {idx}")

    fr = frames[idx]

    # 让每个 actor 输出 DrawOps
    ops: List[Any] = []
    if hasattr(scene, "actors"):
        for name, st in fr.states.items():
            actor = scene.resolve_actor(name) if hasattr(scene, "resolve_actor") else scene.actors[name]
            if hasattr(actor, "draw"):
                ops.extend(actor.draw(st))
    else:
        # 如你的 Scene 有自定义接口，可在此分支适配
        for name, st in fr.states.items():
            actor = getattr(scene, name, None)
            if actor and hasattr(actor, "draw"):
                ops.extend(actor.draw(st))

    bg_rect = ""
    if opt.background:
        bg_rect = f'<rect x="0" y="0" width="{W}" height="{H}" fill="{opt.background}" />\n'

    # 根节点提供 viewBox（缩放友好）；保留默认 preserveAspectRatio
    svg = (
        f'<svg xmlns="http://www.w3.org/2000/svg" '
        f'width="{W}" height="{H}" viewBox="0 0 {W} {H}">\n'
        f'{bg_rect}{_ops_to_svg(ops)}\n'
        f'</svg>'
    )

    with open(outfile, "w", encoding="utf-8") as f:
        f.write(svg)
