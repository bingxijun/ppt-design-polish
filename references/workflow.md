# 运行、恢复与最终交付

当前调用名为 `$ppt-design-polish`。为兼容旧工程，内部 `.ppt-beautify/` 状态目录和 `PPT_BEAUTIFY_*` 环境变量继续保留。

## 工作区

```text
task.json                 页数、制作模式、语言
design-plan.json          需要时记录故事与设计变量
deck.json                 本包原生/混合/图片后端的源工程
contract.json             必需内容、对象和原稿保留约束
assets/                   图片、字体与共享素材
inputs/                   原始材料与原稿副本
slides/                   可选 HTML/SVG 等页面源文件
code/                     可选宿主或其他后端的制作代码
.ppt-beautify/            摘要、草稿、逐页渲染和复查状态
output/                   验收通过的成品
final-report.json         当前验收结论
```

这套工作区让一个入口覆盖不同制作后端。现有工程无需强行迁移文件，但应将本次真正用到的源文件与素材副本放进这些受跟踪目录，避免修改源稿后旧复查仍被使用。外部网站、远端图片或工作区外的可变文件不在摘要追踪范围内，先固化本次使用的本地版本。

## 命令顺序

使用 Python 3.9+；Node 后端要求 Node.js 22+。所有命令共用本文件所在 skill 的绝对目录。

`task.json` 默认输出 PPTX。用户要求额外格式时可设置 `"outputs":["pptx","pdf","png"]`；只输出 PDF 也可设置 `"outputs":["pdf"]`。PDF 输出要求使用本包 LibreOffice 渲染入口生成、绑定并检查该 PDF；PNG 来自最终文件的当前逐页渲染。不要仅修改扩展名完成格式转换。

```bash
python3 "<SKILL_ROOT>/scripts/deck.py" doctor
python3 "<SKILL_ROOT>/scripts/deck.py" --workspace "/absolute/work" init --slides 8 --mode hybrid
```

`doctor` 实际探测 Node、构建库和 artifact 渲染模块是否存在。宿主生图、搜索、文件编辑工具由 agent 从实际工具清单发现，不根据 API key 名称推测。常规运行无需外部模型 API key；生图使用宿主能力，不能用纯文字 CLI 假装已生图。

完成源稿与内容约束后：

```bash
python3 "<SKILL_ROOT>/scripts/deck.py" --workspace "/absolute/work" build
```

使用其他制作工具导出后则接入：

```bash
python3 "<SKILL_ROOT>/scripts/deck.py" --workspace "/absolute/work" adopt --pptx "/absolute/exported.pptx"
```

两者均检查演示页数、记录最终 PPTX 与输入摘要，并清除旧复查。构建的草稿放入 `.ppt-beautify/draft.pptx`。`status` 可读取工作区当前状态，不要求重新创建工程。

## 最终文件渲染

有可用 artifact-tool 时：

```bash
python3 "<SKILL_ROOT>/scripts/deck.py" --workspace "/absolute/work" render --renderer artifact
```

该命令**导入已导出的 PPTX**再渲染，不使用生成时的原始对象。未安装该专有库时不要尝试从公共 npm 安装替代品。另一个支持路径需要已安装 LibreOffice 和 Poppler：

```bash
python3 "<SKILL_ROOT>/scripts/deck.py" --workspace "/absolute/work" render --renderer libreoffice
```

宿主已提供其他原生渲染能力时仍可使用它辅助检查；当前 CLI 的摘要门禁只自动接收以上两个渲染入口。无法使用时不要伪造状态来获得 `complete=true`；说明缺少的渲染能力并保留可继续的草稿。

渲染器不是目标 PowerPoint 本身；有字体替换、特殊对象或高要求交付时应使用目标应用复核。当前验收不宣称像素级跨应用一致。

macOS 的 headless LibreOffice 可能使用 Fontconfig 而不自动发现系统中文字体。本包为该渲染子进程创建临时字体配置，加入实际存在的系统字体目录；`assets/fonts/` 或 `PPT_BEAUTIFY_FONT_DIRS` 可提供额外目录。已有 `FONTCONFIG_FILE` 时保留用户配置，不修改安装的应用或系统字体。字体仍需有正确字形且授权允许使用，最终图像仍须实看。

## 内容约束

`contract.json` 示例：

```json
{
  "required_text":{"2":["2026 年","单位：万元"]},
  "min_objects":{"2":{"native_charts":1},"4":{"native_tables":1}},
  "preserve_from":null
}
```

按真实内容设定；默认空约束不是内容已经验证的证明。只美化时可把 `preserve_from` 设为 `inputs/source.pptx`，详见 [模板与保留](template-edit.md)。运行 `verify` 可提前发现内容或对象缺失；它还检查内部关系目标存在，但不是完整 XSD/Office 验证器。

## 看图并记录

打开返回的每张清晰图，检查全部页面与整体顺序；需要全稿缩略图时使用当前环境的拼图工具辅助。按 [视觉验收](visual-review.md) 修复实际缺陷。

将实际观察写入 `.ppt-beautify/review-input.json`（此目录不作为源稿参与摘要）：

```json
[
  {"slide":1,"verdict":"pass","summary":"根据实际图像填写具体检查结论","issues":[]},
  {"slide":"deck","verdict":"pass","summary":"根据全稿检查填写一致性与内容覆盖结论","issues":[]}
]
```

所有页都需要独立记录，再加一条 `deck`。上面不是可直接提交的完整结果，不要复制空泛语句来假装已检查。`issues` 的每项包含 `severity: blocker/major/minor`、整数页码 `slide`、`description`、`suggested_fix`；有 blocker/major 的记录不能通过。看不到图时用 `unjudgeable`，不要填 pass。

```bash
python3 "<SKILL_ROOT>/scripts/deck.py" --workspace "/absolute/work" review --file "/absolute/work/.ppt-beautify/review-input.json"
python3 "<SKILL_ROOT>/scripts/deck.py" --workspace "/absolute/work" finalize
```

CLI 会拒绝旧输入、旧文件、旧图片和缺页复查。它只能核验记录与版本的对应关系，无法独立证明图片被真正查看、内容属实或设计优美。

## 修复、继续与停止

失败时修改实际源稿 → `build/adopt` → `render` → 看图 → `review` → `finalize`。本版采用保守的全稿失效机制：任一受跟踪输入变化，全部复查过期。不会错误地把共享字体或素材改动当作仅影响一页。

`finalize` 只有在当前构建、当前渲染、全部逐页/全稿记录、内容约束和所需格式都通过时，才把请求的成品复制到 `output/`。PPTX/PDF 使用 `answer` 文件名，已有不同版本则输出带摘要后缀的新文件；PNG 放入按当前稿摘要区分的预览目录。失败返回 `complete=false`、具体检查项与可继续的草稿。

不要编辑状态文件绕过门禁。事实、必需内容与可见缺陷都处理后停止，不为追求抽象“更高级”无限换图或换配色。用户接受未完成草稿时，可直接交付明确标为草稿的文件并说明未完成项，不假称已通过 `finalize`。
