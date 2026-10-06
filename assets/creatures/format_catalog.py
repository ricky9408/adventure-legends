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

def format_fragment(value):
    if isinstance(value,dict):return format_catalog(value)
    if not isinstance(value,list):raise ValueError('Expected catalog object or row array')
    return '[\n'+',\n'.join('  '+json.dumps(row,ensure_ascii=False,separators=(',',':')) for row in value)+'\n]\n'

if __name__ == '__main__':
    from catalog_source import load_catalog, MAX_SOURCE_BYTES
    descriptor=json.loads(PATH.read_text())
    paths=[PATH]
    if '$catalog_source' in descriptor:
        paths += [PATH.parent/name for names in descriptor['sections'].values() for name in names]
    before=load_catalog(PATH)
    for path in paths:
        old=path.read_text();data=json.loads(old)
        result=json.dumps(data,indent=2)+'\n' if path==PATH and '$catalog_source' in data else format_fragment(data)
        assert json.loads(result)==data
        if len(result.encode())>=MAX_SOURCE_BYTES:raise ValueError('Public catalog artifact reaches90KB: '+str(path))
        if '--check' in sys.argv:
            if old!=result:raise SystemExit('Run assets/creatures/format_catalog.py to normalize authoring JSON')
        else:path.write_text(result)
    assert load_catalog(PATH)==before
    print('Catalog source formatting is deterministic and semantic-preserving (%d bounded files)'%len(paths))
