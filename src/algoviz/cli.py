from __future__ import annotations
import argparse
import importlib.util
import sys
from pathlib import Path

from .core.scene import Scene
from .core.timeline import Timeline
from .backends import play_tui


def _load_demo_from_file(path: str | Path) -> tuple[Scene, Timeline]:
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(p)

    spec = importlib.util.spec_from_file_location("algoviz_demo", str(p))
    if spec is None or spec.loader is None:
        raise RuntimeError("cannot load demo module")

    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore

    if hasattr(mod, "build"):
        scene, tl = mod.build()  # type: ignore
        if not isinstance(scene, Scene) or not isinstance(tl, Timeline):
            raise TypeError("build() must return (Scene, Timeline)")
        return scene, tl

    # 兼容：模块变量
    if hasattr(mod, "SCENE") and hasattr(mod, "TIMELINE"):
        scene = mod.SCENE
        tl = mod.TIMELINE
        if not isinstance(scene, Scene) or not isinstance(tl, Timeline):
            raise TypeError("SCENE/TIMELINE must be (Scene, Timeline)")
        return scene, tl

    raise AttributeError("demo module must define build() or SCENE/TIMELINE")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="algoviz", description="Algoviz-TUI CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_tui = sub.add_parser("tui", help="Play timeline in TUI")
    p_tui.add_argument("demo", help="Python file that provides build() -> (Scene, Timeline)")
    p_tui.add_argument("--fps", type=int, default=20)
    p_tui.add_argument("--speed", type=float, default=1.0)
    p_tui.add_argument("--exit-after", type=float, default=None, help="Auto exit after N seconds (for CI)")

    ns = parser.parse_args(argv)

    if ns.cmd == "tui":
        scene, tl = _load_demo_from_file(ns.demo)
        play_tui(scene, tl, fps=ns.fps, speed=ns.speed, exit_after=ns.exit_after)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
