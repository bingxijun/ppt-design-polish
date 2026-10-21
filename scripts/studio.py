#!/usr/bin/env python3
"""Bind design proofs, selections and revision observations to real exported files.

No aesthetic judge or model API is hidden here. This records and validates evidence;
the host must actually inspect the pixels and make the editorial decisions.
"""
import argparse
import hashlib
import json
import re
import shutil
from pathlib import Path
from deck import read, write, digest, task, state, render_current, verify_contract, chart_cache

STORE = '.ppt-beautify/studio'


def token(value):
    if not isinstance(value,str) or not re.fullmatch(r'[a-z0-9][a-z0-9-]{0,47}',value):
        raise ValueError('Use a short lowercase letter/digit/hyphen id')
    return value


def nonempty(value,label):
    if not isinstance(value,str) or not value.strip():raise ValueError(label+' needs meaningful text')
    return value


def local(w,name):
    p=Path(name)
    if p.is_absolute() or '..' in p.parts or not (w/p).resolve().is_relative_to(w.resolve()):
        raise ValueError('Evidence paths must stay inside the workspace')
    return w/p


def fingerprint(w):
    paths=[w/'design-study.json'] if (w/'design-study.json').is_file() else []
    if (w/'source.json').is_file():paths.append(w/'source.json')
    paths += [p for p in (w/'inputs').rglob('*') if p.is_file()]
    return {str(p.relative_to(w)):digest(p) for p in sorted(paths)}


def input_fingerprint(w):
    return {k:v for k,v in fingerprint(w).items() if k!='design-study.json'}


def config(w):
    c=read(w/'design-study.json')
    if not isinstance(c,dict):raise ValueError('Study brief must be an object')
    for key in ('audience','viewing','visual_goal'):nonempty(c.get(key),key)
    groups=c.get('proofs',[])
    if not isinstance(groups,list) or not groups:raise ValueError('Choose meaningful proof pages for this brief')
    ids=[]
    for g in groups:
        if not isinstance(g,dict):raise ValueError('Each proof needs an id and page job')
        ids.append(token(g.get('id')));nonempty(g.get('job'),'Proof page job')
        if g.get('mode','compare') not in ('compare','reference'):raise ValueError('Proof mode is compare or reference')
        if g.get('mode')=='reference':nonempty(g.get('reason'),'Adopted-reference reason')
    if len(set(ids))!=len(ids):raise ValueError('Proof ids must be unique')
    limit=c.get('max_revision_rounds',3)
    if type(limit) is not int or not 1<=limit<=10:raise ValueError('Revision budget must be 1–10 rounds')
    return c


def begin(w,brief):
    if (w/'design-study.json').exists():raise ValueError('Study already exists; preserve it or use a new workspace')
    payload=task(w)
    write(w/'design-study.json',brief)
    try:config(w)
    except Exception:
        (w/'design-study.json').unlink();raise
    payload['design_review']=True;write(w/'task.json',payload)
    return {'ok':True,'next':'Build/render proofs; register candidates; inspect and select before expanding the deck'}


def current(w):
    s=state(w)
    if not render_current(w,s):raise ValueError('Current final-PPTX renders are required')
    result=verify_contract(w,w/s['build']['artifact'])
    if not result['ok']:raise ValueError('Content/object contract failed: '+str(result['errors']))
    return s


def freeze(source,destination):
    if destination.exists():raise ValueError('Evidence id already exists; use a new id')
    s=current(source)
    destination.mkdir(parents=True)
    files={}
    def copy(origin,name):
        target=destination/name;target.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(origin,target);files[name]=digest(target)
    copy(source/s['build']['artifact'],'export.pptx')
    pages=sorted(s['render']['pages'],key=lambda p:int(Path(p).stem.split('-')[-1]))
    for i,p in enumerate(pages,1):copy(source/p,f'page-{i:02}.png')
    for name in ['deck.json','plan.json','contract.json','composition.json','design-audit.json','design-plan.json']:
        if (source/name).is_file():copy(source/name,'sources/'+name)
    return {'artifact_sha256':s['build']['sha256'],'files':files,'pages':len(pages)}


def evidence_ok(w,entry):
    try:return all(local(w,entry['directory']+'/'+p).is_file() and digest(local(w,entry['directory']+'/'+p))==sha
                   for p,sha in entry['files'].items())
    except (ValueError,KeyError,OSError):return False


def database(w):
    path=w/STORE/'index.json'
    return read(path) if path.exists() else {'candidates':{},'selections':{},'rounds':[]}


def save(w,data):write(w/STORE/'index.json',data)


