#!/usr/bin/env python3
"""Independent original Underwater art, camera and exact geometry regression tests.

These are deterministic host proofs; native controller/visual QA is separate.
"""
from collections import deque
from pathlib import Path
import hashlib, importlib.util, json, re, subprocess, sys, tempfile, unittest
from PIL import Image, ImageDraw
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'assets/underwater_region'
sys.dont_write_bytecode=True
spec=importlib.util.spec_from_file_location('underwater_palette',ROOT/'assets/generate_assets.py')
P=importlib.util.module_from_spec(spec);spec.loader.exec_module(P)
DATA=json.loads((OUT/'layout.json').read_text())
C=''.join(p.read_text() for p in sorted((ROOT/'src/underwater_art_data').glob('*.inc')))
BLOBS={n:bytes(map(int,re.findall(r'\d+',body))) for n,body in re.findall(r'const unsigned char (underwater_background_\w+)\[\d+\].*?= \{(.*?)\};',C,re.S)}
def flood(r):
 w,h=r['width'],r['height'];im=Image.new('L',(w,h));d=ImageDraw.Draw(im)
 d.rectangle((0,0,w-1,4),fill=1);d.rectangle((0,h-5,w-1,h-1),fill=1)
 d.rectangle((0,0,4,h-1),fill=1);d.rectangle((w-5,0,w-1,h-1),fill=1)
 for s in r['solids']:
  x,y,bw,bh=s['rect'];d.rectangle((x-5,y-5,x+bw+4,y+bh+4),fill=1)
 blocked=im.tobytes();x,y=r['spawns']['0'];seen=bytearray(w*h);seen[y*w+x]=1;q=deque([y*w+x])
 while q:
  v=q.popleft();x=v%w;y=v//w
  for xx,yy in((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<w and 0<=yy<h:
    n=yy*w+xx
    if not seen[n] and not blocked[n]:seen[n]=1;q.append(n)
 return seen,blocked
class UnderwaterArt(unittest.TestCase):
 def test_frozen_native_palette_and_rom_source_identity(self):
  self.assertEqual(len(P.COLORS),178)
  self.assertEqual([r['id'] for r in DATA['rooms']],list(range(46,54)))
  self.assertEqual([r['width'] for r in DATA['rooms']],[480,480,480,240,240,480,240,240])
  unique=set()
  for r in DATA['rooms']:
   with Image.open(OUT/(r['key']+'.png')) as im:
    self.assertEqual(im.mode,'P');self.assertEqual(im.size,(r['width'],r['height']));self.assertEqual(im.getpalette(),P.PAL)
    a=im.tobytes();unique.add(a);self.assertEqual(BLOBS['underwater_background_'+r['key']],a)
    self.assertGreater(min(a),0);self.assertLess(max(a),178)
    self.assertEqual(hashlib.sha256(a).hexdigest(),r['bitmap_sha256'])
   with Image.open(OUT/(r['key']+'_4x.png')) as large:
    self.assertEqual(large.size,(r['width']*4,r['height']*4))
    self.assertEqual(large.resize((r['width'],r['height']),Image.Resampling.NEAREST).tobytes(),a)
  self.assertEqual(len(unique),8)
 def test_every_scrolling_camera_column_alignment(self):
  for r in DATA['rooms']:
   if r['width']!=480:continue
   a=BLOBS['underwater_background_'+r['key']];b=BLOBS['underwater_background_'+r['key']+'_odd']
   for y in range(320):
    self.assertEqual(b[y*480:(y+1)*480-1],a[y*480+1:(y+1)*480]);self.assertEqual(b[(y+1)*480-1],a[(y+1)*480-1])
   for cy in(0,1,79,80,159,160):
    for cx in range(241):
     src=b if cx&1 else a;offset=cx-(cx&1)
     for dy in(0,1,79,159):self.assertEqual(src[(cy+dy)*480+offset:(cy+dy)*480+offset+240],a[(cy+dy)*480+cx:(cy+dy)*480+cx+240])
  for path in (OUT/'camera').glob('*.png'):
   with Image.open(path) as im:self.assertEqual(im.size,(240,160))
 def test_twenty_original_transparent_streamed_glyphs(self):
  self.assertEqual(len(DATA['sprites']['names']),20);unique=set()
  for n in DATA['sprites']['names']:
   with Image.open(OUT/'sprites'/(n.lower()+'.png')) as im:
    self.assertEqual(im.mode,'P');self.assertEqual(im.size,(16,16));self.assertEqual(im.info['transparency'],0);self.assertEqual(im.getpalette(),P.PAL)
    unique.add(im.tobytes());self.assertIn(0,im.tobytes());self.assertGreater(sum(v!=0 for v in im.tobytes()),30)
  self.assertEqual(len(unique),20)
  self.assertEqual(DATA['generated']['permanent_new_obj_bytes'],0)
  self.assertEqual(DATA['generated']['maximum_streamed_obj_slots'],20)
  self.assertLessEqual(DATA['generated']['ambient_obj_limit'],8)
 def test_every_spawn_exit_interaction_and_enemy_reachable(self):
  for r in DATA['rooms']:
   seen,blocked=flood(r)
   targets=list(r['spawns'].values())+[o['approach'] for o in r['objects']]+[e['approach'] for e in r['exits']]+r['enemy_spawns']+[t['approach'] for t in r['reserved_runtime_targets']]
   for x,y in targets:
    self.assertFalse(blocked[y*r['width']+x],(r['key'],x,y));self.assertTrue(seen[y*r['width']+x],(r['key'],x,y))
   # All branch-trial configurations get an entire invariant clear board.
   cx,cy=(240,160) if r['width']==480 else (120,80)
   for y in range(cy-32,cy+33):
    for x in range(cx-64,cx+65):self.assertFalse(blocked[y*r['width']+x],(r['key'],'trial board',x,y))
 def test_actual_runtime_a_targets_have_reachable_facing_approaches(self):
  source=(ROOT/'src/underwater_game.c').read_text()
  source=source[source.index('COLD int underwater_game_interact'):source.index('int underwater_game_power')]
  for r in DATA['rooms']:
   part=re.search(r'if\(room=='+str(r['id'])+r'\)\{(.*?)(?=\n if\(room==|\n /\* General)',source,re.S)
   actual=set(tuple(map(int,p)) for p in re.findall(r'close\((\d+),(\d+)\)',part[1])) if part else set()
   recorded={tuple(t['center']) for t in r['reserved_runtime_targets']}
   self.assertEqual(actual,recorded,(r['key'],'runtime targets changed; review authoring snapshot'))
   for t in r['reserved_runtime_targets']:
    x,y=t['center'];xx,yy=t['approach'];distance=abs(x-xx)+abs(y-yy)
    self.assertTrue(x==xx or y==yy);self.assertGreaterEqual(distance,6);self.assertLessEqual(distance,26)
 def test_collision_table_matches_every_expanded_solid_pixel(self):
  arrays={n:list(map(int,re.findall(r'\d+',body))) for n,body in re.findall(r'static const unsigned short (underwater_\w+_collision_(?:rows|bands))\[\d+\] = \{(.*?)\};',C,re.S)}
  for r in DATA['rooms']:
   rows=arrays['underwater_'+r['key']+'_collision_rows'];bands=arrays['underwater_'+r['key']+'_collision_bands'];actual=bytearray(r['width']*r['height'])
   for y,o in enumerate(rows):
    for j in range(bands[o]):
     lo,hi=bands[o+1+j*2:o+3+j*2];actual[y*r['width']+lo:y*r['width']+hi]=b'\1'*(hi-lo)
   self.assertEqual(actual,flood(r)[1],r['key'])
 def test_compiled_const_descriptors_and_lookup(self):
  code=r'''#include <stdio.h>
#include "underwater_art.h"
int main(void) {
 unsigned i,x,y,j; unsigned long checked=0;
 if(UNDERWATER_SPR_COUNT!=20 || UNDERWATER_ART_FIRST_ROOM!=46) return 1;
 for(i=0;i<8;i++) {
  const UnderwaterArtRoom *r=&underwater_art_rooms[i];
  if(!r->bitmap || !r->solids || !r->collision_rows || !r->collision_bands) return 2;
  if((r->width==480)!=(r->bitmap_odd!=0)) return 3;
  for(y=0;y<r->height;y++) for(x=0;x<r->width;x++) {
   int expected=x<5 || y<5 || x>=r->width-5u || y>=r->height-5u;
   int actual=0; const unsigned short *b=r->collision_bands+r->collision_rows[y];
   for(j=0;j<r->solid_count;j++) { const UnderwaterArtRect *s=&r->solids[j];
    if((int)x>=s->x-5 && (int)x<s->x+s->w+5 && (int)y>=s->y-5 && (int)y<s->y+s->h+5) expected=1;
   }
   for(j=0;j<b[0];j++) if(x>=b[1+j*2] && x<b[2+j*2]) actual=1;
   if(expected!=actual) return 4;
   if(!r->bitmap[y*r->width+x] || r->bitmap[y*r->width+x]>=178) return 5;
   checked++;
  }
 }
 printf("%lu exact native pixels\n",checked); return 0;
}'''
  with tempfile.TemporaryDirectory() as td:
   src=Path(td)/'art.c';exe=Path(td)/'art';src.write_text(code)
   subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Isrc',str(src),'src/underwater_art.c','-o',str(exe)],cwd=ROOT,check=True,capture_output=True)
   r=subprocess.run([str(exe)],check=True,capture_output=True,text=True)
   self.assertIn('768000 exact native pixels',r.stdout)
 def test_budgets_and_deterministic_regeneration(self):
  self.assertLess(DATA['generated']['rom_payload_bytes'],1400*1024)
  for path in (ROOT/'src/underwater_art_data').glob('*.inc'):self.assertLessEqual(path.stat().st_size,30000)
  for path in OUT.glob('*.json'):self.assertLessEqual(path.stat().st_size,30000)
  files=[p for p in OUT.rglob('*') if p.is_file()]+list((ROOT/'src/underwater_art_data').glob('*.inc'))+[ROOT/'src/underwater_art.c',ROOT/'src/underwater_art.h']
  before={str(p):hashlib.sha256(p.read_bytes()).digest() for p in files}
  subprocess.run([sys.executable,'assets/generate_underwater_region.py'],cwd=ROOT,check=True,capture_output=True)
  self.assertEqual(before,{str(p):hashlib.sha256(p.read_bytes()).digest() for p in files})
if __name__=='__main__':unittest.main(verbosity=2)
