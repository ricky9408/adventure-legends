#!/usr/bin/env python3
"""Exact certified boxes versus current Magma solid pixels; synthetic host only."""
import ctypes as C,hashlib,json,random
from test_magma_game import L,MagmaRuntime,ROOT
R=random.Random(3866);checks=0;cases=[]
class ArtRoom(C.Structure):
 _fields_=[('width',C.c_ushort),('height',C.c_ushort),('bitmap',C.c_void_p),('bitmap_odd',C.c_void_p),('solids',C.c_void_p),('solid_count',C.c_ushort),('collision_rows',C.POINTER(C.c_ushort)),('collision_bands',C.POINTER(C.c_ushort))]
for r in (ArtRoom*8).in_dll(L,'magma_art_rooms'):
 for y in range(r.height):
  o=r.collision_rows[y];previous=-1
  for i in range(r.collision_bands[o]):
   lo=r.collision_bands[o+1+i*2];hi=r.collision_bands[o+2+i*2]
   assert 0<=lo<hi<=r.width and lo>previous,('sorted disjoint Magma band contract',y,lo,hi,previous)
   previous=hi
u=MagmaRuntime();u.setUp();u.guarantees()
for area in (38,39):
 u.entry(area);start=144 if area==38 else 128;prop_y=232 if area==38 else 264
 for step in range(3):
  current=start+step*24;words=(C.c_uint*3)();L.magma_game_collision_inputs(words);assert words[0]==current
  w=480;h=320;prefix=[[0]*(w+1) for _ in range(h+1)]
  for y in range(h):
   total=0
   for x in range(w):
    occupied=L.magma_game_solid(x,y);actual=L.magma_game_clear_box(x,y,x,y)
    assert actual==int(not occupied),(area,current,x,y,occupied,actual)
    checks+=1;total+=occupied;prefix[y+1][x+1]=prefix[y][x+1]+total
  for _ in range(5000):
   x0,x1=sorted((R.randrange(w),R.randrange(w)));y0,y1=sorted((R.randrange(h),R.randrange(h)))
   occupied=prefix[y1+1][x1+1]-prefix[y0][x1+1]-prefix[y1+1][x0]+prefix[y0][x0]
   assert L.magma_game_clear_box(x0,y0,x1,y1)==int(not occupied),(area,current,x0,y0,x1,y1)
   checks+=1
  for box in ((-1,0,0,0),(0,-1,0,0),(0,0,480,320),(8,8,7,8),(8,8,8,7),(-2147483648,0,2147483647,2147483647)):
   assert L.magma_game_clear_box(*box)==0;checks+=1
  cases.append({'area':area,'prop_x':current,'prop_y':prop_y,'pixels':w*h,'rectangles':5000})
  if step<2:
   if step==0:u.target(current,prop_y);assert L.magma_game_grabbed()
   L.magma_game_input(16,0)
 L.magma_game_input(1,0)
for area in (-1,0,37,40,41,42,43,44,45,46,2147483647):
 C.c_int.in_dll(L,'room').value=area
 assert L.magma_game_clear_box(100,100,104,104)==0;checks+=1
out=ROOT/'build/magma-clear-box';out.mkdir(parents=True,exist_ok=True)
report={'checks':checks,'cases':cases,'sorted_disjoint_band_rows_verified':sum(r.height for r in (ArtRoom*8).in_dll(L,'magma_art_rooms')),'scope':'synthetic actual-world exact box oracle; other rooms conservatively return0','source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ('src/magma_game.c','src/magma_game.h','src/magma_powers.c')}}
(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(f'{checks} Magma box proofs match solid(), both large rooms at all three movable-prop positions')
