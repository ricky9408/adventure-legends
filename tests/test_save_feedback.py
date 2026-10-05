#!/usr/bin/env python3
"""Host-simulated game integration: asynchronous save feedback and safe retry.

This calls the actual save/puzzle/SAVE_PENDING functions with fault-injected host
SRAM. It never runs ROM gameplay or claims normal controller progression. Audio
clock is held below its hardware-write interval while only SAVE_PENDING updates
run; render functions and hardware registers are not accessed.
"""
import ctypes as C
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
from test_save5 import Save
ROOT=Path(__file__).resolve().parents[1]

with tempfile.TemporaryDirectory(prefix='emberbond-save-feedback-') as temp:
    library=Path(temp)/'game-host.so'
    modules=['game','assets','ui','world','campaign_art','campaign_rules','save4',
             'creatures','creature_data','save5','progression','evolution_art',
             'advanced_powers','trials','trial_art']
    subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+[
        '-shared','-fPIC','-O0','-std=c99','-fno-builtin','-Wno-attributes',
        '-Wno-pointer-to-int-cast','-Wno-int-to-pointer-cast',
        '-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-Dmain=gba_main',
        *[str(ROOT/'src'/(n+'.c')) for n in modules],'-o',str(library)],check=True)
    lib=C.CDLL(str(library));lib.save5_load.argtypes=[C.POINTER(Save)]
    lib.save5_load.restype=C.c_int
    lib.creatures_migrate_legacy.argtypes=[C.c_void_p,C.c_uint,C.c_uint]
    lib.save5_test_fail_after.argtypes=[C.c_int]
    lib.save5_test_write_count.restype=C.c_uint
    def get(n):return C.c_int.in_dll(lib,n).value
    def put(n,v):C.c_int.in_dll(lib,n).value=v
    sram=(C.c_ubyte*32768).in_dll(lib,'save5_test_sram');sram[:]=b'\xff'*32768
    old=(C.c_ubyte*256).in_dll(lib,'save4_test_sram');old[:]=b'\xff'*256
    live=Save.in_dll(lib,'adventure_save')
    assert lib.creatures_migrate_legacy(C.byref(live.roster),1,2)==1
    for n,v in {'room':7,'game_state':1,'checkpoint_spawn':0,'chapter_flags':1,
                'bridge_open':1,'torches':3,'room_flags':7,'story_seen':2,
                'spirit':2,'px':56,'py':112,'pressed':0}.items():put(n,v)
    def drain():
        lib.save_frame();assert get('game_state')==6
        for _ in range(200):
            put('music_tick',-1000);lib.update()
            if get('game_state')!=6:break
        assert get('game_state')==1,'writer returns to PLAY'
    def load():
        s=Save();assert lib.save5_load(C.byref(s))==1;return s
    ids=list(dict.fromkeys(re.findall(r'\bTX_[A-Z0-9_]+\b',(ROOT/'src/ui.h').read_text())))
    lib.save5_test_fail_after(-1);lib.save_game();drain()
    assert get('save_failed')==0
    prior=load();before=bytes(sram)
    assert prior.campaign.room_flags==7
    lib.save5_test_fail_after(0)
    assert lib.campaign_power()==1
    assert get('room_flags')==15 and get('save_requested')==1
    drain();after=load()
    assert get('save_failed')==1
    assert ids[get('toast_id')]=='TX_C_SAVE_FAILED'
    assert bytes(sram)==before and lib.save5_test_write_count()==0
    assert after.campaign.room_flags==7 and after.campaign.sequence==prior.campaign.sequence
    lib.save5_test_fail_after(-1);lib.save_game()
    assert get('toast_ticks')==0,'retry dismisses stale failure feedback'
    drain();recovered=load()
    assert get('save_failed')==0 and recovered.campaign.room_flags==15
    assert recovered.campaign.sequence==prior.campaign.sequence+1
    assert get('toast_ticks')==0,'successful retry never redisplays old failure'
    print(json.dumps({'passed':True,'scope':'Actual C puzzle/save/pending-state host functions with explicit write failure',
                      'failed_write_preserves_prior_bank':True,'failure_feedback_retained':True,
                      'successful_retry_clears_stale_error':True,'game_ram_injection':False},indent=2))
