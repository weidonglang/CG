from .tui_rich import (
    play_tui, PlayerState, advance_idx, adjust_speed, seek_percent, render_sidebar,
)
from .gif_mpl import export_gif, GifOptions
from .svg_svgwrite import export_svg, SvgOptions  # ← 新增

__all__ = [
    "play_tui", "PlayerState", "advance_idx", "adjust_speed", "seek_percent", "render_sidebar",
    "export_gif", "GifOptions",
    "export_svg", "SvgOptions",
]
