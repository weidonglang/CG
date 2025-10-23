from __future__ import annotations
import pytest

from algoviz.core.timeline import Timeline
from algoviz.core.scene import Scene
from algoviz.components.arraybar import ArrayBar, ArrayBarState

# ---------- 测试 1 ----------
def test_frame_count_and_compare_transient():
    """
    目的：时间线正确累加帧数；compare 只在该事件的帧内生效（临时），之后应清空
    步骤：
      1) 新建 ArrayBar([5,3,4])，加入 Scene
      2) 事件序列：highlight(idx=1, 1帧) -> compare(0,1, 2帧) -> swap(0,1, 1帧)
      3) 生成帧
    预期：
      - 总帧数 = 1 + 2 + 1 = 4
      - frames[1] 与 frames[2] 的 compare 为 (0,1)
      - 非 compare 的帧 compare 为 None（frames[0], frames[3]）
      - highlight 在之后仍保留（持久）
    """
    scene = Scene()
    scene.add(ArrayBar([5, 3, 4], name="A"))
    tl = Timeline(fps=20)
    tl.highlight("A", idx=1)
    tl.compare("A", 0, 1, duration=2)
    tl.swap("A", 0, 1, duration=1)

    frames = tl.build_frames(scene)
    assert len(frames) == 4

    s0 = frames[0].states["A"]; assert isinstance(s0, ArrayBarState)
    s1 = frames[1].states["A"]
    s2 = frames[2].states["A"]
    s3 = frames[3].states["A"]

    assert s0.compare is None
    assert s1.compare == (0, 1)
    assert s2.compare == (0, 1)
    assert s3.compare is None

    # highlight 持久
    assert 1 in s3.highlight

# ---------- 测试 2 ----------
def test_swap_changes_order_persistently():
    """
    目的：交换事件会持久改变 order（槽位->item 映射）
    预期：初始 order=[0,1,2]；swap(0,2) 后 order=[2,1,0]
    """
    scene = Scene()
    scene.add(ArrayBar([5, 3, 4], name="A"))
    tl = Timeline()
    tl.swap("A", 0, 2)

    frames = tl.build_frames(scene)
    s_last = frames[-1].states["A"]
    assert s_last.order == [2, 1, 0]

# ---------- 测试 3 ----------
def test_mark_sorted_and_highlight_range():
    """
    目的：mark_sorted 与区间高亮按预期工作，且 mark_sorted 取最大值（单调不减）
    步骤：
      1) mark_sorted(upto=0)
      2) highlight(start=0,end=1)
      3) mark_sorted(upto=1)
    预期：
      - 最后一帧 sorted_upto == 1
      - highlight 集合包含 {0,1}
    """
    scene = Scene()
    scene.add(ArrayBar([2, 1, 3], name="A"))
    tl = Timeline()
    tl.mark_sorted("A", upto=0)
    tl.highlight("A", start=0, end=1)
    tl.mark_sorted("A", upto=1)

    frames = tl.build_frames(scene)
    s = frames[-1].states["A"]
    assert s.sorted_upto == 1
    assert {0, 1}.issubset(s.highlight)

# ---------- 测试 4 ----------
def test_draw_ops_count_and_colors():
    """
    目的：渲染出的 DrawOps 数量与基本语义正确（每个柱状条 -> 1 个 Rect + 1 个 Text）
    步骤：
      1) 初始无事件渲染：直接使用 initial_state
      2) highlight idx=0 再渲染
    预期：
      - 每帧 Rect 数量 == n，Text 数量 == n
      - 高亮帧中存在被高亮的柱（颜色判断略过到 M2，可先只验证数量）
    """
    scene = Scene()
    arr = ArrayBar([1, 2, 3], name="A")
    scene.add(arr)

    tl = Timeline()
    tl.highlight("A", idx=0)
    frames = tl.build_frames(scene)

    # 第一帧（highlight）：
    ops = scene.render(frames[0].states)
    rects = [op for op in ops if getattr(op, "kind", "") == "rect"]
    texts = [op for op in ops if getattr(op, "kind", "") == "text"]
    assert len(rects) == 3
    assert len(texts) == 3

# ---------- 测试 5 ----------
def test_assign_updates_value():
    """
    目的：assign(i,value) 只改变值，不改变顺序
    预期：值被更新；order 未变
    """
    scene = Scene().add(ArrayBar([5, 3, 4], name="A"))
    tl = Timeline()
    tl.assign("A", i=1, value=9)

    frames = tl.build_frames(scene)
    s = frames[-1].states["A"]
    # 槽位1对应的 item 索引
    item = s.order[1]
    assert s.data[item] == 9
    assert s.order == [0, 1, 2]
