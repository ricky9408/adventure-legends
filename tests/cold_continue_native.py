#!/usr/bin/env python3
"""Actual mGBA loading cadence, cancellation and decoded-state parity.

Input saves are historical/prepared fixtures or explicitly supplied earned
SRAM. They are not evidence of acquiring the whole collection. Native actions
use buttons only; game-RAM writes and machine-state imports are disabled.
"""
import argparse
import ctypes as C
import gzip
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tests'), str(ROOT/'tools')]
from player_feedback_native import Native, sha
from test_save5 import Save, compare_state

LIMIT = 280896


class ControllerNative(Native):
    def write(self, *args, **kwargs):
        raise AssertionError('Cold loading test forbids game-RAM writes')
    def state(self, *args, **kwargs):
        raise AssertionError('Cold loading test forbids machine states')


def codec(out):
    names = ('save4.c','save5.c','creatures.c','creature_data.c','equipment.c','equipment_data.c','economy.c')
    library = out/'codec.so'
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-ffreestanding','-fno-builtin',
                    '-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-shared','-fPIC',
                    *[str(ROOT/'src'/n) for n in names], '-o',str(library)], check=True)
    lib = C.CDLL(str(library))
    lib.sram = (C.c_ubyte*32768).in_dll(lib,'save5_test_sram')
    for name in ('save5_load','save5_store','save5_validate'):
        getattr(lib,name).argtypes = [C.POINTER(Save)]
    lib.creatures_migrate_legacy.argtypes = [C.c_void_p,C.c_uint,C.c_uint]
    lib.equipment_init.argtypes = [C.c_void_p]
    return lib


def full_roster(lib, out):
    s = Save(); s.campaign.chapter_flags=15; s.campaign.story_seen=10
    assert lib.creatures_migrate_legacy(C.byref(s.roster),15,0)==1
    lib.equipment_init(C.byref(s.equipment))
    count=sum(bool(c.flags&1) for c in s.roster.instances)
    for i in range(count,160):
        C.memmove(C.byref(s.roster.instances[i]),C.byref(s.roster.instances[0]),24)
        s.roster.instances[i].flags=1; s.roster.instances[i].instance_id=i+1
    s.roster.next_instance_id=161
    assert lib.save5_validate(C.byref(s))==1
    lib.save5_test_reset_writer();lib.save5_test_fail_after(-1);lib.sram[:]=b'\xff'*32768
    assert lib.save5_store(C.byref(s))==1
    path=out/'synthetic-full160-roster.sav';path.write_bytes(bytes(lib.sram))
    return path


def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('rom','symbols','bridge','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--save',type=Path,action='append',default=[])
    a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
    symbols={v[2]:int(v[0],16) for line in a.symbols.read_text().splitlines() if len(v:=line.split())==3}
    lib=codec(a.output)
    saves=[ROOT/'tests/fixtures/legacy/baseline-v2-bridge.sav',
           ROOT/'tests/fixtures/v4/finished-ending.sav',
           ROOT/'tests/fixtures/v5-revision9/covenants-all128-72-cold.sav',
           full_roster(lib,a.output),*a.save]
    report={'suite':'bounded-cold-continue-native','rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols),
            'bridge_sha256':sha(a.bridge),'helper_sha256':sha(__file__),
            'native_game_ram_writes':0,'machine_state_imports':0,'cases':[],'result':'RUNNING'}
    trace=gzip.open(a.output/'native-frames.jsonl.gz','wt')
    try:
        for case,path in enumerate(saves):
            lib.save5_test_reset_writer();lib.sram[:]=path.read_bytes();expected=Save()
            assert lib.save5_load(C.byref(expected))==1
            row={'source_sram':str(path),'source_sha256':sha(path),'synthetic_prepared_state':path.name.startswith('synthetic'),
                 'native_frames':0,'max_cycles':0,'missed_flips':0,'missed_updates':0,'overruns':0,
                 'music_faults':0,'music_recoveries':0,'loading_seen':False,'checks':[]}
            report['cases'].append(row)
            e=ControllerNative(a.rom.resolve(),a.bridge.resolve());e.load_save(path);e.reset()
            g=lambda n:e.read(symbols[n],4)
            last=None
            def check(label,value):
                row['checks'].append({'check':label,'passed':bool(value)})
                assert value,(path.name,label)
            def step(keys=0,scope='loading'):
                nonlocal last
                e.frames(1,keys)
                serial=g('render_profile_serial');flip=e.read(0x04000000,2)&16
                sample={'case':case,'scope':scope,'hardware_frame':e.frame,'serial':serial,'state':g('game_state'),
                        'frame':g('frame'),'flip':flip,'cycles':g('render_cycles'),
                        'update_cycles':g('render_profile_update'),'render_cycles':g('render_profile_render'),
                        'music_cycles':g('render_profile_music')}
                if serial and last is not None:
                    row['native_frames']+=1
                    row['missed_updates']+=int(serial-last[0]!=2)
                    row['missed_flips']+=int(flip==last[1])
                    row['overruns']+=int(sample['cycles']>LIMIT)
                    row['max_cycles']=max(row['max_cycles'],sample['cycles'])
                if serial:last=(serial,flip)
                row['loading_seen']|=sample['state']==15
                trace.write(json.dumps(sample)+'\n')
                return sample
            def wait(predicate,limit=1500,scope='loading'):
                for _ in range(limit):
                    if predicate():return
                    step(scope=scope)
                raise AssertionError((path.name,'timeout',g('game_state')))
            wait(lambda:g('game_state')==0 and g('render_profile_serial')>0,scope='startup-validation')
            check('startup recognizes existing save',g('has_save')==1)
            before=e.bytes(0x0e000000,32768)
            step('A');step();step();
            check('A enters visible loading',g('game_state')==15)
            e.screenshot(a.output/f'{case:02d}-loading.png')
            for _ in range(12):step()
            step('B');step();step()
            check('B cancels loading to title',g('game_state')==0)
            check('cancel preserves SRAM byte for byte',e.bytes(0x0e000000,32768)==before)
            step('A');step();
            # No publication, migration or ordinary save can modify SRAM while
            # the read job itself owns the loading state.
            while g('game_state')==15:
                check('loading is read only',e.bytes(0x0e000000,32768)==before)
                step()
            got=Save.from_buffer_copy(e.bytes(symbols['adventure_save'],C.sizeof(Save)))
            check('native decode preserves every named field and ledger',compare_state(got)==compare_state(expected))
            wait(lambda:not g('scene_present_phase'),scope='room-presentation')
            for _ in range(4):step(scope='room-presentation')
            e.screenshot(a.output/f'{case:02d}-resumed.png')
            check('loading progress was visible',row['loading_seen'])
            check('native mGBA reports no faults',e.lib.eb_faults(e.ptr)==0)
            row['music_faults']=g('music_faults');row['music_recoveries']=g('music_recoveries')
            check('loading has no missed update or flip',not(row['missed_updates'] or row['missed_flips']))
            check('all presented loading updates fit frame budget',not row['overruns'])
            check('music remains serviced with no fault or recovery',not(row['music_faults'] or row['music_recoveries']))
            e.close();trace.flush()
        report['result']='PASS'
    except Exception:
        report['result']='FAIL'
        raise
    finally:
        trace.close();(a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({k:report[k] for k in ('result','rom_sha256')},indent=2))
    for row in report['cases']:
        print(Path(row['source_sram']).name,row['max_cycles'],row['native_frames'],'frames')
    return 0


if __name__=='__main__':raise SystemExit(main())
