import { createRequire } from 'node:module';
import path from 'node:path';
import fs from 'node:fs';
import os from 'node:os';
import { pathToFileURL } from 'node:url';

export function resolvePackage(name) {
  const roots = [
    path.resolve(import.meta.dirname, '..'), process.cwd(),
    ...(process.env.PPT_BEAUTIFY_NODE_MODULES || '').split(path.delimiter).filter(Boolean).map(p => path.dirname(p)),
    path.join(os.homedir(), '.cache/codex-runtimes/codex-primary-runtime/dependencies/node'),
  ];
  for (const root of roots) {
    try { return createRequire(path.join(root, 'package.json')).resolve(name); } catch {}
  }
  return null;
}

export async function loadPackage(name) {
  const location = resolvePackage(name);
  if (!location) throw new Error(`Missing ${name}; install the skill's package.json dependencies or set PPT_BEAUTIFY_NODE_MODULES`);
  return import(pathToFileURL(location).href);
}

export function readJSON(file) { return JSON.parse(fs.readFileSync(file, 'utf8')); }
export function localAsset(file, root) {
  if (typeof file !== 'string' || /^(https?:|data:)/i.test(file)) throw new Error('Use a local asset path');
  const resolved = path.resolve(root, file);
  if (!fs.statSync(resolved).isFile()) throw new Error(`Missing asset ${resolved}`);
  return resolved;
}
