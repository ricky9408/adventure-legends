#!/usr/bin/env python3
"""Exact endroll delta and chained GBJ/I4 proof; no historical pins are relaxed.

The isolated inverse view is read-only proof input, never a game build. Actual
endroll clipping, input/save/audio behavior and timing have separate host/native
gates. Exact current text inputs and all runtime bytes remain authenticated.
"""
from pathlib import Path
import argparse,gzip,hashlib,json,re,subprocess,sys,tempfile
import verify_gbj_font_successor as font
ROOT=Path(__file__).resolve().parents[1]
CONTRACT=ROOT/'docs/endroll/successor-contract.json'
CONTRACT_SHA='4b1b5583e5f200410f09c48486dda97439b3980776bf1aa0380e6a5c3e30efeb'
NEW_FILES={'src/ending_credits.c','src/ending_credits.h','src/ending_credits_text.c','src/ending_credits_text.h',*(f'src/ending_credits_text_data/part_{i:03}.inc'for i in range(4))}
sha=lambda b:hashlib.sha256(b).hexdigest()
def verify(changes=None,contract_bytes=None,parent_chain=True):
 changes=changes or {}
 def read(path):return changes[path]if path in changes else(ROOT/path).read_bytes()
 raw=CONTRACT.read_bytes()if contract_bytes is None else contract_bytes
 assert sha(raw)==CONTRACT_SHA,'endroll contract changed';c=json.loads(raw)
 assert sha(read('docs/gbj-font/successor-contract.json'))==c['parent_font_contract_sha256']
 parent_raw=gzip.decompress(read('docs/endroll/gbj-runtime.json.gz'))
 assert sha(parent_raw)==c['parent_runtime_sha256'],'font parent receipt changed'
 parent=json.loads(parent_raw);expected=dict(parent)
 assert set(c['changed_runtime'])==NEW_FILES|{'src/game.c'},'runtime delta scope changed'
 for path,d in c['changed_runtime'].items():
  assert parent.get(path)==d['before']and d['after']is not None
  expected[path]=d['after']
 assert {str(p.relative_to(ROOT))for p in(ROOT/'src').rglob('*')if p.is_file()}|{'linker.ld'}==set(expected)
 for path,want in expected.items():assert sha(read(path))==want,('runtime byte changed',path)
 normalized=read('src/game.c').decode();assert 'TX_FONT_'not in normalized,'title font attribution returned'
 for patch in reversed(c['game_changes']):
  assert normalized.count(patch['after'])==patch['occurrences'],'ambiguous ending source site'
  normalized=normalized.replace(patch['after'],patch['before'])
 assert sha(normalized.encode())==parent['src/game.c'],'change beyond reviewed ending sites'
 for path,want in c['input_sha256'].items():assert sha(read(path))==want,('endroll authoring changed',path)
 if parent_chain:
  with tempfile.TemporaryDirectory(prefix='endroll-font-inverse-')as d:
   view=Path(d)
   for path in parent:
    target=view/path;target.parent.mkdir(parents=True,exist_ok=True)
    if path=='src/game.c':target.write_text(normalized)
    else:target.symlink_to(ROOT/path)
   for folder in ('assets','docs','tools'):(view/folder).symlink_to(ROOT/folder,target_is_directory=True)
   font_inputs=json.loads(font.CONTRACT.read_text())['font_input_sha256']
   font_contract,i4_game=font.verify(root=view,changes={k:v for k,v in changes.items()if k in font_inputs})
   assert font.CONTRACT_SHA==c['parent_font_contract_sha256']
  return c,i4_game
 return c,None

