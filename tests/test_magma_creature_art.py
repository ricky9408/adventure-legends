#!/usr/bin/env python3
"""Independent native Magma art contracts, pixels, and target budgets.

These are art-module tests. Passing does not establish gameplay integration,
acquisition, combat balance, live rendering, or a complete game-ROM budget.
Run: python3 -B -m unittest discover -s tests -p 'test_magma_creature_art.py' -v
"""
import ctypes as C
import hashlib
import importlib.util
import itertools
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile
import unittest

from PIL import Image

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
# This host target can run before any ROM/build target in a clean export.
(ROOT / 'build').mkdir(parents=True, exist_ok=True)
SOUTHERN = Path(os.environ.get("SOUTHERN_REFERENCE_ROOT", ROOT))
EXPECTED_IDS = tuple(range(31, 49)) + tuple(range(95, 101))
EXPECTED_DATA_BYTES = 172056
ROM_BUDGET_BYTES = 174080


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.path.insert(0, str(path.parent))
    try:
        spec.loader.exec_module(module)
    finally:
        sys.path.pop(0)
    return module


def silhouette(im):
    return bytes(255 if index else 0 for index in im.tobytes())


def normalized_silhouette(im):
    """Translation-invariant silhouette; transparent clipping cannot mask it."""
    mask = Image.frombytes("L", im.size, silhouette(im))
    bbox = mask.getbbox()
    if bbox is None:
        return (0, 0, b"")
    cropped = mask.crop(bbox)
    return (cropped.width, cropped.height, cropped.tobytes())


def compile_host(root, output):
    subprocess.run([os.environ.get("CC", "cc"), "-std=c99", "-O2", "-Wall",
                    "-Wextra", "-Werror", "-pedantic", "-fPIC", "-shared",
                    "-I" + str(root / "src"), str(root / "src/magma_creature_art.c"),
                    "-o", str(output)], check=True, capture_output=True, text=True)
    lib = C.CDLL(str(output))
    lib.magma_creature_art_index.argtypes = [C.c_uint]
    lib.magma_creature_art_index.restype = C.c_int
    for name, count in (("frame", 3), ("ability_frame", 3), ("portrait", 1)):
        fn = getattr(lib, "magma_creature_art_" + name)
        fn.argtypes = [C.c_uint] * count
        fn.restype = C.POINTER(C.c_ubyte)
    return lib


