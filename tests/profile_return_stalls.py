#!/usr/bin/env python3
"""Reproduce authenticated Return controller input; profile unchanged ROM read-only.
No performance acceptance is inferred from profiling alone. The normal runFrame
control must match every hardware-frame row and complete serialized end state.
"""
import argparse,ctypes as C,hashlib,json,shutil,struct,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator,keymask
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ROM_SHA='5eb5e511b978d198e089ff559f9e742b6b7a81973d38de801ef3c433f0687fc0'
SYM_SHA='f5e600d5ade1255ee1408b01c670b2f708d1cd88782dd6cad3100e440e983d3f'
ELF_SHA='16477fe100f219867863a1066d35e5b78933c21f3d1aaa9047ffb2b35ba59aa2'
class ReadOnly(Emulator):
 def __init__(self,*a):super().__init__(*a);self.lib.eb_write=self.write
 def write(self,*a,**k):raise AssertionError('Game RAM writes forbidden')
class Row(C.Structure):
 _fields_=[('begin',C.c_uint64),('end',C.c_uint64)]+[(k,C.c_uint32) for k in ('probe','entry_frame','exit_frame','entry_pc','return_pc')]
class LoopRow(C.Structure):
 _fields_=[('begin',C.c_uint64),('end',C.c_uint64),('entry_frame',C.c_uint32),('exit_frame',C.c_uint32)]
