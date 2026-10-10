#!/usr/bin/env python3
"""Read-only immutable-F Magma boundary attribution.
Each observer/control run loads the authenticated producer's same-F SRAM/state
pair at hardware245, then replays only the report's post-import input suffix.
One explicit same-ROM state load per run; no ROM patch or game RAM writes.
"""
import argparse,ctypes as C,gzip,hashlib,json,shutil,struct,subprocess
from pathlib import Path
from profile_return_stalls import ReadOnly,Row,LoopRow,functions
from mgba_runner import keymask
ROOT=Path(__file__).resolve().parents[1];sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
ROM_SHA='20ca4ee45956e0112ecc1bb1731b6cb6386d06fe9785231dc2e47dc7a4d6538c';SRAM_SHA='d482466d04050c3d7f2e8eb8e1960729c9b9b33aa3e32440d186a4b54b854a69'
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,default=Path('/tmp/return-native-f-collect-legacy-repeats-01/return-journey.json'));p.add_argument('--start',type=int,required=True);p.add_argument('--end',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(exist_ok=False,parents=True);d=json.loads(a.report.read_text());src=Path(d['source_root']);rom=src/'build/emberbond.gba';sym=rom.with_suffix('.sym');elf=rom.with_suffix('.elf');seed=d['snapshots']['paired-producer-import'];fixture=Path(seed['sram_path']);state_path=Path(seed['state_path']);manifest=a.report.parent/'candidate-source-hashes.json';native=Path(d['global_native']['trace_path'])
 assert sha(rom)==ROM_SHA==d['rom_sha256'];assert sha(fixture)==SRAM_SHA==seed['sram_sha256'];assert sha(sym)==d['symbols_sha256'];assert sha(elf)==d['elf_sha256'];assert sha(manifest)==d['source_manifest_sha256'];assert all(sha(src/k)==v for k,v in json.loads(manifest.read_text()).items());assert all(sha(a.report.parent/'helper-source'/k)==v for k,v in d['helper_sources'].items());assert sha(a.report)=='48bf0648b16e6742b2eb6fa70d2063acf2dc291b0a233836d9235e24f0d11c46'
 original={}
 for line in gzip.open(native,'rt'):
  r=json.loads(line)
  if r['hardware_frame']<=a.end:original[r['hardware_frame']]={**r,'before':r['frame_before'],'after':r['frame_after'],'updates':r['update_delta'],'flip':r['page_flip'],'state':r['state_after'],'obj':r['obj_count']}
 assert sha(state_path)==seed['state_sha256'] and seed['rom_sha256']==ROM_SHA
 gap=next(i for i in range(1,len(d['inputs'])) if d['inputs'][i]['frame']<d['inputs'][i-1]['frame']);commands={};inputs=d['inputs'][gap:];origin=inputs[0]['frame'];assert origin==245
 for v in inputs:
  for f in range(v['frame'],min(v['frame']+v['frames'],a.end)):assert f not in commands;commands[f]=v['keys']
  if v['frame']>=a.end:break
 assert set(commands)==set(range(origin,a.end))
 syms={r[2]:int(r[0],16)for line in sym.read_text().splitlines()if len(r:=line.split())==3};funcs=functions(elf)
 names='magma_game_enter magma_visit magma_anchor magma_game_prepare_save magma_can_enter magma_quest_offer save5_validate_current save5_validate_revision event_step return_game_prepare_event return_job_step return_job_begin return_job_cancel return_job_result creatures_credit_event progression_refresh copy_south south_game_draw_overlay return_validate save5_preflight_step save5_validate update save_frame render render_static draw_world draw_actors obj_commit obj_upload obj_add copy_bg copy_return copy_region game_geometry_sync reuse_modal_bitmap quickparty_draw_journal draw_companion_journal progression_draw_tab gear_menu_draw draw_floating_hud draw_campaign_actors refresh_campaign_props region_game_draw_actors north_game_draw_actors south_game_draw_actors return_game_draw_actors return_game_draw_overlay return_game_draw_old_overlay enter_room creatures_begin_expedition spawn_enemies game_enemy_health_reset progression_save_begin progression_save_step save5_step save5_begin save_game save_at make_save return_game_reset game_attacks_reset return_legacy_reset game_health_fill camera_update event_frame game_draw_health quickparty_menu_input game_region_warp'.split();chosen=[f for name in names for f in funcs if f['name']==name]
 private={'game.c':('copy_world_row','clear','modal','world'),'magma_game.c':('sync','reset_scene','rest','cancel_anchor_prepare'),'return_game.c':('ring','old_notice','dynamic_rects','present','persist','bound_event','changed'),'quickparty.c':('card',),'creatures.c':('family_policy_for_id','revision_policy_for_id')};chosen += [f for f in funcs if f['owner']in private and f['name'].split('.')[0]in private[f['owner']]];assert len(chosen)<128
 cfile=ROOT/'tests/return_stall_observer.c';so=out/'observer.so';sysroot=ROOT/'tools/sysroot/usr';subprocess.run(['cc','-std=c11','-D_GNU_SOURCE','-O2','-fPIC','-shared',str(cfile),'-I'+str(sysroot/'include'),'-L'+str(sysroot/'lib/x86_64-linux-gnu'),'-Wl,-rpath,'+str((sysroot/'lib/x86_64-linux-gnu').resolve()),'-lmgba','-o',str(so)],check=True)
 l=C.CDLL(str(so));ptr=C.POINTER(C.c_uint32);l.return_profile_reset.argtypes=[ptr,C.c_uint,ptr,ptr,C.c_uint];l.return_profile_frames.argtypes=[C.c_void_p,C.c_uint,C.c_uint];l.return_loop_config.argtypes=[C.c_uint32,C.c_uint32];l.return_loops.restype=C.POINTER(LoopRow);l.return_loop_cycles.restype=C.POINTER(C.c_uint64);l.return_state_save.argtypes=[C.c_void_p,C.c_char_p];l.return_profile_rows.restype=C.POINTER(Row);arr=lambda v:(C.c_uint32*len(v))(*v)
 def snapshot(e,old,page,state):
  g=lambda n:e.read(syms[n]);row=dict(hardware_frame=e.frame,before=old,after=g('frame'),updates=(g('frame')-old)&0xffffffff,flip=(e.read(0x04000000,2)&16)!=page,cycles=g('render_cycles'),state_before=state,state=g('game_state'),room=g('room'),obj=g('obj_count'))
  row['detail']={n:g(n)for n in ['journal_tab','page','px','py','camera_x','camera_y','save_resume_state','save_completion_pending','save_begin_pending','save_requested','region_cache_room','gfx_props_room']if n in syms};row['detail']['cache_valid']=[e.read(syms['cache_valid']+i*4)for i in range(2)];row['detail']['cache_fields']=[[e.read(syms['cache_fields']+(i*34+j)*4)for j in range(34)]for i in range(2)];return row
 result={'scope':__doc__,'rom_sha256':sha(rom),'symbols_sha256':sha(sym),'elf_sha256':sha(elf),'fixture_sha256':sha(fixture),'source_manifest_sha256':sha(manifest),'source_report':str(a.report.resolve()),'source_report_sha256':sha(a.report),'native_trace_sha256':sha(native),'source_provenance':d['provenance'],'profile_start':a.start,'profile_end':a.end,'inputs':inputs,'replay_origin_hardware_frame':origin,'loaded_state_sha256':sha(state_path),'game_ram_writes':0,'machine_state_loads':1,'same_ROM_pair':seed,'reset_count_per_run':0,'extra_warmup_frames':0,'probes':chosen,'functions':funcs}
 for observe in (True,False):
  trace=[]
  with ReadOnly(rom)as e:
   e.load_save(fixture);e.state(state_path,True)
   # Use the recorded batched input prefix, including its initial150 frames.
   for v in inputs:
    if v['frame']>=a.start:break
    assert e.frame==v['frame'];e.frames(min(v['frames'],a.start-v['frame']),v['keys'])
   assert e.frame==a.start
   if observe:l.return_profile_reset(arr([f['address']for f in chosen]),len(chosen),arr([f['address']for f in funcs]),arr([f['end']for f in funcs]),len(funcs));l.return_loop_config(syms['update'],syms['render'])
   for frame in range(a.start,a.end):
    old=e.read(syms['frame']);page=e.read(0x04000000,2)&16;state=e.read(syms['game_state'])
    if observe:l.return_profile_frames(e.ptr,1,keymask(commands[frame]))
    else:e.frames(1,commands[frame])
    trace.append(snapshot(e,old,page,state))
   path=out/('profile-end.state'if observe else 'control-end.state');assert l.return_state_save(e.ptr,str(path).encode())
  result['trace'if observe else 'control_trace']=trace
  if observe:
   rs=l.return_profile_rows();result['records']=[{**{k:getattr(rs[i],k)for k,_ in Row._fields_},'name':chosen[rs[i].probe]['name'],'owner':chosen[rs[i].probe]['owner'],'cycles':rs[i].end-rs[i].begin}for i in range(l.return_profile_count())];result['overflow']=l.return_profile_overflow();result['reentered']=l.return_profile_reentered();result['update_to_render_loops']=[];ls=l.return_loops()
   for i in range(l.return_loop_count()):
    if not ls[i].end:continue
    cs=l.return_loop_cycles(i);item={k:getattr(ls[i],k)for k,_ in LoopRow._fields_};item['cycles']=item['end']-item['begin'];item['functions']=[dict(index=j,cycles=cs[j])for j in range(len(funcs)+1)if cs[j]];assert item['cycles']==sum(r['cycles']for r in item['functions']);result['update_to_render_loops'].append(item)
 compare=('before','after','updates','flip','cycles','state_before','state','room','obj');result['original_cadence_mismatches']=[dict(hardware_frame=r['hardware_frame'],field=k,actual=r[k],expected=original[r['hardware_frame']][k])for r in result['control_trace']for k in compare if r[k]!=original[r['hardware_frame']][k]];result['control_trace_equal']=result['trace']==result['control_trace'];result['complete_emulator_state_equal']=(out/'profile-end.state').read_bytes()==(out/'control-end.state').read_bytes();result['profile_end_sha256']=sha(out/'profile-end.state');result['control_end_sha256']=sha(out/'control-end.state')
 own=[Path(__file__),ROOT/'tests/profile_return_stalls.py',cfile,ROOT/'tools/mgba_runner.py',ROOT/'tools/mgba_bridge.c',ROOT/'tools/mgba_bridge.so'];result['observer_sources']={str(f.relative_to(ROOT)):sha(f)for f in own}
 for f in own:dest=out/'observer-source'/f.relative_to(ROOT);dest.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(f,dest)
 (out/'profile-report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ['complete_emulator_state_equal','control_trace_equal','original_cadence_mismatches','overflow','reentered']},indent=2));assert result['complete_emulator_state_equal']and result['control_trace_equal']and not result['original_cadence_mismatches']and not result['overflow']and not result['reentered']
if __name__=='__main__':main()
