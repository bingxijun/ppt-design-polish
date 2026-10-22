# Automatic visual treatment / 自动视觉构成

Use this first for new decks and open visual redesigns. The user gives ordinary material; the host agent interprets the story and creates the semantic plan. The scripts complete supported chart geometry, type selection and asset preparation. They do not parse arbitrary prose into verified data, invent illustrations, or decide taste independently.

新稿默认先读本文件。用户只需给材料；宿主负责理解含义、保留限定条件并编写语义计划。脚本负责图形、字体、素材准备和布局。用户无需填写 JSON、图表参数、字体名称或坐标。

## Use / 执行

1. Freeze and read the entire source with `compose.py prepare`. Ground claims as in [composition](composition-system.md).
2. Add `visual_defaults` and a meaningful relation/analytical intent to each page. Preserve any supplied brand/template. Choose the accent from brand/reference or the subject's actual materials, rather than assigning an industry color.
3. Run `visuals.py prepare`. Read `visual-report.json` and `asset-requests.json`. It selects installed typography and rasterizes pinned Lucide artwork into matching transparent icons offline.
4. Execute required image requests using the host's image generation/search tools. Copy actual assets into the workspace and register path/purpose/provenance in `plan.assets`. The generated prompt specifies ratio, subject placement, text-safe space and shared palette. A real product's identity must use authorized real imagery. Keep generation prompts outside the formal deck.
5. Compose, build through the permitted backend, render the actual export and inspect. Use [studio proof/revision](studio-workflow.md) when exploring a full design; an established visual recipe/reference can use the adopted-reference proof route. Fix the visible source problem, rather than adding scores or decorating failed layouts.

```bash
python3 "<SKILL_ROOT>/scripts/visuals.py" prepare --workspace "/absolute/work"
python3 "<SKILL_ROOT>/scripts/compose.py" compose --workspace "/absolute/work"
```

## Visual identity / 字体与颜色

```json
{"visual_defaults":{"tone":"precise","accent":"B0772A","background":"F4F3EE","ink":"202623",
 "basis":"Graphite product body, brass hinge and ivory light in the supplied reference.",
 "image_style":"Controlled editorial product photography, believable materials and soft shadows."}}
```

`tone` is `precise`, `editorial` or `expressive`. It changes the type starting point; it is not a complete creative direction. Editorial prefers an installed serif heading; the other tones use a clear sans heading. CJK and Latin candidates are checked against actual installed families. The default scale is 62 pt cover, 34 pt headings, 20 pt body, 18 pt table and 54 pt analytical readouts. Recipe labels use their reading needs. Explicit design/brand typography wins. No fonts are bundled; a missing CJK family produces a warning, not a false glyph-coverage claim. Preview the final glyphs.

标题、正文、数字采用明确层级，正文保持中性墨色；强调色主要用于重要数据点、类别标识或关系。普通正文不逐词变彩色。短末行会尝试按整词回移，保留字号和数值单位；这不是完整的中日韩专业排版引擎。仍需检查实际断行。

## Analytical forms / 分析图默认样貌

Keep the existing grounded `chart.series[].points[{label,value}]` data schema. Values are numeric `$claim` references. Labels/series names may also be grounded references. Set `type:"auto"` plus `intent`. The host decides the relationship; the script must not infer time, causality, distributions or a denominator merely from column names.

| Intent / 含义 | Default result / 默认表现 | Guard / 条件 |
|---|---|---|
| `ranking` 排名 | Sorted horizontal bars, direct values; one meaningful focus accent | Source categories stay paired with values and focus after sorting |
| `trend` 时间变化 | Native line chart in supplied time order | One coherent metric; do not sort by magnitude or silently invent missing periods |
| `share` 同一整体的占比 | Native doughnut and direct category labels; more than 5 parts use bars | Name `whole`; sourced `total` must equal the sum; no negative parts |
| `distribution` 分布 | Native columns in declared bin order, narrow gaps | Supply real precomputed bin counts/intervals; no fabricated raw samples |
| `paired` 前后或两条件 | Editable dumbbell diagram on one shared scale | Exactly 2 matched series, at most 4 tasks; endpoints retain both values |
| `contribution` 贡献拆解 | Editable waterfall diagram with connected running totals | `steps:["total","delta",...,"total"]`; changes must reconcile with sourced end total |

