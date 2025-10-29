from __future__ import annotations
import sys
import subprocess
from pathlib import Path
import pytest

def test_cli_tui_smoke(tmp_path: Path):
    # 找到 demos/sort_bubble.py
    root = Path(__file__).resolve().parents[1]
    demo = root / "demos" / "sort_bubble.py"
    assert demo.exists(), demo

    # 用 --exit-after 快速退出；不依赖按键与 TTY
    cmd = [sys.executable, "-m", "algoviz.cli", "tui", str(demo), "--fps", "20", "--speed", "1.0", "--exit-after", "0.5"]
    cp = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=8)
    assert cp.returncode == 0
    # 输出里不作强约束（不同平台 Rich 渲染略异），只需成功退出即可
