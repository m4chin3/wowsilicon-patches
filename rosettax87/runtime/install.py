#!/usr/bin/env python3
"""Check/apply the vendored companion runtime to the matching stable app.

Read-only unless --apply is supplied. Quit WoW and WoWSilicon before applying.
Install game mods separately; see ../README.md.
"""
import argparse
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--app', type=Path, default=Path('/Applications/WoWSilicon.app'))
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    vendor = Path(__file__).resolve().parent
    manifest = json.loads((vendor/'manifest.json').read_text())
    for name in ['rosettax87', 'libRuntimeRosettax87']:
        if sha(vendor/name) != manifest['files'][name]['sha256']:
            parser.error(f'Vendored hash mismatch: {name}')
    app = args.app.expanduser().resolve()
    runtime = app/'Contents/Resources/WoWSilicon-swift_WoWSiliconSwift.bundle/Patching/rosettax87'
    if sha(runtime/'rosettax87') != manifest['files']['rosettax87']['sha256']:
        parser.error('App loader differs from supported stable build; reevaluate before applying.')
    target = runtime/'libRuntimeRosettax87'
    apple = Path('/Library/Apple/usr/libexec/oah/libRosettaRuntime')
    if sha(apple) != 'a9bf23ac1b8a785060d4bec7337e4403d6bb4ad234e99100a489c5c3de4f292e':
        parser.error('Apple runtime differs from supported macOS build; revalidate first.')
    subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
    if sha(target) == manifest['files']['libRuntimeRosettax87']['sha256']:
        print('Patched runtime already installed; app signature verifies. No files changed.')
        return
    if sha(target) != 'd5f065eb9c25481e060631d5681ed068db39d5365a4ad8fb1f9872839ea98cd2':
        parser.error('Original companion runtime differs from supported baseline.')
    if not args.apply:
        print('Matching app/runtime baseline found. Nothing changed; add --apply to install.')
        return
    backup = Path.home()/'Library/Application Support/WoWSilicon/Backups'/(
        'rosetta-recovery-'+datetime.now().strftime('%Y%m%d-%H%M%S'))
    backup.mkdir(parents=True, exist_ok=False)
    entries = []
    for i, path in enumerate([target, app/'Contents/MacOS/WoWSilicon']):
        name = f'{i}-{path.name}'
        shutil.copy2(path, backup/name)
        entries.append(dict(target=str(path), backup=name, original_sha256=sha(path)))
    signature = app/'Contents/_CodeSignature'
    shutil.copytree(signature, backup/'app-signature')
    try:
        shutil.copy2(vendor/'libRuntimeRosettax87', target)
        subprocess.run(['codesign', '--force', '--sign', '-',
                        '--preserve-metadata=entitlements,requirements,flags,runtime', str(app)], check=True)
        subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True)
        for entry in entries:
            entry['installed_sha256'] = sha(Path(entry['target']))
        (backup/'manifest.json').write_text(json.dumps(dict(app=str(app), files=entries,
            signature_backup='app-signature'), indent=2)+'\n')
    except BaseException:
        for entry in entries:
            shutil.copy2(backup/entry['backup'], entry['target'])
        shutil.rmtree(signature)
        shutil.copytree(backup/'app-signature', signature)
        raise
    print(f'Installed and verified. Backup: {backup}')


if __name__ == '__main__':
    main()
