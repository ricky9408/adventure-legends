#!/usr/bin/env python3
"""Controller-only new-adventure safety; no game RAM writes or machine states."""
import argparse,hashlib,json,sys,zlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
FIXTURE=ROOT/'tests/fixtures/v5-revision2/all-eleven-town.sav'
FIXTURE_SHA='74f39c496a1e93eb47c5b50828513033899be0567a1391cf99869750defa9106'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def bank(raw):
 rows=[]
 for off in (0x200,0x1a00):
  b=raw[off:off+6144];v=bytearray(b);v[16:21]=bytes(5)
  if b[:4]==b'EB\x05\x20' and b[20]==0xa5 and zlib.crc32(v)&0xffffffff==int.from_bytes(b[16:20],'little'):rows.append(b)
 assert rows
 result=rows[0]
 for b in rows[1:]:
  d=(int.from_bytes(b[8:12],'little')-int.from_bytes(result[8:12],'little'))&0xffffffff
  if 0<d<0x80000000:result=b
 return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','symbols','output'):p.add_argument('--'+name,required=True,type=Path)
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True)
 assert sha(FIXTURE)==FIXTURE_SHA
 symbols={}
 for line in a.symbols.read_text().splitlines():
  v=line.split()
  if len(v)==3:symbols[v[2]]=int(v[0],16)
 checks=[];metrics={}
 def check(label,result):
  checks.append({'check':label,'passed':bool(result)})
  assert result,label
 def read(e,n):return e.read(symbols[n])
 def raw(e):return e.bytes(0x0e000000,32768)
 def boot(saved=True):
  e=Emulator(a.rom)
  if saved:e.load_save(FIXTURE);e.reset()
  e.frames(150);check('title boot',read(e,'game_state')==0)
  check('save availability',read(e,'has_save')==int(saved));return e
 for cancel in ('B','START','SELECT','A+B'):
  with boot() as e:
   before=raw(e);e.tap('SELECT',2,4)
   check(cancel+': confirmation opens',read(e,'game_state')==9)
   e.frames(80);check(cancel+': unconfirmed wait preserves every SRAM byte',raw(e)==before)
   e.tap(cancel,2,8)
   check(cancel+': cancel wins and returns to title',read(e,'game_state')==0)
   check(cancel+': cancellation preserves every SRAM byte',raw(e)==before)
   e.tap('START',2,140)
   current=bank(raw(e));check(cancel+': Continue preserves eleven-form history',current[112:128]==bank(before)[112:128])
 with boot() as e:
  before=raw(e);start=read(e,'frame');page=read(e,'page');flips=0;peak=0
  for i in range(80):
   e.frames(1,'SELECT' if i<2 else 0);n=read(e,'page');flips+=n!=page;page=n;peak=max(peak,read(e,'render_cycles'))
  metrics['cold_entry']={'window_frames':80,'updates':(read(e,'frame')-start)&0xffffffff,'page_flips':flips,'peak_cycles':peak}
  check('cold confirmation entry updates and presents every hardware frame',metrics['cold_entry']['updates']==80 and flips==80)
  check('cold confirmation entry preserves SRAM',raw(e)==before)
 with boot() as e:
  before=raw(e);e.frames(3,'A');e.frames(3,'A+SELECT');e.frames(100,'A')
  check('held A cannot confirm a newly opened prompt',read(e,'game_state')==9 and raw(e)==before)
  e.frames(3);e.screenshot(a.output/'native-new-game-confirmation.png')
  start=read(e,'frame');page=read(e,'page');flips=0;peak=0
  for _ in range(80):
   e.frames(1);n=read(e,'page');flips+=n!=page;page=n;peak=max(peak,read(e,'render_cycles'))
  metrics['steady']={'window_frames':80,'updates':(read(e,'frame')-start)&0xffffffff,'page_flips':flips,'peak_cycles':peak}
  check('confirmation keeps hardware update and presentation cadence',metrics['steady']['updates']==80 and flips==80)
  check('confirmation contains no world OAM sprites',all(e.read(0x07000000+i*8,2)&0x300==0x200 for i in range(128)))
  e.tap('A',2,160);after=raw(e);new=bank(after)
  check('fresh A explicitly starts new adventure',read(e,'game_state')==2 and after!=before)
  check('confirmed replacement has only opening companions',[new[160+i*24] for i in range(160) if new[161+i*24]&1]==[1,4])
  check('new adventure has no inherited quest rewards',not any(new[4032:4296]))
  check('new adventure transaction leaves old-format SRAM untouched',after[:512]==before[:512])
  check('confirmed save completed successfully',not read(e,'save_failed'))
  (a.output/'confirmed-new-adventure.sav').write_bytes(after)
 with Emulator(a.rom) as e:
  e.load_save(a.output/'confirmed-new-adventure.sav');e.reset();e.frames(150)
  check('confirmed new save independently recognized',read(e,'has_save')==1)
  e.tap('START',2,160);b=bank(raw(e))
  check('confirmed new adventure independently continues',[b[160+i*24] for i in range(160) if b[161+i*24]&1]==[1,4] and read(e,'room')==0)
 with boot() as e:
  before=raw(e);e.tap('SELECT+START',2,140)
  check('Continue takes priority over simultaneous new-game input',read(e,'game_state')!=9 and bank(raw(e))[112:128]==bank(before)[112:128])
 for start_key in ('START','SELECT'):
  with boot(False) as e:
   e.tap(start_key,2,160)
   check('empty cartridge '+start_key+' opens adventure directly',read(e,'game_state')==2 and not read(e,'save_failed'))
 report={'suite':'new-game-confirmation-native','rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols),'test_sha256':sha(__file__),'fixture_sha256':FIXTURE_SHA,'controller_only':True,'game_ram_writes':0,'machine_states_loaded':0,'checks':checks,'failures':[],'cadence':metrics}
 (a.output/'new-game-confirmation.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'checks':len(checks),'failures':0,'cadence':metrics}))
if __name__=='__main__':main()
