#!/usr/bin/env python3
"""Deterministic one-record-per-line authoring JSON; values/order are unchanged."""
import json
from pathlib import Path
import sys

PATH = Path(__file__).with_name('catalog.json')

def format_catalog(data):
    compact = lambda value: json.dumps(value, ensure_ascii=False, separators=(',', ':'))
    entries = []
    for key, value in data.items():
        if isinstance(value, list) and value and all(isinstance(row, dict) for row in value):
            rendered = '[\n' + ',\n'.join('    ' + compact(row) for row in value) + '\n  ]'
        else:
            rendered = compact(value)
        entries.append('  ' + json.dumps(key) + ': ' + rendered)
    return '{\n' + ',\n'.join(entries) + '\n}\n'

if __name__ == '__main__':
    old = PATH.read_text()
    data = json.loads(old)
    result = format_catalog(data)
    assert json.loads(result) == data
    if '--check' in sys.argv:
        if old != result:
            raise SystemExit('Run assets/creatures/format_catalog.py to normalize authoring JSON')
        print('Catalog formatting is deterministic and semantic-preserving')
    else:
        PATH.write_text(result)
        print(f'{PATH.name}: {len(result.encode())} bytes')
