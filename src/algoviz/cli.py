from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Tuple, Optional

from .backends import (
    export_gif, GifOptions,
    export_svg, SvgOptions,
    play_tui,
)
from .core.timeline import Timeline, EASING


def _parse_size(text: str) -> Tuple[int, int]:
    try:
        w_str, h_str = text.lower().split("x")
        w, h = int(w_str), int(h_str)
        if w <= 0 or h <= 0:
            raise ValueError
        return w, h
    except Exception:
        raise argparse.ArgumentTypeError("size 必须是类似 640x360 的正整数格式")

def _positive_int(name: str, v: str) -> int:
    try:
        iv = int(v)
    except Exception:
        raise argparse.ArgumentTypeError(f"{name} 必须是整数")
    if iv <= 0:
        raise argparse.ArgumentTypeError(f"{name} 必须 > 0")
    return iv

def _nonneg_int(name: str, v: str) -> int:
    try:
        iv = int(v)
    except Exception:
        raise argparse.ArgumentTypeError(f"{name} 必须是整数")
    if iv < 0:
        raise argparse.ArgumentTypeError(f"{name} 必须 >= 0")
    return iv

def _load_demo_from_file(path: str):
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"找不到 demo 文件：{p}")
    spec = importlib.util.spec_from_file_location("algoviz_demo_module", str(p))
    if spec is None or spec.loader is None:
        raise RuntimeError(f"无法加载 demo 模块：{p}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules["algoviz_demo_module"] = mod
    spec.loader.exec_module(mod)  # type: ignore
    if not hasattr(mod, "build"):
        raise AttributeError(f"{p} 中未找到 build() 函数")
    scene, tl = mod.build()
    if not isinstance(tl, Timeline):
        raise TypeError("build() 必须返回 (Scene, Timeline)")
    return scene, tl

def _apply_cli_easing(tl: Timeline, easing_name: Optional[str]) -> None:
    if not easing_name:
        return
    key = next((k for k in EASING.keys() if k.lower() == easing_name.lower()), None)
    if key is None:
        valid = ", ".join(sorted(EASING.keys()))
        raise ValueError(f"不支持的 easing：{easing_name}（可选：{valid}）")
    # 把“未显式设置”的事件的 easing 写成字符串 key
    for ev in getattr(tl, "_events", []):
        if getattr(ev, "easing", None) is None:
            ev.easing = key  # type: ignore[attr-defined]

def main() -> int:
    parser = argparse.ArgumentParser(prog="algoviz", description="Algorithm Visualization CLI (TUI / GIF / SVG)")
    sub = parser.add_subparsers(dest="cmd", required=True)

    easing_choices = sorted(EASING.keys())

    # gif
    p_gif = sub.add_parser("gif", help="导出 GIF 动画")
    p_gif.add_argument("demo", help="demo 脚本文件路径（需提供 build()）")
    p_gif.add_argument("--outfile", required=True, help="输出 GIF 文件路径")
    p_gif.add_argument("--size", default="640x360", type=_parse_size, help="画布尺寸，如 640x360")
    p_gif.add_argument("--fps", default=20, type=lambda v: _positive_int("fps", v), help="逻辑帧率（用于采样时间线）")
    p_gif.add_argument("--loop", default=0, type=lambda v: _nonneg_int("loop", v), help="GIF 循环次数（0=无限）")
    p_gif.add_argument("--palettesize", default=256, type=lambda v: _positive_int("palettesize", v), help="调色板大小（2..256）")
    p_gif.add_argument("--subrectangles", action="store_true", help="尽量写入子矩形减少体积")
    p_gif.add_argument("--min-frame-ms", default=40, type=lambda v: _positive_int("min-frame-ms", v),
                       help="每帧最小时长（ms），用于放慢导出速度以及避免过快。")
    p_gif.add_argument("--easing", choices=easing_choices, help="为未指定 easing 的事件设定默认缓动")

    # svg
    p_svg = sub.add_parser("svg", help="导出单帧 SVG")
    p_svg.add_argument("demo", help="demo 脚本文件路径（需提供 build()）")
    p_svg.add_argument("--outfile", required=True, help="输出 SVG 文件路径")
    p_svg.add_argument("--frame", default="last", help="帧索引或 'last'")
    p_svg.add_argument("--size", default="640x360", type=_parse_size, help="画布尺寸，如 640x360")
    p_svg.add_argument("--easing", choices=easing_choices, help="为未指定 easing 的事件设定默认缓动")

    # tui
    p_tui = sub.add_parser("tui", help="在终端播放（可用于快速预览）")
    p_tui.add_argument("demo", help="demo 脚本文件路径（需提供 build()）")
    p_tui.add_argument("--fps", default=20, type=lambda v: _positive_int("fps", v), help="逻辑帧率（生成帧用）")
    p_tui.add_argument("--speed", default=1.0, type=float, help="播放速度倍率（>0）")
    p_tui.add_argument("--exit-after", default=None, type=float, help="自动退出秒数（便于 CI/测试）")
    p_tui.add_argument("--easing", choices=easing_choices, help="为未指定 easing 的事件设定默认缓动")

    ns = parser.parse_args()

    try:
        if ns.cmd == "gif":
            scene, tl = _load_demo_from_file(ns.demo)
            _apply_cli_easing(tl, ns.easing)
            out = Path(ns.outfile); out.parent.mkdir(parents=True, exist_ok=True)
            opt = GifOptions(
                size=ns.size,
                fps=ns.fps,
                loop=ns.loop,
                palettesize=ns.palettesize,
                subrectangles=bool(ns.subrectangles),
                min_frame_ms=ns.min_frame_ms,
            )
            export_gif(scene, tl, str(out), options=opt)
            print(f"[algoviz] GIF 已导出：{out}")
            return 0

        if ns.cmd == "svg":
            scene, tl = _load_demo_from_file(ns.demo)
            _apply_cli_easing(tl, ns.easing)
            out = Path(ns.outfile); out.parent.mkdir(parents=True, exist_ok=True)
            frame_arg = ns.frame
            frame_index: Optional[int] = None if str(frame_arg).lower() == "last" else int(frame_arg)
            if frame_index is not None and frame_index < 0:
                raise ValueError("frame 不能为负数")
            opt = SvgOptions(size=ns.size, frame=frame_index)
            export_svg(scene, tl, str(out), options=opt)
            print(f"[algoviz] SVG 已导出：{out}")
            return 0

        if ns.cmd == "tui":
            scene, tl = _load_demo_from_file(ns.demo)
            _apply_cli_easing(tl, ns.easing)
            play_tui(scene, tl, fps=ns.fps, speed=float(ns.speed), exit_after=ns.exit_after)
            return 0

        parser.print_help()
        return 2

    except Exception as e:
        print(f"[algoviz][error] {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
