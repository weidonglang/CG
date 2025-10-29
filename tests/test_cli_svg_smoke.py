from __future__ import annotations
import sys, subprocess
from pathlib import Path

ART_ROOT = Path(__file__).resolve().parent / "artifacts" / "M4"
ART_ROOT.mkdir(parents=True, exist_ok=True)

def test_cli_svg_smoke():
    root = Path(__file__).resolve().parents[1]
    demo = root / "demos" / "sort_bubble_full.py"
    out = ART_ROOT / "cli_last.svg"
    cmd = [sys.executable, "-m", "algoviz.cli", "svg", str(demo), "--outfile", str(out), "--frame", "last", "--size", "320x180"]
    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=10)
    assert cp.returncode == 0, cp.stderr
    assert out.exists() and out.stat().st_size > 0
