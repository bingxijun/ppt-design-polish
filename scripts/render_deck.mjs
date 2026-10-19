// Render the exported PPTX through an available artifact-tool installation.
import fs from 'node:fs/promises';
import path from 'node:path';
import { loadPackage } from './runtime.mjs';

const [input, outputDirectory] = process.argv.slice(2);
if (!input || !outputDirectory) throw new Error('Usage: render_deck.mjs output.pptx qa-directory');
const { FileBlob, PresentationFile } = await loadPackage('@oai/artifact-tool');
const presentation = await PresentationFile.importPptx(await FileBlob.load(path.resolve(input)));
await fs.mkdir(outputDirectory, { recursive: true });
const pages = [];
for (const [index, slide] of presentation.slides.items.entries()) {
  const target = path.resolve(outputDirectory, `slide-${String(index + 1).padStart(3, '0')}.png`);
  const blob = await presentation.export({ slide, format: 'png', scale: 1.5 });
  await fs.writeFile(target, new Uint8Array(await blob.arrayBuffer()));
  pages.push(target);
}
console.log(JSON.stringify({ ok: true, renderer: 'artifact-tool-imported-pptx', pages }));
