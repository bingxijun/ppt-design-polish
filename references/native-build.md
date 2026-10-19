# 原生、混合与图片式制作后端

本包提供可执行 JSON → PPTX 后端，不需要安装另一套 PPT skill。运行依赖是 Node.js 22+ 和 `pptxgenjs@4.0.1`。优先复用已存在的依赖；缺少时在 skill 的依赖目录安装 `package.json` 所列依赖，或使用宿主规定的制作工具。不要安装或重分发专有 artifact-tool 来补环境。

`PPT_BEAUTIFY_NODE` 可指定 Node；`PPT_BEAUTIFY_NODE_MODULES` 可指定已有的 node_modules 路径。Codex bundled runtime 若实际存在，代码可以复用。直接命令：

```bash
python3 "<SKILL_ROOT>/scripts/deck.py" --workspace "/absolute/work" build
```

## 原生工程

`deck.json` 的画布与对象几何单位为**英寸**，字号为 **pt**。不要混用 HTML 的像素。简单格式如下，具体位置与颜色应来自设计任务：

```json
{
  "title":"方案比较",
  "language":"zh-CN",
  "canvas":{"width":13.333333,"height":7.5},
  "theme":{"background":"FFFFFF","text":"202124","accent":"276B64","headingFont":"实际可用字体","bodyFont":"实际可用字体"},
  "slides":[{
    "elements":[
      {"type":"text","text":"方案比较","options":{"x":0.7,"y":0.6,"w":11.8,"h":0.7,"fontSize":34,"bold":true}},
      {"type":"chart","chartType":"bar","data":[{"name":"示例","labels":["A","B"],"values":[12,18]}],"options":{"x":0.7,"y":1.8,"w":8,"h":4.5,"showValue":true,"valAxisMaxVal":22}},
      {"type":"text","text":"以上仅为格式示例数据","options":{"x":0.7,"y":6.7,"w":11,"h":0.3,"fontSize":12}}
    ],
    "notes":"对听众有用的演讲备注",
    "sources":["原材料或精确来源地址"]
  }]
}
```

不要把示例数字当真实材料。支持的对象：

| type | 内容字段 | 结果 |
|---|---|---|
| text | `text` 字符串或 PptxGenJS rich text runs，`options` | 可编辑文字 |
| chart | `chartType`、`data`、`options` | 原生图表及关联数据 |
| table | `rows`、`options` | 原生表格；不自动增页 |
| image | 本地 `path`、`fit: contain/cover/stretch`、`options` | 图片对象 |
| shape | `shape` 为 PptxGenJS ShapeType 名称、`options` | 原生形状、连线或用户需要的可编辑图解 |

各对象的 `options` 透传相应 PptxGenJS 属性；几何需明确 `x/y/w/h`。`masters` 可放该库的母版定义，页面以 `master` 选择。它是可复用设计工程，不是对现有 PPTX 的无损导入。

中文/日文对象和表格应显式使用已核实覆盖相应字符的字体，可在对象 `options.fontFace` 指定。拉丁字体的自动回退可能在某个渲染器成功、另一个渲染器失败；不能只验证文件里仍有中文字符串。混合语言字体需要分别检查实际字形、行高和断行，不能靠把文字变成图片解决。

图表数据必须有等长的 `labels/values`，数值有限。标签上方留空间，例如按数据范围与单位设置合理坐标上界；不使用误导性轴范围。堆积图标签不放 `outEnd`。复杂双轴/组合图不由简化 JSON 接口猜测生成，使用宿主原生工具或专门源代码再 `adopt`。透传选项不是任意组合已经验证的保证。

## 图片式与混合模式

先按 [图片指导](image-direction.md) 生成或选取实际素材，并放入工作区 `assets/`。每页用一个 `image` 对象覆盖画布即可打包为图片式 PPT；默认 `cover` 会裁切，需看图确认。图片式交付应由用户意图支持。

混合模式将照片/插画作为图片对象，再叠加原生标题、正文和数据对象。不能在整页生图中已经包含正文后又重复叠加同一段。全稿保持统一图像语言；单页修改时只重生成需要改的图，更新后仍使当前复查失效。

页面顺序由 `slides` 数组确定，避免用文件系统字母顺序导致 `10` 在 `2` 前面。内部提示词存于源工程，不放入演讲备注；备注只放讲述和来源。

## 外部后端接入

宿主工具、已有 HTML/SVG 工程、Presenton 等产生的 PPTX 可统一接入：把完整源文件和所需素材保存在工作区 `code/`、`slides/`、`assets/` 或 `inputs/`，然后运行 `adopt --pptx`。此命令不会安装或调用外部服务，也不把缺失的后端标成已实现。

无论哪个后端，后续必须从导出 PPTX 渲染并验收。目标应用与渲染器可能有差异；未经真正检查不能声称 PowerPoint 兼容性已验证。
