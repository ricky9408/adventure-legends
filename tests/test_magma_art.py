#!/usr/bin/env python3
"""Independent art/actual engine-foot reachability checks, not native QA."""
from collections import deque
from pathlib import Path
import hashlib,importlib.util,json,re,subprocess,sys,tempfile,unittest
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/magma_region'
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('magma_palette',ROOT/'assets/generate_assets.py');P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
DATA=json.loads((OUT/'layout.json').read_text());C=''.join(p.read_text()for p in sorted((ROOT/'src/magma_art_data').glob('*.inc')))
BLOBS={n:bytes(map(int,re.findall(r'\d+',body)))for n,body in re.findall(r'const unsigned char (magma_background_\w+)\[\d+\].*?= \{(.*?)\};',C,re.S)}
def flood(r):
 w,h=r['width'],r['height'];im=Image.new('L',(w,h));d=ImageDraw.Draw(im)
 d.rectangle((0,0,w-1,4),fill=1);d.rectangle((0,h-5,w-1,h-1),fill=1);d.rectangle((0,0,4,h-1),fill=1);d.rectangle((w-5,0,w-1,h-1),fill=1)
 for s in r['solids']:
  x,y,bw,bh=s['rect'];d.rectangle((x-5,y-5,x+bw+4,y+bh+4),fill=1)
 blocked=im.tobytes();x,y=r['spawns']['0'];seen=bytearray(w*h);seen[y*w+x]=1;q=deque([y*w+x])
 while q:
  v=q.popleft();x=v%w;y=v//w
  for xx,yy in((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<w and 0<=yy<h:
    n=yy*w+xx
    if not seen[n]and not blocked[n]:seen[n]=1;q.append(n)
 return seen,blocked
class MagmaArt(unittest.TestCase):
 def test_native_palette_source_bytes_and_camera_alignment(self):
  self.assertEqual(len(P.COLORS),178);self.assertEqual([r['id']for r in DATA['rooms']],list(range(38,46)));unique=set()
  for r in DATA['rooms']:
   im=Image.open(OUT/(r['key']+'.png'));self.assertEqual(im.mode,'P');self.assertEqual(im.size,(r['width'],r['height']));self.assertEqual(im.getpalette(),P.PAL);a=im.tobytes();unique.add(a);self.assertEqual(BLOBS['magma_background_'+r['key']],a);self.assertGreater(min(a),0);self.assertLess(max(a),178)
   if r['width']==480:
    b=BLOBS['magma_background_'+r['key']+'_odd']
    for y in range(320):self.assertEqual(b[y*480:(y+1)*480-1],a[y*480+1:(y+1)*480]);self.assertEqual(b[(y+1)*480-1],a[(y+1)*480-1])
    for cy in(0,1,79,80,159,160):
     for cx in range(241):
      src=b if cx&1 else a;offset=cx-(cx&1)
      for dy in(0,1,79,159):self.assertEqual(src[(cy+dy)*480+offset:(cy+dy)*480+offset+240],a[(cy+dy)*480+cx:(cy+dy)*480+cx+240])
  self.assertEqual(len(unique),8)
  for p in(OUT/'camera').glob('*.png'):
   with Image.open(p) as im:self.assertEqual(im.size,(240,160))
  for n in DATA['sprites']['names']:
   im=Image.open(OUT/'sprites'/(n.lower()+'.png'));self.assertEqual(im.mode,'P');self.assertEqual(im.size,(16,16));self.assertEqual(im.info['transparency'],0);self.assertEqual(im.getpalette(),P.PAL)
 def test_all_spawns_exits_clues_rewards_and_enemies_reachable(self):
  for r in DATA['rooms']:
   seen,blocked=flood(r)
   for x,y in list(r['spawns'].values())+[o['approach']for o in r['objects']]+[e['approach']for e in r['exits']]+r['enemy_spawns']:
    self.assertFalse(blocked[y*r['width']+x],(r['key'],x,y));self.assertTrue(seen[y*r['width']+x],(r['key'],x,y))
  # Proposed old-world arrival/NPC do not edit old art and do not collide
  # with previous chapter's descriptor positions or exact foot solids.
  old=json.loads((ROOT/'assets/southern_region/layout.json').read_text())['rooms'][0];seen,blocked=flood(old)
  for x,y in [(288,248),(288,264)]:
   self.assertFalse(blocked[y*480+x]);self.assertTrue(seen[y*480+x]);self.assertTrue(all(abs(x-o['center'][0])+abs(y-o['center'][1])>=32 for o in old['objects']))
 def test_collision_lookup_exactly_matches_expanded_half_open_solids(self):
  arrays={n:list(map(int,re.findall(r'\d+',body)))for n,body in re.findall(r'static const unsigned short (magma_\w+_collision_(?:rows|bands))\[\d+\] = \{(.*?)\};',C,re.S)}
  for r in DATA['rooms']:
   rows=arrays['magma_'+r['key']+'_collision_rows'];bands=arrays['magma_'+r['key']+'_collision_bands'];actual=bytearray(r['width']*r['height'])
   for y,o in enumerate(rows):
    for j in range(bands[o]):lo,hi=bands[o+1+j*2:o+3+j*2];actual[y*r['width']+lo:y*r['width']+hi]=b'\1'*(hi-lo)
   self.assertEqual(actual,flood(r)[1],r['key'])
 def test_exhaustive_actual_pixel_movable_state_proof(self):
  with tempfile.TemporaryDirectory()as td:
   exe=Path(td)/'geometry';subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Isrc','tests/magma_geometry_native.c','src/magma_art.c','-o',str(exe)],cwd=ROOT,check=True);r=subprocess.run([str(exe)],cwd=ROOT,check=True,text=True,capture_output=True);self.assertEqual(r.stdout.count('all reachable pixels exit'),4)
 def test_budgets_deterministic_regeneration(self):
  self.assertEqual(DATA['generated']['permanent_new_obj_bytes'],0);self.assertLess(DATA['generated']['rom_payload_bytes'],1024*1024)
  for p in(ROOT/'src/magma_art_data').glob('*.inc'):self.assertLessEqual(p.stat().st_size,30000)
  for p in OUT.glob('*.json'):self.assertLessEqual(p.stat().st_size,30000)
  files=[p for p in OUT.rglob('*')if p.is_file()]+list((ROOT/'src/magma_art_data').glob('*.inc'))+[ROOT/'src/magma_art.c',ROOT/'src/magma_art.h'];before={str(p):hashlib.sha256(p.read_bytes()).digest()for p in files};subprocess.run([sys.executable,'assets/generate_magma_region.py'],cwd=ROOT,check=True,capture_output=True);self.assertEqual(before,{str(p):hashlib.sha256(p.read_bytes()).digest()for p in files})
if __name__=='__main__':unittest.main(verbosity=2)
