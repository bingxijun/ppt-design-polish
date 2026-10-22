# Visual assets / 配图来源

- `hero.png`: concept illustration generated with Codex's built-in imagegen tool. It is not an application screenshot or an actual export. Prompt: [hero-prompt.txt](hero-prompt.txt).
- `workflow.svg` / `.png`: project-authored bilingual diagram of the implemented workflow.
- `modes.svg` / `.png`: project-authored comparison of native, hybrid, and image-first delivery; schematic, not screenshots.
- `showcase.png`: layout of actual rendered pages from [the editable example](../../examples/editorial/README.md). Source images are LibreOffice renders of the included PPTX; sample data is illustrative.
- `creative-directions.png`: contact sheet of the three [native editable composition studies](../../examples/creative-directions/README.md), rendered from their PPTX. These are authored alternatives, not a comparative model benchmark. / 三种原生可编辑构图方案的真实导出拼图，用于展示方向，不是模型对照测试。

- `hero.png`：使用 Codex 内置 imagegen 生成的项目概念配图，不是应用截图或真实导出稿；提示词见上方链接。
- `workflow` 与 `modes`：项目原创中英图解，保留可编辑 SVG 和方便浏览的 PNG。
- `showcase.png`：真实示例 PPTX 经 LibreOffice 渲染后的页面拼图，示例数据不代表真实业务。

Project-created visuals are shared under the repository's MIT permission grant to the extent applicable. No third-party logos or font files are distributed. Rendered typography may vary with locally installed fonts.

项目原创视觉在适用范围内按仓库 MIT 授权共享，不分发第三方商标或字体文件；重新渲染时字体可能因环境变化。


## Current composition assets / 当前编排配图

- `composition-workflow.svg/png`: original bilingual workflow diagram, editable SVG source. / 原创双语流程图，附可编辑 SVG。
- `launch-showcase.jpg`, `yellow-showcase.jpg`: montages of actual final-PPTX renders. / 最终 PPTX 实际渲染页的拼图。
- Product/architecture imagery and complete built-in imagegen prompts live under `examples/launch/` and `examples/yellow/`. No commercial reference screenshots, third-party keynote images or font files are included. / 产品与建筑配图及提示词见实例目录，不包含商业模板截图、第三方发布会素材或字体文件。

## 4.0 evidence / 4.0 对照

- `evolution-table.jpg`, `evolution-color.jpg`, `evolution-text.jpg`: labelled compositions of actual frozen v3 exports and reviewed v4 exports, same sources/image assets; not a “without skill” benchmark. / 相同原文与素材的实际版本对照。
- `operations-showcase.jpg`: actual native operations report pages, no generated artwork. / 原生运营简报实际页面。
- Current montages and workflow PNG can be rebuilt with `tools/render-doc-visuals.mjs` using host-provided sharp and current example render state. Labels are explicit SVG typography; slide pixels are not repainted. / 可从当前渲染状态重新生成拼图与图解，使用宿主 sharp；不重画页面内容。

## 4.1 proof workflow / 打样流程

- `studio-workflow.svg/png`: original bilingual diagram of the implemented proof/selection/revision protocol.
- `studio-showcase.jpg`, `studio-proofs.jpg`, `studio-revision.jpg`: montages of actual exported PPTX pages; generated with `tools/render-studio-docs.mjs`, without repainting slide content.
- Fictional gallery image and the built-in imagegen prompt: `examples/studio/assets/gallery.jpg` and `examples/studio/prompts.json`.
- 原创流程图与真实导出拼图；展厅配图为虚构生成概念，图中文字均由原生 PPT 对象覆盖。独立人工评审尚未完成。
# 5.0 actual output / 5.0 实际输出

`visual-defaults-showcase.jpg` and `visual-forms.jpg` composite actual exported PPTX page pixels; they are not generated slide mockups. `visual-defaults-workflow.svg/png` are original bilingual documentation diagrams. Reproduce with `tools/render-visual-docs.mjs` after rendering the example. The fictional lamp hero and separate material detail use built-in imagegen; actual tool prompts and provenance are in `examples/visual-defaults/prompts.json`.

新预览由最终 PPTX 的真实页面组成；双语流程图为项目原创文档图。灯具主视觉及材质特写由内置生图工具实际生成，完整提示词与来源见示例记录。原生文字与数据图形没有被画进这些照片里。
