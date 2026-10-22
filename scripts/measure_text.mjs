// Measure text only. This worker never draws or exports artwork.
import readline from 'node:readline';
import fs from 'node:fs';
import path from 'node:path';
import { loadPackage } from './runtime.mjs';
const { createCanvas, GlobalFonts } = await loadPackage('@napi-rs/canvas');
for (const dir of (process.env.PPT_BEAUTIFY_FONT_DIRS || '').split(path.delimiter).filter(Boolean)) {
  if (fs.existsSync(dir)) GlobalFonts.loadFontsFromDir(dir);
}
const ctx = createCanvas(1, 1).getContext('2d');
const families = GlobalFonts.families.map(x => x.family);
if (process.argv.includes('--fonts')) { console.log(JSON.stringify(families)); process.exit(0); }
const noStart = /^[，。！？：；、）》」』】〕〉,.!?;:%]/u;
const noEnd = /[（《「『【〔〈(]$/u;
function tokens(text) {
  // Keep Latin words, values and units together. CJK permits word/character wraps,
  // subject to basic opening/closing punctuation constraints.
  const result=[];
  for (const part of text.match(/\d[\d,.]*(?:\s?(?:km|mm|cm|kg|kWh|kW|ms|min|%|L|分钟|小时|万元|元))?|[A-Za-z][A-Za-z0-9'’/-]*|\s+|[^\s]/gu)||[]) {
    if (/^[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}]/u.test(part)) result.push(...part);
    else result.push(part);
  }
  return result;
}
function headlineTokens(text) {
  // Segment complete CJK runs, preserving the existing numeric/unit tokenizer.
  return (text.match(/[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}]+|[^\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}]+/gu)||[]).flatMap(run=>{
    if (!/^[\p{Script=Han}\p{Script=Hiragana}\p{Script=Katakana}]/u.test(run)) return tokens(run);
    const locale=/[\p{Script=Hiragana}\p{Script=Katakana}]/u.test(run)?'ja':'zh';
    return [...new Intl.Segmenter(locale,{granularity:'word'}).segment(run)].map(x=>x.segment);
  });
}
function measure(q) {
  if (q.op==='fonts') return {families};
  const candidates = [q.font, ...(q.fallbacks || []), 'Arial', 'Liberation Sans', 'DejaVu Sans'].filter(Boolean);
  const chosen = candidates.find(f => GlobalFonts.has(f));
  if (!chosen) throw Error('No usable fonts are installed');
  ctx.font = `${q.bold?'bold ':''}${q.size}px "${chosen.replaceAll('"','')}"`;
  const width = s => ctx.measureText(s).width;
  if (q.op==='width') return {width:width(q.text),font:chosen,substituted:chosen!==q.font};
  const lines=[]; let overlong=false;
  for (const paragraph of String(q.text).split('\n')) {
    const start = lines.length;
    let current='';
    for (const token of q.preferWordBreaks?headlineTokens(paragraph):tokens(paragraph)) {
      const next=current+token;
      // Reserve room for Office/LibreOffice mixed-script automatic spacing.
      // Metrics are a planning aid, not identical shaping across applications.
      if (current.trim() && width(next)>q.width*.92 && !noStart.test(token) && !noEnd.test(current.trimEnd())) {
        lines.push(current.trimEnd()); current=token.trimStart();
      } else current=next;
      if (width(current)>q.width*1.04) overlong=true;
    }
    lines.push(current.trimEnd());
    if (q.balanceLastLine && lines.length-start>1) {
      const last=lines.length-1;
      const target=q.width*.22;
      // Move whole words into an orphaned final line without changing font size,
      // contents, number/unit tokens or the total number of lines.
      const segmenter=new Intl.Segmenter(/\p{Script=Han}/u.test(paragraph)?'zh':'en',{granularity:'word'});
      while (width(lines[last])<target) {
        const words=[...segmenter.segment(lines[last-1])].map(x=>x.segment);
        let moved=''; let accepted=false;
        while (words.length>1) {
          moved=words.pop()+moved;
          const remaining=words.join('').trimEnd(); const candidate=(moved+lines[last]).trimStart();
          if (noStart.test(candidate) || noEnd.test(remaining)) continue;
          if (width(candidate)>q.width*.92 || width(remaining)<q.width*.35) break;
          lines[last-1]=remaining;lines[last]=candidate;accepted=true;break;
        }
        if (!accepted) break;
      }
    }
  }
  const metrics = ctx.measureText('Hg国');
  const lineHeight=Math.max(q.size*(q.leading||1.28),metrics.actualBoundingBoxAscent+metrics.actualBoundingBoxDescent);
  return {lines,widths:lines.map(width),height:lines.length*lineHeight,lineHeight,
    font:chosen,substituted:chosen!==q.font,overlong,engine:'skia-font-metrics',
    limits:'Measured advances and basic line breaking. Final Office export still needs visual inspection.'};
}
for await (const line of readline.createInterface({input:process.stdin,crlfDelay:Infinity})) {
  try { console.log(JSON.stringify({ok:true,...measure(JSON.parse(line))})); }
  catch(e) { console.log(JSON.stringify({ok:false,error:String(e.message||e)})); }
}
