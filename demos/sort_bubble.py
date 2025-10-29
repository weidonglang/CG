from __future__ import annotations
from algoviz.core.scene import Scene
from algoviz.core.timeline import Timeline
from algoviz.components.arraybar import ArrayBar


def build():
    """
    构建一个最小的冒泡排序演示（仅一趟 + 若干对比/交换），提供给 CLI 播放。
    """
    scene = Scene(width=120, height=80)
    arr = ArrayBar([5, 3, 4, 1, 2], name="A", x=6, y=10, bar_width=10, bar_gap=4, height=60)
    scene.add(arr)

    tl = Timeline(fps=20)

    # 第 0 步：预高亮
    tl.highlight("A", start=0, end=4, note="Init highlight [0..4]")

    # 对比与交换（仅示例，不是完整冒泡）
    tl.compare("A", 0, 1, duration=2, note="compare(0,1)")
    tl.swap("A", 0, 1, duration=1, note="swap(0,1)")

    tl.compare("A", 1, 2, duration=2, note="compare(1,2)")
    tl.swap("A", 1, 2, duration=1, note="swap(1,2)")

    tl.compare("A", 2, 3, duration=2, note="compare(2,3)")
    tl.swap("A", 2, 3, duration=1, note="swap(2,3)")

    tl.compare("A", 3, 4, duration=2, note="compare(3,4)")
    tl.swap("A", 3, 4, duration=1, note="swap(3,4)")

    tl.mark_sorted("A", upto=4, note="mark_sorted upto 4")

    return scene, tl
