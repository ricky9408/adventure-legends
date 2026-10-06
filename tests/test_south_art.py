#!/usr/bin/env python3
"""Independent native palette, camera, fixture and exact-foot geometry checks."""
from collections import deque
from pathlib import Path
import ctypes,hashlib,importlib.util,itertools,json,re,subprocess,sys,tempfile,unittest
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/southern_region'
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('south_palette',ROOT/'assets/generate_assets.py');BASE=importlib.util.module_from_spec(spec);spec.loader.exec_module(BASE)
LAYOUT=json.loads((OUT/'layout.json').read_text());CONTRACT=json.loads((OUT/'contract.json').read_text());SCENE=json.loads((OUT/'scene.json').read_text())
C=''.join(p.read_text()for p in sorted((ROOT/'src/south_art_data').glob('*.inc')))
BLOBS={n:bytes(map(int,re.findall(r'\d+',body)))for n,body in re.findall(r'const unsigned char (south_background_\w+)\[\d+\].*?= \{(.*?)\};',C,re.S)}
def hashes():
 files=list(OUT.rglob('*'))+[ROOT/'src/south_art.c',ROOT/'src/south_art.h']+list((ROOT/'src/south_art_data').glob('*.inc'))
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
class SouthernArt(unittest.TestCase):
 def test_palette_native_pixels_and_source_bytes(self):
  self.assertEqual(len(BASE.COLORS),178);unique=set();self.assertEqual([r['id']for r in LAYOUT['rooms']],list(range(30,38)))
  for r,c in zip(LAYOUT['rooms'],CONTRACT['rooms']):
   im=Image.open(OUT/(r['key']+'.png'));self.assertEqual(im.size,tuple(c['size']));self.assertEqual(im.mode,'P');self.assertEqual(im.getpalette(),BASE.PAL);self.assertEqual(r['spawns'],c['spawns']);data=im.tobytes();self.assertGreater(min(data),0);self.assertLess(max(data),178);self.assertEqual(BLOBS['south_background_'+r['key']],data);unique.add(data)
  self.assertEqual(len(unique),8)
  for n in LAYOUT['sprites']['names']:
   im=Image.open(OUT/'sprites'/(n.lower()+'.png'));self.assertEqual(im.mode,'P');self.assertEqual(im.size,(16,16));self.assertEqual(im.info['transparency'],0);self.assertEqual(im.getpalette(),BASE.PAL);self.assertIn(0,im.tobytes());self.assertLess(max(im.tobytes()),178)
 def test_every_x_camera_crops(self):
  for r in LAYOUT['rooms'][:2]:
   k='south_background_'+r['key'];a=BLOBS[k];b=BLOBS[k+'_odd'];w=r['width']
   for y in range(320):self.assertEqual(b[y*w:(y+1)*w-1],a[y*w+1:(y+1)*w]);self.assertEqual(b[(y+1)*w-1],a[(y+1)*w-1])
   for cy in(0,1,79,80,159,160):
    for cx in range(241):
     src=b if cx&1 else a;offset=cx-(cx&1);self.assertEqual(offset%2,0)
     for dy in range(160):self.assertEqual(src[(cy+dy)*w+offset:(cy+dy)*w+offset+240],a[(cy+dy)*w+cx:(cy+dy)*w+cx+240])
  for p in(OUT/'camera').glob('*.png'):
   with Image.open(p)as im:self.assertEqual(im.size,(240,160))
 def test_every_spawn_exit_object_enemy_with_five_pixel_foot(self):
  for r,source in zip(LAYOUT['rooms'],SCENE['objects']):
   seen,blocked=flood(r);w=r['width'];targets=list(r['spawns'].values())+[o['approach']for o in r['objects']]+[e['approach']for e in r['exits']]+r['enemy_spawns']
   self.assertEqual(r['dynamic_rectangles'],[])
   for x,y in targets:self.assertFalse(blocked[y*w+x],(r['key'],x,y));self.assertTrue(seen[y*w+x],(r['key'],x,y))
   self.assertEqual(len(r['objects']),len(source))
   for o,s in zip(r['objects'],source):
    for key in s:self.assertEqual(o[key],s[key])
    self.assertLess(sum(abs(a-b)for a,b in zip(o['center'],o['approach'])),o['interaction_radius'])
   if r['id']>=32:self.assertTrue(any(o['key']=='reset'for o in r['objects']));self.assertTrue(any(e['rect']==[108,144,24,16]for e in r['exits']))
   if r['id']==37:
    for x,y in[(24,112),(216,112),(120,144)]:self.assertTrue(seen[y*w+x]);self.assertFalse(blocked[y*w+x])
  self.assertEqual(len(LAYOUT['rooms'][1]['enemy_spawns']),5);self.assertEqual(len(LAYOUT['rooms'][3]['enemy_spawns']),2)
 def test_no_baked_dynamic_diagonal_or_screen(self):
  moving={'MIRROR_SLASH','MIRROR_BACK','SHADE_CLOSED','SHADE_OPEN','MACHINE_IDLE','MACHINE_WARN','MACHINE_OPEN','GATE','HOOD'}
  for r in LAYOUT['rooms']:
   for o in r['objects']:
    if o['kind']in moving:self.assertFalse(o['static_baked'],(r['key'],o['key']))
  tree=[s['rect']for s in LAYOUT['rooms'][6]['solids']if s['kind']=='living_optical_tree'];self.assertEqual(tree,[[112,72,24,28]])
  self.assertTrue(all(s['rect'][1]+s['rect'][3]<=24 for s in LAYOUT['rooms'][2]['solids']if s['kind']=='upper_wall'))
 def test_permanent_shortcut_approaches_and_existing_destinations(self):
  for area,key,xy,target,spawn,condition in[(32,'market_shortcut',[208,64],30,4,('requires_quest_ready',29)),(36,'field_shortcut',[208,112],31,1,('requires_sunwell_objectives',4))]:
   r=LAYOUT['rooms'][area-30];o=next(o for o in r['objects']if o['key']==key);e=next(e for e in r['exits']if e['key']==key);self.assertEqual(o['center'],xy);self.assertEqual(o['kind'],'GATE');self.assertFalse(o['static_baked']);self.assertEqual(e['approach'],o['approach']);self.assertEqual(e['target'],target);self.assertEqual(e['target_spawn'],spawn);self.assertEqual(e[condition[0]],condition[1]);self.assertIn(str(spawn),CONTRACT['rooms'][target-30]['spawns'])
   seen,blocked=flood(r)
   for x,y in[o['center'],o['approach']]:self.assertFalse(blocked[y*r['width']+x]);self.assertTrue(seen[y*r['width']+x])
 def test_exact_deduplicated_collision_rows(self):
  arrays={n:list(map(int,re.findall(r'\d+',body)))for n,body in re.findall(r'static const unsigned short (south_\w+_collision_(?:rows|bands))\[\d+\] = \{(.*?)\};',C,re.S)}
  count=0
  for r in LAYOUT['rooms']:
   rows=arrays['south_'+r['key']+'_collision_rows'];bands=arrays['south_'+r['key']+'_collision_bands'];self.assertEqual(len(rows),r['height']);count+=2*(len(rows)+len(bands))
   _,expected=flood(r);rebuilt=bytearray(r['width']*r['height']);unique={}
   for y,offset in enumerate(rows):
    num=bands[offset];self.assertGreater(num,0);self.assertLessEqual(offset+1+num*2,len(bands));key=tuple(bands[offset+1:offset+1+num*2]);self.assertEqual(unique.setdefault(key,offset),offset);last=-1
    for i in range(num):
     lo,hi=key[i*2:i*2+2];self.assertLess(lo,hi);self.assertGreater(lo,last);self.assertGreaterEqual(lo,0);self.assertLessEqual(hi,r['width']);last=hi;rebuilt[y*r['width']+lo:y*r['width']+hi]=bytes([1])*(hi-lo)
   self.assertEqual(rebuilt,expected,r['key']);self.assertEqual(len(unique),r['collision_lookup']['unique_bands'])
  self.assertEqual(LAYOUT['generated']['collision_lookup_bytes'],count)
 def test_sprite_and_artifact_budgets(self):
  body=re.search(r'const unsigned char south_sprites\[SOUTH_SPR_COUNT\]\[256\].*?= \{(.*?)\};',C,re.S).group(1);body=re.sub(r'/\*.*?\*/','',body,flags=re.S);data=bytes(map(int,re.findall(r'\d+',body)))
  self.assertEqual(data,b''.join(Image.open(OUT/'sprites'/(n.lower()+'.png')).tobytes()for n in LAYOUT['sprites']['names']))
  self.assertLess(LAYOUT['generated']['rom_payload_bytes'],1.35*1024*1024)
  for p in(ROOT/'src/south_art_data').glob('*.inc'):self.assertLessEqual(p.stat().st_size,30000)
  for p in OUT.glob('*.json'):self.assertLessEqual(p.stat().st_size,30000)
  for p in OUT.rglob('*.png'):self.assertLess(p.stat().st_size,70000)
  self.assertFalse((OUT/'southern_preview_native.png').exists(),'Large contact sheet must remain build-only')
  self.assertNotIn('.iwram',(ROOT/'src/south_art.c').read_text()+C)
 def test_deterministic_regeneration(self):
  before=hashes();subprocess.run([sys.executable,'assets/generate_southern_region.py'],cwd=ROOT,check=True,stdout=subprocess.PIPE);self.assertEqual(before,hashes())
 def test_production_optical_segments_respect_raw_art_solids(self):
  # Compile the unchanged pure optics functions from production, together with
  # real art data, without the unrelated persistence/UI harness.
  source=(ROOT/'src/south_game.c').read_text();a=source.index('static int puzzle_valid(');b=source.index('static int contains(',a)
  class Puzzle(ctypes.Structure):_fields_=[('mirror',ctypes.c_ubyte*2),('shade',ctypes.c_ubyte)]
  class Beam(ctypes.Structure):_fields_=[('x1',ctypes.c_short),('y1',ctypes.c_short),('x2',ctypes.c_short),('y2',ctypes.c_short),('end_kind',ctypes.c_ubyte)]
  with tempfile.TemporaryDirectory(prefix='south-art-optics-')as folder:
   folder=Path(folder);(folder/'rays.c').write_text('#include "south_game.h"\n#include "south_art.h"\n'+source[a:b])
   subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC','-Isrc',str(folder/'rays.c'),'src/south_art.c','-o',str(folder/'rays.so')],cwd=ROOT,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
   lib=ctypes.CDLL(str(folder/'rays.so'));lib.south_puzzle_beam.argtypes=[ctypes.POINTER(Puzzle),ctypes.c_uint,ctypes.POINTER(Beam)];lib.south_puzzle_beam.restype=ctypes.c_uint
   for area in(34,35,36):
    r=LAYOUT['rooms'][area-30]
    def blocked(x,y):return not(0<=x<r['width']and 0<=y<r['height'])or any(rx<=x<rx+rw and ry<=y<ry+rh for rx,ry,rw,rh in(s['rect']for s in r['solids']))
    for state in itertools.product(range(2),repeat=3):
     p=Puzzle((ctypes.c_ubyte*2)(*state[:2]),state[2]);segments=(Beam*4)();n=lib.south_puzzle_beam(ctypes.byref(p),area,segments);self.assertTrue(1<=n<=4)
     for seg in segments[:n]:
      self.assertTrue(seg.x1==seg.x2 or seg.y1==seg.y2);dx=(seg.x2>seg.x1)-(seg.x2<seg.x1);dy=(seg.y2>seg.y1)-(seg.y2<seg.y1);steps=abs(seg.x2-seg.x1)+abs(seg.y2-seg.y1)
      for k in range(1,steps):self.assertFalse(blocked(seg.x1+k*dx,seg.y1+k*dy),(area,state,tuple((seg.x1,seg.y1,seg.x2,seg.y2)),k))
      if seg.end_kind==0:self.assertTrue(blocked(seg.x2,seg.y2),(area,state,seg.x2,seg.y2))
      else:self.assertFalse(blocked(seg.x2,seg.y2),(area,state,seg.x2,seg.y2))
 def test_host_c_syntax(self):
  subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsyntax-only','src/south_art.c'],cwd=ROOT,check=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
if __name__=='__main__':unittest.main()
