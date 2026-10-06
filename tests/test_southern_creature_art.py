#!/usr/bin/env python3
"""Native Southern pixel/lookup budgets. Art evidence, never acquisition proof."""
import ctypes as C
import hashlib, importlib.util, json, os, shutil, subprocess, sys, tempfile, unittest
from pathlib import Path
from PIL import Image, ImageChops
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets/creatures'))
from catalog_source import load_catalog
SPEC=importlib.util.spec_from_file_location('test_southern_art',ROOT/'assets/generate_southern_creatures.py')
ART=importlib.util.module_from_spec(SPEC);SPEC.loader.exec_module(ART)
class SouthernCreatureArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='southern-art-tests-');cls.addClassCleanup(cls.temp.cleanup);cls.tmp=Path(cls.temp.name)
        cls.walks=[[[fn(d,f).im for f in range(4)] for d in ART.DIRECTIONS] for fn in ART.FIELD_FUNCTIONS]
        cls.casts=[[[fn(d,p).im for p in range(2)] for d in ART.DIRECTIONS] for fn in ART.ABILITY_FUNCTIONS]
        cls.portraits=[fn().im for fn in ART.PORTRAIT_FUNCTIONS]
        out=cls.tmp/'art.so';subprocess.run([os.environ.get('CC','cc'),'-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-fPIC','-shared','-I'+str(ROOT/'src'),str(ROOT/'src/southern_creature_art.c'),'-o',str(out)],check=True)
        cls.lib=C.CDLL(str(out));cls.lib.southern_creature_art_index.argtypes=[C.c_uint];cls.lib.southern_creature_art_index.restype=C.c_int
        for name,n in (('frame',3),('ability_frame',3),('portrait',1)):
            fn=getattr(cls.lib,'southern_creature_art_'+name);fn.argtypes=[C.c_uint]*n;fn.restype=C.POINTER(C.c_ubyte)
    def all_images(self):return [im for forms in (self.walks,self.casts) for row in forms for d in row for im in d]+self.portraits
    def test_exact_twenty_fixed_ids_names_and_order(self):
        self.assertEqual(ART.FORM_IDS,(25,26,28,29,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94))
        self.assertEqual(ART.DIRECTIONS,('down','up','left','right'))
        self.assertEqual(bytes((C.c_ubyte*20).in_dll(self.lib,'southern_creature_form_ids')),bytes(ART.FORM_IDS))
        catalog={f['id']:f for f in load_catalog(ROOT/'assets/creatures/catalog.json')['forms']}
        for id,name in zip(ART.FORM_IDS,ART.NAMES):self.assertEqual(catalog[id]['name'],name)
        # Art has no dependency on a particular enablement/acquisition state.
    def test_exact_rgb555_palette_transparency_and_dimensions(self):
        self.assertEqual(len(ART.base.COLORS),178);self.assertEqual(len(self.all_images()),500)
        for i,(name,color) in enumerate(ART.base.COLORS):self.assertEqual(ART.RGB[i],tuple((int(color[k:k+2],16)>>3)*255//31 for k in (1,3,5)),name)
        for im in self.all_images():
            self.assertEqual(im.mode,'P');self.assertEqual(im.getpalette(),ART.PAL);self.assertIn(0,im.tobytes());self.assertLess(max(im.tobytes()),97)
            self.assertIn(im.size,((16,16),(32,32)))
        for key in ART.KEYS:
            for suffix,size in (('walk',(64,64)),('ability',(32,64)),('portrait',(32,32))):
                with Image.open(ART.OUT/f'{key}_{suffix}.png') as im:
                    self.assertEqual(im.size,size);self.assertEqual(im.mode,'P');self.assertEqual(im.getpalette(),ART.PAL);self.assertEqual(im.info.get('transparency'),0)
                    self.assertEqual(im.convert('RGBA').getchannel('A').tobytes(),bytes(255 if n else 0 for n in im.tobytes()))
    def test_authored_vertices_stay_within_native_bounds(self):
        original=ART.Art
        class Bounds(original):
            def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.bad=[]
            def check(self,points):self.bad.extend(p for p in points if p[0]<0 or p[1]<0 or p[0]>=self.im.width or p[1]>=self.im.height)
            def p(self,pts,c):self.check(pts);super().p(pts,c)
            def l(self,pts,c,w=1):self.check(pts);super().l(pts,c,w)
            def e(self,b,c):self.check([(b[0],b[1]),(b[2],b[3])]);super().e(b,c)
            def r(self,b,c):self.check([(b[0],b[1]),(b[2],b[3])]);super().r(b,c)
            def dot(self,x,y,c):self.check([(x,y)]);super().dot(x,y,c)
        ART.Art=Bounds
        try:
            for i in range(20):
                for d in ART.DIRECTIONS:
                    for f in range(6):
                        art=ART.FIELD_FUNCTIONS[i](d,f) if f<4 else ART.ABILITY_FUNCTIONS[i](d,f-4)
                        self.assertEqual(art.bad,[],(ART.NAMES[i],d,f))
                self.assertEqual(ART.PORTRAIT_FUNCTIONS[i]().bad,[],ART.NAMES[i])
        finally:ART.Art=original
    def test_four_walks_two_casts_each_direction_have_articulated_contours(self):
        for i,row in enumerate(self.walks):
            for d in range(4):
                with self.subTest(form=ART.NAMES[i],direction=ART.DIRECTIONS[d]):
                    walk=row[d];cast=self.casts[i][d]
                    self.assertEqual(len({im.tobytes() for im in walk+cast}),6)
                    self.assertEqual(len({ART.mask(im).tobytes() for im in walk}),4)
                    self.assertEqual(len({ART.mask(im).tobytes() for im in cast}),2)
                    self.assertTrue(all(45<=sum(bool(n) for n in im.tobytes())<=230 for im in walk+cast))
                    # Keeping grounded feet while the torso/wing/fin changes makes
                    # this more than a palette cycle or whole-sprite translation.
                    self.assertGreater(len({im.crop((0,10,16,16)).tobytes() for im in walk}),1)
                    translated=[]
                    for im in walk[1:]:
                        matches=False
                        for dx in range(-2,3):
                            for dy in range(-2,3):
                                x=Image.new('P',(16,16),0);x.paste(walk[0],(dx,dy))
                                matches|=x.tobytes()==im.tobytes()
                        translated.append(matches)
                    self.assertFalse(all(translated))
    def test_anatomical_evolution_and_41_form_silhouette_comparison(self):
        masks=[ART.mask(row[0][0]).tobytes() for row in self.walks]
        self.assertEqual(len(set(masks)),20)
        prior=ART.legacy_fields();self.assertEqual(len(prior),21)
        for id,name,fn in prior:self.assertNotIn(ART.mask(fn('down',0).im).tobytes(),masks,(id,name))
        for i in range(0,20,2):
            for d in range(4):self.assertGreaterEqual(sum(a!=b for a,b in zip(ART.mask(self.walks[i][d][0]).tobytes(),ART.mask(self.walks[i+1][d][0]).tobytes())),18,(ART.NAMES[i],d))
        for row in self.walks:self.assertEqual(len({d[0].tobytes() for d in row}),4)
    def test_bilateral_profiles_exact_and_front_rear_are_authored(self):
        for i in range(20):
            for frames in (self.walks,self.casts):
                for left,right in zip(frames[i][2],frames[i][3]):self.assertEqual(left.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes(),right.tobytes())
                for down,up in zip(frames[i][0],frames[i][1]):self.assertNotEqual(down.tobytes(),up.tobytes())
    def test_native_faces_and_cast_eyelids_keep_pupils_clear(self):
        for i,(x1,x2,y) in enumerate(ART.FRONT_PUPILS):
            for f,im in enumerate(self.walks[i][0]):
                dy,_=ART.beat(f,None,i in (1,2,6,7))
                for x in (x1,x2):self.assertEqual(im.getpixel((x,y+dy)),ART.P['ink'],(ART.NAMES[i],f,x))
            for p,im in enumerate(self.casts[i][0]):
                dy=(0,-1)[p]
                for x in (x1,x2):
                    self.assertEqual(im.getpixel((x,y+dy)),ART.P['ink'],(ART.NAMES[i],p,x))
                    self.assertEqual(im.getpixel((x,y+dy-1)),ART.P['purple0' if p==0 else 'white'])
    def test_open_anatomical_spaces_are_transparent(self):
        # Vaultback's shell truly arches over an abdomen; Canopetail has an open
        # living tail loop. Transparent negative space is not merely dark fill.
        for i,box,minimum in ((9,(4,5,11,9),5),(13,(8,2,12,6),2),(19,(3,0,16,5),12)):
            for im in self.walks[i][0]+self.casts[i][0]:self.assertGreaterEqual(sum(n==0 for n in im.crop(box).tobytes()),minimum,ART.NAMES[i])
    def test_twenty_separately_composed_portraits(self):
        self.assertEqual(len({ART.mask(im).tobytes() for im in self.portraits}),20)
        for i,im in enumerate(self.portraits):
            self.assertEqual(im.size,(32,32));self.assertGreater(sum(bool(n) for n in im.tobytes()),250)
            self.assertNotEqual(im.tobytes(),self.walks[i][0][0].resize((32,32),Image.Resampling.NEAREST).tobytes())
    def test_rom_accessors_match_all_native_png_pixels(self):
        for i,id in enumerate(ART.FORM_IDS):
            self.assertEqual(self.lib.southern_creature_art_index(id),i)
            self.assertEqual(C.string_at(self.lib.southern_creature_art_portrait(id),1024),self.portraits[i].tobytes())
            for suffix,frames,n,fn in (('walk',self.walks,4,self.lib.southern_creature_art_frame),('ability',self.casts,2,self.lib.southern_creature_art_ability_frame)):
                with Image.open(ART.OUT/f'{ART.KEYS[i]}_{suffix}.png') as sheet:
                    for d in range(4):
                        for f in range(n):
                            expected=frames[i][d][f].tobytes();self.assertEqual(C.string_at(fn(id,d,f),256),expected)
                            self.assertEqual(sheet.crop((16*f,16*d,16*f+16,16*d+16)).tobytes(),expected)
    def test_total_safe_rejection_of_unknown_ids_and_unsigned_indices(self):
        for id in list(range(65536))+[0x7fffffff,0xffffffff]:
            if id in ART.FORM_IDS:continue
            self.assertEqual(self.lib.southern_creature_art_index(id),-1)
            self.assertFalse(self.lib.southern_creature_art_frame(id,0,0));self.assertFalse(self.lib.southern_creature_art_ability_frame(id,0,0));self.assertFalse(self.lib.southern_creature_art_portrait(id))
        for id in ART.FORM_IDS:
            for invalid in (4,5,255,256,65535,0xffffffff):
                self.assertFalse(self.lib.southern_creature_art_frame(id,invalid,0));self.assertFalse(self.lib.southern_creature_art_frame(id,0,invalid));self.assertFalse(self.lib.southern_creature_art_ability_frame(id,invalid,0))
            for invalid in (2,3,255,0xffffffff):self.assertFalse(self.lib.southern_creature_art_ability_frame(id,0,invalid))
    def test_actual_southern_terrain_composites_are_exact_native_pixels(self):
        manifest=json.loads((ART.OUT/'manifest.json').read_text());sources=manifest['scene_review_sources'];self.assertEqual([s['terrain'] for s in sources],['GRASS','WATER','PLASTER','WOOD'])
        patches=[]
        for source in sources:
            p=ROOT/source['path'];self.assertEqual(hashlib.sha256(p.read_bytes()).hexdigest(),source['sha256'])
            with Image.open(p) as im:patches.append(im.convert('RGB').crop(source['crop']))
        for i,key in enumerate(ART.KEYS):
            with Image.open(ART.OUT/f'{key}_terrain_native.png') as original:
                sheet=original.convert('RGB');self.assertEqual(sheet.size,(576,112))
                for t,patch in enumerate(patches):
                    for d in range(4):
                        for f,im in enumerate(self.walks[i][d]+self.casts[i][d]):
                            expected=patch.copy();ART.paste(expected,im,(4,4));x=t*144+f*24;y=16+d*24
                            self.assertEqual(sheet.crop((x,y,x+24,y+24)).tobytes(),expected.tobytes())
    def test_native_contact_previews_and_small_motion_gifs(self):
        for i,key in enumerate(ART.KEYS):
            with Image.open(ART.OUT/f'{key}_native.png') as original:
                sheet=original.convert('RGB');self.assertEqual(sheet.size,(240,166))
                for bg,y in (('deep',24),('dirt4',100)):
                    for d in range(4):
                        for f,im in enumerate(self.walks[i][d]+self.casts[i][d]):
                            expected=Image.new('RGB',(16,16),ART.RGB[ART.P[bg]]);ART.paste(expected,im,(0,0));x=4+f*30;yy=y+d*16
                            self.assertEqual(sheet.crop((x,yy,x+16,yy+16)).tobytes(),expected.tobytes())
            with Image.open(ART.OUT/f'{key}_motion.gif') as gif:
                self.assertEqual(gif.size,(128,48));self.assertEqual(gif.n_frames,6)
                for frame in range(6):
                    gif.seek(frame);shown=gif.convert('RGB')
                    for d in range(4):
                        im=(self.walks[i][d]+self.casts[i][d])[frame];expected=Image.new('RGB',(16,16),ART.RGB[ART.P['dirt4']]);ART.paste(expected,im,(0,0));x=8+d*30
                        self.assertEqual(shown.crop((x,23,x+16,39)).tobytes(),expected.tobytes())
        for p in ART.OUT.glob('*.png'):self.assertLess(p.stat().st_size,30000,p.name)
    def test_const_rom_no_heap_mutable_ram_or_obj_allocation(self):
        arm=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc'
        if not arm.exists():
            found=shutil.which('arm-none-eabi-gcc');self.assertIsNotNone(found,'ARM target unverified');arm=Path(found)
        obj=self.tmp/'art.o';subprocess.run([str(arm),'-std=c99','-mcpu=arm7tdmi','-mthumb','-O2','-ffreestanding','-fno-builtin','-fstack-usage','-Wall','-Wextra','-Werror','-c',str(ROOT/'src/southern_creature_art.c'),'-o',str(obj)],check=True)
        sizes=subprocess.check_output([str(arm).replace('gcc','size'),str(obj)],text=True);rom,data,bss=map(int,sizes.splitlines()[-1].split()[:3]);self.assertLessEqual(rom,170*1024);self.assertEqual((data,bss),(0,0))
        nm=subprocess.check_output([str(arm).replace('gcc','nm'),'-S','--size-sort',str(obj)],text=True);symbols={p[3]:(int(p[1],16),p[2]) for line in nm.splitlines() if len(p:=line.split())==4}
        expected={'southern_creature_form_ids':20,'southern_creature_direction_frames':81920,'southern_creature_ability_frames':40960,'southern_creature_portraits':20480}
        self.assertEqual(sum(expected.values()),143380)
        for name,size in expected.items():self.assertEqual(symbols[name],(size,'R'))
        stack=[int(line.split('\t')[1]) for p in self.tmp.glob('*.su') for line in p.read_text().splitlines()];self.assertTrue(stack);self.assertLessEqual(max(stack),24)
        self.assertNotIn('malloc',nm);self.assertNotIn(' U ',nm)
        for p in (ROOT/'src/southern_creature_art_data').glob('*.inc'):self.assertLessEqual(p.stat().st_size,30000)
    def test_deterministic_regeneration_and_output_hash_manifest(self):
        before=ART.output_hashes();manifest=ART.generate();self.assertEqual(before,ART.output_hashes())
        self.assertEqual(manifest['data_bytes'],143380);self.assertEqual(manifest['persistent_obj_allocation_bytes'],0);self.assertEqual(manifest['runtime_data_bytes'],0);self.assertEqual(manifest['runtime_bss_bytes'],0);self.assertIn('ART ONLY',manifest['status'])
        self.assertEqual(manifest['palette_sha256'],hashlib.sha256(json.dumps(ART.base.COLORS).encode()).hexdigest())
        report=json.loads((ART.OUT/'validation.json').read_text());self.assertEqual(report['output_sha256'],ART.output_hashes());self.assertEqual(report['arm_rom_object_bytes'],143632);self.assertEqual(report['max_arm_stack_bytes'],8)
if __name__=='__main__':unittest.main(verbosity=2)
