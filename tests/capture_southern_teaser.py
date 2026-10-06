#!/usr/bin/env python3
"""Continuous, spoiler-free Sunlace Anchorage development footage from a pinned ROM.

Fresh-boot the authenticated delivered Northern N5 SRAM, arrive by controller
ferry, then record each hardware frame and the actual current-game PSG. Only
the already-owned Homura form 2 appears. No RAM writes, state restores, recruits,
evolutions, puzzle interactions, secret routes, or late areas. Capture evidence
does not constitute full-candidate QA or a release claim; rerun after any ROM edit.
"""
from __future__ import annotations

import argparse
from array import array
from collections import Counter
import ctypes as C
from fractions import Fraction
import hashlib
import json
import math
from pathlib import Path
import shutil
import subprocess
import sys
import wave

sys.dont_write_bytecode = True
from southern_journey import SouthernJourney, N5_SHA, N5_ROM, ROOT, PLAY, digest
from capture_northern_teaser import core_metadata

FPS = 16777216 / 280896
FPS_RATIONAL = '16777216/280896'
CAPTURE_FRAMES = 1200


class SouthernTeaser(SouthernJourney):
    def __init__(self, *args, source_manifest=None, **kwargs):
        output = Path(args[2] if len(args) > 2 else kwargs['output']).resolve()
        if output.exists() and any(output.iterdir()):
            raise FileExistsError('Use a new empty output directory for each ROM capture; old media must never stand in for a changed candidate')
        self.recording = False
        self.encoder = None
        self.recorded_frames = 0
        self.capture_inputs = []
        self.capture_trace = []
        self.preview_frames = {}
        self.rgb_hash = hashlib.sha256()
        super().__init__(*args, source_manifest=source_manifest, **kwargs)
        # The parent initializer imports exactly the authenticated N5 SRAM and
        # cold resets. From here forward neither game memory nor saved machine
        # state nor further SRAM/reset shortcuts can be changed by the harness.
        self.e.write = self.reject_write
        self.e.state = self.reject_state
        self.e.load_save = self.reject_state
        self.e.reset = self.reject_state
        self.source_hash_artifact = 'candidate-source-hashes.json'
        self.frozen_sources = self.source_hashes
        self.source_verification = {
            'status': 'verified_against_frozen_build_manifest',
            'manifest_sha256': self.source_manifest_sha,
            'verified_root': str(self.source_root),
            'entry_count': len(self.source_checks),
            'all_manifest_entries_match': all(self.source_checks.values()),
            'scope': 'Every entry of the frozen source manifest, including compiled generated art and linker inputs. ROM and symbols are independently authenticated.',
        }
        self.fixture_manifest = ROOT / 'tests/fixtures/v5-revision3/provenance.json'
        self.fixture_provenance = json.loads(self.fixture_manifest.read_text())
        assert self.fixture_provenance['sha256'] == N5_SHA == digest(self.fixture)
        assert self.fixture_provenance['source_rom_sha256'] == N5_ROM
        assert self.fixture_provenance['controller_only'] and self.fixture_provenance['game_ram_writes'] == 0
        shutil.copyfile(self.fixture, self.out / 'source-northern-n5.sav')
        shutil.copyfile(self.fixture_manifest, self.out / 'source-save-provenance.json')
        for name in ('tests/test_creatures.py', 'tests/capture_northern_teaser.py',
                     'tests/northern_sky_route.py', 'tools/mgba_bridge.c', 'tools/mgba_bridge.so'):
            p = ROOT / name
            self.test_sources[name] = digest(p)
            shutil.copyfile(p, self.out / 'test-source' / p.name)
        self.emulator_core = core_metadata(self.e.lib)

    def report(self):
        if not hasattr(self, 'provenance'):
            return
        data = {
            'suite': 'southern-teaser-preparation', 'development_media': True,
            'full_candidate_qa_pass_claim': False, 'release_claim': False,
            **self.candidate, 'controller_only': True, 'game_ram_writes': 0,
            'machine_state_loads': 0, 'source_sram_imports': 1,
            'source_cold_resets': 1, 'provenance': self.provenance,
            'source_manifest_sha256': self.source_manifest_sha,
            'frozen_source_checks': self.source_checks,
            'test_sources': self.test_sources, 'checks': self.checks,
            'failures': self.failures, 'snapshots': self.snapshots,
            'transitions': self.transitions, 'frame_windows': self.frame_windows,
            'inputs': self.inputs,
        }
        (self.out / 'preparation.json').write_text(json.dumps(data, indent=2) + '\n')

    @staticmethod
    def reject_write(*args, **kwargs):
        raise AssertionError('Game RAM writes are forbidden in the player teaser')

    @staticmethod
    def reject_state(*args, **kwargs):
        raise AssertionError('The teaser does not save or load machine states')

    def snapshot(self, name, settle=True):
        # Preparation snapshots are read-only screenshots plus exact SRAM. The
        # teaser never needs a machine state, including during setup or retries.
        if settle:
            self.settle()
        save = self.out / (name + '.sav')
        save.write_bytes(self.e.bytes(0x0e000000, 32768))
        self.e.screenshot(self.out / (name + '.png'))
        self.snapshots[name] = {
            'sram_path': str(save), 'sram_sha256': digest(save),
            'rom_sha256': self.target_sha, 'status': self.status(),
        }
        self.report()
        return name

    def step(self, n, keys=0):
        if not self.recording:
            return super().step(n, keys)
        assert keys in (0, 'UP', 'DOWN', 'LEFT', 'RIGHT'), 'The teaser is a stroll only'
        self.inputs.append({'frame': self.e.frame, 'frames': int(n), 'keys': keys})
        self.capture_inputs.append({'frame_offset': self.recorded_frames, 'frames': int(n), 'keys': keys})
        for _ in range(n):
            self.e.frames(1, keys)
            state = self.get('game_state')
            assert self.get('room') == 30 and state == PLAY, 'Capture must stay in active opening-town play'
            assert self.get('spirit') == 0 and self.get('summoned'), 'Only retained Homura may appear'
            assert not self.get('save_failed'), 'Never conceal a failed save'
            current_update = self.get('frame')
            current_page = self.e.read(0x04000000, 2) & 16
            rgb = self.e.screenshot().tobytes()
            row = {
                'frame_offset': self.recorded_frames, 'hardware_frame': self.e.frame,
                'update_delta': (current_update - self.last_update) & 0xffffffff,
                'page_flip': current_page != self.last_page,
                'render_cycles': self.get('render_cycles'), 'game_state': state,
                'room': self.get('room'), 'spirit': self.get('spirit'),
                'camera': [self.get('camera_x'), self.get('camera_y')],
                'player': [self.get('px'), self.get('py')],
                'obj_count': self.get('obj_count'), 'ability_cd': self.get('ability_cd'),
                'rgb_sha256': hashlib.sha256(rgb).hexdigest(),
            }
            self.capture_trace.append(row)
            self.encoder.stdin.write(rgb)
            self.rgb_hash.update(rgb)
            self.last_update, self.last_page = current_update, current_page
            self.recorded_frames += 1

    def prepare(self):
        self.boot()
        self.owned_select(2)
        self.ready()
        self.goto(240, 244)
        self.face(1)
        self.step(150)
        self.check(self.selected().form_id == 2, 'Retained Northern Homura is selected without evolution')
        self.check(all(self.quest(q) == 0 and not self.state().quests.objectives[q] for q in range(22, 30)), 'No Southern quest or objective was prepared')
        self.check(not self.get('area_ticks') and not self.get('toast_ticks'), 'Opening frame is free of transient text')
        self.collection_before = self.collection()
        self.owned_before = [(c.instance_id, c.form_id) for c in self.live()]
        self.quest_bytes_before = bytes(self.state().quests)
        self.chapter_flags_before = self.get('chapter_flags')
        self.snapshot('capture-start', settle=False)
        self.preparation_frames = self.e.frame
        self.preparation_inputs = list(self.inputs)
        self.start_status = self.status()

    def begin_capture(self):
        self.encoder_log = open(self.out / 'encoder.log', 'w')
        self.encoder = subprocess.Popen([
            'ffmpeg', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', '240x160',
            '-framerate', FPS_RATIONAL, '-i', '-',
            '-map', '0:v', '-c:v', 'ffv1', '-level', '3', str(self.out / 'native-frames.mkv'),
            '-map', '0:v', '-vf', 'scale=960:640:flags=neighbor',
            '-c:v', 'libx264', '-preset', 'medium', '-crf', '18', '-pix_fmt', 'yuv420p',
            str(self.out / 'silent.mp4'),
        ], stdin=subprocess.PIPE, stdout=subprocess.DEVNULL, stderr=self.encoder_log)
        self.e.audio_start(self.out / 'native-psg.wav')
        self.start_frame = self.e.frame
        self.last_update = self.get('frame')
        self.last_page = self.e.read(0x04000000, 2) & 16
        self.recording = True

    def preview(self, name):
        self.e.screenshot(self.out / (name + '.png'))
        self.preview_frames[name + '.png'] = self.recorded_frames - 1

    def route(self):
        # Uninterrupted held D-pad stroll around the opening exterior. Never A,
        # R, doors, selectors, rewards or puzzles; no per-frame teleportation.
        self.step(90)
        self.preview('native-harbor')
        self.step(54, 'UP')
        self.step(96, 'LEFT')
        self.step(66)
        self.preview('native-town-west')
        self.step(16, 'UP')
        self.step(180, 'RIGHT')
        self.step(84)
        self.preview('native-town-east')
        self.step(72, 'DOWN')
        self.step(120, 'LEFT')
        self.step(70)
        self.preview('native-waterfront')
        self.step(52, 'UP')
        self.step(50, 'RIGHT')
        self.face(1)
        assert self.recorded_frames < CAPTURE_FRAMES
        self.step(CAPTURE_FRAMES - self.recorded_frames)
        self.preview('native-sunlace-preview')

    def finish_capture(self):
        self.recording = False
        audio_samples = self.e.audio_stop()
        self.encoder.stdin.close()
        assert self.encoder.wait() == 0, 'Native video encoding failed; see encoder.log'
        self.encoder_log.close()
        self.encoder = None
        self.check(self.e.frame - self.start_frame == self.recorded_frames, 'Every emulated capture frame was recorded')
        self.check(all(r['update_delta'] == 1 and r['page_flip'] for r in self.capture_trace), 'Every captured hardware frame updates and presents')
        self.check(max(r['render_cycles'] for r in self.capture_trace) < 280896, 'Every measured update/render remains within native frame budget')
        self.check(max(r['obj_count'] for r in self.capture_trace) <= 128, 'OAM remains within hardware budget')
        self.check(self.collection() == self.collection_before and [(c.instance_id, c.form_id) for c in self.live()] == self.owned_before, 'No recruit or evolution occurred')
        self.check(bytes(self.state().quests) == self.quest_bytes_before, 'No quest, objective, hidden route or reward changed')
        self.check(self.get('chapter_flags') == self.chapter_flags_before, 'No chapter completion or ending changed')
        self.check(self.selected().form_id == 2, 'The same retained Homura remains selected at the end')
        duration = self.recorded_frames / FPS
        self.check(18 <= duration <= 24, 'Continuous clip lasts 18 to 24 seconds')
        # No -shortest, trim, duplicated still, artificial audio or speed change.
        subprocess.run([
            'ffmpeg', '-y', '-i', str(self.out / 'silent.mp4'), '-i', str(self.out / 'native-psg.wav'),
            '-c:v', 'copy', '-c:a', 'aac', '-ar', '48000', '-b:a', '160k', '-movflags', '+faststart',
            str(self.out / 'sunlace-native-teaser.mp4'),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        probe = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json',
            str(self.out / 'sunlace-native-teaser.mp4'),
        ], text=True))
        video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
        self.check(int(video['nb_frames']) == int(video['nb_read_frames']) == self.recorded_frames, 'Mux and independent decoder preserve every native frame')
        self.check(Fraction(video['r_frame_rate']) == Fraction(FPS_RATIONAL), 'Mux preserves the exact hardware frame-rate ratio')
        self.check((video['width'], video['height']) == (960, 640), 'Player video is exactly four times native resolution')
        from PIL import Image
        self.check(all(Image.open(self.out / name).size == (240, 160) and hashlib.sha256(Image.open(self.out / name).tobytes()).hexdigest() == self.capture_trace[offset]['rgb_sha256'] for name, offset in self.preview_frames.items()), 'Every native preview is an unmodified frame from the continuous recording')
        preview = Image.open(self.out / 'native-sunlace-preview.png')
        preview.resize((960, 640), Image.Resampling.NEAREST).save(self.out / 'sunlace-preview-4x.png')
        scaled = Image.open(self.out / 'sunlace-preview-4x.png')
        self.check(scaled.tobytes() == preview.resize((960, 640), Image.Resampling.NEAREST).tobytes(), '4x preview is exact nearest-neighbor native pixels')
        decoded = subprocess.Popen([
            'ffmpeg', '-v', 'error', '-i', str(self.out / 'native-frames.mkv'),
            '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-',
        ], stdout=subprocess.PIPE)
        decoded_hash = hashlib.sha256()
        decoded_bytes = 0
        while block := decoded.stdout.read(1048576):
            decoded_hash.update(block)
            decoded_bytes += len(block)
        assert decoded.wait() == 0
        self.check(decoded_bytes == 240 * 160 * 3 * self.recorded_frames and decoded_hash.hexdigest() == self.rgb_hash.hexdigest(), 'Lossless native source decodes to the exact captured RGB stream')
        with wave.open(str(self.out / 'native-psg.wav'), 'rb') as wav:
            pcm = array('h', wav.readframes(wav.getnframes()))
            native_audio = {
                'sample_rate': wav.getframerate(), 'channels': wav.getnchannels(),
                'samples': wav.getnframes(), 'duration_seconds': wav.getnframes() / wav.getframerate(),
                'peak_amplitude': max(abs(v) for v in pcm),
                'rms_amplitude': math.sqrt(sum(v * v for v in pcm) / len(pcm)),
            }
        sync_error = native_audio['duration_seconds'] - duration
        self.check(native_audio['samples'] == audio_samples and native_audio['peak_amplitude'] > 0, 'Actual PSG audio is present and matches bridge sample count')
        self.check(abs(sync_error) < 0.05, 'Native PSG/video endpoints differ by less than 50 milliseconds')
        self.check(abs(float(audio['duration']) - float(video['duration'])) < 0.05, 'Muxed AAC/video endpoints remain synchronized')
        self.snapshot('capture-end', settle=False)
        self.check(digest(self.rom) == self.target_sha and digest(self.symbol_path) == self.symbol_sha, 'Captured ROM and symbols remain frozen')
        (self.out / 'frame-trace.json').write_text(json.dumps(self.capture_trace, indent=2) + '\n')
        report = {
            'suite': 'southern-spoiler-free-native-teaser', **self.candidate,
            'development_media': True, 'full_candidate_qa_pass_claim': False, 'release_claim': False,
            'controller_only': True, 'game_ram_writes': 0, 'machine_state_loads': 0,
            'capture_sram_reloads': 0, 'capture_cuts': 0, 'capture_reset_count': 0,
            'scope': 'Sunlace Anchorage opening exterior and an ordinary sunny stroll with retained Northern Homura form 2. No Southern creatures, recruits, evolutions, interactions, hidden routes, puzzles, boss or ending.',
            'preparation': 'Hash-authenticated delivered Northern N5 SRAM, one cold boot, revision3-to4 byte-preservation checks and ordinary controller ferry travel to room30. No completed Southern save or prior-ROM machine state.',
            'source_save': {**self.fixture_provenance, 'fixture_path': str(self.fixture), 'verified_sha256': N5_SHA},
            'source_sram_imports': 1, 'source_cold_resets': 1,
            'retained_companion_form': 2,
            'source_verification': self.source_verification,
            'source_hashes_artifact': self.source_hash_artifact,
            'frozen_source_manifest_sha256': self.source_manifest_sha,
            'frozen_source_count': len(self.frozen_sources),
            'frozen_source_checks': self.source_checks,
            'test_sources': self.test_sources, 'emulator_core': self.emulator_core,
            'preparation_frames': self.preparation_frames, 'preparation_inputs': self.preparation_inputs,
            'capture_start_frame': self.start_frame, 'capture_end_frame': self.e.frame,
            'captured_frames': self.recorded_frames, 'hardware_clock_ratio': FPS_RATIONAL,
            'frame_rate': FPS, 'duration_seconds': duration,
            'native_resolution': [240, 160], 'video_resolution': [960, 640],
            'scaling': '4x nearest-neighbor, one encoded video frame per emulated hardware frame',
            'capture_rgb_stream_sha256': self.rgb_hash.hexdigest(),
            'native_lossless_decoded_rgb_stream_sha256': decoded_hash.hexdigest(),
            'native_frame_stats': {
                'hardware_frames': len(self.capture_trace),
                'game_updates': sum(r['update_delta'] for r in self.capture_trace),
                'display_page_flips': sum(r['page_flip'] for r in self.capture_trace),
                'update_histogram': dict(Counter(r['update_delta'] for r in self.capture_trace)),
                'state_histogram': dict(Counter(r['game_state'] for r in self.capture_trace)),
                'max_update_render_cycles': max(r['render_cycles'] for r in self.capture_trace),
                'native_frame_budget_cycles': 280896,
                'max_obj_count': max(r['obj_count'] for r in self.capture_trace),
                'camera_x_range': [min(r['camera'][0] for r in self.capture_trace), max(r['camera'][0] for r in self.capture_trace)],
                'camera_y_range': [min(r['camera'][1] for r in self.capture_trace), max(r['camera'][1] for r in self.capture_trace)],
                'measurement': 'Emulated hardware frames, live game update counter, displayed VRAM page bit and native update/render cycle timer; not host FPS. Timer excludes VBlank wait/OAM commit.',
            },
            'audio': 'Real emulator PSG stereo PCM, retained as native WAV; MP4 uses 48kHz AAC resampling',
            'audio_samples_from_bridge': audio_samples, 'native_audio': native_audio,
            'native_audio_minus_video_seconds': sync_error,
            'video_stream': video, 'audio_stream': audio, 'preview_frame_offsets': self.preview_frames,
            'capture_inputs': self.capture_inputs, 'start_status': self.start_status, 'final_status': self.status(),
            'checks': self.checks, 'failures': self.failures,
        }
        names = ['sunlace-native-teaser.mp4', 'native-frames.mkv', 'native-psg.wav',
                 'frame-trace.json', 'capture-start.sav', 'capture-end.sav',
                 'source-northern-n5.sav', 'source-save-provenance.json', self.source_hash_artifact, 'sunlace-preview-4x.png'] + list(self.preview_frames)
        report['files'] = {name: {'sha256': digest(self.out / name), 'bytes': (self.out / name).stat().st_size} for name in names}
        (self.out / 'capture.json').write_text(json.dumps(report, indent=2) + '\n')
        self.report()
        checksum_names = ['capture.json', 'preparation.json'] + names
        (self.out / 'SHA256SUMS').write_text(''.join(digest(self.out / name) + '  ' + name + '\n' for name in checksum_names))
        print(json.dumps({
            'video': str(self.out / 'sunlace-native-teaser.mp4'),
            'preview': str(self.out / 'native-sunlace-preview.png'), 'frames': self.recorded_frames,
            'seconds': duration, 'native_audio_sync_error_seconds': sync_error,
            'native_frame_stats': report['native_frame_stats'], 'failed_checks': self.failures,
        }, indent=2))

    def abort(self):
        if self.recording:
            self.e.audio_stop()
            self.recording = False
        if self.encoder:
            self.encoder.stdin.close()
            self.encoder.wait()
            self.encoder_log.close()
            self.encoder = None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for key in ('rom', 'symbols', 'output'):
        parser.add_argument('--' + key, type=Path, required=True)
    parser.add_argument('--expected-rom-sha', required=True)
    parser.add_argument('--expected-symbols-sha', required=True)
    parser.add_argument('--source-manifest', type=Path, help='Required frozen source provenance; defaults to source-hashes.json beside the ROM.')
    args = parser.parse_args()
    run = SouthernTeaser(args.rom, args.symbols, args.output, args.expected_rom_sha, args.expected_symbols_sha, source_manifest=args.source_manifest)
    try:
        run.prepare()
        run.begin_capture()
        run.route()
        run.finish_capture()
    except Exception as exc:
        run.failures.append({'error': str(exc), 'status': run.status()})
        run.e.screenshot(run.out / 'capture-failure.png')
        run.report()
        run.abort()
        raise
    finally:
        run.e.close()


if __name__ == '__main__':
    main()
