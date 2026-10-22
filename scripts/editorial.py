"""Content hierarchy and table geometry, independent of any visual theme."""
import re


def design_tokens(plan, presets):
    name = plan.get('style', 'auto')
    design = plan.get('design', {})
    if name == 'auto':
        if not design.get('basis') or not design.get('palette') or not design.get('typography'):
            raise ValueError('Auto design needs design.basis, palette and typography derived from this brief/reference; no industry theme is selected')
        required = {'background', 'paper', 'ink', 'muted', 'rule', 'accent'}
        if not required.issubset(design['palette']):
            raise ValueError('Design palette needs background, paper, ink, muted, rule and accent roles')
        t = dict(design['palette'])
        t.update(design['typography'])
        t.update(design.get('structure', {}))
        if not {'headingFont', 'bodyFont', 'latinFont'}.issubset(t):
            raise ValueError('Design typography needs installed headingFont, bodyFont and latinFont')
        name = 'brief-derived'
    else:
        if name not in presets: raise ValueError(f'Unknown optional preset {name}')
        t = dict(presets[name])
        t.update(design.get('palette', {})); t.update(design.get('typography', {}))
        t.update(design.get('structure', {}))
    t.update(plan.get('fonts', {}))
    for key in ['background','paper','ink','muted','rule','accent','dark','wash','highlight','onDark','onDarkMuted','chapterNumber']:
        if key in t and not re.fullmatch(r'[0-9A-Fa-f]{6}', t[key]):
            raise ValueError(f'Design color role {key} must be six hex digits')
    t.setdefault('dark', t['ink']); t.setdefault('wash', t['paper'])
    t.setdefault('highlight', t['accent']); t.setdefault('onDark', t['paper'])
    t.setdefault('onDarkMuted', t['paper']); t.setdefault('chapterNumber', t['accent'])
    t.setdefault('cover', 'typographic'); t.setdefault('chapter', 'paper')
    t['bodySize'] = design.get('body_size', 18)
    t['tableSize'] = design.get('table_size', 17)
    t['titleSize'] = design.get('title_size', 32)
    t['coverSize'] = design.get('cover_size', 44)
    t['furniture'] = design.get('furniture', {'brand': True, 'page': True})
    return name, t


RELATIONS = {'comparison':'comparison', 'quantitative':'chart', 'trend':'chart',
             'sequence':'timeline', 'detail':'feature', 'overview':'overview',
             'gallery':'spread', 'callouts':'annotated', 'claim':'statement',
             'explanation':'text', 'reading':'text'}


def semantic_layout(slide):
    if slide.get('layout'):
        return slide['layout']
    if slide.get('role') in ('cover','agenda','chapter','close'):
        return slide['role']
    relation = slide.get('relation')
    if relation not in RELATIONS:
        raise ValueError('Each body slide needs an explicit relation or custom layout; fields alone do not decide communication intent')
    if not slide.get('design_reason', '').strip():
        raise ValueError('A semantic layout needs design_reason explaining the reading task')
    layout = RELATIONS[relation]
    if relation == 'gallery' and slide.get('images'): layout = 'photo-grid'
    required = {'comparison':'rows','chart':'chart','timeline':'events','feature':'image',
                'overview':'metrics','spread':'image','photo-grid':'images','annotated':'annotations',
                'statement':'metric','text':'items'}
    if not slide.get(required[layout]):
        raise ValueError(f'{relation} needs {required[layout]}; regroup the content or author a custom layout')
    if relation == 'trend' and slide['chart'].get('type') != 'line':
        raise ValueError('A trend relation needs a line chart or an explicitly chosen specialist layout')
    return layout


def flow_items(items, resolve, metrics, font, width, height, body_size=18):
    """Return measured block positions. Empty space is not distributed equally."""
    blocks, y = [], 0
    for item in items:
        entry = {'body': item} if isinstance(item, str) else item
        priority = entry.get('priority', 'normal')
        if priority not in ('primary','normal','supporting'):
            raise ValueError('Item priority is primary, normal or supporting')
        if priority != 'normal' and not entry.get('reason', '').strip():
            raise ValueError('Unequal emphasis needs a reason tied to the reading task')
        size = body_size+3 if priority == 'primary' else body_size
        block = {'y': y, 'priority': priority, 'parts': [], 'separator': entry.get('separator', False)}
        if block['separator']: y += .14
        for field in ('title','body'):
            if not entry.get(field): continue
            text = resolve(entry[field]); bold = field == 'title'
            pt = size if field == 'body' else size+1
            measured = metrics.wrap(text, font, pt, width, bold=bold)
            if measured['overlong']:
                raise ValueError(f'Unbreakable text exceeds column width: {text[:50]}')
            h = measured['height']/72+.03
            block['parts'].append({'text':'\n'.join(measured['lines']), 'y':y, 'h':h,
                                   'size':pt,'bold':bold, 'field':field})
            y += h + (.12 if field == 'title' and entry.get('body') else 0)
        y += entry.get('gap_after', .3 if priority == 'primary' else .23)
        blocks.append(block)
    if y and y-.2 > height:
        raise ValueError(f'Content needs {y-.2:.2f}in, only {height:.2f}in available; repaginate or change composition')
    return blocks


