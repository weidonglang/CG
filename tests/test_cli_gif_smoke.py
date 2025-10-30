#tests/以下内容都是测试代码
from __future__ import annotations
import sys, subprocess
from pathlib import Path

ART_ROOT = Path(__file__).resolve().parent / "artifacts" / "M3"
ART_ROOT.mkdir(parents=True, exist_ok=True)

def test_cli_gif_smoke():
    root = Path(__file__).resolve().parents[1]
    demo = root / "demos" / "sort_bubble_full.py"   # 改为完整排序的 demo
    out = ART_ROOT / "cli_full_bubble.gif"

    cmd = [
        sys.executable, "-m", "algoviz.cli", "gif", str(demo),
        "--outfile", str(out),
        "--size", "320x180",
        "--fps", "20",
        "--loop", "0",
        "--palettesize", "128",
        "--subrectangles",
    ]
    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=20)
    assert cp.returncode == 0, cp.stderr
    assert out.exists() and out.stat().st_size > 0
