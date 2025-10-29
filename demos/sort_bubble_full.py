from __future__ import annotations
from algoviz.core.scene import Scene
from algoviz.core.timeline import Timeline
from algoviz.components.arraybar import ArrayBar

def build():
    data = [5, 3, 4, 1, 2]
    n = len(data)
    scene = Scene(width=140, height=80)
    arr = ArrayBar(data, name="A", x=6, y=10, bar_width=10, bar_gap=4, height=60)
    scene.add(arr)

    tl = Timeline(fps=20)
    tl.highlight("A", start=0, end=n-1, note=f"Init range [0..{n-1}]")

    shadow = data[:]  # 槽位 -> 值
    for end in range(n - 1, 0, -1):
        for i in range(0, end):
            tl.compare("A", i, i+1, duration=3, note=f"compare({i},{i+1})")
            if shadow[i] > shadow[i+1]:
                tl.swap("A", i, i+1, duration=2, note=f"swap({i},{i+1})")
                shadow[i], shadow[i+1] = shadow[i+1], shadow[i]
        tl.mark_sorted("A", upto=end, note=f"mark_sorted upto {end}")
    tl.mark_sorted("A", upto=0, note="sorted all")
    return scene, tl

