from __future__ import annotations
from pathlib import Path
from PIL import Image
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


def _gif_total_ms(path: Path) -> int:
    im = Image.open(path)
    try:
        n = im.n_frames
    except Exception:
        n = 1
    total = 0
    for i in range(n):
        im.seek(i)
        total += int(im.info.get("duration", 0))
    return total


def test_export_gif_size_and_frames():
    out = ART_ROOT / "backend_size_frames.gif"
    scene, tl = _mini_scene_tl()
    export_gif(scene, tl, str(out), options=GifOptions(size=(180, 120), fps=10, loop=0))
    assert out.exists() and out.stat().st_size > 0
    im = Image.open(out)
    assert im.format == "GIF"
    assert im.size == (180, 120)
    assert getattr(im, "n_frames", 1) >= 3  # 至少 3 帧


def test_export_gif_content_differs_and_slow():
    out_fast = ART_ROOT / "backend_fast.gif"
    out_slow = ART_ROOT / "backend_slow.gif"
    scene, tl = _mini_scene_tl()

    # 快：较小的每帧时延
    export_gif(
        scene, tl, str(out_fast),
        options=GifOptions(size=(160, 100), fps=20, loop=0, min_frame_ms=40),
    )
    # 慢：强制更大的最小时延
    export_gif(
        scene, tl, str(out_slow),
        options=GifOptions(size=(160, 100), fps=20, loop=0, min_frame_ms=120),
    )

    # 首尾不同，证明确实是动画
    im = Image.open(out_fast)
    im.seek(0); f0 = im.convert("RGBA").tobytes()
    im.seek(im.n_frames - 1); fN = im.convert("RGBA").tobytes()
    assert f0 != fN

    # 总时长：慢版应更长
    assert _gif_total_ms(out_slow) > _gif_total_ms(out_fast)
