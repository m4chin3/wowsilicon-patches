#!/usr/bin/env python3
"""Verify or restore a deployment backup, including the original app signature.

Read-only by default. Quit WoW and WoWSilicon before using --apply.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--backup', required=True, type=Path)
    parser.add_argument('--apply', action='store_true', help='Actually restore; otherwise verify only')
    parser.add_argument('--runtime-only', action='store_true',
                        help='Restore native app files only from a backup that also contains game files')
    args = parser.parse_args()
    backup = args.backup.expanduser().resolve()
    manifest = json.loads((backup/'manifest.json').read_text())
    app = Path(manifest['app'])
    files = manifest['files']
    if args.runtime_only:
        targets = {
            app/'Contents/Resources/WoWSilicon-swift_WoWSiliconSwift.bundle/Patching/rosettax87/libRuntimeRosettax87',
            app/'Contents/MacOS/WoWSilicon',
        }
        files = [item for item in files if Path(item['target']) in targets]
        if {Path(item['target']) for item in files} != targets or len(files) != len(targets):
            parser.error('Backup must contain exactly one companion and app executable entry')
    for item in files:
        saved = backup/item['backup']
        target = Path(item['target'])
        if not saved.resolve().is_relative_to(backup):
            parser.error('Invalid backup path')
        if sha(saved) != item['original_sha256']:
            parser.error(f'Backup hash differs: {saved}')
        if not target.is_file() or sha(target) != item['installed_sha256']:
            parser.error(f'Installed file changed since deployment: {target}. Review before restoring.')
    signature = backup/manifest['signature_backup']
    if not signature.is_dir() or not signature.resolve().is_relative_to(backup):
        parser.error('Original app signature backup is missing or invalid')
    if not args.apply:
        print(f'Verified {len(files)} original/current file pairs and original signature directory.')
        print('Nothing restored. Quit WoW/WoWSilicon, then add --apply to restore.')
        return
    for item in files:
        shutil.copy2(backup/item['backup'], item['target'])
    live_signature = app/'Contents/_CodeSignature'
    shutil.rmtree(live_signature)
    shutil.copytree(signature, live_signature)
    subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
    for item in files:
        if sha(Path(item['target'])) != item['original_sha256']:
            raise RuntimeError(f'Restore verification failed: {item["target"]}')
    print('Original files and app signature restored and verified.')


if __name__ == '__main__':
    main()