def register(w,group,identifier,candidate,page):
    c=config(w);token(group);token(identifier)
    if group not in [g['id'] for g in c['proofs']]:raise ValueError('Unknown proof group')
    # Every variant shares the exact frozen raw material, not a more convenient summary.
    if input_fingerprint(w)!=input_fingerprint(candidate):raise ValueError('Candidate raw inputs/source index differ from the study')
    s=current(candidate)
    if type(page) is not int or not 1<=page<=task(candidate)['slides']:raise ValueError('Invalid candidate page')
    contract=read(candidate/'contract.json')
    required=contract.get('required_text',{}).get(str(page),[])
    if not required:raise ValueError('Proof pages need a nonempty content contract')
    cache=chart_cache(candidate/s['build']['artifact'])[page-1]
    content={'text':sorted(''.join(t.split()) for t in required),'chart':sorted(cache.items())}
    signature=hashlib.sha256(json.dumps(content,sort_keys=True).encode()).hexdigest()
    d=database(w);others=d['candidates'].get(group,{})
    if others and any(e['content_signature']!=signature for e in others.values()):
        raise ValueError('Variants need the same page content contract and chart values; compare composition on equal content')
    path=f'{STORE}/candidates/{group}/{identifier}'
    e=freeze(candidate,w/path);e.update(directory=path,page=page,brief=fingerprint(w),content_signature=signature)
    d['candidates'].setdefault(group,{})[identifier]=e;d['selections'].pop(group,None);save(w,d)
    return {'ok':True,'image':str(w/path/f'page-{page:02}.png'),'next':'Inspect this exported page; no design score has been assigned'}


def select(w,choice):
    if not isinstance(choice,dict):raise ValueError('Selection must be an object')
    c=config(w);group=choice.get('group');g=next((g for g in c['proofs'] if g['id']==group),None)
    if not g:raise ValueError('Unknown proof group')
    d=database(w);variants=d['candidates'].get(group,{})
    if len(variants)<(1 if g.get('mode')=='reference' else 2):raise ValueError('Comparison needs at least two actual candidates')
    if choice.get('selected') not in variants:raise ValueError('Select a registered candidate')
    if any(e['brief']!=fingerprint(w) or not evidence_ok(w,e) for e in variants.values()):
        raise ValueError('Candidate evidence or source brief is stale')
    observations=choice.get('observations',[])
    if not isinstance(observations,list) or any(not isinstance(o,dict) for o in observations):
        raise ValueError('Candidate observations must be objects in a list')
    if len(observations)!=len(variants) or {o.get('candidate') for o in observations}!=set(variants):
        raise ValueError('Inspect and record every candidate, including the rejected alternatives')
    for o in observations:
        nonempty(o.get('strength'),'Observed strength');nonempty(o.get('weakness'),'Observed limitation/tradeoff')
    nonempty(choice.get('reason'),'Selection reason')
    d['selections'][group]={**choice,'brief':fingerprint(w),'candidate_evidence':variants}
    save(w,d);return {'ok':True,'group':group,'selected':choice['selected']}


def critique(w,payload):
    if not isinstance(payload,dict):raise ValueError('Critique must be an object')
    c=config(w);s=current(w);d=database(w)
    if len(d['rounds'])>=c.get('max_revision_rounds',3):raise ValueError('Revision budget reached; report the remaining limitation instead of looping')
    nonempty(payload.get('summary'),'Visual inspection summary')
    issues=payload.get('issues')
    if not isinstance(issues,list):raise ValueError('Issues must be a list; empty is valid after an actual clean inspection')
    ids={i['id'] for r in d['rounds'] for i in r['issues']}
    for i in issues:
        if not isinstance(i,dict):raise ValueError('Each issue must be an object')
        token(i.get('id'))
        if i['id'] in ids:raise ValueError('Issue ids must be unique across the study')
        ids.add(i['id'])
        if type(i.get('slide')) is not int or not 1<=i['slide']<=task(w)['slides']:raise ValueError('Invalid issue slide')
        if i.get('severity') not in ('blocker','major','minor'):raise ValueError('Issue severity is blocker, major or minor')
        nonempty(i.get('observation'),'Visible observation');nonempty(i.get('action'),'Concrete source edit')
        box=i.get('bbox')
        if not isinstance(box,list) or len(box)!=4 or any(type(v) not in (int,float) or not 0<=v<=1 for v in box) or box[2]<=0 or box[3]<=0 or box[0]+box[2]>1.001 or box[1]+box[3]>1.001:
            raise ValueError('Issue bbox is normalized [x,y,width,height] inside the rendered page')
    directory=f'{STORE}/rounds/{len(d["rounds"])+1:02}'
    frozen=freeze(w,w/directory)
    r={**payload,**frozen,'directory':directory,'brief':fingerprint(w),'resolutions':{},'render':s['render']}
    d['rounds'].append(r);save(w,d)
    return {'ok':True,'round':len(d['rounds']),'issues':[i['id'] for i in issues]}


