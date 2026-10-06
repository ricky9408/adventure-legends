#!/usr/bin/env python3
"""Native Northern art, stable lookup, RGB555, ROM and stack contract tests.

These verify pixels and const data only, never acquisition or gameplay behavior.
Python 3 + Pillow, host C compiler, and the repository ARM toolchain are required.
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
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets/creatures'))
from catalog_source import load_catalog
SPEC=importlib.util.spec_from_file_location('test_northern_art_generator',ROOT/'assets/generate_northern_creatures.py')
ART=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(ART)

class NorthernCreatureArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='northern-art-tests-');cls.addClassCleanup(cls.temp.cleanup);cls.tmp=Path(cls.temp.name)
        cls.walks=[[[fn(d,f).im for f in range(4)] for d in ART.DIRECTIONS] for fn in ART.FIELD_FUNCTIONS]
        cls.casts=[[[fn(d,p).im for p in range(2)] for d in ART.DIRECTIONS] for fn in ART.ABILITY_FUNCTIONS]
        cls.portraits=[fn().im for fn in ART.PORTRAIT_FUNCTIONS]
        output=cls.tmp/'northern-art.so'
        subprocess.run([os.environ.get('CC','cc'),'-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-fPIC','-shared','-I'+str(ROOT/'src'),str(ROOT/'src/northern_creature_art.c'),'-o',str(output)],check=True)
        cls.lib=C.CDLL(str(output));cls.lib.northern_creature_art_index.argtypes=[C.c_uint];cls.lib.northern_creature_art_index.restype=C.c_int
        for name,n in (('frame',3),('ability_frame',3),('portrait',1)):
            fn=getattr(cls.lib,'northern_creature_art_'+name);fn.argtypes=[C.c_uint]*n;fn.restype=C.POINTER(C.c_ubyte)

    def all_images(self):
        return [im for forms in (self.walks,self.casts) for rows in forms for row in rows for im in row]+self.portraits

    def test_exact_sparse_form_identity_and_order(self):
        self.assertEqual(ART.FORM_IDS,(19,20,22,23,73,74,75,76,77,78))
        self.assertEqual(ART.DIRECTIONS,('down','up','left','right'))
        expected=('Spoolbud','Loomcrown','Cindertray','Kilnbarrow','Keelkip','Wakecradle','Cairncricket','Archspring','Rivetfoil','Gimbalcloak')
        self.assertEqual(ART.NAMES,expected)
        ids=(C.c_ubyte*10).in_dll(self.lib,'northern_creature_form_ids');self.assertEqual(bytes(ids),bytes(ART.FORM_IDS))
        catalog=load_catalog(ROOT/'assets/creatures/catalog.json')
        lock=json.loads((ROOT/'assets/creatures/identity-lock.json').read_text())
        self.assertTrue(lock)
        self.assertTrue(set(ART.FORM_IDS).issubset({f['id'] for f in catalog['forms']}))
        # Art ownership intentionally does not require or mutate enabled IDs.

    def test_exact_palette_rgb555_alpha_and_frame_sizes(self):
        self.assertEqual(len(ART.base.COLORS),178)
        for i,(name,color) in enumerate(ART.base.COLORS):
            rgb=tuple((int(color[k:k+2],16)>>3)*255//31 for k in (1,3,5));self.assertEqual(ART.RGB[i],rgb,name)
        self.assertEqual(len(self.all_images()),250)
        for im in self.all_images():
            self.assertEqual(im.mode,'P');self.assertEqual(im.getpalette(),ART.PAL)
            self.assertIn(0,im.tobytes());self.assertLess(max(im.tobytes()),97)
            self.assertEqual(im.getpixel((0,0)),0);self.assertEqual(im.getpixel((im.width-1,0)),0)
        for key in ART.KEYS:
            for suffix,size in (('walk',(64,64)),('ability',(32,64)),('portrait',(32,32))):
                with Image.open(ART.OUT/f'{key}_{suffix}.png') as im:
                    self.assertEqual(im.size,size);self.assertEqual(im.mode,'P');self.assertEqual(im.info.get('transparency'),0)
                    self.assertEqual(im.getpalette(),ART.PAL)
                    self.assertEqual(im.convert('RGBA').getchannel('A').tobytes(),bytes(255 if n else 0 for n in im.tobytes()))

    def test_four_articulated_walk_and_two_separate_cast_poses(self):
        for i,rows in enumerate(self.walks):
            for d,row in enumerate(rows):
                with self.subTest(form=ART.NAMES[i],direction=ART.DIRECTIONS[d]):
                    cast=self.casts[i][d]
                    self.assertTrue(all(im.size==(16,16) for im in row+cast))
                    self.assertEqual(len({im.tobytes() for im in row+cast}),6)
                    self.assertEqual(len({ART.mask(im).tobytes() for im in row}),4)
                    self.assertEqual(len({ART.mask(im).tobytes() for im in cast}),2)
                    for f in range(4):self.assertNotEqual(ART.mask(row[f]).tobytes(),ART.mask(row[(f+1)%4]).tobytes())
                    self.assertTrue(all(60<=sum(bool(n) for n in im.tobytes())<=215 for im in row+cast))

    def test_native_silhouettes_distinguish_directions_and_evolutions(self):
        self.assertEqual(len({ART.mask(rows[0][0]).tobytes() for rows in self.walks}),10)
        for i,rows in enumerate(self.walks):
            self.assertEqual(len({rows[d][0].tobytes() for d in range(4)}),4,ART.NAMES[i])
            self.assertEqual(len({ART.mask(rows[d][0]).tobytes() for d in range(4)}),4,ART.NAMES[i])
        for base in range(0,10,2):
            for d in range(4):
                before=ART.mask(self.walks[base][d][0]).tobytes();after=ART.mask(self.walks[base+1][d][0]).tobytes()
                self.assertGreater(sum(a!=b for a,b in zip(before,after)),30,(ART.NAMES[base],d))

    def test_expressive_front_faces_survive_all_poses(self):
        # Pupils must remain clear through gather/release, never overpainted by FX.
        anchors=((5,8,8),(6,8,10),(6,8,10),(6,8,11),(5,8,7),
                 (6,8,4),(5,8,10),(6,8,10),(5,8,6),(6,8,5))
        for i,(left,right,y) in enumerate(anchors):
            for f,im in enumerate(self.walks[i][0]):
                dy=(0,0,-1,0)[f]
                for x in (left,right):self.assertEqual(im.getpixel((x,y+dy)),ART.P['ink'],(ART.NAMES[i],f,x))
            for pose,im in enumerate(self.casts[i][0]):
                dy=(0,-1)[pose]
                for x in (left,right):self.assertEqual(im.getpixel((x,y+dy)),ART.P['ink'],(ART.NAMES[i],pose,x))
        # The folded bird's profile has a gold beak at the forward-most edge.
        for i in (8,9):
            for f,im in enumerate(self.walks[i][2]):self.assertEqual(im.getpixel((1,8+(0,0,-1,0)[f])),ART.P['gold3'])

    def test_evolved_negative_space_is_real_transparency(self):
        # The trellis/arch/cloak must stay open rather than becoming filled blobs.
        for i,box in ((1,(5,3,10,8)),(5,(3,6,12,11)),(7,(2,5,13,10)),(9,(7,11,9,13))):
            for im in self.walks[i][0]+self.casts[i][0]:
                self.assertGreaterEqual(sum(p==0 for p in im.crop(box).tobytes()),2,ART.NAMES[i])

    def test_separately_authored_native_portraits(self):
        for i,im in enumerate(self.portraits):
            self.assertEqual(im.size,(32,32));self.assertGreater(sum(bool(n) for n in im.tobytes()),250)
            self.assertNotEqual(im.tobytes(),self.walks[i][0][0].resize((32,32),Image.Resampling.NEAREST).tobytes())
        self.assertEqual(len({ART.mask(im).tobytes() for im in self.portraits}),10)

    def test_rom_bytes_match_authoring_and_pngs(self):
        for i,id in enumerate(ART.FORM_IDS):
            self.assertEqual(self.lib.northern_creature_art_index(id),i)
            self.assertEqual(C.string_at(self.lib.northern_creature_art_portrait(id),1024),self.portraits[i].tobytes())
            for suffix,frames,count,fn in (('walk',self.walks,4,self.lib.northern_creature_art_frame),('ability',self.casts,2,self.lib.northern_creature_art_ability_frame)):
                with Image.open(ART.OUT/f'{ART.KEYS[i]}_{suffix}.png') as sheet:
                    for d in range(4):
                        for f in range(count):
                            pixels=frames[i][d][f].tobytes()
                            self.assertEqual(C.string_at(fn(id,d,f),256),pixels)
                            self.assertEqual(sheet.crop((16*f,16*d,16*f+16,16*d+16)).tobytes(),pixels)

    def test_unsupported_ids_indices_and_unsigned_boundaries_fail_closed(self):
        # Includes reserved holes 21/24 and every stable byte ID, no subtraction map.
        for id in list(range(65536))+[0x7fffffff,0xffffffff]:
            if id in ART.FORM_IDS:continue
            self.assertEqual(self.lib.northern_creature_art_index(id),-1)
            self.assertFalse(self.lib.northern_creature_art_frame(id,0,0));self.assertFalse(self.lib.northern_creature_art_ability_frame(id,0,0));self.assertFalse(self.lib.northern_creature_art_portrait(id))
        for id in ART.FORM_IDS:
            for bad in (4,255,256,65535,0xffffffff):
                self.assertFalse(self.lib.northern_creature_art_frame(id,bad,0));self.assertFalse(self.lib.northern_creature_art_frame(id,0,bad));self.assertFalse(self.lib.northern_creature_art_ability_frame(id,bad,0))
            for bad in (2,3,255,0xffffffff):self.assertFalse(self.lib.northern_creature_art_ability_frame(id,0,bad))

    def test_exact_native_dark_light_and_actual_terrain_composites(self):
        with Image.open(ART.OUT/'native_dark_light.png') as source:
            preview=source.convert('RGB');self.assertEqual(preview.size,(720,438))
            for bg,yy in (('deep',25),('dirt4',230)):
                for i in range(10):
                    x=(i//2)*144;y=yy+(i%2)*100
                    for d in range(4):
                        for f,im in enumerate(self.walks[i][d]+self.casts[i][d]):
                            expected=Image.new('RGB',(16,16),ART.RGB[ART.P[bg]]);ART.paste(expected,im,(0,0))
                            self.assertEqual(preview.crop((x+2+16*f,y+20+16*d,x+18+16*f,y+36+16*d)).tobytes(),expected.tobytes())
            with Image.open(ART.OUT/'native_dark_light_2x.png') as zoom:self.assertEqual(zoom.convert('RGB').tobytes(),preview.resize((1440,876),Image.Resampling.NEAREST).tobytes())
        manifest=json.loads((ART.OUT/'manifest.json').read_text())
        with Image.open(ART.OUT/'scene_readability_native.png') as source:
            preview=source.convert('RGB');self.assertEqual(preview.size,(692,558))
            for t,terrain in enumerate(manifest['scene_review_sources']):
                path=ROOT/terrain['path'];self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(),terrain['sha256'])
                with Image.open(path) as bg:patch=bg.convert('RGB').crop(terrain['crop']).crop((4,4,28,28))
                for i in range(10):
                    for j,d in enumerate((0,2)):
                        for f,im in enumerate(self.walks[i][d]+self.casts[i][d]):
                            expected=patch.copy();ART.paste(expected,im,(4,4));x=114+t*192+f*30;y=48+i*50+j*24
                            self.assertEqual(preview.crop((x,y,x+24,y+24)).tobytes(),expected.tobytes())
        for path in ART.OUT.glob('*.png'):self.assertLess(path.stat().st_size,70000,path.name)

    def test_const_rom_arm_and_stack_budget(self):
        sizes={'northern_creature_form_ids':10,'northern_creature_direction_frames':40960,'northern_creature_ability_frames':20480,'northern_creature_portraits':10240}
        self.assertEqual(sum(sizes.values()),71690)
        arm=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc'
        if not arm.exists():
            found=shutil.which('arm-none-eabi-gcc');self.assertIsNotNone(found,'ARM toolchain missing; target budget not verified');arm=Path(found)
        obj=self.tmp/'northern-art.o'
        subprocess.run([str(arm),'-std=c99','-mcpu=arm7tdmi','-mthumb','-O2','-ffreestanding','-fno-builtin','-fstack-usage','-Wall','-Wextra','-Werror','-c',str(ROOT/'src/northern_creature_art.c'),'-o',str(obj)],check=True)
        output=subprocess.check_output([str(arm).replace('gcc','size'),str(obj)],text=True);rom,data,bss=map(int,output.splitlines()[-1].split()[:3])
        self.assertLessEqual(rom,73728);self.assertEqual((data,bss),(0,0))
        nm=subprocess.check_output([str(arm).replace('gcc','nm'),'-S','--size-sort',str(obj)],text=True)
        symbols={p[3]:(int(p[1],16),p[2]) for line in nm.splitlines() if len(p:=line.split())==4}
        for name,size in sizes.items():self.assertEqual(symbols[name],(size,'R'))
        stack=[int(line.split('\t')[1]) for p in self.tmp.glob('*.su') for line in p.read_text().splitlines()]
        self.assertTrue(stack);self.assertLessEqual(max(stack),24)
        for path in (ROOT/'src/northern_creature_art_data').glob('*.inc'):self.assertLess(path.stat().st_size,32000)

    def test_deterministic_generation_and_manifest(self):
        before=ART.output_hashes();manifest=ART.generate();self.assertEqual(before,ART.output_hashes())
        self.assertEqual(manifest['data_bytes'],71690);self.assertEqual(manifest['runtime_data_bytes'],0);self.assertEqual(manifest['runtime_bss_bytes'],0)
        self.assertEqual(manifest['palette_sha256'],hashlib.sha256(json.dumps(ART.base.COLORS).encode()).hexdigest())
        self.assertLess(manifest['max_include_bytes'],32000);self.assertIn('ART ONLY',manifest['status'])

if __name__=='__main__':unittest.main(verbosity=2)
