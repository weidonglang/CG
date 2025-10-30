#algoviz/core/scene.py
from __future__ import annotations
from dataclasses import dataclass
from typing import Dict, Any, List, Protocol
from .drawops import DrawList, DrawOp

class Actor(Protocol):
    name: str
    def initial_state(self) -> Any: ...
    def draw(self, state: Any) -> DrawList: ...
    # apply_event 返回：该事件持续的每一帧状态（长度=duration）与事件结束后要“持久化”的最终状态
    def apply_event(self, state: Any, event_type: str, payload: Dict[str, Any], duration: int) -> tuple[List[Any], Any]: ...

@dataclass
class Scene:
    width: int
    height: int
    actors: Dict[str, Actor]

    def __init__(self, width: int = 80, height: int = 24) -> None:
        self.width = width
        self.height = height
        self.actors = {}

    def add(self, actor: Actor) -> "Scene":
        if actor.name in self.actors:
            raise ValueError(f"Actor name duplicated: {actor.name}")
        self.actors[actor.name] = actor
        return self

    def render(self, frame_states: Dict[str, Any]) -> List[DrawOp]:
        ops: List[DrawOp] = []
        for name, actor in self.actors.items():
            state = frame_states.get(name, actor.initial_state())
            ops.extend(actor.draw(state))
        return ops
