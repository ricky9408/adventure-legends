#!/usr/bin/env python3
"""Only the three reviewed road directions may differ from accepted P2 UI."""
from pathlib import Path
import hashlib,json,re,unittest
ROOT=Path(__file__).resolve().parents[1]
import os,sys
from retained_ui_story_successor import read_view_for_flags
_UI=read_view_for_flags(ROOT,sys.argv)
CONTRACT=json.loads((ROOT/'docs/connected-roads/route-clue-ui-contract.json').read_text())
KEYS={'UW_CLUE45A','RT_VILLAGE_B','RT_HUD_COMMON'}
def digest(data):return hashlib.sha256(data).hexdigest()
def canonical(obj):return json.dumps(obj,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
def rasters():
    source=_UI.raster_source
    return {name:(key,statement)for statement,name,key in re.findall(r'(static const UiRun (txt_(\w+)_[01])\[\] = \{[^\n]*\};)',source)}
class RouteCopy(unittest.TestCase):
    def test_exact_approved_authoring_and_rendered_text(self):
        self.assertEqual(set(CONTRACT['allowed_keys']),KEYS)
        changes=json.loads((ROOT/'docs/connected-roads/late-route-clue-changes.json').read_text())['changes']
        self.assertEqual({c['key']for c in changes},KEYS)
        for c in changes:self.assertEqual(json.loads((ROOT/c['file']).read_text())[c['key']],c['new'])
        for c in CONTRACT['metadata_changes']:self.assertEqual(json.loads((ROOT/c['file']).read_text())[c['key']],c['new'])
    def test_other_metadata_values_and_enum_are_exact_p2(self):
        self.assertEqual(digest(_UI.header.encode()),CONTRACT['enum_sha256'])
        for file,expected in CONTRACT['unchanged_metadata_sha256'].items():
            values=_UI.metadata(file);self.assertEqual(digest(canonical({k:v for k,v in values.items()if k not in KEYS})),expected,file)
    def test_only_six_approved_paired_rasters_change(self):
        rows=rasters();unchanged=[rows[n][1]for n in sorted(rows)if rows[n][0]not in KEYS]
        self.assertEqual(len(unchanged),CONTRACT['unchanged_raster_statements'])
        self.assertEqual(digest('\n'.join(unchanged).encode()),CONTRACT['unchanged_raster_sha256'])
        changed={n for n,(k,_)in rows.items()if k in KEYS};self.assertEqual(changed,set(CONTRACT['new_raster_sha256']))
        self.assertEqual(len(changed),6)
        for name in changed:self.assertEqual(digest(rows[name][1].encode()),CONTRACT['new_raster_sha256'][name])
if __name__=='__main__':unittest.main(verbosity=2)
