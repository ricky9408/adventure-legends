#!/usr/bin/env python3
"""Read-only Covenants CPU profiling from exact native report inputs and cold SRAM.
Paired ordinary runFrame control must match the original per-frame cadence and
instrumented complete terminal state. No game RAM writes or machine-state loads.
"""
import argparse,ctypes as C,gzip,hashlib,json,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
KEYS={'A':1,'B':2,'SELECT':4,'START':8,'RIGHT':16,'LEFT':32,'UP':64,'DOWN':128,'R':256,'L':512,'NONE':0}
def keymask(keys):
 if isinstance(keys,int):return keys
 return sum(KEYS[k.upper()] for k in keys.replace('|','+').split('+'))
class ReadOnly:
 def __init__(self,rom,bridge):
  self.lib=C.CDLL(str(bridge))
  for n,args,ret in [('eb_open',[C.c_char_p],C.c_void_p),('eb_close',[C.c_void_p],None),('eb_frames',[C.c_void_p,C.c_uint,C.c_uint],None),('eb_read',[C.c_void_p,C.c_uint32,C.c_uint],C.c_uint32),('eb_framecounter',[C.c_void_p],C.c_uint),('eb_reset',[C.c_void_p],None),('eb_load_save',[C.c_void_p,C.c_char_p],C.c_int),('eb_rgb',[C.c_void_p,C.c_void_p],None),('eb_save',[C.c_void_p,C.c_char_p],C.c_int)]:
   f=getattr(self.lib,n);f.argtypes=args;f.restype=ret
  assert not hasattr(self.lib,'eb_write') and not hasattr(self.lib,'eb_state')
  self.ptr=self.lib.eb_open(str(rom.resolve()).encode());assert self.ptr
 def __enter__(self):return self
 def __exit__(self,*args):self.lib.eb_close(self.ptr)
 @property
 def frame(self):return self.lib.eb_framecounter(self.ptr)
 def frames(self,n,keys=0):self.lib.eb_frames(self.ptr,n,keymask(keys))
 def read(self,address,width=4):return self.lib.eb_read(self.ptr,address,width)
 def reset(self):self.lib.eb_reset(self.ptr)
 def load_save(self,p):assert self.lib.eb_load_save(self.ptr,str(p).encode())
 def pixels(self):
  p=(C.c_uint8*(240*160*3))();self.lib.eb_rgb(self.ptr,p);return bytes(p)
class Row(C.Structure):
 _fields_=[('begin',C.c_uint64),('end',C.c_uint64)]+[(k,C.c_uint32)for k in ('probe','entry_frame','exit_frame','entry_pc','return_pc')]
class LoopRow(C.Structure):
 _fields_=[('begin',C.c_uint64),('end',C.c_uint64),('entry_frame',C.c_uint32),('exit_frame',C.c_uint32)]
def functions(elf):
 raw=elf.read_bytes();h=struct.unpack_from('<16sHHIIIIIHHHHHH',raw);sections=[struct.unpack_from('<IIIIIIIIII',raw,h[6]+i*h[11])for i in range(h[12])];result=[]
 for section in sections:
  if section[1]!=2:continue
  strings=sections[section[6]];strings=raw[strings[4]:strings[4]+strings[5]];owner=''
  for pos in range(section[4],section[4]+section[5],section[9]):
   ni,value,size,info,other,index=struct.unpack_from('<IIIBBH',raw,pos);name=strings[ni:].split(b'\0',1)[0].decode()
   if info&15==4:owner=name
   if info&15==2 and index and size:result.append(dict(name=name,owner=owner if info>>4==0 else '',address=value&~1,end=(value&~1)+size,size=size))
 return sorted(result,key=lambda r:r['address'])
