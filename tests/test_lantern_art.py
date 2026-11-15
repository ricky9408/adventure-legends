#!/usr/bin/env python3
"""The lantern cast stays legible, articulated and inside its existing GBA slots."""
import ctypes
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(ROOT / 'assets'))
import generate_assets as art


def silhouette(image):
    return bytes(bool(pixel) for pixel in image.tobytes())


class LanternArtTests(unittest.TestCase):
    def test_cast_uses_existing_native_actor_palette_and_transparency(self):
        images = [fn(direction, frame).im for fn in (art.hero, art.fox_direction, art.leaf_direction)
                  for direction in ('down', 'up', 'left', 'right') for frame in range(4)]
        images += [art.resident_sprite(region, name).im for region, people in art.characters.RESIDENTS.items()
                   for name in people]
        images += [art.flame(0).im, art.flame(1).im, art.projectile().im]
        for image in images:
            self.assertEqual(image.size, (16, 16))
            self.assertEqual(image.mode, 'P')
            self.assertEqual(image.getpalette(), art.PAL)
            self.assertIn(0, image.tobytes())
            self.assertLess(max(image.tobytes()), 97)
        self.assertEqual(art.golem().im.size, (32, 32))

    def test_each_walk_has_four_articulated_poses_and_four_facing_views(self):
        for fn in (art.hero, art.fox_direction, art.leaf_direction):
            with self.subTest(actor=fn.__name__):
                views = []
                for direction in ('down', 'up', 'left', 'right'):
                    images = [fn(direction, frame).im for frame in range(4)]
                    self.assertEqual(len({image.tobytes() for image in images}), 4)
                    self.assertEqual(len({silhouette(image) for image in images}), 4)
                    views.append(images[0].tobytes())
                self.assertEqual(len(set(views)), 4)

    def test_enemy_projectile_reads_the_same_in_every_firing_direction(self):
        image = art.projectile().im
        for turn in (Image.Transpose.ROTATE_90, Image.Transpose.ROTATE_180,
                     Image.Transpose.ROTATE_270):
            self.assertEqual(image.tobytes(), image.transpose(turn).tobytes())
        self.assertEqual(set(image.crop((7, 7, 9, 9)).tobytes()), {art.P['white']})

    def test_residents_in_each_place_are_distinguishable_without_color(self):
        for region, people in art.characters.RESIDENTS.items():
            with self.subTest(region=region):
                shapes = [silhouette(art.resident_sprite(region, name).im) for name in people]
                self.assertEqual(len(set(shapes)), len(people))

    def test_work_and_walking_poses_change_body_or_tool_silhouette(self):
        for region, name in [('magma', 'RESSA'), ('magma', 'NEMI'), ('magma', 'OMI'),
                             ('magma', 'TAVI'), ('magma', 'PELL'), ('underwater', 'KEEPER'),
                             ('underwater', 'SHELLWRIGHT'), ('return', 'GARDENER'),
                             ('return', 'PORTER'), ('horizons', 'HOST'), ('horizons', 'PORTER')]:
            self.assertNotEqual(silhouette(art.resident_sprite(region, name).im),
                                silhouette(art.resident_sprite(region, name, work=True).im))
        for name in ('WALKER', 'SEED_KEEPER', 'PASSENGER'):
            self.assertNotEqual(silhouette(art.resident_sprite('covenants', name, step=1).im),
                                silhouette(art.resident_sprite('covenants', name, step=2).im))

    def test_nature_companion_reads_green_instead_of_water_blue(self):
        green = {art.P[name] for name in ('pine0', 'pine1', 'pine2', 'pine3', 'pine4', 'pine5',
                                        'moss0', 'moss1', 'moss2', 'moss3', 'leaflight')}
        blue = {art.P[name] for name in ('blue0', 'blue1', 'blue2', 'blue3', 'water0', 'water1',
                                       'water2', 'water3', 'water4')}
        for direction in ('down', 'up', 'left', 'right'):
            pixels = art.leaf_direction(direction, 0).im.tobytes()
            self.assertGreater(sum(p in green for p in pixels), 35)
            self.assertFalse(any(p in blue for p in pixels))

    def test_title_reserves_quiet_planes_for_wordmark_and_controls(self):
        image = art.color_background(art.title(), 'title').im
        self.assertEqual(len(set(image.crop((40, 35, 204, 58)).tobytes())), 1)
        self.assertEqual(len(set(image.crop((46, 92, 196, 107)).tobytes())), 1)

    def test_shipped_core_arrays_match_authoring_without_expanding_slots(self):
        with tempfile.TemporaryDirectory(prefix='lantern-art-') as directory:
            library = Path(directory) / 'art.so'
            subprocess.run([os.environ.get('CC', 'cc'), '-std=c99', '-shared', '-fPIC',
                            str(ROOT / 'src/assets.c'), '-o', str(library)], check=True)
            compiled = ctypes.CDLL(str(library))
            hero = bytes((ctypes.c_ubyte * 4096).in_dll(compiled, 'hero_frames'))
            companions = bytes((ctypes.c_ubyte * 8192).in_dll(compiled, 'companion_direction_frames'))
            boss = bytes((ctypes.c_ubyte * 1024).in_dll(compiled, 'boss_data'))
            sprites = bytes((ctypes.c_ubyte * (len(art.SPR_NAMES) * 256)).in_dll(compiled, 'sprite_data'))
            self.assertEqual(hero, b''.join(art.hero(d, f).im.tobytes()
                                           for d in ('down', 'up', 'left', 'right') for f in range(4)))
            self.assertEqual(companions, b''.join(fn(d, f).im.tobytes()
                                                 for fn in (art.fox_direction, art.leaf_direction)
                                                 for d in ('down', 'up', 'left', 'right') for f in range(4)))
            self.assertEqual(boss, art.golem().im.tobytes())
            for name, image in [('PROJECTILE', art.projectile().im),
                                ('FLAME_0', art.flame(0).im), ('FLAME_1', art.flame(1).im)]:
                offset = art.SPR_NAMES.index(name) * 256
                self.assertEqual(sprites[offset:offset + 256], image.tobytes())


if __name__ == '__main__':
    unittest.main()
