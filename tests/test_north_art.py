#!/usr/bin/env python3
"""Independent native art/palette/collision/camera/archive-size verification."""
from collections import deque
from pathlib import Path
import hashlib,importlib.util,json,re,subprocess,sys,unittest
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/northern_region'
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('north_palette',ROOT/'assets/generate_assets.py');BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
LAYOUT=json.loads((OUT/'layout.json').read_text());CONTRACT=json.loads((OUT/'contract.json').read_text())
C=''.join(p.read_text()for p in sorted((ROOT/'src/north_art_data').glob('*.inc')))
BLOBS={n:bytes(map(int,re.findall(r'\d+',body)))for n,body in re.findall(r'const unsigned char (north_background_\w+)\[\d+\].*?= \{(.*?)\};',C,re.S)}
def hashes():
 files=list(OUT.rglob('*'))+[ROOT/'src/north_art.c',ROOT/'src/north_art.h']+list((ROOT/'src/north_art_data').glob('*.inc'))
 return{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files if p.is_file()}
def flood(r):
 w,h=r['width'],r['height'];im=Image.new('L',(w,h));d=ImageDraw.Draw(im)
 d.rectangle((0,0,w-1,4),fill=1);d.rectangle((0,h-5,w-1,h-1),fill=1);d.rectangle((0,0,4,h-1),fill=1);d.rectangle((w-5,0,w-1,h-1),fill=1)
 for b in r['solids']:
  x,y,bw,bh=b['rect'];d.rectangle((x-5,y-5,x+bw+4,y+bh+4),fill=1)
 blocked=im.tobytes();x,y=r['spawns']['0'];start=y*w+x;seen=bytearray(w*h);seen[start]=1;todo=deque([start])
 while todo:
  p=todo.popleft();x=p%w;y=p//w
  for nx,ny in((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=nx<w and 0<=ny<h:
    n=ny*w+nx
    if not seen[n]and not blocked[n]:seen[n]=1;todo.append(n)
 return seen,blocked
class NorthernArt(unittest.TestCase):
 def test_native_palette_and_source_bytes(self):
  self.assertEqual(len(BASE.COLORS),178);unique=set()
  self.assertEqual([r['id']for r in LAYOUT['rooms']],list(range(22,30)))
  for r,c in zip(LAYOUT['rooms'],CONTRACT['rooms']):
   im=Image.open(OUT/(r['key']+'.png'));self.assertEqual(im.size,tuple(c['size']));self.assertEqual(im.mode,'P');self.assertEqual(im.getpalette(),BASE.PAL);self.assertEqual(r['spawns'],c['spawns']);data=im.tobytes();self.assertGreater(min(data),0);self.assertLess(max(data),178);self.assertEqual(BLOBS['north_background_'+r['key']],data);unique.add(data)
  self.assertEqual(len(unique),8)
  for n in LAYOUT['sprites']['names']:
   im=Image.open(OUT/'sprites'/(n.lower()+'.png'));self.assertEqual(im.mode,'P');self.assertEqual(im.size,(16,16));self.assertEqual(im.info['transparency'],0);self.assertEqual(im.getpalette(),BASE.PAL);self.assertIn(0,im.tobytes());self.assertLess(max(im.tobytes()),178)
 def test_native_every_x_camera_crops(self):
  for r in LAYOUT['rooms'][:2]:
   k='north_background_'+r['key'];a=BLOBS[k];b=BLOBS[k+'_odd'];w=r['width']
   for y in range(320):self.assertEqual(b[y*w:(y+1)*w-1],a[y*w+1:(y+1)*w]);self.assertEqual(b[(y+1)*w-1],a[(y+1)*w-1])
   for cy in(0,1,79,80,159,160):
    for cx in range(241):
     src=b if cx&1 else a;offset=cx-(cx&1);self.assertEqual(offset%2,0)
     for dy in range(160):self.assertEqual(src[(cy+dy)*w+offset:(cy+dy)*w+offset+240],a[(cy+dy)*w+cx:(cy+dy)*w+cx+240])
  for p in(OUT/'camera').glob('*.png'):
   with Image.open(p) as im:self.assertEqual(im.size,(240,160))
 def test_every_spawn_exit_object_with_five_pixel_foot(self):
  for r in LAYOUT['rooms']:
   seen,blocked=flood(r);w=r['width'];targets=list(r['spawns'].values())+[o['approach']for o in r['objects']]+[e['approach']for e in r['exits']]
   # Mechanisms have no movement-blocking geometry. All72 finite states share
   # these reset/exit routes; actors cannot close a walkway or crush a player.
   self.assertEqual(r['dynamic_rectangles'],[])
   for x,y in targets:self.assertFalse(blocked[y*w+x],(r['key'],x,y));self.assertTrue(seen[y*w+x],(r['key'],x,y))
   if r['id']>=24:self.assertTrue(any(o['key']=='reset'for o in r['objects']))
   for o in r['objects']:self.assertLess(sum(abs(a-b)for a,b in zip(o['center'],o['approach'])),o['interaction_radius'])
 def test_actor_data_archive_budgets(self):
  body=re.search(r'const unsigned char north_sprites\[NORTH_SPR_COUNT\]\[256\].*?= \{(.*?)\};',C,re.S).group(1);body=re.sub(r'/\*.*?\*/','',body,flags=re.S);data=bytes(map(int,re.findall(r'\d+',body)))
  self.assertEqual(data,b''.join(Image.open(OUT/'sprites'/(n.lower()+'.png')).tobytes()for n in LAYOUT['sprites']['names']))
  self.assertLessEqual(LAYOUT['generated']['rom_payload_bytes'],1310720)
  for p in(ROOT/'src/north_art_data').glob('*.inc'):self.assertLessEqual(p.stat().st_size,32000)
  for p in OUT.rglob('*.png'):self.assertLess(p.stat().st_size,70000)
  self.assertFalse((OUT/'northern_preview_native.png').exists(),'Large generated collage must remain build-only')
 def test_exact_deduplicated_row_band_collision(self):
  arrays={n:list(map(int,re.findall(r'\d+',body)))for n,body in re.findall(r'static const unsigned short (north_\w+_collision_(?:rows|bands))\[\d+\] = \{(.*?)\};',C,re.S)}
  for r in LAYOUT['rooms']:
   rows=arrays['north_'+r['key']+'_collision_rows'];bands=arrays['north_'+r['key']+'_collision_bands'];self.assertEqual(len(rows),r['height'])
   _,expected=flood(r);rebuilt=bytearray(r['width']*r['height']);unique={}
   for y,offset in enumerate(rows):
    count=bands[offset];self.assertGreater(count,0);self.assertLessEqual(offset+1+count*2,len(bands));key=tuple(bands[offset+1:offset+1+count*2]);self.assertEqual(unique.setdefault(key,offset),offset)
    last=-1
    for i in range(count):
     lo,hi=key[i*2:i*2+2];self.assertLess(lo,hi);self.assertGreater(lo,last);self.assertGreaterEqual(lo,0);self.assertLessEqual(hi,r['width']);last=hi
     rebuilt[y*r['width']+lo:y*r['width']+hi]=bytes([1])*(hi-lo)
   self.assertEqual(rebuilt,expected,r['key']);self.assertEqual(len(unique),r['collision_lookup']['unique_bands'])
  self.assertEqual(LAYOUT['generated']['collision_lookup_bytes'],4014)
 def test_japanese_ui_width_and_keys(self):
  f=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',12,index=0)
  for k,v in json.loads((OUT/'ui_additions.json').read_text()).items():self.assertLessEqual(f.getbbox(v)[2]+1,214,(k,v))
  self.assertIn('A ページ',json.loads((OUT/'ui_additions.json').read_text())['NT_KEYS'])
 def test_deterministic_regeneration(self):
  before=hashes();subprocess.run([sys.executable,'assets/generate_northern_region.py'],cwd=ROOT,check=True,stdout=subprocess.PIPE);self.assertEqual(before,hashes())
if __name__=='__main__':unittest.main()
