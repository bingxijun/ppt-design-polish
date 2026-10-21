---
name: ppt-design-polish
description: "Create, redesign, polish, and review PowerPoint presentations (PPT/PPTX), including editable slides, brand/template reuse, purposeful imagery, and final-export visual review. 创建、重设计、美化与审查 PPT。Use for presentation authoring and design, not text extraction alone."
metadata:
  version: "3.0.0"
---

# PPT Design & Polish

One entry point for story, design, assets, authoring, export, and review. **For a new deck, use the composition system below by default, not a blank JSON canvas.** Do not require users to choose layouts or orchestrate several skills. 图片模型与推理来自宿主；本包提供实际版式、来源检查、分页和导出工具。

Resolve this file's directory as `SKILL_ROOT`. Author user decks in a separate `WORKSPACE`, never inside the installation. Replace command placeholders with actual absolute paths. Respond and author in the user's requested language.

## Routing / 路径选择

| Task | Route | Read when relevant |
|---|---|---|
| New deck from announcement/materials | Semantic content plan → default composition kit → editable/hybrid slides | **[Default composition system](references/composition-system.md)** |
| Creative, artistic, clean, or premium visual redesign | Content-specific visual concept, composition exploration, then a representative body-page proof | [Creative direction](references/creative-direction.md), [art direction](references/art-direction.md) |
| Polish/redesign an existing deck | Render and inventory before rearranging; preserve facts and objects | [Template preservation](references/template-edit.md), [art direction](references/art-direction.md) |
| Template updates or exact text edits | Native editing; scoped patching only when appropriate | [Template preservation](references/template-edit.md) |
| Image-first or poster-like slides | Shared art direction, per-page images, optional native text overlays | [Image direction](references/image-direction.md), [native builder](references/native-build.md) |
| Review only | Render, identify concrete issues and fixes; do not modify | [Visual review](references/visual-review.md) |

Default to native key text, data, labels, and diagrams that need editing, with photos/illustrations on separate layers. Image-first delivery is a distinct mode: pixels inside a generated image are not separately editable. User brand, template, slide count, viewing conditions, and chosen style take priority. References include detailed Chinese guidance; follow them regardless of output language.

## Work / 执行

### Default design system / 默认制作方式

Read [composition-system.md](references/composition-system.md) before a full new deck. A user's reference/brand/template takes priority. Otherwise choose `teal-launch` for product/technology launches and `editorial-yellow` for general business. These are complete layout families with defined image ratios, typographic hierarchy, spacing and annotation rules. They are not palette suggestions.

The user should be able to say “turn this announcement into a presentation.” Infer a sensible page count, read the **entire** material, extract atomic facts with qualifiers, and arrange pages by meaning. Do not copy each paragraph to a slide, insist on three ideas per page, or ask the user to choose among design directions when a default suffices. An exact reference already establishes the direction.

Use `compose.py prepare` to freeze the material. Author `plan.json` with grounded claims and purposeful assets. `compose.py compose` selects semantic layouts and paginates overfull lists into `deck.json`, `contract.json`, and `composition.json`. Use these source objects through the host's mandatory authoring path, or this package's builder where permitted. Then render and review the actual export. Never treat successful compilation as aesthetic validation.

For the default launch appearance, source or generate a coherent product hero **and** detail/context imagery before expanding the deck. Keep key text, data, charts, labels, conditions, prices and dates native. Do not substitute a geometric drawing for a requested product photograph, put every page on one photographic background, or flatten whole slides into images. For real products, use actual supplied/authorized product imagery rather than invented lookalikes.

Match the visual grammar, not just the colors: a strong product hero; large chapter numerals; restrained CJK headline typography; asymmetric photo/text pages; quiet white evidence pages; large single metrics; native comparison tables and charts; precise units, conditions and annotations. Check a representative body page, a data page and the densest page at readable size before calling the default successful.

### Understand and preserve

Infer audience, language, page count, viewing conditions, and output location from available materials. Ask only for missing information that materially changes the result; continue independent work. Explicit PPTX requests require a local PPTX. Use connected cloud tools when the user requests a cloud deck.

For an existing PPTX, render and inspect it, then inventory text, charts, tables, notes, and special objects:

```bash
python3 "<SKILL_ROOT>/scripts/inspect_pptx.py" "/absolute/source.pptx" --output "/absolute/work/before.json"
python3 "<SKILL_ROOT>/scripts/reference_library.py" "/absolute/reference.pptx" --output "/absolute/work/reference"
```

