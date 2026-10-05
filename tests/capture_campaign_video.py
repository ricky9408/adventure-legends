#!/usr/bin/env python3
"""Continuous controller-only campaign movie, at actual GBA cadence and audio.

Uses the tested navigation/combat route without savestate branches or test reloads.
ffmpeg is optional for development and required only for this capture target.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import campaign_tests as T

ROOT=T.ROOT
OUT=ROOT/'build/campaign-video'
OUT.mkdir(parents=True,exist_ok=True)

class Movie(T.CampaignRun):
    def __init__(self):
        super().__init__(ROOT/'build/emberbond.gba',ROOT/'build/emberbond.sym',OUT,optional=True,exhaustive=False)
        self.encoder=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','240x160','-r',str(T.REFRESH_HZ),'-i','-','-vf','scale=960:640:flags=neighbor','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p',str(OUT/'silent.mp4')],stdin=subprocess.PIPE,stderr=subprocess.DEVNULL)
        self.e.audio_start(OUT/'gameplay.wav')
        self.recorded_frames=0
    def one_frame(self,keys):
        previous=self.get('room')
        self.inputs.append({'emulator_frame':self.e.frame,'frames':1,'keys':keys})
        self.e.frames(1,keys)
        current=self.get('room')
        if current!=previous:self.edges.append([previous,current])
        if current not in self.visits:self.visits.append(current)
        if self.get('save_failed'):raise AssertionError('Capture encountered a failed save')
        self.encoder.stdin.write(self.e.screenshot().tobytes())
        self.recorded_frames+=1
    def step(self,count,keys=0):
        for _ in range(count):self.one_frame(keys)
        while self.get('game_state')==6:self.one_frame(0)
    def dialogs(self,reward=None):
        for _ in range(32):
            if self.get('game_state')!=T.DIALOG:return
            self.step(95)
            self.tap('A',4,12)
        raise AssertionError('Dialogue did not end')
    def menu_case(self,name):
        self.tap('START');self.step(80)
        self.tap('A');self.step(80)
        self.tap('A');self.step(80)
        self.shot(name+'-companions')
        self.tap('B')
    def cadence(self,*args,**kwargs):pass
    def reload_case(self,*args,**kwargs):pass
    def object(self,oid,negatives=False,persistence=False):
        return super().object(oid,negatives=False,persistence=False)
    def restore(self,*args,**kwargs):
        raise AssertionError('Continuous capture must not restore a state')
    def reopen(self,*args,**kwargs):
        raise AssertionError('Continuous capture must not reload a save')
    def finish(self):
        self.step(150)
        self.e.audio_stop();self.encoder.stdin.close()
        if self.encoder.wait():raise RuntimeError('ffmpeg encoding failed')
        subprocess.run(['ffmpeg','-y','-i',str(OUT/'silent.mp4'),'-i',str(OUT/'gameplay.wav'),'-c:v','copy','-c:a','aac','-shortest','-movflags','+faststart',str(OUT/'emberbond-gameplay.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        (OUT/'capture.json').write_text(json.dumps({'rom_sha256':hashlib.sha256(self.rom.read_bytes()).hexdigest(),'controller_only':True,'game_ram_writes':0,'savestate_restores':0,'sram_reloads':0,'recorded_frames':self.recorded_frames,'frame_rate':T.REFRESH_HZ,'duration_seconds':self.recorded_frames/T.REFRESH_HZ,'audio':'actual emulator PSG audio','route':'optional relic and chime; all14areas; all3bosses; ending and peaceful village','final':self.status()},indent=2)+'\n')
        self.e.close()

if __name__=='__main__':
    p=Movie()
    try:
        p.run();p.finish()
    except Exception:
        p.encoder.stdin.close();p.encoder.wait();p.e.close();raise
