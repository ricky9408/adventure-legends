#!/usr/bin/env python3
"""Continuous spoiler-free native town preview from a genuinely earned save.

The complete same-candidate native matrix must pass before this runs. Familiar
base starters, walking and the held-L selector only; no puzzle inputs, new
creatures, invitations or ending. Actual mGBA audio and lossless RGB are checked.
"""
import argparse
from array import array
import ctypes as C
from fractions import Fraction
import gzip
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import traceback
import wave
from covenants_journey import CovenantsJourney, ROOT, digest, newest_bank, PLAY
from capture_northern_teaser import core_metadata

FPS=Fraction(16777216,280896)
FRAMES=1140

class CovenantTeaser(CovenantsJourney):
    def __init__(self,args):
        self.recording=False;self.encoder=None;self.capture_rows=[];self.capture_inputs=[];self.preview_offsets={};self.rgb_hash=hashlib.sha256()
        base=args.candidate_root.resolve();status=json.loads((base/'run-status.json').read_text());pins=status['candidate']
        acceptance=args.acceptance_status.resolve();assert digest(acceptance)==args.acceptance_sha
        matrix=json.loads(acceptance.read_text());assert matrix['finished'] and matrix['all_native_gates_passed'] and matrix['candidate']==pins
        assert status['finished'] and status['all_requested_stages_passed']
        candidate=base/'candidate'
        super().__init__(candidate/'emberbond.gba',candidate/'emberbond.sym',args.output,pins['emberbond.gba'],pins['emberbond.sym'],pins['emberbond.elf'],
            candidate/'source-hashes.json',pins['source-hashes.json'],source_root=base/'runtime-source',timing_mode='strict',prior_root=base/'prior-current-c',fixture_kind='minimal-stage')
        report=args.producer_report.resolve();assert digest(report)==args.producer_sha
        producer=json.loads(report.read_text());assert producer['finished_scope']=='full' and producer['timing_mode']=='strict'
        assert producer['controller_only'] and not producer['failures'] and all(c['passed'] for c in producer['checks'])
        assert not producer['game_ram_writes'] and not producer['machine_state_loads']
        trace=producer['global_native'];assert trace['closed'] and not trace['exceptions']
        assert digest(report.parent/Path(trace['trace_path']).name)==trace['trace_sha256']
        assert all(producer[k]==self.candidate[k] for k in ('rom_sha256','symbols_sha256','elf_sha256'))
        assert producer['source_manifest_sha256']==self.source_manifest_sha
        saved=producer['snapshots']['01-final-chapter-welcome'];source=report.parent/Path(saved['sram_path']).name
        assert digest(source)==saved['sram_sha256'] and saved['sram_export']=='mCore.savedataClone'
        assert saved['status']['room']==70 and saved['quests'][60:64]==[3,1,0,0] and not saved['fulfilled'] and not saved['invitations']
        assert len(saved['individuals'])==18 and len(saved['obtained_form_ids'])==18
        self.fixture=self.out/'source-covenants-welcome.sav';shutil.copyfile(source,self.fixture);shutil.copyfile(report,self.out/'teaser-source-producer.json')
        self.source_bytes=self.fixture.read_bytes();self.source_bank=newest_bank(self.source_bytes)
        self.provenance={'fixture_path':str(self.fixture),'sram_sha256':digest(self.fixture),'source_rom_sha256':producer['rom_sha256'],
            'producer_sha256':args.producer_sha,'source_snapshot':'01-final-chapter-welcome','source_individuals':18,'source_history':18,
            'cross_rom_machine_state_loaded':False,'bootstrap':'Accepted prior-C initialization executes zero frames. Authenticated same-candidate ordinary welcome SRAM replaces it before playback.'}
        assert self.e.frame==0;self.e.load_save(self.fixture);self.e.reset()
        self.e.lib.eb_audio_start.argtypes=[C.c_void_p,C.c_char_p];self.e.lib.eb_audio_start.restype=C.c_int
        self.e.lib.eb_audio_stop.argtypes=[C.c_void_p];self.e.lib.eb_audio_stop.restype=C.c_uint
        self.emulator_core=core_metadata(self.e.lib)
        self.music_fields=('music_faults','music_recoveries','music_stopped','music_irq_count','music_irq_late_max','music_track','music_source_cursor')
        self.media_source={'report':str(report),'report_sha256':args.producer_sha,'snapshot':'01-final-chapter-welcome','sram_sha256':digest(self.fixture),
            'complete_native_acceptance_sha256':args.acceptance_sha,'candidate_stage_status_sha256':digest(base/'run-status.json')}

    def step(self,n,keys=0):
        if not self.recording:return super().step(n,keys)
        assert keys in (0,'UP','DOWN','LEFT','RIGHT','L','L+RIGHT')
        self.capture_inputs.append({'offset':len(self.capture_rows),'frames':n,'keys':keys})
        for _ in range(n):
            assert len(self.capture_rows)<FRAMES
            super().step(1,keys)
            self.check(self.get('game_state')==PLAY and self.get('room')==70,'continuous clip stays on the town promenade')
            self.check(self.get('camera_y')==0 and 0<=self.get('camera_x')<=240,'continuous framing stays on the upper town promenade')
            self.check(self.selected().form_id in (1,4) and not self.get('covenants_power_time') and not self.state().quests.region_flags[22] and not self.state().quests.region_flags[23],'only familiar starters appear, before any legendary invitation or completed work')
            r=self.roster();self.check([r.instances[i].form_id for i in r.party]==[1,4,7,10],'held-L preview contains only four familiar base starters')
            rgb=self.e.screenshot().tobytes();row={'offset':len(self.capture_rows),'hardware_frame':self.e.frame,
                'player':[self.get('px'),self.get('py')],'camera':[self.get('camera_x'),self.get('camera_y')],
                'selected_form':self.selected().form_id,'selected_instance':self.selected().instance_id,'summoned':self.get('summoned'),
                'quickparty_open':self.get('quickparty_open'),'cycles':self.get('render_cycles'),'obj_count':self.get('obj_count'),
                'rgb_sha256':hashlib.sha256(rgb).hexdigest(),'music':{name:self.get(name) for name in self.music_fields}}
            self.capture_rows.append(row);self.rgb_hash.update(rgb);self.encoder.stdin.write(rgb)

    def preview(self,name):
        self.e.screenshot(self.out/(name+'.png'));self.preview_offsets[name+'.png']=len(self.capture_rows)-1

    def prepare(self):
        self.step(150);self.measured('bounded-cold-welcome-continue',lambda:(self.tap('START',2,90),self.settle()),cold_continue=True)
        self.check(newest_bank(self.e.bytes(0x0e000000,32768))[32:]==self.source_bank[32:],'ordinary Continue preserves the exact earned source payload')
        self.check(self.get('room')==70 and self.quest(60)==3 and self.quest(61)==1 and not self.state().quests.region_flags[22] and not self.state().quests.region_flags[23],'welcome is before all new work, invitations and ending')
        for slot,form in enumerate((1,4,7,10)):self.assign(slot,form)
        self.select_slot(0);self.equip_item(0,1);self.ready();self.goto(128,32,radius=4);self.face(3);self.step(160)
        self.check(not self.get('area_ticks') and not self.get('toast_ticks'),'capture opens without notices')
        self.before=(bytes(self.state().quests),bytes(self.state().equipment),self.collection(),[(c.instance_id,c.form_id) for c in self.live()],self.get('chapter_flags'))
        self.snapshot('capture-start',settle=False)

    def begin(self):
        self.encoder_log=(self.out/'encoder.log').open('w')
        self.encoder=subprocess.Popen(['ffmpeg','-y','-f','rawvideo','-pix_fmt','rgb24','-s','240x160','-framerate',str(FPS),'-i','-',
            '-map','0:v','-c:v','ffv1','-level','3',str(self.out/'native-frames.mkv'),
            '-map','0:v','-vf','scale=960:640:flags=neighbor','-c:v','libx264','-preset','medium','-crf','18','-pix_fmt','yuv420p',str(self.out/'silent.mp4')],
            stdin=subprocess.PIPE,stdout=subprocess.DEVNULL,stderr=self.encoder_log)
        self.music_before={n:self.get(n) for n in self.music_fields}
        self.check(not any(self.music_before[n] for n in ('music_faults','music_recoveries','music_stopped')),'native PCM transport is healthy before recording')
        self.e.audio_start(self.out/'native-game-audio.wav');self.start_frame=self.e.frame;self.start_global=self.global_native['hardware_frames'];self.recording=True

    def route(self):
        self.step(30);self.goto(336,32,radius=4);self.step(24);self.preview('native-siltwake-starter')
        self.step(18,'L');self.step(18,'L+RIGHT');self.step(1);self.step(30);self.preview('native-siltwake-switch')
        for point in ((128,32),(288,32),(152,32),(320,32),(200,32)):
            self.goto(*point,radius=4);self.step(18)
        self.face(0)
        self.check(len(self.capture_rows)<=FRAMES,'planned public promenade fits the continuous clip')
        self.step(FRAMES-len(self.capture_rows));self.preview('native-siltwake-still')

    def finish(self):
        self.recording=False;samples=self.e.audio_stop();self.encoder.stdin.close();self.check(self.encoder.wait()==0,'both video encoders finish');self.encoder_log.close();self.encoder=None
        self.check(self.e.frame-self.start_frame==FRAMES==len(self.capture_rows),'every uninterrupted hardware frame has one captured native image')
        after=(bytes(self.state().quests),bytes(self.state().equipment),self.collection(),[(c.instance_id,c.form_id) for c in self.live()],self.get('chapter_flags'))
        self.check(after==self.before,'capture grants no quest, item, individual, evolution, hidden route or ending')
        self.music_after={n:self.get(n) for n in self.music_fields}
        self.check(self.music_after['music_irq_count']>self.music_before['music_irq_count'],'actual PCM IRQ advances through the full clip')
        self.check(all(r['music']['music_track']==self.music_before['music_track'] for r in self.capture_rows),'one original native music track continues throughout')
        self.check({r['selected_form'] for r in self.capture_rows}=={1,4} and any(r['quickparty_open'] for r in self.capture_rows),'short real held-L switch selects a second familiar starter')
        self.check(max(r['camera'][0] for r in self.capture_rows)-min(r['camera'][0] for r in self.capture_rows)>=160,'ordinary walking demonstrates a wide camera pan')
        subprocess.run(['ffmpeg','-y','-i',str(self.out/'silent.mp4'),'-i',str(self.out/'native-game-audio.wav'),'-c:v','copy','-c:a','aac','-ar','48000','-b:a','160k','-movflags','+faststart',str(self.out/'covenants-native-teaser.mp4')],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
        probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_streams','-show_format','-of','json',str(self.out/'covenants-native-teaser.mp4')],text=True))
        video=next(s for s in probe['streams'] if s['codec_type']=='video');audio=next(s for s in probe['streams'] if s['codec_type']=='audio')
        self.check(int(video['nb_frames'])==int(video['nb_read_frames'])==FRAMES and Fraction(video['r_frame_rate'])==FPS,'independent decoder preserves frame count and exact hardware rate')
        self.check((video['width'],video['height'])==(960,640),'presentation is uncropped exact4x nearest-neighbor native world')
        with wave.open(str(self.out/'native-game-audio.wav')) as wav:
            pcm=array('h',wav.readframes(wav.getnframes()));native_audio={'samples':wav.getnframes(),'rate':wav.getframerate(),'channels':wav.getnchannels(),'duration':wav.getnframes()/wav.getframerate(),'peak':max(abs(x) for x in pcm),'rms':math.sqrt(sum(x*x for x in pcm)/len(pcm)),'clipped_samples':sum(abs(x)>=32767 for x in pcm)}
        duration=FRAMES/float(FPS)
        self.check(samples==native_audio['samples'] and native_audio['peak']>0 and not native_audio['clipped_samples'],'actual native mixed PCM+PSG audio is non-silent and unclipped')
        self.check(abs(native_audio['duration']-duration)<.05 and abs(float(audio['duration'])-float(video['duration']))<.05,'native WAV and muxed audio stay within50ms of hardware video endpoints')
        from PIL import Image
        still=Image.open(self.out/'native-siltwake-still.png');self.check(still.size==(240,160) and hashlib.sha256(still.tobytes()).hexdigest()==self.capture_rows[-1]['rgb_sha256'],'native still is the unmodified final captured frame')
        still.resize((960,640),Image.Resampling.NEAREST).save(self.out/'siltwake-preview-4x.png')
        decoder=subprocess.Popen(['ffmpeg','-v','error','-i',str(self.out/'native-frames.mkv'),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
        h=hashlib.sha256();size=0
        while chunk:=decoder.stdout.read(1048576):h.update(chunk);size+=len(chunk)
        self.check(decoder.wait()==0 and size==FRAMES*240*160*3 and h.hexdigest()==self.rgb_hash.hexdigest(),'lossless master decodes to the exact native RGB stream')
        self.snapshot('capture-end',settle=False);self.check((self.out/'capture-start.sav').read_bytes()==(self.out/'capture-end.sav').read_bytes(),'entire cartridge SRAM stays byte-identical during the recorded clip')
        self.finished_scope='spoiler-free-native-siltwake-teaser';self.verify_closures();self.close_global_trace();self.report()
        with gzip.open(self.out/'capture-frame-trace.jsonl.gz','wt') as f:
            for row in self.capture_rows:f.write(json.dumps(row,separators=(',',':'))+'\n')
        names=('covenants-native-teaser.mp4','native-frames.mkv','native-game-audio.wav','native-siltwake-still.png','siltwake-preview-4x.png','capture-frame-trace.jsonl.gz','capture-start.sav','capture-end.sav','source-covenants-welcome.sav')
        result={'scope':'Public town promenade, walking/camera and one held-L switch among familiar base starters. No puzzle inputs, invitations, new creatures, hidden routes or ending are shown.','controller_only':True,'game_ram_writes':0,'machine_state_loads':0,'continuous_frames':FRAMES,'duration_seconds':duration,'fps':str(FPS),'native_resolution':[240,160],'presentation_resolution':[960,640],'physical_handheld_tested':False,
            **self.candidate,'source_manifest_sha256':self.source_manifest_sha,'source':self.media_source,'helper_sources':self.test_sources,'emulator':self.emulator_core,'inputs':self.capture_inputs,'previews':self.preview_offsets,'native_rgb_sha256':self.rgb_hash.hexdigest(),'music_before':self.music_before,'music_after':self.music_after,'native_audio':native_audio,'audio_minus_video_seconds':float(audio['duration'])-float(video['duration']),
            'capture_maximum_cycles':max(r['cycles'] for r in self.capture_rows),'capture_maximum_oam':max(r['obj_count'] for r in self.capture_rows),'global_native':self.global_native,'checks':self.checks,'failures':self.failures,'files':{n:{'bytes':(self.out/n).stat().st_size,'sha256':digest(self.out/n)} for n in names}}
        (self.out/'teaser-report.json').write_text(json.dumps(result,indent=2)+'\n')
        print(json.dumps({'video':str(self.out/'covenants-native-teaser.mp4'),'frames':FRAMES,'seconds':duration,'failures':self.failures}),flush=True)

def main():
    p=argparse.ArgumentParser(description=__doc__)
    for name in ('candidate-root','acceptance-status','producer-report','output'):p.add_argument('--'+name,type=Path,required=True)
    p.add_argument('--producer-sha',required=True);p.add_argument('--acceptance-sha',required=True);a=p.parse_args();r=CovenantTeaser(a)
    try:r.prepare();r.begin();r.route();r.finish()
    except Exception as exc:
        r.failures.append({'error':str(exc),'traceback':traceback.format_exc(),'status':r.status()});r.report();raise
    finally:
        if r.recording:r.e.audio_stop();r.recording=False
        if r.encoder:
            r.encoder.stdin.close();r.encoder.wait();r.encoder_log.close()
        r.close_global_trace();r.report();r.e.close()
    return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
