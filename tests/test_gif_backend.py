from __future__ import annotations
from pathlib import Path
from PIL import Image  # Pillow
from algoviz.core.scene import Scene
from algoviz.core.timeline import Timeline
from algoviz.components.arraybar import ArrayBar
from algoviz.backends import export_gif, GifOptions

ART_ROOT = Path(__file__).resolve().parent / "artifacts" / "M3"
ART_ROOT.mkdir(parents=True, exist_ok=True)

def _mini_scene_tl():
    scene = Scene(width=120, height=80)
    scene.add(ArrayBar([3, 1, 2], name="A", x=6, y=10, bar_width=10, bar_gap=4, height=60))
    tl = Timeline(fps=10)
    tl.highlight("A", idx=0, note="h0")
    tl.swap("A", 0, 1, note="swap01")
    tl.swap("A", 1, 2, note="swap12")
    return scene, tl

def test_export_gif_size_and_frames():
    out = ART_ROOT / "backend_size_frames.gif"
    scene, tl = _mini_scene_tl()
    export_gif(scene, tl, str(out), options=GifOptions(size=(180, 120), fps=10, loop=0))
    assert out.exists() and out.stat().st_size > 0
    im = Image.open(out)
    assert im.format == "GIF"
    assert im.size == (180, 120)
    assert getattr(im, "n_frames", 1) >= 3  # 至少 3 帧

def test_export_gif_content_differs():
    out = ART_ROOT / "backend_content_diff.gif"
    scene, tl = _mini_scene_tl()
    export_gif(scene, tl, str(out), options=GifOptions(size=(160, 100), fps=10, loop=0))
    im = Image.open(out)
    im.seek(0); f0 = im.convert("RGBA").tobytes()
    im.seek(im.n_frames - 1); fN = im.convert("RGBA").tobytes()
    assert f0 != fN
