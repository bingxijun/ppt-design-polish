# ATELIER NORTH / 建筑工作室

**v4.0 · 5 pages / 5 页**. English studio brief: architecture, anchored labels, portfolio chart, service sequence and an editorial paragraph. / 英文工作室介绍，含建筑标注、数量比较、服务流程与编辑式正文。

[PPTX](business.pptx) · [PDF](business.pdf) · [Source / 文告](inputs/announcement.md) · [Plan / 计划](plan.json) · [Provenance / 来源](composition.json) · [Review / 逐页观察](review.json) · [Validation / 交付检查](validation.json)

![All exported pages / 全部实际导出页](contact-sheet.jpg)

## Reproduce / 复现

Install the repository dependencies. Copy `plan.json`, `source.json`, `inputs/` and `assets/` (if present) to a fresh workspace. / 安装依赖，将计划、来源与素材复制到新的工作区。

```bash
python3 scripts/compose.py compose --workspace /absolute/example-copy
python3 scripts/deck.py --workspace /absolute/example-copy init --slides 5 --mode hybrid
# Set task.outputs to ["pptx","pdf","png"] before building for all formats.
python3 scripts/deck.py --workspace /absolute/example-copy build
python3 scripts/deck.py --workspace /absolute/example-copy render --renderer libreoffice
python3 scripts/deck.py --workspace /absolute/example-copy verify
```

Read `design-audit.json`, inspect every current exported page against the complete source, then record actual reviews and run `finalize`. Included reviews apply only to these files; do not reuse them as evidence for a new export. / 阅读诊断，对照全文实看当前导出稿，再记录真实复查并完成交付；不可套用旧验收。

This is an authored example using the shipped skill, not an independent or blinded model trial. Data and identities are fictional. Source coverage is traceability, not automatic proof of semantic completeness. / 这是使用本包制作的实例，不是独立模型盲测；身份与数据虚构，来源覆盖不等于自动证明语义完整。

Fonts in `plan.design.typography` were installed on the exporting Mac. Use licensed installed alternatives on other systems and recheck shaping and wrapping. Fonts are not distributed. Text, chart data and tables stay native; image pixels are not individually editable. / 其他系统需使用授权可用的本机字体并复查排版；不附带字体。正文与数据为原生对象，图片内部像素不可逐项编辑。

Original fictional image assets and built-in imagegen prompts: [prompts.json](prompts.json). / 原创虚构配图与完整提示词见上。
