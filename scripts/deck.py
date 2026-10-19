#!/usr/bin/env python3
"""Unified workspace, native/image build, render and hash-bound delivery checks."""
import argparse
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
from zipfile import ZipFile, BadZipFile
import xml.etree.ElementTree as ET

from inspect_pptx import inspect_pptx, NS, relationships, read_xml
from vendor.pptagent_review import validate_review

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / 'scripts'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(path.suffix + '.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    temp.replace(path)


def snapshot(workspace):
    files = [workspace/name for name in ['task.json', 'deck.json', 'contract.json', 'design-plan.json'] if (workspace/name).is_file()]
    for directory in ['assets', 'slides', 'inputs', 'code']:
        files += [p for p in (workspace/directory).rglob('*') if p.is_file()]
    return {str(p.relative_to(workspace)): digest(p) for p in sorted(set(files))}


def node_binary():
    explicit = os.environ.get('PPT_BEAUTIFY_NODE')
    bundled = Path.home()/'.cache/codex-runtimes/codex-primary-runtime/dependencies/node/bin/node'
    return explicit or shutil.which('node') or (str(bundled) if bundled.is_file() else None)


def node_run(script, *args):
    node = node_binary()
    if not node:
        raise ValueError('Node.js is unavailable; set PPT_BEAUTIFY_NODE')
    proc = subprocess.run([node, str(SCRIPTS/script), *map(str, args)], capture_output=True, text=True)
    if proc.returncode:
        raise ValueError((proc.stderr or proc.stdout)[-5000:])
    # Some importers log informational lines; the last line is our JSON result.
    return json.loads(proc.stdout.strip().splitlines()[-1])


def state_path(w):
    return w/'.ppt-beautify/state.json'


def state(w):
    return read(state_path(w)) if state_path(w).is_file() else {}


def task(w):
    payload = read(w/'task.json')
    if type(payload.get('slides')) is not int or payload['slides'] < 1:
        raise ValueError('task.slides must be a positive integer')
    formats = payload.get('outputs', ['pptx'])
    if not isinstance(formats, list) or not formats or any(f not in ['pptx', 'pdf', 'png'] for f in formats):
        raise ValueError('task.outputs must list pptx, pdf or png')
    return payload


def init(w, slides, mode):
    if slides < 1:
        raise ValueError('slides must be positive')
    if (w/'task.json').exists():
        raise ValueError('Workspace already initialized; reuse existing task.json')
    w.mkdir(parents=True, exist_ok=True)
    for name in ['assets', 'inputs', 'code', 'slides', '.ppt-beautify']:
        (w/name).mkdir(exist_ok=True)
    write(w/'task.json', {'slides': slides, 'mode': mode, 'language': 'zh-CN'})
    write(w/'contract.json', {'required_text': {}, 'min_objects': {}, 'preserve_from': None})
    return {'ok': True, 'workspace': str(w), 'mode': mode, 'next': 'Author deck.json or sources under code/slides; keep assets and inputs local'}


def register_build(w, pptx, backend):
    inventory = inspect_pptx(pptx)
    if inventory['slide_count'] != task(w)['slides']:
        raise ValueError(f"Slide count mismatch: expected {task(w)['slides']}, got {inventory['slide_count']}")
    record = {'artifact': str(Path(pptx).relative_to(w)), 'sha256': digest(pptx),
              'inputs': snapshot(w), 'backend': backend}
    write(state_path(w), {'build': record, 'render': {}, 'reviews': {}})
    write(w/'.ppt-beautify/inventory.json', inventory)
    return {'ok': True, **record}


def build(w):
    task(w)
    output = w/'.ppt-beautify/draft.pptx'
    result = node_run('build_deck.mjs', w/'deck.json', output)
    return register_build(w, output, result['backend'])


def adopt(w, source):
    source = Path(source).resolve()
    dest = w/'.ppt-beautify/draft.pptx'
    task(w)
    inspect_pptx(source)
    dest.parent.mkdir(exist_ok=True)
    if source != dest.resolve():
        shutil.copyfile(source, dest)
    return register_build(w, dest, 'external-export')


def build_current(w, current):
    b = current.get('build', {})
    path = w/b.get('artifact', '.missing')
    return bool(path.is_file() and b.get('sha256') == digest(path) and b.get('inputs') == snapshot(w))


def render(w, renderer):
    current = state(w)
    if not build_current(w, current):
        raise ValueError('Missing or stale build; build/adopt the current sources first')
    artifact = w/current['build']['artifact']
    destination = w/'.ppt-beautify/renders'/current['build']['sha256'][:16]
    destination.mkdir(parents=True, exist_ok=True)
    auxiliary = {}
    if renderer == 'artifact':
        result = node_run('render_deck.mjs', artifact, destination)
        pages, actual_renderer = list(map(Path, result['pages'])), result['renderer']
    else:
        binary = shutil.which('libreoffice') or shutil.which('soffice')
        mac = Path('/Applications/LibreOffice.app/Contents/MacOS/soffice')
        binary = binary or (str(mac) if mac.is_file() else None)
        poppler = shutil.which('pdftoppm')
        if not binary or not poppler:
            raise ValueError('LibreOffice rendering requires soffice/libreoffice and pdftoppm')
        with tempfile.TemporaryDirectory(prefix='ppt-beautify-lo-') as tmp:
            environment = os.environ.copy()
            # macOS headless Fontconfig builds may not discover CoreText fonts.
            # Scope extra font discovery to this process; never alter installed apps.
            extra_dirs = [Path(p) for p in environment.get('PPT_BEAUTIFY_FONT_DIRS', '').split(os.pathsep) if p]
            if sys.platform == 'darwin':
                extra_dirs += [Path('/System/Library/Fonts'), Path('/Library/Fonts'), Path.home()/'Library/Fonts']
            if (w/'assets/fonts').is_dir():
                extra_dirs.append(w/'assets/fonts')
            extra_dirs = [p.resolve() for p in extra_dirs if p.is_dir()]
            if extra_dirs and not environment.get('FONTCONFIG_FILE'):
                config = ET.Element('fontconfig')
                if Path('/etc/fonts/fonts.conf').is_file():
                    ET.SubElement(config, 'include', {'ignore_missing': 'yes'}).text = '/etc/fonts/fonts.conf'
                for directory in extra_dirs:
                    ET.SubElement(config, 'dir').text = str(directory)
                ET.SubElement(config, 'cachedir').text = str(Path(tmp)/'font-cache')
                fontconfig = Path(tmp)/'fonts.conf'
                ET.ElementTree(config).write(fontconfig, encoding='utf-8', xml_declaration=True)
                environment['FONTCONFIG_FILE'] = str(fontconfig)
            subprocess.run([binary, '-env:UserInstallation='+Path(tmp).as_uri(), '--headless', '--convert-to', 'pdf', '--outdir', str(destination), str(artifact)], env=environment, check=True, capture_output=True, timeout=180)
        pdf = destination/(artifact.stem+'.pdf')
        subprocess.run([poppler, '-png', '-scale-to', '1600', str(pdf), str(destination/'page')], check=True, capture_output=True, timeout=180)
        pages = sorted(destination.glob('page-*.png'), key=lambda p: int(p.stem.split('-')[-1]))
        actual_renderer = 'libreoffice-exported-pptx'
        auxiliary[str(pdf.relative_to(w))] = digest(pdf)
    if len(pages) != task(w)['slides']:
        raise ValueError('Rendered page count mismatch')
    rendered = {str(p.relative_to(w)): digest(p) for p in pages}
    current['render'] = {'artifact_sha256': digest(artifact), 'inputs': snapshot(w),
                         'renderer': actual_renderer, 'pages': rendered, 'auxiliary': auxiliary}
    current['reviews'] = {}
    write(state_path(w), current)
    return {'ok': True, 'renderer': actual_renderer, 'pages': [str(p) for p in pages],
            'next': 'Inspect every page and the deck order, then record actual review results'}


def render_current(w, current):
    record = current.get('render', {})
    pages = record.get('pages', {})
    return bool(build_current(w, current) and len(pages) == task(w)['slides']
                and record.get('artifact_sha256') == current['build']['sha256']
                and record.get('inputs') == snapshot(w)
                and all((w/p).is_file() and digest(w/p) == sha for p, sha in {**pages, **record.get('auxiliary', {})}.items()))


def review(w, records):
    if not isinstance(records, list) or not records or not all(isinstance(r, dict) for r in records):
        raise ValueError('Review input must be a nonempty array of review objects')
    current = state(w)
    if not render_current(w, current):
        raise ValueError('Missing/stale final PPTX renders; render and inspect again')
    for entry in records:
        scope = entry.get('slide')
        if scope != 'deck' and (type(scope) is not int or not 1 <= scope <= task(w)['slides']):
            raise ValueError('Review slide must be a valid number or deck')
        validated = validate_review(entry)
        current.setdefault('reviews', {})[str(scope)] = {**validated, 'render': current['render']}
    write(state_path(w), current)
    return {'ok': True, 'recorded': [r['slide'] for r in records]}


def chart_cache(pptx):
    inventory = inspect_pptx(pptx)
    result = []
    with ZipFile(pptx) as z:
        for slide in inventory['slides']:
            values = []
            for rel in slide['related_parts']:
                if rel['type'] == 'chart' and not rel['external']:
                    values += [n.text or '' for n in read_xml(z, rel['target']).findall('.//c:v', NS)]
            result.append(Counter(values))
    return result


def normalized(value):
    return ''.join(value.split())


def verify_contract(w, artifact):
    inventory = inspect_pptx(artifact)
    contract = read(w/'contract.json')
    errors = []
    for page, required in contract.get('required_text', {}).items():
        number = int(page)
        if not 1 <= number <= len(inventory['slides']):
            errors.append(f'Required-text slide {number} is missing')
            continue
        actual = normalized('\n'.join(inventory['slides'][number-1]['paragraphs']))
        for text in required:
            if normalized(text) not in actual:
                errors.append(f'Slide {page}: missing required text {text!r}')
    for page, counts in contract.get('min_objects', {}).items():
        number = int(page)
        if not 1 <= number <= len(inventory['slides']):
            errors.append(f'Object-contract slide {number} is missing')
            continue
        actual = inventory['slides'][number-1]['objects']
        for kind, minimum in counts.items():
            if kind not in actual or actual[kind] < minimum:
                errors.append(f'Slide {page}: requires {minimum} {kind}')
    source = contract.get('preserve_from')
    if source:
        source = (w/source).resolve()
        before = inspect_pptx(source)
        if before['slide_count'] != inventory['slide_count']:
            errors.append('Source-preservation slide count mismatch')
        for original, changed in zip(before['slides'], inventory['slides']):
            actual = normalized('\n'.join(changed['paragraphs']))
            for text in original['paragraphs']:
                if normalized(text) not in actual:
                    errors.append(f"Slide {original['slide']}: source text missing {text!r}")
            notes = normalized('\n'.join(changed['speaker_notes']))
            for text in original['speaker_notes']:
                if normalized(text) not in notes:
                    errors.append(f"Slide {original['slide']}: source note missing")
            for kind in ['native_charts', 'native_tables', 'smartart_links']:
                if changed['objects'][kind] < original['objects'][kind]:
                    errors.append(f"Slide {original['slide']}: lost {kind}; preservation needs a native editing path")
        for number, (old, new) in enumerate(zip(chart_cache(source), chart_cache(artifact)), 1):
            if old-new:
                errors.append(f'Slide {number}: source chart cache values or labels missing')
    # Relationship existence is a structural check, not full XSD or Office validation.
    with ZipFile(artifact) as z:
        names = set(z.namelist())
        for name in names:
            if not name.endswith('.rels'):
                continue
            if name == '_rels/.rels':
                part = ''
            else:
                directory, filename = name.rsplit('/_rels/', 1)
                part = directory+'/'+filename[:-5]
            for rel in relationships(z, part).values():
                if not rel['external'] and rel['target'] not in names:
                    errors.append(f'Missing relationship target {rel["target"]}')
    return {'ok': not errors, 'errors': errors, 'slide_count': inventory['slide_count'],
            'limits': 'Text/cache presence and object counts do not establish semantic equivalence, workbook correctness, animation behavior, or visual quality'}


def finalize(w):
    current = state(w)
    checks = {'build_current': build_current(w, current), 'renders_current': render_current(w, current)}
    expected = [str(n) for n in range(1, task(w)['slides']+1)] + ['deck']
    reviews = current.get('reviews', {})
    checks['reviews_pass'] = all(reviews.get(key, {}).get('ok') is True and reviews[key].get('render') == current.get('render') for key in expected)
    artifact = w/current.get('build', {}).get('artifact', '.missing')
    result = verify_contract(w, artifact) if artifact.is_file() else {'ok': False, 'errors': ['No artifact']}
    checks['content_contract'] = result['ok']
    formats = task(w).get('outputs', ['pptx'])
    pdfs = [w/name for name in current.get('render', {}).get('auxiliary', {}) if name.endswith('.pdf')]
    checks['requested_formats'] = 'pdf' not in formats or len(pdfs) == 1
    complete = all(checks.values())
    delivery = None
    deliveries = []
    if complete:
        output = w/'output';output.mkdir(exist_ok=True)
        for kind in formats:
            if kind == 'png':
                directory = output/('previews-'+digest(artifact)[:12]);directory.mkdir(exist_ok=True)
                for name in current['render']['pages']:
                    dest = directory/Path(name).name
                    shutil.copyfile(w/name, dest)
                    deliveries.append(str(dest))
            else:
                source = artifact if kind == 'pptx' else pdfs[0]
                dest = output/('answer.'+kind)
                if dest.exists() and digest(dest) != digest(source):
                    dest = output/('answer-'+digest(source)[:12]+'.'+kind)
                shutil.copyfile(source, dest)
                deliveries.append(str(dest))
        delivery = deliveries[0]
    report = {'complete': complete, 'checks': checks, 'contract': result,
              'output': str(delivery) if delivery else None, 'outputs': deliveries,
              'artifact_sha256': digest(artifact) if artifact.is_file() else None,
              'renderer': current.get('render', {}).get('renderer'),
              'review_evidence': 'Host-recorded observations bound to current file/images; the CLI cannot prove an image was actually viewed'}
    write(w/'final-report.json', report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--workspace', type=Path)
    sub = p.add_subparsers(dest='command', required=True)
    sub.add_parser('doctor')
    init_p = sub.add_parser('init');init_p.add_argument('--slides', type=int, required=True)
    init_p.add_argument('--mode', choices=['native', 'hybrid', 'image', 'template', 'beautify'], default='hybrid')
    sub.add_parser('build')
    adopt_p = sub.add_parser('adopt');adopt_p.add_argument('--pptx', type=Path, required=True)
    render_p = sub.add_parser('render');render_p.add_argument('--renderer', choices=['artifact', 'libreoffice'], default='artifact')
    review_p = sub.add_parser('review');review_p.add_argument('--file', type=Path, required=True)
    sub.add_parser('verify');sub.add_parser('finalize');sub.add_parser('status')
    a = p.parse_args()
    try:
        if a.command == 'doctor':
            result = {'python': sys.version.split()[0], 'node': node_binary(), 'skill_root': str(ROOT),
                      'native_backend': 'node scripts/build_deck.mjs; requires pptxgenjs 4.0.1',
                      'renderers': {'libreoffice': shutil.which('libreoffice') or shutil.which('soffice'), 'poppler': shutil.which('pdftoppm')},
                      'note': 'Host imagegen/search is discovered by the agent, not inferred from environment keys'}
            if node_binary():
                result['node_runtime'] = node_run('probe_runtime.mjs')
        else:
            if not a.workspace:
                p.error('--workspace is required')
            w = a.workspace.resolve()
            if a.command == 'init': result = init(w, a.slides, a.mode)
            elif a.command == 'build': result = build(w)
            elif a.command == 'adopt': result = adopt(w, a.pptx)
            elif a.command == 'render': result = render(w, a.renderer)
            elif a.command == 'review': result = review(w, read(a.file))
            elif a.command == 'verify': result = verify_contract(w, w/state(w)['build']['artifact'])
            elif a.command == 'finalize': result = finalize(w)
            else: result = {'state': state(w), 'inputs': snapshot(w)}
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if result.get('complete') is False or result.get('ok') is False else 0
    except (OSError, ValueError, KeyError, BadZipFile, ET.ParseError, subprocess.SubprocessError) as exc:
        print(json.dumps({'ok': False, 'error': str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == '__main__':
    sys.exit(main())
