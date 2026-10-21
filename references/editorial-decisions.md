# Editorial decisions / 文字、表格与颜色的判断

Read for any full new deck or visual redesign. The outcome is a specific, readable presentation, not a score for whether AI was used. A style rule cannot guarantee perceived authorship.

完整新稿或视觉重设计时阅读。目标是具体、清楚、有设计判断的稿件；不将“AI 痕迹”当成可精确检测的属性，也不承诺任何人都识别不出制作工具。

## Copy before coordinates / 先编辑文字

Read the source as an editor: what must the audience understand, believe, compare or decide? Distinguish facts, interpretations, campaign language and caveats. Preserve uncertainty. Write the page headline after choosing its job, before choosing its geometry.

Ask whether a headline could be pasted into an unrelated deck unchanged. “Experience the future” or “A new chapter of growth” may be valid campaign copy, but they need an actual brand brief; otherwise prefer the concrete subject or a supported finding. Do not automatically add a poetic two-part Chinese headline, an English uppercase kicker, a subheading and a recap to every page. Vary sentence structure because the content differs, not to manufacture randomness. A paragraph can remain a paragraph. Not every sentence needs a bold label, a bullet, an icon or a box.

先确定观众要理解、比较或决定什么，再写标题和排版。检查标题是否换个产品也成立；没有明确品牌表达需要时，把空泛修辞换成具体主题或有证据的结论。不要机械生成“中文两段式标题＋英文小标＋三条粗体小标题＋总结”。也不要把“反 AI”变成禁用所有修辞、彩色或项目符号的新模板。保留真实的作者语气。

When polishing an existing file, inventory all text and numeric qualifiers before rewriting. A shorter headline is not permission to change a claim. Review the rewritten page against the original, including table cells, footnotes and chart definitions.

## Hierarchy and rhythm / 主次与整稿节奏

Choose the dominant evidence and the reading sequence. Allocate area to importance and actual text extent; independent facts need not receive equal rectangles. Use alignment, distance, type size and weight to establish relationships before adding more colors. Equivalent alternatives may deliberately have equal space. Repeated comparison pages can deliberately repeat a layout.

Design the body page as carefully as the cover. Check a representative text page, the hardest table/chart and a page with an image crop before extending a full deck. Look at the sequence: does a chapter or agenda provide real navigation? Remove filler pages in a short deck. Avoid switching compositions merely to satisfy a “variety” count. Keep a stable identity while page purpose determines emphasis.

面积服从信息主次与实际字数，不把所有内容机械等分。真正同级的备选方案可以等宽；连续比较可以复用同一版式。整稿节奏来自内容推进，不来自随机轮换模板。短稿不为了显得完整而硬插目录、章节页和重复大数字。

## Tables are comparisons / 表格先明确比较任务

Decide what readers compare across rows and columns. Put units in headers where that reduces repetition without ambiguity. Give descriptions enough width, align comparable numbers consistently, and retain meaningful precision and missing-value labels. Extract shared specifications into a nearby sentence when repeating them hides actual differences. Keep all material facts and conditions accessible.

Quiet rules and unfilled headers are a useful starting point, not a universal aesthetic law. Use group spacing, a fill, or cell emphasis when it conveys grouping, a decision or a brand requirement. Explain the information being emphasized. Do not color every row/column differently or bold every data cell. A projected table and a reading appendix need different density. Split or restructure before shrinking all cells.

先确定横向、纵向要比较什么。说明列按内容分配宽度，数字对齐；保留单位、精度及“未提供”。共同参数可移到表旁，让差异可见。表头色块、斑马纹、等宽列都应有用途，不能因为库支持就默认套上。小字号不是装下所有资料的唯一办法。

## Color has a job / 每种颜色有职责

Derive the palette from the supplied brand/reference, image treatment or this brief's visual concept. Record roles: background, main text, secondary text, rules, accent and status/series meanings. If no reference exists, choose a defensible concept without making the user pick a theme. Do not map an entire industry to one preset.

Use color when it changes what readers perceive: one focal data point, one unresolved issue, stable category identities, an authentic brand gesture. Multi-series data can require several colors; provide a legend or direct labels and distinguishability beyond hue. Do not paint unrelated key words automatically. Do not use muted gray for every body paragraph; supporting status must be intentional and readable. A monochrome deck can still be generic.

配色从品牌、参考、图像或本次主题推导。强调色对应焦点、类别或状态，不能自动把所有关键词、数字和图表都染成品牌色。灰色仅用于确实次要且可读的信息。单色、宋体、大数字同样可能被滥用；它们不是高级感的保证。

## Typography needs the exported file / 字体以成品为准

Use available, licensed fonts with the required glyphs. `measure_text.mjs` uses real Skia font advances, reserves wrap room and returns explicit line breaks; `compose.py` writes the measured line spacing into native paragraphs. It reports unavailable-family substitutions. Font-family availability does not prove every glyph comes from that family. Office and LibreOffice can shape, space and substitute differently.

Inspect Chinese punctuation, mixed Latin/numeric units, orphan lines, headline breaks, paragraph leading and table alignment in the actual export. Fix wording, box width, grouping or pagination first. A rendered overlap fails review even when the measurement and content contract pass.

实际字体测量用于规划，不是跨软件排版等同证明。检查中英混排、数字与单位、标点、孤行及原生表格；出现挤压或重叠就修源稿重新导出，不能拿“测试通过”替代看图。

## Use the diagnostics in context / 在语境中处理诊断

Read `design-audit.json`: repeated kicker layers, repeated headline cadence, repeated layout geometry and equal table columns are questions for review. For each relevant finding, revise the source or record why repetition helps this deck in the deck review. Do not add random decoration to clear a finding. Zero findings does not certify originality, beauty, completeness or human authorship perception.

查看诊断后，修改有问题的源稿，或在全稿复查中说明合理复用的用途。诊断是审查提示，不是 AI 检测器，也不提供美感分数。交付前仍需逐页看清全部导出稿。
