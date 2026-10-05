#!/usr/bin/env python3
"""Independent region asset checks. No game/save/UI mutations.

Verifies committed PNG/C bytes, exact shared palette, half-open collision,
cardinal 5px-foot accessibility, native DMA crops, deterministic regeneration,
and a real ARM object budget where the supplied compiler is present.
"""
from collections import deque
from pathlib import Path
import hashlib, importlib.util, json, re, shutil, subprocess, sys, tempfile, unittest
from PIL import Image, ImageDraw
sys.dont_write_bytecode = True
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/region'
LAYOUT=json.loads((OUT/'layout.json').read_text())
CONTRACT=json.loads((OUT/'contract.json').read_text())
C_TEXT=''.join(p.read_text() for p in sorted((ROOT/'src/region_art_data').glob('part_*.inc')))
C_NO_COMMENTS=re.sub(r'/\*.*?\*/','',C_TEXT,flags=re.S)
BLOBS={name:bytes(map(int,re.findall(r'\d+',body))) for name,body in re.findall(r'const unsigned char (region_background_\w+)\[\d+\].*?= \{(.*?)\};',C_TEXT,re.S)}
spec=importlib.util.spec_from_file_location('region_original_palette',ROOT/'assets/generate_assets.py')
BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)


def rectangle_overlap(a,b):
    return a[0]<b[0]+b[2] and b[0]<a[0]+a[2] and a[1]<b[1]+b[3] and b[1]<a[1]+a[3]


def blocked_mask(room,closed,radius=5):
    w,h=room['width'],room['height'];mask=Image.new('L',(w,h));d=ImageDraw.Draw(mask)
    # Independently rasterize the square foot Minkowski expansion of each solid.
    d.rectangle((0,0,w-1,radius-1),fill=1);d.rectangle((0,h-radius,w-1,h-1),fill=1)
    d.rectangle((0,0,radius-1,h-1),fill=1);d.rectangle((w-radius,0,w-1,h-1),fill=1)
    rects=[s['rect'] for s in room['solids']]
    if closed:rects += [s['rect'] for s in room['dynamic_rectangles'] if s['closed_by_default']]
    for x,y,rw,rh in rects:d.rectangle((x-radius,y-radius,x+rw-1+radius,y+rh-1+radius),fill=1)
    return mask.tobytes()


def flood(room,closed):
    w,h=room['width'],room['height'];blocked=blocked_mask(room,closed)
    sx,sy=room['spawns']['0'];start=sx+sy*w;seen=bytearray(w*h);q=deque([start]);seen[start]=1
    while q:
        p=q.popleft();x=p%w;y=p//w
        for nx,ny in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
            if 0<=nx<w and 0<=ny<h:
                n=ny*w+nx
                if not seen[n] and not blocked[n]:seen[n]=1;q.append(n)
    return seen,blocked


OPTIONAL_OVERVIEWS={
    "region_preview_native.png", "region_preview_2x.png",
    "native_camera_sheet.png", "native_camera_sheet_2x.png",
}


def generated_hashes(include_optional=False):
    files=list(OUT.rglob('*'))+[ROOT/'src/region_art.c',ROOT/'src/region_art.h']+list((ROOT/'src/region_art_data').glob('*.inc'))
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file() and (include_optional or p.name not in OPTIONAL_OVERVIEWS)}


