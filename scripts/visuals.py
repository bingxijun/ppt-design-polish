#!/usr/bin/env python3
"""Resolve semantic visual recipes, installed typography and host image requests.

The host interprets the source. These recipes automate the resulting geometry,
chart choice and assets without pretending to infer causation or call an image API.
"""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import tempfile
from typography import TextMetrics
from deck import node_binary

ROOT = Path(__file__).resolve().parents[1]
FORMS = {'ranking':'bar', 'trend':'line', 'share':'doughnut',
         'distribution':'bar', 'paired':'dumbbell', 'contribution':'waterfall'}
ALIASES = {
    'sense':'radio', 'analyse':'chart-no-axes-combined', 'compute':'cpu',
    'adapt':'sun-moon', 'control':'sliders-horizontal', 'protect':'shield-check',
    'sustain':'leaf', 'illuminate':'lightbulb', 'time':'clock-3', 'route':'route',
    'verify':'check-check', 'structure':'layers', 'people':'users', 'power':'bolt',
    'observe':'eye', 'discover':'search', 'touch':'hand', 'deliver':'package',
    'connect':'cloud', 'listen':'headphones', 'workflow':'workflow',
    'share':'chart-pie', 'schedule':'calendar-days', 'scan':'scan-line'}
KEYWORDS = [
    ('sense', r'感知|传感|采集|监测|\b(?:sensor|sensing|detect)'),
    ('analyse', r'分析|评估|研判|\b(?:analys|assess)'),
    ('compute', r'计算|模型|算法|\b(?:comput|algorithm|model)'),
    ('adapt', r'自适应|调光|昼夜|\b(?:adapt|dimm|daylight)'),
    ('control', r'调节|控制|\b(?:control|adjust)'),
    ('protect', r'保护|安全|隐私|\b(?:protect|safety|privacy)'),
    ('sustain', r'节能|能耗|环保|\b(?:energy|sustain)'),
    ('illuminate', r'照明|光源|灯光|\b(?:light|illumin)'),
    ('time', r'时间|延迟|\b(?:timing|latency|duration)'),
    ('verify', r'检查|验证|确认|复核|\b(?:verify|check|confirm|review)'),
    ('people', r'团队|用户|人员|\b(?:team|user|people)'),
    ('deliver', r'交付|配送|\b(?:deliver|shipping)')]


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def text(ref, plan):
    if isinstance(ref,str) and ref.startswith('$'):
        return plan['claims'][ref[1:]]['text']
    return str(ref)


def number(ref, plan):
    value = float(text(ref,plan).replace(',',''))
    if not math.isfinite(value): raise ValueError('Visual data must be finite')
    return value


def icon_name(entry, plan):
    requested = entry.get('icon','auto')
    if requested in (None,False,'none'):return None
    if requested != 'auto':
        if requested not in ALIASES: raise ValueError('Unknown semantic icon: '+str(requested))
        return ALIASES[requested]
    visible = ' '.join(text(entry[k],plan) for k in ('title','body') if entry.get(k))
    return next((ALIASES[key] for key,pattern in KEYWORDS if re.search(pattern,visible,re.I)), None)


