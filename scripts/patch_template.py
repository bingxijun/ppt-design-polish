#!/usr/bin/env python3
"""Focused text edits without rebuilding the deck or touching unrelated ZIP parts."""
import argparse
import json
from pathlib import Path
from xml.dom import minidom
from zipfile import ZipFile
import os
import tempfile

from inspect_pptx import NS, inspect_pptx


def patch(source, changes, output):
    source, output = Path(source), Path(output)
    if source.resolve() == output.resolve() or output.exists():
        raise ValueError('Output must be a new file, separate from the source')
    inventory = inspect_pptx(source)
    grouped = {}
    for change in changes:
        slide = change.get('slide')
        if type(slide) is not int or not 1 <= slide <= inventory['slide_count']:
            raise ValueError('Invalid slide number')
        if not isinstance(change.get('old'), str) or not change['old'] or not isinstance(change.get('new'), str):
            raise ValueError('Each edit needs nonempty old text and string new text')
        grouped.setdefault(inventory['slides'][slide-1]['part'], []).append(change)
    modified = {}
    with ZipFile(source) as z:
        for part, edits in grouped.items():
            raw = z.read(part)
            if b'<!DOCTYPE' in raw.upper() or b'<!ENTITY' in raw.upper():
                raise ValueError('Unsupported XML declaration')
            doc = minidom.parseString(raw)
            for edit in edits:
                candidates = []
                for shape in doc.getElementsByTagNameNS(NS['p'], 'sp'):
                    ids = shape.getElementsByTagNameNS(NS['p'], 'cNvPr')
                    if edit.get('shape_id') and (not ids or ids[0].getAttribute('id') != str(edit['shape_id'])):
                        continue
                    for node in shape.getElementsByTagNameNS(NS['a'], 't'):
                        text = ''.join(c.data for c in node.childNodes if c.nodeType in (c.TEXT_NODE, c.CDATA_SECTION_NODE))
                        if text == edit['old']:
                            candidates.append(node)
                if len(candidates) != 1:
                    raise ValueError(f"Expected one exact text-run match for {edit['old']!r}, found {len(candidates)}; select shape_id or use a native editor for multi-run text")
                node = candidates[0]
                for child in list(node.childNodes):
                    node.removeChild(child)
                node.appendChild(doc.createTextNode(edit['new']))
                if edit['new'] != edit['new'].strip():
                    node.setAttribute('xml:space', 'preserve')
            modified[part] = doc.toxml(encoding='utf-8')
        output.parent.mkdir(parents=True, exist_ok=True)
        handle, temporary = tempfile.mkstemp(suffix='.pptx', dir=output.parent)
        os.close(handle)
        try:
            with ZipFile(temporary, 'w') as dst:
                for info in z.infolist():
                    dst.writestr(info, modified.get(info.filename, z.read(info.filename)))
            inspect_pptx(temporary)
            Path(temporary).replace(output)
        finally:
            Path(temporary).unlink(missing_ok=True)
    return {'ok': True, 'output': str(output.resolve()), 'modified_parts': sorted(modified),
            'preservation': 'All other ZIP entry payloads are byte-identical; changed slides retain DOM objects and run formatting'}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('source', type=Path)
    p.add_argument('--changes', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    print(json.dumps(patch(a.source, json.loads(a.changes.read_text()), a.output), ensure_ascii=False))