def negative_controls():
 game=(ROOT/'src/game.c').read_bytes();module=(ROOT/'src/ending_credits.c').read_bytes()
 probes={
  'title attribution restored':{'src/game.c':game.replace(b'else centered(TX_BUILD,132,CREAM);}return;}',b'else centered(TX_BUILD,132,CREAM);}centered(TX_FONT_URL,149,CREAM);return;}')},
  'replay writes save':{'src/game.c':game.replace(b'if(!(chapter_flags&SAVE4_ENDING_SEEN)){',b'if(1){')},
  'initial ending save removed':{'src/game.c':game.replace(b'completed=1;save_at(0,3);',b'completed=1;')},
  'actors overlap credits':{'src/game.c':game.replace(b'if(ending_credits_phase)return;',b'')},
  'scroll cache key removed':{'src/game.c':game.replace(b'game_state==WIN?ending_credits_revision:(unsigned)title_option',b'(unsigned)title_option')},
  'held keys skip':{'src/ending_credits.c':module.replace(b'if(!ending_credits_armed){',b'if(0){',1)},
  'clipping boundary escaped':{'src/ending_credits.c':module.replace(b'yy<TOP||yy>=BOTTOM',b'yy<TOP-1||yy>BOTTOM')},
  'scroll end changed':{'src/ending_credits.c':module.replace(b'+15-TOP',b'+16-TOP')},
  'GeeBee attribution removed':{'assets/ending_credits.json':(ROOT/'assets/ending_credits.json').read_bytes().replace(b'GeeBee',b'Unknown')},
  'unrelated gameplay change':{'src/equipment.c':(ROOT/'src/equipment.c').read_bytes()+b'\n'},
  'font config changed':{'assets/fonts/gbj/GBJ.json':(ROOT/'assets/fonts/gbj/GBJ.json').read_bytes()+b' '},
 }
 # Parent chain must check font inputs too; current source proof checks each
 # endroll pixel/span/count/width against its pinned generated output.
 path='src/ending_credits_text_data/part_000.inc';raw=(ROOT/path).read_bytes();m=re.search(rb'\{(\d+),(\d+),(\d+)\}',raw);assert m
 for label,group in [('span offset',1),('span count',2),('span pixel mask',3)]:
  start,end=m.span(group);probes[label]={path:raw[:start]+str(int(m[group])+1).encode()+raw[end:]}
 table=next(p for p in(ROOT/'src/ending_credits_text_data').glob('*.inc')if b'const UiText ending_credits_texts' in p.read_bytes());raw=table.read_bytes();m=re.search(rb'\{(\d+),(\d+),0,\{ec_',raw);assert m
 probes['text width']={str(table.relative_to(ROOT)):raw[:m.start(1)]+str(int(m[1])+1).encode()+raw[m.end(1):]}
 # Verify parent-font source tampering through the same reader before chaining.
 # Endroll input delta intentionally doesn't repin or replace any GBJ asset.
 for name,changed in probes.items():
  assert any((ROOT/p).read_bytes()!=b for p,b in changed.items()),('ineffective probe',name)
  try:verify(changes=changed,parent_chain=name=='font config changed')
  except (AssertionError,ValueError):pass
  else:raise AssertionError('accepted mutation '+name)
 try:verify(contract_bytes=CONTRACT.read_bytes()+b' ')
 except AssertionError:pass
 else:raise AssertionError('accepted contract mutation')
 return list(probes)+['contract tampering']

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path);p.add_argument('--skip-renderer',action='store_true');a=p.parse_args()
 c,i4_game=verify();neg=negative_controls()
 if not a.skip_renderer:
  with tempfile.TemporaryDirectory(prefix='endroll-i4-renderer-')as d:
   temp=Path(d);(temp/'src').mkdir();(temp/'src/game.c').write_bytes(i4_game)
   pins=json.loads((ROOT/'tests/fixtures/render-equipment-i4/reference.json').read_text())['context_source_pins']
   for rel in pins:(temp/rel).write_bytes((ROOT/rel).read_bytes())
   cmd=[sys.executable,str(ROOT/'tests/verify_late_renderer.py'),'--equipment-rewards-successor','--source-root',str(temp)]
   if a.output:cmd+=['--output',str(a.output.with_name('inherited-renderer.json'))]
   subprocess.run(cmd,check=True)
 report={'result':'PASS','endroll_contract_sha256':CONTRACT_SHA,'font_contract_sha256':c['parent_font_contract_sha256'],'runtime_files':1947,'changed_runtime_files':9,'exact_reversible_game_change_sites':sum(p['occurrences']for p in c['game_changes']),'negative_controls':neg,'parent_font_and_i4_proof':'PASS','renderer_rerun':not a.skip_renderer,'scope':'Exact current endroll delta; chained inverse view for inherited source-only renderer proof. Native current ending flow is tested separately.'}
 if a.output:a.output.write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps(report))
if __name__=='__main__':main()
