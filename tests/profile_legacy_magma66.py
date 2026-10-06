#!/usr/bin/env python3
"""Read-only exact-ROM mGBA PC/timing profile of an earned Magma66 cast.

No ROM patch, game-memory write or production recompilation. Function entry
and return observations use the existing mGBA session and its emulated clock.
The measured input sequence is replayed by normal runFrame and its complete
serialized emulator state must exactly match the single-stepped profile.
"""
import argparse,ctypes as C,hashlib,json,struct,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--workspace',required=True,type=Path);p.add_argument('--output',required=True,type=Path)
a=p.parse_args();workspace=a.workspace.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(workspace/'tests'));sys.path.insert(0,str(workspace/'tools'))
from magma_combat_tests import MagmaCombat,digest
from mgba_runner import Emulator,keymask
rom=workspace/'build/emberbond.gba';sym=rom.with_suffix('.sym');elf=rom.with_suffix('.elf')
source=workspace/'build/magma-journey/magma-journey.json';manifest=workspace/'build/source-hashes.json'
r=MagmaCombat(rom,sym,out,digest(rom),digest(sym),source,'09-all65-earned-town',manifest,None)
so=out/'observer.so';sysroot=workspace/'tools/sysroot/usr'
subprocess.run(['cc','-std=c11','-D_GNU_SOURCE','-O2','-fPIC','-shared',str(HERE/'legacy_mgba_profile.c'),'-I'+str(sysroot/'include'),'-L'+str(sysroot/'lib/x86_64-linux-gnu'),'-Wl,-rpath,'+str((sysroot/'lib/x86_64-linux-gnu').resolve()),'-lmgba','-o',str(so)],check=True)
l=C.CDLL(str(so))
class Row(C.Structure):
 _fields_=[('begin',C.c_uint64),('end',C.c_uint64)]+[(k,C.c_uint32) for k in ('probe','entry_frame','exit_frame','entry_pc','return_pc')]
l.legacy_profile_reset.argtypes=[C.POINTER(C.c_uint32),C.c_uint]
l.legacy_profile_frames.argtypes=[C.c_void_p,C.c_uint,C.c_uint]
l.legacy_profile_rows.restype=C.POINTER(Row)
probes=['update','save_frame','game_geometry_sync','render','render_static','draw_world','draw_actors','obj_commit','draw_floating_hud','draw_campaign_actors','refresh_campaign_props','magma_game_draw_overlay','magma_game_draw_actors','magma_powers_tick','magma_powers_draw','solid','magma_game_solid','magma_game_geometry_solid','obj_add','obj_upload']
addresses=[r.sym[name] for name in probes]
# Resolve private function identities by exact STT_FILE ownership, never an
# ambiguous flat nm spelling. The constructor already authenticated ELF/ROM.
raw=elf.read_bytes();h=struct.unpack_from('<16sHHIIIIIHHHHHH',raw)
sections=[struct.unpack_from('<IIIIIIIIII',raw,h[6]+i*h[11]) for i in range(h[12])]
for section in sections:
 if section[1]!=2:continue
 strings=sections[section[6]];strings=raw[strings[4]:strings[4]+strings[5]];owner=None
 for pos in range(section[4],section[4]+section[5],section[9]):
  ni,value,size,info,other,index=struct.unpack_from('<IIIBBH',raw,pos);name=strings[ni:].split(b'\0',1)[0].decode()
  if info&15==4:owner=name
  if owner=='magma_powers.c' and info&15==2 and name.split('.')[0] in ('geometry','clear','refresh_one','draw_path','path_set','line','draw_at','refresh'):
   assert index and size;probes.append(owner+':'+name);addresses.append(value&~1)
assert len(set(a&~1 for a in addresses))==len(addresses)

result={'scope':'Read-only exact-ROM emulator-side function-entry/return cycle profile; no production instrumentation','rom_sha256':digest(rom),'elf_sha256':digest(elf),'symbols_sha256':digest(sym),'source_manifest_sha256':digest(manifest),'producer_report_sha256':digest(source),'observer_sha256':{str(HERE/f):digest(HERE/f) for f in ('profile_legacy_magma66.py','legacy_mgba_profile.c')},'probes':dict(zip(probes,addresses))}
try:
 r.boot();r.prepare(66,False);r.align(240,220,1);r.ready();r.current_case='profile-lifetime-66'
 start=out/'profile-start.state';save=out/'profile-start.sav';r.e.state(start);save.write_bytes(r.e.bytes(0x0e000000,32768));r.e.load_save(save);r.e.state(start,True);first=len(r.inputs)
 r.e.frames=lambda n,keys=0:l.legacy_profile_frames(r.e.ptr,n,keymask(keys))
 l.legacy_profile_reset((C.c_uint32*len(addresses))(*addresses),len(addresses))
 try:r.cast(66)
 except Exception as exc:result['strict_cast_error']=str(exc)
 finally:
  count=l.legacy_profile_count();rows=l.legacy_profile_rows();records=[{k:getattr(rows[i],k) for k,_ in Row._fields_} for i in range(count)]
  for row in records:row['name']=probes[row['probe']];row['cycles']=row['end']-row['begin']
  result.update(records=records,record_count=count,overflow=l.legacy_profile_overflow(),reentered=l.legacy_profile_reentered(),input_sequence=r.inputs[first:],frame_windows=r.frame_windows)
  finish=out/'profile-end.state';r.e.state(finish)
  with Emulator(rom) as baseline:
   baseline.load_save(save);baseline.state(start,True)
   for command in result['input_sequence']:baseline.frames(command['frames'],command['keys'])
   baseline_end=out/'baseline-end.state';baseline.state(baseline_end)
  left,right=finish.read_bytes(),baseline_end.read_bytes();result['complete_emulator_state_equal']=left==right;result['state_diff_bytes']=sum(x!=y for x,y in zip(left,right));result['profile_end_sha256']=digest(finish);result['baseline_end_sha256']=digest(baseline_end)
  result['function_summary']={name:{'calls':sum(x['name']==name for x in records),'cycles':sum(x['cycles'] for x in records if x['name']==name),'max_cycles':max((x['cycles'] for x in records if x['name']==name),default=0)} for name in probes}
  (out/'profile-report.json').write_text(json.dumps(result,indent=2)+'\n')
  print(json.dumps({k:v for k,v in result.items() if k not in ('records','frame_windows','input_sequence')},indent=2))
  assert result['complete_emulator_state_equal'],'Profiler changed observable emulated execution; diagnostic invalid'
  assert not result['overflow'] and not result['reentered'],'Profiler lost records or encountered unhandled recursion'
finally:r.report();r.e.close()
