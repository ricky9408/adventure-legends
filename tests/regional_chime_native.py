#!/usr/bin/env python3
"""Explicitly prepared room68: actual controller chime trigger over HORIZONS PCM."""
import argparse,ctypes as C,json,hashlib,shutil
from pathlib import Path
from player_feedback_native import Run,ROOT,sha
from test_save5 import Save
class Chime(Run):
    def step(self,n=1,keys=0,phase='measured'):
        for _ in range(n):
            super().step(1,keys,phase)
            self.frames[-1]['chime']={k:self.g(k,1) for k in ('horizons_music_active','horizons_music_note','horizons_music_left','horizons_music_paused')}
            self.frames[-1]['psg2_on']=bool(self.e.read(0x04000084,2)&2)
            self.frames[-1]['music_consumed']=self.g('music_consumed')
    def chime(self):
        self.play();self.location(68,120,112);self.put('face',1,reason='Prepared interaction pose,16pixels south and facing assembly')
        self.put('adventure_save',4,w=2,offset=Save.quests.offset+type(Save().quests).objectives.offset+57*2,reason='Explicit synthetic previously committed assembly objective; controller starts original chime')
        self.step(90,phase='prepared');self.check('HORIZONS cue playing',self.g('music_track')==21)
        for name,args,ret in [('eb_audio_start',[C.c_void_p,C.c_char_p],C.c_int),('eb_audio_stop',[C.c_void_p],C.c_uint)]:
            fn=getattr(self.e.lib,name);fn.argtypes=args;fn.restype=ret
        self.e.audio_start(self.out/'room68-native-mix.wav');self.step(30)
        begin=len(self.frames);self.tap('A');self.step(15);self.check('Controller A starts native assembly chime',self.g('horizons_music_active',1)==1)
        self.tap('START');self.step(45);self.check('Pause holds chime while regional PCM continues',self.g('game_state')==3 and self.g('horizons_music_paused',1)==1 and self.g('music_track')==21)
        self.tap('START');self.step(210);self.check('Chime completes with regional PCM intact',not self.g('horizons_music_active',1) and self.g('music_track')==21)
        rows=self.frames[begin:];self.check('Native PSG2 is active concurrently with PCM',any(r['psg2_on'] and r['music_consumed']>0 for r in rows))
        self.check('All12 native chime notes observed',set(range(12)).issubset({r['chime']['horizons_music_note'] for r in rows if r['chime']['horizons_music_active']}))
        self.check('No audio starvation/recovery during chime',not any(r['music'][k] for r in rows for k in ('music_faults','music_recoveries','music_stopped')))
        self.e.audio_stop()
        self.hashes['room68_native_mix_sha256']=sha(self.out/'room68-native-mix.wav')
        self.shot('native-room68-chime-complete')
def main():
    p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,default=ROOT/'build/emberbond.gba');p.add_argument('--symbols',type=Path,default=ROOT/'build/emberbond.sym');p.add_argument('--output',type=Path,required=True);p.add_argument('--expected-rom-sha');p.add_argument('--expected-symbols-sha');p.add_argument('--earned-shop-save',type=Path);p.add_argument('--allow-pacing-exceptions',action='store_true');p.add_argument('--cases',default='chime');a=p.parse_args();r=Chime(a)
    r.hashes['chime_harness_sha256']=sha(__file__);shutil.copyfile(__file__,r.out/'test-source/tests/regional_chime_native.py')
    r.section('chime',r.chime);r.complete=True;r.finish()
if __name__=='__main__':main()
