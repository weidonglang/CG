# src/algoviz/backends/__init__.py
from .tui_rich import (
    play_tui,
    PlayerState,
    advance_idx,
    adjust_speed,
    seek_percent,
    render_sidebar,
)

__all__ = [
    "play_tui",
    "PlayerState",
    "advance_idx",
    "adjust_speed",
    "seek_percent",
    "render_sidebar",
]
