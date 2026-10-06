#!/usr/bin/env python3
"""Independent art-only C reconstruction, bounds, identity, and target contracts.
Passing is not proof of gameplay acquisition, integrated renderer, or frame budget.
"""
import ctypes as C
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from PIL import Image
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
IDS=tuple(range(49,73));DATA_BYTES=196632;ROM_BUDGET=198656

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def compile_host(root,out):
    subprocess.run([os.environ.get('CC','cc'),'-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-fPIC','-shared','-I'+str(root/'src'),str(root/'src/underwater_creature_art.c'),'-o',str(out)],check=True,capture_output=True,text=True)
    lib=C.CDLL(str(out));lib.underwater_creature_art_index.argtypes=[C.c_uint];lib.underwater_creature_art_index.restype=C.c_int
    for name,count in (('frame',3),('ability_frame',3),('portrait',1)):
        fn=getattr(lib,'underwater_creature_art_'+name);fn.argtypes=[C.c_uint]*count;fn.restype=C.POINTER(C.c_ubyte)
    return lib

def normal_mask(im):
    m=Image.frombytes('L',im.size,bytes(255 if p else 0 for p in im.tobytes()));box=m.getbbox();return (box[2]-box[0],box[3]-box[1],m.crop(box).tobytes())

class CodegenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.codegen=load('underwater_codegen_tests',ROOT/'assets/underwater_creatures/codegen.py')
        cls.names=tuple(f['name'] for f in json.loads((ROOT/'docs/underwater-design/creature_forms.json').read_text()))
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='uw-art-emitter-');self.addCleanup(tmp.cleanup);self.root=Path(tmp.name)
        # Leaf-specific markers catch every transpose, duplication and omission.
        def im(size,n):
            v=Image.new('P',size,0);v.putpixel((n%size[0],(n//size[0])%size[1]),n%96+1);return v
        self.fields=[[[im((16,16),i*16+d*4+f) for f in range(4)] for d in range(4)] for i in range(24)]
        self.casts=[[[im((16,16),i*12+d*3+p) for p in range(3)] for d in range(4)] for i in range(24)]
        self.portraits=[im((32,32),i*39) for i in range(24)]
    def emit(self,**changes):
        kw=dict(root=self.root,form_ids=IDS,names=self.names,fields=self.fields,abilities=self.casts,portraits=self.portraits);kw.update(changes);return self.codegen.emit_code(**kw)
    def test_independent_tensor_roundtrip_all_696_leaves(self):
        chunks=self.emit();self.assertLess(max(chunks),30000);lib=compile_host(self.root,self.root/'art.so')
        for i,fid in enumerate(IDS):
            self.assertEqual(lib.underwater_creature_art_index(fid),i)
            self.assertEqual(C.string_at(lib.underwater_creature_art_portrait(fid),1024),self.portraits[i].tobytes())
            for d in range(4):
                for f in range(4):self.assertEqual(C.string_at(lib.underwater_creature_art_frame(fid,d,f),256),self.fields[i][d][f].tobytes())
                for p in range(3):self.assertEqual(C.string_at(lib.underwater_creature_art_ability_frame(fid,d,p),256),self.casts[i][d][p].tobytes())
    def test_invalid_emission_never_writes(self):
        badfields=[row[:] for row in self.fields];badfields[0]=badfields[0][:-1]
        for changes in ({'form_ids':IDS[::-1]},{'form_ids':tuple(range(24))},{'names':self.names[:-1]},
          {'names':('invalid-name',)+self.names[1:]},{'names':(self.names[1],)+self.names[1:]},
          {'fields':badfields},{'fields':[[[Image.new('RGB',(16,16))]*4]*4]*24},
          {'portraits':self.portraits[:-1]+[Image.new('P',(16,16))]},
          {'portraits':self.portraits[:-1]+[Image.new('P',(32,32),97)]},
          {'abilities':[[[Image.new('P',(16,16))]*2]*4]*24}):
            with self.subTest(case=list(changes)):
                with self.assertRaises(ValueError):self.emit(**changes)
                self.assertEqual(list(self.root.iterdir()),[])
    def test_deterministic_emitter_only_cleans_its_chunks(self):
        self.emit();src=self.root/'src';before={p.relative_to(src):p.read_bytes() for p in src.rglob('*') if p.is_file()};folder=src/'underwater_creature_art_data'
        (folder/'part_999.inc').write_text('stale');(folder/'caller-owned.txt').write_text('keep');self.emit()
        self.assertFalse((folder/'part_999.inc').exists());self.assertEqual((folder/'caller-owned.txt').read_text(),'keep')
        for p,b in before.items():self.assertEqual((src/p).read_bytes(),b)

class CreatureArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.art=load('underwater_art_tests',ROOT/'assets/generate_underwater_creatures.py');tmp=tempfile.TemporaryDirectory(prefix='uw-art-tests-');cls.addClassCleanup(tmp.cleanup);cls.tmp=Path(tmp.name)
        cls.walks=[[[cls.art.field(fid,d,f) for f in range(4)] for d in cls.art.DIRECTIONS] for fid in IDS]
        cls.casts=[[[cls.art.field(fid,d,p,p) for p in range(3)] for d in cls.art.DIRECTIONS] for fid in IDS]
        cls.portraits=[cls.art.portrait(fid) for fid in IDS];cls.lib=compile_host(ROOT,cls.tmp/'art.so')
    def test_identity_axis_coverage_and_direction_convention(self):
        self.assertEqual(self.art.FORM_IDS,IDS);self.assertEqual(self.art.DIRECTIONS,('down','up','left','right'))
        self.assertEqual(bytes((C.c_ubyte*24).in_dll(self.lib,'underwater_creature_form_ids')),bytes(IDS))
        cat={f['id']:f for f in self.art.load_catalog(ROOT/'assets/creatures/catalog.json')['forms']}
        self.assertEqual(tuple(cat[i]['name'] for i in IDS),self.art.NAMES)
        self.assertEqual({f['phase'] for f in self.art.BRIEFS},{'fire','water','earth','metal','wood'})
        self.assertEqual({f['polarity'] for f in self.art.BRIEFS},{'yin','yang'})
    def test_authored_geometry_never_relies_on_implicit_canvas_clipping(self):
        original=self.art.Art;errors=[];current=None
        class CheckedArt(original):
            def check(self,points):
                errors.extend((current,x,y) for x,y in points if x<0 or y<0 or x>=self.im.width or y>=self.im.height)
            def p(self,points,color):self.check(points);super().p(points,color)
            def l(self,points,color,w=1):self.check(points);super().l(points,color,w)
            def e(self,box,color):self.check(((box[0],box[1]),(box[2],box[3])));super().e(box,color)
            def r(self,box,color):self.check(((box[0],box[1]),(box[2],box[3])));super().r(box,color)
            def dot(self,x,y,color):self.check(((x,y),));super().dot(x,y,color)
        self.art.Art=CheckedArt
        try:
            for fid in IDS:
                for d in self.art.DIRECTIONS:
                    for f in range(7):
                        current=(fid,d,f);self.art.field(fid,d,f if f<4 else f-4,None if f<4 else f-4)
                current=(fid,'portrait');self.art.portrait(fid)
        finally:self.art.Art=original
        self.assertEqual(errors,[])
    def test_palette_is_actual_cartridge_palette_and_previews_are_nearest_neighbor(self):
        source=(ROOT/'src/asset_data/part_000.inc').read_text()
        body=re.search(r'game_palette\[256\] = \{(.*?)\};',source,re.S).group(1)
        native=list(map(int,re.findall(r'\d+',body)))
        expected=[]
        for _,color in self.art.COLORS:
            r,g,b=(int(color[k:k+2],16)>>3 for k in (1,3,5));expected.append(r|(g<<5)|(b<<10))
        self.assertEqual(native[:len(expected)],expected)
        for stem in ('roster','all_frames','released89_silhouettes'):
            with Image.open(self.art.OUT/f'{stem}_native.png') as im, Image.open(self.art.OUT/f'{stem}_2x.png') as enlarged:
                self.assertEqual(enlarged.tobytes(),im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST).tobytes())
        for key in self.art.KEYS:
            with Image.open(self.art.OUT/f'{key}_native.png') as im, Image.open(self.art.OUT/f'{key}_3x.png') as enlarged:
                self.assertEqual(enlarged.tobytes(),im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).tobytes())
    def test_every_authored_byte_roundtrips_through_c_and_saved_png(self):
        for i,fid in enumerate(IDS):
            key=self.art.KEYS[i];w=Image.open(self.art.OUT/f'{key}_walk.png');a=Image.open(self.art.OUT/f'{key}_ability.png');p=Image.open(self.art.OUT/f'{key}_portrait.png')
            self.assertEqual(C.string_at(self.lib.underwater_creature_art_portrait(fid),1024),self.portraits[i].tobytes());self.assertEqual(p.tobytes(),self.portraits[i].tobytes())
            for d in range(4):
                for f in range(4):
                    expected=self.walks[i][d][f].tobytes();self.assertEqual(C.string_at(self.lib.underwater_creature_art_frame(fid,d,f),256),expected);self.assertEqual(w.crop((f*16,d*16,f*16+16,d*16+16)).tobytes(),expected)
                for pose in range(3):
                    expected=self.casts[i][d][pose].tobytes();self.assertEqual(C.string_at(self.lib.underwater_creature_art_ability_frame(fid,d,pose),256),expected);self.assertEqual(a.crop((pose*16,d*16,pose*16+16,d*16+16)).tobytes(),expected)
    def test_full_width_invalid_api_arguments_return_null(self):
        invalid=(0,1,48,73,127,128,255,256,65535,65536,0x1000031,0xffffffff)
        for fid in invalid:
            self.assertEqual(self.lib.underwater_creature_art_index(fid),-1);self.assertFalse(self.lib.underwater_creature_art_portrait(fid))
            self.assertFalse(self.lib.underwater_creature_art_frame(fid,0,0));self.assertFalse(self.lib.underwater_creature_art_ability_frame(fid,0,0))
        for fid in IDS:
            for bad in (4,5,255,256,65535,65536,0xffffffff):
                self.assertFalse(self.lib.underwater_creature_art_frame(fid,bad,0));self.assertFalse(self.lib.underwater_creature_art_frame(fid,0,bad));self.assertFalse(self.lib.underwater_creature_art_ability_frame(fid,bad,0))
            for bad in (3,4,255,256,65535,65536,0xffffffff):self.assertFalse(self.lib.underwater_creature_art_ability_frame(fid,0,bad))
    def test_articulated_motion_directions_transparency_and_palette(self):
        fronts=[]
        for i in range(24):
            self.assertEqual(len({self.walks[i][d][0].tobytes() for d in range(4)}),4)
            fronts.append(normal_mask(self.walks[i][0][0]))
            for d in range(4):
                w=self.walks[i][d];c=self.casts[i][d];self.assertEqual(len({im.tobytes() for im in w+c}),7);self.assertEqual(len({normal_mask(im) for im in w}),4);self.assertEqual(len({normal_mask(im) for im in c}),3)
                for im in w+c:
                    self.assertEqual(im.mode,'P');self.assertEqual(im.size,(16,16));self.assertLess(max(im.tobytes()),97)
                    self.assertEqual(im.getpalette(),self.art.PAL)
                    self.assertTrue(all(im.getpixel((x,y))==0 for x in range(16) for y in (0,15)))
                    self.assertTrue(all(im.getpixel((x,y))==0 for x in (0,15) for y in range(16)))
            for f in range(4):self.assertEqual(self.walks[i][3][f].tobytes(),self.walks[i][2][f].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes())
            self.assertNotEqual(self.portraits[i].tobytes(),self.walks[i][0][0].resize((32,32),Image.Resampling.NEAREST).tobytes())
        self.assertEqual(len(set(fronts)),24)
    def test_distinct_branch_masks_and_frozen_prior_pixels(self):
        self.assertTrue(self.art.validate_legacy_prefix()['unchanged'])
        manifest=json.loads((self.art.OUT/'manifest.json').read_text())
        self.assertEqual(manifest['silhouette_comparison']['cross_release_front_mask_matches'],0)
        self.assertEqual(len(manifest['silhouette_comparison']['released_form_ids']),65)
        for i in range(0,24,3):
            for d in range(4):
                left=self.walks[i+1][d][0].tobytes();right=self.walks[i+2][d][0].tobytes();self.assertGreaterEqual(sum(bool(a)!=bool(b) for a,b in zip(left,right)),12)
    def test_target_immutable_rom_no_ram_iwram_dependencies_or_stack(self):
        sys.path.insert(0,str(ROOT/'tools'));from arm_toolchain import resolve_arm_tools
        tools=resolve_arm_tools('gcc','nm','size','objdump',root=ROOT);obj=self.tmp/'art.o'
        subprocess.run([tools['gcc'],'-std=c99','-O2','-Wall','-Wextra','-Werror','-mcpu=arm7tdmi','-mthumb','-ffreestanding','-fno-builtin','-fstack-usage','-c',str(ROOT/'src/underwater_creature_art.c'),'-o',str(obj)],check=True,capture_output=True,text=True)
        sizes=list(map(int,subprocess.check_output([tools['size'],str(obj)],text=True).splitlines()[-1].split()[:3]));self.assertLessEqual(sizes[0],ROM_BUDGET);self.assertEqual(sizes[1:],[0,0])
        symbols={}
        for line in subprocess.check_output([tools['nm'],'-S',str(obj)],text=True).splitlines():
            parts=line.split()
            if len(parts)==4:symbols[parts[3]]=(int(parts[1],16),parts[2])
        expected={'underwater_creature_form_ids':24,'underwater_creature_direction_frames':24*4*4*256,'underwater_creature_ability_frames':24*4*3*256,'underwater_creature_portraits':24*1024}
        self.assertEqual(sum(expected.values()),DATA_BYTES)
        for key,size in expected.items():self.assertEqual(symbols[key],(size,'R'))
        self.assertFalse(any(kind in 'BbDdCc' for size,kind in symbols.values()))
        self.assertEqual(subprocess.check_output([tools['nm'],'-u',str(obj)],text=True).strip(),'')
        sections=subprocess.check_output([tools['objdump'],'-h',str(obj)],text=True).lower();self.assertNotIn('iwram',sections);self.assertNotIn('ewram',sections)
        stack=[int(line.split('\t')[1]) for p in self.tmp.glob('*.su') for line in p.read_text().splitlines()];self.assertEqual(len(stack),4);self.assertLessEqual(max(stack),24)
        for p in (ROOT/'src/underwater_creature_art_data').glob('*.inc'):self.assertLess(p.stat().st_size,30000)
    def test_regeneration_exact_and_validation_report(self):
        before=self.art.output_hashes();run=subprocess.run([sys.executable,'-B',str(ROOT/'assets/generate_underwater_creatures.py'),'--verify'],cwd=ROOT,capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stdout+run.stderr);self.assertEqual(before,self.art.output_hashes())
        report=json.loads((self.art.OUT/'validation.json').read_text());self.assertTrue(report['deterministic_regeneration']);self.assertEqual(report['output_sha256'],self.art.output_hashes());self.assertEqual(report['arm_compile'],'passed');self.assertEqual(report['arm_data_bytes'],0);self.assertEqual(report['arm_bss_bytes'],0)
    def test_python_art_entry_points_reject_bad_inputs(self):
        for args in ((48,'down',0),(73,'down',0),(49,'sideways',0),(49,'down',4),(49,'down',-1),(49,'down',True),(49,'down',0,3),(49,'down',0,-1)):
            with self.assertRaises(ValueError):self.art.field(*args)
        for fid in (-1,0,48,73,256,'49',True):
            with self.assertRaises(ValueError):self.art.portrait(fid)

if __name__=='__main__':unittest.main(verbosity=2)