def default_design(config, language, families):
    tone = config.get('tone','precise')
    if tone not in ('precise','editorial','expressive'):raise ValueError('Visual tone is precise, editorial or expressive')
    cjk = language.startswith(('zh','ja','ko'))
    sans = (['Hiragino Sans GB','PingFang SC','Microsoft YaHei','Noto Sans CJK SC','Source Han Sans SC','WenQuanYi Zen Hei']
            if cjk else ['Arial','Aptos','Helvetica Neue','Liberation Sans'])
    serif = (['Songti SC','Noto Serif CJK SC','Source Han Serif SC','SimSun']
             if cjk else ['Georgia','Baskerville','Liberation Serif'])
    if language.startswith('ja'):
        sans=['Hiragino Sans','Hiragino Kaku Gothic ProN','Yu Gothic','Noto Sans CJK JP','Noto Sans JP','MS Gothic']
        serif=['Hiragino Mincho ProN','Yu Mincho','Noto Serif CJK JP','Noto Serif JP']
    elif language.startswith('ko'):
        sans=['Apple SD Gothic Neo','Malgun Gothic','Noto Sans CJK KR','Noto Sans KR']
        serif=['AppleMyungjo','Batang','Noto Serif CJK KR','Noto Serif KR']
    elif language.lower().startswith(('zh-tw','zh-hk','zh-hant')):
        sans=['PingFang TC','Microsoft JhengHei','Noto Sans CJK TC','Noto Sans TC','Heiti TC']
        serif=['Songti TC','Noto Serif CJK TC','Source Han Serif TC']
    choose = lambda options: next((f for f in options if f in families), next((f for f in ('Arial','Liberation Sans','DejaVu Sans') if f in families), None))
    body = choose(sans)
    if not body:raise ValueError('No usable font installed')
    heading = choose(serif) if tone=='editorial' else body
    background=config.get('background','F7F7F4')
    def luminance(value):
        rgb=[int(value[i:i+2],16)/255 for i in (0,2,4)]
        return sum(weight*(v/12.92 if v<=.04045 else ((v+.055)/1.055)**2.4) for weight,v in zip((.2126,.7152,.0722),rgb))
    if not re.fullmatch('[0-9a-fA-F]{6}',background):raise ValueError('Visual background needs six hex digits')
    ink=config.get('ink','F4F5F2' if luminance(background)<.2 else '202320')
    if not re.fullmatch('[0-9a-fA-F]{6}',ink):raise ValueError('Visual ink needs six hex digits')
    a,b=sorted((luminance(ink),luminance(background)))
    if (b+.05)/(a+.05)<4.5:raise ValueError('Default ink/background contrast is too low; choose readable text ink')
    mix=lambda fraction:''.join(f'{round(int(ink[i:i+2],16)*fraction+int(background[i:i+2],16)*(1-fraction)):02X}' for i in (0,2,4))
    palette={'background':background,'paper':background,
             'ink':ink,'muted':mix(.72),'rule':mix(.18),
             'accent':config.get('accent','826C3A'),'dark':ink,
             'onDark':'F7F7F4','onDarkMuted':'CFD4CE'}
    for value in palette.values():
        if not re.fullmatch('[0-9a-fA-F]{6}',value):raise ValueError('Visual palette colors need six hex digits')
    # Accent is used in marks and icons, never as the default body-text color.
    return {'basis':config.get('basis','Quiet neutral typography; semantic marks use the brief-selected accent.'),
            'palette':palette,'typography':{'headingFont':heading,'bodyFont':body,'latinFont':choose(['Avenir Next','Arial','Liberation Sans'])},
            'body_size':20,'table_size':18,'title_size':34,'cover_size':62,
            'structure':{'cover':'typographic','chapter':'paper'},
            'furniture':{'brand':False,'page':True},
            'font_warning': 'CJK family unavailable: install a suitable family before visual delivery.' if cjk and body not in sans else None}


