"""Page-level art direction shared by semantic plans and the native compositor.

These are starting compositions, not quality scores or a substitute for rendering.
The brief is also usable by host authoring tools that do not use our builder.
"""
import copy


def profile_for(plan, config):
    explicit=config.get('profile')
    if explicit:
        if explicit not in ('classic','product-launch','editorial','analytical'):
            raise ValueError('Unknown visual profile: '+str(explicit))
        return explicit
    if plan.get('design') or plan.get('style','auto')!='auto':return 'classic'
    if any(s.get('illustration',{}).get('product') for s in plan['slides']):return 'product-launch'
    if config.get('tone')=='editorial':return 'editorial'
    return 'analytical'


def recipe_for(slide, profile):
    if profile=='classic' or not slide.get('layout','').startswith('visual-'):return None
    if slide['layout']=='visual-cover':return 'image-led-opening'
    if slide['layout']=='visual-feature':return 'material-and-functions'
    if slide['layout']=='visual-diagram':
        return 'numbered-sequence' if slide['diagram']['form']=='process' else 'structured-relations'
    chart=slide['chart']
    return {'share':'share-spotlight','ranking':'rank-and-readout','trend':'trend-and-endpoint',
            'paired':'paired-evidence','contribution':'reconciled-bridge','distribution':'distribution-field'}[chart['intent']]


def surface_for(slide, profile, palette):
    # Content-led contrasts, never arbitrary alternation by page number.
    dark_ink=sum(int(palette['ink'][i:i+2],16) for i in (0,2,4))<384
    if dark_ink and profile=='product-launch' and slide.get('layout')=='visual-feature':return 'dark'
    return 'paper'


DESCRIPTIONS={
    'image-led-opening':'Full-bleed subject photograph with an unobstructed text area; large regular-weight display title, smaller sans subtitle, restrained rule and native disclosure.',
    'material-and-functions':'A tall material photograph occupies the left side. The right side holds a compact display headline and measured feature rows with matched line icons, readable descriptions and subtle separators.',
    'rank-and-readout':'A large sourced readout and its explanation anchor the left column; a native sorted bar chart occupies the right. One category may carry semantic emphasis. Keep zero baseline and direct values.',
    'share-spotlight':'A narrow headline column names the finding and the whole; a native pie/ring occupies the middle; direct category/value labels form a right-hand ledger. Tonal colors separate parts, not unrelated decoration.',
    'trend-and-endpoint':'A native time-series plot spans the lower field. A compact upper readout repeats the final observed value and its period; retain time order, units, axis and source qualifier.',
    'paired-evidence':'Two matched conditions share a scale. Task labels sit left, endpoint values sit next to their marks, and a restrained legend identifies the conditions. Preserve the qualification near the title.',
    'reconciled-bridge':'A proportional editable waterfall links baseline, signed contributions and ending total. Native numeric labels and unit sit near the evidence; connectors explain continuity.',
    'numbered-sequence':'A continuous numbered rail establishes sequence. Each step has a quiet large ordinal, a small semantic icon, a concise label and its complete explanation; arrows communicate direction.',
    'structured-relations':'Measured native parent-child or cycle connections preserve the actual relation. Distinguish root and leaves through type and position; use symbols only where they identify meaning.',
    'distribution-field':'An ordered native frequency chart uses adjoining bins, a zero baseline and explicit labels. Keep source conditions adjacent; do not sort bins as a ranking.'}


def visual_brief(plan, profile):
    from visuals import text
    design=plan['design'];pages=[]
    for i,s in enumerate(plan['slides'],1):
        recipe=s.get('_recipe')
        if not recipe:continue
        pages.append({'slide':i,'title':text(s['title'],plan),'recipe':recipe,
                      'surface':s['_surface'],'appearance':DESCRIPTIONS[recipe],
                      'communication_reason':s.get('design_reason'),
                      'typography':design['typography'],
                      'image':s.get('image'),'chart_form':s.get('chart',{}).get('type'),
                      'decoration':'Functional rules, ordinal steps and material imagery; no unrelated badges or colored keyword spans.'})
    return {'profile':profile,'palette':design['palette'],'pages':pages,
            'execution':'Apply this complete treatment in the native builder or host authoring tool. Resolve actual image requests; inspect final exported pages. This file alone is not a generated deck.'}


def header(c,s,width=11.9,x=.72,y=.82):
    from visuals import text
    t=c.t
    size=t.get('titleSize',34)
    m=c.metrics.wrap(text(s['title'],c.plan),t['headingFont'],size,width)
    h=m['height']/72+.04
    if h>1.6:raise ValueError('Recipe headline needs a shorter title or a custom composition')
    c.content(s['title'],x,y,width,h,size,font=t['headingFont'],bold=False)
    bottom=y+h
    if s.get('subtitle'):
        c.content(s['subtitle'],x,bottom+.2,width,.82,17,t['muted'])
        bottom+=1.02
    return bottom


