# Algoviz-TUI（暂停进一步开发状态）

Python 算法动画库：**TUI 实时播放 + GIF 导出 + SVG 静态快照**

> 一次记录时间线，多端复用输出：课堂讲解、博客配图、社媒动图，一套代码全部搞定。

---

## ✨ 特性（当前能力）

* **统一时间线 `Timeline`**：以事件（compare / swap / highlight / assign…）记录算法过程，支持帧间插值（`linear`、`easeInOutCubic` 等）。
* **组件化建模**：`ArrayBar`（数组/柱状条）已可用；**Graph（BFS）在 M5 中开发中**。
* **三种后端**

  * **TUI 实时**：终端播放（暂停、单步、倍速、进度跳转、注释侧栏）。
  * **GIF 导出**：离线合成动图；可设尺寸、FPS、循环次数、调色板等。
  * **SVG 静态**：输出任意帧的矢量图（含 `viewBox`、非缩放描边、文本基线等）。
* **CLI 与 Python API 双形态**：`python -m algoviz.cli ...` 或在脚本中 `export_gif/export_svg/play_tui`。
* **测试齐全**：核心/后端/CLI 冒烟、GIF 帧时长与首末帧像素校验、SVG 结构属性断言等。
* **Headless 友好**：GIF 导出默认走非交互后端（如 Matplotlib 的 Agg），适合 CI。([matplotlib.org][1])

---

## 🧪 快速开始

### 安装

```bash
# 建议 3.10+；先克隆仓库
pip install -e ".[dev]"        # 本地可编辑安装（含测试/lint 等开发依赖）
# 或仅运行所需
pip install -e .
```

### 最小示例（Python API）

```python
from algoviz.core.scene import Scene
from algoviz.core.timeline import Timeline
from algoviz.components.arraybar import ArrayBar
from algoviz.backends import export_gif, export_svg, play_tui, GifOptions, SvgOptions

scene = Scene(width=320, height=200)
scene.add(ArrayBar([5,3,4,1,2], name="A", x=20, y=20, bar_width=30, bar_gap=10, height=140))

tl = Timeline(fps=20)
tl.highlight("A", start=0, end=4, note="Init range")
tl.compare("A", 0, 1, duration=2)
tl.swap("A", 0, 1, duration=8, easing="easeInOutCubic")
tl.mark_sorted("A", upto=1)

export_gif(scene, tl, "out.gif", options=GifOptions(size=(640,360), fps=20, loop=0))
export_svg(scene, tl, "snap.svg", options=SvgOptions(size=(640,360)))     # 默认导出最后一帧
# play_tui(scene, tl, fps=20, speed=1.0)  # 终端实时播放（可选）
```

### 命令行（CLI）

```bash
# 1) TUI 播放
python -m algoviz.cli tui demos/sort_bubble.py --fps 20 --speed 1.0 --exit-after 3

# 2) GIF 导出（完整排序动画）
python -m algoviz.cli gif demos/sort_bubble_full.py \
  --outfile out.gif --size 640x360 --fps 20 --loop 0 --palettesize 256 --subrectangles

# 3) SVG 快照（最后一帧）
python -m algoviz.cli svg demos/sort_bubble_full.py \
  --outfile snap.svg --frame last --size 640x360
```

> 小贴士：若在无 GUI 的环境（CI/服务器）出现 Tk/Tcl 报错，请确保使用 **非交互图形后端**（如 Matplotlib 的 Agg），或在环境中显式设置。([matplotlib.org][1])

---

## 🗂 目录结构（核心模块）

```
algoviz/
  core/        # 与渲染无关：时间线/帧/插值/绘制指令
  components/  # 可视化组件：ArrayBar（已完成）、Graph（开发中）
  backends/    # TUI（rich）、GIF（matplotlib+Pillow）、SVG（svgwrite）
  demos/       # 冒泡/插入排序；BFS 网格（M5 将加入）
  cli.py       # 命令行入口
tests/         # 单元与端到端测试（含 GIF/SVG 属性断言）
```

---

## ✅ 里程碑与完成度

### 已完成（M0–M4）

* **M0 项目初始化**：`pyproject.toml`、基本 CI 骨架、README 雏形。
* **M1 核心抽象**：`Timeline/Scene/DrawOps`；`ArrayBar` 组件；基础事件与状态机。
* **M2 TUI 播放器**：暂停/单步/倍速、侧栏提示；命令行 `tui` 子命令。
* **M3 GIF 导出**：`export_gif`，CLI 参数（分辨率/FPS/循环/调色板/子矩形）；**帧时长放慢**（`min_frame_ms`/低 FPS）测试覆盖。
* **M4 SVG 导出**：`export_svg`，可导出最后一帧或指定帧；`viewBox` 与不随缩放变化的描边、文本基线等属性；CLI `svg` 子命令。

> 上述能力均有测试：时间线帧数/事件生效范围、`swap` 插值单调性、GIF 首末帧像素差异、导出总时长对比、SVG 关键属性存在等。

### 进行中（M5）

* **Graph 组件 + BFS demo**

  * `GraphState`（节点/边/访问状态、层次）、事件（`enqueue/visit/dequeue/highlight_path`…）
  * 三后端渲染：Circle/Line/Arrow/Text
  * Demo：网格 BFS，统一时间线 → TUI/GIF/SVG
  * 测试：事件顺序、层次标注、SVG 属性
* **文档站 v1（MkDocs）**：快速上手、API 参考、FAQ、示例（中/英）([mkdocs.org][2])
* **CLI 健壮性**：easing 名称校验、帧索引与尺寸解析错误提示统一化。

### 计划中（0.3.x+）

* Pointer 组件；时间线 JSON 导入/导出；TUI 在线插值/固定步进优化；更多算法（堆、并查集、Dijkstra…）
* CI → PyPI **Trusted Publishing**（免 token，基于 OIDC 的官方方案）([docs.pypi.org][3])
* CHANGELOG 采用 **Keep a Changelog**；版本遵循 **SemVer**（0.y.z 阶段 API 不稳定）([keepachangelog.com][4])

---

## 🧭 路线图（暂停开发状态，主要因为技术问题） |

---
