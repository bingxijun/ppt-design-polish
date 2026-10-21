# Third-party notices / 第三方说明

Original orchestration, workspace commands, JSON/native authoring adapter, template patching, reference extraction, content constraints, and fingerprint tracking are implemented by this project. This is an independent project and is not affiliated with the upstream authors.

- **Reused code:** the MIT-licensed `validate_review` function from ICIP-CAS/PPTAgent, pinned to commit `833cda553b343be0e486a93b0b57cac962cdd566`, is adapted in `scripts/vendor/pptagent_review.py`. Unrelated external vision API code is omitted. The original license and copyright are retained in [licenses/PPTAgent.txt](licenses/PPTAgent.txt).
- **Runtime dependency:** `@napi-rs/canvas` 0.1.100, MIT, for font measurement only. Installed separately, including its own native-component notices; no node_modules or fonts are shipped. / 用于实际字体测量，保留依赖自身与原生组件的许可。
- **Runtime dependency:** PptxGenJS 4.0.1 by Brent Ely, MIT. It is installed separately; no node_modules are shipped. Preserve its own license when distributing the dependency.
- **Method inspiration, independent implementation:** PPT Master (preservation/reference workflows), Baoyu slide-deck (art direction and per-slide imagery), PPTAgent (export review and stale-review prevention), and Presenton (reusable themes and multiple production paths). Pinned source links and precise scope appear below and in [docs/DESIGN.md](https://github.com/bingxijun/ppt-design-polish/blob/v4.1.0/docs/DESIGN.md).
- **Not redistributed:** Anthropic's separately licensed PPTX skill, complete upstream applications, image models, search services, cloud accounts, Microsoft PowerPoint, LibreOffice, and the proprietary artifact runtime. Availability depends on the user's host and installed tools.

Project-created documentation graphics and generated concept art are described in [docs/assets/README.md](https://github.com/bingxijun/ppt-design-polish/blob/v4.1.0/docs/assets/README.md). Their conceptual diagrams are not evidence of upstream integrations or comparative quality.

## 第三方复用与能力来源

本包的入口、工作区命令、原生构建适配、模板补丁、参考提取、内容约束与摘要追踪由本项目实现。没有将几个上游仓库整包复制，也不声称继承其所有应用、转换器或服务功能。

## 实际复用代码

- **ICIP-CAS / PPTAgent**，commit `833cda553b343be0e486a93b0b57cac962cdd566`，MIT。
  - 来源：[visual.py / validate_review](https://github.com/icip-cas/PPTAgent/blob/833cda553b343be0e486a93b0b57cac962cdd566/skills/pptagent/scripts/pptagent_runtime/visual.py)。
  - 本包 `scripts/vendor/pptagent_review.py` 保留并独立使用其复查结果校验函数；删除了无关的外部视觉 API 调用代码。
  - 原始许可见 [licenses/PPTAgent.txt](licenses/PPTAgent.txt)。
- **PptxGenJS 4.0.1**，Brent Ely，MIT，作为独立运行依赖。
  - 本包 `package.json` 锁定直接依赖版本；优先复用已安装库。本包不附带其 node_modules。
  - 来源：[PptxGenJS](https://github.com/gitbrent/PptxGenJS)。依赖本身的许可文件应随其安装保留。

## 方法层整合与独立实现

- [PPT Master](https://github.com/hugohe3/ppt-master/tree/b113d23720260c411ee47b2b05a73615f954deeb)：参考其内容保留、参考身份、原生交付与工作区思路；本包没有复制其转换引擎、图标库、模板或完整流程代码。
- [Baoyu slide-deck](https://github.com/JimLiu/baoyu-skills/tree/1567581c26ec29f4216c6e6835415bf30343b0e3/skills/baoyu-slide-deck)：整合风格先行、逐页图像与打包方法；由本包统一 JSON 后端实现图片式/混合交付，不复制完整 skill 或把生成提示词写入正式备注。
- [PPTAgent skill](https://github.com/icip-cas/PPTAgent/tree/833cda553b343be0e486a93b0b57cac962cdd566/skills/pptagent)：吸收源稿/导出稿分开复查与变更后失效的思想；工作区摘要门禁由本包独立实现。
- [Presenton](https://github.com/presenton/presenton/tree/b5fcb91a12473f39ee94445f462155af5bf5854c)：吸收可复用主题、编辑与多种输入/导出后端的产品思路。未集成或分发其完整应用/API；用户已有导出文件可接入本包。
- [Anthropic PPTX 指南](https://github.com/anthropics/skills/tree/dbd4588f9e1033efb41dad4bef2f7947c8993d44/skills/pptx)：调研文件处理、设计与质量检查方法。该目录使用其单独许可，本包不复制或重分发该 skill、文档或脚本。

图像模型、搜索工具、云端账户、PowerPoint/LibreOffice、专有 artifact-tool 并非本包附赠组件。可用性由宿主工具与安装环境决定；缺少时不虚报该能力。