Native bar/line/doughnut charts contain their workbook data. Dumbbell/waterfall recipes use editable measured shapes, connectors and native number labels, not embedded Excel charts. Source data remains in the plan. Do not advertise all recipes as native Excel chart types.

```json
{"title":"$headline","design_reason":"The two periods share identical task categories.",
 "chart":{"type":"auto","intent":"paired","unit":"次","series":[
  {"name":"$before","points":[{"label":"$task_a","value":"$a0"},{"label":"$task_b","value":"$b0"}]},
  {"name":"$after","points":[{"label":"$task_a","value":"$a1"},{"label":"$task_b","value":"$b1"}]}]}}
```

An optional `insight:{value,label,body}` is a sourced adjacent readout for ranking/trend/distribution. Do not turn every chart into a KPI card. `share` supports `center` and optional `center_point`; its sourced number must match that data point, whose category is displayed inside the ring. Keep the denominator and conditions visible. `min/max/major_unit/number_format` remain available; observed values may not be clipped. Bar scale includes zero unless the analytical task explicitly requires a justified specialist composition.

## Diagrams / 内容关系图

`relation:"process"|"cycle"|"hierarchy"` with `diagram.nodes` selects real relational geometry. Nodes need `id` and grounded `title`; optional `body` and `icon`. Do not use a cycle for a one-way process or hierarchy for peer items.

```json
{"relation":"process","title":"$title","design_reason":"These actions are performed in source order.",
 "diagram":{"nodes":[{"id":"sense","title":"$sense","body":"$sense_detail"},
                      {"id":"adjust","title":"$adjust","body":"$adjust_detail"}]}}
```

Process supports 2–5 nodes in order; cycle 2–4 repeated stages. Hierarchy uses each child node's `parent` id, requires one root and no cycles, at most 4 nodes per level and 3 levels. Parent descriptions require a separate explanation/custom composition; two-level diagrams allow leaf descriptions. Three-level diagrams use compact labels. Nodes and connectors are editable. Capacity errors stop instead of shrinking text or discarding content.

For `relation:"capabilities"`, provide an image and 1–3 `items` with title/body. The compiler uses an asymmetric material/detail photograph plus vertically measured explanations and consistent icons. It is a complete composition rather than a grid of equal cards.

## Images, icons and decoration / 配图、图标与装饰

```json
{"role":"cover","title":"$name","design_reason":"A product silhouette with quiet native text on the left.",
 "illustration":{"asset":"hero","subject":"Original fictional graphite desk lamp with a brass hinge.",
 "purpose":"Introduce the silhouette and material character.","placement":"right","product":true}} 
```

`placement` is `left`, `right`, `full`, or `detail` (portrait). `mode` is `generate` or `source`; `identity:"real"` requires `source`. This produces a real asset request and blocks composition if the registered file is missing. `visual-cover` currently places native text on the left, so its illustration must use `placement:"right"`; use a custom frame composition for a different cover. Other explicit page layouts can use other asset placements. The helper never claims that merely writing a prompt generated an image.

Auto icon matching uses the node/item's visible title and body in Chinese or English: sensing, analysis, adjustment, safety, energy, delivery and other covered concepts. It selects from 24 pinned Lucide icons in one consistent stroke language. Unknown concepts remain without an icon; there is no arbitrary decorative fallback. Set semantic `icon` explicitly when context needs it: `sense`, `analyse`, `compute`, `adapt`, `control`, `protect`, `sustain`, `illuminate`, `time`, `route`, `verify`, `structure`, `people`, `power`, `observe`, `discover`, `touch`, `deliver`, `connect`, `listen`, `workflow`, `share`, `schedule`, `scan`. `icon:false` suppresses it. Icons are replaceable transparent image assets, not individually editable paths.

装饰应来自主题本身：灯具的光影、建筑的材质截面、产品的局部细节、内容关系中的引导线。数据页通常让图形本身成为视觉主体。不要为填空白自动增加随机几何图案、表情符号或无含义图标。需要原创装饰插画时，使用真实图像工具生成并检查；不能用“写好了提示词”冒充完成。

## Boundaries / 边界

These are supported starting treatments, not an exhaustive design catalog. Scatter plots, statistical interval inference, Sankey/chord diagrams, maps and arbitrary graph layout are not auto-implemented; select a suitable host backend or custom native composition when needed. Respect image tool availability and provenance. These helpers automate recurring decisions and real output, but authoring-agent review is still required and independent human preference has not been established.
