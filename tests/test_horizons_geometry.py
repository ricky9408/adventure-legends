#!/usr/bin/env python3
"""Authored pixel-foot geometry, not native/controller evidence."""
from pathlib import Path
from collections import deque
import importlib.util,json,unittest,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets'))
from generate_region import occupancy
class Geometry(unittest.TestCase):
 def test_every_spawn_reset_portal_and_work_approach(self):
  rooms=json.loads((ROOT/'assets/horizons_region/geometry.json').read_text())['rooms']
  doors={62:[(240,304),(464,160),(16,160),(240,16)],63:[(8,128),(472,128),(208,16),(400,16)],64:[(120,150),(8,112)],65:[(16,160),(464,160),(240,16)],66:[(120,304),(48,8),(224,272)],67:[(80,288),(400,288),(240,16),(16,144)],68:[(120,150)],69:[(120,150),(224,112)]}
  special={62:[(352,176),(352,224),(352,256),(384,208),(304,272),(304,240),(320,240),(336,272)],63:[(416,96),(416,128),(392,96),(440,96),(64,64),(80,96),(48,64),(112,96),(136,80),(336,128),(336,104),(336,64),(368,96),(336,112),(400,112)],64:[(32,48),(32,80),(64,120),(120,112),(200,112),(176,120),(200,104),(160,112)],65:[(416,256),(384,224),(384,256),(416,224),(352,272)],66:[(64,256),(64,224),(48,240),(80,272),(48,208),(48,176),(48,160),(80,208),(48,72),(80,160),(144,248),(176,248),(80,248),(64,288)],67:[(368,208),(300,232),(288,208),(312,208),(400,240),(368,272),(64,192),(48,144),(64,144),(96,192),(80,144)],68:[(192,112),(160,136),(176,112),(216,112),(48,112),(80,112),(80,88),(48,136),(160,88),(112,112),(116,102)],69:[(208,112),(48,48),(192,64),(176,112),(192,32),(48,104),(80,104)]}
  for r in rooms:
   w,h=r['width'],r['height'];base=occupancy(r,False)
   # Every2px motion state is independently reversible/escapable, including
   # a load halted by a late actor. No southern lane cell becomes occupied.
   for load in range(192,289,2) if r['id']==63 else [None]:
    blocked=bytearray(base)
    if load is not None:
     for y in range(60,85):
      for x in range(load-12,load+13):blocked[y*w+x]=1
    start=r['spawns']['0'];p=start[1]*w+start[0];seen=bytearray(w*h);q=deque([p]);seen[p]=1
    while q:
     p=q.popleft();x=p%w;y=p//w
     for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
      if 0<=xx<w and 0<=yy<h:
       z=yy*w+xx
       if not blocked[z] and not seen[z]:seen[z]=1;q.append(z)
    for point in list(r['spawns'].values())+[r['reset']]+doors[r['id']]:
     self.assertTrue(seen[point[1]*w+point[0]] and not blocked[point[1]*w+point[0]],(r['id'],load,point))
    for x,y in special[r['id']]+r['field_targets']:
     self.assertTrue(any(0<=x+dx*d<w and 0<=y+dy*d<h and seen[(y+dy*d)*w+x+dx*d] and not blocked[(y+dy*d)*w+x+dx*d] for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)) for d in range(16,27)),(r['id'],load,(x,y)))
    if load is not None:
     self.assertTrue(all(not blocked[y*w+x] for y in range(112,145) for x in range(16,w-16)))
 def test_map_assets_and_budget(self):
  from PIL import Image
  rooms=json.loads((ROOT/'assets/horizons_region/geometry.json').read_text())['rooms']
  for r in rooms:
   im=Image.open(ROOT/f'assets/horizons_region/room{r["id"]}.png');self.assertEqual(im.size,(r['width'],r['height']));self.assertGreater(len(set(im.tobytes())),12);self.assertNotIn(0,im.tobytes())
  v=json.loads((ROOT/'assets/horizons_region/validation.json').read_text());self.assertLessEqual(v['rom_art_bytes'],1310720)
if __name__=='__main__':unittest.main()