def resolve(w,fixes):
    s=current(w);d=database(w)
    if not isinstance(fixes,list) or not fixes:raise ValueError('Supply actual issue resolutions')
    if any(not isinstance(f,dict) for f in fixes):raise ValueError('Each resolution must be an object')
    ids=[f.get('id') for f in fixes]
    if len(set(ids))!=len(ids):raise ValueError('Duplicate resolution id')
    for f in fixes:
        pair=next(((r,i) for r in d['rounds'] for i in r['issues'] if i['id']==f.get('id')),None)
        if not pair:raise ValueError('Unknown issue id')
        r,i=pair;outcome=f.get('outcome','fixed')
        if outcome not in ('fixed','accepted'):raise ValueError('Resolution outcome is fixed or accepted')
        nonempty(f.get('change'),'Source change or accepted-minor rationale');nonempty(f.get('verification'),'Observation of the current export')
        if outcome=='accepted' and i['severity']!='minor':raise ValueError('Major/blocker issues must be fixed')
        page=f.get('current_slide',i['slide'])
        if type(page) is not int or not 1<=page<=task(w)['slides']:raise ValueError('Invalid resolution page')
        if outcome=='fixed':
            old=r['files'][f'page-{i["slide"]:02}.png']
            images=sorted(s['render']['pages'],key=lambda p:int(Path(p).stem.split('-')[-1]))
            if r['artifact_sha256']==s['build']['sha256'] or old==digest(w/images[page-1]):
                raise ValueError('A claimed visual fix needs a changed export and changed affected page pixels')
        r['resolutions'][i['id']]={**f,'render':s['render'],'brief':fingerprint(w)}
    save(w,d);return {'ok':True,'resolved':ids}


def status(w):
    try:
        c=config(w);d=database(w);s=state(w);problems=[];fp=fingerprint(w)
        for g in c['proofs']:
            choice=d['selections'].get(g['id']);variants=d['candidates'].get(g['id'],{})
            if not choice or choice.get('brief')!=fp or choice.get('candidate_evidence')!=variants:
                problems.append('Missing/stale selection: '+g['id']);continue
            if any(e['brief']!=fp or not evidence_ok(w,e) for e in variants.values()):problems.append('Changed proof evidence: '+g['id'])
        if not d['rounds']:problems.append('Inspect the final export and register a critique, even if no issues remain')
        current_inspection=False
        for r in d['rounds']:
            if r['brief']!=fp or not evidence_ok(w,r):problems.append('Changed critique evidence')
            if not r['issues'] and r['render']==s.get('render'):current_inspection=True
            for i in r['issues']:
                f=r['resolutions'].get(i['id'])
                if not f or f.get('render')!=s.get('render') or f.get('brief')!=fp:problems.append('Unresolved/stale issue: '+i['id'])
                else:current_inspection=True
        if not current_inspection:problems.append('Current export needs a clean inspection or current issue resolutions')
        if not render_current(w,s):problems.append('Final export/render is stale')
        return {'ready':not problems,'problems':problems,'proof_groups':len(c['proofs']),'revision_rounds':len(d['rounds']),
                'limits':'Host-recorded design decisions bound to real exports. Not independent human review or aesthetic certification.'}
    except (OSError,ValueError,KeyError,TypeError) as e:return {'ready':False,'problems':[str(e)]}


def export_evidence(w,output):
    """Make a portable review packet; no mutable workspace state is overwritten."""
    result=status(w)
    if not result['ready']:raise ValueError('Complete the current study before exporting evidence: '+str(result['problems']))
    output=Path(output).resolve()
    if output.exists():raise ValueError('Use a fresh evidence output directory')
    d=database(w)
    shutil.copytree(w/STORE,output)
    entries=[e for group in d['candidates'].values() for e in group.values()]+d['rounds']
    entries += [e for choice in d['selections'].values() for e in choice['candidate_evidence'].values()]
    for entry in entries:
        entry['directory']=entry['directory'].removeprefix(STORE+'/')
    final=freeze(w,output/'final');final['directory']='final'
    write(output/'index.json',d);write(output/'report.json',{'study':read(w/'design-study.json'),'status':result,'final':final,
          'human_blind_review':'pending; host observations are not independent reader judgments'})
    return {'ok':True,'output':str(output),'limits':result['limits']}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--workspace',type=Path,required=True)
    sub=p.add_subparsers(dest='command',required=True)
    b=sub.add_parser('begin');b.add_argument('--brief',type=Path,required=True)
    r=sub.add_parser('register');r.add_argument('--group',required=True);r.add_argument('--id',required=True);r.add_argument('--candidate',type=Path,required=True);r.add_argument('--page',type=int,required=True)
    for name in ('select','critique','resolve'):
        a=sub.add_parser(name);a.add_argument('--file',type=Path,required=True)
    sub.add_parser('status');e=sub.add_parser('export');e.add_argument('--output',type=Path,required=True)
    a=p.parse_args();w=a.workspace.resolve()
    try:
        if a.command=='begin':result=begin(w,read(a.brief))
        elif a.command=='register':result=register(w,a.group,a.id,a.candidate.resolve(),a.page)
        elif a.command=='select':result=select(w,read(a.file))
        elif a.command=='critique':result=critique(w,read(a.file))
        elif a.command=='resolve':result=resolve(w,read(a.file))
        elif a.command=='export':result=export_evidence(w,a.output)
        else:result=status(w)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 2 if result.get('ready') is False else 0
    except (OSError,ValueError,KeyError,TypeError) as e:
        print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));return 2

if __name__=='__main__':raise SystemExit(main())
