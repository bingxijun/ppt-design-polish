# Proof, selection and revision / 打样、选稿与返工

For a full new deck or visual redesign, use this workflow to make important design decisions reviewable. Routine text corrections stay small; a user-requested rough draft can remain a clearly labelled draft. A specific approved template/reference can use an adopted-reference proof rather than inventing alternatives. The host reads images and makes decisions; these scripts validate evidence, not taste.

完整新稿或重设计时使用。用户仍只需提供材料。简单改字无需完整打样；已定参考可直接验证参考，粗稿按用户要求交付为草稿。脚本验证证据对应关系，不代替审美判断。

## Choose proof pages / 选择验证页

Read the entire material and define audience, viewing conditions and a concrete visual goal. Choose representative page jobs: usually a body page, data page and difficult-content page, adapted to this brief. There is no universal page count or mandatory chart/photo quota. Record substantive alternatives only where the decision benefits from comparison. Keep facts and page intent fixed; vary spatial hierarchy, typography, visual explanation or image treatment. A color swap alone rarely tests a new composition.

First make a `study-brief.json` outside the tracked source directories, then initialize the ordinary deck workspace and start the study before building the final deck:

```json
{
  "audience":"Curatorial committee",
  "viewing":"Chinese PDF read on a laptop, with readable conditions on the relevant page",
  "visual_goal":"Use a clear reading interval and architectural space to support slower looking",
  "proofs":[
    {"id":"body","job":"Understand the premise and three optional viewing stages"},
    {"id":"data","job":"Compare questionnaire responses and their limitations"},
    {"id":"dense","job":"Read the schedule and completion checks"}
  ],
  "max_revision_rounds":3
}
```

```bash
python3 "<SKILL_ROOT>/scripts/studio.py" --workspace "/absolute/work" begin --brief "/absolute/study-brief.json"
```

`begin` writes tracked `design-study.json` and opts this workspace into `task.design_review:true`. Use meaningful language and proof jobs for this actual task, not the example's wording. Existing sources/render reviews become stale as expected. Changing frozen raw inputs or the study brief requires fresh proofs/selections.

For a fixed reference, a proof entry may be `{"id":"body","job":"Test the approved template with the actual body content","mode":"reference","reason":"User supplied and selected this template"}`. This needs one real candidate. `compare` is the default and needs at least two. The agent selects autonomously within the authorized brief; users need not approve every page.

## Build fair candidates / 制作可比候选

Create separate temporary candidate workspaces. Copy the **same** frozen `inputs/` and `source.json`, author the representative pages, and use the normal compose/build or host export/adopt route. Give each proof page a nonempty content contract, render the exported PPTX and verify it. A multi-page candidate deck can serve several proof groups. Do not improve one variant by dropping inconvenient conditions or changing the survey.

```bash
python3 "<SKILL_ROOT>/scripts/studio.py" --workspace "/absolute/work" register --group body --id a --candidate "/absolute/proof-a" --page 1
python3 "<SKILL_ROOT>/scripts/studio.py" --workspace "/absolute/work" register --group body --id b --candidate "/absolute/proof-b" --page 1
```

Registration checks current exports, source inputs, text contracts and chart-cache equivalence, then freezes PPTX, page pixels and available source JSON. It does not infer semantic equivalence or detect dishonest contracts. Review the underlying source facts too. Candidate ids are immutable; changed variants use new ids or a new study.

Inspect every returned candidate image at readable size. Write one selection JSON per proof group:

```json
{
  "group":"body", "selected":"b",
  "reason":"The viewing premise leads clearly, while the three optional stages remain a quieter secondary reading column.",
  "observations":[
    {"candidate":"a","strength":"A straightforward list with consistent alignment","weakness":"The premise competes with three equally labelled sections"},
    {"candidate":"b","strength":"The premise and the secondary explanations have distinct reading roles","weakness":"This proportion needs concise copy and does not suit a long report"}
  ]
}
```

```bash
python3 "<SKILL_ROOT>/scripts/studio.py" --workspace "/absolute/work" select --file "/absolute/selection.json"
```

