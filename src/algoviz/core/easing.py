from __future__ import annotations
from typing import Callable, Dict

EasingFn = Callable[[float], float]

def linear(t: float) -> float:
    return t

def ease_in_out_quad(t: float) -> float:
    # 常见的二次缓入缓出：0→0.5 区间加速，0.5→1 减速
    # 参考：通用 easing 的数学定义（f(0)=0, f(1)=1）及二次型示例。
    # （M1 先保留钩子，后续事件可选用）
    if t < 0.5:
        return 2 * t * t
    t = 1 - t
    return 1 - 2 * t * t

REGISTRY: Dict[str, EasingFn] = {
    "linear": linear,
    "ease_in_out_quad": ease_in_out_quad,
}
