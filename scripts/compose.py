#!/usr/bin/env python3
"""Ground an agent's semantic plan, paginate it, and compose editable launch slides.

No language-model or image-generation API is hidden here. The host agent reads the
whole source and writes plan.json. This compiler checks traceability and provides
actual reusable layouts rather than asking each agent to invent coordinates.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
PRESETS = json.loads((ROOT/'references/launch-presets.json').read_text())
W, H = 13.333333, 7.5


def write(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def prepare(source, workspace):
    source, workspace = Path(source), Path(workspace)
    target = workspace/'inputs/announcement.md'
    if (workspace/'source.json').exists() or target.exists():
        raise ValueError('Source workspace exists; use a new workspace to preserve provenance')
    raw = source.read_text(encoding='utf-8')
    units = [{'id': f'p{i:03}', 'text': p.strip(), 'kind': 'heading' if p.lstrip().startswith('#') else 'content'}
             for i, p in enumerate(re.split(r'\n\s*\n', raw.strip()), 1) if p.strip()]
    if not units:
        raise ValueError('Empty announcement')
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(raw, encoding='utf-8')
    data = {'sha256': hashlib.sha256(target.read_bytes()).hexdigest(), 'path': 'inputs/announcement.md', 'units': units}
    write(workspace/'source.json', data)
    return data


def numbers(text):
    # A conservative lexical check, not semantic fact verification. Preserve units
    # and qualifiers in claims; the agent must review paraphrases and calculations.
    return {float(x.replace(',', '')) for x in re.findall(r'(?<![\d.])\d[\d,]*(?:\.\d+)?', str(text))}


def references(value):
    if isinstance(value, str) and value.startswith('$'):
        yield value[1:]
    elif isinstance(value, dict):
        for key, item in value.items():
            if key not in ('notes',):
                yield from references(item)
    elif isinstance(value, list):
        for item in value:
            yield from references(item)


def validate(plan, source, workspace):
    raw = (workspace/source['path']).read_bytes()
    if hashlib.sha256(raw).hexdigest() != source['sha256'] or plan.get('source_sha256') != source['sha256']:
        raise ValueError('Announcement changed; prepare a new source index and re-ground the plan')
    units = {u['id']: u for u in source['units']}
    claims = plan.get('claims', {})
    used = set(references(plan.get('slides', [])))
    covered, provenance = set(), {}
    if not plan.get('slides'):
        raise ValueError('Plan needs slides')
    unused = set(claims)-used
    deferred = plan.get('unpresented_claims', {})
    if set(deferred) != unused or any(not isinstance(v, str) or not v.strip() for v in deferred.values()):
        raise ValueError(f'Every unpresented claim needs an explicit reason: {sorted(unused)}')
    for key in used:
        if key not in claims:
            raise ValueError(f'Unknown claim ${key}')
        claim = claims[key]
        if not isinstance(claim.get('text'), str) or not claim['text'].strip():
            raise ValueError(f'Claim {key} needs text')
        evidence = claim.get('evidence', [])
        if not evidence:
            raise ValueError(f'Claim {key} needs exact source evidence')
        quotes = []
        for anchor in evidence:
            unit, quote = anchor.get('unit'), anchor.get('quote')
            if unit not in units or not isinstance(quote, str) or not quote.strip() or quote not in units[unit]['text']:
                raise ValueError(f'Claim {key}: evidence is not an exact quote of {unit}')
            quotes.append(quote)
            covered.add(unit)
        if not numbers(claim['text']).issubset(numbers(' '.join(quotes))):
            raise ValueError(f'Claim {key}: displayed number is absent from quoted source')
        provenance[key] = evidence
    omitted = plan.get('omitted', [])
    omitted_ids = set()
    for item in omitted:
        if item.get('unit') not in units or not item.get('reason', '').strip():
            raise ValueError('Every omitted source unit needs a valid id and reason')
        if item['unit'] in omitted_ids or item['unit'] in covered:
            raise ValueError('Omission duplicates a covered/omitted source unit')
        omitted_ids.add(item['unit'])
    missing = {u['id'] for u in units.values() if u['kind'] == 'content'} - covered - omitted_ids
    if missing:
        raise ValueError(f'Unaccounted source paragraphs: {sorted(missing)}')
    return {'used_claims': sorted(used), 'covered_units': sorted(covered), 'omitted': omitted,
            'unpresented_claims': deferred, 'provenance': provenance}


def choose_layout(slide):
    if slide.get('layout'):
        return slide['layout']
    role = slide.get('role', 'content')
    if role in ('cover', 'agenda', 'chapter', 'close'):
        return role
    if slide.get('chart'):
        return 'chart'
    if slide.get('rows'):
        return 'comparison'
    if slide.get('events'):
        return 'timeline'
    if slide.get('annotations'):
        return 'annotated'
    if slide.get('images'):
        return 'photo-grid'
    if slide.get('metric'):
        return 'statement'
    if slide.get('metrics') and slide.get('image'):
        return 'overview'
    if slide.get('secondary_image'):
        return 'spread'
    if slide.get('image'):
        return 'feature'
    return 'text'


def resolve(ref, plan):
    if not isinstance(ref, str) or not ref.startswith('$') or ref[1:] not in plan['claims']:
        raise ValueError(f'Visible content must reference a grounded claim, got {ref!r}')
    return plan['claims'][ref[1:]]['text']


def text_weight(text):
    return sum(1 if ord(c) > 255 else .52 for c in text)


def paginate(slides, plan):
    result = []
    for original in slides:
        slide = copy.deepcopy(original)
        layout = choose_layout(slide)
        slide['layout'] = layout
        # Bound list lengths and actual text volume. Never silently drop items or
        # shrink everything to make it fit. Fixed slide-count requests are checked.
        key, capacity, budget = ('items', 4, 250)
        if layout == 'feature': capacity, budget = 3, 150
        if layout == 'agenda': capacity, budget = 4, 100
        if layout == 'spread': capacity, budget = 2, 90
        if layout == 'timeline': key, capacity, budget = 'events', 4, 220
        if layout == 'comparison': key, capacity, budget = 'rows', 6, 300
        items = slide.get(key, [])
        if layout == 'comparison':
            header, items = items[:1], items[1:]
        else: header = []
        groups, group, weight = [], [], 0
        for item in items:
            item_weight = sum(text_weight(resolve('$'+r, plan)) for r in references(item))
            if item_weight > budget:
                raise ValueError('A single content item exceeds the layout budget; split the claim semantically')
            if group and (len(group) >= capacity or weight + item_weight > budget):
                groups.append(group); group, weight = [], 0
            group.append(item); weight += item_weight
        if group: groups.append(group)
        for i, chunk in enumerate(groups or [[]]):
            page = copy.deepcopy(slide)
            if items: page[key] = header + chunk
            page['continuation'] = i
            result.append(page)
    if plan.get('slide_count') is not None and len(result) != plan['slide_count']:
        raise ValueError(f"Content needs {len(result)} slides, requested {plan['slide_count']}; regroup without dropping facts")
    return result


class Composer:
    def __init__(self, plan, workspace):
        self.plan, self.workspace = plan, workspace
        name = plan.get('style', 'auto')
        if name == 'auto':
            name = 'teal-launch' if plan.get('kind') == 'product-launch' else 'editorial-yellow'
        if name not in PRESETS: raise ValueError(f'Unknown style {name}')
        self.style_name = name
        self.t = copy.deepcopy(PRESETS[name])
        self.t.update(plan.get('fonts', {}))
        self.assets = plan.get('assets', {})
        self.slides, self.contract, self.manifest = [], {}, []
        self.e = []

    def txt(self, text, x, y, w, h, size=18, color=None, font=None, **options):
        # Fit estimates catch obvious overflow before export. Actual glyph metrics
        # differ across Office/font engines, so rendering remains mandatory.
        estimated_lines = sum(max(1, math.ceil(text_weight(line)*size/(w*72))) for line in text.split('\n'))
        if estimated_lines*size*1.1 > h*72 + 5:
            raise ValueError(f'Text does not fit {size}pt box: {text[:70]!r}; shorten or repaginate')
        self.e.append({'type': 'text', 'text': text, 'options': {
            'x': x, 'y': y, 'w': w, 'h': h, 'fontSize': size,
            'fontFace': font or self.t['bodyFont'], 'color': color or self.t['ink'],
            'margin': 0, 'breakLine': False, 'valign': 'mid', 'paraSpaceAfterPt': 0, **options}})

    def content(self, ref, *args, **kwargs):
        self.txt(resolve(ref, self.plan), *args, **kwargs)

    def rect(self, x, y, w, h, fill, transparency=0):
        self.e.append({'type': 'shape', 'shape': 'rect', 'options': {
            'x': x, 'y': y, 'w': w, 'h': h, 'line': {'transparency': 100},
            'fill': {'color': fill, 'transparency': transparency}}})

    def line(self, x, y, w, color=None):
        self.e.append({'type': 'shape', 'shape': 'line', 'options': {
            'x': x, 'y': y, 'w': w, 'h': 0, 'line': {'color': color or self.t['rule'], 'width': .6}}})

    def image(self, name, x, y, w, h):
        if name not in self.assets: raise ValueError(f'Missing asset {name}; source/generate it before composing')
        entry = self.assets[name]
        file = Path(entry['path'])
        if file.is_absolute() or '..' in file.parts or not (self.workspace/file).is_file():
            raise ValueError('Assets must be frozen inside the workspace')
        if not entry.get('provenance') or not entry.get('purpose'):
            raise ValueError(f'Asset {name} needs provenance and purpose')
        self.e.append({'type': 'image', 'path': file.as_posix(), 'fit': entry.get('fit', 'cover'),
                       'options': {'x': x, 'y': y, 'w': w, 'h': h}})

    def chrome(self, slide, page, dark=False):
        color = 'D2E4E3' if dark else self.t['muted']
        self.txt(self.plan.get('brand', 'PRESENTATION'), .65, .28, 5, .25, 10, color,
                 self.t['latinFont'], bold=True, charSpacing=2)
        self.txt(slide.get('section', ''), 8.5, .28, 4.16, .25, 9, color, align='right')
        self.txt(f'{page:02}', 12.2, 6.97, .47, .22, 9, color, self.t['latinFont'], align='right')
        if slide.get('footnote'):
            self.content(slide['footnote'], .65, 6.93, 11.1, .31, 9, color)

    def heading(self, s):
        if s.get('kicker'):
            self.txt(s['kicker'].upper(), .65, .83, 11.8, .23, 10, self.t['accent'], self.t['latinFont'], charSpacing=2)
        self.content(s['title'], .65, 1.15, 11.9, .65, 32, font=self.t['headingFont'])
        if s.get('subtitle'):
            self.content(s['subtitle'], .68, 1.91, 11.8, .38, 13, self.t['muted'])

    def items(self, items, x, y, w, height, dark=False):
        if not items: return
        row = height/len(items)
        color, muted = ('FFFFFF', 'C6DCDB') if dark else (self.t['ink'], self.t['muted'])
        for i, item in enumerate(items):
            yy = y+i*row
            self.line(x, yy, w, '39636B' if dark else None)
            if isinstance(item, str):
                self.content(item, x, yy+.16, w, row-.24, 18, color)
            else:
                self.content(item['title'], x, yy+.16, w, .38, 19, color, bold=True)
                if item.get('body'):
                    self.content(item['body'], x, yy+.66, w, row-.75, 15, muted, valign='top')

    def render(self, s, page):
        self.e = []
        layout, t = s['layout'], self.t
        background = t['background']
        if layout == 'cover':
            if t['cover'] == 'cinematic':
                self.image(s['image'], 0, 0, W, H)
                self.chrome(s, page, True)
                self.content(s['title'], .7, 1.42, 6.8, 1.7, 42, 'FFFFFF', t['headingFont'])
                if s.get('subtitle'): self.content(s['subtitle'], .74, 3.35, 5.3, .55, 16, 'D2E4E3')
                if s.get('body'): self.content(s['body'], .74, 5.92, 4.8, .7, 12, 'D2E4E3')
            else:
                self.image(s['image'], 6.75, 0, 6.59, H)
                self.rect(0, 0, 6.75, H, t['paper'])
                self.rect(.65, 1.17, .65, .11, t['highlight'])
                self.chrome(s, page)
                self.content(s['title'], .65, 1.75, 5.9, 2.1, 40, font=t['headingFont'], bold=True)
                if s.get('subtitle'): self.content(s['subtitle'], .68, 4.18, 5.3, .7, 18)
                if s.get('body'): self.content(s['body'], .68, 5.9, 5.5, .65, 12, t['muted'])
        elif layout == 'chapter':
            dark = t['chapter'] == 'dark'
            background = t['dark'] if dark else t['paper']
            self.chrome(s, page, dark)
            self.txt(s.get('chapter', '01'), .65, 1.08, 5, 2.1, 130,
                     '31616A' if dark else t['highlight'], t['latinFont'])
            self.content(s['title'], .75, 3.48, 7.1, 1.3, 42, 'FFFFFF' if dark else t['ink'], t['headingFont'])
            if s.get('subtitle'): self.content(s['subtitle'], .79, 5.15, 6.2, .6, 15, 'C6DCDB' if dark else t['muted'])
            if s.get('image'): self.image(s['image'], 8.3, 1.1, 4.38, 5.58)
        elif layout == 'agenda':
            self.chrome(s, page); self.heading(s)
            for i, item in enumerate(s['items']):
                y = 2.65+i*.88
                self.txt(f'{i+1:02}', .7, y, .75, .56, 25, t['accent'], t['latinFont'])
                self.content(item, 1.7, y, 6.8, .56, 22)
                self.line(1.7, y+.7, 10.9)
        elif layout == 'overview':
            self.chrome(s, page); self.heading(s)
            self.image(s['image'], 4.2, 2.42, 8.5, 2.95)
            if s.get('body'): self.content(s['body'], .68, 2.65, 3.22, 2.0, 19, valign='top')
            metrics = s['metrics']
            if len(metrics) > 4: raise ValueError('Overview supports at most four metrics; split content')
            for i, m in enumerate(metrics):
                x = .7+i*(11.96/len(metrics))
                self.content(m['value'], x, 5.71, 2.8, .6, 33, t['accent'], t['latinFont'])
                self.content(m['label'], x, 6.4, 2.8, .35, 12, t['muted'])
        elif layout == 'feature':
            self.chrome(s, page); self.heading(s)
            reverse = s.get('image_side') == 'left'
            ix, tx = (.65, 8.4) if reverse else (5.75, .7)
            self.image(s['image'], ix, 2.52, 7 if reverse else 6.93, 4.12)
            self.items(s.get('items', []), tx, 2.53, 4.27 if reverse else 4.55, 4.1)
        elif layout == 'spread':
            self.chrome(s, page); self.heading(s)
            self.image(s['image'], .65, 2.52, 7.55, 4.12)
            self.image(s['secondary_image'], 8.43, 2.52, 4.25, 2.38)
            self.items(s.get('items', []), 8.43, 5.12, 4.25, 1.5)
        elif layout == 'photo-grid':
            self.chrome(s, page); self.heading(s)
            images = s['images']
            if not 2 <= len(images) <= 3: raise ValueError('Photo grid needs two or three purposeful images')
            self.image(images[0], .65, 2.52, 4.15, 4.1)
            if len(images) == 2:
                self.image(images[1], 5.05, 2.52, 7.63, 3.0)
                self.items(s.get('items', []), 5.05, 5.74, 7.63, .9)
            else:
                self.image(images[1], 5.05, 2.52, 3.7, 2.3)
                self.image(images[2], 8.98, 2.52, 3.7, 2.3)
                self.items(s.get('items', []), 5.05, 5.08, 7.63, 1.54)
        elif layout == 'annotated':
            self.chrome(s, page); self.heading(s)
            self.image(s['image'], .65, 2.52, 7.6, 4.12)
            annotations = s['annotations']
            if not 1 <= len(annotations) <= 3: raise ValueError('Use one to three meaningful callouts')
            for i, a in enumerate(annotations):
                if not 0 <= a['x'] <= 1 or not 0 <= a['y'] <= 1: raise ValueError('Annotation anchors are normalized image coordinates')
                x, y = .65+7.6*a['x'], 2.52+4.12*a['y']
                self.e.append({'type':'shape','shape':'ellipse','options':{'x':x-.16,'y':y-.16,'w':.32,'h':.32,
                    'line':{'color':'FFFFFF','width':1},'fill':{'color':t['accent']}}})
                self.txt(str(i+1), x-.16, y-.16, .32, .32, 10, 'FFFFFF', t['latinFont'], align='center')
                yy = 2.7+i*1.25
                self.txt(f'{i+1:02}', 8.65, yy, .55, .4, 18, t['accent'], t['latinFont'])
                self.content(a['label'], 9.32, yy, 3.22, .75, 19)
        elif layout == 'statement':
            background = t['dark']; self.chrome(s, page, True)
            self.content(s['title'], .75, 1.1, 11.9, .75, 31, 'FFFFFF', t['headingFont'])
            self.content(s['metric'], .7, 2.43, 8, 1.7, 105, 'FFFFFF', t['latinFont'])
            if s.get('unit'): self.content(s['unit'], 8.62, 3.2, 3.9, .65, 25, 'C6DCDB')
            if s.get('body'): self.content(s['body'], .8, 5.2, 10.8, .9, 21, 'C6DCDB')
        elif layout == 'chart':
            self.chrome(s, page); self.heading(s)
            chart = s['chart']; data = []
            for series in chart['series']:
                values = [float(resolve(p['value'], self.plan).replace(',', '')) for p in series['points']]
                data.append({'name': series['name'], 'labels': [p['label'] for p in series['points']], 'values': values})
            opts = {'x': .75, 'y': 2.7, 'w': 7.6, 'h': 3.85, 'catAxisLabelFontSize': 14,
                    'valAxisLabelFontSize': 11, 'valAxisMinVal': 0,
                    'catAxisLineShow': False, 'valAxisLineShow': False,
                    'showValue': True, 'dataLabelPosition': 'outEnd', 'dataLabelFormatCode': '0',
                    'dataLabelColor': t['ink'], 'dataLabelBkgrdColor': t['background'],
                    'dataLabelFormatCodeSourceLinked': False, 'dataLabelFontSize': 16,
                    'showLegend': False, 'showCatName': False,
                    'chartColors': [t['accent']], 'showTitle': False,
                    'showMarker': False, 'showBorder': False,
                    'showSerName': False, 'gapSize': 120,
                    'catAxisLabelColor': t['muted'], 'valAxisLabelColor': t['muted'],
                    'valGridLine': {'color': t['rule'], 'width': .5},
                    'catGridLine': {'style': 'none'}}
            if chart.get('max') is not None: opts['valAxisMaxVal'] = chart['max']
            self.e.append({'type': 'chart', 'chartType': chart.get('type', 'bar'), 'data': data,
                           'options': {**opts, 'barDir': 'col', 'showLegend': len(data)>1}})
            self.items(s.get('items', []), 9, 2.76, 3.55, 3.7)
        elif layout == 'comparison':
            self.chrome(s, page); self.heading(s)
            rows = [[resolve(cell, self.plan) for cell in row] for row in s['rows']]
            if not rows or len({len(r) for r in rows}) != 1: raise ValueError('Rectangular table required')
            styled = []
            for i, row in enumerate(rows):
                styled.append([{'text': cell, 'options': {
                    'fill': t['accent'] if i == 0 else (t['wash'] if i%2 else t['paper']),
                    'color': 'FFFFFF' if i == 0 else t['ink'], 'bold': i == 0,
                    'fontFace': t['bodyFont']}} for cell in row])
            self.e.append({'type': 'table', 'rows': styled, 'options': {
                'x': .7, 'y': 2.65, 'w': 11.94, 'h': min(3.9, .61*len(rows)),
                'fontFace': t['bodyFont'], 'fontSize': 16, 'color': t['ink'],
                'rowH': .61, 'margin': .12, 'border': {'type': 'solid', 'color': t['background'], 'pt': 2},
                'colW': [11.94/len(rows[0])]*len(rows[0]), 'valign': 'mid'}})
        elif layout == 'timeline':
            self.chrome(s, page); self.heading(s)
            events = s['events']; n = len(events)
            if not n: raise ValueError('Timeline needs events')
            self.line(.82, 3.43, 11.6)
            for i, event in enumerate(events):
                x = .82+i*11.8/n; width = 11.8/n-.42
                self.rect(x, 3.35, .16, .16, t.get('highlight', t['accent']))
                if event.get('date'):
                    self.content(event['date'], x, 2.68, width, .55, 24, t['accent'], t['latinFont'])
                else:
                    self.txt(f'{i+1:02}', x, 2.68, width, .55, 24, t['accent'], t['latinFont'])
                self.content(event['title'], x, 3.84, width, .6, 21, bold=True)
                if event.get('body'): self.content(event['body'], x, 4.65, width, 1.35, 16, t['muted'], valign='top')
        elif layout == 'close':
            background = t['dark']; self.chrome(s, page, True)
            self.content(s['title'], .75, 1.45, 11.6, 1.0, 42, 'FFFFFF', t['headingFont'])
            if s.get('metric'): self.content(s['metric'], .75, 3.02, 8, 1.0, 62, 'FFFFFF', t['latinFont'])
            if s.get('body'): self.content(s['body'], .8, 4.55, 10.8, 1.25, 21, 'C6DCDB')
        elif layout == 'text':
            self.chrome(s, page); self.heading(s)
            self.items(s.get('items', []), .75, 2.6, 11.8, 3.95)
        else: raise ValueError(f'Unsupported layout {layout}')
        required = [resolve('$'+ref, self.plan) for ref in set(references(s))]
        # Charts have values in embedded chart/workbook, not text extraction.
        chart_refs = set(references(s.get('chart', {})))
        required = [resolve('$'+ref, self.plan) for ref in set(references(s))-chart_refs]
        self.contract[str(page)] = required
        self.slides.append({'background': background, 'elements': self.e, 'notes': s.get('notes', '')})
        self.manifest.append({'slide': page, 'layout': layout, 'claims': sorted(set(references(s))),
                              'images': [s[k] for k in ('image', 'secondary_image') if s.get(k)]+s.get('images', [])})


def compose(workspace):
    workspace = Path(workspace).resolve()
    plan = json.loads((workspace/'plan.json').read_text())
    source = json.loads((workspace/'source.json').read_text())
    report = validate(plan, source, workspace)
    slides = paginate(plan['slides'], plan)
    composer = Composer(plan, workspace)
    for i, slide in enumerate(slides, 1): composer.render(slide, i)
    spec = {'title': plan.get('title', ''), 'language': plan.get('language', 'zh-CN'),
            'canvas': {'width': W, 'height': H}, 'theme': {
                'background': composer.t['background'], 'text': composer.t['ink'],
                'accent': composer.t['accent'], 'headingFont': composer.t['headingFont'],
                'bodyFont': composer.t['bodyFont'], 'bodySize': 18}, 'slides': composer.slides}
    write(workspace/'deck.json', spec)
    write(workspace/'contract.json', {'required_text': composer.contract, 'min_objects': {
        str(i): {'native_charts': 1} if s['layout'] == 'chart' else {'native_tables': 1}
        for i, s in enumerate(slides, 1) if s['layout'] in ('chart', 'comparison')}})
    write(workspace/'composition.json', {'style': composer.style_name, 'slides': composer.manifest,
          'source_sha256': source['sha256'], **report,
          'limits': 'Exact quotes, paragraph accounting, and lexical number checks. Host agent must review semantic fidelity and final-export visuals.'})
    return {'slides': len(slides), 'style': composer.style_name, 'deck': str(workspace/'deck.json')}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('prepare'); p.add_argument('--input', type=Path, required=True); p.add_argument('--workspace', type=Path, required=True)
    p = sub.add_parser('compose'); p.add_argument('--workspace', type=Path, required=True)
    args = parser.parse_args()
    try:
        result = prepare(args.input, args.workspace) if args.command == 'prepare' else compose(args.workspace)
        print(json.dumps(result, ensure_ascii=False, indent=2))
    except (ValueError, OSError, KeyError) as error:
        parser.exit(1, f'Composition stopped: {error}\n')


if __name__ == '__main__': main()
