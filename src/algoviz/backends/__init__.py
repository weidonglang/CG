# src/algoviz/backends/__init__.py
"""
后端统一导出清单。
保持轻量，禁止在此做任何渲染/构帧逻辑，避免环依赖。
"""

from .gif_mpl import export_gif, GifOptions  # GIF 导出（Matplotlib + Pillow）
from .svg_svgwrite import export_svg, SvgOptions  # SVG 导出（svgwrite 或纯字符串）
from .tui_rich import (
    play_tui,            # 终端预览播放器
    PlayerState,         # （供测试使用）
    render_sidebar,      # （供测试快照使用）
    advance_idx,         # （tests/test_tui_player_logic.py 依赖）
    adjust_speed,        # idem
    seek_percent,        # idem
)

__all__ = [
    "export_gif", "GifOptions",
    "export_svg", "SvgOptions",
    "play_tui", "PlayerState", "render_sidebar",
    "advance_idx", "adjust_speed", "seek_percent",
]
