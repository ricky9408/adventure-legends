#!/usr/bin/env python3
"""Synthetic native renderer differential, separate from controller-earned QA.
Only scene/cache setup writes below are used. Identical real cartridge rendering
runs independently on each ROM. No machine state is transferred between ROMs.
"""
import argparse,gzip,hashlib,json,re,struct,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
SCRIPT_BYTES=Path(__file__).read_bytes()
FIELDS=('game_state','room','px','py','camera_x','camera_y','journal_tab','cache_valid','prev_keys','quickparty_open','frame','progression_evolution_count','progression_evolution_source_form','progression_evolution_reason','save_begin_pending','save_completion_pending','event_warmup','evolution_tick','evolution_before')

def run(root,producer,out):
 rom=root/'build/emberbond.gba';sym=rom.with_suffix('.sym');manifest=root/'build/source-hashes.json'
 sources=json.loads(manifest.read_text());pins={p:sha(p) for p in (rom,sym,rom.with_suffix('.elf'),manifest)}
 assert all(sha(root/k)==v for k,v in sources.items())
 symbols={v[2]:int(v[0],16) for line in sym.read_text().splitlines() if len(v:=line.split())==3};d=json.loads(producer.read_text());provenance=d['provenance'];fixture=ROOT/provenance['fixture_relative'] if 'fixture_relative' in provenance else Path(provenance['fixture_path']);assert sha(fixture)==provenance['sram_sha256']
 out.mkdir(parents=True,exist_ok=False);results=[];writes=0
 with Emulator(rom) as e:
  e.load_save(fixture);e.reset()
  for c in d['inputs']:
   if c['frame']>=362:break
   e.frames(min(c['frames'],362-c['frame']),c['keys'])
  assert e.read(symbols['game_state'])==1
  def put(n,v,offset=0):
   nonlocal writes
   assert n in FIELDS;e.write(symbols[n]+offset,v);writes+=1
  for area in range(62):
   # Zero camera is legal for every scene, including single-screen interiors.
   for old in range(11):
    for new in (2,3,4):
     for name,value in [('game_state',3),('room',area),('px',120),('py',100),('camera_x',0),('camera_y',0),('journal_tab',old),('cache_valid',0),('prev_keys',0),('quickparty_open',0)]:put(name,value)
     put('cache_valid',0,4);e.frames(6)
     put('journal_tab',new);e.frames(6)
     im=e.screenshot();record=dict(area=area,old=old,new=new,rgb=hashlib.sha256(im.tobytes()).hexdigest(),oam=hashlib.sha256(e.bytes(0x07000000,1024)).hexdigest(),page=(e.read(0x04000000,2)>>4)&1)
     results.append(record)
   if area%8==0:print('area',area,flush=True)
  # Deliberately stale camera/world keys must cause a full repair rather than
  # retain a previous room's outer-world pixels or saved y153 row.
  scroll_function=re.search(r'int scrolling_room\(void\)\{([^}]+)\}',(root/'src/game.c').read_text()).group(1)
  scrolling=tuple(map(int,re.findall(r'room==(\d+)',scroll_function)))
  assert scrolling==(1,16,17,22,23,30,31,38,39,46,47,48,51,54,56,57,58)
  for area in scrolling:
   for cx,cy in ((2,2),(120,80),(240,160)):
    for old,new in ((2,3),(4,3),(1,2)):
     for name,value in [('game_state',3),('room',area),('px',240),('py',200),('camera_x',0),('camera_y',0),('journal_tab',old),('cache_valid',0),('prev_keys',0),('quickparty_open',0)]:put(name,value)
     put('cache_valid',0,4);e.frames(6);put('camera_x',cx);put('camera_y',cy);put('journal_tab',new);e.frames(6)
     im=e.screenshot();results.append(dict(area=area,old=old,new=new,camera=[cx,cy],rgb=hashlib.sha256(im.tobytes()).hexdigest(),oam=hashlib.sha256(e.bytes(0x07000000,1024)).hexdigest()))
  # Independently rendered card states and actual SAVE->PAUSE coverage.
  # Pending-state setup freezes the scheduler rather than fabricating a save.
  # These are renderer cases only, not transaction or acquisition evidence.
  def bitmap_hash():
   address=0x0600A000 if e.read(0x04000000,2)&16 else 0x06000000
   raw=b''.join(struct.pack('<I',e.read(address+i,4)) for i in range(0,38400,4))
   return hashlib.sha256(raw).hexdigest()
  def setup(area,cx,cy,state,tab=3,count=2,tick=0):
   for name,value in [('game_state',state),('room',area),('px',120),('py',100),('camera_x',cx),('camera_y',cy),('journal_tab',tab),('cache_valid',0),('prev_keys',0),('quickparty_open',0),('save_begin_pending',100),('save_completion_pending',0),('event_warmup',100),('progression_evolution_count',count),('progression_evolution_source_form',49),('progression_evolution_reason',2),('evolution_tick',tick),('evolution_before',49)]:put(name,value)
   put('cache_valid',0,4);e.frames(8)
  for area in range(62):
   cameras=((0,0),(1,1),(119,79),(239,159),(240,160)) if area in scrolling else ((0,0),)
   for cx,cy in cameras:
    for state,count,tick,tab in ((7,1,0,3),(7,2,0,3),(6,2,0,3),(10,2,0,3),(8,2,0,3),(8,2,40,3),(3,2,0,0)):
     setup(area,cx,cy,state,count=count,tick=tick,tab=tab)
     results.append(dict(area=area,state=state,count=count,evolution_start_tick=tick,tab=tab,camera=[cx,cy],rgb=bitmap_hash(),oam='not-compared-animation-clock',comparison='all38400 native indexed framebuffer bytes; world OBJ animation separately tested'))
    for target in (2,3,4):
     setup(area,cx,cy,6,tab=target);put('game_state',3);e.frames(8)
     results.append(dict(area=area,state='SAVE-to-PAUSE',new=target,camera=[cx,cy],rgb=bitmap_hash(),oam='not-compared-animation-clock',comparison='all38400 native indexed framebuffer bytes'))
 assert all(sha(root/k)==v for k,v in sources.items()) and all(sha(p)==v for p,v in pins.items()),'Input closure changed during rendering'
 report=dict(scope='Synthetic scene and cache setup, not controller acquisition or native pacing acceptance',rom_sha256=sha(rom),symbol_sha256=sha(sym),source_manifest_sha256=sha(manifest),source_sram_sha256=sha(fixture),write_fields=FIELDS,game_ram_writes=writes,cross_rom_machine_states=0,results=results)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');return report

