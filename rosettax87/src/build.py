#!/usr/bin/env python3
"""Build the patched Rosetta x87 companion and pair it with the stable loader."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    source = Path(__file__).resolve().parent / 'upstream'
    payload = source.parent.parent / 'runtime'
    manifest = json.loads((payload / 'manifest.json').read_text())
    loader = payload / 'rosettax87'
    if hashlib.sha256(loader.read_bytes()).hexdigest() != manifest['files']['rosettax87']['sha256']:
        parser.error('Matching loader hash differs')
    out = args.out.expanduser().resolve()
    out.mkdir(parents=True, exist_ok=False)
    subprocess.run(['cmake', '-S', str(source), '-B', str(out / 'build'),
                    '-DCMAKE_BUILD_TYPE=Debug', '-DCMAKE_OSX_ARCHITECTURES=arm64',
                    '-DCMAKE_CXX_FLAGS=-fno-stack-check'], check=True)
    subprocess.run(['cmake', '--build', str(out / 'build'), '--target',
                    'libRuntimeRosettax87', '-j', '6'], check=True)
    runtime = out / 'runtime'
    runtime.mkdir()
    shutil.copy2(loader, runtime / loader.name)
    shutil.copy2(out / 'build/bin/libRuntimeRosettax87', runtime / 'libRuntimeRosettax87')
    print(f'Runtime: {runtime}')


if __name__ == '__main__':
    main()
