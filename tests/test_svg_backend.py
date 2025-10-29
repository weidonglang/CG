from __future__ import annotations
from pathlib import Path
import xml.etree.ElementTree as ET
from algoviz.core.scene import Scene
from algoviz.core.timeline import Timeline
from algoviz.components.arraybar import ArrayBar
from algoviz.backends import export_svg, SvgOptions

ART_ROOT = Path(__file__).resolve().parent / "artifacts" / "M4"
ART_ROOT.mkdir(parents=True, exist_ok=True)

def test_export_svg_basic():
    scene = Scene(width=120, height=80)
    data = [2, 1, 3]
    scene.add(ArrayBar(data, name="A", x=6, y=10, bar_width=10, bar_gap=4, height=60))
    tl = Timeline(fps=10)
    tl.highlight("A", start=0, end=2, note="init")
    tl.swap("A", 0, 1, note="swap")
    out = ART_ROOT / "arr3_last.svg"
    export_svg(scene, tl, str(out), frame_index=-1, options=SvgOptions(size=(320, 200)))
    assert out.exists() and out.stat().st_size > 0

    # 解析与要点校验
    tree = ET.parse(out)
    root = tree.getroot()
    ns = {"svg": "http://www.w3.org/2000/svg"}
    assert root.tag.endswith("svg")
    rects = root.findall(".//svg:rect", ns)
    texts = root.findall(".//svg:text", ns)
    # 每个柱一个 rect + 一个数值 text
    assert len(rects) >= len(data) and len(texts) >= len(data)