def numeric_column(values):
    return all(re.fullmatch(r'[\s¥$€£+−\-\d,.%/():]+(?:km|mm|cm|kg|kWh|kW|L|分钟|小时|年)?', v) for v in values)


def table_geometry(rows, config, metrics, font, size, width, max_height):
    if not rows or not rows[0]:raise ValueError('Table needs nonempty rows and columns')
    cols = len(rows[0])
    if not all(len(row) == cols for row in rows): raise ValueError('Rectangular table required')
    weights = config.get('column_widths')
    if weights is None:
        weights = [max(metrics.width(row[j], font, size, bold=i == 0) for i,row in enumerate(rows))+.4 for j in range(cols)]
        # Cap very long cells. They should wrap rather than consume the whole table.
        median = sorted(weights)[len(weights)//2]
        weights = [min(v, max(1.3, median*1.7)) for v in weights]
    if len(weights) != cols or any(not isinstance(v,(float,int)) or v <= 0 for v in weights):
        raise ValueError('Table column_widths must give a positive weight per column')
    widths = [width*v/sum(weights) for v in weights]
    aligns = config.get('alignments') or ['left' if j == 0 or not numeric_column([r[j] for r in rows[1:]]) else 'right' for j in range(cols)]
    if len(aligns) != cols or any(a not in ('left','right','center') for a in aligns):
        raise ValueError('Table alignments must match columns')
    heights = []
    for i,row in enumerate(rows):
        measured=[metrics.wrap(cell,font,size,widths[j]-.28,bold=i == 0) for j,cell in enumerate(row)]
        if any(cell['overlong'] for cell in measured):raise ValueError('Unbreakable table text exceeds its column; widen or edit the cell')
        content_h = max(cell['height']/72 for cell in measured)
        heights.append(max(.45,content_h+.22)+(config.get('group_gap', .08) if i in config.get('group_breaks',[]) else 0))
    if sum(heights) > max_height:
        raise ValueError('Measured table exceeds available height; split rows or use a wider composition')
    return widths, heights, aligns


def audit(plan, deck, manifest):
    """Find reviewable repetition; never claim authorship detection or aesthetic scores."""
    findings = []
    body = [(i+1,s) for i,s in enumerate(plan['slides']) if s.get('role') not in ('cover','chapter','agenda','close')]
    kickers = [i for i,s in body if s.get('kicker')]
    if len(kickers) >= 3 and len(kickers) >= len(body)*.6:
        findings.append({'pattern':'repeated-kickers','slides':kickers,
                         'question':'Do these repeated labels help navigation, or add the same decorative layer to every page?'})
    titles = [plan['claims'][s['title'][1:]]['text'] for _,s in body if s.get('title','').startswith('$')]
    comma_titles = [i for (i,s) in body if s.get('title','').startswith('$') and re.search('[，,]',plan['claims'][s['title'][1:]]['text'])]
    if len(comma_titles) >= 3 and len(comma_titles) >= len(titles)*.5:
        findings.append({'pattern':'repeated-headline-cadence','slides':comma_titles,
                         'question':'Are repeated two-part headlines specific to the evidence, or generic copy polishing?'})
    signatures = {}
    for item in manifest:
        signature = item['layout']
        if signature=='freeform':
            elements=deck['slides'][item['slide']-1]['elements']
            signature=tuple((e['type'],*(round(e.get('options',{}).get(k,0),1) for k in ('x','y','w','h'))) for e in elements)
        signatures.setdefault(signature,[]).append(item['slide'])
    for signature,pages in signatures.items():
        if len(pages) >= 4:
            findings.append({'pattern':'repeated-layout','slides':pages,
                             'question':f'Is repeating {signature} useful for comparison, or erasing differences in page purpose?'})
    for i,slide in enumerate(deck['slides'],1):
        for e in slide['elements']:
            if e['type'] != 'table': continue
            widths=e['options'].get('colW',[])
            if len(widths)>1 and max(widths)-min(widths)<.01:
                findings.append({'pattern':'equal-table-columns','slides':[i],
                                 'question':'Are the columns equivalent alternatives? Otherwise allocate width by reading task and actual content.'})
    return {'findings':findings,'review_required':True,
            'limits':'Pattern observations for contextual review. No AI detector, beauty score, or guarantee of human authorship perception.'}
