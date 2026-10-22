// Rasterize pinned upstream artwork; no newly drawn icon or illustration paths.
import fs from 'node:fs/promises';
import path from 'node:path';
import { loadPackage, readJSON } from './runtime.mjs';
const { createCanvas, loadImage } = await loadPackage('@napi-rs/canvas');
const requests = readJSON(process.argv[2]);
for (const request of requests) {
  if (!/^[0-9a-f]{6}$/i.test(request.color)) throw Error('Invalid icon ink');
  const source = await fs.readFile(request.source, 'utf8');
  const svg = source.replaceAll('currentColor', '#'+request.color)
    .replace(/width="24"/, 'width="384"').replace(/height="24"/, 'height="384"');
  const image = await loadImage(Buffer.from(svg));
  const canvas = createCanvas(384, 384);
  canvas.getContext('2d').drawImage(image, 0, 0, 384, 384);
  await fs.mkdir(path.dirname(request.output), {recursive:true});
  await fs.writeFile(request.output, canvas.toBuffer('image/png'));
}
console.log(JSON.stringify({icons:requests.length, source:'Pinned Lucide SVG artwork'}));
