#!/usr/bin/env python3
"""Install the portable skill; never silently replace an existing directory."""
import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import shutil
import tempfile

NAME = 'ppt-design-polish'
ROOT = Path(__file__).resolve().parents[1]
COMPONENTS = ('SKILL.md', 'agents', 'references', 'scripts', 'assets', 'licenses',
              'LICENSE', 'THIRD_PARTY_NOTICES.md', 'package.json', 'package-lock.json')


def install(client, skills_dir=None, update=False):
    default = ((Path(os.environ.get('CODEX_HOME', Path.home()/'.codex'))/'skills')
               if client == 'codex' else Path.home()/'.claude/skills')
    directory = Path(skills_dir).expanduser().resolve() if skills_dir else default.resolve()
    target = directory/NAME
    if target.resolve() == ROOT:
        raise ValueError('Source is already the installation directory')
    if ROOT in target.parents or target in ROOT.parents:
        raise ValueError('Source and destination must not contain one another')
    exists = target.exists() or target.is_symlink()
    if exists and not update:
        raise ValueError(f'{target} already exists; use --update to keep a backup and replace it')
    if exists and (target.is_symlink() or not target.is_dir()):
        raise ValueError('Refusing to replace a symlink or non-directory destination')
    if exists:
        entry = target/'SKILL.md'
        parts = entry.read_text(encoding='utf-8').split('---', 2) if entry.is_file() else []
        if len(parts) != 3 or 'name: ppt-design-polish' not in parts[1].splitlines():
            raise ValueError('Existing directory is not this skill; refusing to replace it')
    directory.mkdir(parents=True, exist_ok=True)
    backup = None
    with tempfile.TemporaryDirectory(prefix=f'.{NAME}-', dir=directory) as staging:
        payload = Path(staging)/NAME
        payload.mkdir()
        for name in COMPONENTS:
            source = ROOT/name
            if source.is_dir():
                shutil.copytree(source, payload/name, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            elif source.is_file():
                shutil.copy2(source, payload/name)
        if exists:
            stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
            backup_root = directory.parent/(directory.name+'-backups')
            backup_root.mkdir(exist_ok=True)
            backup = backup_root/f'{NAME}-{stamp}'
            target.rename(backup)
        try:
            payload.rename(target)
        except OSError:
            if backup:
                backup.rename(target)
            raise
    return target, backup


def main():
    parser = argparse.ArgumentParser(description='Install PPT Design & Polish / 安装 skill')
    parser.add_argument('--client', choices=['codex', 'claude'], required=True)
    parser.add_argument('--skills-dir', type=Path, help='Override the client skills directory')
    parser.add_argument('--update', action='store_true', help='Replace this skill, retaining a backup')
    args = parser.parse_args()
    try:
        target, backup = install(args.client, args.skills_dir, args.update)
    except (ValueError, OSError) as error:
        parser.exit(1, f'Install failed / 安装失败: {error}\n')
    print(f'Installed / 已安装: {target}')
    if backup:
        print(f'Backup / 备份: {backup}')
    print('If the builder dependency is missing, run npm install in this directory.')
    print('如缺少制作依赖，请在安装目录运行 npm install。刷新客户端的 skill 发现后使用。')


if __name__ == '__main__':
    main()