def resolve_chart(slide, plan):
    chart = slide['chart']; goal = chart.get('intent')
    if goal not in FORMS:raise ValueError('Auto visual needs an explicit analytical intent: '+', '.join(FORMS))
    series = chart.get('series',[])
    if not series or not all(s.get('points') for s in series):raise ValueError('Visual chart needs data series')
    labels = [[text(p['label'],plan) for p in s['points']] for s in series]
    values = [[number(p['value'],plan) for p in s['points']] for s in series]
    observed=[v for group in values for v in group]
    if chart.get('min') is not None and chart['min']>min(observed):raise ValueError('Chart minimum clips observed data')
    if chart.get('max') is not None and chart['max']<max(observed):raise ValueError('Chart maximum clips observed data')
    if any(group!=labels[0] for group in labels[1:]):raise ValueError('Series categories must match in order')
    if len(set(labels[0])) != len(labels[0]):raise ValueError('Repeated category labels need disambiguation')
    if not 2 <= len(labels[0]) <= (12 if goal=='trend' else 8):raise ValueError('Split visual data into readable pages; expected 2–8 categories (12 for trend)')
    if goal in ('share','contribution','distribution','ranking') and len(series)!=1:raise ValueError(goal+' requires one coherent series')
    if goal=='distribution' and any(v<0 for v in observed):raise ValueError('Distribution bin counts cannot be negative')
    form=FORMS[goal]
    if goal=='share':
        if chart.get('form') not in (None,'pie','doughnut','bar'):raise ValueError('Share form must be pie, doughnut or bar')
        form=chart.get('form') or form
        if any(v<0 for v in values[0]) or sum(values[0])<=0:raise ValueError('Share needs nonnegative parts of a positive whole')
        if not isinstance(chart.get('whole'),str) or not chart['whole'].strip():raise ValueError('Share needs the named whole represented by these parts')
        if chart.get('total') is None or not math.isclose(sum(values[0]),number(chart['total'],plan),rel_tol=1e-7,abs_tol=1e-7):
            raise ValueError('Share parts must sum to the explicitly sourced total')
        if len(labels[0])>5:form='bar'
        chart['_category_colors']=[plan['design']['palette']['accent'],'414B47','7D8982','A6B1A9','CDD3CC'][:len(labels[0])]
    if goal=='paired':
        if len(series)!=2:raise ValueError('Paired comparison needs exactly two matched series')
        if len(labels[0])>4:raise ValueError('Split paired comparisons with more than four tasks to keep endpoint labels readable')
    if chart.get('center'):
        index=chart.get('center_point',values[0].index(max(values[0])))
        if type(index) is not int or not 0<=index<len(values[0]):raise ValueError('Center point outside chart')
        if not math.isclose(float(text(chart['center'],plan).rstrip('%')),values[0][index]):raise ValueError('Center readout must match its explicitly selected data point')
        chart['center_point']=index
    if goal=='contribution':
        if len(values[0])<3 or chart.get('steps') is None or len(chart['steps'])!=len(values[0]):
            raise ValueError('Contribution needs total/delta/total step roles')
        if chart['steps'][0]!='total' or chart['steps'][-1]!='total' or any(k!='delta' for k in chart['steps'][1:-1]):
            raise ValueError('Contribution roles must be total, delta(s), total')
        if not math.isclose(values[0][0]+sum(values[0][1:-1]),values[0][-1],rel_tol=1e-7,abs_tol=1e-7):
            raise ValueError('Waterfall contributions do not reconcile to the sourced ending total')
    if goal=='ranking':
        order=sorted(range(len(labels[0])),key=lambda i:values[0][i],reverse=True)
        series[0]['points']=[series[0]['points'][i] for i in order]
        chart['focus_points']=[order.index(i) for i in chart.get('focus_points',[])]
    chart['type']=form
    if form=='bar':
        chart['orientation']='col' if goal=='distribution' else 'bar'
        if chart['orientation']=='bar':chart['category_order']='first-at-top'
        if chart.get('min',0)>0 or chart.get('max',0)<0:raise ValueError('Default bar scale must include zero')
        if max(observed)<0:chart.setdefault('max',0)
    if len(series)>1 and 'series_colors' not in chart:
        ink=plan['design']['palette']['ink'];accent=plan['design']['palette']['accent']
        chart['series_colors']=[ink,accent][:len(series)]
        if len(series)>2:raise ValueError('More than two series need an explicit stable category palette')
        chart['series_color_reason']='Named comparison series retain their own ink throughout this page.'
    if form in ('bar','line'):
        extent=max(0,max(observed))-min(0,min(observed))
        raw=(extent or 1)/4;scale=10**math.floor(math.log10(raw))
        tick=next(f*scale for f in (1,2,5,10) if f*scale>=raw)
        if all(v.is_integer() for v in observed):tick=max(1,tick)
        if chart.get('min') is None:chart['min']=math.floor(min(0,min(observed))/tick)*tick
        if chart.get('max') is None:chart['max']=max(tick,math.ceil(max(0,max(observed))/tick)*tick)
        chart.setdefault('major_unit',tick)
    return {'intent':goal,'form':form,'categories':len(labels[0]),'editable':'native diagram' if form in ('dumbbell','waterfall') else 'native chart'}


