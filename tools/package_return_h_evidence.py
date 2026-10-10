#!/usr/bin/env python3
"""Preserve the independent H receipts, compressing large reports losslessly.

This is an evidence-export helper. It requires the original, immutable review
directory; ordinary cartridge builds and current test recipes do not use it.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sha = lambda data: hashlib.sha256(data).hexdigest()

def main():
    p = argparse.ArgumentParser()
    p.add_argument('--review-root', type=Path, required=True)
    a = p.parse_args()
    acceptance = a.review_root / 'docs/integration-acceptance.json'
    rows = json.loads(acceptance.read_text())['artifacts']
    rows += [{'path': 'docs/integration-acceptance.json', 'sha256': sha(acceptance.read_bytes())}]
    exported = []
    for row in rows:
        data = (a.review_root / row['path']).read_bytes()
        assert sha(data) == row['sha256'], row['path']
        packed = len(data) > 90000
        rel = row['path'] + ('.gz' if packed else '')
        target = ROOT / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        content = gzip.compress(data, compresslevel=9, mtime=0) if packed else data
        target.write_bytes(content)
        exported.append(dict(original_path=row['path'], original_bytes=len(data),
            original_sha256=sha(data), exported_path=rel, exported_bytes=len(content),
            exported_sha256=sha(content), lossless_gzip=packed))
    receipt = dict(scope='Immutable independent H review receipts. Original large JSON reports are lossless gzip; decompress before following their original path references.',
        omitted_scope='Raw frame traces, WAV auditions, tool binaries and the complete reviewer workspace are retained locally and are not bundled. This is not a self-contained historical replay archive.',
        files=exported)
    (ROOT/'docs/evidence/return-h-review-export.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps(dict(files=len(exported), bytes=sum(x['exported_bytes'] for x in exported))))

if __name__ == '__main__':
    main()
