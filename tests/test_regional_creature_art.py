#!/usr/bin/env python3
"""Native pixel/ROM/API tests for the regional art-only module.

No emulator state injection, gameplay surrogate, asset downloads, or new colors.
Run directly with Python 3 + Pillow, a host C compiler, and the ARM toolchain.
"""
import ctypes as C
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from PIL import Image

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets/creatures'))
from catalog_source import load_catalog
SPEC = importlib.util.spec_from_file_location('regional_art_test_generator', ROOT / 'assets/generate_regional_creatures.py')
ART = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(ART)


class RegionalCreatureArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix='regional-art-tests-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.tmp = Path(cls.temp.name)
        cls.walks = [[[fn(d, f).im for f in range(4)] for d in ART.DIRECTIONS] for fn in ART.FIELD_FUNCTIONS]
        cls.abilities = [[[fn(d, f).im for f in range(2)] for d in ART.DIRECTIONS] for fn in ART.ABILITY_FUNCTIONS]
        cls.portraits = [fn().im for fn in ART.PORTRAIT_FUNCTIONS]
        output = cls.tmp / 'regional-art.so'
        subprocess.run([os.environ.get('CC', 'cc'), '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-pedantic', '-fPIC', '-shared', '-I' + str(ROOT / 'src'), str(ROOT / 'src/regional_creature_art.c'), '-o', str(output)], check=True)
        cls.lib = C.CDLL(str(output))
        cls.lib.regional_creature_art_index.argtypes = [C.c_uint]
        cls.lib.regional_creature_art_index.restype = C.c_int
        for name, count in (('frame', 3), ('ability_frame', 3), ('portrait', 1)):
            fn = getattr(cls.lib, 'regional_creature_art_' + name)
            fn.argtypes = [C.c_uint] * count
            fn.restype = C.POINTER(C.c_ubyte)

    def all_images(self):
        return [im for forms in (self.walks, self.abilities) for rows in forms for row in rows for im in row] + self.portraits

    def test_catalog_identity(self):
        self.assertEqual(ART.FORM_IDS, (13, 14, 16))
        self.assertEqual(ART.DIRECTIONS, ('down', 'up', 'left', 'right'))
        catalog = load_catalog(ROOT / 'assets/creatures/catalog.json')
        names = {form['id']: form['name'] for form in catalog['forms']}
        self.assertEqual([names[i] for i in ART.FORM_IDS], list(ART.NAMES))
        ids = (C.c_ubyte * 3).in_dll(self.lib, 'regional_creature_form_ids')
        self.assertEqual(bytes(ids), bytes(ART.FORM_IDS))

    def test_native_palette_indices_rgb555_and_alpha(self):
        for i, (name, source) in enumerate(ART.base.COLORS):
            rgb = tuple((int(source[k:k + 2], 16) >> 3) * 255 // 31 for k in (1, 3, 5))
            self.assertEqual(ART.RGB[i], rgb, name)
        for im in self.all_images():
            self.assertEqual(im.mode, 'P')
            self.assertEqual(im.getpalette(), ART.PAL)
            self.assertIn(0, im.tobytes())
            self.assertLess(max(im.tobytes()), 97)
            self.assertEqual(im.getpixel((0, 0)), 0)
            self.assertEqual(im.getpixel((im.width - 1, 0)), 0)
        for key in ART.KEYS:
            for suffix, size in (('walk', (64, 64)), ('ability', (32, 64)), ('portrait', (32, 32))):
                with Image.open(ART.OUT / f'{key}_{suffix}.png') as im:
                    self.assertEqual(im.mode, 'P')
                    self.assertEqual(im.size, size)
                    self.assertEqual(im.info.get('transparency'), 0)
                    self.assertEqual(im.getpalette(), ART.PAL)
                    self.assertEqual(im.convert('RGBA').getchannel('A').tobytes(), bytes(255 if n else 0 for n in im.tobytes()))

    def test_four_walk_poses_and_two_additional_ability_poses(self):
        for i, rows in enumerate(self.walks):
            for d, row in enumerate(rows):
                with self.subTest(form=ART.FORM_IDS[i], direction=d):
                    self.assertTrue(all(im.size == (16, 16) for im in row + self.abilities[i][d]))
                    self.assertEqual(len({im.tobytes() for im in row}), 4)
                    self.assertGreaterEqual(len({ART.mask(im).tobytes() for im in row}), 3)
                    self.assertEqual(len({im.tobytes() for im in row + self.abilities[i][d]}), 6)
                    self.assertEqual(len({ART.mask(im).tobytes() for im in self.abilities[i][d]}), 2)
                    # No all-color shimmer standing in for articulated motion.
                    for f in range(4):
                        self.assertNotEqual(ART.mask(row[f]).tobytes(), ART.mask(row[(f + 1) % 4]).tobytes())

    def test_directions_and_forms_have_distinct_silhouettes(self):
        for i, rows in enumerate(self.walks):
            self.assertEqual(len({rows[d][0].tobytes() for d in range(4)}), 4, ART.NAMES[i])
            self.assertEqual(len({ART.mask(rows[d][0]).tobytes() for d in range(4)}), 4, ART.NAMES[i])
        self.assertEqual(len({ART.mask(rows[0][0]).tobytes() for rows in self.walks}), 3)
        # Distinctive water hoop and metal loop contain actual transparent gaps.
        for i, rows in enumerate(self.walks):
            for f, im in enumerate(rows[0]):
                lift = (0, 0, -1, 0)[f]
                if i == 1:
                    self.assertEqual(im.getpixel((7, 4 + lift)), 0)
                    self.assertEqual(im.getpixel((8, 4 + lift)), 0)
                if i == 2:
                    self.assertEqual(im.getpixel((7, 3 + lift)), 0)
                    self.assertEqual(im.getpixel((8, 3 + lift)), 0)

    def test_front_faces_stay_visible_in_walk_and_ability_poses(self):
        # Fixed face anchors catch an accidentally overpainted wheel or effect.
        for i, y in enumerate((7, 9, 7)):
            for f, im in enumerate(self.walks[i][0]):
                lift = (0, 0, -1, 0)[f]
                for x in (6, 9): self.assertEqual(im.getpixel((x, y + lift)), ART.P['ink'])
            lifts = (-1, 0) if i == 0 else (0, -1) if i == 1 else (1, -1)
            for f, im in enumerate(self.abilities[i][0]):
                for x in (6, 9): self.assertEqual(im.getpixel((x, y + lifts[f])), ART.P['ink'])

    def test_portraits_are_separately_authored(self):
        for i, portrait in enumerate(self.portraits):
            self.assertEqual(portrait.size, (32, 32))
            self.assertNotEqual(portrait.tobytes(), self.walks[i][0][0].resize((32, 32), Image.Resampling.NEAREST).tobytes())
            self.assertGreater(sum(bool(n) for n in portrait.tobytes()), 250)

    def test_native_preview_has_unobscured_one_to_one_pixels(self):
        with Image.open(ART.OUT / 'native_dark_light.png') as preview:
            self.assertEqual(preview.size, (432, 222))
            for bg, yy in (('deep', 27), ('dirt4', 124)):
                for i in range(3):
                    for d in range(4):
                        for f, im in enumerate(self.walks[i][d] + self.abilities[i][d]):
                            x = i * 144 + (3 + f * 16 if f < 4 else 71 + (f - 4) * 16)
                            y = yy + 20 + d * 16
                            expected = Image.new('RGB', (16, 16), ART.RGB[ART.P[bg]])
                            ART.paste(expected, im, (0, 0))
                            self.assertEqual(preview.crop((x, y, x + 16, y + 16)).tobytes(), expected.tobytes())
                    x, y = i * 144 + 108, yy + 23
                    expected = Image.new('RGB', (32, 32), ART.RGB[ART.P[bg]])
                    ART.paste(expected, self.portraits[i], (0, 0))
                    self.assertEqual(preview.crop((x, y, x + 32, y + 32)).tobytes(), expected.tobytes())
            with Image.open(ART.OUT / 'native_dark_light_3x.png') as zoom:
                self.assertEqual(zoom.tobytes(), preview.resize((1296, 666), Image.Resampling.NEAREST).tobytes())

    def test_rom_pixels_match_native_authoring_and_png_sheets(self):
        for i, form_id in enumerate(ART.FORM_IDS):
            self.assertEqual(self.lib.regional_creature_art_index(form_id), i)
            pointer = self.lib.regional_creature_art_portrait(form_id)
            self.assertEqual(C.string_at(pointer, 1024), self.portraits[i].tobytes())
            for suffix, frames, count, fn in (('walk', self.walks, 4, self.lib.regional_creature_art_frame), ('ability', self.abilities, 2, self.lib.regional_creature_art_ability_frame)):
                with Image.open(ART.OUT / f'{ART.KEYS[i]}_{suffix}.png') as sheet:
                    for d in range(4):
                        for f in range(count):
                            expected = frames[i][d][f].tobytes()
                            self.assertEqual(C.string_at(fn(form_id, d, f), 256), expected)
                            self.assertEqual(sheet.crop((f * 16, d * 16, f * 16 + 16, d * 16 + 16)).tobytes(), expected)

    def test_unsupported_ids_and_indices_fail_closed(self):
        # Test the byte form-ID space plus unsigned-overflow boundary values.
        for form_id in list(range(1024)) + [65535, 65536, 0x7fffffff, 0xffffffff]:
            if form_id in ART.FORM_IDS: continue
            self.assertEqual(self.lib.regional_creature_art_index(form_id), -1)
            self.assertFalse(self.lib.regional_creature_art_frame(form_id, 0, 0))
            self.assertFalse(self.lib.regional_creature_art_ability_frame(form_id, 0, 0))
            self.assertFalse(self.lib.regional_creature_art_portrait(form_id))
        for form_id in ART.FORM_IDS:
            for bad in (4, 255, 256, 65535, 0xffffffff):
                self.assertFalse(self.lib.regional_creature_art_frame(form_id, bad, 0))
                self.assertFalse(self.lib.regional_creature_art_ability_frame(form_id, bad, 0))
                self.assertFalse(self.lib.regional_creature_art_frame(form_id, 0, bad))
            for bad in (2, 3, 255, 0xffffffff):
                self.assertFalse(self.lib.regional_creature_art_ability_frame(form_id, 0, bad))

    def test_const_data_and_arm_budget(self):
        sizes = {'regional_creature_form_ids': 3, 'regional_creature_direction_frames': 12288,
                 'regional_creature_ability_frames': 6144, 'regional_creature_portraits': 3072}
        self.assertEqual(sum(sizes.values()), 21507)
        arm = ROOT / 'tools/sysroot/usr/bin/arm-none-eabi-gcc'
        if not arm.exists():
            found = shutil.which('arm-none-eabi-gcc')
            self.assertIsNotNone(found, 'ARM toolchain missing; target budget not verified')
            arm = Path(found)
        obj = self.tmp / 'regional-art.o'
        subprocess.run([str(arm), '-std=c99', '-mcpu=arm7tdmi', '-mthumb', '-O2', '-ffreestanding', '-fno-builtin', '-Wall', '-Wextra', '-Werror', '-c', str(ROOT / 'src/regional_creature_art.c'), '-o', str(obj)], check=True)
        size = subprocess.check_output([str(arm).replace('gcc', 'size'), str(obj)], text=True)
        text, data, bss = map(int, size.splitlines()[-1].split()[:3])
        self.assertLessEqual(text, 22528)
        self.assertEqual((data, bss), (0, 0))
        nm = subprocess.check_output([str(arm).replace('gcc', 'nm'), '-S', '--size-sort', str(obj)], text=True)
        symbols = {p[3]: (int(p[1], 16), p[2]) for line in nm.splitlines() if len(p := line.split()) == 4}
        for name, expected in sizes.items(): self.assertEqual(symbols[name], (expected, 'R'))
        for chunk in (ROOT / 'src/regional_creature_art_data').glob('*.inc'):
            self.assertLessEqual(chunk.stat().st_size, 32000)

    def test_deterministic_regeneration_and_manifest(self):
        before = ART.output_hashes()
        manifest = ART.generate()
        self.assertEqual(before, ART.output_hashes())
        self.assertEqual(manifest['data_bytes'], 21507)
        self.assertEqual(manifest['runtime_data_bytes'], 0)
        self.assertEqual(manifest['runtime_bss_bytes'], 0)
        self.assertEqual(manifest['palette_sha256'], hashlib.sha256(json.dumps(ART.base.COLORS).encode()).hexdigest())
        self.assertLessEqual(manifest['max_include_bytes'], 32000)
        self.assertIn('ART ONLY', manifest['status'])


if __name__ == '__main__': unittest.main(verbosity=2)
