# Setup and workflow / 环境与操作

## Install and update / 安装与更新

Run the repository's installer with Python 3.9+. It copies only runtime instructions, references, tools, licensed icons, and licenses, without the large documentation images. No API keys or system settings are changed.

使用 Python 3.9+ 运行安装器。安装内容仅包含运行指令、参考资料、工具、授权图标和许可，不包含较大的文档配图；不修改 API key 或系统设置。

```bash
git clone https://github.com/bingxijun/ppt-design-polish.git
cd ppt-design-polish
python3 scripts/install.py --client codex
# Or / 或：python3 scripts/install.py --client claude

# Later, update from the clone / 后续从克隆仓库更新
git pull --ff-only
python3 scripts/install.py --client codex --update
```

`--skills-dir /path/to/skills` overrides the destination. Codex defaults to `${CODEX_HOME:-~/.codex}/skills`; Claude Code defaults to `~/.claude/skills`. Existing installations require `--update`, which retains a complete backup outside the discovery directory (for example, `~/.codex/skills-backups/`). Copy any customizations you want to keep from that backup.

可用 `--skills-dir /path/to/skills` 指定目录。已有同名安装需显式 `--update`，旧目录完整备份在 skill 发现目录之外，例如 `~/.codex/skills-backups/`；如有本地自定义内容，可从备份中取回。

In the installed directory, run `npm install` if `doctor` cannot find PptxGenJS or @napi-rs/canvas. The builder needs Node.js 22+. Python inspection and template patching use the standard library.

若 `doctor` 找不到 PptxGenJS 或 @napi-rs/canvas，在安装目录运行 `npm install`。制作后端需要 Node.js 22+；Python 清点与模板补丁只用标准库。

## Rendering / 渲染环境

| Component / 组件 | Purpose / 用途 |
|---|---|
| LibreOffice + Poppler | Publicly installable final-PPTX → PDF → PNG path / 可公开安装的最终稿渲染路径 |
| Host-provided `@oai/artifact-tool` | Optional alternative for PPTX → PNG; not a public dependency bundled here / 宿主已有时可用于 PNG，不随本项目分发 |
| Host image tools / 宿主图像工具 | Optional image generation/search/editing / 按需生图、搜图与修图 |
| Installed fonts / 本机字体 | Required glyph coverage and layout; especially CJK / 字形覆盖与排版，尤其是中日韩文字 |

Common package-manager commands / 常见安装方式：

```bash
# macOS (Homebrew)
brew install --cask libreoffice
brew install poppler

# Ubuntu / Debian
sudo apt-get install libreoffice-impress poppler-utils fonts-noto-cjk
```

On Windows, install LibreOffice and Poppler and put their executables on PATH; use `python` when `python3` is unavailable. The command workflow is exercised on macOS and CI builds on Linux; Windows rendering has not been tested in this release.

Windows 安装 LibreOffice 与 Poppler 后，将可执行文件加入 PATH；如没有 `python3`，使用 `python`。本版在 macOS 实际验证渲染、Linux CI 验证构建，尚未验证 Windows 渲染。

## Agent usage / 日常使用

Use `$ppt-design-polish` in Codex, or `/ppt-design-polish` in Claude Code. Give materials plus the audience, language, brand reference, and requested output. Existing decks should be attached as files. You normally do not need to run the commands below yourself.

在客户端调用 skill，提供材料及受众、语言、品牌参考与输出要求。已有 PPT 直接提供文件。日常任务通常无需用户手动执行下面的底层命令。

## Default announcement workflow / 默认文告制作

Users only attach materials and invoke the skill. The agent handles the following internal steps; users do not write the plan themselves.

用户附上材料并调用 skill 即可，以下由 agent 内部执行，无需用户编写计划。

1. Read the entire announcement and extract facts with units/conditions. / 通读原文并提取事实与条件。
2. Freeze the source with `compose.py prepare`; write grounded `plan.json`. / 固化来源并编写语义计划。
3. Enable visual defaults; select analytical/relational intent. `visuals.py prepare` resolves typography, icons and image prompts. / 启用默认视觉构成并确定分析或内容关系，工具自动准备字体、图标和配图要求。
4. Execute the host image/source tools and register actual assets; then compose native objects. / 实际调用生图或取图工具并登记素材，再编排原生页面。
5. Render the exported PPTX, inspect all pages and fix visible issues. / 渲染导出稿，逐页看图并修正。

[Automatic visual recipes / 自动视觉配方](../references/visual-defaults.md) · [Plan schema and commands / 完整计划格式与命令](../references/composition-system.md) · [10-page launch source / 发布会源稿](../examples/launch/README.md) · [5-page studio source / 工作室源稿](../examples/yellow/README.md).

