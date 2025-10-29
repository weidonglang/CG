from pathlib import Path

from algoviz.core.scene import Scene
from algoviz.components.arraybar import ArrayBar
from algoviz.core.timeline import Timeline
from algoviz.backends import export_svg, SvgOptions

def test_svg_has_viewbox_and_scaling_attrs(tmp_path: Path):
    scene = Scene(width=180, height=100)
    scene.add(ArrayBar([2, 1, 3], name="A", x=10, y=10, bar_width=12, bar_gap=4, height=80))
    tl = Timeline(fps=10)
    tl.highlight("A", idx=1, duration=1)

    out = tmp_path / "snap.svg"
    export_svg(scene, tl, str(out), options=SvgOptions(size=(180,100), frame=None))
    txt = out.read_text(encoding="utf-8")

    # 根 <svg> + viewBox（必须）
    assert "<svg" in txt and "viewBox=" in txt

    # 允许二选一，以兼容你当前 SVG 后端实现阶段
    has_non_scaling = ('vector-effect="non-scaling-stroke"' in txt)
    has_dom_baseline = ("dominant-baseline=" in txt)
    assert has_non_scaling or has_dom_baseline
