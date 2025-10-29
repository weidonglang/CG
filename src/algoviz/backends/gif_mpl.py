from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple, Optional
import numpy as np
import imageio.v3 as iio
from PIL import Image  # 仅测试/调试时可能用到

from matplotlib.figure import Figure
from matplotlib.patches import Rectangle
from matplotlib.backends.backend_agg import FigureCanvasAgg

from ..core.scene import Scene
from ..core.timeline import Timeline, Frame
from ..core.drawops import DrawOp, Rect, Line, Text as TextOp




@dataclass
class GifOptions:
    size: Tuple[int, int] = (640, 360)
    fps: int = 20                    # 仍保留，作为基准换算
    palettesize: int = 256
    loop: int = 0
    subrectangles: bool = True
    facecolor: str = "white"
    # 新增：
    min_frame_ms: Optional[int] = 100        # 建议默认 100ms，更稳
    per_frame_ms: Optional[List[int]] = None # 若给出，优先生效
    repeat_each: int = 1                     # 每帧重复次数（>=1）

def _draw_ops_to_ndarray(scene: Scene, ops: List[DrawOp], size_px: Tuple[int, int]) -> np.ndarray:
    """将一帧 DrawOps 渲染为 RGBA ndarray（H,W,4）。"""
    w_px, h_px = size_px
    # 用 Figure + Agg 后端，强制像素尺寸
    dpi = 100
    fig = Figure(figsize=(w_px / dpi, h_px / dpi), dpi=dpi, facecolor="white")
    canvas = FigureCanvasAgg(fig)
    ax = fig.add_axes([0, 0, 1, 1])  # 全屏铺满
    ax.set_xlim(0, scene.width)
    # 重要：反转 y 轴以匹配我们“y 向下”的场景坐标
    ax.set_ylim(scene.height, 0)
    ax.set_aspect("auto")
    ax.axis("off")

    for op in ops:
        if isinstance(op, Rect):
            ax.add_patch(Rectangle((op.x, op.y), op.w, op.h, linewidth=0,
                                   facecolor=op.fill if op.fill else "#000000"))
        elif isinstance(op, Line):
            (x1, y1), (x2, y2) = op.p1, op.p2
            ax.plot([x1, x2], [y1, y2], linewidth=max(1.0, op.width), color=op.stroke)
        elif isinstance(op, TextOp):
            # 粗体映射；fontsize 用 px 粗略映射
            ax.text(op.x, op.y, op.content, ha="center", va="bottom",
                    fontsize=op.size, fontweight=("bold" if op.weight == "bold" else "normal"),
                    color=op.fill)

    # 渲染到 RGBA 缓冲区
    canvas.draw()
    buf = canvas.buffer_rgba()
    arr = np.asarray(buf)  # (H, W, 4) uint8
    return arr.copy()      # 拷贝以防后续 GC/复用问题


def frames_to_arrays(scene: Scene, frames: Iterable[Frame], size_px: Tuple[int, int]) -> List[np.ndarray]:
    images: List[np.ndarray] = []
    for fr in frames:
        ops = scene.render(fr.states)
        img = _draw_ops_to_ndarray(scene, ops, size_px)
        images.append(img)
    return images


def export_gif(scene, timeline, outfile: str, *, options: GifOptions | None = None) -> None:
    opts = options or GifOptions()
    frames = timeline.build_frames(scene)
    if not frames:
        raise ValueError("timeline has no frames")

    imgs = frames_to_arrays(scene, frames, opts.size)

    # --- 计算每帧时长（毫秒） ---
    if opts.per_frame_ms is not None:
        durations = list(opts.per_frame_ms)
        if len(durations) != len(imgs):
            raise ValueError("per_frame_ms length must equal number of frames")
    else:
        # 基于 fps 的均匀时长
        base_ms = max(1, int(round(1000.0 / max(1, opts.fps))))
        # 套最小时延（应对浏览器/播放器的回退/钳制）
        if opts.min_frame_ms:
            base_ms = max(base_ms, int(opts.min_frame_ms))
        durations = [base_ms] * len(imgs)

    # --- 按需重复每帧（进一步放慢且避免某些环境对 duration 的取整/钳制） ---
    if opts.repeat_each > 1:
        imgs = [img for img in imgs for _ in range(opts.repeat_each)]
        durations = [d for d in durations for _ in range(opts.repeat_each)]

    # imageio(pillow) 推荐显式给 duration（秒/列表）；我们给“毫秒列表”
    iio.imwrite(
        outfile,
        imgs,
        plugin="pillow",
        duration=durations,            # 支持 list：逐帧毫秒
        loop=opts.loop,
        palettesize=opts.palettesize,
        subrectangles=opts.subrectangles,
    )
