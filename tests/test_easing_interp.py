from pathlib import Path

from algoviz.core.scene import Scene
from algoviz.components.arraybar import ArrayBar
from algoviz.core.timeline import Timeline, EASING


def test_builtin_easings_basic_props():
    # f(0)=0, f(1)=1, 且 0<=f(t)<=1
    for name in ("linear", "easeInOutCubic"):
        f = EASING[name]
        assert f(0.0) == 0.0
        assert f(1.0) == 1.0
        for i in range(21):
            t = i / 20
            y = f(t)
            assert -1e-9 <= y <= 1.0 + 1e-9

def test_swap_interp_is_monotonic_and_finalize():
    scene = Scene(width=240, height=120)
    scene.add(ArrayBar([3, 1, 2], name="A", x=20, y=20, bar_width=20, bar_gap=10, height=80))
    tl = Timeline(fps=10)
    # 注意：传“名字”，不要传函数
    tl.swap("A", 0, 2, duration=8, easing="easeInOutCubic")
    frames = tl.build_frames(scene)

    # 中间帧：偏移单调逼近；最后一帧已交换且 offsets 清空
    offs0, offs2 = [], []
    for fr in frames[:-1]:  # 不含末帧
        s = fr.states["A"]
        offs0.append(abs(s.offsets.get(0, 0.0)))
        offs2.append(abs(s.offsets.get(2, 0.0)))
    assert all(offs0[i] >= offs0[i+1] - 1e-6 for i in range(len(offs0)-1))
    assert all(offs2[i] >= offs2[i+1] - 1e-6 for i in range(len(offs2)-1))

    last = frames[-1].states["A"]
    assert last.order == [2, 1, 0]
    assert last.offsets == {}
