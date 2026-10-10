#!/usr/bin/env python3
"""Replay recorded prepared entry, then observe unchanged ARM function timing.

The setup writes are exactly those from the retained native matrix and are
reported as synthetic. The observation interval itself is read-only. A normal
runFrame control must match every observation and complete serialized state.
"""
import argparse,ctypes as C,gzip,json,shutil,subprocess
from pathlib import Path
from player_feedback_native import Native,ROOT,sha
from profile_return_stalls import functions,Row
class Guarded(Native):
    write_count=0;guard=False
    def write(self,*args):
        assert not self.guard,'Profile interval may not inject game state'
        self.write_count+=1;return super().write(*args)
def read_jsonl(path):
    with gzip.open(path,'rt') as f:return [json.loads(line) for line in f]
def main():
    p=argparse.ArgumentParser(description=__doc__)
    for n in ('rom','symbols','elf','bridge','evidence','output'):p.add_argument('--'+n,type=Path,required=True)
    p.add_argument('--save',type=Path,help='Exact initial SRAM used by this recorded emulator session')
    p.add_argument('--probes',help='Optional comma-separated exact function names');p.add_argument('--emulator-id',type=int,default=12);p.add_argument('--start',type=int,default=7576);p.add_argument('--end',type=int,default=7602);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
    d=json.loads((a.evidence/'report.json').read_text());assert sha(a.rom)==d['provenance']['rom_sha256'] and sha(a.symbols)==d['provenance']['symbols_sha256'];sy={v[2]:int(v[0],16) for line in a.symbols.read_text().splitlines() if len(v:=line.split())==3}
    all_inputs=read_jsonl(a.evidence/'inputs.jsonl.gz');inputs=[x for x in all_inputs if x.get('emulator_id')==a.emulator_id];all_writes=read_jsonl(a.evidence/'preparation-writes.jsonl.gz');writes=[x for x in all_writes if x.get('emulator_id')==a.emulator_id];commands={}
    for row in inputs:
        for frame in range(row['frame'],min(a.end,row['frame']+row['frames'])):assert frame not in commands;commands[frame]=row['keys']
    assert set(range(a.end))<=commands.keys();assert not any(a.start<=x['frame']<a.end for x in writes)
    names={'copy_south','south_game_draw_overlay','feedback_world_draw','trials_draw_background','capture_play_strip','draw_world','render','render_static','draw_actors','draw_floating_hud','game_geometry_sync','update','save_frame','enter_room','south_game_enter','south_game_commit_enter','south_enter_apply','reset_scene','south_puzzle_beam','south_puzzle_beam.part.0','south_puzzle_solved','south_puzzle_receivers','south_game_solid','south_game_solid.part.0','rect','line','pix','box','text','centered','sprite','south_game_draw_actors','south_actor','region_actor','region_pixels_actor','obj_upload','obj_add','south_game_tick','southern_powers_draw','south_puzzle_geometry_build','south_game_geometry_changed','southern_powers_geometry_changed'}
    if a.probes:names=set(a.probes.split(','))
    fs=functions(a.elf);selected=[f for f in fs if f['name'] in names and (f['name'] not in ('reset_scene',) or f['owner']=='south_game.c')];assert len(selected)<=64
    usr=ROOT/'tools/sysroot/usr';observer=out/'observer.so';subprocess.run(['cc','-std=c11','-D_GNU_SOURCE','-O2','-fPIC','-shared',str(ROOT/'tests/legacy_mgba_profile.c'),str(ROOT/'tests/return_stall_observer.c'),'-I'+str(usr/'include'),'-L'+str(usr/'lib/x86_64-linux-gnu'),'-Wl,-rpath,'+str((usr/'lib/x86_64-linux-gnu').resolve()),'-lmgba','-o',str(observer)],check=True)
    lib=C.CDLL(str(observer));lib.legacy_profile_reset.argtypes=[C.POINTER(C.c_uint32),C.c_uint];lib.legacy_profile_frames.argtypes=[C.c_void_p,C.c_uint,C.c_uint];lib.legacy_profile_rows.restype=C.POINTER(Row);lib.return_state_save.argtypes=[C.c_void_p,C.c_char_p];lib.return_state_save.restype=C.c_int
    fixture=a.save if a.save else ROOT/'tests/fixtures/v5-revision9/covenants-all128-72-cold.sav'
    if not a.save:assert sha(fixture)==d['fixture_sha256']
    byframe={}
    for row in writes:byframe.setdefault(row['frame'],[]).append(row)
    result={'scope':__doc__,'rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols),'elf_sha256':sha(a.elf),'fixture_sha256':sha(fixture),'initial_sram_path':str(fixture.resolve()),'input_report_sha256':sha(a.evidence/'report.json'),'profile_start':a.start,'profile_end':a.end,'setup_writes':[],'profile_window_game_ram_writes':0,'probes':selected}
    def status(e,old,page):
        g=lambda n:e.read(sy[n]);return {'hardware_frame':e.frame,'delta':(g('frame')-old)&0xffffffff,'flip':int((e.read(0x04000000,2)&16)!=page),'cycles':g('render_cycles'),'mode':g('game_state'),'room':g('room'),'px':g('px'),'py':g('py'),'world':g('render_profile_world'),'south_puzzle':list(e.bytes(sy['south_game_puzzle'],3)),'save_failed':g('save_failed')}
    with Guarded(a.rom,a.bridge) as e:
        e.load_save(fixture);e.reset()
        for frame in range(a.start):
            assert e.frame==frame
            for row in byframe.get(frame,[]):
                address=sy[row['symbol']]+row['offset'];width=row['width'];e.write(address,row['value']&((1<<(8*width))-1),width);result['setup_writes'].append(row)
            e.frames(1,commands[frame])
        result['setup_write_count']=e.write_count;e.guard=True;assert lib.return_state_save(e.ptr,str(out/'start.state').encode());e.save(out/'start.sav');result['start']={'room':e.read(sy['room']),'state':e.read(sy['game_state']),'south_puzzle':list(e.bytes(sy['south_game_puzzle'],3))}
        # mGBA normalizes PSG event timestamps on state import. Apply the
        # identical import to both branches, as the retained profiler does.
        e.close();e=Guarded(a.rom,a.bridge);e.load_save(out/'start.sav');e.state(out/'start.state',load=True);e.guard=True;result['same_rom_state_loads']=2
        lib.legacy_profile_reset((C.c_uint32*len(selected))(*[f['address'] for f in selected]),len(selected));trace=[]
        for frame in range(a.start,a.end):
            old=e.read(sy['frame']);page=e.read(0x04000000,2)&16;lib.legacy_profile_frames(e.ptr,1,commands[frame]);trace.append(status(e,old,page))
        assert lib.return_state_save(e.ptr,str(out/'observed.state').encode());rs=lib.legacy_profile_rows();records=[{**{k:getattr(rs[i],k) for k,_ in Row._fields_},'name':selected[rs[i].probe]['name'],'owner':selected[rs[i].probe]['owner'],'cycles':rs[i].end-rs[i].begin} for i in range(lib.legacy_profile_count())];result.update(observed=trace,records=records,overflow=lib.legacy_profile_overflow(),reentered=lib.legacy_profile_reentered(),native_faults=e.lib.eb_faults(e.ptr));e.close()
    with Guarded(a.rom,a.bridge) as e:
        e.load_save(out/'start.sav');e.state(out/'start.state',load=True);e.guard=True;trace=[]
        for frame in range(a.start,a.end):
            old=e.read(sy['frame']);page=e.read(0x04000000,2)&16;e.frames(1,commands[frame]);trace.append(status(e,old,page))
        assert lib.return_state_save(e.ptr,str(out/'control.state').encode());result['control']=trace
    result['trace_equal']=result['observed']==result['control'];result['complete_state_equal']=(out/'observed.state').read_bytes()==(out/'control.state').read_bytes();original={x['hw']:x for x in read_jsonl(a.evidence/'native-frames.jsonl.gz') if x.get('emulator_id')==a.emulator_id};result['original_cadence_mismatches']=[{'frame':x['hardware_frame'],'field':k,'original':original[x['hardware_frame']][k],'actual':x[k]} for x in trace for k in ('delta','flip','cycles','mode','room') if x[k]!=original[x['hardware_frame']][k]]
    result['summary']={f['name']:{'calls':sum(r['probe']==i for r in records),'max_cycles':max((r['cycles'] for r in records if r['probe']==i),default=0),'total_cycles':sum(r['cycles'] for r in records if r['probe']==i)} for i,f in enumerate(selected)}
    for rel in ('tests/profile_player_feedback_entry.py','tests/player_feedback_native.py','tests/legacy_mgba_profile.c','tests/return_stall_observer.c','tests/profile_return_stalls.py'):
        dest=out/'source'/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(ROOT/rel,dest)
    (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ('summary','trace_equal','complete_state_equal','original_cadence_mismatches','overflow','reentered')},indent=2));assert result['trace_equal'] and result['complete_state_equal'] and not result['original_cadence_mismatches'] and not result['overflow'] and not result['reentered']
if __name__=='__main__':main()
