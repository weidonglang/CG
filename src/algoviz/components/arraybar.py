#algoviz/components/arraybar.py
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple, Any

from ..core.drawops import Rect, Text

# ===== 主题色 =====
DEFAULT_FILL = "#4C97FF"
HIGHLIGHT_FILL = "#FFB800"
COMPARE_FILL = "#FF5A5A"
SORTED_FILL = "#33C48E"
LABEL_COLOR = "#222"


@dataclass
class ArrayBarState:
    values: List[float]
    # 槽位 -> 初始索引 的顺序映射，swap 后持久更新
    order: List[int]
    sorted_upto: int = -1
    highlight: Set[int] = field(default_factory=set)
    compare: Optional[Tuple[int, int]] = None
    # 子步插值期间的像素位移（按槽位）
    offsets: Dict[int, float] = field(default_factory=dict)

    # 兼容 tests: s.data[item] 读取数值（映射到 values）
    @property
    def data(self) -> List[float]:
        return self.values


def _copy_state(st: ArrayBarState) -> ArrayBarState:
    return ArrayBarState(
        values=list(st.values),
        order=list(st.order),
        sorted_upto=st.sorted_upto,
        highlight=set(st.highlight),
        compare=None if st.compare is None else (st.compare[0], st.compare[1]),
        offsets=dict(st.offsets),
    )


class ArrayBar:
    """
    柱状数组组件：
      - swap/assign 子步只改 offsets，finalize 落位
      - 颜色优先级：已排序 > compare > highlight > 默认
      - order: 槽位 → 初始索引，swap 后需持久更新
    """

    def __init__(
        self,
        values: List[float],
        name: str,
        x: int = 6,
        y: int = 10,
        bar_width: int = 10,
        bar_gap: int = 4,
        height: int = 60,
        show_value: bool = True,
    ) -> None:
        self.name = name
        self.x = int(x)
        self.y = int(y)
        self.bar_width = int(bar_width)
        self.bar_gap = int(bar_gap)
        self.height = int(height)
        self.show_value = show_value

        n = len(values)
        self._init_state = ArrayBarState(values=list(values), order=list(range(n)))

    # ==== 场景接口 ====
    def initial_state(self) -> ArrayBarState:
        return _copy_state(self._init_state)

    def _slot_x(self, slot: int) -> int:
        return self.x + (self.bar_width + self.bar_gap) * slot

    def draw(self, st: ArrayBarState) -> List[Any]:
        ops: List[Any] = []
        n = len(st.values)
        vmax = max(st.values) if n else 1.0
        vmax = 1.0 if vmax <= 0 else float(vmax)

        for i, v in enumerate(st.values):
            x_base = self._slot_x(i)
            x = x_base + st.offsets.get(i, 0.0)

            h = max(1, int(round((float(v) / vmax) * self.height)))
            y_top = self.y + (self.height - h)

            # 颜色优先级：最后覆盖者最高
            fill = DEFAULT_FILL
            if i in st.highlight:
                fill = HIGHLIGHT_FILL
            if st.compare and i in st.compare:
                fill = COMPARE_FILL
            if st.sorted_upto >= 0 and i <= st.sorted_upto:
                fill = SORTED_FILL

            ops.append(Rect(x=x, y=y_top, w=self.bar_width, h=h, fill=fill, stroke=None))
            if self.show_value:
                ops.append(Text(content=str(v), x=x + self.bar_width / 2, y=y_top - 12,
                                size=10, weight="normal", fill=LABEL_COLOR))
        return ops

    # ==== 旧离散版（兼容）====
    def apply_event(self, st: ArrayBarState, etype: str, payload: dict) -> ArrayBarState:
        ns = _copy_state(st)
        if etype == "highlight":
            if "idx" in payload:
                ns.highlight = {int(payload["idx"])}
            elif "start" in payload and "end" in payload:
                a, b = int(payload["start"]), int(payload["end"])
                ns.highlight = set(range(min(a, b), max(a, b) + 1))
        elif etype == "compare":
            ns.compare = (int(payload["i"]), int(payload["j"]))
        elif etype == "swap":
            i, j = int(payload["i"]), int(payload["j"])
            ns.values[i], ns.values[j] = ns.values[j], ns.values[i]
            ns.order[i], ns.order[j] = ns.order[j], ns.order[i]
        elif etype == "assign":
            i = int(payload["i"])
            if "value" in payload:
                ns.values[i] = payload["value"]
            else:
                j = int(payload["j"])
                ns.values[i] = ns.values[j]
        elif etype == "mark_sorted":
            ns.sorted_upto = max(ns.sorted_upto, int(payload["upto"]))
        return ns

    # ==== 子步插值版（M5）====
    def apply_event_step(self, st: ArrayBarState, etype: str, payload: dict, t: float) -> ArrayBarState:
        """
        t 已是缓动后的 0..1。为满足“单调逼近目标”的测试，这里采用 (1 - t) 作为剩余距离权重。
        """
        ns = _copy_state(st)
        rem = 1.0 - float(t)  # 关键：剩余比例，随帧推进单调下降

        if etype == "swap":
            i, j = int(payload["i"]), int(payload["j"])
            xi, xj = self._slot_x(i), self._slot_x(j)
            # 偏移量单调递减至 0（末帧 offsets 清空，finalize 后落位）
            ns.offsets[i] = (xj - xi) * rem
            ns.offsets[j] = (xi - xj) * rem

        elif etype == "assign":
            i = int(payload["i"])
            # 常量赋值无需插值；若为 j->i 的“视觉拷贝”，让源 j 朝着 i 的槽位靠近
            if "j" in payload and "value" not in payload:
                j = int(payload["j"])
                xi, xj = self._slot_x(i), self._slot_x(j)
                ns.offsets[j] = (xi - xj) * rem

        elif etype == "highlight":
            if "idx" in payload:
                ns.highlight = {int(payload["idx"])}
            elif "start" in payload and "end" in payload:
                a, b = int(payload["start"]), int(payload["end"])
                ns.highlight = set(range(min(a, b), max(a, b) + 1))

        elif etype == "compare":
            ns.compare = (int(payload["i"]), int(payload["j"]))

        elif etype == "mark_sorted":
            ns.sorted_upto = max(ns.sorted_upto, int(payload["upto"]))

        return ns

    def finalize_event(self, st: ArrayBarState, etype: str, payload: dict) -> ArrayBarState:
        ns = _copy_state(st)
        if etype == "swap":
            i, j = int(payload["i"]), int(payload["j"])
            ns.values[i], ns.values[j] = ns.values[j], ns.values[i]
            ns.order[i], ns.order[j] = ns.order[j], ns.order[i]
        elif etype == "assign":
            i = int(payload["i"])
            if "value" in payload:
                ns.values[i] = payload["value"]
            else:
                j = int(payload["j"])
                ns.values[i] = ns.values[j]
        elif etype == "compare":
            # compare 为瞬时：事件结束后清空
            ns.compare = None
        ns.offsets.clear()
        return ns