def main():
 p=argparse.ArgumentParser(description=__doc__)
 source=p.add_mutually_exclusive_group(required=True)
 source.add_argument('--before-root',type=Path)
 source.add_argument('--baseline-report',type=Path,help='Pinned prior native case hashes; no prior ROM needed')
 for k in ('after-root','output'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--producer',type=Path,default=ROOT/'tests/fixtures/return-modal-bootstrap.json')
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);(a.output/'helper-source.py').write_bytes(SCRIPT_BYTES)
 if a.before_root:b=run(a.before_root.resolve(),a.producer.resolve(),a.output/'before')
 else:
  raw=a.baseline_report.read_bytes();b=json.loads(gzip.decompress(raw) if a.baseline_report.suffix=='.gz' else raw)
 c=run(a.after_root.resolve(),a.producer.resolve(),a.output/'after')
 assert len(b['results'])==len(c['results']), 'Native case count changed'
 identity=('area','old','new','camera','state','count','evolution_start_tick','tab')
 failures=[dict(before=x,after=y) for x,y in zip(b['results'],c['results']) if any(x.get(k)!=y.get(k)for k in identity) or x['rgb']!=y['rgb'] or x['oam']!=y['oam']]
 report=dict(suite='native-modal-cache-and-opaque-boundary-all-scenes',before_rom=b['rom_sha256'],after_rom=c['rom_sha256'],cases=len(c['results']),full_screen_pixels_compared=38400*len(c['results']),failures=failures,helper_sha256=hashlib.sha256(SCRIPT_BYTES).hexdigest(),synthetic_setup=True)
 (a.output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not failures
if __name__=='__main__':main()
