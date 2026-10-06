#!/usr/bin/env python3
"""Continuous, spoiler-free Hearthwake Quay footage from a hash-pinned native ROM.

Fresh-boot the authenticated Sky-clear SRAM, earn the ferry arrival by controller,
then record every hardware frame and the emulator's actual PSG. No RAM writes,
machine-state restores, new recruits, evolutions, quest solutions or late areas.
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
import platform
from pathlib import Path
import shutil
import subprocess
import sys
import wave

sys.dont_write_bytecode = True
from northern_sky_route import SkyRoute, SKY_SHA, ROOT, PLAY, digest

FPS = 16777216 / 280896
FPS_RATIONAL = '16777216/280896'
CAPTURE_FRAMES = 1200


def enforced_source(path):
    """Build inputs whose mismatch invalidates a supplied frozen manifest."""
    path = Path(path)
    if path.suffix.lower() in ('.md', '.markdown', '.rst'):
        return False
    if path.stem.lower() in ('readme', 'credits', 'credit', 'license', 'licence', 'notice', 'authors', 'changelog'):
        return False
    return path.as_posix() == 'linker.ld' or path.parts[0] in ('src', 'assets')


def core_metadata(bridge):
    """Observe the actually loaded mGBA library without assuming a sysroot."""
    data = {'name': None, 'version': None, 'path': None, 'sha256': None,
            'path_status': 'unlocated_system_library', 'host_platform': platform.platform()}
    for field, symbol in (('name', 'projectName'), ('version', 'projectVersion')):
        try:
            value = C.c_char_p.in_dll(bridge, symbol).value
            data[field] = value.decode('utf-8', errors='replace') if value else None
        except (AttributeError, ValueError, TypeError, OSError):
            pass
    # dladdr is available on ordinary Linux/macOS environments and identifies
    # the library owning mCoreFind, rather than merely guessing from filenames.
    class DlInfo(C.Structure):
        _fields_ = [('filename', C.c_char_p), ('base', C.c_void_p),
                    ('symbol', C.c_char_p), ('symbol_address', C.c_void_p)]
    try:
        lookup = C.CDLL(None).dladdr
        lookup.argtypes = [C.c_void_p, C.POINTER(DlInfo)]
        lookup.restype = C.c_int
        info = DlInfo()
        if lookup(C.cast(bridge.mCoreFind, C.c_void_p), C.byref(info)) and info.filename:
            path = Path(info.filename.decode('utf-8', errors='replace')).resolve()
            if path.is_file():
                data.update(path=str(path), sha256=digest(path), path_status='located_loaded_library_via_dladdr')
    except (AttributeError, ValueError, TypeError, OSError):
        pass
    return data


class NorthernTeaser(SkyRoute):
    def __init__(self, *args, source_manifest=None, **kwargs):
        self.recording = False
        self.encoder = None
        self.recorded_frames = 0
        self.capture_inputs = []
        self.capture_trace = []
        self.preview_frames = {}
        self.rgb_hash = hashlib.sha256()
        super().__init__(*args, **kwargs)
        # These observations cannot mutate gameplay; make accidental writes or
        # state imports fail even if a future inherited helper attempts one.
        self.e.write = self.reject_write
        self.e.state = self.reject_state
        manifest = Path(source_manifest).resolve() if source_manifest else self.source_rom.parent / 'source-hashes.json'
        if source_manifest and not manifest.is_file():
            raise FileNotFoundError(f'Explicit source manifest does not exist: {manifest}')
        self.frozen_sources = {}
        self.source_comparison = {}
        self.source_manifest_sha = None
        if manifest.is_file():
            self.frozen_sources = json.loads(manifest.read_text())
            self.source_comparison = {
                path: {'frozen_sha256': sha,
                       'current_sha256': digest(ROOT / path) if (ROOT / path).is_file() else None,
                       'enforced_build_input': enforced_source(path)}
                for path, sha in self.frozen_sources.items()
                if not (ROOT / path).is_file() or digest(ROOT / path) != sha
            }
            mismatches = [p for p in self.source_comparison if enforced_source(p)]
            assert not mismatches, 'Build inputs differ from frozen source manifest: ' + ', '.join(mismatches)
            self.source_hash_artifact = 'frozen-source-hashes.json'
            if manifest != self.out / self.source_hash_artifact:
                shutil.copyfile(manifest, self.out / self.source_hash_artifact)
            self.source_manifest_sha = digest(manifest)
            self.source_verification = {
                'status': 'verified_against_frozen_build_manifest',
                'manifest_path': str(manifest), 'manifest_sha256': self.source_manifest_sha,
                'enforced_entry_count': sum(enforced_source(p) for p in self.frozen_sources),
                'scope': 'Compiled src, linker.ld, and art/generator inputs; Markdown and credits documentation are excluded from enforcement. ROM and symbols are independently hash-authenticated.',
            }
        else:
            self.source_hash_artifact = 'current-source-hashes.json'
            paths = [p for directory in ('src', 'assets') for p in (ROOT / directory).rglob('*') if p.is_file()]
            paths.extend(p for p in (ROOT / 'linker.ld', ROOT / 'Makefile') if p.is_file())
            current = {str(p.relative_to(ROOT)): digest(p) for p in sorted(paths)}
            (self.out / self.source_hash_artifact).write_text(json.dumps(current, indent=2) + '\n')
            self.source_verification = {
                'status': 'unverified_against_binary', 'manifest_path': None,
                'current_checkout_entry_count': len(current),
                'scope': 'Current checkout source hashes only. No frozen build manifest was supplied or found beside the ROM, so these sources are explicitly unverified against the captured binary. ROM and symbol hashes remain mandatory and authenticated.',
            }
        shutil.copyfile(self.fixture, self.out / 'source-sky-clear.sav')
        shutil.copyfile(ROOT / 'tests/fixtures/v4/manifest.json', self.out / 'source-save-manifest.json')
        for p in (ROOT / 'tests/test_creatures.py', ROOT / 'tools/mgba_bridge.c', ROOT / 'tools/mgba_bridge.so'):
            self.test_sources[str(p.relative_to(ROOT))] = digest(p)
            shutil.copyfile(p, self.out / 'test-source' / p.name)
        self.emulator_core = core_metadata(self.e.lib)

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
        assert keys in (0, 'UP', 'DOWN', 'LEFT', 'RIGHT', 'R')
        self.inputs.append({'frame': self.e.frame, 'frames': int(n), 'keys': keys})
        self.capture_inputs.append({'frame_offset': self.recorded_frames, 'frames': int(n), 'keys': keys})
        for _ in range(n):
            self.e.frames(1, keys)
            state = self.get('game_state')
            assert self.get('room') == 22 and state == PLAY, 'Capture must stay in active opening-town play'
            assert self.get('spirit') == 0 and self.get('summoned'), 'Only base Homura may appear'
            assert not self.get('save_failed'), 'Never conceal a failed save'
            current_update = self.get('frame')
            current_page = self.e.read(0x04000000, 2) & 16
            rgb = self.e.screenshot().tobytes()
            row = {
                'frame_offset': self.recorded_frames, 'hardware_frame': self.e.frame,
                'update_delta': (current_update - self.last_update) & 0xffffffff,
                'page_flip': current_page != self.last_page,
                'render_cycles': self.get('render_cycles'), 'game_state': state,
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
        self.owned_select(1)
        self.ready()
        self.goto(240, 224)
        self.face(1)
        self.step(150)
        self.check(self.selected().form_id == 1 and self.command() == 1, 'Base Homura and its initial Fire command are selected')
        self.check(all(self.quest(q) == 0 for q in range(22)), 'No optional regional quest was prepared')
        self.check(not self.get('area_ticks') and not self.get('toast_ticks'), 'Opening frame is free of transient text')
        self.collection_before = self.collection()
        self.owned_before = [(c.instance_id, c.form_id) for c in self.live()]
        self.quest_bytes_before = bytes(self.state().quests)
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
        # Ordinary held D-pad walking, never per-frame teleportation or cuts.
        # Every pause, camera easing frame and Fire effect remains in the clip.
        self.step(90)
        self.preview('native-harbor')
        self.step(35, 'UP')
        self.step(135, 'LEFT')
        self.step(40)
        self.preview('native-quay-west')
        self.step(28, 'UP')
        self.step(130, 'RIGHT')
        self.step(38, 'UP')
        self.step(55)
        self.preview('native-quay-preview')
        self.tap('R', 2, 10)
        self.preview('native-homura-fire')
        self.step(60)
        self.step(36, 'DOWN')
        self.step(138, 'RIGHT')
        self.step(70)
        self.preview('native-quay-east')
        self.step(35, 'DOWN')
        self.step(130, 'LEFT')
        self.step(28, 'DOWN')
        self.face(1)
        assert self.recorded_frames < CAPTURE_FRAMES
        self.step(CAPTURE_FRAMES - self.recorded_frames)
        self.preview('native-final')

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
        self.check(self.get('chapter_flags') == 3, 'No Core completion or ending was introduced')
        self.check(self.selected().form_id == 1, 'Base Homura remains selected at the end')
        duration = self.recorded_frames / FPS
        self.check(15 <= duration <= 25, 'Continuous clip lasts 15 to 25 seconds')
        # No -shortest, trim, duplicated still, artificial audio or speed change.
        subprocess.run([
            'ffmpeg', '-y', '-i', str(self.out / 'silent.mp4'), '-i', str(self.out / 'native-psg.wav'),
            '-c:v', 'copy', '-c:a', 'aac', '-ar', '48000', '-b:a', '160k', '-movflags', '+faststart',
            str(self.out / 'hearthwake-native-teaser.mp4'),
        ], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        probe = json.loads(subprocess.check_output([
            'ffprobe', '-v', 'error', '-count_frames', '-show_streams', '-show_format', '-of', 'json',
            str(self.out / 'hearthwake-native-teaser.mp4'),
        ], text=True))
        video = next(s for s in probe['streams'] if s['codec_type'] == 'video')
        audio = next(s for s in probe['streams'] if s['codec_type'] == 'audio')
        self.check(int(video['nb_frames']) == int(video['nb_read_frames']) == self.recorded_frames, 'Mux and independent decoder preserve every native frame')
        self.check(Fraction(video['r_frame_rate']) == Fraction(FPS_RATIONAL), 'Mux preserves the exact hardware frame-rate ratio')
        self.check((video['width'], video['height']) == (960, 640), 'Player video is exactly four times native resolution')
        from PIL import Image
        self.check(all(Image.open(self.out / name).size == (240, 160) and hashlib.sha256(Image.open(self.out / name).tobytes()).hexdigest() == self.capture_trace[offset]['rgb_sha256'] for name, offset in self.preview_frames.items()), 'Every native preview is an unmodified frame from the continuous recording')
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
        source_save_manifest = json.loads((self.out / 'source-save-manifest.json').read_text())
        source_save = next(row for row in source_save_manifest['fixtures'] if row['file'] == 'sky-complete.sav')
        report = {
            'suite': 'northern-spoiler-free-native-teaser', **self.candidate,
            'controller_only': True, 'game_ram_writes': 0, 'machine_state_loads': 0,
            'capture_sram_reloads': 0, 'capture_cuts': 0, 'capture_reset_count': 0,
            'scope': 'Hearthwake Quay opening exterior, base Homura, ordinary walking and one harmless initial Fire cast. No recruits, evolutions, hidden routes, puzzle solutions, boss or ending.',
            'preparation': 'Hash-authenticated Sky-clear SRAM fresh boot, followed by ordinary controller travel through Grove and Reedhaven to the ferry. No prior-ROM machine state.',
            'source_save': {**source_save, 'fixture_path': str(self.fixture), 'verified_sha256': SKY_SHA},
            'source_verification': self.source_verification,
            'source_hashes_artifact': self.source_hash_artifact,
            'frozen_source_manifest_sha256': self.source_manifest_sha,
            'frozen_source_count': len(self.frozen_sources),
            'current_checkout_differences_from_build_manifest': self.source_comparison,
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
        names = ['hearthwake-native-teaser.mp4', 'native-frames.mkv', 'native-psg.wav',
                 'frame-trace.json', 'capture-start.sav', 'capture-end.sav',
                 'source-sky-clear.sav', 'source-save-manifest.json', self.source_hash_artifact] + list(self.preview_frames)
        report['files'] = {name: {'sha256': digest(self.out / name), 'bytes': (self.out / name).stat().st_size} for name in names}
        (self.out / 'capture.json').write_text(json.dumps(report, indent=2) + '\n')
        self.report()
        print(json.dumps({
            'video': str(self.out / 'hearthwake-native-teaser.mp4'),
            'preview': str(self.out / 'native-quay-preview.png'), 'frames': self.recorded_frames,
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
    parser.add_argument('--source-manifest', type=Path, help='Optional frozen source-hash manifest; defaults to source-hashes.json beside the ROM. Without one, checkout sources are recorded as unverified against the binary.')
    args = parser.parse_args()
    run = NorthernTeaser(args.rom, args.symbols, args.output, args.expected_rom_sha, args.expected_symbols_sha, source_manifest=args.source_manifest)
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
