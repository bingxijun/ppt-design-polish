// Original unified backend. PptxGenJS is a separately installed MIT dependency.
import fs from 'node:fs/promises';
import path from 'node:path';
import { loadPackage, readJSON, localAsset } from './runtime.mjs';

const [specFile, outputFile] = process.argv.slice(2);
if (!specFile || !outputFile) throw new Error('Usage: build_deck.mjs deck.json output.pptx');
const spec = readJSON(specFile);
const { default: PptxGenJS } = await loadPackage('pptxgenjs');
const pptx = new PptxGenJS();
const canvas = spec.canvas || { width: 13.333333, height: 7.5 };
if (![canvas.width, canvas.height].every(v => Number.isFinite(v) && v > 0)) throw new Error('Invalid canvas inches');
if (!Array.isArray(spec.slides) || !spec.slides.length) throw new Error('slides must be nonempty');
const theme = spec.theme || {};
pptx.defineLayout({ name: 'CUSTOM', width: canvas.width, height: canvas.height });
pptx.layout = 'CUSTOM';
pptx.author = spec.author || 'PPT Design & Polish';
pptx.subject = spec.subject || '';
pptx.title = spec.title || '';
pptx.lang = spec.language || 'zh-CN';
pptx.theme = { headFontFace: theme.headingFont || 'Arial', bodyFontFace: theme.bodyFont || 'Arial', lang: pptx.lang };
const defaults = { fontFace: theme.bodyFont || 'Arial', color: theme.text || '202124', margin: 0,
  breakLine: false, fontSize: theme.bodySize || 22 };
// Masters are explicit PptxGenJS definitions: no fixed card-based slide layout.
for (const master of spec.masters || []) pptx.defineSlideMaster(master);

function geometry(options, label) {
  for (const key of ['x', 'y', 'w', 'h']) {
    if (!Number.isFinite(options?.[key])) throw new Error(`${label}: numeric ${key} in inches required`);
  }
  if (options.w < 0 || options.h < 0) throw new Error(`${label}: negative extent`);
}

for (const [index, source] of spec.slides.entries()) {
  const slide = pptx.addSlide(source.master ? { masterName: source.master } : undefined);
  slide.background = { color: source.background || theme.background || 'FFFFFF' };
  if (source.hidden) slide.hidden = true;
  const elements = source.elements || [];
  for (const [j, obj] of elements.entries()) {
    const options = structuredClone(obj.options || {});
    const label = `Slide ${index + 1}, object ${j + 1}`;
    geometry(options, label);
    if (obj.type === 'text') {
      if (typeof obj.text !== 'string' && !Array.isArray(obj.text)) throw new Error(`${label}: text required`);
      slide.addText(obj.text, { ...defaults, ...options });
    } else if (obj.type === 'image') {
      const imagePath = localAsset(obj.path, path.dirname(specFile));
      const fit = obj.fit || 'contain';
      if (!['contain', 'cover', 'stretch'].includes(fit)) throw new Error(`${label}: invalid image fit`);
      const { x, y, w, h } = options;
      const sizing = fit === 'stretch' ? {} : { sizing: { type: fit, w, h } };
      slide.addImage({ ...options, ...sizing, path: imagePath });
    } else if (obj.type === 'chart') {
      if (!Array.isArray(obj.data) || !obj.data.length) throw new Error(`${label}: chart data required`);
      for (const series of obj.data) {
        if (!Array.isArray(series.values) || !series.values.every(Number.isFinite)) throw new Error(`${label}: numeric chart values required`);
        if (!Array.isArray(series.labels) || series.labels.length !== series.values.length) throw new Error(`${label}: labels/values mismatch`);
      }
      if (options.catAxisLabelPos === undefined) options.catAxisLabelPos = 'low';
      if (['stacked', 'percentStacked'].includes(options.barGrouping) && options.dataLabelPosition === 'outEnd') throw new Error(`${label}: stacked chart labels cannot be outEnd`);
      if (options.secondaryValAxis || options.secondaryCatAxis) throw new Error(`${label}: use a specialist backend for dual-axis charts`);
      const chartType = pptx.ChartType[obj.chartType];
      if (!chartType) throw new Error(`${label}: unsupported chartType ${obj.chartType}`);
      slide.addChart(chartType, obj.data, {
        showLegend: obj.data.length > 1, showValue: false,
        chartColors: theme.seriesColors || [theme.accent || '276B64', 'A4B7B2'],
        titleFontFace: defaults.fontFace, legendFontFace: defaults.fontFace,
        catAxisLabelFontFace: defaults.fontFace, valAxisLabelFontFace: defaults.fontFace,
        showBorder: false, ...options,
      });
    } else if (obj.type === 'table') {
      if (!Array.isArray(obj.rows) || !obj.rows.length) throw new Error(`${label}: table rows required`);
      // Disable auto-pagination: the task's requested slide count is authoritative.
      slide.addTable(obj.rows, { ...defaults, border: { type: 'solid', color: 'D9DEDC', pt: 0.5 },
        margin: 0.08, ...options, autoPage: false });
    } else if (obj.type === 'shape') {
      const type = pptx.ShapeType[obj.shape];
      if (!type) throw new Error(`${label}: invalid shape ${obj.shape}`);
      slide.addShape(type, options);
    } else throw new Error(`${label}: unknown type ${obj.type}`);
  }
  // Source provenance and useful presenter notes, never hidden generation prompts.
  const notes = [source.notes || '', ...(source.sources || []).map(x => `Source: ${x}`)].filter(Boolean).join('\n');
  if (notes) slide.addNotes(notes);
}
await fs.mkdir(path.dirname(path.resolve(outputFile)), { recursive: true });
await pptx.writeFile({ fileName: path.resolve(outputFile) });
console.log(JSON.stringify({ ok: true, output: path.resolve(outputFile), slides: spec.slides.length,
  editable: 'Native text/chart/table/shape objects; images remain images', backend: 'pptxgenjs-4.0.1' }));
