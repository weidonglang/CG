from __future__ import annotations
from algoviz.backends import advance_idx, adjust_speed, seek_percent

def test_advance_frame_basic():
    # 未暂停：20fps，1.0x，0.5秒 -> 前进 10 帧
    idx = advance_idx(idx=0, paused=False, fps=20, speed=1.0, dt=0.5, total=120)
    assert idx == 10
    # 暂停：不前进
    idx2 = advance_idx(idx=10, paused=True, fps=20, speed=1.0, dt=1.0, total=120)
    assert idx2 == 10
    # 越界：夹到最后一帧
    idx3 = advance_idx(idx=119, paused=False, fps=60, speed=4.0, dt=1.0, total=120)
    assert idx3 == 119

def test_speed_adjust():
    # 初始 1.0，向下两步 -> 0.5
    s = adjust_speed(1.0, -2)
    assert s == 0.5
    # 再向上四步 -> 1.5
    s2 = adjust_speed(s, +4)
    assert s2 == 1.5
    # 下限/上限
    assert adjust_speed(0.25, -4) == 0.25
    assert adjust_speed(4.0, +4) == 4.0

def test_seek_percent():
    total = 100
    assert seek_percent(total, 0.0) == 0
    assert seek_percent(total, 0.3) == 30
    assert seek_percent(total, 1.0) == 99
    assert seek_percent(total, -1.0) == 0
    assert seek_percent(total, 2.0) == 99
