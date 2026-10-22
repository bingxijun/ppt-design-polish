#!/usr/bin/env python3
"""Build a reproducible portable skill ZIP with icons, excluding examples and local state."""
import argparse
import hashlib
import json
from pathlib import Path
from zipfile import ZipFile, ZipInfo, ZIP_DEFLATED
from install import COMPONENTS, NAME, ROOT


def package(destination):
    destination = Path(destination).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    output = destination/(NAME+'.zip')
    checksum = output.with_suffix('.zip.sha256')
    if output.exists() or checksum.exists():
        raise ValueError('Release files already exist; choose a fresh output directory')
    files = []
    for name in COMPONENTS:
        source = ROOT/name
        if source.is_file():
            files.append(source)
        elif source.is_dir():
            files += [p for p in source.rglob('*') if p.is_file()
                      and '__pycache__' not in p.parts and p.suffix != '.pyc']
        else:
            raise ValueError(f'Missing release component: {name}')
    with ZipFile(output, 'w', compression=ZIP_DEFLATED, compresslevel=9) as archive:
        for source in sorted(files):
            entry = ZipInfo((Path(NAME)/source.relative_to(ROOT)).as_posix(), (2026, 1, 1, 0, 0, 0))
            entry.compress_type = ZIP_DEFLATED
            entry.create_system = 3
            entry.external_attr = 0o100644 << 16
            archive.writestr(entry, source.read_bytes())
    with ZipFile(output) as archive:
        if archive.testzip() is not None:
            raise ValueError('ZIP integrity check failed')
    sha = hashlib.sha256(output.read_bytes()).hexdigest()
    checksum.write_text(f'{sha}  {output.name}\n', encoding='utf-8')
    return {'zip': str(output), 'checksum': str(checksum), 'sha256': sha, 'files': len(files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, required=True)
    args = parser.parse_args()
    try:
        print(json.dumps(package(args.output_dir), indent=2))
    except (ValueError, OSError) as error:
        parser.exit(1, str(error)+'\n')


if __name__ == '__main__':
    main()
