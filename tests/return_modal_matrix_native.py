#!/usr/bin/env python3
"""Synthetic native renderer differential, separate from controller-earned QA.
Only scene/cache setup writes below are used. Identical real cartridge rendering
runs independently on each ROM. No machine state is transferred between ROMs.
"""
import argparse,hashlib,json,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
FIELDS=('game_state','room','px','py','camera_x','camera_y','journal_tab','cache_valid','prev_keys','quickparty_open')

def run(root,producer,out):
 rom=root/'build/emberbond.gba';sym=rom.with_suffix('.sym');manifest=root/'build/source-hashes.json'
 assert all(sha(root/k)==v for k,v in json.loads(manifest.read_text()).items())
 symbols={v[2]:int(v[0],16) for line in sym.read_text().splitlines() if len(v:=line.split())==3};d=json.loads(producer.read_text());fixture=Path(d['provenance']['fixture_path']);assert sha(fixture)==d['provenance']['sram_sha256']
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
 report=dict(scope='Synthetic scene and cache setup, not controller acquisition or native pacing acceptance',rom_sha256=sha(rom),symbol_sha256=sha(sym),source_manifest_sha256=sha(manifest),source_sram_sha256=sha(fixture),write_fields=FIELDS,game_ram_writes=writes,cross_rom_machine_states=0,results=results)
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');return report

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('before-root','after-root','producer','output'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 b=run(a.before_root.resolve(),a.producer.resolve(),a.output/'before');c=run(a.after_root.resolve(),a.producer.resolve(),a.output/'after')
 failures=[dict(before=x,after=y) for x,y in zip(b['results'],c['results']) if x['rgb']!=y['rgb'] or x['oam']!=y['oam']]
 report=dict(suite='native-modal-cache-all-scenes',before_rom=b['rom_sha256'],after_rom=c['rom_sha256'],cases=len(c['results']),full_screen_pixels_compared=38400*len(c['results']),failures=failures,helper_sha256=sha(__file__),synthetic_setup=True)
 (a.output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2));assert not failures
if __name__=='__main__':main()
