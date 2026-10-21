#!/usr/bin/env python3
"""Build the public sample in isolation and verify its useful native objects."""
from pathlib import Path
import shutil
import tempfile
from deck import init, build, verify_contract
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
    for name in ('launch', 'yellow'):
        source = root/'examples'/name
        with tempfile.TemporaryDirectory(prefix='ppt-design-polish-composition-') as tmp:
            workspace = Path(tmp)
            for file in ('plan.json', 'source.json'):
                shutil.copyfile(source/file, workspace/file)
            for directory in ('assets', 'inputs'):
                shutil.copytree(source/directory, workspace/directory)
            result = compose(workspace)
            init(workspace, result['slides'], 'hybrid')
            artifact = workspace/build(workspace)['artifact']
            verification = verify_contract(workspace, artifact)
            if not verification['ok']:
                raise SystemExit(str(verification))
            print(f"{name}: {result['slides']} slides; source coverage, native objects and contracts checked.")


if __name__ == '__main__':
    main()