def render(c,s,page):
    from visuals import text
    from visual_layouts import segment, dot, dumbbell, waterfall, diagram
    original=c.t;c.t=copy.deepcopy(c.t);t=c.t
    dark=s.get('_surface')=='dark'
    if dark:
        t.update(background=original['dark'],ink=original['onDark'],muted=original['onDarkMuted'],rule='515854')
    try:
        recipe=s['_recipe']
        if recipe=='image-led-opening':
            c.image(s['image'],0,0,13.333333,7.5)
            c.line(.78,1.3,.65,t['accent'])
            c.content(s['title'],.72,1.77,6.0,1.65,78,font=t['headingFont'])
            if s.get('subtitle'):c.content(s['subtitle'],.8,3.55,5.6,.8,27)
            if s.get('body'):c.content(s['body'],.8,5.67,5.7,.7,17,t['muted'])
        elif recipe=='material-and-functions':
            c.image(s['image'],0,0,5.5,7.5)
            header(c,s,6.2,6.22,.85)
            items=s['items']
            if not 1<=len(items)<=3:raise ValueError('Feature recipe needs one to three complete groups')
            y=2.4
            for item in items:
                if not item.get('title') or not item.get('body'):raise ValueError('Feature group needs title and body')
                if item.get('_icon'):c.image(item['_icon'],6.23,y+.06,.32,.32)
                c.content(item['title'],6.9,y,5.53,.52,22)
                h=c.metrics.wrap(text(item['body'],c.plan),t['bodyFont'],18,5.53)['height']/72+.04
                c.content(item['body'],6.9,y+.53,5.53,h,18,t['muted'])
                y+=.53+h+.32
                if item is not items[-1]:c.line(6.9,y-.13,5.53)
            if y>6.72:raise ValueError('Feature text exceeds recipe; split or use a custom composition')
        elif recipe=='rank-and-readout' and s.get('insight'):
            header(c,s)
            entry=s['insight'];c.content(entry['value'],.72,2.62,3.45,1.35,78,font=t['latinFont'])
            if entry.get('label'):c.content(entry['label'],.8,4.08,3.65,.75,22)
            c.line(.8,5.07,3.4)
            if entry.get('body'):c.content(entry['body'],.8,5.35,3.65,1.0,17,t['muted'])
            segment(c,4.97,2.6,4.97,6.2)
            c.chart(s,5.32,2.6,7.34,3.73)
        elif recipe=='share-spotlight' and s['chart']['type'] in ('pie','doughnut'):
            chart=s['chart'];header(c,s,3.72,.72,1.13)
            c.line(.76,3.74,.68,t['accent'])
            c.txt(text(chart['whole'],c.plan),.76,4.03,3.48,.7,20)
            if s.get('body'):c.content(s['body'],.76,5.0,3.5,1.05,17,t['muted'])
            c.chart(s,4.4,1.45,4.55,4.87)
            if chart['type']=='doughnut' and chart.get('center'):
                c.content(chart['center'],5.12,3.17,3.1,.85,40,font=t['latinFont'],align='center')
            points=chart['series'][0]['points'];compact=len(points)>3
            for i,p in enumerate(points):
                y=(1.65+i*.94) if compact else (2.15+i*1.23)
                c.rect(9.36,y+.09,.09,.29,chart['_category_colors'][i])
                c.txt(text(p['label'],c.plan),9.65,y,2.95,.45,16 if compact else 18)
                c.txt(text(p['value'],c.plan)+chart.get('unit',''),9.65,y+.45,2.95,.58,26 if compact else 30,font=t['latinFont'])
                c.line(9.65,y+(.88 if compact else 1.08),2.95)
        elif recipe=='trend-and-endpoint':
            if s.get('insight'):
                from visual_layouts import key_readout
                header(c,s,8.8)
                c.chart(s,.66,2.6,8.5,3.6)
                key_readout(c,s['insight'],9.62,2.65,2.83)
                if s.get('body'):c.content(s['body'],.76,6.42,11.7,.4,15,t['muted'])
                c.line(.72,6.83,11.9);c.chrome(s,page)
                return t['background']
            end=header(c,s,8.9)
            series=s['chart']['series'][0];last=series['points'][-1]
            c.txt(text(last['value'],c.plan),10.25,.78,2.35,.9,49,font=t['latinFont'],align='right')
            c.txt(text(last['label'],c.plan)+' / '+text(series['name'],c.plan),9.35,1.78,3.25,.42,15,t['muted'],align='right')
            c.chart(s,.66,max(2.45,end+.25),11.98,3.72)
            if s.get('body'):c.content(s['body'],.76,6.42,11.7,.4,15,t['muted'])
        elif recipe=='numbered-sequence':
            header(c,s)
            nodes=s['diagram']['nodes']
            from visual_layouts import validate_diagram
            validate_diagram(s['diagram'])
            stride=11.85/len(nodes)
            for i,node in enumerate(nodes):
                x=.76+i*stride;w=stride-.44
                c.txt(f'{i+1:02}',x,2.65,w,1.25,70,t['rule'],font=t['latinFont'])
                if node.get('_icon'):c.image(node['_icon'],x,4.2,.35,.35)
                c.content(node['title'],x,4.91,w,.65,24)
                if node.get('body'):c.content(node['body'],x,5.66,w,.68,17,t['muted'])
                segment(c,x,3.99,x+stride-.14,3.99,t['rule'],i<len(nodes)-1,1)
            if s.get('body'):c.content(s['body'],.76,6.53,11.6,.36,14,t['muted'])
        elif recipe in ('paired-evidence','reconciled-bridge','structured-relations'):
            header(c,s)
            if recipe=='paired-evidence':
                dumbbell(c,s)
                if s.get('body'):c.content(s['body'],.76,6.43,11.6,.4,15,t['muted'])
            elif recipe=='reconciled-bridge':
                if s.get('body'):raise ValueError('Bridge qualifier needs subtitle or a custom composition')
                waterfall(c,s)
            else:diagram(c,s,with_title=False)
        else:
            header(c,s)
            c.chart(s,.66,2.65,11.97,3.6)
            if s.get('body'):c.content(s['body'],.76,6.42,11.6,.43,16,t['muted'])
        # Functional page furniture: a consistent baseline, no fake brand badge.
        if dark:c.rect(0,6.8,13.333333,.7,t['background'])
        c.line(.72,6.83,11.9)
        c.chrome(s,page)
        return t['background']
    finally:c.t=original