def functions(elf):
 raw=elf.read_bytes();h=struct.unpack_from('<16sHHIIIIIHHHHHH',raw);sections=[struct.unpack_from('<IIIIIIIIII',raw,h[6]+i*h[11]) for i in range(h[12])];result=[]
 for section in sections:
  if section[1]!=2:continue
  strings=sections[section[6]];strings=raw[strings[4]:strings[4]+strings[5]];owner=''
  for pos in range(section[4],section[4]+section[5],section[9]):
   ni,value,size,info,other,index=struct.unpack_from('<IIIBBH',raw,pos);name=strings[ni:].split(b'\0',1)[0].decode()
   if info&15==4:owner=name
   if info&15==2 and index and size:result.append(dict(name=name,owner=owner if info>>4==0 else '',address=value&~1,end=(value&~1)+size,size=size))
 return sorted(result,key=lambda r:r['address'])
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);p.add_argument('--start',type=int,required=True);p.add_argument('--end',type=int,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--seed-report',type=Path);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);d=json.loads(a.report.read_text());src=Path(d['source_root']);rom=src/'build/emberbond.gba';sym=rom.with_suffix('.sym');elf=rom.with_suffix('.elf');fixture=Path(d['provenance']['fixture_path'])
 for path,expected in [(rom,ROM_SHA),(sym,SYM_SHA),(elf,ELF_SHA),(fixture,d['provenance']['sram_sha256'])]:assert sha(path)==expected,(path,sha(path))
 manifest=a.report.parent/'candidate-source-hashes.json';assert sha(manifest)==d['source_manifest_sha256'];assert all(sha(src/k)==v for k,v in json.loads(manifest.read_text()).items())
 for k,v in d['helper_sources'].items():assert sha(a.report.parent/'helper-source'/k)==v,('helper',k)
 # Original report's inputs are authoritative; do not rerun changed route code.
 commands={}
 for v in d['inputs']:
  for f in range(v['frame'],min(a.end,v['frame']+v['frames'])):assert f not in commands;commands[f]=v['keys']
  if v['frame']+v['frames']>=a.end:break
 assert set(range(a.end))<=commands.keys()
 syms={r[2]:int(r[0],16) for line in sym.read_text().splitlines() if len(r:=line.split())==3};funcs=functions(elf)
 probes='solid return_game_solid return_game_supercover northern_power northern_powers_field_geometry northern_powers_draw southern_power southern_powers_field_geometry southern_powers_draw update save_frame render render_static draw_world draw_actors draw_floating_hud obj_commit game_geometry_sync reuse_modal_bitmap copy_underwater copy_return underwater_game_draw_overlay return_game_draw_old_overlay return_game_draw_overlay return_game_draw_actors return_game_field_target return_game_field_hit return_legacy_field return_legacy_tick return_legacy_draw return_legacy_begin ability_apply progression_command creature_current_policy quickparty_draw_journal progression_draw_tab gear_menu_draw region_game_draw_journal north_game_draw_journal south_game_draw_journal magma_game_draw_journal underwater_game_draw_journal return_game_draw_journal advanced_tick regional_powers_tick northern_powers_tick southern_powers_tick magma_powers_tick underwater_powers_tick return_powers_tick return_game_tick return_game_geometry_changed return_game_geometry_solid event_frame game_combat_tick update_enemies update_shots obj_upload obj_add game_draw_health game_draw_weapon game_draw_enemy_phase'.split()
 chosen=[f for name in probes for f in funcs if f['name']==name]
 private={'return_legacy_powers.c':('snapshot','field_pass','geometry','clear','current','bounds'),'return_game.c':('span','dynamic_solid','dynamic_rects','changed','geometry','tick','queue_event','finish','ring','old_notice'),'northern_powers.c':('clear_segment','origin_clear','field_line','draw_line'),'southern_powers.c':('clear','origin_clear','field_line','draw_line','particle','field_piece','draw_checked','active','wood_tick','wedge_tick'),'creatures.c':('form_policy_for_id','family_policy_for_id','revision_policy_for_id')}
 chosen += [f for f in funcs if f['owner'] in private and f['name'].split('.')[0] in private[f['owner']]]
 assert len(chosen)<=128
 observer=out/'observer.so';sysroot=ROOT/'tools/sysroot/usr';cfile=ROOT/'tests/return_stall_observer.c'
 subprocess.run(['cc','-std=c11','-D_GNU_SOURCE','-O2','-fPIC','-shared',str(cfile),'-I'+str(sysroot/'include'),'-L'+str(sysroot/'lib/x86_64-linux-gnu'),'-Wl,-rpath,'+str((sysroot/'lib/x86_64-linux-gnu').resolve()),'-lmgba','-o',str(observer)],check=True)
 for f in [Path(__file__),cfile,ROOT/'tools/mgba_runner.py',ROOT/'tools/mgba_bridge.c',ROOT/'tools/mgba_bridge.so']:
  dest=out/'observer-source'/f.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest)
 l=C.CDLL(str(observer));ptr=C.POINTER(C.c_uint32);l.return_profile_reset.argtypes=[ptr,C.c_uint,ptr,ptr,C.c_uint];l.return_profile_frames.argtypes=[C.c_void_p,C.c_uint,C.c_uint];l.return_loop_config.argtypes=[C.c_uint32,C.c_uint32];l.return_loops.restype=C.POINTER(LoopRow);l.return_loop_cycles.restype=C.POINTER(C.c_uint64);l.return_state_save.argtypes=[C.c_void_p,C.c_char_p];l.return_profile_rows.restype=C.POINTER(Row);l.return_hist_cycles.restype=C.POINTER(C.c_uint64);l.return_hist_instructions.restype=C.POINTER(C.c_uint64)
 arr=lambda vals:(C.c_uint32*len(vals))(*vals)
 def row(e,old,page):
  g=lambda n:e.read(syms[n]);return dict(hardware_frame=e.frame,update_delta=(g('frame')-old)&0xffffffff,page_flip=(e.read(0x04000000,2)&16)!=page,cycles=g('render_cycles'),state=g('game_state'),room=g('room'),journal_tab=g('journal_tab'),obj_count=g('obj_count'),px=g('px'),py=g('py'),toast_id=g('toast_id'),toast_ticks=g('toast_ticks'))
 result=dict(scope='Read-only exact-ROM emulator-side instruction cycles and function-entry/return; unchanged ROM; normal runFrame paired control',rom_sha256=sha(rom),symbols_sha256=sha(sym),elf_sha256=sha(elf),source_manifest_sha256=sha(manifest),source_report=str(a.report.resolve()),source_report_sha256=sha(a.report),fixture_sha256=sha(fixture),game_ram_writes=0,serialization_note='mCore.saveState receives zero-initialized host output buffer so reserved bytes cannot contain uninitialized malloc data; no emulated state is modified',cold_boot_replay=True,profile_start=a.start,profile_end=a.end,probes=chosen,functions=funcs,observer_sources={str(f.relative_to(out)):sha(f) for f in (out/'observer-source').rglob('*') if f.is_file()},inputs=[dict(frame=f,keys=commands[f]) for f in range(a.start,a.end)])
 with ReadOnly(rom) as e:
  start=out/'start.state';save=out/'start.sav'
  if a.seed_report:
   seed=json.loads(a.seed_report.read_text());assert seed['rom_sha256']==ROM_SHA and seed['source_report_sha256']==sha(a.report) and seed['profile_start']<=a.start and seed['game_ram_writes']==0
   for name,dest,key in [('start.state',start,'start_state_sha256'),('start.sav',save,'start_sram_sha256')]:
    path=a.seed_report.parent/name;assert sha(path)==seed[key];shutil.copyfile(path,dest)
   result.update(cold_boot_replay=False,same_ROM_seed_report=str(a.seed_report.resolve()),same_ROM_seed_report_sha256=sha(a.seed_report),seed_start=seed['profile_start'])
   if seed['profile_start']<a.start:
    e.load_save(save);e.state(start,True)
    for command in d['inputs']:
     lo=max(command['frame'],seed['profile_start']);hi=min(command['frame']+command['frames'],a.start)
     if lo>=hi:continue
     assert e.frame==lo;e.frames(hi-lo,command['keys'])
     if hi==a.start:break
    assert e.frame==a.start;assert l.return_state_save(e.ptr,str(start).encode());save.write_bytes(e.bytes(0x0e000000,32768))
  else:
   e.load_save(fixture);e.reset()
   # Replay original batched calls exactly before the observation window.
   for command in d['inputs']:
    if command['frame']>=a.start:break
    assert e.frame==command['frame'];e.frames(min(command['frames'],a.start-e.frame),command['keys'])
   assert e.frame==a.start
   assert l.return_state_save(e.ptr,str(start).encode());save.write_bytes(e.bytes(0x0e000000,32768))
  e.close();e=ReadOnly(rom);e.load_save(save);e.state(start,True)
  l.return_profile_reset(arr([f['address'] for f in chosen]),len(chosen),arr([f['address'] for f in funcs]),arr([f['end'] for f in funcs]),len(funcs))
  l.return_loop_config(syms['update'],syms['render'])
  trace=[];hist=[]
  for f in range(a.start,a.end):
   assert e.frame==f;old=e.read(syms['frame']);page=e.read(0x04000000,2)&16;l.return_hist_reset();l.return_profile_frames(e.ptr,1,keymask(commands[f]));trace.append(row(e,old,page));cs=l.return_hist_cycles();ins=l.return_hist_instructions();hist.append(dict(hardware_frame=e.frame,functions=[dict(index=i,cycles=cs[i],instructions=ins[i]) for i in range(len(funcs)+1) if cs[i]]))
  end=out/'profile-end.state';assert l.return_state_save(e.ptr,str(end).encode());records=l.return_profile_rows();result['records']=[{**{k:getattr(records[i],k) for k,_ in Row._fields_},'name':chosen[records[i].probe]['name'],'owner':chosen[records[i].probe]['owner'],'cycles':records[i].end-records[i].begin} for i in range(l.return_profile_count())];result.update(trace=trace,instruction_histograms=hist,overflow=l.return_profile_overflow(),reentered=l.return_profile_reentered())
  result['update_to_render_loops']=[];ls=l.return_loops()
  for i in range(l.return_loop_count()):
   if not ls[i].end:continue
   cs=l.return_loop_cycles(i);parts=[dict(index=j,cycles=cs[j]) for j in range(len(funcs)+1) if cs[j]];item={**{k:getattr(ls[i],k) for k,_ in LoopRow._fields_},'functions':parts};item['cycles']=item['end']-item['begin'];item['attributed_cycles']=sum(v['cycles'] for v in parts);assert item['cycles']==item['attributed_cycles'];result['update_to_render_loops'].append(item)
  e.close()
 with ReadOnly(rom) as control:
  control.load_save(save);control.state(start,True);rows=[]
  for f in range(a.start,a.end):
   old=control.read(syms['frame']);page=control.read(0x04000000,2)&16;control.frames(1,commands[f]);rows.append(row(control,old,page))
  control_end=out/'control-end.state';assert l.return_state_save(control.ptr,str(control_end).encode())
 result.update(control_trace=rows,control_trace_equal=rows==trace,complete_emulator_state_equal=end.read_bytes()==control_end.read_bytes(),profile_end_sha256=sha(end),control_end_sha256=sha(control_end),start_state_sha256=sha(start),start_sram_sha256=sha(save))
 # Original observed cadence fields must reproduce, including earlier failures.
 original={r['hardware_frame']:r for w in d['frame_windows'] for r in w['trace']};compare=('update_delta','page_flip','cycles','room','toast_id','toast_ticks','obj_count');mismatches=[dict(frame=r['hardware_frame'],field=k,expected=original[r['hardware_frame']][k],actual=r[k]) for r in rows if r['hardware_frame'] in original for k in compare if r[k]!=original[r['hardware_frame']][k]]
 result['original_cadence_mismatches']=mismatches;(out/'profile-report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('complete_emulator_state_equal','control_trace_equal','original_cadence_mismatches','overflow','reentered')},indent=2),flush=True);print('STALLS',json.dumps([r for r in rows if r['update_delta']!=1 or not r['page_flip'] or r['cycles']>=280896]),flush=True)
 assert result['complete_emulator_state_equal'] and result['control_trace_equal'] and not mismatches and not result['overflow'] and not result['reentered']
if __name__=='__main__':main()
