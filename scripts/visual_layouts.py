"""Measured, editable compositions for resolved semantic visual recipes."""
import math
from visuals import text, number


def segment(c,x1,y1,x2,y2,color=None,arrow=False,width=1):
    c.e.append({'type':'shape','shape':'line','options':{
        'x':min(x1,x2),'y':min(y1,y2),'w':abs(x2-x1),'h':abs(y2-y1),
        'flipH':x2<x1,'flipV':y2<y1,
        'line':{'color':color or c.t['rule'],'width':width,**({'endArrowType':'triangle'} if arrow else {})}}})


def dot(c,x,y,color,r=.075):
    c.e.append({'type':'shape','shape':'ellipse','options':{'x':x-r,'y':y-r,'w':2*r,'h':2*r,
        'line':{'transparency':100},'fill':{'color':color}}})


def route(c,points):
    for i,(a,b) in enumerate(zip(points,points[1:])):
        segment(c,*a,*b,c.t['rule'],i==len(points)-2,1.2)


def title(c,s,width=11.9):
    c.content(s['title'],.72,.83,width,1.12,c.t.get('titleSize',34),font=c.t['headingFont'],bold=True)
    if s.get('subtitle'):c.content(s['subtitle'],.75,1.98,width,.54,18,c.t['muted'])


def key_readout(c,entry,x,y,w):
    c.content(entry['value'],x,y,w,1.15,54,font=c.t['latinFont'])
    if entry.get('label'):c.content(entry['label'],x,y+1.22,w,1.0,21,bold=True)
    if entry.get('body'):c.content(entry['body'],x,y+2.4,w,1.25,18,c.t['muted'])


def analysis(c,s):
    title(c,s); chart=s['chart'];form=chart['type'];t=c.t
    if form=='dumbbell':return dumbbell(c,s)
    if form=='waterfall':return waterfall(c,s)
    if form=='doughnut':
        c.chart(s,.7,2.28,6.25,4.05)
        if chart.get('center'):
            c.content(chart['center'],2.23,3.83,3.1,.9,40,font=t['latinFont'],align='center')
        center_label=chart['series'][0]['points'][chart.get('center_point',0)]['label'] if chart.get('center') else chart['whole']
        c.txt(text(center_label,c.plan),2.25,4.58,3.0,.55,16,t['muted'],align='center')
        points=chart['series'][0]['points']; colors=chart['_category_colors']
        for i,p in enumerate(points):
            y=2.6+i*.85
            c.rect(7.43,y+.12,.12,.38,colors[i])
            c.txt(text(p['label'],c.plan),7.8,y,3.13,.6,21)
            c.txt(text(p['value'],c.plan)+chart.get('unit',''),11.0,y,1.45,.6,25,font=t['latinFont'],align='right')
    else:
        aside=s.get('insight')
        c.chart(s,.62,2.48,8.5 if aside else 12.0,3.85)
        if aside:key_readout(c,aside,9.62,2.65,2.83)
    if s.get('body'):c.content(s['body'],.75,6.35,11.6,.48,16,t['muted'])


def dumbbell(c,s):
    chart=s['chart'];a,b=chart['series'];n=len(a['points']);t=c.t
    values=[number(p['value'],c.plan) for series in (a,b) for p in series['points']]
    low=min(0,min(values)); high=max(values)
    if high==low:high=low+1
    if chart.get('min') is not None:
        if chart['min']>min(values):raise ValueError('Dumbbell scale clips observed data')
        low=chart['min']
    if chart.get('max') is not None:
        if chart['max']<max(values):raise ValueError('Dumbbell scale clips observed data')
        high=chart['max']
    x0,x1=3.1,11.97
    position=lambda v:x0+(v-low)/(high-low)*(x1-x0)
    # Legend identifies periods/conditions; both endpoint labels remain visible.
    for i,series in enumerate((a,b)):
        xx=3.12+i*4.2;dot(c,xx,2.82,t['muted'] if i==0 else t['accent'],.07)
        c.txt(text(series['name'],c.plan),xx+.22,2.61,3.6,.45,17)
    segment(c,x0,3.3,x1,3.3)
    for i in range(5):
        value=low+(high-low)*i/4;xx=position(value)
        c.txt(f'{value:g}',xx-.28,3.05,.65,.24,10,t['muted'],font=t['latinFont'],align='center')
    gap=min(.9,2.46/max(1,n-1))
    for i,(pa,pb) in enumerate(zip(a['points'],b['points'])):
        y=3.75+i*gap;va,vb=number(pa['value'],c.plan),number(pb['value'],c.plan)
        c.txt(text(pa['label'],c.plan),.75,y-.19,2.12,.63,19)
        segment(c,position(va),y,position(vb),y,t['rule'],width=2)
        dot(c,position(va),y,t['muted'],.075);dot(c,position(vb),y,t['accent'],.105)
        c.txt(text(pa['value'],c.plan),position(va)-.44,y-.39,.88,.29,14,t['muted'],align='center')
        c.txt(text(pb['value'],c.plan),position(vb)-.44,y+.15,.88,.32,16,align='center',bold=True)
    if chart.get('unit'):c.txt(chart['unit'],12.51,3.03,.32,.32,12,t['muted'])


