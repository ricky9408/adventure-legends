#!/usr/bin/env python3
"""Read-only cold-Gear function profile on an exact ROM and supplied late SRAM.
Fixture-based diagnostic, never evidence of acquiring the collection. No ROM
patch, game-RAM writes or machine-state import. A cold normal-frame control
must match the complete serialized end state and frame observations.
"""
import argparse,ctypes as C,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_native import Native,sha
from profile_return_stalls import functions,Row
from mgba_runner import keymask
class ReadOnly(Native):
 def write(self,*a,**kw):raise AssertionError('Game-RAM writes forbidden')
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ('rom','symbols','bridge','save','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False);syms={v[2]:int(v[0],16) for line in a.symbols.read_text().splitlines() if len(v:=line.split())==3}
 names={'gear_menu_draw','equipment_preview','equipment_equip','equipment_derive','game_gear_apply','game_health_refresh','equipment_validate','equipment_refs_validate','equipment_reserved_validate','equipment_record_validate','derive_refs','number','stat','text','centered','rect','box','draw_world','render','render_static','game_gear_bonus_stats'}
 selected=[f for f in functions(a.rom.with_suffix('.elf')) if f['name'].split('.')[0] in names and (f['name'].split('.')[0] not in ('number','stat','derive_refs') or f['owner'] in ('gear_menu.c','equipment.c'))]
 assert len(selected)<64
 so=a.output/'observer.so';usr=ROOT/'tools/sysroot/usr';subprocess.run(['cc','-std=c11','-D_GNU_SOURCE','-O2','-fPIC','-shared',str(ROOT/'tests/legacy_mgba_profile.c'),'-I'+str(usr/'include'),'-L'+str(usr/'lib/x86_64-linux-gnu'),'-Wl,-rpath,'+str((usr/'lib/x86_64-linux-gnu').resolve()),'-lmgba','-o',str(so)],check=True)
 lib=C.CDLL(str(so));lib.legacy_profile_reset.argtypes=[C.POINTER(C.c_uint32),C.c_uint];lib.legacy_profile_frames.argtypes=[C.c_void_p,C.c_uint,C.c_uint];lib.legacy_profile_rows.restype=C.POINTER(Row)
 result={'scope':__doc__,'rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols),'elf_sha256':sha(a.rom.with_suffix('.elf')),'save_sha256':sha(a.save),'bridge_sha256':sha(a.bridge),'probes':selected,'game_ram_writes':0,'machine_state_imports':0};commands=[]
 for observe in (True,False):
  e=ReadOnly(a.rom,a.bridge);e.load_save(a.save);e.reset();e.frames(160);e.frames(2,'A');e.frames(3)
  g=lambda name:e.read(syms[name])
  for _ in range(1800):
   if g('game_state')==1 and g('frame') and not g('save_requested') and not g('save_feedback_background'):break
   e.frames(1)
  else:raise AssertionError('Cold Continue did not settle')
  e.frames(2,'START');e.frames(2);e.frames(2,'RIGHT');e.frames(2);assert g('journal_tab')==13
  if observe:lib.legacy_profile_reset((C.c_uint32*len(selected))(*[f['address'] for f in selected]),len(selected))
  rows=[]
  for keys in [1,1,0,0,128,128,0,0,1,1,0,0,0,0,0,0]:
   before=g('frame');page=e.read(0x04000000,2)&16
   if observe:lib.legacy_profile_frames(e.ptr,1,keys)
   else:e.frames(1,keys)
   rows.append({'frame':e.frame,'delta':(g('frame')-before)&0xffffffff,'flip':page!=(e.read(0x04000000,2)&16),'cycles':g('render_cycles'),'state':g('game_state'),'tab':g('journal_tab')})
  e.state(a.output/('observed.state' if observe else 'control.state'));result['observed' if observe else 'control']=rows;e.close()
  if observe:
   rs=lib.legacy_profile_rows();records=[{**{k:getattr(rs[i],k) for k,_ in Row._fields_},'name':selected[rs[i].probe]['name'],'owner':selected[rs[i].probe]['owner'],'cycles':rs[i].end-rs[i].begin} for i in range(lib.legacy_profile_count())];result.update(records=records,overflow=lib.legacy_profile_overflow(),reentered=lib.legacy_profile_reentered());result['summary']={f['name']:{'calls':sum(r['probe']==i for r in records),'max_cycles':max((r['cycles'] for r in records if r['probe']==i),default=0),'total_cycles':sum(r['cycles'] for r in records if r['probe']==i)} for i,f in enumerate(selected)}
 result['complete_state_equal']=(a.output/'observed.state').read_bytes()==(a.output/'control.state').read_bytes();result['trace_equal']=result['observed']==result['control'];(a.output/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('summary','complete_state_equal','trace_equal','overflow','reentered')},indent=2));assert result['complete_state_equal'] and result['trace_equal'] and not result['overflow'] and not result['reentered']
if __name__=='__main__':main()