## Reproduce the sample / 复现示例

From the repository root / 从仓库根目录运行：

```bash
npm install
python3 scripts/check_example.py
python3 scripts/deck.py --workspace /absolute/work init --slides 3 --mode native
```

Copy `examples/editorial/deck.json` and `contract.json` to that workspace. Use an installed CJK font in `theme.bodyFont` and `theme.headingFont` if needed.

将示例的两个 JSON 复制到工作区；如需，修改主题中的字体为本机实际安装的中文字体。

```bash
python3 scripts/deck.py --workspace /absolute/work build
python3 scripts/deck.py --workspace /absolute/work render --renderer libreoffice
python3 scripts/deck.py --workspace /absolute/work verify
```

Open **all returned page images**. Record actual observations for each page and the whole deck in `.ppt-beautify/review-input.json`; do not copy a generic “pass” from documentation.

打开返回的**全部页面图片**。在 `.ppt-beautify/review-input.json` 中记录每页与全稿的真实观察，不复制通用“通过”文本冒充检查。

```json
[
  {"slide":1,"verdict":"pass","summary":"Replace with actual observations / 填写实际观察","issues":[]},
  {"slide":"deck","verdict":"unjudgeable","summary":"Example only; all pages need review / 仅为格式示例，须逐页检查","issues":[]}
]
```

This is a format example, not a complete passing review. Include slide 2 and 3 for the sample, and mark any unreadable or uninspected page `unjudgeable`.

以上仅演示格式，不是完整验收记录；示例还需第 2、3 页。看不清或未查看的页面应写 `unjudgeable`。

```bash
python3 scripts/deck.py --workspace /absolute/work review --file /absolute/work/.ppt-beautify/review-input.json
python3 scripts/deck.py --workspace /absolute/work finalize
```

Successful delivery goes to `output/`. `task.json` defaults to PPTX; set `"outputs":["pptx","pdf","png"]` before building for additional formats. PDF requires a current PDF from the LibreOffice rendering path.

验收通过后成品进入 `output/`。增加交付格式时，在构建前修改 `task.json`。PDF 必须来自当前 LibreOffice 渲染路径。

## Reuse another backend / 接入其他后端

Keep source files under `code/` or `slides/`, and asset snapshots under `assets/` or `inputs/`, then register the exported PPTX:

源文件放在 `code/` 或 `slides/`，素材快照放在 `assets/` 或 `inputs/`，然后接入最终导出稿：

```bash
python3 scripts/deck.py --workspace /absolute/work adopt --pptx /absolute/export.pptx
python3 scripts/deck.py --workspace /absolute/work render --renderer libreoffice
```

`adopt` does not install or call a service. After tracked inputs, assets, the exported PPTX, or rendered pages change, rebuild/re-adopt and re-render before recording a new review.

`adopt` 不安装或调用服务。受跟踪输入、素材、PPTX 或页面图变化后，需要重建或重新接入、重新渲染并复查。

## Configuration / 环境变量

The compatibility names below are retained intentionally / 以下兼容名称为有意保留：

| Variable / 变量 | Meaning / 含义 |
|---|---|
| `PPT_BEAUTIFY_NODE` | Explicit Node executable / 指定 Node 可执行文件 |
| `PPT_BEAUTIFY_NODE_MODULES` | Existing node_modules directories, separated by the OS path delimiter / 已有依赖目录，按系统路径分隔符分开 |
| `PPT_BEAUTIFY_FONT_DIRS` | Additional font directories for measurement and rendering / 测量与渲染使用的额外字体目录 |

Files outside the tracked workspace directories and changing remote resources are not fingerprinted. Save local snapshots first. Existing `FONTCONFIG_FILE` is respected; no system fonts are installed or modified by this skill.

工作区外文件及动态远端资源不参与摘要追踪，请先保存本地快照。本包尊重已有 `FONTCONFIG_FILE`，不安装或改写系统字体。

## Proof and revision / 打样与返工

For a full new deck or visual redesign, follow [studio-workflow.md](../references/studio-workflow.md): initialize a study, register actual exported candidates, inspect/select, expand the full deck and close located critique issues against the current render. An approved reference can use one reference proof; small text changes need no full study. Users normally only invoke the skill. / 新稿或重设计由 agent 完成打样、选稿与返工，用户无需编写配置。

The new [exhibition example](../examples/studio/README.md) includes six final pages, proof exports and actual revisions. Its independent reader review remains pending; see [evaluation status](EVALUATION.md). / 展览实例附完整证据，独立人工评审仍待完成。