class RegionArtTests(unittest.TestCase):
    def test_contract_spawns_unchanged(self):
        self.assertEqual([r['id'] for r in LAYOUT['rooms']],list(range(16,22)))
        for room,c in zip(LAYOUT['rooms'],CONTRACT['rooms']):
            self.assertEqual([room['width'],room['height']],c['size'])
            self.assertEqual(room['spawns'],c['spawns'])
            self.assertEqual(room['name'],c['name'])

    def test_native_pngs_and_exact_palette(self):
        hashes=set()
        self.assertEqual(len(BASE.COLORS),178)
        for room in LAYOUT['rooms']:
            key=room['key'];im=Image.open(OUT/f'{key}.png')
            self.assertEqual(im.mode,'P');self.assertEqual(im.size,(room['width'],room['height']))
            self.assertEqual(im.getpalette(),BASE.PAL)
            data=im.tobytes();self.assertGreater(min(data),0);self.assertLess(max(data),178)
            self.assertEqual(BLOBS['region_background_'+key],data)
            hashes.add(hashlib.sha256(data).hexdigest())
        self.assertEqual(len(hashes),6,'Every room must have its own original composition')
        for i,name in enumerate(LAYOUT['sprites']['names']):
            im=Image.open(OUT/'sprites'/f'{name.lower()}.png')
            self.assertEqual(im.size,(16,16));self.assertEqual(im.mode,'P');self.assertEqual(im.info.get('transparency'),0)
            self.assertEqual(im.getpalette(),BASE.PAL);self.assertIn(0,im.tobytes());self.assertLess(max(im.tobytes()),178)
            self.assertEqual(LAYOUT['sprites']['indices'][name],i)

    def test_c_sprite_bytes_and_symbols(self):
        body=re.search(r'const unsigned char region_sprites\[REGION_SPR_COUNT\]\[256\].*?= \{(.*?)\};',C_NO_COMMENTS,re.S).group(1)
        data=bytes(map(int,re.findall(r'\d+',body)))
        expected=b''.join(Image.open(OUT/'sprites'/f'{n.lower()}.png').tobytes() for n in LAYOUT['sprites']['names'])
        self.assertEqual(data,expected)
        header=(ROOT/'src/region_art.h').read_text()
        for i,name in enumerate(LAYOUT['sprites']['names']):self.assertIn(f'REGION_SPR_{name} = {i}',header)
        self.assertIn('REGION_ART_FOOT_RADIUS 5',header)
        self.assertIn('REGION_ART_FIRST_ROOM 16',header)

    def test_camera_dma_every_x_and_native_rows(self):
        for room in LAYOUT['rooms'][:2]:
            w,h=room['width'],room['height'];key='region_background_'+room['key'];data=BLOBS[key];odd=BLOBS[key+'_odd']
            self.assertEqual(len(data),w*h);self.assertEqual(len(odd),w*h)
            for y in range(h):
                self.assertEqual(odd[y*w:(y+1)*w-1],data[y*w+1:(y+1)*w]);self.assertEqual(odd[(y+1)*w-1],data[(y+1)*w-1])
            for camera_y in (0,1,79,80,159,160):
                for camera_x in range(241):
                    source=odd if camera_x&1 else data;offset=camera_x-(camera_x&1)
                    self.assertEqual(offset%2,0)
                    crop=b''.join(source[(camera_y+y)*w+offset:(camera_y+y)*w+offset+240] for y in range(160))
                    expected=b''.join(data[(camera_y+y)*w+camera_x:(camera_y+y)*w+camera_x+240] for y in range(160))
                    self.assertEqual(crop,expected)
        for p in (OUT/'camera').glob('*.png'):
            with Image.open(p) as im:self.assertEqual(im.size,(240,160))
        for room in LAYOUT['rooms'][2:]:self.assertNotIn('region_background_'+room['key']+'_odd',BLOBS)

    def test_collision_contract_and_disjoint_dynamic_objects(self):
        for room in LAYOUT['rooms']:
            w,h=room['width'],room['height']
            for s in room['solids']+room['dynamic_rectangles']:
                x,y,rw,rh=s['rect'];self.assertGreater(rw,0);self.assertGreater(rh,0)
                self.assertGreaterEqual(x,0);self.assertGreaterEqual(y,0);self.assertLessEqual(x+rw,w);self.assertLessEqual(y+rh,h)
            for dyn in room['dynamic_rectangles']:
                for static in room['solids']:self.assertFalse(rectangle_overlap(dyn['rect'],static['rect']),(room['key'],dyn,static))
            cbody=re.search(rf'const RegionArtRect region_{room["key"]}_solids\[.*?\] = \{{(.*?)\}};',C_NO_COMMENTS,re.S).group(1)
            numbers=list(map(int,re.findall(r'-?\d+',cbody)))
            self.assertEqual([numbers[i:i+4] for i in range(0,len(numbers),4)],[s['rect'] for s in room['solids']])
            for o in room['objects']:
                self.assertEqual(o['sprite_index'],LAYOUT['sprites']['indices'][o['sprite']])
                self.assertLess(sum(abs(c-p) for c,p in zip(o['center'],o['approach'])),o['interaction_radius'])

    def test_cardinal_radius_five_every_exit_spawn_interaction(self):
        total=0
        for room in LAYOUT['rooms']:
            w=room['width'];targets=list(room['spawns'].items())+[(o['key'],o['approach']) for o in room['objects']]+[(e['key'],e['approach']) for e in room['exits']]
            for closed in (False,True):
                reachable,blocked=flood(room,closed)
                for key,(x,y) in targets:
                    self.assertFalse(blocked[y*w+x],(room['key'],key,'overlap',closed))
                    self.assertTrue(reachable[y*w+x],(room['key'],key,'unreachable',closed));total+=1
        self.assertEqual(total,140)

    def test_chunk_and_rom_budget(self):
        parts=sorted((ROOT/'src/region_art_data').glob('*.inc'))
        self.assertEqual(len(parts),LAYOUT['generated']['chunks'])
        self.assertTrue(all(0<p.stat().st_size<=32000 for p in parts))
        self.assertEqual(max(p.stat().st_size for p in parts),LAYOUT['generated']['largest_chunk_bytes'])
        budget=LAYOUT['generated']
        self.assertEqual(budget['bitmap_bytes'],768000);self.assertEqual(budget['sprite_bytes'],40*256)
        self.assertEqual(budget['rom_payload_bytes'],sum(budget[k] for k in ('bitmap_bytes','sprite_bytes','collision_bytes','arm32_room_table_bytes')))
        self.assertLess(budget['rom_payload_bytes'],800000)
        self.assertLess((ROOT/'src/region_art.c').stat().st_size,8192)

    def test_real_arm_object_is_readonly_and_matches_budget(self):
        compiler=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc'
        if not compiler.exists():
            candidate=shutil.which('arm-none-eabi-gcc')
            if not candidate:self.skipTest('ARM compiler is not installed; all source/PNG/navigation checks still ran')
            compiler=Path(candidate)
        prefix=str(compiler)[:-len('gcc')]
        with tempfile.TemporaryDirectory(prefix='region-art-') as tmp:
            obj=Path(tmp)/'region_art.o'
            subprocess.run([str(compiler),'-mcpu=arm7tdmi','-mthumb','-O2','-std=c99','-ffreestanding','-Wall','-Wextra','-Werror','-c',str(ROOT/'src/region_art.c'),'-o',str(obj)],check=True,capture_output=True,text=True)
            size=subprocess.check_output([prefix+'size','-A',str(obj)],text=True)
            sections={name:int(n) for name,n in re.findall(r'^(\.[\w.]+)\s+(\d+)\s+\d+',size,re.M)}
            self.assertEqual(sections.get('.data',0),0);self.assertEqual(sections.get('.bss',0),0);self.assertEqual(sections.get('.text',0),0)
            self.assertEqual(sections['.rodata'],LAYOUT['generated']['rom_payload_bytes'])
            symbols=subprocess.check_output([prefix+'nm','-S',str(obj)],text=True)
            for room in LAYOUT['rooms']:
                name='region_background_'+room['key']
                for sym in [name]+([name+'_odd'] if room['width']>240 else []):
                    match=re.search(rf'^([0-9a-f]+) ([0-9a-f]+) R {sym}$',symbols,re.M)
                    self.assertIsNotNone(match,sym);self.assertEqual(int(match[1],16)%4,0)
                    self.assertEqual(int(match[2],16),room['width']*room['height'])

    def test_z_deterministic_regeneration_and_readonly_contract(self):
        before=generated_hashes();contract=(OUT/'contract.json').read_bytes()
        existing_optional={k:v for k,v in generated_hashes(True).items() if Path(k).name in OPTIONAL_OVERVIEWS}
        with tempfile.TemporaryDirectory(prefix='region-regenerate-') as cwd:
            subprocess.run([sys.executable,str(ROOT/'assets/generate_region.py')],cwd=cwd,check=True,capture_output=True,text=True)
            self.assertEqual((OUT/'contract.json').read_bytes(),contract)
            self.assertEqual(generated_hashes(),before,'Every shipped artifact must reproduce exactly')
            all_after=generated_hashes(True)
            for name,digest in existing_optional.items():self.assertEqual(all_after[name],digest)
            self.assertEqual({Path(k).name for k in all_after if Path(k).name in OPTIONAL_OVERVIEWS},OPTIONAL_OVERVIEWS)
            # A clean source archive intentionally omits these large, redundant
            # review sheets. Their first generation is allowed; the second must
            # reproduce every optional and shipped byte without changing input.
            subprocess.run([sys.executable,str(ROOT/'assets/generate_region.py')],cwd=cwd,check=True,capture_output=True,text=True)
        self.assertEqual((OUT/'contract.json').read_bytes(),contract)
        self.assertEqual(generated_hashes(True),all_after)


if __name__=='__main__':unittest.main(verbosity=2)
