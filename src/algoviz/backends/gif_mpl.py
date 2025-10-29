from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Sequence, Tuple

# —— 关键：在导入 pyplot 之前强制使用 Agg（无 GUI 后端）——
# 官方文档：可通过 matplotlib.use() / MPLBACKEND / rcParams 设后端；Agg 是非交互后端，适合脚本/CI。:contentReference[oaicite:2]{index=2}
import matplotlib
matplotlib.use("Agg")

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import imageio.v3 as iio


@dataclass
class GifOptions:
    size: Tuple[int, int] = (640, 360)
    fps: int = 20
    palettesize: int = 256
    loop: int = 0
    subrectangles: bool = True
    facecolor: str = "white"
    min_frame_ms: Optional[int] = 100
    per_frame_ms: Optional[List[int]] = None
    repeat_each: int = 1


def _render_frame(scene, frame, size: Tuple[int, int], facecolor: str = "white") -> np.ndarray:
    W, H = size
    dpi = 100
    fig = plt.figure(figsize=(W / dpi, H / dpi), dpi=dpi)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, scene.width)
    ax.set_ylim(scene.height, 0)  # y 向下
    ax.set_axis_off()
    fig.patch.set_facecolor(facecolor)
    ax.set_facecolor(facecolor)

    ops = scene.render(frame.states)
    for op in ops:
        # Rect
        if hasattr(op, "w") and hasattr(op, "h") and hasattr(op, "x") and hasattr(op, "y"):
            ec = getattr(op, "stroke", None)
            fc = getattr(op, "fill", None) or "#000"
            ax.add_patch(
                mpatches.Rectangle((op.x, op.y), op.w, op.h, linewidth=0 if ec is None else 1, edgecolor=ec, facecolor=fc)
            )
        # Text
        if hasattr(op, "content") and hasattr(op, "size") and hasattr(op, "x") and hasattr(op, "y"):
            color = getattr(op, "fill", "#000")
            weight = getattr(op, "weight", "normal")
            ax.text(op.x, op.y, op.content, fontsize=op.size, color=color, fontweight=weight,
                    ha="center", va="bottom")

    fig.canvas.draw()
    buf = np.asarray(fig.canvas.buffer_rgba(), dtype=np.uint8)
    plt.close(fig)
    return buf


def _frames_to_arrays(scene, frames: Sequence, size: Tuple[int, int]) -> List[np.ndarray]:
    return [_render_frame(scene, f, size) for f in frames]


def export_gif(scene, timeline, outfile: str, *, options: GifOptions | None = None) -> None:
    opt = options or GifOptions()
    frames = timeline.build_frames(scene)
    if not frames:
        raise ValueError("timeline has no frames")

    imgs = _frames_to_arrays(scene, frames, opt.size)

    # 每帧毫秒（Pillow 读回 info['duration'] 为 ms）
    if opt.per_frame_ms is not None:
        durations = list(opt.per_frame_ms)
        if len(durations) != len(imgs):
            raise ValueError("per_frame_ms length must equal number of frames")
    else:
        base_ms = max(1, int(round(1000.0 / max(1, opt.fps))))
        if opt.min_frame_ms:
            base_ms = max(base_ms, int(opt.min_frame_ms))
        durations = [base_ms] * len(imgs)

    if opt.repeat_each > 1:
        imgs = [img for img in imgs for _ in range(opt.repeat_each)]
        durations = [d for d in durations for _ in range(opt.repeat_each)]

    # 流式逐帧写入；GIF 内部以 1/100s 精度存储，但此处统一以 ms 传入，Pillow 读取时也是 ms。
    with iio.imopen(outfile, "w", plugin="pillow") as writer:
        for idx, (img, ms) in enumerate(zip(imgs, durations)):
            if idx == 0:
                writer.write(img, duration=ms, loop=opt.loop,
                             palettesize=opt.palettesize, subrectangles=opt.subrectangles)
            else:
                writer.write(img, duration=ms)
