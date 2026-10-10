#!/usr/bin/env python3
"""Spoiler-free continuous native Return-build footage in a familiar old town.

Imports authenticated same-candidate minimal-route SRAM, uses only controller
input, records every hardware frame and the real emulator PSG, and never loads
a machine state. No new companions, puzzles, rewards or endings are shown.
"""
import argparse
from array import array
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import traceback
import wave

from return_journey import ReturnJourney, ROOT, PLAY, digest, newest_bank
from capture_northern_teaser import core_metadata

FPS = Fraction(16777216, 280896)
FRAMES = 1080


class ReturnTeaser(ReturnJourney):
    def __init__(self, args):
        self.recording = False
        self.encoder = None
        self.capture_rows, self.capture_inputs, self.preview_offsets = [], [], {}
        self.rgb_hash = hashlib.sha256()
        super().__init__(args.rom, args.symbols, args.output, args.rom_sha,
                         args.symbols_sha, args.elf_sha, args.source_manifest,
                         args.manifest_sha, ROOT / 'tests/fixtures/v5-revision6/underwater-minimal12-town.sav',
                         args.source_root, 'strict')
        assert digest(args.producer_report) == args.producer_sha
        producer = json.loads(args.producer_report.read_text())
        assert producer['finished_scope'] == 'lifecycle' and not producer['failures']
        assert not producer['machine_state_loads'] and producer['provenance']['minimal_prior_route']
        assert producer['global_native']['closed'] and not producer['global_native']['exceptions']
        for key in ('rom_sha256', 'symbols_sha256', 'elf_sha256'):
            assert producer[key] == self.candidate[key]
        saved = producer['snapshots']['town22-after-return']
        assert digest(saved['sram_path']) == saved['sram_sha256']
        self.source_sram = self.out / 'source-g-minimal.sav'
        shutil.copyfile(saved['sram_path'], self.source_sram)
        self.media_source = {'producer_report': str(args.producer_report.resolve()),
                             'producer_sha256': args.producer_sha,
                             'snapshot': 'town22-after-return',
                             'source_sram_sha256': digest(self.source_sram),
                             'source_rom_sha256': producer['rom_sha256'],
                             'bootstrap': 'Base constructor authenticated its delivered minimal fixture but executed zero frames with it; the G SRAM below replaces it before any gameplay.'}
        self.provenance = self.media_source
        assert self.e.frame == 0
        self.e.load_save(self.source_sram)
        self.e.reset()
        self.e.state = self.reject_state
        self.e.load_save = self.reject_state
        self.e.reset = self.reject_state
        self.emulator_core = core_metadata(self.e.lib)

    @staticmethod
    def reject_state(*args, **kwargs):
        raise AssertionError('No machine states or further SRAM/reset shortcuts in teaser')

    def snapshot(self, name, settle=True):
        if settle:
            self.settle()
            self.step(3)
        save = self.out / (name + '.sav')
        save.write_bytes(self.e.bytes(0x0e000000, 32768))
        self.e.screenshot(self.out / (name + '.png'))
        self.snapshots[name] = {'sram_path': str(save), 'sram_sha256': digest(save),
                                'status': self.status(), 'machine_state_saved': False}
        self.report()
        return name

    def step(self, count, keys=0):
        if not self.recording:
            return super().step(count, keys)
        assert keys in (0, 'UP', 'DOWN', 'LEFT', 'RIGHT', 'UP+LEFT', 'UP+RIGHT',
                        'DOWN+LEFT', 'DOWN+RIGHT', 'A', 'B')
        self.capture_inputs.append({'offset': len(self.capture_rows), 'frames': count, 'keys': keys})
        for _ in range(count):
            super().step(1, keys)
            assert self.get('game_state') == PLAY and self.get('room') == 22
            assert self.selected().form_id == 1 and self.selected().instance_id == self.companion_id
            assert 0 <= self.get('camera_x') <= 160, 'Keep eastern Return entrance offscreen'
            rgb = self.e.screenshot().tobytes()
            row = {'offset': len(self.capture_rows), 'hardware_frame': self.e.frame,
                   'player': [self.get('px'), self.get('py')],
                   'camera': [self.get('camera_x'), self.get('camera_y')],
                   'summoned': self.get('summoned'), 'sword_swing': self.get('swing'),
                   'render_cycles': self.get('render_cycles'), 'obj_count': self.get('obj_count'),
                   'rgb_sha256': hashlib.sha256(rgb).hexdigest()}
            self.capture_rows.append(row)
            self.rgb_hash.update(rgb)
            self.encoder.stdin.write(rgb)

    def preview(self, name):
        self.e.screenshot(self.out / (name + '.png'))
        self.preview_offsets[name + '.png'] = len(self.capture_rows) - 1

    def prepare(self):
        bank = newest_bank(self.source_sram.read_bytes())
        self.step(150)
        self.measured('bounded-cold-G-minimal-SRAM',
                      lambda: (self.tap('START', 2, 90), self.settle()), cold_continue=True)
        self.check(newest_bank(self.e.bytes(0x0e000000, 32768))[32:] == bank[32:],
                   'Cold G import preserves the exact earned durable payload')
        self.owned_select(1)
        self.equip_item(0, 1)
        self.ready()
        self.goto(208, 180, radius=4)
        self.face(0)
        self.step(160)
        self.check(not self.get('area_ticks') and not self.get('toast_ticks'), 'Start has no transient title or reward notice')
        self.companion_id = self.selected().instance_id
        self.before = (bytes(self.state().quests), self.collection(),
                       [(c.instance_id, c.form_id) for c in self.live()], self.get('chapter_flags'))
        self.snapshot('capture-start', settle=False)

    def begin(self):
        self.encoder_log = (self.out / 'encoder.log').open('w')
        self.encoder = subprocess.Popen([
            'ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '240x160',
            '-framerate', str(FPS), '-i', '-', '-map', '0:v', '-c:v', 'ffv1', '-level', '3',
            str(self.out / 'native-frames.mkv'), '-map', '0:v', '-vf', 'scale=960:640:flags=neighbor',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
            str(self.out / 'silent.mp4')], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=self.encoder_log)
        self.e.audio_start(self.out / 'native-psg.wav')
        self.start_frame = self.e.frame
        self.start_global = self.global_native['hardware_frames']
        self.recording = True

    def route(self):
        self.step(45)
        self.goto(144, 180, radius=4); self.step(18)
        self.goto(120, 180, radius=4); self.face(3)
        self.tap('A', 2, 18); self.tap('A', 2, 26)
        self.preview('native-sword-court')
        self.goto(160, 180, radius=4); self.goto(248, 180, radius=4)
        self.goto(264, 208, radius=4); self.step(25)
        self.tap('B', 2, 25)
        self.goto(224, 208, radius=4)
        self.tap('B', 2, 95)
        self.preview('native-homura-called')
        self.goto(192, 208, radius=4); self.step(15)
        self.goto(136, 208, radius=4); self.face(1); self.tap('A', 2, 22)
        for point in ((104,208), (144,180), (208,180), (256,208), (192,180), (160,208), (208,180)):
            self.goto(*point, radius=4)
            self.step(12)
        self.face(0)
        assert len(self.capture_rows) < FRAMES
        self.step(FRAMES - len(self.capture_rows))
        self.preview('native-quay-still')

    def finish(self):
        self.recording = False
        samples = self.e.audio_stop()
        self.encoder.stdin.close()
        assert self.encoder.wait() == 0
        self.encoder_log.close(); self.encoder = None
        self.check(self.e.frame - self.start_frame == FRAMES == len(self.capture_rows), 'Exactly one captured image per uninterrupted hardware frame')
        after = (bytes(self.state().quests), self.collection(),
                 [(c.instance_id, c.form_id) for c in self.live()], self.get('chapter_flags'))
        self.check(after == self.before, 'No quest, reward, ownership, evolution, hidden route or ending changed during capture')
        self.check(any(r['sword_swing'] for r in self.capture_rows), 'Actual sword action appears')
        self.check({r['summoned'] for r in self.capture_rows} == {0, 1}, 'Actual companion dismissal and call appear')
        subprocess.run(['ffmpeg', '-y', '-i', str(self.out / 'silent.mp4'), '-i', str(self.out / 'native-psg.wav'),
                        '-c:v', 'copy', '-c:a', 'aac', '-ar', '48000', '-b:a', '160k', '-movflags', '+faststart',
                        str(self.out / 'return-native-teaser.mp4')], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        probe = json.loads(subprocess.check_output(['ffprobe', '-v', 'error', '-count_frames', '-show_streams',
                                                   '-show_format', '-of', 'json', str(self.out / 'return-native-teaser.mp4')], text=True))
        video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
        self.check(int(video['nb_frames']) == int(video['nb_read_frames']) == FRAMES and Fraction(video['r_frame_rate']) == FPS,
                   'Independent MP4 decoder preserves every frame and exact hardware rate')
        self.check((video['width'], video['height']) == (960, 640), 'Video is exact 4x nearest-neighbor presentation')
        with wave.open(str(self.out / 'native-psg.wav')) as wav:
            pcm = array('h', wav.readframes(wav.getnframes()))
            native_audio = {'samples': wav.getnframes(), 'rate': wav.getframerate(), 'channels': wav.getnchannels(),
                            'duration': wav.getnframes()/wav.getframerate(), 'peak': max(abs(x) for x in pcm),
                            'rms': math.sqrt(sum(x*x for x in pcm)/len(pcm))}
        duration = FRAMES / float(FPS)
        self.check(samples == native_audio['samples'] and native_audio['peak'] > 0, 'Native PSG sample count is exact and non-silent')
        self.check(abs(native_audio['duration'] - duration) < .05 and abs(float(audio['duration']) - float(video['duration'])) < .05,
                   'Actual WAV and muxed audio stay within 50ms of hardware video endpoints')
        from PIL import Image
        still = Image.open(self.out / 'native-quay-still.png')
        self.check(still.size == (240,160) and hashlib.sha256(still.tobytes()).hexdigest() == self.capture_rows[-1]['rgb_sha256'],
                   'Native still is an unmodified captured frame')
        still.resize((960,640), Image.Resampling.NEAREST).save(self.out / 'quay-preview-4x.png')
        decoder = subprocess.Popen(['ffmpeg','-v','error','-i',str(self.out/'native-frames.mkv'),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
        h = hashlib.sha256(); size = 0
        while block := decoder.stdout.read(1048576): h.update(block); size += len(block)
        self.check(decoder.wait() == 0 and size == FRAMES*240*160*3 and h.hexdigest() == self.rgb_hash.hexdigest(),
                   'Lossless master decodes to the exact native RGB stream')
        self.snapshot('capture-end', settle=False)
        self.verify_closures(); self.close_global_trace(); self.report()
        (self.out/'capture-frame-trace.json').write_text(json.dumps(self.capture_rows,indent=2)+'\n')
        names = ['return-native-teaser.mp4','native-frames.mkv','native-psg.wav','native-quay-still.png',
                 'quay-preview-4x.png','capture-frame-trace.json','capture-start.sav','capture-end.sav','source-g-minimal.sav']
        report = {'scope':'Continuous familiar western quay: original Homura, movement, sword and call. No Return area, new form, puzzle solution, quest reward, hidden path or ending shown.',
                  'development_media':True, 'candidate':self.candidate,'source':self.media_source,'source_manifest_sha256':self.source_manifest_sha,
                  'helper_manifest_sha256':digest(self.out/'helper-source-hashes.json'),'emulator_core':self.emulator_core,
                  'controller_only':True,'game_ram_writes':0,'machine_state_loads':0,'capture_cuts':0,'capture_resets':0,
                  'capture_sram_imports':0,'preparation_sram_imports':2,'unexecuted_bootstrap_imports':1,
                  'frames':FRAMES,'frame_rate_ratio':str(FPS),'duration_seconds':duration,'native_resolution':[240,160],
                  'video_resolution':[960,640],'source_companion_form':1,'source_companion_instance_id':self.companion_id,
                  'capture_start_hardware_frame':self.start_frame,'capture_start_global_index':self.start_global,
                  'global_native':self.global_native,'capture_inputs':self.capture_inputs,'preview_offsets':self.preview_offsets,
                  'native_audio':native_audio,'audio_minus_video_seconds':native_audio['duration']-duration,
                  'audio_source':'Actual unchanged G ROM PSG captured by mGBA; no added music or audio trimming',
                  'native_rgb_stream_sha256':self.rgb_hash.hexdigest(),'checks':self.checks,'failures':self.failures,
                  'files':{name:{'sha256':digest(self.out/name),'bytes':(self.out/name).stat().st_size} for name in names}}
        (self.out/'capture.json').write_text(json.dumps(report,indent=2)+'\n')
        print(json.dumps({'video':str(self.out/'return-native-teaser.mp4'),'frames':FRAMES,'seconds':duration,'audio_sync_seconds':report['audio_minus_video_seconds'],'failures':self.failures},indent=2))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('rom','symbols','source-manifest','source-root','producer-report','output'):
        p.add_argument('--'+name,type=Path,required=True)
    for name in ('rom-sha','symbols-sha','elf-sha','manifest-sha','producer-sha'):
        p.add_argument('--'+name,required=True)
    run = ReturnTeaser(p.parse_args())
    try:
        run.prepare(); run.begin(); run.route(); run.finish()
    except Exception as exc:
        run.failures.append({'error':str(exc),'traceback':traceback.format_exc()})
        run.e.screenshot(run.out/'capture-failure.png')
        raise
    finally:
        if run.recording: run.e.audio_stop(); run.recording=False
        if run.encoder:
            run.encoder.stdin.close(); run.encoder.wait(); run.encoder_log.close()
        run.close_global_trace(); run.report(); run.e.close()


if __name__ == '__main__':
    main()
