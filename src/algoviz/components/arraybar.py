from __future__ import annotations
from dataclasses import dataclass, replace
from typing import Any, Dict, List, Optional, Tuple
from ..core.drawops import Rect, Text, DrawList
from ..core.scene import Actor

DEFAULT_FILL = "#5B8FF9"
HIGHLIGHT_FILL = "#F6BD16"
COMPARE_FILL = "#E8684A"
SORTED_FILL = "#49AA19"
LABEL_COLOR = "#333333"

@dataclass
class ArrayBarState:
    data: List[float]               # 固定值数组（item 索引 -> 值）
    order: List[int]                # 槽位 -> item 索引（可交换）
    highlight: set[int]             # 被高亮的槽位集合
    compare: Optional[Tuple[int,int]]  # 当前对比的 (i, j)，仅在 compare 事件帧有效
    sorted_upto: int                # 已排序前缀的最大槽位（包含）；-1 表示无

class ArrayBar(Actor):
    def __init__(self, data: List[float], name: str = "A",
                 x: float = 10, y: float = 10,
                 bar_width: float = 18, bar_gap: float = 6, height: float = 120) -> None:
        self.name = name
        self._data = list(float(v) for v in data)
        self.x = x
        self.y = y
        self.bar_width = bar_width
        self.bar_gap = bar_gap
        self.height = height

    # ---------- Actor 接口 ----------
    def initial_state(self) -> ArrayBarState:
        n = len(self._data)
        return ArrayBarState(
            data=list(self._data),
            order=list(range(n)),
            highlight=set(),
            compare=None,
            sorted_upto=-1,
        )

    def draw(self, state: ArrayBarState) -> DrawList:
        ops: DrawList = []
        n = len(state.order)
        vmax = max(state.data) if state.data else 1.0

        for slot in range(n):
            item = state.order[slot]
            val = state.data[item]
            h = 0 if vmax <= 0 else (val / vmax) * self.height
            x = self.x + slot * (self.bar_width + self.bar_gap)
            y = self.y + (self.height - h)

            # 颜色优先级：已排序 > compare > highlight > 默认
            fill = DEFAULT_FILL
            if state.sorted_upto >= 0 and slot <= state.sorted_upto:
                fill = SORTED_FILL
            if state.compare and slot in state.compare:
                fill = COMPARE_FILL
            elif slot in state.highlight:
                fill = HIGHLIGHT_FILL

            ops.append(Rect(x, y, self.bar_width, h, fill=fill, stroke=None, label=f"{val:g}"))
            # 在柱顶上方放一个数值标签
            ops.append(Text(x + self.bar_width * 0.5, y - 6, f"{val:g}", size=11, weight="bold", fill=LABEL_COLOR))
        return ops

    def apply_event(self, state: ArrayBarState, event_type: str, payload: Dict[str, Any], duration: int):
        # 深拷贝帮助函数（仅浅层可变容器）
        def clone(s: ArrayBarState) -> ArrayBarState:
            return ArrayBarState(
                data=list(s.data),
                order=list(s.order),
                highlight=set(s.highlight),
                compare=None if s.compare is None else (s.compare[0], s.compare[1]),
                sorted_upto=s.sorted_upto,
            )

        frames: List[ArrayBarState] = []
        current = clone(state)

        if event_type == "compare":
            i, j = int(payload["i"]), int(payload["j"])
            for _ in range(duration):
                step = clone(current)
                step.compare = (i, j)
                frames.append(step)
            # compare 仅在该事件帧有效，事件结束后清空 compare
            persist = clone(current)
            persist.compare = None
            return frames, persist

        if event_type == "highlight":
            idx = payload.get("idx")
            start = payload.get("start")
            end = payload.get("end")
            clear = bool(payload.get("clear", False))

            next_state = clone(current)
            if clear:
                next_state.highlight.clear()
            if idx is not None:
                next_state.highlight.add(int(idx))
            if start is not None and end is not None:
                for k in range(int(start), int(end) + 1):
                    next_state.highlight.add(k)

            # 持续 1 帧（或 duration 帧相同）
            for _ in range(duration):
                frames.append(clone(next_state))
            return frames, next_state

        if event_type == "mark_sorted":
            upto = int(payload["upto"])
            next_state = clone(current)
            next_state.sorted_upto = max(next_state.sorted_upto, upto)
            for _ in range(duration):
                frames.append(clone(next_state))
            return frames, next_state

        if event_type == "assign":
            i = int(payload["i"])
            value = float(payload["value"])
            # 修改 data（值），不改变顺序
            next_state = clone(current)
            item = next_state.order[i]
            next_state.data[item] = value
            for _ in range(duration):
                frames.append(clone(next_state))
            return frames, next_state

        if event_type == "swap":
            i, j = int(payload["i"]), int(payload["j"])
            next_state = clone(current)
            if i < 0 or j < 0 or i >= len(next_state.order) or j >= len(next_state.order):
                raise IndexError("swap index out of range")
            # M1：离散交换（动画插值将于后续里程碑加入）
            next_state.order[i], next_state.order[j] = next_state.order[j], next_state.order[i]
            for _ in range(duration):
                frames.append(clone(next_state))
            return frames, next_state

        raise KeyError(f"Unknown event type: {event_type}")