The selected variant need not be the new one. Record the rejected variants' actual strengths/tradeoffs, not generic praise. Changing frozen evidence invalidates the selection. Expand the final deck using the chosen visual language while each page's task controls its composition.

## Inspect and repair / 看图返工

Render the full exported deck. Review against the source and actual brief before writing a critique. Inspect focus, reading path, body hierarchy, CJK line breaks, numeric units, table comparisons, crop/annotations and deck rhythm. Record **visible** issues with a normalized location and concrete source edit. Empty `issues` is valid after a genuinely clean inspection; do not manufacture defects to demonstrate the tool.

```json
{
  "summary":"The exported body page has one unintended text collision.",
  "issues":[{
    "id":"body-caption-gap","slide":2,"severity":"major",
    "bbox":[0.08,0.46,0.38,0.16],
    "observation":"The wrapped explanation reaches the caption's first line.",
    "action":"Increase the gap and shorten the explanation without losing its condition."
  }]
}
```

```bash
python3 "<SKILL_ROOT>/scripts/studio.py" --workspace "/absolute/work" critique --file "/absolute/critique.json"
```

Fix the actual source, build/adopt, render, and inspect the affected export again. Resolve with `[{"id":"body-caption-gap","change":"Actual edit made","verification":"What is now visible in the new export","outcome":"fixed"}]`:

```bash
python3 "<SKILL_ROOT>/scripts/studio.py" --workspace "/absolute/work" resolve --file "/absolute/fixes.json"
python3 "<SKILL_ROOT>/scripts/studio.py" --workspace "/absolute/work" status
```

A claimed visual fix needs a different PPTX and different affected page pixels. `current_slide` can map a moved page. A minor limitation can be `outcome:"accepted"` with an explicit rationale; blockers/major issues require a fix. Resolutions bind to the current render and brief; later changes require checking them again. A clean critique on the final export does not erase previously unresolved issues. Revision budget limits repeated loops; remaining problems must be reported rather than silently declared passed.

Complete the normal every-page/deck review and `finalize`. Study-enabled workspaces additionally require current selections and closed critique issues. Legacy workspaces and small edits retain their existing delivery path. A ready study proves records match files; it cannot prove image viewing, taste, originality or complete source understanding.

## Export evidence / 保存可复查证据

```bash
python3 "<SKILL_ROOT>/scripts/studio.py" --workspace "/absolute/work" export --output "/absolute/new-evidence-folder"
```

This copies frozen candidate exports, sources, critiques and the current final file/images into a fresh portable packet. It never alters the original state to obtain a pass. Evidence may contain the actual user's material; publish it only when the user has authorized that material/destination. Our repository's fictional example is intentionally public.

## Independent reader comparison / 独立读者比较

Use `blind_review.py prepare` for actual exported image pairs. Supply a JSON list with `case`, `task` (audience/viewing/page job), `a`, `b` (local PNG/JPG/WebP paths), `a_label` and `b_label`. Anonymous filenames and randomized sides hide condition names; visible styling may still identify a condition. Keep the answer key outside the reader packet and do not publish it alongside a pending review.

```bash
python3 "<SKILL_ROOT>/scripts/blind_review.py" prepare --pairs "/absolute/pairs.json" --output "/absolute/new-reader-pack" --key "/absolute/private-answer-key.json"
python3 "<SKILL_ROOT>/scripts/blind_review.py" summarize --pack "/absolute/new-reader-pack" --ratings "/absolute/returned-ratings.csv" --key "/absolute/private-answer-key.json"
```

Readers open `index.html`/full-size images and fill `ratings.csv` with reviewer code, left/right/tie/unjudgeable per criterion and concrete observations. Share only if the user authorized sending it; preparing a packet does not authorize contacting others. Blank rows remain **pending**, not approval. Summaries are descriptive counts of supplied judgments, with no verified expertise, significance test or universal quality rate. Keep host selections separate from independent human feedback.

本轮如没有独立评审，就写“待评审”。不能用生成方自己的选稿、脚本通过或空白 CSV 冒充设计师盲评，更不能把少量投票包装成“百分百高质量”。
