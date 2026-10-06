#!/usr/bin/env python3
"""Exact host broad-phase equivalence, not controller or pacing evidence."""
import ctypes as C,hashlib,json,random,unittest
from pathlib import Path
from test_underwater_game import L,UnderwaterWorld,puzzle,ROOT
R=random.Random(91277)
class ClearBox(unittest.TestCase):
 def test_all_pixels_dynamic_states_and_rectangles(self):
  rows=[];checks=0
  for area in range(46,54):
   for ballast,b0,b1 in ([(b,0,0) for b in range(2)] if area in (50,51,53) else [(0,a,b) for a in range(2) for b in range(2)] if area==52 else [(0,0,0)]):
    C.c_int.in_dll(L,'room').value=area;L.underwater_game_reset();p=puzzle();p.ballast=ballast;p.baffle[0]=b0;p.baffle[1]=b1
    w,h=(480,320) if area in (46,47,48,51) else (240,160)
    prefix=[[0]*(w+1) for _ in range(h+1)]
    for y in range(h):
     run=0
     for x in range(w):
      v=L.underwater_game_solid(x,y);self.assertEqual(L.underwater_game_clear_box(x,y,x,y),not v,(area,ballast,b0,b1,x,y));checks+=1;run+=v;prefix[y+1][x+1]=prefix[y][x+1]+run
    for _ in range(5000):
     x0,x1=sorted([R.randrange(w),R.randrange(w)]);y0,y1=sorted([R.randrange(h),R.randrange(h)])
     occupied=prefix[y1+1][x1+1]-prefix[y0][x1+1]-prefix[y1+1][x0]+prefix[y0][x0]
     self.assertEqual(L.underwater_game_clear_box(x0,y0,x1,y1),not occupied,(area,ballast,b0,b1,x0,y0,x1,y1));checks+=1
    for box in ((-1,5,5,5),(5,-1,5,5),(5,5,w,h),(8,8,7,8),(8,8,8,7),(-2147483648,0,2147483647,2147483647)):
     self.assertEqual(L.underwater_game_clear_box(*box),0);checks+=1
    rows.append({'room':area,'ballast':ballast,'baffles':[b0,b1],'all_single_pixels':w*h,'rectangles':5000})
  for room in (-1,0,38,45,54,2147483647):
   C.c_int.in_dll(L,'room').value=room;self.assertEqual(L.underwater_game_clear_box(5,5,8,8),0);checks+=1
  out=ROOT/'build/underwater-clear-box';out.mkdir(parents=True,exist_ok=True)
  (out/'report.json').write_text(json.dumps({'scope':'host exact broadphase versus independent per-pixel solid prefix sum','checks':checks,'cases':rows,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('src/underwater_game.c','src/underwater_game.h','src/underwater_game_draw.inc')}},indent=2)+'\n')
 def test_authored_projection_removes_only_dynamic_collision(self):
  u=UnderwaterWorld();u.setUp();u.sources();u.start(17,1)
  self.assertEqual(C.c_int.in_dll(L,'room').value,50)
  for y in range(5,154):
   for x in range(5,234):self.assertEqual(L.underwater_game_clear_box(x,y,x,y),not L.underwater_game_solid(x,y))
  self.assertEqual(L.underwater_game_clear_box(136,86,145,87),1)
if __name__=='__main__':unittest.main(verbosity=2)
