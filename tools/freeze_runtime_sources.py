#!/usr/bin/env python3
"""Record runtime inputs immediately after a successful cartridge build.

The native harnesses independently authenticate the ROM/symbol/ELF pair and
reject source edits after this manifest was produced. This is a build receipt,
not a substitute for a clean reproducible build or generator verification.
"""
import hashlib
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=ROOT / 'build/source-hashes.json')
    args = parser.parse_args()
    paths = sorted(p for p in (ROOT / 'src').rglob('*') if p.is_file())
    paths.append(ROOT / 'linker.ld')
    manifest = {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in paths}
    target = args.output.resolve()
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(manifest, indent=2) + '\n')
    print(f'{target}: {len(manifest)} frozen runtime inputs')

if __name__ == '__main__':
    main()
