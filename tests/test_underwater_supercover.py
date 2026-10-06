#!/usr/bin/env python3
"""Real-world bounded supercover versus frozen pixel-step mathematics.

Synthetic host world configurations only; native cadence remains separate.
"""
import ctypes as C,hashlib,json,random
from test_underwater_game import L,UnderwaterWorld,puzzle,ROOT
R=random.Random(87160)
checks=0;rows=[]
class ArtRoom(C.Structure):
 _fields_=[('width',C.c_ushort),('height',C.c_ushort),('bitmap',C.c_void_p),('bitmap_odd',C.c_void_p),('solids',C.c_void_p),('solid_count',C.c_ushort),('collision_rows',C.POINTER(C.c_ushort)),('collision_bands',C.POINTER(C.c_ushort))]
sorted_rows=0
for room in (ArtRoom*8).in_dll(L,'underwater_art_rooms'):
 for y in range(room.height):
  offset=room.collision_rows[y];count=room.collision_bands[offset];last=-1
  for i in range(count):
   lo=room.collision_bands[offset+1+i*2];hi=room.collision_bands[offset+2+i*2]
   assert 0<=lo<hi<=room.width and lo>last,('generated sorted/disjoint band contract',y,lo,hi,last)
   last=hi
  sorted_rows+=1
def reference(grid,x,y,tx,ty):
 if min(x,y,tx,ty)<0 or max(x,y,tx,ty)>1023 or abs(x-tx)+abs(y-ty)>160:return 0
 h=len(grid);w=len(grid[0])
 def solid(a,b):return not (0<=a<w and 0<=b<h) or grid[b][a]
 if solid(x,y) or solid(tx,ty):return 0
 ax=abs(tx-x);ay=-abs(ty-y);sx=1 if x<tx else -1;sy=1 if y<ty else -1;e=ax+ay
 while x!=tx or y!=ty:
  twice=e*2;nx=x;ny=y
  if twice>=ay:e+=ay;nx+=sx
  if twice<=ax:e+=ax;ny+=sy
  if nx!=x and ny!=y and (solid(nx,y) or solid(x,ny)):return 0
  x=nx;y=ny
  if solid(x,y):return 0
 return 1
def check_scene(area,label):
 global checks
 w,h=(480,320) if area in (46,47,48,51) else (240,160)
 grid=[bytearray(bool(L.underwater_game_solid(x,y)) for x in range(w)) for y in range(h)]
 rays=[]
 for _ in range(5000):
  x=R.randrange(-8,w+8);y=R.randrange(-8,h+8);tx=x+R.randrange(-80,81);ty=y+R.randrange(-80,81)
  rays.extend(((x,y,tx,ty),(tx,ty,x,y)))
 # Exact hostile-scene origin, small octants/ties, horizontal and vertical rays.
 for ox,oy in ((400,255),(303,196),(176,120),(96,128),(100,100)):
  if ox>=w or oy>=h:continue
  for dx in range(-20,21):
   for dy in range(-20,21):rays.append((ox,oy,ox+dx,oy+dy))
 rays.extend(((0,0,0,0),(-2147483648,0,0,0),(0,0,2147483647,0),(5,5,166,5),(5,5,165,5),(1023,1023,1023,1023),(1024,0,0,0)))
 for ray in rays:
  expected=reference(grid,*ray);actual=L.underwater_game_supercover(*ray)
  assert actual==expected,(area,label,ray,actual,expected)
 checks+=len(rays);rows.append({'room':area,'configuration':label,'rays':len(rays)})
for area in range(46,54):
 configs=[(b,0,0) for b in range(2)] if area in (50,51,53) else [(0,a,b) for a in range(2) for b in range(2)] if area==52 else [(0,0,0)]
 for ballast,b0,b1 in configs:
  C.c_int.in_dll(L,'room').value=area;L.underwater_game_reset();p=puzzle();p.ballast=ballast;p.baffle[0]=b0;p.baffle[1]=b1
  check_scene(area,{'ballast':ballast,'baffles':[b0,b1]})
u=UnderwaterWorld();u.setUp();u.sources();u.start(17,1)
assert C.c_int.in_dll(L,'room').value==50
check_scene(50,'authored-trial-projection')
for area in (-1,0,38,45,54,2147483647):
 C.c_int.in_dll(L,'room').value=area
 assert L.underwater_game_supercover(0,0,1,1)==-1
 checks+=1
report={'checks':checks,'sorted_disjoint_band_rows_verified':sorted_rows,'configurations':rows,'reference':'endpoint-inclusive integer supercover with both diagonal side cells; independent Python over actual solid pixel grid','native_cadence_proven':False,'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('src/underwater_game.c','src/underwater_game.h','src/underwater_powers.c')}}
out=ROOT/'build/underwater-supercover';out.mkdir(parents=True,exist_ok=True);(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(f'{checks} directed rays across15 world/projection configurations match exact pixel oracle')
