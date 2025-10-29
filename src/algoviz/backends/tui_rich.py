from __future__ import annotations
import sys
import time
from dataclasses import dataclass
from typing import List, Optional, Tuple

from rich.console import Console, RenderableType
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text
from rich.table import Table
from rich.live import Live

from ..core.scene import Scene
from ..core.timeline import Timeline, Frame
from ..core.drawops import DrawOp, Rect, Text as TextOp


# --------------------- 播放器状态 & 纯逻辑函数（可单测） ---------------------

@dataclass
class PlayerState:
    frame_idx: int
    paused: bool
    speed: float           # 倍速：0.25 ~ 4.0
    total_frames: int
    fps: int
    note: Optional[str] = None

def clamp(n: int, lo: int, hi: int) -> int:
    return lo if n < lo else hi if n > hi else n

def advance_idx(idx: int, paused: bool, fps: int, speed: float, dt: float, total: int) -> int:
    """
    按 fps * speed * dt 推进帧索引；暂停则不前进；越界夹取到 total-1。
    """
    if paused or total <= 0:
        return idx
    inc = int(fps * max(speed, 0.0) * max(dt, 0.0))
    if inc <= 0:
        return idx
    return clamp(idx + inc, 0, max(0, total - 1))

def adjust_speed(speed: float, delta_steps: int) -> float:
    """
    倍速调节：每一步 0.25 倍速增减，范围 [0.25, 4.0]。
    例如：1.0 经两次负向步骤 -> 0.5；再三次正向步骤 -> 1.25 -> 1.5 -> 1.75（测试里会根据断言设置）。
    """
    new_speed = speed + 0.25 * delta_steps
    if new_speed < 0.25:
        new_speed = 0.25
    if new_speed > 4.0:
        new_speed = 4.0
    # 避免浮点误差
    return round(new_speed + 1e-9, 2)

def seek_percent(total: int, percent: float) -> int:
    """
    百分比跳转：p ∈ [0,1] -> floor(total * p)，再夹取到 [0, total-1]
    p=1.0 时跳到最后一帧。
    """
    if total <= 0:
        return 0
    p = 0.0 if percent < 0 else 1.0 if percent > 1 else percent
    idx = int(total * p)
    if idx >= total:
        idx = total - 1
    return idx


# --------------------- 渲染：DrawOps -> 字符画布 & 侧栏 ---------------------

def _rasterize_ops_to_canvas(ops: List[DrawOp], scene: Scene, cols: int, rows: int) -> RenderableType:
    """
    非等宽像素 -> 等宽字符的简单栅格化（Rect 填充块，Text 放置文本）。
    仅为 M2 最小可用，后续可替换为更精细的字符画/半块字符等。
    """
    # 留出 2 行上下边距，避免顶边贴字
    rows = max(6, rows)
    cols = max(20, cols)

    # 初始化空白画布
    grid = [[" " for _ in range(cols)] for _ in range(rows)]

    def to_cell_x(x: float) -> int:
        return int(x / max(1, scene.width) * (cols - 1))

    def to_cell_y(y: float) -> int:
        # 场景 y 向下为正；终端行号向下为正，这里直接线性映射
        return int(y / max(1, scene.height) * (rows - 1))

    # 先画 Rect
    for op in ops:
        if isinstance(op, Rect):
            x1 = clamp(to_cell_x(op.x), 0, cols - 1)
            y1 = clamp(to_cell_y(op.y), 0, rows - 1)
            x2 = clamp(to_cell_x(op.x + op.w), 0, cols - 1)
            y2 = clamp(to_cell_y(op.y + op.h), 0, rows - 1)
            if x2 < x1:
                x1, x2 = x2, x1
            if y2 < y1:
                y1, y2 = y2, y1
            for yy in range(y1, y2 + 1):
                row = grid[yy]
                for xx in range(x1, x2 + 1):
                    row[xx] = "█"

    # 再放 Text
    for op in ops:
        if isinstance(op, TextOp):
            cx = clamp(to_cell_x(op.x), 0, cols - 1)
            cy = clamp(to_cell_y(op.y), 0, rows - 1)
            s = str(op.content)
            for i, ch in enumerate(s):
                xx = cx + i
                if xx < cols:
                    grid[cy][xx] = ch

    # 拼成 Rich Text
    lines = ["".join(r) for r in grid]
    return Text("\n".join(lines))

