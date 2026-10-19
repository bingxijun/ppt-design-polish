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