def waterfall(c,s):
    chart=s['chart'];points=chart['series'][0]['points'];values=[number(p['value'],c.plan) for p in points]
    spans=[];level=values[0]
    for i,value in enumerate(values):
        if i in (0,len(values)-1):bottom,top=0,value
        else:bottom,top=level,level+value;level=top
        spans.append((bottom,top))
    low=min(0,min(min(v) for v in spans));high=max(0,max(max(v) for v in spans))
    if low==high:high+=1
    pos=lambda v:6.05-(v-low)/(high-low)*3.23
    x0=1.12;stride=11.1/len(points);bw=min(1.05,stride*.64)
    segment(c,.85,pos(0),12.48,pos(0))
    for i,(p,(bottom,top)) in enumerate(zip(points,spans)):
        x=x0+i*stride;color=c.t['ink'] if i in (0,len(points)-1) else c.t['accent']
        c.rect(x,min(pos(top),pos(bottom)),bw,max(.012,abs(pos(top)-pos(bottom))),color)
        label=text(p['value'],c.plan)
        if 0<i<len(points)-1 and values[i]>0:label='+'+label
        c.txt(label,x-.16,min(pos(top),pos(bottom))-.47,bw+.32,.4,22,font=c.t['latinFont'],align='center')
        c.txt(text(p['label'],c.plan),x-.32,6.18,bw+.64,.61,16,align='center')
        if i<len(points)-1:segment(c,x+bw,pos(top),x+stride,pos(top),c.t['rule'])
    if chart.get('unit'):c.txt(chart['unit'],11.93,6.33,.7,.35,13,c.t['muted'],align='right')


def validate_diagram(diagram):
    nodes=diagram.get('nodes',[]);form=diagram.get('form')
    limit={'process':5,'cycle':4,'hierarchy':9}.get(form)
    if limit is None or not 2<=len(nodes)<=limit:raise ValueError('Split this diagram into readable semantic groups')
    ids=[n.get('id') for n in nodes]
    if any(not isinstance(k,str) or not k for k in ids) or len(set(ids))!=len(ids):raise ValueError('Diagram nodes need unique nonempty ids')
    if any(not n.get('title') for n in nodes):raise ValueError('Diagram nodes need grounded titles')
    if form!='hierarchy':return nodes,None
    by_id={n['id']:n for n in nodes};roots=[n for n in nodes if not n.get('parent')]
    if len(roots)!=1:raise ValueError('Hierarchy needs exactly one root')
    levels={}
    for node in nodes:
        cursor=node;seen=set();depth=0
        while cursor.get('parent'):
            if cursor['id'] in seen:raise ValueError('Hierarchy cycle')
            seen.add(cursor['id']);parent=cursor['parent']
            if parent not in by_id:raise ValueError('Hierarchy parent is missing')
            cursor=by_id[parent];depth+=1
        if depth>2:raise ValueError('Split hierarchy deeper than three readable levels')
        levels.setdefault(depth,[]).append(node)
    if any(len(group)>4 for group in levels.values()):raise ValueError('Split hierarchy level with more than four nodes')
    if any(n.get('body') and any(child.get('parent')==n['id'] for child in nodes) for n in nodes):raise ValueError('Hierarchy parent descriptions need a separate explanation or custom composition')
    if len(levels)>2 and any(n.get('body') for n in nodes):raise ValueError('A three-level hierarchy with descriptions needs another page or a custom composition')
    return nodes,levels


