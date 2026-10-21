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
from editorial import design_tokens, semantic_layout, flow_items, table_geometry, audit
from typography import TextMetrics

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
    return semantic_layout(slide)


def resolve(ref, plan):
    if not isinstance(ref, str) or not ref.startswith('$') or ref[1:] not in plan['claims']:
        raise ValueError(f'Visible content must reference a grounded claim, got {ref!r}')
    return plan['claims'][ref[1:]]['text']


def paginate(slides, plan, metrics=None):
    if metrics is None:
        with TextMetrics() as worker:
            return paginate(slides,plan,worker)
    _,tokens=design_tokens(plan,PRESETS)
    font=tokens['bodyFont']
    result = []
    for original in slides:
        slide = copy.deepcopy(original)
        layout = choose_layout(slide)
        slide['layout'] = layout
        if layout=='freeform':
            result.append(slide);continue
        key='rows' if layout=='comparison' else ('events' if layout=='timeline' else 'items')
        items = slide.get(key, [])
        if layout == 'comparison':
            header, items = items[:1], items[1:]
        else: header = []
        def fits(chunk):
            if layout=='comparison':
                rows=[[resolve(cell,plan) for cell in row] for row in header+chunk]
                table_geometry(rows,slide.get('table',{}),metrics,font,tokens['tableSize'],11.94,3.9)
            elif layout=='timeline':
                if len(chunk)>4:raise ValueError('Timeline needs another page')
            elif layout=='agenda':
                if len(chunk)>4:raise ValueError('Agenda needs another page')
            else:
                width,height={'feature':(4.27 if slide.get('image_side')=='left' else 4.55,4.1),
                              'spread':(4.25,1.5),'photo-grid':(7.63,1.54),
                              'chart':(3.55,3.7)}.get(layout,(11.8,3.95))
                flow_items(chunk,lambda ref:resolve(ref,plan),metrics,font,width,height,tokens['bodySize'])
        groups, group = [], []
        for item in items:
            try: fits(group+[item])
            except ValueError:
                if not group:raise
                groups.append(group);group=[]
                fits([item])
            group.append(item)
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
    def __init__(self, plan, workspace, metrics):
        self.plan, self.workspace = plan, workspace
        self.metrics = metrics
        self.style_name, self.t = design_tokens(plan, PRESETS)
        for role in ('headingFont','bodyFont','latinFont'):
            result = metrics.query({'op':'width','text':'Hg','font':self.t[role],'size':18})
            self.t[role] = result['font']
        self.assets = plan.get('assets', {})
        self.slides, self.contract, self.manifest = [], {}, []
        self.e = []

    def txt(self, text, x, y, w, h, size=18, color=None, font=None, **options):
        font = font or self.t['bodyFont']
        measured = self.metrics.wrap(text, font, size, w, bold=options.get('bold',False),
                                     leading=1.06 if size>=30 else 1.28)
        if measured['overlong'] or measured['height'] > h*72 + 5:
            raise ValueError(f'Text does not fit {size}pt box: {text[:70]!r}; shorten or repaginate')
        self.e.append({'type': 'text', 'text': '\n'.join(measured['lines']), 'options': {
            'x': x, 'y': y, 'w': w, 'h': h, 'fontSize': size,
            'fontFace': measured['font'], 'color': color or self.t['ink'],
            'margin': 0, 'breakLine': False, 'valign': 'top', 'paraSpaceAfterPt': 0,
            'lineSpacing': measured['lineHeight'], 'lang': self.plan.get('language','en-US'), **options}})

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
        color = self.t['onDarkMuted'] if dark else self.t['muted']
        furniture = self.t['furniture']
        if furniture.get('brand'):
            self.txt(self.plan.get('brand', ''), .65, .28, 5, .25, 10, color,
                     self.t['latinFont'], bold=True)
        if furniture.get('section'):
            self.txt(slide.get('section', ''), 8.5, .28, 4.16, .25, 9, color, align='right')
        if furniture.get('page'):
            self.txt(f'{page:02}', 12.2, 6.97, .47, .22, 9, color, self.t['latinFont'], align='right')
        if slide.get('footnote'):
            self.content(slide['footnote'], .65, 6.93, 11.1, .31, 9, color)

    def heading(self, s):
        if s.get('kicker'):
            self.txt(s['kicker'], .65, .83, 11.8, .23, 10, self.t['muted'], self.t['latinFont'])
        self.content(s['title'], .65, 1.15, 11.9, .65, 32, font=self.t['headingFont'])
        if s.get('subtitle'):
            self.content(s['subtitle'], .68, 1.91, 11.8, .38, 13, self.t['muted'])

    def items(self, items, x, y, w, height, dark=False):
        blocks = flow_items(items, lambda ref:resolve(ref,self.plan), self.metrics,
                            self.t['bodyFont'], w, height, self.t['bodySize'])
        for block in blocks:
            if block['separator']: self.line(x, y+block['y'], w)
            color = self.t['onDark'] if dark else self.t['ink']
            if block['priority']=='supporting': color=self.t['onDarkMuted'] if dark else self.t['muted']
            for part in block['parts']:
                self.txt(part['text'],x,y+part['y'],w,part['h'],part['size'],color,
                         bold=part['bold'])

    def table(self, s, x=.7, y=2.65, w=11.94, h=3.9):
        t=self.t; config=s.get('table',{})
        rows=[[resolve(cell,self.plan) for cell in row] for row in s['rows']]
        if not rows: raise ValueError('Table needs rows')
        size=config.get('font_size',t['tableSize'])
        widths,heights,aligns=table_geometry(rows,config,self.metrics,t['bodyFont'],size,w,h)
        emphasis={tuple(cell) for cell in config.get('emphasis_cells',[])}
        if emphasis and not config.get('emphasis_reason'): raise ValueError('Table emphasis needs an information-specific reason')
        if any(len(cell)!=2 or any(type(v) is not int for v in cell) or
               not 0<=cell[0]<len(rows) or not 0<=cell[1]<len(rows[0]) for cell in emphasis):
            raise ValueError('Table emphasis cell outside the data')
        styled=[]
        for i,row in enumerate(rows):
            cells=[]
            for j,cell in enumerate(row):
                border=[{'color':t['rule'],'pt':.7 if i==0 else .3},
                        {'color':t['paper'],'pt':0},
                        {'color':t['rule'],'pt':.7 if i==0 or i==len(rows)-1 else .3},
                        {'color':t['paper'],'pt':0}]
                options={'fill':config.get('header_fill',t['paper']) if i==0 else t['paper'],
                    'color':config.get('header_color',t['ink']) if i==0 else t['ink'],
                    'bold':i==0 or (i,j) in emphasis,'align':aligns[j], 'border':border,
                    'fontFace':t['bodyFont']}
                cells.append({'text':cell,'options':options})
            styled.append(cells)
        self.e.append({'type':'table','rows':styled,'options':{'x':x,'y':y,'w':w,'h':sum(heights),
            'fontFace':t['bodyFont'],'fontSize':size,'color':t['ink'], 'rowH':heights,
            'margin':[.1,.14,.1,.14],'colW':widths,'valign':'mid'}})
        if s.get('body'):
            self.content(s['body'],x,y+sum(heights)+.28,w,.8,self.t['bodySize'])

    def chart(self,s,x=.75,y=2.7,w=7.6,h=3.85):
        t=self.t; chart=s['chart']; data=[]
        for series in chart['series']:
            values=[float(resolve(p['value'],self.plan).replace(',','')) for p in series['points']]
            data.append({'name':series['name'],'labels':[p['label'] for p in series['points']],'values':values})
        focus=chart.get('focus_points',[])
        if len(data)>1 and (len(chart.get('series_colors',[]))!=len(data) or not chart.get('series_color_reason')):
            raise ValueError('Multiple series need distinct series_colors and a semantic series_color_reason')
        if focus and chart.get('series_colors'):
            raise ValueError('Choose point focus or series colors, not both')
        if focus and (len(data)!=1 or not chart.get('focus_reason')):
            raise ValueError('Point emphasis needs one series and a substantive focus_reason')
        if any(type(i) is not int or i<0 or i>=len(data[0]['values']) for i in focus):
            raise ValueError('Chart focus point outside the data')
        colors=chart.get('series_colors') or ([t['accent'] if i in focus else t['ink']
                                             for i in range(len(data[0]['values']))] if focus else [t['ink']])
        opts={'x':x,'y':y,'w':w,'h':h,'catAxisLabelFontSize':14,'valAxisLabelFontSize':11,
              'valAxisMinVal':chart.get('min',0),'catAxisLineShow':False,'valAxisLineShow':False,
              'showValue':True,'dataLabelPosition':'outEnd','dataLabelFormatCode':chart.get('number_format','0'),
              'dataLabelColor':t['ink'],'dataLabelFontSize':15,'showLegend':len(data)>1,
              'chartColors':colors,'showTitle':False,'showMarker':chart.get('type')=='line',
              'showBorder':False,'showSerName':False,'gapSize':100,
              'catAxisLabelColor':t['ink'],'valAxisLabelColor':t['muted'],
              'valGridLine':{'style':'none'},'catGridLine':{'style':'none'},
              'barDir':chart.get('orientation','col')}
        if chart.get('max') is not None:opts['valAxisMaxVal']=chart['max']
        if chart.get('major_unit') is not None:opts['valAxisMajorUnit']=chart['major_unit']
        if chart.get('category_order') is not None:
            if chart['category_order']!='first-at-top' or chart.get('orientation')!='bar':
                raise ValueError('category_order:first-at-top applies to horizontal bars')
            opts['catAxisOrientation']='maxMin'
            opts['catAxisLabelPos']='low'
            opts['valAxisLabelPos']='low'
        if chart.get('type')=='line': opts['dataLabelPosition']='t'
        self.e.append({'type':'chart','chartType':chart.get('type','bar'),'data':data,'options':opts})

    def freeform(self,s,page):
        if not s.get('design_reason','').strip() or not s.get('frames'):
            raise ValueError('Custom composition needs frames and a design_reason')
        for frame in s.get('frames',[]):
            kind=frame['kind']; x,y,w,h=[frame[k] for k in ('x','y','w','h')]
            if min(x,y)<0 or w<=0 or (h<=0 and kind!='rule') or x+w>W+.01 or y+h>H+.01:
                raise ValueError('Custom composition frame is outside the slide')
            if kind=='text':
                role=frame.get('color_role','ink')
                if role=='accent' and not frame.get('reason'):
                    raise ValueError('Accent text needs a meaning-specific reason')
                self.content(frame['claim'],x,y,w,h,frame.get('size',self.t['bodySize']),
                    self.t[role],self.t[frame.get('font_role','bodyFont')],
                    bold=frame.get('bold',False),align=frame.get('align','left'))
            elif kind=='image':self.image(frame['asset'],x,y,w,h)
            elif kind=='table':self.table(s,x,y,w,h)
            elif kind=='chart':self.chart(s,x,y,w,h)
            elif kind=='rule':self.line(x,y,w)
            elif kind=='connector':
                direction=frame.get('direction','down')
                if direction not in ('down','up'):raise ValueError('Connector direction is down or up')
                self.e.append({'type':'shape','shape':'line','options':{'x':x,'y':y,'w':w,'h':h,
                    'flipV':direction=='up','line':{'color':self.t['rule'],'width':1,'endArrowType':'triangle'}}})
            else:raise ValueError(f'Unsupported custom frame {kind}')
        # Full-bleed imagery must not cover disclosure/footer/native furniture.
        self.chrome(s,page,s.get('dark',False))

    def render(self, s, page):
        self.e = []
        layout, t = s['layout'], self.t
        background = t['background']
        if layout == 'cover':
            if t['cover'] == 'cinematic':
                self.image(s['image'], 0, 0, W, H)
                self.chrome(s, page, True)
                self.content(s['title'], .7, 1.42, 6.8, 1.7, 42, t['onDark'], t['headingFont'])
                if s.get('subtitle'): self.content(s['subtitle'], .74, 3.35, 5.3, .55, 16, t['onDarkMuted'])
                if s.get('body'): self.content(s['body'], .74, 5.92, 4.8, .7, 12, t['onDarkMuted'])
            elif t['cover']=='editorial':
                self.image(s['image'], 6.75, 0, 6.59, H)
                self.rect(0, 0, 6.75, H, t['paper'])
                self.rect(.65, 1.17, .65, .11, t['highlight'])
                self.chrome(s, page)
                self.content(s['title'], .65, 1.75, 5.9, 2.1, 40, font=t['headingFont'], bold=True)
                if s.get('subtitle'): self.content(s['subtitle'], .68, 4.18, 5.3, .7, 18)
                if s.get('body'): self.content(s['body'], .68, 5.9, 5.5, .65, 12, t['muted'])
            else:
                self.chrome(s,page)
                self.content(s['title'],.75,1.65,11.8,2.0,44,font=t['headingFont'],bold=True)
                if s.get('subtitle'):self.content(s['subtitle'],.78,4.0,10,.8,23)
                if s.get('body'):self.content(s['body'],.78,5.65,10,.7,17,t['muted'])
        elif layout == 'chapter':
            dark = t['chapter'] == 'dark'
            background = t['dark'] if dark else t['paper']
            self.chrome(s, page, dark)
            self.txt(s.get('chapter', '01'), .65, 1.08, 5, 2.1, 130,
                     t['chapterNumber'], t['latinFont'])
            self.content(s['title'], .75, 3.48, 7.1, 1.3, 42, t['onDark'] if dark else t['ink'], t['headingFont'])
            if s.get('subtitle'): self.content(s['subtitle'], .79, 5.15, 6.2, .6, 15, t['onDarkMuted'] if dark else t['muted'])
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
                if m.get('emphasis') and not m.get('reason'):raise ValueError('Metric emphasis needs a reason')
                self.content(m['value'], x, 5.71, 2.8, .6, 33, t['accent'] if m.get('emphasis') else t['ink'], t['latinFont'])
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
            self.content(s['title'], .75, 1.1, 11.9, .75, 31, t['onDark'], t['headingFont'])
            self.content(s['metric'], .7, 2.43, 8, 1.7, 105, t['onDark'], t['latinFont'])
            if s.get('unit'): self.content(s['unit'], 8.62, 3.2, 3.9, .65, 25, t['onDarkMuted'])
            if s.get('body'): self.content(s['body'], .8, 5.2, 10.8, .9, 21, t['onDarkMuted'])
        elif layout == 'chart':
            self.chrome(s, page); self.heading(s)
            self.chart(s)
            self.items(s.get('items', []), 9, 2.76, 3.55, 3.7)
        elif layout == 'comparison':
            self.chrome(s, page); self.heading(s)
            self.table(s)
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
            self.content(s['title'], .75, 1.45, 11.6, 1.0, 42, t['onDark'], t['headingFont'])
            if s.get('metric'): self.content(s['metric'], .75, 3.02, 8, 1.0, 62, t['onDark'], t['latinFont'])
            if s.get('body'): self.content(s['body'], .8, 4.55, 10.8, 1.25, 21, t['onDarkMuted'])
        elif layout == 'text':
            self.chrome(s, page); self.heading(s)
            self.items(s.get('items', []), .75, 2.6, 11.8, 3.95)
        elif layout == 'freeform':
            background=s.get('background',t['background'])
            self.freeform(s,page)
        else: raise ValueError(f'Unsupported layout {layout}')
        required = [resolve('$'+ref, self.plan) for ref in set(references(s))]
        # Charts have values in embedded chart/workbook, not text extraction.
        chart_refs = set(references(s.get('chart', {})))
        required = [resolve('$'+ref, self.plan) for ref in set(references(s))-chart_refs]
        self.contract[str(page)] = required
        self.slides.append({'background': background, 'elements': self.e, 'notes': s.get('notes', '')})
        self.manifest.append({'slide': page, 'layout': layout, 'claims': sorted(set(references(s))),
                              'images': [s[k] for k in ('image', 'secondary_image') if s.get(k)]+s.get('images', [])+
                              [f['asset'] for f in s.get('frames',[]) if f['kind']=='image']})


