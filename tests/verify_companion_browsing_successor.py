#!/usr/bin/env python3
"""Exact display-only successor proof. Historical contracts remain unchanged.

An authenticated inverse source view chains to the parent endroll/font/I4
contracts. It is never compiled as the release. Current behavioral/native
checks remain separate and are required alongside this source-only proof.
"""
from pathlib import Path
import argparse,base64,gzip,hashlib,json,subprocess,sys,tempfile
import verify_endroll_successor as parent
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'docs/companion-browsing/successor-contract.json'
CONTRACT_SHA='f82e113792fab92f8c3e771fe09d0816a1ded35618d0db5fad9e44c5ffb51efb'
DELTA={'src/quickparty.c','src/companion_guide.c','src/companion_guide.h','src/companion_guide_text.c','src/companion_guide_text.h',*(f'src/companion_guide_text_data/part_{i:03}.inc' for i in (48,49,50))}
sha=lambda b:hashlib.sha256(b).hexdigest()
def verify(changes=None,contract_bytes=None,chain=True):
 changes=changes or {}
 def read(path):return changes[path]if path in changes else(ROOT/path).read_bytes()
 raw=CONTRACT.read_bytes()if contract_bytes is None else contract_bytes
 assert sha(raw)==CONTRACT_SHA,'companion contract changed';c=json.loads(raw)
 assert set(c['changed_runtime'])==DELTA,'unexpected runtime scope'
 assert sha(read('docs/endroll/successor-contract.json'))==c['parent_endroll_contract_sha256']==parent.CONTRACT_SHA
 packed=read('docs/companion-browsing/endroll-parent.json.gz');assert sha(packed)==c['parent_snapshot_sha256']
 snapshot=json.loads(gzip.decompress(packed));old=snapshot['runtime'];expected=dict(old)
 restored={k:base64.b64decode(v)for k,v in snapshot['restored_files'].items()}
 for path,row in c['changed_runtime'].items():
  assert old.get(path)==row['before']and row['after'] is not None
  if row['before'] is not None:assert sha(restored[path])==row['before']
  expected[path]=row['after']
 assert {str(p.relative_to(ROOT))for p in(ROOT/'src').rglob('*')if p.is_file()}|{'linker.ld'}==set(expected),'runtime file set changed'
 for path,want in expected.items():assert sha(read(path))==want,('runtime changed',path)
 for path,want in c['authoring_sha256'].items():assert sha(read(path))==want,('authoring changed',path)
 for path,want in c['parent_authoring_sha256'].items():assert sha(restored[path])==want
 if chain:
  with tempfile.TemporaryDirectory(prefix='companion-endroll-inverse-')as d:
   view=Path(d)
   for path in old:
    target=view/path;target.parent.mkdir(parents=True,exist_ok=True)
    if path in restored:target.write_bytes(restored[path])
    else:target.symlink_to(ROOT/path)
   for folder in ('docs','tools'):(view/folder).symlink_to(ROOT/folder,target_is_directory=True)
   (view/'Makefile').symlink_to(ROOT/'Makefile')
   (view/'assets').mkdir()
   for source in (ROOT/'assets').iterdir():
    rel=str(source.relative_to(ROOT));target=view/rel
    if rel in restored:target.write_bytes(restored[rel])
    else:target.symlink_to(source,target_is_directory=source.is_dir())
   # Endroll's authoring inputs exclude the companion generator. Its parent
   # font contract includes that generator, so restore only that exact input.
   saved=parent.ROOT;parent.ROOT=view
   try:pc,i4=parent.verify(changes={k:v for k,v in restored.items()if k.startswith('assets/')});parent.negative_controls()
   finally:parent.ROOT=saved
  return c,i4
 return c,None

def negatives():
 probes={}
 for path in sorted(DELTA|{'src/game.c','src/save5.c','src/music.c','assets/generate_companion_guide.py','docs/endroll/successor-contract.json','docs/companion-browsing/endroll-parent.json.gz'}):probes[path]={path:(ROOT/path).read_bytes()+b' '}
 for name,change in probes.items():
  try:verify(change,chain=False)
  except (AssertionError,ValueError):pass
  else:raise AssertionError('accepted mutation '+name)
 try:verify(contract_bytes=CONTRACT.read_bytes()+b' ',chain=False)
 except AssertionError:pass
 else:raise AssertionError('accepted contract mutation')
 return list(probes)+['contract tampering']

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);a=p.parse_args();c,i4=verify();neg=negatives()
 with tempfile.TemporaryDirectory(prefix='companion-i4-renderer-')as d:
  temp=Path(d);(temp/'src').mkdir();(temp/'src/game.c').write_bytes(i4)
  pins=json.loads((ROOT/'tests/fixtures/render-equipment-i4/reference.json').read_text())['context_source_pins']
  for rel in pins:(temp/rel).write_bytes((ROOT/rel).read_bytes())
  subprocess.run([sys.executable,str(ROOT/'tests/verify_late_renderer.py'),'--equipment-rewards-successor','--source-root',str(temp)],check=True)
 report={'result':'PASS','contract_sha256':CONTRACT_SHA,'changed_runtime_files':len(DELTA),'negative_controls':neg,'parent_endroll_font_i4_chain':'PASS','inherited_renderer':'PASS','scope':__doc__}
 if a.output:a.output.parent.mkdir(parents=True,exist_ok=True);a.output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
