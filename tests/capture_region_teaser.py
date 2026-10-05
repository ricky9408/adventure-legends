#!/usr/bin/env python3
"""Spoiler-free native Reedhaven clip, every GBA frame and actual PSG audio.

Preparation reaches the town and practice gear only through controller inputs
from the same hash-pinned legacy fixture as region_journey.py. Capture then runs
continuously in room16 with Homura, without reloads, cuts, accelerated gameplay,
new recruits, evolution, secret routes, puzzle solutions or reward claims.
"""
from pathlib import Path
import argparse, hashlib, json, subprocess, sys, wave
from collections import Counter
sys.dont_write_bytecode=True
from region_journey import RegionJourney,ROOT,PLAY,SAVING,DIALOG

FPS=16777216/280896
FPS_RATIONAL='16777216/280896'

class RegionTeaser(RegionJourney):
    def __init__(self,*args,**kwargs):
        self.recording=False;self.encoder=None;self.recorded_frames=0;self.capture_states=Counter();self.capture_inputs=[]
        super().__init__(*args,**kwargs)
    def step(self,n,keys=0):
        if not self.recording:return super().step(n,keys)
        self.inputs.append({'frame':self.e.frame,'frames':int(n),'keys':keys})
        self.capture_inputs.append({'frame_offset':self.recorded_frames,'frames':int(n),'keys':keys})
        for _ in range(n):
            self.e.frames(1,keys)
            assert self.get('room')==16,'The spoiler-free clip must remain in the opening town'
            assert self.get('spirit') in (0,1),'Only Homura or Midori may be selected during the clip'
            state=self.get('game_state');assert state in (PLAY,SAVING,DIALOG),'Unexpected modal during continuous capture'
            assert not self.get('save_failed'),'Capture must not hide a failed save'
            self.capture_states[state]+=1
            self.encoder.stdin.write(self.e.screenshot().tobytes());self.recorded_frames+=1
    def prepare(self):
        self.step(150);self.tap('START',2,35);self.settle();self.step(88,'UP');self.settle()
        self.check(self.get('room')==1,'controller setup reaches Grove')
        self.step(49,'LEFT');self.step(27,'UP');self.settle()
        for _ in range(20):
            if self.get('room')==16:break
            self.tap('A',2,22);self.settle()
        self.check(self.get('room')==16,'controller setup enters Reedhaven')
        self.act(320,150,1);self.act(432,256,1);self.act(456,256,1)
        self.check(self.quest(0)==1 and self.state().quests.objectives[0]==0,'practice is offered but no target is solved during preparation')
        self.equip_class(2);self.select_form(1)
        # Actual gear screen, independently supplied as a native preview. It is
        # not a composite or a still inserted into the continuous walking clip.
        self.open_tab(4);self.step(6);self.e.screenshot(self.out/'native-gear.png');self.close_menu()
        if not self.get('summoned'):self.tap('B');self.settle()
        self.goto(240,220);self.face(1);self.step(120);self.settle()
        self.check(self.selected().form_id==1,'opening Homura remains selected')
        self.check(all(self.quest(q)==0 for q in range(1,11)),'no later quest, recruit or puzzle is prepared for this clip')
        self.e.state(self.out/'capture-start.state');(self.out/'capture-start.sav').write_bytes(self.e.bytes(0x0e000000,32768))
        self.preparation_frames=self.e.frame;self.preparation_inputs=list(self.inputs)
    def begin_capture(self):
        self.encoder_log=open(self.out/'encoder.log','w')
        self.encoder=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','240x160','-framerate',FPS_RATIONAL,'-i','-',
            '-vf','scale=960:640:flags=neighbor','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',str(self.out/'silent.mp4')],
            stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=self.encoder_log)
        self.e.audio_start(self.out/'native-psg.wav');self.start_frame=self.e.frame;self.recording=True
    def route(self):
        # Wide, controller-traversed town lanes. Every step is recorded, including
        # the real autosave triggered by the single lance hit on the training target.
        self.step(90)
        self.step(59,'UP');self.step(8);self.e.screenshot(self.out/'native-town.png')
        self.step(113,'RIGHT');self.step(45)
        self.step(88,'DOWN');self.step(35,'RIGHT');self.step(39,'DOWN');self.step(10,'RIGHT')
        self.face(1);self.tap('A',2,40);self.settle();self.step(90);self.e.screenshot(self.out/'native-practice.png')
        self.check(self.state().quests.objectives[0]==2,'the clip contains one real lance target hit, not a completed quest')
        self.face(2);self.tap('SELECT',2,18);self.step(38,'UP');self.step(32,'LEFT');self.step(60)
        self.step(99,'LEFT');self.step(87,'UP');self.step(140)
        self.check(self.get('room')==16,'clip ends in opening town')
        self.check(self.quest(0)==1 and all(self.quest(q)==0 for q in range(1,11)),'no reward claim, recruit or puzzle solution entered the clip')
    def finish_capture(self):
        self.recording=False;audio_samples=self.e.audio_stop();self.encoder.stdin.close()
        if self.encoder.wait():raise RuntimeError('Native video encoding failed; see encoder.log')
        self.encoder_log.close();self.encoder=None
        # No -shortest: preserve every recorded video frame even if the audio
        # buffer endpoint differs by a fraction of a hardware frame.
        subprocess.run(['ffmpeg','-y','-i',str(self.out/'silent.mp4'),'-i',str(self.out/'native-psg.wav'),'-c:v','copy','-c:a','aac','-ar','48000','-b:a','160k','-movflags','+faststart',str(self.out/'reedhaven-native-teaser.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(self.out/'reedhaven-native-teaser.mp4')],text=True))
        video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
        with wave.open(str(self.out/'native-psg.wav'),'rb') as w:
            native_audio={'sample_rate':w.getframerate(),'channels':w.getnchannels(),'samples':w.getnframes(),'duration_seconds':w.getnframes()/w.getframerate()}
        duration=self.recorded_frames/FPS
        self.check(15<=duration<=25,'clip duration is within15–25 seconds')
        self.check(int(video['nb_frames'])==self.recorded_frames,'mux preserves every captured native frame')
        self.check(self.e.frame-self.start_frame==self.recorded_frames,'no emulated frame was omitted during capture')
        self.check(self.capture_states[SAVING]>0,'the real practice autosave is visibly retained')
        self.check(abs(native_audio['duration_seconds']-duration)<0.05,'native PSG and video remain synchronized')
        report={**self.candidate,'controller_only':True,'game_ram_writes':0,'captured_savestate_restores':0,'captured_sram_reloads':0,
            'fixture':{'path':str(self.fixture),'sha256':hashlib.sha256(self.fixture.read_bytes()).hexdigest()},
            'scope':'Continuous opening town and one lance training hit with Homura. No new recruit/evolution, secret route, puzzle solution, reward claim or ending.',
            'preparation':'Unrecorded controller-only arrival and practice-gear setup; capture-start.state and matching SRAM preserve its exact reached state.',
            'preparation_frames':self.preparation_frames,'capture_start_frame':self.start_frame,'captured_frames':self.recorded_frames,
            'frame_rate':FPS,'hardware_clock_ratio':FPS_RATIONAL,'duration_seconds':duration,'state_frame_counts':dict(self.capture_states),
            'native_resolution':[240,160],'video_resolution':[960,640],'scaling':'4x nearest neighbor; no interpolated frames',
            'audio':'Actual emulator PSG recording, retained as native WAV; MP4 uses48kHz AAC resampling',
            'audio_samples_from_bridge':audio_samples,'native_audio':native_audio,'video_stream':video,'audio_stream':audio,
            'capture_inputs':self.capture_inputs,'preparation_inputs':self.preparation_inputs,'final':self.status(),
            'files':{name:{'sha256':hashlib.sha256((self.out/name).read_bytes()).hexdigest(),'bytes':(self.out/name).stat().st_size} for name in ('reedhaven-native-teaser.mp4','native-psg.wav','native-town.png','native-gear.png','native-practice.png')},
            'checks':self.checks,'failures':self.failures}
        (self.out/'capture.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
        self.report();print(json.dumps({'frames':self.recorded_frames,'seconds':duration,'save_frames':self.capture_states[SAVING],'video':str(self.out/'reedhaven-native-teaser.mp4'),'previews':[str(self.out/'native-town.png'),str(self.out/'native-gear.png')]},indent=2))
    def abort(self):
        if self.recording:self.e.audio_stop();self.recording=False
        if self.encoder:
            self.encoder.stdin.close();self.encoder.wait();self.encoder=None;self.encoder_log.close()

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--rom',required=True,type=Path);p.add_argument('--symbols',required=True,type=Path);p.add_argument('--output',required=True,type=Path);a=p.parse_args()
    r=RegionTeaser(a.rom,a.symbols,a.output,ROOT/'tests/fixtures/v4/finished-ending.sav')
    try:r.prepare();r.begin_capture();r.route();r.finish_capture()
    except Exception as exc:
        r.failures.append({'error':str(exc),'status':r.status()});r.e.screenshot(r.out/'capture-failure.png');r.report();r.abort();raise
    finally:r.e.close()
    return 0
if __name__=='__main__':raise SystemExit(main())
