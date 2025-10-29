# Algoviz-TUI

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

## 🧭 路线图（可调整）

| 版本    | 主要内容                                    | 交付                     |
| ----- | --------------------------------------- | ---------------------- |
| 0.2.0 | ArrayBar + 三后端 + CLI + 文档站 v1           | README/Docs/示例产物/CI 全绿 |
| 0.3.x | Graph + BFS Demo；Pointer；JSON 时间线（可阶段化） | 新组件与 demo、测试           |
| 0.4.x | 主题与样式、APNG/MP4 导出（探索）                   | 新后端或格式适配               |

> **SemVer 提示**：在 **0.y.z** 阶段一切都可能变化；1.0.0 才视为稳定公共 API。README/CHANGELOG 中需注明该事实。([Semantic Versioning][5])

---

## 🧰 开发与质量

### 代码规范

* **Ruff**：超快的 Python linter/formatter，一套工具管住 Flake8/isort 等规则集，`pyproject.toml` 可集中配置。([docs.astral.sh][6])
* **Black**：不可妥协的自动格式化（可选；如仅用 Ruff 也可）。([GitHub][7])
* **mypy**：可选的静态类型检查（严格模式建议给 core 层）。

### 测试与覆盖率

```bash
pytest -q                          # 运行全部测试
pytest --cov=algoviz -q            # 带覆盖率
```

* 建议在 CI 使用 `pytest-cov` 并产出 XML 报告（便于徽章/阈值）。([pytest-cov.readthedocs.io][8])

---

## 🖥️ 文档与站点

* 文档基于 **MkDocs**（可选主题：mkdocs/readthedocs 或 Material 生态）
  常用命令：

  ```bash
  mkdocs new docs-site
  mkdocs serve         # 热更新预览
  mkdocs build         # 生成静态站点到 site/
  ```

  主题与配置见官方指南。([mkdocs.org][2])

---

## 🚀 发布（预案）

* **CI**：三平台矩阵（Windows/Linux/macOS）+（Lint/Type/Unit/E2E）
* **PyPI**：推荐 **Trusted Publishing**：

  * 工作流中启用 `id-token: write`，用 `pypa/gh-action-pypi-publish@release/v1` 上传，无需保存 API Token。([docs.pypi.org][3])
  * 结合 GitHub Environments 做更细粒度的发布保护（分支/Tag 规则）。([GitHub Docs][9])
  * 新版 Action 默认产出 **PEP 740 数字佐证（attestations）**，供应链可信度更高。([GitHub][10])
* **版本与变更**：

  * 遵循 **SemVer**；
  * 用 **Keep a Changelog** 模板维护 `CHANGELOG.md`（人读友好、分门别类：Added/Changed/Deprecated/Removed/Fixed/Security）。([keepachangelog.com][4])

---

## 🙌 参与贡献

1. Fork & 创建分支：`feat/xxx`
2. `pip install -e ".[dev]"` 安装依赖
3. 运行 `pytest -q` 确认本地全绿
4. 遵循代码风格（Ruff/Black）、补充/更新测试
5. 提交 PR，描述动机、设计要点与可视化快照（GIF/SVG）

---

## 📃 许可证

MIT（建议；若仓库尚未包含 LICENSE 文件，请添加）

