import argparse
import ctypes as C
import gzip
import hashlib
import json
import random
import struct
import zlib
from pathlib import Path


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def png(path, rgb):
    def chunk(kind, data):
        return struct.pack('>I', len(data)) + kind + data + struct.pack('>I', zlib.crc32(kind + data))
    rows = b''.join(b'\0' + rgb[y * 720:(y + 1) * 720] for y in range(160))
    path.write_bytes(b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 240, 160, 8, 2, 0, 0, 0))
                     + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))


class Observation:
    def __init__(self, rom, symbols, bridge, output, earned_save=None):
        self.symbols = {words[2]: int(words[0], 16) for line in symbols.read_text().splitlines()
                        if len(words := line.split()) == 3}
        self.lib = C.CDLL(str(bridge))
        for name, args, result in (
            ('trust_open', [C.c_char_p, C.c_char_p], C.c_void_p),
            ('trust_close', [C.c_void_p], None),
            ('trust_step', [C.c_void_p, C.c_uint], None),
            ('trust_read', [C.c_void_p, C.c_uint32, C.c_uint], C.c_uint32),
            ('trust_faults', [C.c_void_p], C.c_uint),
            ('trust_rgb', [C.c_void_p, C.c_void_p], None),
            ('trust_library_path', [], C.c_char_p),
        ):
            method = getattr(self.lib, name)
            method.argtypes = args
            method.restype = result
        library = self.lib.trust_library_path()
        if not library:
            raise RuntimeError('Cannot identify the loaded mGBA library')
        self.library_path = Path(library.decode()).resolve()
        self.handle = self.lib.trust_open(str(rom).encode(), str(earned_save).encode() if earned_save else None)
        if not self.handle:
            raise RuntimeError('mGBA failed to open the candidate')
        self.frames = 0
        self.measured_frames = 0
        self.peak_cycles = 0
        self.output = output
        self.trace = gzip.open(output / 'frames.jsonl.gz', 'wt')

    def close(self):
        self.trace.close()
        self.lib.trust_close(self.handle)

    def get(self, name, width=4):
        return self.lib.trust_read(self.handle, self.symbols[name], width)

    def state(self):
        return {key: self.get(key) for key in ('game_state', 'room', 'px', 'py', 'hp', 'has_save', 'frame', 'render_cycles', 'render_profile_serial')}

    def sram(self):
        return bytes(self.lib.trust_read(self.handle, 0x0E000000 + offset, 1) for offset in range(32768))

    def step(self, count=1, keys=0, measured=True):
        for _ in range(count):
            previous = self.get('render_profile_serial')
            self.lib.trust_step(self.handle, keys)
            self.frames += 1
            current = self.state()
            self.trace.write(json.dumps({'hardware_frame': self.frames, 'keys': keys, 'measured': measured, **current}) + '\n')
            if self.lib.trust_faults(self.handle):
                raise AssertionError('The native core reported an error or crash')
            if measured:
                self.measured_frames += 1
                self.peak_cycles = max(self.peak_cycles, current['render_cycles'])
                if (current['render_profile_serial'] - previous) & 0xffffffff != 2:
                    raise AssertionError(f'A presented frame missed its game update: {current}')
                if current['render_cycles'] > 280896:
                    raise AssertionError(f'Frame exceeded the hardware cycle budget: {current}')
                if self.get('music_faults'):
                    raise AssertionError('Audio producer missed its deadline')

    def tap(self, keys):
        self.step(2, keys)
        self.step(3)

    def until(self, predicate, limit=1800):
        for _ in range(limit):
            if predicate():
                return
            self.step()
        raise AssertionError(f'Transition did not complete: {self.state()}')

    def settled(self):
        return self.get('game_state') == 1 and all(self.get(key) == 0 for key in (
            'save_requested', 'save_feedback_background', 'scene_present_phase'))

    def screenshot(self, name):
        pixels = (C.c_uint8 * (240 * 160 * 3))()
        self.lib.trust_rgb(self.handle, pixels)
        png(self.output / name, bytes(pixels))
        if len(set(bytes(pixels))) < 8:
            raise AssertionError('The native display is blank or degenerate')


