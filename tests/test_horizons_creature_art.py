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
IDS=tuple(range(105,121));DATA_BYTES=131088;ROM_BUDGET=134144

def load(name,path):
    spec=importlib.util.spec_from_file_location(name,path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);return module

def compile_host(root,out):
    subprocess.run([os.environ.get('CC','cc'),'-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-fPIC','-shared','-I'+str(root/'src'),str(root/'src/horizons_creature_art.c'),'-o',str(out)],check=True,capture_output=True,text=True)
    lib=C.CDLL(str(out));lib.horizons_creature_art_index.argtypes=[C.c_uint];lib.horizons_creature_art_index.restype=C.c_int
    for name,count in (('frame',3),('ability_frame',3),('portrait',1)):
        fn=getattr(lib,'horizons_creature_art_'+name);fn.argtypes=[C.c_uint]*count;fn.restype=C.POINTER(C.c_ubyte)
    return lib

def normal_mask(im):
    m=Image.frombytes('L',im.size,bytes(255 if p else 0 for p in im.tobytes()));box=m.getbbox();return (box[2]-box[0],box[3]-box[1],m.crop(box).tobytes())

class CodegenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.codegen=load('horizons_codegen_tests',ROOT/'assets/horizons_creatures/codegen.py')
        cls.names=tuple(f['name'] for f in json.loads((ROOT/'docs/horizons-design/shared_horizons_plan.json').read_text())['forms'])
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='horizons-art-emitter-');self.addCleanup(tmp.cleanup);self.root=Path(tmp.name)
        # Leaf-specific markers catch every transpose, duplication and omission.
        def im(size,n):
            v=Image.new('P',size,0);v.putpixel((n%size[0],(n//size[0])%size[1]),n%96+1);return v
        self.fields=[[[im((16,16),i*16+d*4+f) for f in range(4)] for d in range(4)] for i in range(16)]
        self.casts=[[[im((16,16),i*12+d*3+p) for p in range(3)] for d in range(4)] for i in range(16)]
        self.portraits=[im((32,32),i*39) for i in range(16)]
    def emit(self,**changes):
        kw=dict(root=self.root,form_ids=IDS,names=self.names,fields=self.fields,abilities=self.casts,portraits=self.portraits);kw.update(changes);return self.codegen.emit_code(**kw)
    def test_independent_tensor_roundtrip_all_464_leaves(self):
        chunks=self.emit();self.assertLess(max(chunks),30000);lib=compile_host(self.root,self.root/'art.so')
        for i,fid in enumerate(IDS):
            self.assertEqual(lib.horizons_creature_art_index(fid),i)
            self.assertEqual(C.string_at(lib.horizons_creature_art_portrait(fid),1024),self.portraits[i].tobytes())
            for d in range(4):
                for f in range(4):self.assertEqual(C.string_at(lib.horizons_creature_art_frame(fid,d,f),256),self.fields[i][d][f].tobytes())
                for p in range(3):self.assertEqual(C.string_at(lib.horizons_creature_art_ability_frame(fid,d,p),256),self.casts[i][d][p].tobytes())
    def test_invalid_emission_never_writes(self):
        badfields=[row[:] for row in self.fields];badfields[0]=badfields[0][:-1]
        for changes in ({'form_ids':IDS[::-1]},{'form_ids':tuple(range(16))},{'form_ids':tuple(float(n)for n in IDS)},{'names':self.names[:-1]},
          {'names':('invalid-name',)+self.names[1:]},{'names':(self.names[1],)+self.names[1:]},
          {'fields':badfields},{'fields':[[[Image.new('RGB',(16,16))]*4]*4]*16},
          {'portraits':self.portraits[:-1]+[Image.new('P',(16,16))]},
          {'portraits':self.portraits[:-1]+[Image.new('P',(32,32),97)]},
          {'abilities':[[[Image.new('P',(16,16))]*2]*4]*16}):
            with self.subTest(case=list(changes)):
                with self.assertRaises(ValueError):self.emit(**changes)
                self.assertEqual(list(self.root.iterdir()),[])
    def test_deterministic_emitter_only_cleans_its_chunks(self):
        self.emit();src=self.root/'src';before={p.relative_to(src):p.read_bytes() for p in src.rglob('*') if p.is_file()};folder=src/'horizons_creature_art_data'
        (folder/'part_999.inc').write_text('stale');(folder/'caller-owned.txt').write_text('keep');self.emit()
        self.assertFalse((folder/'part_999.inc').exists());self.assertEqual((folder/'caller-owned.txt').read_text(),'keep')
        for p,b in before.items():self.assertEqual((src/p).read_bytes(),b)

class CreatureArtTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.art=load('horizons_art_tests',ROOT/'assets/generate_horizons_creatures.py');tmp=tempfile.TemporaryDirectory(prefix='horizons-art-tests-');cls.addClassCleanup(tmp.cleanup);cls.tmp=Path(tmp.name)
        cls.walks=[[[cls.art.field(fid,d,f) for f in range(4)] for d in cls.art.DIRECTIONS] for fid in IDS]
        cls.casts=[[[cls.art.field(fid,d,p,p) for p in range(3)] for d in cls.art.DIRECTIONS] for fid in IDS]
        cls.portraits=[cls.art.portrait(fid) for fid in IDS];cls.lib=compile_host(ROOT,cls.tmp/'art.so')
    def test_identity_axis_coverage_and_direction_convention(self):
        self.assertEqual(self.art.FORM_IDS,IDS);self.assertEqual(self.art.DIRECTIONS,('down','up','left','right'))
        self.assertEqual(bytes((C.c_ubyte*16).in_dll(self.lib,'horizons_creature_form_ids')),bytes(IDS))
        self.assertEqual(tuple(f['name'] for f in self.art.BRIEFS),self.art.NAMES)
        self.assertEqual(tuple(f['id'] for f in self.art.BRIEFS),IDS)
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
        for stem in ('roster','all_frames','released120_silhouettes','lineage'):
            with Image.open(self.art.OUT/f'{stem}_native.png') as im, Image.open(self.art.OUT/f'{stem}_2x.png') as enlarged:
                self.assertEqual(enlarged.tobytes(),im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST).tobytes())
        for key in self.art.KEYS:
            with Image.open(self.art.OUT/f'{key}_native.png') as im, Image.open(self.art.OUT/f'{key}_3x.png') as enlarged:
                self.assertEqual(enlarged.tobytes(),im.resize((im.width*3,im.height*3),Image.Resampling.NEAREST).tobytes())
    def test_every_authored_byte_roundtrips_through_c_and_saved_png(self):
        for i,fid in enumerate(IDS):
            key=self.art.KEYS[i];w=Image.open(self.art.OUT/f'{key}_walk.png');a=Image.open(self.art.OUT/f'{key}_ability.png');p=Image.open(self.art.OUT/f'{key}_portrait.png')
            self.assertEqual(C.string_at(self.lib.horizons_creature_art_portrait(fid),1024),self.portraits[i].tobytes());self.assertEqual(p.tobytes(),self.portraits[i].tobytes())
            for d in range(4):
                for f in range(4):
                    expected=self.walks[i][d][f].tobytes();self.assertEqual(C.string_at(self.lib.horizons_creature_art_frame(fid,d,f),256),expected);self.assertEqual(w.crop((f*16,d*16,f*16+16,d*16+16)).tobytes(),expected)
                for pose in range(3):
                    expected=self.casts[i][d][pose].tobytes();self.assertEqual(C.string_at(self.lib.horizons_creature_art_ability_frame(fid,d,pose),256),expected);self.assertEqual(a.crop((pose*16,d*16,pose*16+16,d*16+16)).tobytes(),expected)
    def test_full_width_invalid_api_arguments_return_null(self):
        invalid=tuple(i for i in range(256)if i not in IDS)+(256,361,376,65535,65536,0x1000069,0xffffffff)
        for fid in invalid:
            self.assertEqual(self.lib.horizons_creature_art_index(fid),-1);self.assertFalse(self.lib.horizons_creature_art_portrait(fid))
            self.assertFalse(self.lib.horizons_creature_art_frame(fid,0,0));self.assertFalse(self.lib.horizons_creature_art_ability_frame(fid,0,0))
        for fid in IDS:
            for bad in (4,5,255,256,65535,65536,0xffffffff):
                self.assertFalse(self.lib.horizons_creature_art_frame(fid,bad,0));self.assertFalse(self.lib.horizons_creature_art_frame(fid,0,bad));self.assertFalse(self.lib.horizons_creature_art_ability_frame(fid,bad,0))
            for bad in (3,4,255,256,65535,65536,0xffffffff):self.assertFalse(self.lib.horizons_creature_art_ability_frame(fid,0,bad))
    def test_articulated_motion_directions_transparency_and_palette(self):
        fronts=[]
        for i in range(16):
            self.assertEqual(len({self.walks[i][d][0].tobytes() for d in range(4)}),4)
            self.assertEqual(len({self.art.mask(self.walks[i][d][0]).tobytes() for d in range(4)}),4)
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
        self.assertEqual(len(set(fronts)),16)
    def test_all_field_anatomy_is_one_eight_connected_body(self):
        # Catches feet or tail tips accidentally left floating during body bob.
        for i,fid in enumerate(IDS):
            for d in range(4):
                for im in self.walks[i][d]+self.casts[i][d]:
                    remaining={(x,y)for y in range(16)for x in range(16)if im.getpixel((x,y))}
                    pending=[remaining.pop()]
                    while pending:
                        x,y=pending.pop()
                        for nx in range(x-1,x+2):
                            for ny in range(y-1,y+2):
                                if(nx,ny)in remaining:remaining.remove((nx,ny));pending.append((nx,ny))
                    self.assertFalse(remaining,(fid,d,'detached anatomy'))
    def test_distinct_evolutions_and_all_accepted104_silhouettes(self):
        manifest=json.loads((self.art.OUT/'manifest.json').read_text())
        comparison=manifest['silhouette_comparison']
        self.assertEqual(comparison['cross_release_front_mask_matches'],0)
        self.assertEqual(len(comparison['released_form_ids']),104)
        self.assertEqual(len(set(comparison['released_form_ids'])),104)
        self.assertEqual(hashlib.sha256((ROOT/comparison['source']).read_bytes()).hexdigest(),comparison['source_sha256'])
        self.assertGreaterEqual(min(r['different_front_mask_pixels']for r in comparison['nearest_front_masks']),20)
        for a,b in ((105,106),(107,108),(109,110),(111,112)):
            for d in range(4):
                left=self.walks[IDS.index(a)][d][0].tobytes();right=self.walks[IDS.index(b)][d][0].tobytes()
                self.assertGreaterEqual(sum(bool(x)!=bool(y)for x,y in zip(left,right)),8)
    def test_native_walk_and_cast_recovery_gifs(self):
        for i,key in enumerate(self.art.KEYS):
            with Image.open(self.art.OUT/f'{key}_walk_native.gif')as gif:
                self.assertEqual(gif.size,(64,16));self.assertEqual(gif.n_frames,4)
                for f in range(4):
                    gif.seek(f);expected=Image.new('RGB',(64,16),self.art.RGB[self.art.P['dirt4']])
                    for d in range(4):self.art.paste(expected,self.walks[i][d][f],(d*16,0))
                    self.assertEqual(gif.convert('RGB').tobytes(),expected.tobytes())
            with Image.open(self.art.OUT/f'{key}_motion.gif')as gif:
                self.assertEqual(gif.n_frames,11);gif.seek(0);first=gif.convert('RGB').tobytes();gif.seek(7)
                self.assertEqual(first,gif.convert('RGB').tobytes())
    def test_terrain_sources_are_real_and_current(self):
        manifest=json.loads((self.art.OUT/'manifest.json').read_text())
        sources=manifest['scene_review_sources'];self.assertEqual(sum('crop'in row for row in sources),6)
        for row in sources:self.assertEqual(hashlib.sha256((ROOT/row['path']).read_bytes()).hexdigest(),row['sha256'])
        report=json.loads((self.art.OUT/'terrain_readability.json').read_text())
        self.assertEqual(report['samples'],2688);self.assertEqual(len(report['rows']),96)
        self.assertGreaterEqual(report['minimum_opaque_fraction'],0.80)
        self.assertGreaterEqual(report['minimum_boundary_fraction'],0.78)
        self.assertIn('ART ONLY',manifest['status']);self.assertEqual(manifest['anchor'],[8,8])

    def test_target_immutable_rom_no_ram_iwram_dependencies_or_stack(self):
        sys.path.insert(0,str(ROOT/'tools'));from arm_toolchain import resolve_arm_tools
        tools=resolve_arm_tools('gcc','nm','size','objdump',root=ROOT);obj=self.tmp/'art.o'
        subprocess.run([tools['gcc'],'-std=c99','-O2','-Wall','-Wextra','-Werror','-mcpu=arm7tdmi','-mthumb','-ffreestanding','-fno-builtin','-fstack-usage','-c',str(ROOT/'src/horizons_creature_art.c'),'-o',str(obj)],check=True,capture_output=True,text=True)
        sizes=list(map(int,subprocess.check_output([tools['size'],str(obj)],text=True).splitlines()[-1].split()[:3]));self.assertLessEqual(sizes[0],ROM_BUDGET);self.assertEqual(sizes[1:],[0,0])
        symbols={}
        for line in subprocess.check_output([tools['nm'],'-S',str(obj)],text=True).splitlines():
            parts=line.split()
            if len(parts)==4:symbols[parts[3]]=(int(parts[1],16),parts[2])
        expected={'horizons_creature_form_ids':16,'horizons_creature_direction_frames':16*4*4*256,'horizons_creature_ability_frames':16*4*3*256,'horizons_creature_portraits':16*1024}
        self.assertEqual(sum(expected.values()),DATA_BYTES)
        for key,size in expected.items():self.assertEqual(symbols[key],(size,'R'))
        self.assertFalse(any(kind in 'BbDdCc' for size,kind in symbols.values()))
        self.assertEqual(subprocess.check_output([tools['nm'],'-u',str(obj)],text=True).strip(),'')
        sections=subprocess.check_output([tools['objdump'],'-h',str(obj)],text=True).lower();self.assertNotIn('iwram',sections);self.assertNotIn('ewram',sections)
        stack=[int(line.split('\t')[1]) for p in self.tmp.glob('*.su') for line in p.read_text().splitlines()];self.assertEqual(len(stack),4);self.assertLessEqual(max(stack),24)
        for p in (ROOT/'src/horizons_creature_art_data').glob('*.inc'):self.assertLess(p.stat().st_size,30000)
    def test_regeneration_exact_and_validation_report(self):
        before=self.art.output_hashes();run=subprocess.run([sys.executable,'-B',str(ROOT/'assets/generate_horizons_creatures.py'),'--verify'],cwd=ROOT,capture_output=True,text=True);self.assertEqual(run.returncode,0,run.stdout+run.stderr);self.assertEqual(before,self.art.output_hashes())
        report=json.loads((self.art.OUT/'validation.json').read_text());self.assertTrue(report['deterministic_regeneration']);self.assertEqual(report['output_sha256'],self.art.output_hashes());self.assertEqual(report['arm_compile'],'passed');self.assertEqual(report['arm_data_bytes'],0);self.assertEqual(report['arm_bss_bytes'],0)
    def test_python_art_entry_points_reject_bad_inputs(self):
        for args in ((104,'down',0),(121,'down',0),(105,'sideways',0),(105,'down',4),(105,'down',-1),(105,'down',True),(105,'down',0,3),(105,'down',0,-1),(105,'down',0,True)):
            with self.assertRaises(ValueError):self.art.field(*args)
        for fid in (-1,0,104,121,256,'105',True):
            with self.assertRaises(ValueError):self.art.portrait(fid)

if __name__=='__main__':unittest.main(verbosity=2)
