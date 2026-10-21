import { resolvePackage } from './runtime.mjs';
console.log(JSON.stringify({
  node: process.version,
  native_build: { available: Boolean(resolvePackage('pptxgenjs')), module: resolvePackage('pptxgenjs') },
  font_measurement: { available: Boolean(resolvePackage('@napi-rs/canvas')), module: resolvePackage('@napi-rs/canvas') },
  artifact_renderer: { available: Boolean(resolvePackage('@oai/artifact-tool')), module: resolvePackage('@oai/artifact-tool') },
}));