def verify(rom, symbols, bridge, output):
    output.mkdir(parents=True, exist_ok=True)
    report = {'passed': False, 'rom_sha256': sha(rom), 'symbols_sha256': sha(symbols),
              'bridge_sha256': sha(bridge), 'checks': [], 'sessions': [],
              'game_ram_writes': 0, 'machine_state_imports': 0,
              'initial_progress': 'blank cartridge', 'physical_hardware': False}

    def check(condition, name):
        if not condition:
            raise AssertionError(name)
        report['checks'].append(name)

    def finish_session(session):
        report['sessions'].append({'name': session.output.name, 'frames': session.frames, 'measured_frames': session.measured_frames,
                                   'peak_cycles': session.peak_cycles})
        session.close()

    fresh = output / 'fresh'
    fresh.mkdir()
    session = Observation(rom, symbols, bridge, fresh)
    report['loaded_mgba'] = {'path': str(session.library_path), 'sha256': sha(session.library_path)}
    try:
        session.step(240, measured=False)
        check(session.get('game_state') == 0 and session.get('has_save') == 0, 'blank cartridge boots to title')
        session.screenshot('title.png')
        initial = session.sram()
        session.step(120, 1)
        check(session.get('game_state') == 14 and session.get('opening_page', 1) == 0,
              'held title A cannot skip or advance the opening')
        check(session.sram() == initial, 'an unfinished opening does not publish a save')
        session.step(4)
        session.step(120, 1)
        check(session.get('opening_page', 1) == 1, 'held A advances only one story page')
        session.screenshot('opening.png')
        session.step(4)
        session.tap(8)
        session.until(session.settled)
        session.step(30)
        check(session.get('has_save') == 1 and session.get('save_failed') == 0, 'completed opening durably saves')
        check(session.get('room') == 0, 'new adventure starts in the village')
        session.screenshot('village.png')
        initial_position = (session.get('px'), session.get('py'))
        saved = session.sram()
        session.tap(8)
        check(session.get('game_state') == 3, 'Start opens the journal')
        rng = random.Random(20261117)
        for _ in range(120):
            session.step(rng.randrange(1, 8), rng.choice((0, 16, 32, 64, 128)))
            check((session.get('px'), session.get('py')) == initial_position, 'journal navigation cannot move the player')
        session.screenshot('journal.png')
        session.tap(8)
        check(session.get('game_state') == 1 and session.sram() == saved, 'closing the journal preserves the save')
        for key, axis, direction in ((16, 'px', 1), (32, 'px', -1), (128, 'py', 1), (64, 'py', -1)):
            before = session.get(axis)
            session.step(8, key)
            after = session.get(axis)
            check((after - before) * direction > 0, f'directional input moves the player on {axis}')
            session.step(3)
        session.screenshot('movement.png')
        earned = output / 'earned.sav'
        earned.write_bytes(session.sram())
        report['earned_save_sha256'] = sha(earned)
    except Exception as error:
        report['error'] = str(error)
        session.screenshot('failure.png')
        raise
    finally:
        finish_session(session)
        (output / 'native.json').write_text(json.dumps(report, indent=2) + '\n')

    start_held = output / 'start-held'
    start_held.mkdir()
    session = Observation(rom, symbols, bridge, start_held)
    try:
        session.step(240, measured=False)
        check(session.get('game_state') == 0 and session.get('has_save') == 0,
              'Start-hold session independently boots a blank cartridge')
        initial = session.sram()
        session.step(120, 8)
        check(session.get('game_state') == 14 and session.get('opening_page', 1) == 0,
              'held title Start cannot skip or advance the opening')
        check(session.get('has_save') == 0 and session.sram() == initial,
              'held title Start cannot publish a save')
        session.screenshot('opening.png')
        session.step(4)
        check(session.get('game_state') == 14 and session.get('opening_page', 1) == 0
              and session.get('has_save') == 0 and session.sram() == initial,
              'releasing Start leaves the opening and blank save unchanged')
        session.tap(8)
        session.until(session.settled)
        session.step(30)
        check(session.get('game_state') == 1 and session.get('room') == 0,
              'a new Start press skips the opening into the village')
        check(session.get('has_save') == 1 and session.get('save_failed') == 0 and session.sram() != initial,
              'a new Start press publishes the completed opening save')
        session.screenshot('village.png')
    except Exception as error:
        report['error'] = str(error)
        session.screenshot('failure.png')
        raise
    finally:
        finish_session(session)
        (output / 'native.json').write_text(json.dumps(report, indent=2) + '\n')

    continued = output / 'continued'
    continued.mkdir()
    session = Observation(rom, symbols, bridge, continued, earned)
    try:
        session.step(240, measured=False)
        check(session.get('game_state') == 0 and session.get('has_save') == 1, 'cold boot recognizes the same-run earned save')
        session.tap(8)
        session.until(session.settled)
        check(session.get('game_state') == 1 and session.get('room') == 0, 'Continue reaches the saved village without replaying the opening')
        session.screenshot('continue.png')
        check(sha(earned) == report['earned_save_sha256'], 'Continue does not modify its input save file')
        report['passed'] = True
    except Exception as error:
        report['error'] = str(error)
        session.screenshot('failure.png')
        raise
    finally:
        finish_session(session)
        report['checks'] = list(dict.fromkeys(report['checks']))
        (output / 'native.json').write_text(json.dumps(report, indent=2) + '\n')
    return report


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--rom', type=Path, required=True)
    parser.add_argument('--symbols', type=Path, required=True)
    parser.add_argument('--bridge', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    report = verify(args.rom.resolve(), args.symbols.resolve(), args.bridge.resolve(), args.output.resolve())
    print(json.dumps({'passed': report['passed'], 'checks': len(report['checks']), 'sessions': report['sessions']}))


if __name__ == '__main__':
    main()
