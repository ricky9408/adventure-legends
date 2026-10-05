#!/usr/bin/env python3
"""Host-simulated integration regression for save-failure feedback.

Run: python3 tests/test_save_feedback.py

Compiles actual game/source modules into a temporary host library and exercises
only the hardware-independent save and puzzle paths. No emulator, game-RAM
injection, real SRAM, or repository build outputs are used. The previous valid
checkpoint must survive a failed write without a misleading success toast.
"""
import ctypes as C
import json
import os
import shlex
from pathlib import Path
import re
import subprocess
import tempfile

root = Path(__file__).resolve().parents[1]


class CampaignSave(C.Structure):
    _fields_ = [
        ('room', C.c_ubyte), ('spawn', C.c_ubyte),
        ('chapter_flags', C.c_ubyte), ('bridge', C.c_ubyte),
        ('torches', C.c_ubyte), ('relic', C.c_ubyte), ('camp', C.c_ubyte),
        ('room_flags', C.c_uint), ('optional_flags', C.c_ubyte),
        ('story_seen', C.c_ushort), ('spirit', C.c_ubyte),
        ('sequence', C.c_uint), ('loaded_version', C.c_ubyte),
    ]


with tempfile.TemporaryDirectory(prefix='emberbond-save-feedback-') as temp:
    library = Path(temp) / 'game-host.so'
    modules = ['game', 'assets', 'ui', 'world', 'campaign_art', 'campaign_rules', 'save4']
    # Unexecuted GBA render functions contain 32-bit hardware address casts.
    subprocess.run(shlex.split(os.environ.get('HOST_CC', 'cc')) + [
        '-shared', '-fPIC', '-O0', '-std=c99', '-fno-builtin',
        '-Wno-attributes', '-Wno-pointer-to-int-cast', '-Wno-int-to-pointer-cast',
        '-DSAVE4_HOST_TEST', '-Dmain=gba_main',
        *[str(root / 'src' / (name + '.c')) for name in modules],
        '-o', str(library),
    ], check=True)
    lib = C.CDLL(str(library))
    lib.save4_load.argtypes = [C.POINTER(CampaignSave)]
    lib.save4_load.restype = C.c_int
    lib.save4_test_fail_after.argtypes = [C.c_int]
    lib.save4_test_write_count.restype = C.c_uint
    lib.campaign_power.restype = C.c_int

    def get(name):
        return C.c_int.in_dll(lib, name).value

    def load():
        result = CampaignSave()
        assert lib.save4_load(C.byref(result)) == 1
        return {name: getattr(result, name) for name, _ in CampaignSave._fields_}

    sram = (C.c_ubyte * 256).in_dll(lib, 'save4_test_sram')
    sram[:] = bytes([255]) * 256
    # Valid room-7 checkpoint before the left relay: Grove clear, bridge,
    # vane and patrol complete, wind join seen, wind companion selected.
    initial = {
        'room': 7, 'checkpoint_spawn': 0, 'chapter_flags': 1,
        'room_flags': 7, 'story_seen': 2, 'spirit': 2, 'px': 56, 'py': 112,
    }
    for name, value in initial.items():
        C.c_int.in_dll(lib, name).value = value

    lib.save4_test_fail_after(-1)
    lib.save_game()
    assert get('save_failed') == 0
    assert lib.save4_test_write_count() == 33
    before_sram = bytes(sram)
    before_save = load()
    assert (before_save['room'], before_save['room_flags'], before_save['sequence']) == (7, 7, 1)

    lib.save4_test_fail_after(0)
    assert lib.campaign_power() == 1
    after_save = load()
    ui_ids = list(dict.fromkeys(re.findall(
        r'\bTX_[A-Z0-9_]+\b', (root / 'src/ui.h').read_text())))
    toast_name = ui_ids[get('toast_id')]
    result = {
        'save_failed': get('save_failed'), 'toast': toast_name,
        'toast_ticks': get('toast_ticks'), 'live_room_flags': get('room_flags'),
        'write_count': lib.save4_test_write_count(),
        'SRAM_unchanged': bytes(sram) == before_sram,
        'loaded_room_flags': after_save['room_flags'],
        'loaded_sequence': after_save['sequence'],
        'previous_save_preserved': after_save == before_save,
    }
    print(json.dumps(result, indent=2), flush=True)
    assert result['save_failed'] == 1
    assert result['live_room_flags'] == 15
    assert result['write_count'] == 0
    assert result['SRAM_unchanged']
    assert result['previous_save_preserved']
    # Regression expectation: keep save_at's error toast instead of replacing
    # it with a success toast for the relay activation that was not persisted.
    assert toast_name == 'TX_C_SAVE_FAILED', ('failed save displayed ' + toast_name)

    # A later successful checkpoint clears the error and records the live flag.
    lib.save4_test_fail_after(-1)
    lib.save_game()
    recovered = load()
    assert get('save_failed') == 0
    assert lib.save4_test_write_count() == 33
    assert (recovered['room_flags'], recovered['sequence']) == (15, 2)
    print('PASS: failed puzzle save retains error feedback and prior checkpoint; retry persists progress')
