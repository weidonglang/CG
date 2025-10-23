from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from .easing import REGISTRY as EASING_REGISTRY
from .scene import Scene

@dataclass(frozen=True)
class Event:
    actor: str
    etype: str
    payload: Dict[str, Any] = field(default_factory=dict)
    duration: int = 1
    easing: str = "linear"
    note: str | None = None

@dataclass(frozen=True)
class Frame:
    index: int
    states: Dict[str, Any]
    note: str | None = None

class Timeline:
    def __init__(self, fps: int = 20) -> None:
        self.fps = fps
        self._events: List[Event] = []

    # ------------- 通用添加 -------------
    def add(self, actor: str, etype: str, *, payload: Dict[str, Any] | None = None,
            duration: int = 1, easing: str = "linear", note: str | None = None) -> "Timeline":
        if duration <= 0:
            raise ValueError("duration must be >= 1 frame")
        self._events.append(Event(actor, etype, payload or {}, duration, easing, note))
        return self

    # ------------- 语义别名（利于使用与测试） -------------
    def compare(self, actor: str, i: int, j: int, *, duration: int = 1, note: str | None = None) -> "Timeline":
        return self.add(actor, "compare", payload={"i": i, "j": j}, duration=duration, easing="linear", note=note)

    def swap(self, actor: str, i: int, j: int, *, duration: int = 1, note: str | None = None) -> "Timeline":
        return self.add(actor, "swap", payload={"i": i, "j": j}, duration=duration, easing="linear", note=note)

    def highlight(self, actor: str, idx: int | None = None, start: int | None = None, end: int | None = None,
                  *, clear: bool = False, note: str | None = None) -> "Timeline":
        payload = {"idx": idx, "start": start, "end": end, "clear": clear}
        return self.add(actor, "highlight", payload=payload, duration=1, easing="linear", note=note)

    def mark_sorted(self, actor: str, upto: int, *, note: str | None = None) -> "Timeline":
        return self.add(actor, "mark_sorted", payload={"upto": upto}, duration=1, note=note)

    def assign(self, actor: str, i: int, value: float, *, note: str | None = None) -> "Timeline":
        return self.add(actor, "assign", payload={"i": i, "value": value}, duration=1, note=note)

    # ------------- 帧生成 -------------
    def build_frames(self, scene: Scene) -> List[Frame]:
        # 初始化每个 actor 的状态
        current: Dict[str, Any] = {name: actor.initial_state() for name, actor in scene.actors.items()}
        frames: List[Frame] = []
        fidx = 0

        for ev in self._events:
            actor = scene.actors.get(ev.actor)
            if actor is None:
                raise KeyError(f"actor not found: {ev.actor}")
            easing_fn = EASING_REGISTRY.get(ev.easing)
            if easing_fn is None:
                raise KeyError(f"unknown easing: {ev.easing}")

            # 让 actor 生成该事件各帧状态 & 事件结束后的持久状态
            per_step_states, persistent_state = actor.apply_event(current[ev.actor], ev.etype, ev.payload, ev.duration)

            # 叠加到“当前全局状态”，并输出帧
            for k in range(ev.duration):
                # 其他 actor 维持上一帧状态；目标 actor 使用该事件的第 k 帧状态
                fs = {a: current[a] for a in current}
                fs[ev.actor] = per_step_states[k]
                frames.append(Frame(index=fidx, states=fs, note=ev.note))
                fidx += 1

            # 事件结束后更新持久状态（用于后续事件）
            current[ev.actor] = persistent_state

        return frames

    @property
    def events(self) -> List[Event]:
        return list(self._events)
