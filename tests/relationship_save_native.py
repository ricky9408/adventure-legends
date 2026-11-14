#!/usr/bin/env python3
"""Prepared relationship ledger: controller travel/save and cold Continue.
The input ledger is synthetic, not evidence of playable relationship scenes.
No game-RAM writes or machine-state imports are used.
"""
import argparse
import ctypes as C
import json
from pathlib import Path
from cold_continue_native import ControllerNative, codec, sha, ROOT
from test_save5 import Save


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('rom', 'symbols', 'bridge', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    a = p.parse_args(); a.output.mkdir(parents=True, exist_ok=False)
    sources = json.loads((a.rom.parent / 'source-hashes.json').read_text())
    assert all(sha(ROOT / name) == digest for name, digest in sources.items())
    symbols = {v[2]: int(v[0], 16) for line in a.symbols.read_text().splitlines() if len(v := line.split()) == 3}
    lib = codec(a.output); s = Save()
    assert lib.creatures_migrate_legacy(C.byref(s.roster), 0, 0) == 1
    lib.equipment_init(C.byref(s.equipment)); s.relationships[:] = [31, 15, 7, 3]
    lib.sram[:] = b'\xff' * 32768
    assert lib.save5_store(C.byref(s)) == 1
    prepared = a.output / 'synthetic-input.sav'; prepared.write_bytes(bytes(lib.sram))
    events = bytes(s.relationships); trace = []; engine = None

    def g(name):
        return engine.read(symbols[name], 4)

    def step(keys=0):
        engine.frames(1, keys)
        trace.append({'keys': keys, 'room': g('room'), 'state': g('game_state'),
                      'save_requested': g('save_requested'), 'background': g('save_feedback_background')})

    def wait(test, limit=1800):
        for _ in range(limit):
            if test(): return
            step()
        raise AssertionError(('timeout', trace[-1]))

    def open_save(path):
        nonlocal engine
        engine = ControllerNative(a.rom.resolve(), a.bridge.resolve())
        engine.load_save(path); engine.reset()
        wait(lambda: g('game_state') == 0 and g('has_save') == 1)
        step('A'); step()
        wait(lambda: g('game_state') == 1 and not g('scene_present_phase'))
        wait(lambda: not g('save_requested') and not g('save_feedback_background'))
        state = Save.from_buffer_copy(engine.bytes(symbols['adventure_save'], C.sizeof(Save)))
        assert bytes(state.relationships) == events

    result = {'result': 'RUNNING', 'synthetic_ledger': list(events), 'rom_sha256': sha(a.rom),
              'symbols_sha256': sha(a.symbols), 'source_manifest_sha256': sha(a.rom.parent / 'source-hashes.json'),
              'bridge_sha256': sha(a.bridge), 'game_ram_writes': 0, 'machine_state_imports': 0}
    try:
        open_save(prepared)
        first_room = g('room'); before = engine.bytes(0x0e000000, 32768)
        for _ in range(500):
            if g('room') != first_room: break
            step('UP')
        assert g('room') != first_room, ('road was not crossed', trace[-1])
        step(); wait(lambda: not g('scene_present_phase'))
        wait(lambda: not g('save_requested') and not g('save_feedback_background'))
        after = engine.bytes(0x0e000000, 32768)
        assert after != before, 'travel must actually write a new save'
        lib.sram[:] = after; saved = Save()
        assert lib.save5_load(C.byref(saved)) == 1
        assert bytes(saved.relationships) == events
        engine.screenshot(a.output / 'after-travel.png')
        resumed = a.output / 'controller-saved.sav'; engine.save(resumed)
        assert engine.lib.eb_faults(engine.ptr) == 0
        engine.close(); engine = None
        open_save(resumed)
        engine.screenshot(a.output / 'cold-continue.png')
        assert engine.lib.eb_faults(engine.ptr) == 0
        result.update(result='PASS', frames=len(trace), save_sha256=sha(resumed))
    except Exception:
        result['result'] = 'FAIL'
        raise
    finally:
        if engine: engine.close()
        (a.output / 'inputs.json').write_text(json.dumps(trace, indent=2) + '\n')
        (a.output / 'report.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