def diagram(c,s):
    title(c,s);data=s['diagram'];nodes,levels=validate_diagram(data);form=data['form'];t=c.t
    positions={};compact=form=='hierarchy' and len(levels)>2
    if form=='process':
        stride=11.7/len(nodes)
        for i,n in enumerate(nodes):positions[n['id']]=(.85+i*stride,3.23,stride-.4)
        for a,b in zip(nodes,nodes[1:]):
            xa,ya,wa=positions[a['id']];xb,yb,wb=positions[b['id']]
            segment(c,xa+wa/2+.44,ya,xb+wb/2-.44,yb,t['rule'],True,1.2)
    elif form=='cycle':
        presets={2:[(2.0,3.4,3.0),(8.4,3.4,3.0)],
                 3:[(5.0,2.6,3.0),(8.6,4.55,3.0),(1.4,4.55,3.0)],
                 4:[(2.0,2.6,3.0),(8.4,2.6,3.0),(8.4,4.7,3.0),(2.0,4.7,3.0)]}
        positions={n['id']:p for n,p in zip(nodes,presets[len(nodes)])}
        centers=[(x+w/2,y) for x,y,w in positions.values()]
        if len(nodes)==4:
            (ax,ay),(bx,by),(cx,cy),(dx,dy)=centers
            route(c,[(ax+.4,ay),(bx-.4,by)])
            route(c,[(bx+.4,by),(12.0,by),(12.0,cy),(cx+.4,cy)])
            route(c,[(cx-.4,cy),(dx+.4,dy)])
            route(c,[(dx-.4,dy),(1.4,dy),(1.4,ay),(ax-.4,ay)])
        elif len(nodes)==3:
            (ax,ay),(bx,by),(cx,cy)=centers
            route(c,[(ax+.4,ay),(bx,ay),(bx,by-.4)])
            route(c,[(bx-.4,by),(cx+.4,cy)])
            route(c,[(cx-.4,cy),(1.0,cy),(1.0,ay),(ax-.4,ay)])
        else:
            (ax,ay),(bx,by)=centers
            route(c,[(ax+.4,ay),(bx-.4,by)])
            route(c,[(bx+.4,by),(12.0,by),(12.0,6.1),(1.4,6.1),(1.4,ay),(ax-.4,ay)])
    else:
        children={n['id']:[child for child in nodes if child.get('parent')==n['id']] for n in nodes}
        root=levels[0][0];leaves=[];descendants={}
        def visit(node):
            group=children[node['id']]
            if not group:leaves.append(node['id']);indices=[len(leaves)-1]
            else:indices=[i for child in group for i in visit(child)]
            descendants[node['id']]=indices;return indices
        visit(root)
        if len(leaves)>4:raise ValueError('Split a hierarchy with more than four terminal branches')
        stride=11.7/len(leaves)
        for depth,group in levels.items():
            for node in group:
                indices=descendants[node['id']];cx=.8+(min(indices)+max(indices)+1)*stride/2
                width=min(4.8,(max(indices)-min(indices)+1)*stride-.4)
                positions[node['id']]=(cx-width/2,2.5+depth*(1.4 if compact else 1.95),width)
        for node in nodes:
            if node.get('parent'):
                x,y,w=positions[node['id']];px,py,pw=positions[node['parent']]
                parent=next(n for n in nodes if n['id']==node['parent'])
                label_h=c.metrics.wrap(text(parent['title'],c.plan),t['bodyFont'],20,pw,bold=True)['height']/72
                start=py+.8 if compact else py+.49+label_h+.12
                gutter=y-.25 if compact else y-.5
                stop=y-.08 if compact else y-.34
                segment(c,px+pw/2,start,px+pw/2,gutter)
                segment(c,px+pw/2,gutter,x+w/2,gutter)
                segment(c,x+w/2,gutter,x+w/2,stop,t['rule'],True)
    for i,node in enumerate(nodes):
        x,y,w=positions[node['id']]
        if compact:
            c.content(node['title'],x,y+.03,w,.65,20,align='center',bold=True)
            continue
        if node.get('_icon'):
            c.image(node['_icon'],x+w/2-.23,y-.25,.46,.46)
        elif form=='process':c.txt(f'{i+1:02}',x+w/2-.4,y-.31,.8,.55,26,t['accent'],font=t['latinFont'],align='center')
        else:dot(c,x+w/2,y,t['accent'],.065)
        c.content(node['title'],x,y+.49,w,.7,22 if form!='hierarchy' else 20,align='center',bold=True)
        if node.get('body'):c.content(node['body'],x,y+1.2,w,1.0 if form=='process' else .66,17,t['muted'],align='center')
    if s.get('body'):c.content(s['body'],.75,6.45,11.7,.42,16,t['muted'])


def feature(c,s):
    title(c,s,6.9);c.image(s['image'],8.22,.75,4.42,5.97)
    items=s.get('items',[])
    if not 1<=len(items)<=3:raise ValueError('Visual feature supports one to three complete feature groups')
    y=2.55
    for item in items:
        if not isinstance(item,dict) or not item.get('title') or not item.get('body'):raise ValueError('Visual feature needs title/body items')
        if item.get('_icon'):c.image(item['_icon'],.76,y+.05,.39,.39)
        c.content(item['title'],1.43,y,6.1,.52,23,bold=True)
        measured=c.metrics.wrap(text(item['body'],c.plan),c.t['bodyFont'],19,6.1)
        h=measured['height']/72+.03
        c.content(item['body'],1.43,y+.58,6.1,h,19,c.t['muted'])
        y+=.58+h+.38
    if y-.38>6.7:raise ValueError('Feature groups exceed page; edit or split instead of shrinking')


def render_visual(c,s,page):
    if not s.get('design_reason','').strip():raise ValueError('Visual recipe needs its communication reason')
    layout=s['layout']
    if layout=='visual-cover':
        c.image(s['image'],0,0,13.333333,7.5)
        c.content(s['title'],.76,1.53,6.3,1.7,c.t.get('coverSize',62),font=c.t['headingFont'],bold=True)
        if s.get('subtitle'):c.content(s['subtitle'],.8,3.52,5.63,1.1,30)
        if s.get('body'):c.content(s['body'],.8,5.48,5.35,.9,18,c.t['muted'])
    elif layout=='visual-analysis':analysis(c,s)
    elif layout=='visual-diagram':diagram(c,s)
    elif layout=='visual-feature':feature(c,s)
    else:raise ValueError('Unknown visual recipe '+layout)
    c.chrome(s,page)
    return c.t['background']
