# src/algoviz/core/timeline.py

from __future__ import annotations


from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

# ====== Easing（默认：easeInOutCubic）======
def _linear(t: float) -> float:
    return float(t)

def _ease_in_out_cubic(t: float) -> float:
    t = float(t)
    return 4 * t * t * t if t < 0.5 else 1 - ((-2 * t + 2) ** 3) / 2

EASING: Dict[str, Callable[[float], float]] = {
    "linear": _linear,
    "easeInOutCubic": _ease_in_out_cubic,
}
DEFAULT_EASING = "easeInOutCubic"


@dataclass
class Event:
    actor: str
    etype: str
    payload: Dict[str, Any]
    duration: int = 1     # 子步数
    easing: Optional[str] = None
    note: Optional[str] = None


@dataclass
class Frame:
    states: Dict[str, Any]
    note: Optional[str] = None


class Timeline:
    def __init__(self, fps: int = 20) -> None:
        self.fps = int(fps)
        self._events: List[Event] = []

    # ===== 事件 API =====
    def add(self, actor: str, etype: str, payload: Dict[str, Any],
            *, duration: int = 1, easing: Optional[str] = None, note: Optional[str] = None) -> "Timeline":
        self._events.append(Event(actor, etype, payload, int(duration), easing, note))
        return self

    def highlight(self, actor: str, *,
                  idx: Optional[int] = None,
                  start: Optional[int] = None,
                  end: Optional[int] = None,
                  duration: int = 1,
                  note: Optional[str] = None) -> "Timeline":
        if idx is None and (start is None or end is None):
            raise TypeError("highlight() requires either idx or start/end")
        payload: Dict[str, Any] = {}
        if idx is not None:
            payload["idx"] = int(idx)
        else:
            payload["start"] = int(start)  # type: ignore[arg-type]
            payload["end"] = int(end)      # type: ignore[arg-type]
        return self.add(actor, "highlight", payload, duration=duration, note=note)

    def compare(self, actor: str, i: int, j: int, *, duration: int = 1, note: Optional[str] = None) -> "Timeline":
        return self.add(actor, "compare", {"i": int(i), "j": int(j)}, duration=duration, note=note)

    def swap(self, actor: str, i: int, j: int, *, duration: int = 10,
             easing: Optional[str] = None, note: Optional[str] = None) -> "Timeline":
        return self.add(actor, "swap", {"i": int(i), "j": int(j)}, duration=duration, easing=easing, note=note)

    def assign(self, actor: str, i: int, j: Optional[int] = None, *,
               value: Optional[float] = None,
               duration: int = 8,
               easing: Optional[str] = None,
               note: Optional[str] = None) -> "Timeline":
        """
        两种用法：
          1) assign(i, j=src)          -> 将 j 槽位的值写到 i
          2) assign(i, value=literal)  -> 将常量写到 i
        """
        payload: Dict[str, Any] = {"i": int(i)}
        if value is not None and j is not None:
            raise TypeError("assign(): specify either j or value, not both")
        if value is not None:
            payload["value"] = value
        elif j is not None:
            payload["j"] = int(j)
        else:
            raise TypeError("assign(): missing j or value")
        return self.add(actor, "assign", payload, duration=duration, easing=easing, note=note)

    def mark_sorted(self, actor: str, upto: int, *, duration: int = 1, note: Optional[str] = None) -> "Timeline":
        return self.add(actor, "mark_sorted", {"upto": int(upto)}, duration=duration, note=note)

    def scaled(self, factor: float) -> "Timeline":
        f = max(0.01, float(factor))
        nt = Timeline(self.fps)
        for ev in self._events:
            dur = max(1, int(round(ev.duration * f)))
            nt._events.append(Event(ev.actor, ev.etype, ev.payload, dur, ev.easing, ev.note))
        return nt

    # ===== 场景辅助 =====
    @staticmethod
    def _resolve_actor(scene: Any, name: str) -> Any:
        if hasattr(scene, "resolve_actor"):
            return scene.resolve_actor(name)  # type: ignore[attr-defined]
        if hasattr(scene, "get"):
            return scene.get(name)  # type: ignore[attr-defined]
        if hasattr(scene, "actors"):
            a = getattr(scene, "actors")
            if isinstance(a, dict) and name in a:
                return a[name]
        raise KeyError(f"actor '{name}' not found in scene")

    @staticmethod
    def _initial_states(scene: Any) -> Dict[str, Any]:
        if hasattr(scene, "initial_state"):
            return scene.initial_state()  # type: ignore[attr-defined]
        if hasattr(scene, "initial_states"):
            return scene.initial_states()  # type: ignore[attr-defined]
        states: Dict[str, Any] = {}
        actors = []
        if hasattr(scene, "actors"):
            a = getattr(scene, "actors")
            actors = list(a.values()) if isinstance(a, dict) else list(a)
        for actor in actors:
            if hasattr(actor, "name") and hasattr(actor, "initial_state"):
                states[getattr(actor, "name")] = actor.initial_state()
        if not states:
            raise RuntimeError("Cannot build initial states from scene; please implement Scene.initial_state()")
        return states

    # ===== 编译为帧序列 =====
    def build_frames(self, scene: Any) -> List[Frame]:
        frames: List[Frame] = []
        states: Dict[str, Any] = self._initial_states(scene)

        for ev in self._events:
            actor = self._resolve_actor(scene, ev.actor)
            steps = max(1, int(ev.duration))
            easing_name = ev.easing or DEFAULT_EASING
            easing_fn = EASING.get(easing_name, _linear)

            for k in range(steps):
                t = (k + 1) / steps
                ns = dict(states)  # 浅拷贝映射
                st = ns[ev.actor]
                if hasattr(actor, "apply_event_step"):
                    ns[ev.actor] = actor.apply_event_step(st, ev.etype, ev.payload, easing_fn(t))  # type: ignore[attr-defined]
                elif hasattr(actor, "apply_event"):
                    ns[ev.actor] = actor.apply_event(st, ev.etype, ev.payload)  # type: ignore[attr-defined]
                else:
                    raise AttributeError(f"actor '{ev.actor}' has no apply_event[_step]()")
                frames.append(Frame(states=ns, note=ev.note))

            # finalize：根据事件类型决定是否“替换最后一帧”
            if hasattr(actor, "finalize_event"):
                last_states = dict(frames[-1].states)
                finalized_actor = actor.finalize_event(last_states[ev.actor], ev.etype, ev.payload)  # type: ignore[attr-defined]

                if ev.etype in ("swap", "assign"):
                    # 持久性事件：最后一帧需体现已落位
                    replaced = dict(frames[-1].states)
                    replaced[ev.actor] = finalized_actor
                    frames[-1] = Frame(states=replaced, note=ev.note)
                    states = replaced
                else:
                    # 瞬时事件（如 compare）：不改最后一帧，但更新下一事件的基线
                    base_next = dict(frames[-1].states)
                    base_next[ev.actor] = finalized_actor
                    states = base_next
            else:
                states = dict(frames[-1].states)

        return frames