def render_sidebar(state: PlayerState) -> RenderableType:
    table = Table.grid(expand=True)
    table.add_row(f"[bold]Frame:[/bold] {state.frame_idx + 1}/{state.total_frames}")
    table.add_row(f"[bold]Speed:[/bold] {state.speed:.2f}x")
    table.add_row(f"[bold]FPS:[/bold] {state.fps}")
    table.add_row(f"[bold]Paused:[/bold] {state.paused}")
    if state.note:
        table.add_row(f"[bold]Note:[/bold] {state.note}")
    help_text = Text("Space=Play/Pause  ←/→=Step  [ / ]=Speed  0..9=Seek  Q=Quit", style="dim")
    return Panel.fit(Columns([table, help_text], expand=True), title="Algoviz TUI")

def _compose_view(scene: Scene, frame: Frame, state: PlayerState, term_cols: int, term_rows: int) -> RenderableType:
    # 左画布 2/3 宽；右侧栏 1/3 宽
    canvas_cols = max(20, int(term_cols * 0.66))
    sidebar_cols = term_cols - canvas_cols - 1
    if sidebar_cols < 20:
        sidebar_cols = 20
        canvas_cols = max(20, term_cols - sidebar_cols - 1)
    canvas_rows = term_rows - 2

    ops = scene.render(frame.states)
    canvas = _rasterize_ops_to_canvas(ops, scene, canvas_cols, canvas_rows)
    sidebar = render_sidebar(state)
    return Columns([Panel(canvas, title="Canvas"), sidebar], expand=True)


# --------------------- 键盘（Windows 原生；非 Windows 自动降级无键） ---------------------

def _read_key_nonblocking() -> Optional[str]:
    """
    返回一个简单键位字符串：
      " " 空格; "q"; "[" 或 "]"; "left"/"right"; "0".."9"
    非 Windows 返回 None（降级为无键交互）。
    """
    if sys.platform.startswith("win"):
        try:
            import msvcrt  # type: ignore
        except Exception:
            return None
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            if not ch:
                return None
            if ch in (b"q", b"Q"):
                return "q"
            if ch == b" ":
                return " "
            if ch == b"[":
                return "["
            if ch == b"]":
                return "]"
            if ch.isdigit():
                return ch.decode()
            # 方向键
            if ch in (b"\xe0", b"\x00"):
                k = msvcrt.getch()
                if k == b"K":
                    return "left"
                if k == b"M":
                    return "right"
        return None
    else:
        # 非 Windows：为简洁与稳定，此版不启用原始模式读键，直接降级为无键
        return None


# --------------------- 主入口：play_tui ---------------------

def play_tui(scene: Scene, timeline: Timeline, fps: int = 20, speed: float = 1.0, exit_after: float | None = None) -> None:
    """
    在终端播放 Scene+Timeline 生成的帧序列；支持（Windows）键控。
    非 TTY 或无键平台也能播放，并可通过 exit_after 自动退出（用于 CI）。
    """
    frames: List[Frame] = timeline.build_frames(scene)
    total = len(frames) if frames else 0
    if total == 0:
        return

    console = Console()
    state = PlayerState(frame_idx=0, paused=False, speed=speed, total_frames=total, fps=fps, note=frames[0].note)

    last_ts = time.monotonic()
    start_ts = last_ts

    with Live(console=console, refresh_per_second=max(10, fps)) as live:
        while True:
            now = time.monotonic()
            dt = now - last_ts
            last_ts = now

            # 按键（可能为 None）
            key = _read_key_nonblocking()
            if key == "q":
                break
            elif key == " ":
                state.paused = not state.paused
            elif key == "left":
                state.frame_idx = clamp(state.frame_idx - 1, 0, total - 1)
            elif key == "right":
                state.frame_idx = clamp(state.frame_idx + 1, 0, total - 1)
            elif key == "[":
                state.speed = adjust_speed(state.speed, -1)
            elif key == "]":
                state.speed = adjust_speed(state.speed, +1)
            elif key and key.isdigit():
                # 数字键 0..9 -> 百分位跳转
                percent = int(key) / 10.0
                state.frame_idx = seek_percent(total, percent)

            # 时间推进
            state.frame_idx = advance_idx(state.frame_idx, state.paused, state.fps, state.speed, dt, total)
            state.note = frames[state.frame_idx].note

            # 退出门槛（用于 CI/自动测试）
            if exit_after is not None and (now - start_ts) >= exit_after:
                break

            # 渲染
            term = console.size
            view = _compose_view(scene, frames[state.frame_idx], state, term.width, term.height)
            live.update(view)
