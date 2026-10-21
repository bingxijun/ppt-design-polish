#!/usr/bin/env python3
"""Prepare anonymous slide pairs and summarize supplied reader decisions only."""
import argparse
import csv
import hashlib
import html
import json
from pathlib import Path
import random
import shutil
from studio import token, nonempty
from deck import read,write,digest

FIELDS=['case','reviewer','preference','readability','hierarchy','typography','color','comments']
VOTES={'left','right','tie','unjudgeable'}


def prepare(pairs,output,key,seed=None):
    output,key=Path(output).resolve(),Path(key).resolve()
    if key==output or output in key.parents:raise ValueError('Keep the answer key outside the reader pack')
    if output.exists() or key.exists():raise ValueError('Use fresh output and answer-key paths')
    if not isinstance(pairs,list) or not pairs:raise ValueError('Supply actual exported image pairs')
    cases=[token(p.get('case')) for p in pairs]
    if len(set(cases))!=len(cases):raise ValueError('Case ids must be unique')
    for pair in pairs:
        nonempty(pair.get('task'),'Audience, viewing conditions and page task')
        for side in ('a','b'):
            f=Path(pair[side]);nonempty(pair.get(side+'_label'),'Condition label')
            if not f.is_file() or f.suffix.lower() not in ('.png','.jpg','.jpeg','.webp'):raise ValueError('Pairs must be actual local slide images')
    rng=random.Random(seed) if seed is not None else random.SystemRandom()
    output.mkdir(parents=True);answers={};images={};body=[]
    for pair in pairs:
        case=pair['case'];order=['a','b'];rng.shuffle(order);answers[case]={}
        body.append(f'<section><h2>{html.escape(case)}</h2><p>{html.escape(pair["task"])}</p><div class="pair">')
        for side,original in zip(('left','right'),order):
            source=Path(pair[original]);name=case+'-'+side+source.suffix.lower();shutil.copyfile(source,output/name)
            images[name]=digest(output/name);answers[case][side]=pair[original+'_label']
            body.append(f'<figure><figcaption>{side.upper()}</figcaption><img src="{html.escape(name)}" alt="{case} {side}"></figure>')
        body.append('</div></section>')
    with (output/'ratings.csv').open('w',encoding='utf-8',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=FIELDS);writer.writeheader();writer.writerows({'case':c} for c in cases)
    (output/'index.html').write_text('''<!doctype html><meta charset="utf-8"><title>Slide pair review / 页面比较</title>
<style>body{font:18px Arial,sans-serif;background:#eee;color:#222;margin:32px;max-width:1800px}.pair{display:flex;gap:20px}figure{margin:0;flex:1;min-width:0}img{width:100%;height:auto}figcaption{font-weight:bold;margin:12px 0}section{margin:44px 0}p{max-width:1000px;line-height:1.6}</style>
<h1>Slide pair review / 页面比较</h1><p>Judge the supplied brief and intended viewing conditions. Open images at readable size. In ratings.csv, enter your reviewer code, left/right/tie/unjudgeable for each criterion, and concrete observations. Leave unreviewed rows blank. Do not infer the production method. / 按任务与观看条件比较，放大看清文字。填写匿名评审编号、各项 left/right/tie/unjudgeable 及具体观察，未看过的保持空白。</p>'''+''.join(body),encoding='utf-8')
    pack={'cases':cases,'images':images,'limits':'Anonymous image filenames and randomized sides. Visible content may reveal a style. No human review has occurred merely by creating this pack.'}
    write(output/'manifest.json',pack);write(key,{'answers':answers,'pack_sha256':digest(output/'manifest.json')})
    return {'ok':True,'cases':len(cases),'reader_pack':str(output),'human_review':'pending'}


def summarize(pack,ratings,key):
    pack=Path(pack);m=read(pack/'manifest.json');k=read(key)
    if k['pack_sha256']!=digest(pack/'manifest.json'):raise ValueError('Answer key does not match this reader pack')
    if any(not (pack/p).is_file() or digest(pack/p)!=sha for p,sha in m['images'].items()):raise ValueError('Pair images changed; prepare a new reader pack')
    counts={};seen=set();pending=0;decisions=[]
    with Path(ratings).open(encoding='utf-8',newline='') as f:
        reader=csv.DictReader(f)
        if reader.fieldnames!=FIELDS:raise ValueError('Use the supplied CSV columns')
        for row in reader:
            if row['case'] not in m['cases']:raise ValueError('Unknown review case')
            values=[row[field].strip() for field in FIELDS[2:-1]]
            if not row['reviewer'].strip() and not any(values) and not row['comments'].strip():pending+=1;continue
            nonempty(row['reviewer'],'Reviewer code');nonempty(row['comments'],'Concrete reader observations')
            identifier=(row['case'],row['reviewer'].strip())
            if identifier in seen:raise ValueError('Duplicate case/reviewer decision')
            seen.add(identifier)
            if any(v not in VOTES for v in values):raise ValueError('Use left/right/tie/unjudgeable for every reviewed criterion')
            decoded={}
            for field,value in zip(FIELDS[2:-1],values):
                condition=k['answers'][row['case']].get(value,value);decoded[field]=condition
                count=counts.setdefault(field,{});count[condition]=count.get(condition,0)+1
            decisions.append({'case':row['case'],'reviewer':row['reviewer'].strip(),**decoded,'comments':row['comments']})
    return {'status':'pending' if not decisions else 'reader-decisions-supplied','decisions':len(decisions),
            'reviewers':len({r['reviewer'] for r in decisions}),'pending_rows':pending,'counts':counts,'records':decisions,
            'limits':'Descriptive counts only. Reviewer independence/expertise is not verified. No population-wide quality claim or significance test.'}


def main():
    p=argparse.ArgumentParser(description=__doc__);sub=p.add_subparsers(dest='command',required=True)
    a=sub.add_parser('prepare');a.add_argument('--pairs',type=Path,required=True);a.add_argument('--output',type=Path,required=True);a.add_argument('--key',type=Path,required=True);a.add_argument('--seed',type=int)
    a=sub.add_parser('summarize');a.add_argument('--pack',type=Path,required=True);a.add_argument('--ratings',type=Path,required=True);a.add_argument('--key',type=Path,required=True)
    a=p.parse_args()
    try:
        result=prepare(read(a.pairs),a.output,a.key,a.seed) if a.command=='prepare' else summarize(a.pack,a.ratings,a.key)
        print(json.dumps(result,ensure_ascii=False,indent=2));return 0
    except (ValueError,KeyError,OSError) as e:print(json.dumps({'ok':False,'error':str(e)},ensure_ascii=False));return 2
if __name__=='__main__':raise SystemExit(main())