def image_request(slide, plan, config):
    request=slide['illustration']
    if not isinstance(request,dict) or not request.get('asset') or not request.get('subject') or not request.get('purpose'):
        raise ValueError('Illustration needs asset, subject and purpose')
    if not re.fullmatch('[a-z0-9][a-z0-9-]{0,47}',request['asset']):raise ValueError('Use a short safe asset id')
    real=request.get('identity')=='real'
    mode=request.get('mode','source' if real else 'generate')
    if mode not in ('source','generate'):raise ValueError('Image mode is source or generate')
    if real and mode=='generate':raise ValueError('Real product identity requires supplied or authorized source imagery')
    placement=request.get('placement','right')
    if placement not in ('left','right','full','detail'):raise ValueError('Image placement is left, right, full or detail')
    ratio='4:5' if placement=='detail' else '16:9'
    composition={'left':'Subject on the left; clean negative space on the right.',
                 'right':'Subject on the right 45%; quiet negative space across the left 50% for native slide text.',
                 'full':'One coherent full-frame composition, with a clear focal subject.',
                 'detail':'Close-up material or mechanism detail; portrait crop; identify the same fictional product.'}[placement]
    palette=plan['design']['palette']
    prompt='\n'.join([
        'Use case: product-mockup' if request.get('product',False) else 'Use case: productivity-visual',
        'Asset type: presentation photo/illustration layer; '+ratio+' composition.',
        'Primary request: '+request['subject'], 'Purpose: '+request['purpose'],
        'Style/medium: '+request.get('style',config.get('image_style','Professional editorial photography with believable materials and controlled lighting.')),
        'Composition/framing: '+composition,
        'Color palette: background #'+palette['background']+', ink #'+palette['ink']+', restrained accent #'+palette['accent']+'.',
        'Constraints: no text, logos, watermark, chart labels or invented data; leave all slide typography native.',
        'Identity: use supplied real image unchanged where identity matters.' if real else 'Identity: original fictional subject; do not imitate a named real product or venue.'])
    return {**request,'mode':mode,'ratio':ratio,'prompt':prompt,'output':'assets/'+request['asset']+'.png'}


