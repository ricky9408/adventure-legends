#!/usr/bin/env python3
"""Compile/exported C parity, exhaustive bad-index contract and deterministic source."""
from pathlib import Path
import ctypes
import hashlib
import importlib.util
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/covenants-art-host'
OUT.mkdir(parents=True, exist_ok=True)
paths = sorted((ROOT / 'src/covenants_creature_art_data').glob('*.inc'))
paths += [ROOT / 'src/covenants_creature_art.c', ROOT / 'src/covenants_creature_art.h',
          ROOT / 'assets/covenants_creatures/manifest.json']
before = {p: p.read_bytes() for p in paths}
subprocess.run(['python3', 'assets/generate_covenants_creatures.py'], cwd=ROOT, check=True)
assert all(p.read_bytes() == value for p, value in before.items())
assert all(p.stat().st_size < 30000 for p in paths if p.suffix == '.inc')
so = OUT / 'art.so'
subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-pedantic',
                '-shared', '-fPIC', '-Isrc', 'src/covenants_creature_art.c', '-o', str(so)], cwd=ROOT, check=True)
lib = ctypes.CDLL(str(so))
for name in ('frame', 'cast_frame', 'portrait'):
    getattr(lib, 'covenants_creature_art_' + name).restype = ctypes.POINTER(ctypes.c_ubyte)
spec = importlib.util.spec_from_file_location('source_kit', ROOT / 'assets/covenants_creatures/source/generate_covenant_art.py')
kit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(kit)
walk, cast, portraits = kit.tensors()
pixel_bytes = b''
for index, form in enumerate(range(121, 129)):
    assert lib.covenants_creature_art_index(form) == index
    for direction in range(4):
        for frame in range(4):
            data = bytes(lib.covenants_creature_art_frame(form, direction, frame)[:256])
            assert data == walk[index][direction][frame].tobytes()
            pixel_bytes += data
        for pose in range(3):
            assert bytes(lib.covenants_creature_art_cast_frame(form, direction, pose)[:256]) == cast[index][direction][pose].tobytes()
    assert bytes(lib.covenants_creature_art_portrait(form)[:1024]) == portraits[index].tobytes()
    expected = [frame for frame in range(4) for _ in range(kit.WALK_TICKS[index][frame])]
    assert [lib.covenants_creature_art_walk_index(form, t) for t in range(len(expected)*3)] == expected*3
    for bad in (4, 5, 255, 256, 0x7fffffff, 0xffffffff):
        assert not lib.covenants_creature_art_frame(form, bad, 0)
        assert not lib.covenants_creature_art_frame(form, 0, bad)
        assert not lib.covenants_creature_art_cast_frame(form, bad, 0)
        assert not lib.covenants_creature_art_cast_frame(form, 0, bad)
    assert not lib.covenants_creature_art_cast_frame(form, 0, 3)
for form in [*range(121), *range(129, 513), 0xffffffff]:
    assert lib.covenants_creature_art_index(form) == -1
    assert not lib.covenants_creature_art_frame(form, 0, 0)
    assert not lib.covenants_creature_art_cast_frame(form, 0, 0)
    assert not lib.covenants_creature_art_portrait(form)
    assert lib.covenants_creature_art_walk_index(form, 100) == 0
report = {'scope': 'immutable native indexed data; actual ROM motion/controller acquisition unverified',
          'images': 232, 'dimensions': {'walk': [8, 4, 4, 256], 'cast': [8, 4, 3, 256], 'portrait': [8, 1024]},
          'pixel_validation': kit.validate(walk, cast, portraits), 'deterministic': True,
          'compiled_pixel_parity': True, 'authored_gait_periods': [sum(row) for row in kit.WALK_TICKS],
          'negative_index_contract': True,
          'source_sha256': {str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}}
assert report['pixel_validation']['passed']
(OUT / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
print('232 compiled native images match the original kit; all invalid IDs/indices rejected;8 authored gait periods and deterministic regeneration passed')
