# Why AI slides look generic / AI PPT 为什么容易雷同

Adding an image model does not automatically create a design process. A model can produce a beautiful isolated picture while the deck still has weak information hierarchy, repetitive layouts, poor evidence, or a broken export. Editing PPTX directly is useful for editability; it is not itself the cause of a generic look.

有生图能力并不等于有设计流程。单张图片可以很好看，但整稿仍可能层级不清、版式重复、证据不足，甚至导出后损坏。直接编辑 PPTX 有助于保留可编辑性，本身并不是“AI 味”的根因。

| Failure pattern / 常见问题 | Design response / 本项目的应对 |
|---|---|
| Writing code before deciding what the page communicates / 未明确页面任务就开始写代码 | Establish audience, evidence, page purpose, and viewing conditions first / 先明确受众、证据、页面任务与观看条件 |
| Default templates become the design / 默认模板代替设计判断 | Define a coherent grid, typography, color roles, and composition choices / 先建立网格、字体、颜色语义和构图原则 |
| Every paragraph becomes a colorful card / 每段内容都变成彩色卡片 | Match the visual form to comparison, trend, structure, process, or evidence / 按比较、趋势、结构、流程或证据选择表达 |
| Images are decoration or full-page workarounds / 配图仅装饰，或整页生图掩盖排版问题 | Use imagery when it explains, documents, contextualizes, or supports the intended mood / 图片用于解释、举证、建立场景或必要情绪 |
| A good source preview is treated as a finished file / 源码预览被当作最终成品 | Re-import/render the exported PPTX; inspect every page / 从最终 PPTX 重新渲染，实看每页 |
| The reviewer approves an old version / 修改后仍沿用旧验收 | Bind review records to the current files and rendered images / 验收绑定当前文件与页面图摘要 |

These are engineering and design hypotheses behind the workflow, not a controlled study proving one universal cause. Background photography is appropriate for some slides; blank space, a chart, a diagram, or a typographic page can be the stronger answer for others.

以上是本项目采用的工程与设计判断，不是证明单一普遍原因的对照研究。某些页面适合背景照片，另一些页面适合留白、图表、图解或纯文字排版。

## What changed in 4.0 / 4.0 的实际修正

We inspected our own compiler, not Codex's private training process. v3 chose geometry from JSON field presence, divided text into equal slots, used fixed bold/gray copy, equal-width colored tables and automatic accents. These choices actively reproduced a common look. The public Codex architecture does not require that particular PPT theme.

本次检查对象是我们自己的编排器，不是不可见的训练过程。v3 根据字段选版、等分正文、统一粗体/灰字、等宽彩色表格并自动强调所有图表；这些代码选择本身就在复制固定样式。

