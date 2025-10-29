from __future__ import annotations
from rich.console import Console
from algoviz.backends import PlayerState, render_sidebar

def test_sidebar_render_snapshot():
    state = PlayerState(frame_idx=0, paused=False, speed=1.0, total_frames=3, fps=20, note="hello")
    rend = render_sidebar(state)
    console = Console(width=60, record=True)
    console.print(rend)
    text = console.export_text()
    assert "Frame: 1/3" in text
    assert "Speed: 1.00x" in text
    assert "Paused: False" in text
    assert "hello" in text