class MagmaCodegenContractTests(unittest.TestCase):
    """Exercise the emitter separately, without trusting the art generator."""

    @classmethod
    def setUpClass(cls):
        cls.codegen = load_module("magma_codegen_independent", ROOT / "assets/magma_codegen.py")
        cls.names = tuple(item["name"] for item in json.loads(
            (ROOT / "assets/magma_creature_briefs.json").read_text()))

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="magma-codegen-", dir=ROOT / "build")
        self.addCleanup(self.temp.cleanup)
        self.tmp = Path(self.temp.name)
        # Every leaf has a position-dependent marker, catching row/direction/
        # frame transposition independently of the authored art's own content.
        def im(size, n):
            image = Image.new("P", size, 0)
            image.putpixel((n % size[0], (n // size[0]) % size[1]), n % 177 + 1)
            return image
        self.fields = [[[im((16, 16), i * 16 + d * 4 + f)
                         for f in range(4)] for d in range(4)] for i in range(24)]
        self.abilities = [[[im((16, 16), i * 8 + d * 2 + p)
                           for p in range(2)] for d in range(4)] for i in range(24)]
        self.portraits = [im((32, 32), i * 37) for i in range(24)]

    def emit(self, **changes):
        arguments = dict(root=self.tmp, form_ids=EXPECTED_IDS, names=self.names,
                         fields=self.fields, abilities=self.abilities,
                         portraits=self.portraits)
        arguments.update(changes)
        return self.codegen.emit_code(**arguments)

    def test_emitter_compiles_and_every_tensor_leaf_round_trips(self):
        chunks = self.emit()
        lib = compile_host(self.tmp, self.tmp / "test.so")
        self.assertTrue(chunks)
        self.assertLessEqual(max(chunks), 30000)
        self.assertEqual(chunks, [p.stat().st_size for p in sorted(
            (self.tmp / "src/magma_creature_art_data").glob("part_*.inc"))])
        for i, form_id in enumerate(EXPECTED_IDS):
            self.assertEqual(lib.magma_creature_art_index(form_id), i)
            self.assertEqual(C.string_at(lib.magma_creature_art_portrait(form_id), 1024),
                             self.portraits[i].tobytes())
            for d in range(4):
                for f in range(4):
                    self.assertEqual(C.string_at(lib.magma_creature_art_frame(form_id, d, f), 256),
                                     self.fields[i][d][f].tobytes())
                for p in range(2):
                    self.assertEqual(C.string_at(lib.magma_creature_art_ability_frame(form_id, d, p), 256),
                                     self.abilities[i][d][p].tobytes())

    def test_bad_input_is_rejected_before_any_files_are_written(self):
        bad_fields = [row[:] for row in self.fields]
        bad_fields[0] = bad_fields[0][:-1]
        bad_image = Image.new("RGB", (16, 16))
        bad_portraits = self.portraits[:-1] + [Image.new("P", (16, 16))]
        bad_index = self.portraits[:-1] + [Image.new("P", (32, 32), 178)]
        cases = ({"form_ids": tuple(range(24))}, {"form_ids": EXPECTED_IDS[::-1]},
                 {"names": self.names[:-1]}, {"names": ("bad-name",) + self.names[1:]},
                 {"names": (self.names[1],) + self.names[1:]},
                 {"fields": bad_fields}, {"portraits": bad_portraits},
                 {"portraits": bad_index},
                 {"fields": [[[bad_image] * 4] * 4] * 24})
        for case in cases:
            with self.subTest(case=list(case)):
                with self.assertRaises(ValueError):
                    self.emit(**case)
                self.assertEqual(list(self.tmp.iterdir()), [])

    def test_emitter_determinism_and_precise_stale_chunk_cleanup(self):
        self.emit()
        src = self.tmp / "src"
        before = {p.relative_to(src): p.read_bytes() for p in src.rglob("*") if p.is_file()}
        data = src / "magma_creature_art_data"
        (data / "part_999.inc").write_text("stale generated output")
        (data / "caller_owned.txt").write_text("keep")
        self.emit()
        self.assertFalse((data / "part_999.inc").exists())
        self.assertEqual((data / "caller_owned.txt").read_text(), "keep")
        for path, content in before.items():
            self.assertEqual((src / path).read_bytes(), content)


class MagmaCreatureArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.art = load_module("magma_art_under_test", ROOT / "assets/generate_magma_creatures.py")
        cls.temp = tempfile.TemporaryDirectory(prefix="magma-art-tests-", dir=ROOT / "build")
        cls.addClassCleanup(cls.temp.cleanup)
        cls.tmp = Path(cls.temp.name)
        cls.walks = [[[cls.art.field(form_id, d, f) for f in range(4)]
                      for d in cls.art.DIRECTIONS] for form_id in EXPECTED_IDS]
        cls.casts = [[[cls.art.field(form_id, d, p, cast=p) for p in range(2)]
                      for d in cls.art.DIRECTIONS] for form_id in EXPECTED_IDS]
        cls.portraits = [cls.art.portrait(form_id) for form_id in EXPECTED_IDS]
        cls.lib = compile_host(ROOT, cls.tmp / "magma_art.so")

    def all_images(self):
        return [im for tensor in (self.walks, self.casts) for form in tensor
                for direction in form for im in direction] + self.portraits

    def test_exact_ids_names_direction_order_and_const_id_table(self):
        self.assertEqual(self.art.FORM_IDS, EXPECTED_IDS)
        self.assertEqual(self.art.DIRECTIONS, ("down", "up", "left", "right"))
        briefs = json.loads((ROOT / "assets/magma_creature_briefs.json").read_text())
        self.assertEqual(tuple(b["id"] for b in briefs), EXPECTED_IDS)
        self.assertEqual(tuple(self.art.NAMES), tuple(b["name"] for b in briefs))
        self.assertEqual(tuple(self.art.KEYS), tuple(n.lower() for n in self.art.NAMES))
        self.assertEqual(bytes((C.c_ubyte * 24).in_dll(self.lib, "magma_creature_form_ids")),
                         bytes(EXPECTED_IDS))

    def test_every_palette_slot_matches_actual_southern_game_palette(self):
        source = (SOUTHERN / "src/asset_data/part_000.inc").read_text()
        match = re.search(r"const unsigned short game_palette\[256\]\s*=\s*\{([^}]+)\}", source)
        self.assertIsNotNone(match)
        native = [int(n, 0) for n in re.findall(r"0x[0-9a-fA-F]+|\d+", match.group(1))]
        self.assertEqual(len(native), 256)
        rgb = [((n & 31) * 255 // 31, ((n >> 5) & 31) * 255 // 31,
                ((n >> 10) & 31) * 255 // 31) for n in native]
        self.assertEqual(list(self.art.RGB), rgb)
        self.assertEqual(self.art.PAL, [component for color in rgb for component in color])
        self.assertEqual(len(self.art.base.COLORS), 178)
        self.assertEqual(self.art.P["transparent"], 0)
        self.assertEqual(self.art.P["ink"], 1)

    def test_all_six_hundred_images_have_native_dimensions_and_transparency(self):
        images = self.all_images()
        self.assertEqual(len(images), 600)
        for n, im in enumerate(images):
            with self.subTest(image=n):
                self.assertEqual(im.mode, "P")
                self.assertEqual(im.getpalette(), self.art.PAL)
                self.assertEqual(im.size, (32, 32) if n >= 576 else (16, 16))
                self.assertIn(0, im.tobytes())
                # Creature colors remain in the original actor slots; later
                # Southern scenery ramps must not silently recolor companions.
                self.assertLess(max(im.tobytes()), 97)
                self.assertGreater(sum(bool(p) for p in im.tobytes()), 35)

    def test_indexed_pngs_preserve_all_palette_entries_and_alpha(self):
        for key in self.art.KEYS:
            for suffix, size in (("walk", (64, 64)), ("ability", (32, 64)),
                                 ("portrait", (32, 32))):
                with self.subTest(key=key, suffix=suffix):
                    with Image.open(self.art.OUT / f"{key}_{suffix}.png") as im:
                        self.assertEqual(im.size, size)
                        self.assertEqual(im.mode, "P")
                        self.assertEqual(im.getpalette(), self.art.PAL)
                        self.assertEqual(im.info.get("transparency"), 0)
                        self.assertEqual(im.convert("RGBA").getchannel("A").tobytes(),
                                         bytes(255 if p else 0 for p in im.tobytes()))

    def test_authored_geometry_never_relies_on_implicit_canvas_clipping(self):
        original = self.art.Art
        errors = []
        current = None

        class CheckedArt(original):
            def check(self, points):
                errors.extend((current, x, y) for x, y in points
                              if x < 0 or y < 0 or x >= self.im.width or y >= self.im.height)

            def p(self, points, color):
                self.check(points)
                super().p(points, color)

            def l(self, points, color, width=1):
                self.check(points)
                super().l(points, color, width)

            def e(self, box, color):
                self.check(((box[0], box[1]), (box[2], box[3])))
                super().e(box, color)

            def r(self, box, color):
                self.check(((box[0], box[1]), (box[2], box[3])))
                super().r(box, color)

            def dot(self, x, y, color):
                self.check(((x, y),))
                super().dot(x, y, color)

        self.art.Art = CheckedArt
        try:
            for form_id in EXPECTED_IDS:
                for d in self.art.DIRECTIONS:
                    for f in range(6):
                        current = (form_id, d, f)
                        self.art.field(form_id, d, f if f < 4 else f - 4,
                                       cast=None if f < 4 else f - 4)
                current = (form_id, "portrait")
                self.art.portrait(form_id)
        finally:
            self.art.Art = original
        self.assertEqual(errors, [])

    def test_all_rom_accessors_match_pngs_and_authored_pixels(self):
        for i, form_id in enumerate(EXPECTED_IDS):
            self.assertEqual(self.lib.magma_creature_art_index(form_id), i)
            self.assertEqual(C.string_at(self.lib.magma_creature_art_portrait(form_id), 1024),
                             self.portraits[i].tobytes())
            with Image.open(self.art.OUT / f"{self.art.KEYS[i]}_portrait.png") as im:
                self.assertEqual(im.tobytes(), self.portraits[i].tobytes())
            for suffix, frames, count, accessor in (
                    ("walk", self.walks, 4, self.lib.magma_creature_art_frame),
                    ("ability", self.casts, 2, self.lib.magma_creature_art_ability_frame)):
                with Image.open(self.art.OUT / f"{self.art.KEYS[i]}_{suffix}.png") as sheet:
                    for d in range(4):
                        for f in range(count):
                            expected = frames[i][d][f].tobytes()
                            self.assertEqual(C.string_at(accessor(form_id, d, f), 256), expected)
                            self.assertEqual(sheet.crop((16*f, 16*d, 16*f+16, 16*d+16)).tobytes(), expected)

    def test_unknown_ids_and_unsigned_negative_inputs_are_safely_rejected(self):
        for form_id in itertools.chain(range(65536), (-1, -2, -31, -95, -2**31,
                                                     2**31-1, 2**31, 2**32-1)):
            if form_id in EXPECTED_IDS:
                continue
            self.assertEqual(self.lib.magma_creature_art_index(form_id), -1, form_id)
            self.assertFalse(self.lib.magma_creature_art_frame(form_id, 0, 0), form_id)
            self.assertFalse(self.lib.magma_creature_art_ability_frame(form_id, 0, 0), form_id)
            self.assertFalse(self.lib.magma_creature_art_portrait(form_id), form_id)
        bad = (-1, -2, -256, -2**31, 4, 5, 255, 256, 65535, 2**31, 2**32-1)
        for form_id in EXPECTED_IDS:
            for value in bad:
                self.assertFalse(self.lib.magma_creature_art_frame(form_id, value, 0))
                self.assertFalse(self.lib.magma_creature_art_frame(form_id, 0, value))
                self.assertFalse(self.lib.magma_creature_art_ability_frame(form_id, value, 0))
            for value in (2, 3) + bad:
                self.assertFalse(self.lib.magma_creature_art_ability_frame(form_id, 0, value))

    def test_four_articulated_walk_contours_and_two_unique_casts_per_direction(self):
        for i, form_id in enumerate(EXPECTED_IDS):
            for d in range(4):
                with self.subTest(form=form_id, direction=self.art.DIRECTIONS[d]):
                    walk, casts = self.walks[i][d], self.casts[i][d]
                    self.assertEqual(len({im.tobytes() for im in walk + casts}), 6)
                    self.assertEqual(len({silhouette(im) for im in walk}), 4)
                    self.assertEqual(len({silhouette(im) for im in casts}), 2)
                    # Four cropped silhouettes must remain unique after removing
                    # offsets. This rejects palette flicker and translated poses.
                    self.assertEqual(len({normalized_silhouette(im) for im in walk}), 4)
                    self.assertEqual(len({normalized_silhouette(im) for im in casts}), 2)

    def test_material_rim_preserves_alpha_native_palette_and_bilateral_profiles(self):
        for i, form_id in enumerate(EXPECTED_IDS):
            low, _, author = next(item for item in self.art.FAMILY_FUNCTIONS
                                  if item[0] <= form_id <= item[1])
            for d in self.art.DIRECTIONS:
                for pose in range(6):
                    frame, cast = (pose, None) if pose < 4 else (pose-4, pose-4)
                    source = author(form_id-low, d, frame, cast)
                    before = source.tobytes()
                    rimmed = self.art.material_rim(source, form_id, d)
                    with self.subTest(form=form_id, direction=d, pose=pose):
                        self.assertEqual(source.tobytes(), before, "Rim mutated its input")
                        self.assertEqual(rimmed.mode, "P")
                        self.assertEqual(rimmed.size, (16,16))
                        self.assertEqual(rimmed.getpalette(), source.getpalette())
                        self.assertEqual(silhouette(source), silhouette(rimmed))
                        self.assertEqual(self.art.field(form_id, d, frame, cast=cast).tobytes(),
                                         rimmed.tobytes())
                        changed = [(old,new) for old,new in zip(before,rimmed.tobytes()) if old != new]
                        self.assertTrue(changed)
                        color = self.art.P[self.art.RIM_COLORS[i]]
                        self.assertLess(color, 97)
                        self.assertTrue(all(old == self.art.P["ink"] and new == color
                                            for old,new in changed))
            for frames in (self.walks[i], self.casts[i]):
                for left,right in zip(frames[2],frames[3]):
                    self.assertEqual(left.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes(),
                                     right.tobytes(), form_id)

    def test_every_form_has_distinct_direction_pixels_and_front_silhouette(self):
        self.assertEqual(len({silhouette(form[0][0]) for form in self.walks}), 24)
        for form_id, walk, cast in zip(EXPECTED_IDS, self.walks, self.casts):
            for frames in (walk, cast):
                self.assertEqual(len({direction[0].tobytes() for direction in frames}), 4, form_id)
                for down, up in zip(frames[0], frames[1]):
                    self.assertNotEqual(down.tobytes(), up.tobytes(), form_id)

    def test_evolution_and_sibling_branch_silhouettes_are_different(self):
        edges = ((31,32),(32,33),(34,35),(35,36),(37,38),(37,39),
                 (40,41),(40,42),(43,44),(43,45),(46,47),(46,48),
                 (95,96),(97,98),(99,100))
        branches = ((38,39),(41,42),(44,45),(47,48))
        for left, right in edges + branches:
            i, j = EXPECTED_IDS.index(left), EXPECTED_IDS.index(right)
            for d in range(4):
                a, b = silhouette(self.walks[i][d][0]), silhouette(self.walks[j][d][0])
                with self.subTest(pair=(left, right), direction=d):
                    self.assertGreaterEqual(sum(x != y for x, y in zip(a,b)), 18)

    def test_released_comparison_preserves_all_sixty_five_native_silhouettes(self):
        fixture = ROOT / "assets/review_terrain/released41_silhouettes_native.png"
        original = SOUTHERN / "assets/southern_creatures/prior21_silhouettes_native.png"
        self.assertEqual(fixture.read_bytes(), original.read_bytes())
        prior = json.loads((ROOT / "assets/review_terrain/released41_ids.json").read_text())["form_ids"]
        self.assertEqual(tuple(prior), (1,2,4,5,7,8,10,11,13,14,16,19,20,22,23,
                                       73,74,75,76,77,78,25,26,28,29,
                                       79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94))
        old_fronts = []
        with Image.open(fixture) as image:
            source = image.convert("RGB")
        with Image.open(self.art.OUT / "released65_silhouettes_native.png") as image:
            comparison = image.convert("RGB")
        self.assertEqual(comparison.size, (560,444))
        ink = bytes(self.art.RGB[self.art.P["ink"]])
        for i, form_id in enumerate(prior + list(EXPECTED_IDS)):
            for d in range(4):
                if i < len(prior):
                    sx, sy = (i%7)*80+4+d*18, 35+(i//7)*42
                    rgb = source.crop((sx,sy,sx+16,sy+16)).tobytes()
                    pixels = bytes(255 if rgb[k:k+3] == ink else 0
                                   for k in range(0, len(rgb), 3))
                    if d == 0:
                        old_fronts.append(pixels)
                else:
                    pixels = silhouette(self.walks[i-len(prior)][d][0])
                expected = Image.new("RGB", (16,16), self.art.RGB[self.art.P["white"]])
                expected.paste(Image.new("RGB", (16,16), tuple(ink)), (0,0),
                               Image.frombytes("L", (16,16), pixels))
                x, y = (i%7)*80+4+d*18, 36+(i//7)*42
                self.assertEqual(comparison.crop((x,y,x+16,y+16)).tobytes(),
                                 expected.tobytes(), (form_id,d))
        self.assertEqual(len(old_fronts), 41)
        current = {silhouette(form[0][0]) for form in self.walks}
        self.assertFalse(current.intersection(old_fronts))
        report = json.loads((self.art.OUT / "manifest.json").read_text())["silhouette_comparison"]
        self.assertEqual(report["released_form_ids"], prior)
        self.assertEqual(report["cross_release_front_mask_matches"], 0)

    def test_portraits_are_independently_composed_and_not_scaled_fields(self):
        self.assertEqual(len({silhouette(im) for im in self.portraits}), 24)
        self.assertEqual(len({normalized_silhouette(im) for im in self.portraits}), 24)
        for i, portrait in enumerate(self.portraits):
            self.assertEqual(portrait.size, (32, 32))
            self.assertGreater(sum(bool(n) for n in portrait.tobytes()), 200)
            for d in range(4):
                for frame in self.walks[i][d] + self.casts[i][d]:
                    self.assertNotEqual(portrait.tobytes(), frame.resize((32,32), Image.Resampling.NEAREST).tobytes())

    @staticmethod
    def compose(background, sprite, xy):
        result = background.copy()
        result.paste(sprite.convert("RGB"), xy,
                     Image.frombytes("L", sprite.size, silhouette(sprite)))
        return result

    def terrain_sources(self):
        manifest = json.loads((self.art.OUT / "manifest.json").read_text())
        sources = manifest["scene_review_sources"]
        expected = (("GRASS", "frondshore_commons.png", [276,262,300,286]),
                    ("WATER", "sunlace_anchorage.png", [32,287,56,311]),
                    ("PLASTER", "sunlace_anchorage.png", [40,96,64,120]),
                    ("WOOD", "awning_loft.png", [136,120,160,144]))
        self.assertGreaterEqual(len(sources), len(expected))
        self.assertEqual(len({source["terrain"] for source in sources}), len(sources))
        for source, (terrain, filename, crop) in zip(sources, expected):
            self.assertEqual(source["terrain"], terrain)
            self.assertEqual(source["path"], "assets/review_terrain/" + filename)
            self.assertEqual(source["crop"], crop)
        patches = []
        for source in sources:
            filename = Path(source["path"]).name
            crop = source["crop"]
            self.assertEqual(source["path"], "assets/review_terrain/" + filename)
            self.assertEqual(len(crop), 4)
            self.assertEqual((crop[2]-crop[0], crop[3]-crop[1]), (24,24))
            path = ROOT / source["path"]
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), source["sha256"])
            # Validate against the actual preserved Southern source as well,
            # rather than accepting a mutually changed copy/hash manifest.
            originals = [p for p in (SOUTHERN / "assets/southern_region" / filename,
                                     SOUTHERN / "assets" / filename) if p.exists()]
            self.assertTrue(originals, "Southern source is missing: " + filename)
            self.assertTrue(any(path.read_bytes() == original.read_bytes() for original in originals),
                            "Copied terrain does not match Southern: " + filename)
            with Image.open(path) as im:
                self.assertGreaterEqual(crop[0], 0)
                self.assertGreaterEqual(crop[1], 0)
                self.assertLessEqual(crop[2], im.width)
                self.assertLessEqual(crop[3], im.height)
                patches.append(im.convert("RGB").crop(crop))
        return sources, patches

    def test_terrain_contact_sheets_are_exact_native_sprite_composites(self):
        sources, patches = self.terrain_sources()
        for i, key in enumerate(self.art.KEYS):
            with Image.open(self.art.OUT / f"{key}_terrain_native.png") as original:
                sheet = original.convert("RGB")
                self.assertEqual(sheet.size, (144*len(sources),112))
                for t, patch in enumerate(patches):
                    for d in range(4):
                        for f, im in enumerate(self.walks[i][d] + self.casts[i][d]):
                            expected = self.compose(patch, im, (4,4))
                            x, y = t*144 + f*24, 16 + d*24
                            self.assertEqual(sheet.crop((x,y,x+24,y+24)).tobytes(),
                                             expected.tobytes(), (key,sources[t]["terrain"],d,f))

    def test_native_contact_previews_and_motion_gifs_match_exact_pixels(self):
        manifest = json.loads((self.art.OUT / "manifest.json").read_text())
        self.assertEqual(len(self.art.WALK_TICKS), 24)
        for i, key in enumerate(self.art.KEYS):
            with Image.open(self.art.OUT / f"{key}_native.png") as original:
                sheet = original.convert("RGB")
                self.assertEqual(sheet.size, (240,166))
                for bg, y in (("deep",24), ("dirt4",100)):
                    for d in range(4):
                        for f, sprite in enumerate(self.walks[i][d] + self.casts[i][d]):
                            expected = self.compose(Image.new("RGB", (16,16),
                                                    self.art.RGB[self.art.P[bg]]), sprite, (0,0))
                            x, yy = 4 + f*30, y + d*16
                            self.assertEqual(sheet.crop((x,yy,x+16,yy+16)).tobytes(),
                                             expected.tobytes(), (key,bg,d,f))
                expected = self.compose(Image.new("RGB", (32,32),
                                        self.art.RGB[self.art.P["deep"]]), self.portraits[i], (0,0))
                self.assertEqual(sheet.crop((204,28,236,60)).tobytes(), expected.tobytes())
            with Image.open(self.art.OUT / f"{key}_motion.gif") as gif:
                self.assertEqual(gif.size, (128,48))
                self.assertEqual(gif.n_frames, 6)
                self.assertEqual(gif.info.get("loop"), 0)
                ticks = self.art.WALK_TICKS[i]
                self.assertEqual(len(ticks), 4)
                self.assertTrue(all(isinstance(n,int) and n > 0 for n in ticks))
                self.assertEqual(manifest["walk_ticks_by_form"][str(EXPECTED_IDS[i])], list(ticks))
                # GIF stores hundredths of a second; its integer 60Hz preview
                # durations round down to the next 10ms unit on serialization.
                durations = [(n*1000//60)//10*10 for n in ticks] + [240,220]
                for frame, duration in enumerate(durations):
                    gif.seek(frame)
                    self.assertEqual(gif.info["duration"], duration)
                    shown = gif.convert("RGB")
                    for d in range(4):
                        sprite = (self.walks[i][d] + self.casts[i][d])[frame]
                        expected = self.compose(Image.new("RGB", (16,16),
                                                self.art.RGB[self.art.P["dirt4"]]), sprite, (0,0))
                        x = 8 + d*30
                        self.assertEqual(shown.crop((x,23,x+16,39)).tobytes(),
                                         expected.tobytes(), (key,d,frame))

    def test_native_fullscreen_composites_and_roster_animation_have_no_scaling(self):
        sources, _ = self.terrain_sources()
        for source in sources:
            with Image.open(ROOT / source["path"]) as original:
                scene = original.convert("RGB").crop((0,0,240,160))
            for i in range(24):
                scene = self.compose(scene, self.walks[i][i%4][0],
                                     (10+(i%6)*38,24+(i//6)*32))
            with Image.open(self.art.OUT / f'fullscreen_{source["terrain"].lower()}_native.png') as actual:
                self.assertEqual(actual.size, (240,160))
                self.assertEqual(actual.convert("RGB").tobytes(), scene.tobytes())
        with Image.open(ROOT / sources[0]["path"]) as original:
            scene = original.convert("RGB").crop((0,0,240,160))
        with Image.open(self.art.OUT / "roster_walk_native.gif") as gif:
            self.assertEqual(gif.size, (240,160))
            self.assertEqual(gif.n_frames, 4)
            for f in range(4):
                gif.seek(f)
                expected = scene.copy()
                for i in range(24):
                    expected = self.compose(expected, self.walks[i][i%4][f],
                                            (10+(i%6)*38,24+(i//6)*32))
                self.assertEqual(gif.convert("RGB").tobytes(), expected.tobytes(), f)
        with Image.open(self.art.OUT / "roster_native.png") as native:
            with Image.open(self.art.OUT / "roster_2x.png") as doubled:
                self.assertEqual(doubled.size, (960,576))
                self.assertEqual(doubled.convert("RGB").tobytes(),
                                 native.convert("RGB").resize((960,576), Image.Resampling.NEAREST).tobytes())
        credits = (self.art.OUT / "CREDITS.txt").read_text()
        self.assertIn("art composites", credits)
        self.assertIn("never emulator evidence or acquisition proof", credits)

    def test_terrain_readability_report_recomputes_from_all_native_pixels(self):
        sources, patches = self.terrain_sources()
        report = json.loads((self.art.OUT / "terrain_readability.json").read_text())
        self.assertEqual(report["samples"], 24*24*len(sources))
        expected = []
        for i, form_id in enumerate(EXPECTED_IDS):
            for t, patch in enumerate(patches):
                visible_ratios, boundary_ratios = [], []
                for directions in (self.walks[i], self.casts[i]):
                    for direction in directions:
                        for sprite in direction:
                            pixels = sprite.tobytes()
                            visible = boundary_visible = boundary_count = 0
                            opaque = sum(bool(p) for p in pixels)
                            for y in range(16):
                                for x in range(16):
                                    index = pixels[y*16+x]
                                    if not index:
                                        continue
                                    color = self.art.RGB[index]
                                    background = patch.getpixel((x+4,y+4))
                                    distinct = sum((a-b)**2 for a,b in zip(color,background)) >= 48**2
                                    visible += distinct
                                    neighbors = ((x-1,y),(x+1,y),(x,y-1),(x,y+1))
                                    boundary = any(not (0<=xx<16 and 0<=yy<16) or
                                                   pixels[yy*16+xx] == 0 for xx,yy in neighbors)
                                    if boundary:
                                        boundary_count += 1
                                        boundary_visible += distinct
                            visible_ratios.append(visible/opaque)
                            boundary_ratios.append(boundary_visible/boundary_count)
                expected.append({"form_id":form_id, "terrain":sources[t]["terrain"],
                                 "minimum_distinct_opaque_fraction":round(min(visible_ratios),4),
                                 "minimum_distinct_boundary_fraction":round(min(boundary_ratios),4)})
        self.assertEqual(report["rows"], expected)
        opaque = min(row["minimum_distinct_opaque_fraction"] for row in expected)
        boundary = min(row["minimum_distinct_boundary_fraction"] for row in expected)
        self.assertEqual(report["minimum_opaque_fraction"], opaque)
        self.assertEqual(report["minimum_boundary_fraction"], boundary)
        # Conservative regression floors, not a claim of uniform contrast or
        # readability in gameplay; the exact per-form/per-terrain rows remain
        # available for judging the visibly harder dark-scene samples.
        self.assertGreaterEqual(opaque, 0.40)
        self.assertGreaterEqual(boundary, 0.35)
        manifest = json.loads((self.art.OUT / "manifest.json").read_text())
        self.assertEqual(manifest["terrain_visibility_minimum_opaque"], opaque)
        self.assertEqual(manifest["terrain_visibility_minimum_boundary"], boundary)

    def test_const_arm_rom_stack_and_no_external_runtime_dependencies(self):
        arm = ROOT / "tools/sysroot/usr/bin/arm-none-eabi-gcc"
        if not arm.exists():
            found = shutil.which("arm-none-eabi-gcc")
            self.assertIsNotNone(found, "ARM target budget is unverified: compiler is absent")
            arm = Path(found)
        obj = self.tmp / "magma_art.o"
        subprocess.run([str(arm), "-std=c99", "-mcpu=arm7tdmi", "-mthumb", "-O2",
                        "-ffreestanding", "-fno-builtin", "-fstack-usage", "-Wall",
                        "-Wextra", "-Werror", "-c", str(ROOT / "src/magma_creature_art.c"),
                        "-o", str(obj)], check=True, capture_output=True, text=True)
        sizes = subprocess.check_output([str(arm).replace("gcc", "size"), str(obj)], text=True)
        rom, data, bss = map(int, sizes.splitlines()[-1].split()[:3])
        self.assertGreaterEqual(rom, EXPECTED_DATA_BYTES)
        self.assertLessEqual(rom, ROM_BUDGET_BYTES)
        self.assertEqual((data,bss), (0,0))
        nm = subprocess.check_output([str(arm).replace("gcc", "nm"), "-S", "--size-sort", str(obj)], text=True)
        symbols = {parts[3]: (int(parts[1],16), parts[2]) for line in nm.splitlines()
                   if len(parts := line.split()) == 4}
        expected = {"magma_creature_form_ids":24, "magma_creature_direction_frames":98304,
                    "magma_creature_ability_frames":49152, "magma_creature_portraits":24576}
        self.assertEqual(sum(expected.values()), EXPECTED_DATA_BYTES)
        for name, size in expected.items():
            self.assertEqual(symbols[name], (size, "R"))
        self.assertFalse(any(kind in "BbDdCc" for _, kind in symbols.values()))
        undefined = subprocess.check_output([str(arm).replace("gcc", "nm"), "-u", str(obj)], text=True)
        self.assertEqual(undefined.strip(), "")
        sections = subprocess.check_output([str(arm).replace("gcc", "objdump"), "-h", str(obj)], text=True)
        self.assertNotIn("iwram", sections.lower())
        self.assertNotIn("ewram", sections.lower())
        stack = [int(line.split("\t")[1]) for path in self.tmp.glob("*.su")
                 for line in path.read_text().splitlines()]
        self.assertEqual(len(stack), 4)
        self.assertLessEqual(max(stack), 24)
        header = (ROOT / "src/magma_creature_art.h").read_text()
        self.assertIn("signed", header)
        self.assertIn("clipping", header)
        for p in (ROOT / "src/magma_creature_art_data").glob("*.inc"):
            self.assertLessEqual(p.stat().st_size, 30000, p.name)

    def test_deterministic_cli_verify_and_manifest_budget_evidence(self):
        before = self.art.output_hashes()
        completed = subprocess.run(
            [sys.executable, "-B", str(ROOT / "assets/generate_magma_creatures.py"), "--verify"],
            cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(completed.returncode, 0, completed.stdout + completed.stderr)
        self.assertEqual(before, self.art.output_hashes())
        manifest = json.loads((self.art.OUT / "manifest.json").read_text())
        self.assertEqual(manifest["data_bytes"], EXPECTED_DATA_BYTES)
        for key in ("runtime_data_bytes", "runtime_bss_bytes", "persistent_obj_allocation_bytes"):
            self.assertEqual(manifest[key], 0)
        self.assertIn("ART ONLY", manifest["status"])
        self.assertEqual(manifest["palette_sha256"], hashlib.sha256(
            json.dumps(self.art.base.COLORS).encode()).hexdigest())
        self.assertLessEqual(manifest["max_include_bytes"], 30000)
        report = json.loads((self.art.OUT / "validation.json").read_text())
        self.assertTrue(report["deterministic_regeneration"])
        self.assertEqual(report["output_sha256"], self.art.output_hashes())
        self.assertEqual(report["arm_compile"], "passed")
        self.assertLessEqual(report["arm_rom_object_bytes"], ROM_BUDGET_BYTES)
        self.assertEqual(report["arm_data_bytes"], 0)
        self.assertEqual(report["arm_bss_bytes"], 0)
        self.assertLessEqual(report["max_arm_stack_bytes"], 24)


if __name__ == "__main__":
    unittest.main(verbosity=2)
