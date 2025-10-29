from pathlib import Path
from PIL import Image

from algoviz.core.scene import Scene
from algoviz.components.arraybar import ArrayBar
from algoviz.core.timeline import Timeline
from algoviz.backends import export_gif, GifOptions

ART = Path(__file__).resolve().parent / "_artifacts"
ART.mkdir(exist_ok=True, parents=True)

def _mini_scene_tl():
    scene = Scene(width=200, height=120)
    scene.add(ArrayBar([2, 1, 3], name="A", x=20, y=20, bar_width=24, bar_gap=8, height=80))
    tl = Timeline(fps=10)
    tl.compare("A", 0, 1, duration=3)
    tl.swap("A", 0, 1, duration=4)
    return scene, tl

def _gif_total_ms(path: Path) -> int:
    im = Image.open(path)
    total = 0
    while True:
        total += int(im.info.get("duration", 0))
        try:
            im.seek(im.tell() + 1)
        except EOFError:
            break
    return total

def test_slow_has_longer_total_ms():
    scene, tl = _mini_scene_tl()
    fast = ART / "slowdown_fast.gif"
    slow = ART / "slowdown_slow.gif"

    export_gif(scene, tl, str(fast), options=GifOptions(size=(160,100), fps=20, loop=0, min_frame_ms=20))
    export_gif(scene, tl, str(slow), options=GifOptions(size=(160,100), fps=20, loop=0, min_frame_ms=120))

    # 首尾不同，确认有动画
    im = Image.open(fast); im.seek(0); f0 = im.convert("RGBA").tobytes()
    im.seek(im.n_frames - 1); fN = im.convert("RGBA").tobytes()
    assert f0 != fN

    # 总时长判断：慢版更长
    assert _gif_total_ms(slow) > _gif_total_ms(fast)
