#!/usr/bin/env python3
"""Extract reusable reference facts and original media; never modify the source."""
import argparse
import json
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET

from inspect_pptx import inspect_pptx, read_xml, NS


def extract(source, output):
    output = Path(output)
    if output.exists() and any(output.iterdir()):
        raise ValueError("Use a new or empty output directory")
    output.mkdir(parents=True, exist_ok=True)
    inventory = inspect_pptx(source)
    themes, layouts, assets = [], [], []
    with ZipFile(source) as z:
        for name in z.namelist():
            if name.startswith("ppt/theme/") and name.endswith(".xml"):
                root = read_xml(z, name)
                colors = root.find("a:themeElements/a:clrScheme", NS)
                fonts = root.find("a:themeElements/a:fontScheme", NS)
                themes.append({"part": name, "name": root.get("name"),
                               "declared_palette": {c.tag.split('}')[-1]: dict(c[0].attrib) for c in colors if len(c)} if colors is not None else {},
                               "font_scheme_xml": ET.tostring(fonts, encoding='unicode') if fonts is not None else None})
            if name.startswith("ppt/slideLayouts/") and name.endswith(".xml"):
                root = read_xml(z, name)
                placeholders = []
                for shape in root.findall('.//p:sp', NS):
                    ph = shape.find('p:nvSpPr/p:nvPr/p:ph', NS)
                    if ph is not None:
                        placeholders.append({"type": ph.get('type', 'obj'), "index": ph.get('idx'),
                                             "text": [t.text or '' for t in shape.findall('.//a:t', NS)]})
                layouts.append({"part": name, "type": root.get('type'), "placeholders": placeholders})
        media_dir = output / 'assets'
        media_dir.mkdir(exist_ok=True)
        for item in inventory['media']:
            target = media_dir / Path(item['part']).name
            target.write_bytes(z.read(item['part']))
            assets.append({**item, "file": str(target.relative_to(output))})
    report = {"source_sha256": inventory['input_sha256'], "themes": themes, "layouts": layouts,
              "assets": assets, "slide_count": inventory['slide_count'],
              "limitations": "Declared themes and layout placeholders are references, not fully resolved style or semantic layout classifications. Render and inspect before reuse."}
    (output / 'reference.json').write_text(json.dumps(report, ensure_ascii=False, indent=2)+'\n')
    (output / 'inventory.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2)+'\n')
    return {"ok": True, "reference": str((output/'reference.json').resolve()),
            "inventory": str((output/'inventory.json').resolve()), "assets": len(assets)}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(extract(a.source, a.output), ensure_ascii=False))
