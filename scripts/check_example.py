#!/usr/bin/env python3
"""Build the public sample in isolation and verify its useful native objects."""
from pathlib import Path
import shutil
import tempfile
from deck import init, build, verify_contract, read, digest
from compose import compose


def main():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='ppt-design-polish-example-') as tmp:
        workspace = Path(tmp)
        init(workspace, 3, 'native')
        for name in ('deck.json', 'contract.json'):
            shutil.copyfile(root/'examples/editorial'/name, workspace/name)
        result = build(workspace)
        artifact = workspace/result['artifact']
        verification = verify_contract(workspace, artifact)
        if not verification['ok']:
            raise SystemExit(str(verification))
        print('Sample built: 3 slides; required text, native chart/table, and relationships checked.')
        print('Visual quality still requires rendering and inspection.')
    for name in ('launch', 'yellow', 'operations', 'studio', 'visual-defaults','launch-studio'):
        source = root/'examples'/name
        with tempfile.TemporaryDirectory(prefix='ppt-design-polish-composition-') as tmp:
            workspace = Path(tmp)
            for file in ('plan.json', 'source.json'):
                shutil.copyfile(source/file, workspace/file)
            for directory in ('assets', 'inputs'):
                shutil.copytree(source/directory, workspace/directory) if (source/directory).exists() else (workspace/directory).mkdir()
            if name in ('visual-defaults','launch-studio'):
                from visuals import prepare as prepare_visuals
                prepare_visuals(workspace)
            result = compose(workspace)
            init(workspace, result['slides'], 'hybrid')
            artifact = workspace/build(workspace)['artifact']
            verification = verify_contract(workspace, artifact)
            if not verification['ok']:
                raise SystemExit(str(verification))
            print(f"{name}: {result['slides']} slides; source coverage, native objects and contracts checked.")
    # Frozen evidence is verified independently of mutable local render state.
    from studio import evidence_ok
    evidence=root/'examples/studio/evidence'
    index=read(evidence/'index.json');report=read(evidence/'report.json')
    records=[e for group in index['candidates'].values() for e in group.values()]+index['rounds']+[report['final']]
    if not all(evidence_ok(evidence,e) for e in records):raise SystemExit('Changed studio evidence files')
    validation=read(root/'examples/studio/validation.json')
    if digest(root/'examples/studio/exhibition.pptx')!=validation['artifact_sha256']:
        raise SystemExit('Public studio export differs from reviewed artifact')
    validation=read(root/'examples/visual-defaults/validation.json')
    if digest(root/'examples/visual-defaults/visual-defaults.pptx')!=validation['artifact_sha256']:
        raise SystemExit('Public visual-defaults export differs from reviewed artifact')
    validation=read(root/'examples/launch-studio/validation.json')
    if digest(root/'examples/launch-studio/launch-studio.pptx')!=validation['artifact_sha256']:
        raise SystemExit('Public launch-studio export differs from reviewed artifact')
    print('Studio evidence: candidate, critique and final file hashes match. Human preference review remains separate.')


if __name__ == '__main__':
    main()