def scoped_objects(elf):
 raw=elf.read_bytes();h=struct.unpack_from('<16sHHIIIIIHHHHHH',raw);sections=[struct.unpack_from('<IIIIIIIIII',raw,h[6]+i*h[11])for i in range(h[12])];result={}
 for section in sections:
  if section[1]!=2:continue
  strings=sections[section[6]];strings=raw[strings[4]:strings[4]+strings[5]];owner=''
  for pos in range(section[4],section[4]+section[5],section[9]):
   ni,value,size,info,other,index=struct.unpack_from('<IIIBBH',raw,pos);name=strings[ni:].split(b'\0',1)[0].decode()
   if info&15==4:owner=name
   if info&15==1 and info>>4==0 and owner=='covenants_powers.c':result[name]=(value,size)
 assert result['cast'][1]==240 and result['collision'][1]==396
 return result
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--report',type=Path,required=True);p.add_argument('--start',type=int,required=True);p.add_argument('--end',type=int,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--candidate',type=Path,help='Explicit isolated experiment candidate, compared with native original');p.add_argument('--source-root',type=Path);p.add_argument('--original-source-root',type=Path,help='Frozen original runtime closure when relocating the diagnostic');p.add_argument('--sysroot',type=Path,default=ROOT/'tools/sysroot/usr');a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);report=a.report.resolve();d=json.loads(report.read_text());base=report.parent;src=a.original_source_root.resolve()if a.original_source_root else Path(d['source_root']);manifest=base/'candidate-source-hashes.json';fixture=Path(d['provenance']['fixture_path']);earned=Path(d['provenance']['earned_report']);native=base/'native-global.jsonl.gz';bridge=base/'helper-source/tools/horizons_mgba_bridge.so';mgba=base/'helper-source/tools/emulator-libs/libmgba.so.0.10'
 for ext,key in [('gba','rom'),('sym','symbols'),('elf','elf')]:assert sha(base/('tested.'+ext))==d[key+'_sha256']
 assert sha(manifest)==d['source_manifest_sha256'];assert all(sha(src/k)==v for k,v in json.loads(manifest.read_text()).items())
 assert sha(fixture)==d['provenance']['sram_sha256'];assert sha(earned)==d['provenance']['earned_sha256'];producer=json.loads(earned.read_text());assert producer['rom_sha256']==d['provenance']['source_rom_sha256'];assert not producer['failures'] and not producer['game_ram_writes'] and not producer['machine_state_loads'] and not producer['global_native']['exceptions'];assert producer['snapshots'][d['provenance']['earned_snapshot']]['sram_sha256']==sha(fixture)
 assert all(sha(base/'helper-source'/k)==v for k,v in d['helper_sources'].items());assert sha(native)==d['global_native']['trace_sha256']
 rom=a.candidate.resolve()if a.candidate else base/'tested.gba';sym=rom.with_suffix('.sym');elf=rom.with_suffix('.elf');assert not a.candidate or a.source_root
 experiment_manifest=None
 if a.candidate:
  experiment_manifest=rom.parent/'source-hashes.json';experiment_hashes=json.loads(experiment_manifest.read_text());assert all(sha(a.source_root/k)==v for k,v in experiment_hashes.items())
 C.CDLL(str(mgba),mode=C.RTLD_GLOBAL)
 original={};first_boot=None
 for line in gzip.open(native,'rt'):
  r=json.loads(line)
  if first_boot is None:first_boot=r['boot_serial']
  if r['boot_serial']!=first_boot:break
  if r['hardware_frame']<=a.end:original[r['hardware_frame']]=r
 commands={};first_inputs=[]
 for v in d['inputs']:
  if first_inputs and v['frame']<first_inputs[-1]['frame']:break
  first_inputs.append(v)
 d['inputs']=first_inputs
 assert d['inputs'][0]['frame']==0 and d['inputs'][0]['frames']==150 and d['inputs'][0]['keys']==0
 for v in d['inputs']:
  for f in range(v['frame'],min(v['frame']+v['frames'],a.end)):assert f not in commands;commands[f]=v['keys']
  if v['frame']+v['frames']>=a.end:break
 assert set(commands)==set(range(a.end));assert 0<=a.start<a.end<=d['global_native']['hardware_frames']
 syms={r[2]:int(r[0],16)for line in sym.read_text().splitlines()if len(r:=line.split())==3};funcs=functions(elf);assert len(funcs)<=2048
 names='covenants_power covenants_powers_tick covenants_powers_draw covenants_powers_geometry_changed covenants_game_tick covenants_game_clear_box covenants_game_supercover covenants_game_collision_rects update render render_static draw_world draw_actors draw_floating_hud game_geometry_sync copy_covenants covenants_game_draw_overlay covenants_game_draw_actors game_draw_health game_draw_weapon obj_commit obj_upload obj_add text box rect line world_rect world_text banner'.split();chosen=[f for name in names for f in funcs if f['name']==name];chosen +=[f for f in funcs if f['owner']=='covenants_powers.c' and f['name'].split('.')[0]in ('clear','clear_box','geometry','geometry_snapshot','rectangle_ray','rectangle_stamp','mark','line','stamp_clear','retain_complete_geometry')];assert len(chosen)<=128
 cfile=ROOT/'tests/return_stall_observer.c';so=out/'observer.so';subprocess.run(['cc','-std=c11','-D_GNU_SOURCE','-O2','-fPIC','-shared',str(cfile),'-I'+str(a.sysroot/'include'),str(mgba),'-Wl,-rpath,'+str(mgba.parent),'-o',str(so)],check=True)
 l=C.CDLL(str(so));ptr=C.POINTER(C.c_uint32);l.return_profile_reset.argtypes=[ptr,C.c_uint,ptr,ptr,C.c_uint];l.return_profile_frames.argtypes=[C.c_void_p,C.c_uint,C.c_uint];l.return_loop_config.argtypes=[C.c_uint32,C.c_uint32];l.return_loops.restype=C.POINTER(LoopRow);l.return_loop_cycles.argtypes=[C.c_uint];l.return_loop_cycles.restype=C.POINTER(C.c_uint64);l.return_state_save.argtypes=[C.c_void_p,C.c_char_p];l.return_profile_rows.restype=C.POINTER(Row);l.return_hist_cycles.restype=C.POINTER(C.c_uint64);arr=lambda v:(C.c_uint32*len(v))(*v)
 objects=scoped_objects(elf)
 def snapshot(e,old,display,state):
  g=lambda n:e.read(syms[n]);row=dict(hardware_frame=e.frame,frame_before=old,frame_after=g('frame'),update_delta=(g('frame')-old)&0xffffffff,page_flip=bool((e.read(0x04000000,2)^display)&16),display_before=display,display_after=e.read(0x04000000,2),cycles=g('render_cycles'),state_before=state,state_after=g('game_state'),room=g('room'),journal_tab=g('journal_tab'),toast_id=g('toast_id'),toast_ticks=g('toast_ticks'),obj_count=g('obj_count'),music={n:g(n)for n in ('music_faults','music_recoveries','music_stopped','music_irq_count','music_irq_late_max','music_track')})
  row['detail']={n:g(n)for n in ('page','px','py','hp','camera_x','camera_y','covenants_game_revision','covenants_power_kind','covenants_power_time','covenants_power_age','covenants_power_origin_x','covenants_power_origin_y','covenants_power_direction','ability_cd','save_resume_state','save_completion_pending','save_begin_pending','save_requested','region_cache_room','gfx_props_room')if n in syms};row['detail']['cache_valid']=[e.read(syms['cache_valid']+i*4)for i in range(2)];row['detail']['cache_fields']=[[e.read(syms['cache_fields']+(i*38+j)*4)for j in range(38)]for i in range(2)];raw=bytes(e.read(objects['cast'][0]+i,1)for i in range(240));geo=bytes(e.read(objects['collision'][0]+i,1)for i in range(396));row['cast_observation']={'count':raw[220],'revoked':raw[224],'dirty':raw[225],'marks':[list(struct.unpack_from('<bbB',raw,84+i*3))for i in range(raw[220])],'raw_hex':raw.hex(),'geometry_bounds':list(struct.unpack_from('<5h',geo,384)),'geometry_valid':geo[394],'geometry_rects':[list(struct.unpack_from('<4h',geo,i*8))for i in range(geo[395])]};row['pixels_sha256']=hashlib.sha256(e.pixels()).hexdigest();return row
 result={'scope':__doc__,'rom_sha256':sha(rom),'symbols_sha256':sha(sym),'elf_sha256':sha(elf),'fixture_sha256':sha(fixture),'source_manifest_sha256':sha(manifest),'source_report':str(report),'source_report_sha256':sha(report),'native_trace_sha256':sha(native),'source_producer_sha256':sha(earned),'profile_start':a.start,'profile_end':a.end,'selected_boot_serial':first_boot,'inputs':d['inputs'],'game_ram_writes':0,'machine_state_loads':0,'explicit_reset_count_per_run':1,'extra_warmup_frames':0,'cache_fields':38,'probes':chosen,'functions':funcs,'experiment':bool(a.candidate),'serialization_note':'Output-only mCore.saveState writes a zero-initialized host buffer; no state imports or emulated memory writes.'}
 if experiment_manifest:result['experiment_source_manifest_sha256']=sha(experiment_manifest);result['experiment_source_changes']=[k for k,v in json.loads(manifest.read_text()).items()if experiment_hashes.get(k)!=v];result['experiment_source_root']=str(a.source_root.resolve())
 for observe in (True,False):
  trace=[];hist=[]
  with ReadOnly(rom,bridge)as e:
   e.load_save(fixture);e.reset()
   for v in d['inputs']:
    if v['frame']>=a.start:break
    assert e.frame==v['frame'];e.frames(min(v['frames'],a.start-v['frame']),v['keys'])
   assert e.frame==a.start
   if observe:l.return_profile_reset(arr([f['address']for f in chosen]),len(chosen),arr([f['address']for f in funcs]),arr([f['end']for f in funcs]),len(funcs));l.return_loop_config(syms['update'],syms['render'])
   for frame in range(a.start,a.end):
    old=e.read(syms['frame']);display=e.read(0x04000000,2);state=e.read(syms['game_state'])
    if observe:l.return_hist_reset();l.return_profile_frames(e.ptr,1,keymask(commands[frame]));cs=l.return_hist_cycles();hist.append(dict(hardware_frame=e.frame,functions=[dict(index=j,cycles=cs[j])for j in range(len(funcs)+1)if cs[j]]))
    else:e.frames(1,commands[frame])
    trace.append(snapshot(e,old,display,state))
   path=out/('profile-end.state'if observe else 'control-end.state');assert l.return_state_save(e.ptr,str(path).encode());assert e.lib.eb_save(e.ptr,str(out/('profile-end.sav'if observe else 'control-end.sav')).encode());(out/('profile-end.rgb'if observe else 'control-end.rgb')).write_bytes(e.pixels())
  result['trace'if observe else 'control_trace']=trace
  if observe:
   result['hardware_frame_histograms']=hist;rs=l.return_profile_rows();result['records']=[{**{k:getattr(rs[i],k)for k,_ in Row._fields_},'name':chosen[rs[i].probe]['name'],'owner':chosen[rs[i].probe]['owner'],'cycles':rs[i].end-rs[i].begin}for i in range(l.return_profile_count())];result['overflow']=l.return_profile_overflow();result['reentered']=l.return_profile_reentered();result['update_to_render_loops']=[];ls=l.return_loops()
   for i in range(l.return_loop_count()):
    if not ls[i].end:continue
    cs=l.return_loop_cycles(i);item={k:getattr(ls[i],k)for k,_ in LoopRow._fields_};item['cycles']=item['end']-item['begin'];item['functions']=[dict(index=j,cycles=cs[j])for j in range(len(funcs)+1)if cs[j]];assert item['cycles']==sum(r['cycles']for r in item['functions']);result['update_to_render_loops'].append(item)
 compare=('frame_before','frame_after','update_delta','page_flip','display_before','display_after','cycles','state_before','state_after','room','journal_tab','toast_id','toast_ticks','obj_count','music');result['original_cadence_mismatches']=[dict(hardware_frame=r['hardware_frame'],field=k,actual=r[k],expected=original[r['hardware_frame']][k])for r in result['control_trace']for k in compare if r[k]!=original[r['hardware_frame']][k]];result['control_trace_equal']=result['trace']==result['control_trace'];result['complete_emulator_state_equal']=(out/'profile-end.state').read_bytes()==(out/'control-end.state').read_bytes();result['sram_equal']=(out/'profile-end.sav').read_bytes()==(out/'control-end.sav').read_bytes()
 result['terminal_sha256']={n:sha(out/n)for n in ('profile-end.state','control-end.state','profile-end.sav','control-end.sav','profile-end.rgb','control-end.rgb')};result['observer_sources']={str(f.relative_to(ROOT)):sha(f)for f in (Path(__file__),cfile)}
 for f in (Path(__file__),cfile):dest=out/'observer-source'/f.relative_to(ROOT);dest.parent.mkdir(exist_ok=True,parents=True);shutil.copyfile(f,dest)
 (out/'profile-report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k]for k in ('complete_emulator_state_equal','sram_equal','control_trace_equal','original_cadence_mismatches','overflow','reentered')},indent=2),flush=True)
 assert result['complete_emulator_state_equal']and result['sram_equal']and result['control_trace_equal']and(not result['original_cadence_mismatches']or a.candidate)and not result['overflow']and not result['reentered']
if __name__=='__main__':main()
