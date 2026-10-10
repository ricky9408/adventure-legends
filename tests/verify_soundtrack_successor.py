#!/usr/bin/env python3
"""Exact soundtrack boundary and historical inverse proof, never a ROM projection.

Current-ROM behavioral/native tests run separately against unmodified runtime.
Historical renderer/UI pixels are not claimed to equal the current presentation.
"""
from pathlib import Path
from contextlib import contextmanager
import argparse,base64,gzip,hashlib,json,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1]
CONTRACT_SHA='d04ee42034fa2f867643afa399327a60c8e952f2664bc89198e205f2cb46d3e6'
CONTRACT=ROOT/'docs/soundtrack-successor/contract.json'
INVERSE=ROOT/'docs/soundtrack-successor/parent-inverse.json.gz'
sha=lambda b:hashlib.sha256(b).hexdigest()

def load():
 raw=CONTRACT.read_bytes();assert sha(raw)==CONTRACT_SHA,'soundtrack contract changed';c=json.loads(raw)
 assert c['schema']==1 and c['name']=='reviewed-23-cue-soundtrack-successor'
 assert set(c['changed'])=={'src/music.c','src/music_data.c','src/music_data.h',*(f'src/ending_credits_text_data/part_{i:03}.inc'for i in (1,2,3))}
 assert set(c['added'])=={'src/music_copy.h','src/music_catalog.h',*[k for k in c['added']if k.startswith('src/music_data/')and k.endswith('.inc')]}
 assert all(k.startswith('src/music_data/')and k.endswith('.inc')for k in c['removed'])
 assert set(c['current_runtime'])==(set(c['parent_runtime'])-set(c['removed']))|set(c['added'])
 assert {k for k in c['parent_runtime'].keys()&c['current_runtime'].keys()if c['parent_runtime'][k]!=c['current_runtime'][k]}==set(c['changed'])
 return c

def state(c):
 files={str(p.relative_to(ROOT)):sha(p.read_bytes())for p in(ROOT/'src').rglob('*')if p.is_file()};files['linker.ld']=sha((ROOT/'linker.ld').read_bytes())
 authoring={k:sha((ROOT/k).read_bytes())for k in c['current_authoring']}
 contracts={k:sha((ROOT/k).read_bytes())for k in c['historical_contracts']}
 return {'runtime':files,'authoring':authoring,'contracts':contracts,'inverse':sha(INVERSE.read_bytes())}

def authenticate(c,s):
 assert s['runtime']==c['current_runtime'],'unreviewed runtime bytes or file set'
 assert s['authoring']==c['current_authoring'],'unreviewed soundtrack authoring/PCM input'
 assert s['contracts']==c['historical_contracts'],'historical proof input changed'
 assert s['inverse']==c['inverse_sha256'],'inverse archive changed'

def negatives(c,s):
 import copy
 authenticate(c,s) # Clean positive first: no vacuous rejection controls.
 probes=[]
 def reject(label,group,key,value=None,remove=False):
  changed=copy.deepcopy(s)
  if group=='inverse':changed[group]='0'*64
  elif remove:del changed[group][key]
  else:changed[group][key]=value or (sha((ROOT/key).read_bytes()+b'\0')if (ROOT/key).is_file()else'0'*64)
  assert changed!=s,label
  try:authenticate(c,changed)
  except AssertionError:probes.append(label)
  else:raise AssertionError('accepted negative '+label)
 for p in ['src/game.c','src/save5.c','src/gear_runtime.c','src/music.c','src/music_copy.h','src/music_catalog.h',*c['added'][-1:],*c['changed'][:3]]:
  reject('changed '+p,'runtime',p)
 reject('unexpected runtime file','runtime','src/unreviewed.c')
 reject('deleted runtime file','runtime','src/game.c',remove=True)
 for p in c['current_authoring']:
  reject('changed authoring '+p,'authoring',p)
 for p in c['historical_contracts']:reject('changed historical contract '+p,'contracts',p)
 reject('inverse payload tampering','inverse',None)
 try:
  assert sha(CONTRACT.read_bytes()+b' ') == CONTRACT_SHA
 except AssertionError:probes.append('current contract tampering')
 else:raise AssertionError('accepted current contract tampering')
 return probes

@contextmanager
def parent_view(c):
 packed=INVERSE.read_bytes();assert sha(packed)==c['inverse_sha256']
 restored={k:base64.b64decode(v,validate=True)for k,v in json.loads(gzip.decompress(packed)).items()}
 assert {k:sha(v)for k,v in restored.items()}==c['inverse_files_sha256']
 assert set(restored)==set(c['changed'])|set(c['removed'])|{'assets/ending_credits.json'}
 with tempfile.TemporaryDirectory(prefix='soundtrack-authenticated-parent-')as d:
  view=Path(d)
  for path,want in c['parent_runtime'].items():
   data=restored[path]if path in restored else(ROOT/path).read_bytes();assert sha(data)==want,('parent byte mismatch',path)
   target=view/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  assert {str(p.relative_to(view))for p in(view/'src').rglob('*')if p.is_file()}|{'linker.ld'}==set(c['parent_runtime'])
  (view/'Makefile').symlink_to(ROOT/'Makefile')
  for name in ('docs','tools','tests'):(view/name).symlink_to(ROOT/name,target_is_directory=True)
  (view/'assets').mkdir()
  for source in(ROOT/'assets').iterdir():
   target=view/'assets'/source.name;rel='assets/'+source.name
   if rel in restored:target.write_bytes(restored[rel])
   else:target.symlink_to(source,target_is_directory=source.is_dir())
  yield view

def verify():
 c=load();s=state(c);authenticate(c,s)
 import verify_companion_browsing_successor as previous
 with parent_view(c)as view:
  old=previous.ROOT;previous.ROOT=view
  try:_,i4=previous.verify();previous.negatives()
  finally:previous.ROOT=old
 assert i4 is not None
 return c,i4

@contextmanager
def renderer_view(i4):
 with tempfile.TemporaryDirectory(prefix='soundtrack-historical-renderer-')as d:
  view=Path(d);(view/'src').mkdir();(view/'src/game.c').write_bytes(i4)
  pins=json.loads((ROOT/'tests/fixtures/render-equipment-i4/reference.json').read_text())['context_source_pins']
  for path,want in pins.items():
   data=(ROOT/path).read_bytes();assert sha(data)==want;target=view/path;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
  (view/'tests').symlink_to(ROOT/'tests',target_is_directory=True)
  yield view

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--renderer-negatives',action='store_true');p.add_argument('--output',type=Path);a=p.parse_args()
 c,i4=verify();rejected=negatives(c,state(c))
 with renderer_view(i4)as view:
  if a.renderer_negatives:
   import unittest,test_renderer_equipment_successor as original
   assert sha((ROOT/'tests/test_renderer_equipment_successor.py').read_bytes())=='c64c1b00333d24b6f47432ed4b23aa49cce5801b5ccbe2520611a54cb7a8583f'
   old=original.ROOT;original.ROOT=view
   try:result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(original));assert result.wasSuccessful()
   finally:original.ROOT=old
  else:subprocess.run([sys.executable,str(ROOT/'tests/verify_late_renderer.py'),'--equipment-rewards-successor','--source-root',str(view)],check=True)
 report={'result':'PASS','scope':__doc__,'contract_sha256':CONTRACT_SHA,'current_runtime_files':len(c['current_runtime']),'exact_parent_files':len(c['parent_runtime']),'mutation_negatives':rejected,'historical_renderer_negative_suite':a.renderer_negatives}
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
