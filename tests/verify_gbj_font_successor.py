#!/usr/bin/env python3
"""Fail-closed GBJ font-only successor proof; historical gates are unchanged.

Authenticates every runtime byte against I4 plus a pinned font delta. The only
handwritten runtime change is one title-credit draw. An isolated TITLE-only
inverse view is passed to the unchanged pure-renderer verifier; it is never
compiled into a ROM or claimed as current gameplay acceptance. Current text
pixels are separately tested in test_gbj_font, shared-span, native and layout
suites. No arbitrary new raster is normalized to the old font.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,subprocess,sys,tempfile,shutil
ROOT=Path(__file__).resolve().parents[1]
CONTRACT_SHA='1b5ff977e4b93156a073aca4017d49aa1f7d99fd37e716d7bf07faf799fb5a81'
CONTRACT=ROOT/'docs/gbj-font/successor-contract.json'
sha=lambda b:hashlib.sha256(b).hexdigest()

def verify(root=ROOT,changes=None,contract_bytes=None):
 changes=changes or {};root=Path(root)
 def read(path):return changes[path] if path in changes else (root/path).read_bytes()
 raw=contract_bytes if contract_bytes is not None else CONTRACT.read_bytes()
 assert sha(raw)==CONTRACT_SHA,'font contract changed'
 c=json.loads(raw)
 parent_raw=gzip.decompress(read('docs/gbj-font/i4-runtime.json.gz'))
 assert sha(parent_raw)==c['parent_runtime_sha256'],'parent runtime receipt changed'
 parent=json.loads(parent_raw);expected=dict(parent)
 for path,d in c['changed_runtime'].items():
  assert parent.get(path)==d['before'],'wrong parent delta'
  assert path in ('src/game.c','src/ui.h','src/ui.c','src/journey_map_text.c','src/companion_guide_text.c','src/gear_preview_text.c','src/treasure_text_text.c','src/opening_scene_data.c') or any(path.startswith('src/'+family+'/')for family in ('ui_data','companion_guide_text_data','gear_preview_text_data','treasure_text_text_data','opening_scene_data')),'out-of-scope runtime delta'
  if d['after'] is None:expected.pop(path)
  else:expected[path]=d['after']
 actual={str(p.relative_to(root))for p in(root/'src').rglob('*')if p.is_file()}|{'linker.ld'}
 assert actual==set(expected),'runtime file set changed'
 for path,want in expected.items():assert sha(read(path))==want,('runtime changed',path)
 game=read('src/game.c');footer=c['footer'].encode()
 assert game.count(footer)==1,'missing or duplicated title credit'
 normalized=game.replace(footer,b'',1)
 assert sha(normalized)==parent['src/game.c'],'change beyond title credit'
 header=read('src/ui.h')
 for name in c['credit_ids']:
  token=(' TX_'+name+',\n').encode();assert header.count(token)==1
  header=header.replace(token,b'',1)
 assert sha(header)==c['parent_ui_h_sha256'],'existing UI ID changed'
 for path,want in c['parent_metadata_sha256'].items():
  value=json.loads(read(path))
  if path=='assets/ui_texts.json':
   for name,text in c['credit_texts'].items():assert value.pop(name)==text
  assert sha((json.dumps(value,ensure_ascii=False,indent=2)+'\n').encode())==want,('existing authored text changed',path)
 for path,want in c['font_input_sha256'].items():assert sha(read(path))==want,('font input changed',path)
 return c,normalized

def negatives():
 c,_=verify();game=(ROOT/'src/game.c').read_bytes();footer=c['footer'].encode();header=(ROOT/'src/ui.h').read_bytes();tests={
 'footer missing':{'src/game.c':game.replace(footer,b'',1)},
 'footer duplicated':{'src/game.c':game.replace(footer,footer*2,1)},
 'footer typo':{'src/game.c':game.replace(footer,footer.replace(b'149',b'148'),1)},
 'unrelated game code':{'src/game.c':game+b'\n/* unreviewed */\n'},
 'enum reorder':{'src/ui.h':header.replace(b' TX_SUBTITLE,\n TX_START,',b' TX_START,\n TX_SUBTITLE,')},
 'enum insert':{'src/ui.h':header.replace(b' TX_START,',b' TX_UNAPPROVED,\n TX_START,')},
 'existing dialogue':{'assets/ui_texts.json':(ROOT/'assets/ui_texts.json').read_bytes().replace('灯の契約'.encode(),'別の契約'.encode(),1)},
 }
 raster='src/ui_data/part_000.inc';b=(ROOT/raster).read_bytes()
 import re
 for name,group in [('span offset',1),('span count',2),('pixel mask',3)]:
  m=re.search(rb'\{(\d+),(\d+),(\d+)\}',b);assert m
  start,end=m.span(group);v=str(int(m[group])+1).encode();tests[name]={raster:b[:start]+v+b[end:]}
 table=next(p for p in(ROOT/'src/ui_data').glob('*.inc')if b'const UiText ui_texts' in p.read_bytes());b=table.read_bytes();m=re.search(rb'\{(\d+),(\d+),0,\{txt_',b);assert m
 tests['text width']={str(table.relative_to(ROOT)):b[:m.start(1)]+str(int(m[1])+1).encode()+b[m.end(1):]}
 for path in ('assets/fonts/gbj/GBJ.png','assets/fonts/gbj/GBJ.json','assets/gbj_font.py'):
  b=(ROOT/path).read_bytes();tests['font '+path]={path:b+b' '}
 for name,changes in tests.items():
  assert any((ROOT/k).read_bytes()!=v for k,v in changes.items()),('ineffective negative',name)
  try:verify(changes=changes)
  except (AssertionError,ValueError):pass
  else:raise AssertionError('accepted negative '+name)
 try:verify(contract_bytes=CONTRACT.read_bytes()+b' ')
 except AssertionError:pass
 else:raise AssertionError('accepted contract mutation')
 return list(tests)+['contract tampering']

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--skip-renderer',action='store_true');a=p.parse_args()
 c,normalized=verify();rejected=negatives()
 if not a.skip_renderer:
  with tempfile.TemporaryDirectory(prefix='gbj-title-inverse-')as d:
   temp=Path(d);(temp/'src').mkdir();(temp/'src/game.c').write_bytes(normalized)
   pins=json.loads((ROOT/'tests/fixtures/render-equipment-i4/reference.json').read_text())['context_source_pins']
   for rel in pins:(temp/rel).write_bytes((ROOT/rel).read_bytes())
   cmd=[sys.executable,str(ROOT/'tests/verify_late_renderer.py'),'--equipment-rewards-successor','--source-root',str(temp)]
   if a.output:cmd+=['--output',str(a.output.with_name('inherited-renderer-comparison.json'))]
   subprocess.run(cmd,check=True)
 report={'result':'PASS','contract_sha256':CONTRACT_SHA,'runtime_files_authenticated':len(json.loads((ROOT/'build/source-hashes.json').read_text())),'negative_controls_rejected':rejected,'renderer_rerun':not a.skip_renderer,'scope':'Exact font-only byte delta, preserved old IDs/texts and renderer functions; isolated title inverse only. No current-title gameplay claim from normalized source.'}
 if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