def normalise(plan, workspace, metrics, require_assets=True):
    plan=copy.deepcopy(plan); config=plan.get('visual_defaults')
    if config is None:
        if plan.get('design') or plan.get('style','auto')!='auto':return plan,{'enabled':False,'decisions':[],'image_requests':[],'icons':[]}
        config={};plan['visual_defaults']=config
    if not isinstance(config,dict):raise ValueError('visual_defaults must be an object')
    from presentation_recipes import profile_for, recipe_for, surface_for, visual_brief
    profile=profile_for(plan,config)
    # A supplied design keeps its fonts. Default launch/editorial profiles use a
    # real display/body pairing rather than different sizes of the same face.
    design_config={**config}
    if profile in ('product-launch','editorial'):design_config['tone']='editorial'
    families=metrics.query({'op':'fonts'})['families']
    if not plan.get('design'):
        plan['design']=default_design(design_config,plan.get('language','en-US'),families)
        if plan.get('style','auto')!='auto':
            presets=json.loads((ROOT/'references/launch-presets.json').read_text())
            if plan['style'] not in presets:raise ValueError('Unknown explicit visual preset')
            preset=presets[plan['style']]
            plan['design']['palette'].update({k:v for k,v in preset.items() if re.fullmatch('[0-9a-fA-F]{6}',v)})
            plan['design']['structure'].update({k:preset[k] for k in ('cover','chapter')})
        else:plan['style']='auto'
    plan.setdefault('assets',{})
    report={'enabled':True,'profile':profile,'decisions':[],'image_requests':[],'icons':[],
            'typography':plan['design'].get('typography'),
            'font_warning':plan['design'].get('font_warning'),
            'limits':'Host interprets meaning and supplies truthful data. Fixed recipes automate geometry, not aesthetic judgment.'}
    for i,slide in enumerate(plan['slides'],1):
        if slide.get('chart',{}).get('type')=='auto':
            decision=resolve_chart(slide,plan);slide['layout']='visual-analysis'
            report['decisions'].append({'slide':i,**decision})
        relation=slide.get('relation')
        if relation in ('process','cycle','hierarchy') and not slide.get('layout'):
            slide['layout']='visual-diagram'
            slide.setdefault('diagram',{})['form']=relation
        if relation=='capabilities' and not slide.get('layout'):slide['layout']='visual-feature'
        slide['_surface']=surface_for(slide,profile,plan['design']['palette'])
        for entry in slide.get('diagram',{}).get('nodes',[])+[x for x in slide.get('items',[]) if isinstance(x,dict)]:
            name=icon_name(entry,plan)
            if name:
                color=plan['design']['palette']['onDark' if slide['_surface']=='dark' else 'ink']
                key='icon-'+name+'-'+color.lower(); entry['_icon']=key
                relative='assets/icons/'+name+'-'+color.lower()+'.png'
                plan['assets'][key]={'path':relative,'purpose':'Semantic sign for '+text(entry.get('title',entry.get('body','')),plan),
                                     'provenance':'Pinned Lucide artwork; licenses/Lucide.txt; source hash in assets/icons/manifest.json','fit':'contain'}
                icon={'name':name,'color':color,'source':str(ROOT/'assets/icons'/ (name+'.svg')),
                      'output':str(workspace/relative)}
                if icon not in report['icons']:report['icons'].append(icon)
                if require_assets and not (workspace/relative).is_file():raise ValueError('Run visuals.py prepare to materialize matching icons')
        if slide.get('illustration'):
            req=image_request(slide,plan,config);report['image_requests'].append({'slide':i,**req})
            slide.setdefault('image',req['asset'])
            if slide.get('role')=='cover':
                slide.setdefault('layout','visual-cover')
                if slide['layout']=='visual-cover' and req.get('placement','right')!='right':raise ValueError('Visual cover needs a right-side subject and left text-safe area; use a custom cover for other placement')
            if require_assets and (req['asset'] not in plan['assets'] or not (workspace/plan['assets'][req['asset']]['path']).is_file()):
                raise ValueError('Missing '+req['asset']+': use the host image/source tool with asset-requests.json, then register the real asset in plan.assets')
        recipe=recipe_for(slide,profile)
        if recipe:slide['_recipe']=recipe
    if profile!='classic':report['visual_brief']=visual_brief(plan,profile)
    return plan,report


def prepare(workspace):
    workspace=Path(workspace).resolve();plan=json.loads((workspace/'plan.json').read_text())
    with TextMetrics() as metrics:effective,report=normalise(plan,workspace,metrics,False)
    save(workspace/'visual-plan.json',effective)
    if report.get('visual_brief'):save(workspace/'visual-brief.json',report['visual_brief'])
    elif (workspace/'visual-brief.json').exists():(workspace/'visual-brief.json').unlink()
    save(workspace/'asset-requests.json',{'requests':report['image_requests'],'execution':'Host must execute actual image/source tools and register assets; this CLI does not call a model.'})
    with tempfile.TemporaryDirectory() as tmp:
        file=Path(tmp)/'icons.json';save(file,report['icons'])
        result=subprocess.run([node_binary(),str(ROOT/'scripts/visual_assets.mjs'),str(file)],capture_output=True,text=True)
        if result.returncode:raise ValueError('Icon materialization failed: '+result.stderr[-1200:])
    report['icons']=[{'name':x['name'],'path':str(Path(x['output']).relative_to(workspace))} for x in report['icons']]
    save(workspace/'visual-report.json',report)
    return {'image_requests':len(report['image_requests']),'icons':len(report['icons']),
            'requests':str(workspace/'asset-requests.json'),'next':'Resolve image requests with host tools, register assets, then compose.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('command',choices=['prepare']);parser.add_argument('--workspace',type=Path,required=True)
    args=parser.parse_args()
    try:print(json.dumps(prepare(args.workspace),ensure_ascii=False,indent=2))
    except (ValueError,KeyError,OSError) as error:parser.exit(1,str(error)+'\n')


if __name__=='__main__':main()
