#!/usr/bin/env python3
"""Build the public sample in isolation and verify its useful native objects."""
from pathlib import Path
import shutil
import tempfile
from deck import init, build, verify_contract


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


if __name__ == '__main__':
    main()