OpenAI's [official design guidance](https://developers.openai.com/blog/designing-delightful-frontends-with-gpt-5-4) describes underspecified frontend prompts falling back to frequent training patterns. Applying that explanation to PPT is **our inference**, not a disclosed PPT-specific training finding. [Codex's public architecture](https://developers.openai.com/blog/codex-as-a-platform) describes model, context, tools and an agent loop, not a mandatory slide palette. [Evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices) supports combining checks with human judgment; passing tests does not certify aesthetics.

官方材料支持“约束不足时容易回到高频模式”的一般解释；迁移到 PPT 是本项目推断，不冒充内部训练事实。文件正确、测试通过、来源覆盖和视觉质量是不同的问题。

| v3 mechanism / 旧逻辑 | v4 mechanism / 修正 |
|---|---|
| Industry → two default styles / 行业映射到两个主题 | Brief-derived design roles; old themes optional / 本次材料推导设计，可选旧主题 |
| Fields → layout / 有字段就选版 | Explicit relation and reason, or custom native frames / 指定表达关系与理由，或原生自定义构图 |
| Equal text slots, estimated character counts / 等分正文、字数估算 | Real Skia font metrics, explicit wrapping/leading and measured flow / 实际字体测量、换行行距与流式排列 |
| Equal colored table columns / 等宽彩色表格 | Measured/configurable widths, numeric alignment, grouping and selective emphasis / 测量或显式列宽、数字对齐、分组和差异强调 |
| Every chart uses accent / 图表统一强调色 | Neutral ink, meaningful focus points, stable series identities / 默认正文色，有意义的焦点及稳定类别 |
| Generic page approval / 泛化验收 | Contextual pattern questions plus all-page exported review / 重复模式提示与最终稿逐页检查 |

During export review, a mixed-script charging paragraph wrapped differently in LibreOffice and collided with the next section despite passing measurement. We added wrap room and explicit native line spacing, then rebuilt and inspected the export. This is why metrics are planning aids rather than a replacement for actual file review.

实际检查发现过中英混排在 LibreOffice 额外换行并挤压下一段，虽测量通过仍须修复。现已加入换行余量与原生行距并重新导出，保留这一过程说明测量不能替代看图。

The user supplied two low-resolution commercial template previews: one white/yellow editorial family, one teal vehicle-launch family. They informed these two examples; they are not licensed reusable assets or verified top-keynote files. Earlier research inspected selected frames from [Apple's official September 2024 event](https://www.youtube.com/watch?v=uarNiSl_uh4&t=3910s), [its iPhone 16 launch material](https://www.apple.com/newsroom/2024/09/apple-introduces-iphone-16-and-iphone-16-plus/) and [Google's launch collection](https://blog.google/products-and-platforms/devices/made-by-google-2024-collection/). We infer principles such as clear focal hierarchy and separating product views, evidence and availability; we do not copy their full decks, palettes or assets.

用户参考只决定对应实例的方向，不成为全行业默认模板。官方发布资料帮助理解焦点、产品视角、证据与上市信息的组织；不复制完整原稿或品牌素材。

[Actual v3/v4 comparisons](../examples/evolution/README.md) retain the same source and images. Three complete v4 examples cover a Chinese launch, an English studio brief and an operational reading report. They are authored demonstrations of this runtime, not independent model trials, automatic aesthetic rankings or proof of perfect document interpretation. The next useful evaluation is a blinded multi-brief review with fixed inputs, target viewers and recorded typography/table/color judgments.

版本对照沿用同样原文与图片，另有三个完整主题示例。它们是本次实际制作与检查的证据，尚不是独立模型盲测，更不能证明“绝无 AI 痕迹”。[编辑判断](../references/editorial-decisions.md)与[编排接口](../references/composition-system.md)给出可执行方法。

## Integration map / 优势整合

This project integrates useful methods into one entry point and implements a smaller, explicit runtime. It does not claim feature parity with every upstream application. Sources below are pinned for attribution; star counts change and are not quality evidence.

本项目将有用方法整合为一个入口，并实现范围明确的运行工具，不宣称覆盖每个上游应用的全部功能。下面固定来源版本以便追溯；Star 数会变化，也不等于设计质量。

| Source / 来源 | Useful core / 吸收的优势 | Implemented here / 本项目落地 |
|---|---|---|
| [PPT Master](https://github.com/hugohe3/ppt-master/tree/b113d23720260c411ee47b2b05a73615f954deeb) | Content/brand preservation and editable delivery / 内容、品牌与原生交付 | PPTX inventory, theme/layout/media extraction, scoped patches, preservation contracts / 清点、主题与素材提取、局部补丁、保留约束 |
| [Baoyu slide-deck](https://github.com/JimLiu/baoyu-skills/tree/1567581c26ec29f4216c6e6835415bf30343b0e3/skills/baoyu-slide-deck) | Art direction before per-slide imagery / 先定美术方向，再逐页生图 | Image planning plus image-first/hybrid packaging / 生图指导与图片式、混合式打包 |
| [PPTAgent](https://github.com/icip-cas/PPTAgent/tree/833cda553b343be0e486a93b0b57cac962cdd566/skills/pptagent) | Separate source review from export review / 区分源稿与导出稿验收 | Final-PPTX rendering, page/deck review records, invalidation after changes / 最终稿渲染、逐页与全稿复查、变更后失效 |
| [Presenton](https://github.com/presenton/presenton/tree/b5fcb91a12473f39ee94445f462155af5bf5854c) | Reusable themes and flexible production paths / 可复用主题与灵活制作路径 | Theme/master configuration and `adopt` for existing exports / 主题、母版配置与导出接入 |

Most integration is independent implementation inspired by these methods. The reused PPTAgent validator and dependency licenses are listed in [THIRD_PARTY_NOTICES.md](../THIRD_PARTY_NOTICES.md). No proprietary Anthropic PPTX skill content is redistributed.

整合主要是参考方法后的独立实现。实际复用的 PPTAgent 校验函数及依赖许可见第三方说明；不重分发 Anthropic PPTX skill 的专有内容。

## Delivery contract / 交付约束

`finalize` checks five groups: current build, current rendering, every-page plus deck reviews, content/object constraints, and requested export formats. Source and image fingerprints detect changes. A technical pass still depends on honest, competent visual inspection and source checking.

`finalize` 检查五组条件：当前构建、当前渲染、全部逐页与全稿记录、内容与对象约束、所需输出格式。摘要可发现文件变化；技术通过仍依赖真实且合格的视觉检查与事实核对。

Editable text, charts, tables, and shapes are native objects. An image's pixels are not individually editable. Target PowerPoint rendering, unusual objects, complex dual-axis charts, and arbitrary template reconstruction require appropriate tools and additional verification.

可编辑文字、图表、表格和形状采用原生对象；图片内部像素并不逐项可编辑。目标 PowerPoint 呈现、特殊对象、复杂双轴图及任意模板重建，仍需合适工具和额外验证。
