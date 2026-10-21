> Legacy runtime/design fixture. Current default design examples: [launch](../launch/README.md) and [business](../yellow/README.md).
> 旧版运行或构图示例；当前默认效果请看发布会与商务实例。

# Editable editorial sample / 可编辑演示样稿

Three real PowerPoint slides: an editorial cover, a native line chart with embedded data, and a native table. The example uses synthetic revenue values **12, 18, 25, 31 (¥ million)**. These are illustrative data, not a performance claim or a forecast.

三页真实 PowerPoint：文字封面、含关联工作簿的原生折线图、原生表格。收入数值 **12、18、25、31 百万元**为演示数据，不代表业绩或预测。

[PPTX](sample.pptx) · [PDF](sample.pdf) · [Source / 源工程](deck.json) · [Content contract / 内容约束](contract.json)

The committed PPTX was built from `deck.json`, rendered through LibreOffice, inspected page by page, and accepted by the repository's delivery checks. Microsoft PowerPoint itself was not used to validate this sample. Fonts are Georgia and Hiragino Sans GB on macOS; choose installed equivalents (such as Noto CJK for Chinese) when reproducing on another system. Font files are not bundled.

仓库中的 PPTX 由 `deck.json` 构建，经 LibreOffice 渲染、逐页实看与交付检查通过；本示例尚未在 Microsoft PowerPoint 本体中验证。macOS 使用 Georgia 与 Hiragino Sans GB，其他系统复现时可替换为已安装字体，例如 Noto CJK；不附带字体文件。

To reproduce, install the root npm dependencies, initialize a separate 3-slide native workspace, copy the two JSON files into it, then build, render, inspect, and review. The exact commands and review format are in [the workflow guide](../../docs/QUICKSTART.md#reproduce-the-sample--复现示例).

复现时安装根目录 npm 依赖，初始化独立的三页原生工作区，将两个 JSON 复制进去，再构建、渲染、实看和复查。命令与记录格式见进阶说明。

`python3 scripts/check_example.py` (from the repository root) builds in a temporary directory and checks slide count, required text, native objects, and internal relationships. It does not perform visual review.

在仓库根目录运行上述脚本，可隔离构建并检查页数、必要文字、原生对象及内部关系；该脚本不执行视觉评审。