The second tool extracts declared themes, layout placeholders, and original media. It does not infer the complete visual identity; compare actual rendered pages.

### Decide the story and visual language

Use the relevant story and art-direction references. Define each page's job and evidence. Separate supplied facts, calculations, and assumptions. Headlines should express the actual subject or a supported conclusion.

For a custom art direction beyond the defaults, read [creative direction](references/creative-direction.md). Connect a visual concept to the subject and explore alternatives only when useful for the brief. Validate representative body and difficult-content pages. A polished cover or different palette alone does not establish a usable deck. Respect a chosen brand/reference and keep small edits small.

For a full new deck or redesign, keep a short `design-plan.json` with audience, viewing conditions, sources, color/font/grid roles, and page purposes/composition reasons. A small text correction does not need a full design process. Do not put internal plans or image prompts in speaker notes.

Prove the design on representative content and difficult pages before expanding. When already authorized, choose routine layout and palette details without requesting page-by-page approval.

Match comparison, trend, process, structure, evidence, and context to suitable visual forms. Use position, scale, alignment, and weight before color. Give the same meaning the same color across the deck. Avoid defaulting every paragraph to three colored cards, icons, pills, decorative lines, or closing slogans. A restrained text page or a dense reading page may be appropriate.

Add images when they explain, document, contextualize, or support an intended mood. Do not impose a background-image quota. Before generation, decide frame ratio, subject placement, text-safe area, and shared image language. Use actual host search/generation/editing tools. If image generation is unavailable, continue with native design and disclose the specific limitation; never pretend an image was generated.

### Build with an available backend

Read [workspace and commands](references/workflow.md) for the detailed protocol:

```bash
python3 "<SKILL_ROOT>/scripts/deck.py" doctor
python3 "<SKILL_ROOT>/scripts/deck.py" --workspace "/absolute/work" init --slides 8 --mode hybrid
```

- Respect a host's mandatory authoring path; save its source in the workspace and register its PPTX using `adopt`.
- Otherwise this package's JSON → PptxGenJS builder supports native text, charts, tables, shapes/diagrams, images, masters, and notes. Read the native-builder reference for the schema.
- For complex existing decks, prefer native editing over rebuilding that can lose animations, masters, embedded objects, or linked data. The patcher handles only bounded exact text-run replacement.
- Existing HTML/SVG/app exports can enter through `adopt`; inspect the converted objects and final PPTX. A source preview is not final-export validation.

Use real brand/product/source imagery where identity or evidence matters. Do not replace it with generated lookalikes. Do not flatten an entire slide merely to conceal layout problems.

### Constrain and export

`contract.json` can require text, native object minimums, and preservation from an original deck. Check values, units, periods, baselines, and calculations against sources; string presence is not fact-checking.

For Chinese/Japanese/Korean, inspect actual glyph coverage, line breaks, and table fonts. Naming a font in XML does not install it. If text is crowded, improve organization, grouping, and box geometry before repeatedly shrinking the type.

Keep reusable themes/masters as source inputs. Deliver templates when requested; the skill does not authorize uploading or publishing user material.

### Review the actual deliverable

Read the workflow and visual-review references. Render the **exported PPTX**, open every page, and inspect the deck order. Check facts/completeness, legibility/clipping, hierarchy/imagery, consistency, and intended editability. Fix the source, export, render, and review again after meaningful changes.

For design work, also inspect focal hierarchy, typographic craft, purposeful imagery, subject specificity, and the rhythm between pages. Record concrete observations and fixes in review summaries. Technical delivery checks do not certify these judgments; a visibly generic or unfinished result still needs design work when it misses the user's brief.

The CLI binds review records to source/file/image fingerprints. Changed inputs invalidate old reviews. Never edit state files to bypass this behavior. Normal local delivery uses `finalize`; it copies requested outputs only after the current build, renders, all page/deck reviews, content contract, and formats pass.

A missing renderer, unreadable page, missing asset, or unverifiable special object is a concrete limitation. Use `unjudgeable` when a page cannot be inspected. Deliver a clearly labeled incomplete draft only when the user accepts it. Automated checks cannot establish beauty, factual accuracy, or prove an image was viewed.

## Deliver / 交付

Return requested artifacts with material limitations and useful previews. Keep internal QA outside the formal deck and speaker notes. Review-only output should identify slide numbers, observable issues, and practical fixes.

Do not claim arbitrary lossless template reconstruction, all upstream application features, pixel-identical cross-application rendering, or guaranteed “zero AI look.” One skill coordinates methods and tools; it does not create missing models or services.

Attribution: [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md).
