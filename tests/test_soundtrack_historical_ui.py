#!/usr/bin/env python3
"""Unchanged G5 UI positives/negatives on authenticated historical-only input.

The exact old corpus is reconstructed for source checks only; current glyphs,
spans, geometry, and native pixels are checked by separate current suites.
"""
from pathlib import Path
import argparse,base64,gzip,hashlib,json,os,shutil,subprocess,sys,tempfile
from verify_soundtrack_successor import verify,ROOT,sha
MANIFEST_SHA='ed09025e05dfa1cc8a28196b65a18504a8c3fd6f2a6985cad081f3ebdd151d25'
D=ROOT/'docs/soundtrack-successor'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--parent',action='store_true');a=p.parse_args();verify()
 raw=(D/'historical-g5-ui.json').read_bytes();assert sha(raw)==MANIFEST_SHA
 m=json.loads(raw);packed=(D/'historical-g5-ui.json.gz').read_bytes();assert sha(packed)==m['payload_sha256']
 files={k:base64.b64decode(v,validate=True)for k,v in json.loads(gzip.decompress(packed)).items()}
 assert {k:sha(v)for k,v in files.items()}==m['files']
 assert all(k in ('src/ui.c','src/ui.h')or k.startswith('src/ui_data/')or k.startswith('assets/')for k in files)
 with tempfile.TemporaryDirectory(prefix='historical-g5-proof-only-')as d:
  view=Path(d)
  for k,b in files.items():target=view/k;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(b)
  for source in(ROOT/'assets').iterdir():
   target=view/'assets'/source.name
   if not target.exists():target.symlink_to(source,target_is_directory=source.is_dir())
  (view/'docs').symlink_to(ROOT/'docs',target_is_directory=True);(view/'tests').mkdir()
  name='test_retained_ui_successor.py'if a.parent else'test_retained_ui_story_successor.py'
  expected={'test_retained_ui_story_successor.py':'4aa5c85fc9c732633e350185da06fd21286066a3aa8da3b8fc00846be1535be9','test_retained_ui_successor.py':'9dc02b0ed55f523e6f9fb64562dbd0ad869ad5ae39860f0206670c0cea7bd8c6'}
  assert sha((ROOT/'tests'/name).read_bytes())==expected[name], 'historical test changed'
  shutil.copyfile(ROOT/'tests'/name,view/'tests'/name)
  cmd=[sys.executable,str(view/'tests'/name)]+(['--journey-story-ui-successor']if a.parent else[])
  env={**os.environ,'PYTHONPATH':str(ROOT/'tests')}
  subprocess.run(cmd,check=True,env=env)
 print('PASS historical G5 corpus and unchanged mutation suite; no current-pixel claim')
if __name__=='__main__':main()
