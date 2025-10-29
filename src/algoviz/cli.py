from __future__ import annotations
import argparse
import importlib.util
import sys
from pathlib import Path

from .core.scene import Scene
from .core.timeline import Timeline
from .backends import play_tui
from .backends import play_tui, export_gif, GifOptions
from .backends import play_tui, export_gif, GifOptions, export_svg, SvgOptions


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

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="algoviz", description="Algoviz-TUI CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_tui = sub.add_parser("tui", help="Play timeline in TUI")
    p_tui.add_argument("demo")
    p_tui.add_argument("--fps", type=int, default=20)
    p_tui.add_argument("--speed", type=float, default=1.0)
    p_tui.add_argument("--duration-scale", type=float, default=1.0,
                       help="Scale all event durations (e.g., 1.5 makes animation slower)")
    p_tui.add_argument("--exit-after", type=float, default=None)

    p_gif = sub.add_parser("gif", help="Export timeline as GIF")
    p_gif.add_argument("demo")
    p_gif.add_argument("--outfile", type=str, required=True)
    p_gif.add_argument("--size", type=str, default="640x360")
    p_gif.add_argument("--fps", type=int, default=20)
    p_gif.add_argument("--duration-scale", type=float, default=1.0)
    p_gif.add_argument("--loop", type=int, default=0)
    p_gif.add_argument("--palettesize", type=int, default=256)
    p_gif.add_argument("--subrectangles", action="store_true")

    # 新增 SVG 子命令（M4）
    p_svg = sub.add_parser("svg", help="Export a single frame as SVG")
    p_svg.add_argument("demo")
    p_svg.add_argument("--outfile", type=str, required=True)
    p_svg.add_argument("--size", type=str, default=None, help="WxH in px; omit to rely on viewBox only")
    p_svg.add_argument("--frame", type=str, default="last", help="'first'|'last'|index (0-based)")
    p_svg.add_argument("--background", type=str, default="white")

    ns = parser.parse_args(argv)

    if ns.cmd == "tui":
        scene, tl = _load_demo_from_file(ns.demo)
        if ns.duration_scale != 1.0:
            tl = tl.scaled(ns.duration_scale)
        play_tui(scene, tl, fps=ns.fps, speed=ns.speed, exit_after=ns.exit_after)
        return 0

    if ns.cmd == "gif":
        scene, tl = _load_demo_from_file(ns.demo)
        if ns.duration_scale != 1.0:
            tl = tl.scaled(ns.duration_scale)
        w, h = (int(x) for x in ns.size.lower().split("x"))
        opts = GifOptions(size=(w, h), fps=ns.fps, loop=ns.loop,
                          palettesize=ns.palettesize, subrectangles=bool(ns.subrectangles))
        export_gif(scene, tl, ns.outfile, options=opts)
        return 0

    if ns.cmd == "svg":
        scene, tl = _load_demo_from_file(ns.demo)
        # 解析 frame 选择
        frame_sel = ns.frame.strip().lower()
        if frame_sel == "first":
            idx = 0
        elif frame_sel == "last":
            idx = -1
        else:
            idx = int(frame_sel)
        size = None
        if ns.size:
            w, h = (int(x) for x in ns.size.lower().split("x"))
            size = (w, h)
        opts = SvgOptions(size=size, background=ns.background)
        export_svg(scene, tl, ns.outfile, frame_index=idx, options=opts)
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