def compose(workspace):
    workspace = Path(workspace).resolve()
    plan = json.loads((workspace/'plan.json').read_text())
    source = json.loads((workspace/'source.json').read_text())
    report = validate(plan, source, workspace)
    with TextMetrics() as metrics:
        slides = paginate(plan['slides'], plan,metrics)
        composer = Composer(plan, workspace, metrics)
        for i, slide in enumerate(slides, 1): composer.render(slide, i)
        substitutions=dict(metrics.substitutions)
    spec = {'title': plan.get('title', ''), 'language': plan.get('language', 'zh-CN'),
            'canvas': {'width': W, 'height': H}, 'theme': {
                'background': composer.t['background'], 'text': composer.t['ink'],
                'accent': composer.t['accent'], 'headingFont': composer.t['headingFont'],
                'bodyFont': composer.t['bodyFont'], 'bodySize': 18}, 'slides': composer.slides}
    write(workspace/'deck.json', spec)
    minimums={}
    for i,s in enumerate(slides,1):
        kinds={f['kind'] for f in s.get('frames',[])}|{s['layout']}
        expected={}
        if 'chart' in kinds:expected['native_charts']=1
        if 'comparison' in kinds or 'table' in kinds:expected['native_tables']=1
        if expected:minimums[str(i)]=expected
    write(workspace/'contract.json', {'required_text': composer.contract, 'min_objects':minimums})
    write(workspace/'design-audit.json', audit({**plan,'slides':slides},spec,composer.manifest))
    write(workspace/'composition.json', {'style': composer.style_name, 'slides': composer.manifest,
          'font_substitutions':substitutions,'text_measurement':'Skia font metrics; final Office rendering needs review',
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
