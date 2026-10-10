#!/usr/bin/env python3
"""Original Shared Horizons scenery, authored collision and native geometry proof.
The moving carriage, hanging gauze, ink marks and transfer notch are runtime work.
No imported images and no transformed older map raster are used.
"""
from pathlib import Path
from PIL import Image,ImageDraw
import connected_road_art as roads
from collections import deque
import json,random,hashlib,sys
sys.dont_write_bytecode=True
from generate_assets import Art,P
from generate_region import odd_bitmap,cbytes,occupancy
from generate_northern_region import collision_bands
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/horizons_region';SRC=ROOT/'src'
NAMES=['HOST','PORTER','STORYTELLER','SCRIBE','JOINER','HOST_WORK','PORTER_WORK','REST','REST_LIT','RESET','TRIAL','NOTICE','HANDLE','CUP','CARRIAGE','PANEL','WAX','BOWL','LATCH','DONE']
SOLIDS={62:[[160,48,160,24],[160,72,24,48],[296,72,24,48],[40,40,72,24],[360,40,72,24],[112,128,40,32],[328,128,40,32]],63:[[112,24,48,24],[256,24,48,24],[416,24,48,24]],64:[[80,20,80,16]],65:[[160,80,144,24],[160,104,24,48],[280,104,24,48],[200,184,64,20]],66:[[88,32,104,24],[64,112,64,24],[112,192,80,24]],67:[[200,64,80,64],[128,80,24,88],[328,80,24,88]],68:[[88,20,64,16]],69:[[88,24,24,56],[144,48,24,48]]}
DECOR_SOLIDS={62:[[8,24,24,64],[440,24,32,64],[12,212,24,32]],63:[[8,16,24,16]],64:[],65:[[24,32,40,24],[408,32,48,24],[112,216,40,24],[224,232,48,24]],66:[],67:[[24,64,32,40],[424,96,32,48]],68:[],69:[]}

TARGETS={62:[[192,176],[320,240]],63:[[192,72],[392,96]],64:[[64,56],[120,56],[176,56],[208,88]],65:[[336,160],[384,256]],66:[[144,248],[144,80],[176,80],[208,80],[48,176]],67:[[112,224],[288,208],[312,208],[64,144]],68:[[48,64],[120,64],[192,64],[160,112]],69:[[192,64]]}
EXTRA={62:[[120,208],[208,208],[272,208],[352,224],[72,256],[304,272],[320,272]],63:[[80,96],[352,96],[416,96],[64,64],[112,96],[336,128],[368,112]],64:[[56,104],[120,104],[176,104],[200,112],[32,48],[32,80],[64,120],[176,120]],65:[[96,176],[336,208],[384,224],[416,256],[80,256],[352,272]],66:[[64,256],[48,208],[48,176],[48,72],[80,160],[64,288]],67:[[352,224],[352,256],[64,192],[48,144],[80,144],[368,208],[400,208],[400,240]],68:[[192,112],[160,136],[48,112],[80,112],[80,88]],69:[[40,80],[48,48],[192,32],[48,104],[80,104],[208,112]]}
def rr(a,xy,c):a.r(tuple(xy),c)
def path(a,pts,w=26,c='bg_sunlit_dirt4'):
 a.l(pts,'bg_sunlit_dirt2',w+5);a.l(pts,c,w)
def ring(a,x,y,r=12,c='gold1'):
 a.l([(x-r,y-3),(x-3,y-r),(x+3,y-r),(x+r,y-3),(x+r,y+3),(x+3,y+r),(x-3,y+r),(x-r,y+3),(x-r,y-3)],c)
def wood(a,x,y,w,h):
 a.r((x,y,x+w-1,y+h-1),'wood1');a.r((x+1,y+1,x+w-2,y+h-3),'wood3')
 for yy in range(y+3,y+h-2,6):a.l([(x+2,yy),(x+w-3,yy)],'wood4');a.dot(x+4,yy+1,'wood1');a.dot(x+w-5,yy+1,'wood1')
 a.l([(x+1,y+h-2),(x+w-2,y+h-2)],'wood2')
def canopy(a,x,y,w,h,tone='rose3'):
 wood(a,x,y,w,h);a.p([(x,y),(x+w//2,y-10),(x+w-1,y),(x+w-1,y+7),(x,y+7)],tone)
 for xx in range(x+3,x+w-2,10):a.l([(xx,y),(xx,y+6)],'gold4',3)
 a.l([(x,y+8),(x+w-1,y+8)],'wood1')
def stone(a,x,y,w,h):
 a.r((x,y,x+w-1,y+h-1),'bg_sunlit_stone2');a.r((x+1,y+1,x+w-2,y+h-3),'bg_sunlit_stone4')
 for yy in range(y+5,y+h-2,9):
  a.l([(x+1,yy),(x+w-2,yy)],'bg_sunlit_stone3')
  for xx in range(x+5+(yy%2)*6,x+w-2,15):a.l([(xx,yy),(xx,yy+7)],'bg_sunlit_stone2')
 a.l([(x+2,y+1),(x+w-3,y+1)],'bg_sunlit_stone5')
def vase(a,x,y,c='water3'):
 a.e((x-5,y-4,x+5,y+5),'wood1');a.e((x-4,y-4,x+4,y+3),c);a.e((x-3,y-5,x+3,y-2),'gold4');a.l([(x-2,y-3),(x+2,y-3)],'wood1')
def motif(a,x,y,n,c='gold1'):
 if n%3==0:a.e((x-3,y-3,x+3,y+3),c)
 elif n%3==1:a.r((x-5,y-2,x+5,y+2),c)
 else:a.l([(x-4,y+4),(x,y-4),(x+4,y+4)],c,2)
def draw_room(r):
 n=r['id'];w,h=r['width'],r['height'];a=Art(w,h,'bg_sunlit_grass3' if n==62 else 'dirt3' if n in (65,67) else 'dirt2' if n==69 else 'stone4' if n==66 else 'grasslit' if n==68 else 'wood3');rng=random.Random(n*823)
 # Low-detail ground and edge material make every raised landmark legible.
 for _ in range(w*h//100):
  x=rng.randrange(7,w-7);y=rng.randrange(7,h-7);a.l([(x,y),(x+rng.randrange(1,4),y)],'bg_sunlit_grass2' if n==62 else 'bg_sunlit_dirt2' if n in (65,67,69) else 'wood3' if n in (63,64) else 'bg_temple_stone3')
 for pts in [r['safe_spine']]:path(a,pts,28,'wood5' if n in (63,64) else 'bg_sunlit_dirt4')
 for s in r['spawns'].values():path(a,[s,[max(24,min(w-24,s[0])),max(32,min(h-32,s[1]))]],25)
 if n==62:
  a.e((176,176,304,282),'bg_sunlit_dirt2');a.e((180,180,300,278),'bg_sunlit_dirt4');a.d.ellipse((198,194,282,262),outline=P['gold2'],width=2)
  for x,y in [(36,190),(94,288),(372,288),(430,196),(72,114),(408,110)]:
   a.e((x-8,y-4,x+8,y+4),'bg_sunlit_grass2')
   for dx,dy in [(-4,-3),(2,-5),(6,1)]:a.dot(x+dx,y+dy,'rose4');a.dot(x+dx+1,y+dy,'gold3')
  for x,y,ww,hh in SOLIDS[n][3:]:canopy(a,x,y,ww,hh,'water3' if x<200 else 'rose3')
  wood(a,160,48,160,24);stone(a,160,72,24,48);stone(a,296,72,24,48)
  for x in range(188,296,18):a.l([(x,50),(x+8,61),(x+16,50)],'gold4',2)
  for x in (172,308):a.e((x-10,106,x+10,125),'wood1');a.e((x-6,111,x+6,122),'gold2');a.l([(x-8,116),(x+8,116)],'wood3')
  # Distinct contributors' flat inlays wait below the incomplete arch.
  for x,c in [(208,'rose3'),(240,'water3'),(272,'gold2')]:a.r((x-10,136,x+10,151),c);motif(a,x,143,(x-208)//32,'gold4')
 elif n==63:
  path(a,[(10,128),(470,128)],28);a.l([(10,114),(470,114)],'white',3)
  for x,y,ww,hh in SOLIDS[n]:
   wood(a,x,y,ww,hh)
   for xx in (x+7,x+ww-8):a.e((xx-5,y+hh-3,xx+5,y+hh+7),'wood1');a.e((xx-2,y+hh,xx+2,y+hh+4),'gold2')
  for i,x in enumerate([136,280,440]):motif(a,x,33,i,'gold4')
  a.l([(176,66),(304,66)],'stone1',2);a.l([(176,78),(304,78)],'stone1',2)
  for x in range(176,305,8):a.l([(x,64),(x,80)],'wood2')
  for x in (192,224,256,288):a.d.ellipse((x-10,60,x+10,84),outline=P['gold3']);a.l([(x,52),(x,58)],'gold1')
  for x in (80,352):a.l([(x-15,93),(x,83),(x+15,93)],'gold1',2)
 elif n==64:
  wood(a,80,20,80,16);a.l([(42,44),(198,44)],'wood1',2)
  for x in (64,120,176):a.l([(x,44),(x,91)],'gold1');a.l([(x-4,56),(x+4,56)],'gold4');a.l([(x-4,80),(x+4,80)],'gold4')
  # Program: low/high/low silhouette and its large white central opening.
  a.r((96,22,144,34),'gold4');a.r((100,28,110,33),'rose3');a.r((116,23,126,27),'rose3');a.r((132,28,142,33),'rose3')
  for x,y in [(72,126),(96,133),(120,137),(144,133),(168,126)]:wood(a,x-6,y-3,12,5)
  # Wide wingprints and empty nesting slit are intentional hints, not hidden pixels.
  for x,y in [(180,124),(192,116),(205,106)]:a.p([(x-5,y),(x-1,y-4),(x,y+2),(x+1,y-4),(x+5,y),(x,y+5)],'gold2')
 elif n==65:
  for x,y,ww,hh in SOLIDS[n]:wood(a,x,y,ww,hh)
  for i,(x,y) in enumerate([(196,91),(220,91),(248,91),(292,122),(216,192)]):vase(a,x,y,['rose3','water3','pine3','gold2','silver'][i]);motif(a,x,y+10,i,'wood1')
  # Giant broad reference lies flat so its white path is never a hidden solid.
  a.r((72,112,136,145),'wood1');a.r((74,114,134,143),'gold4');a.e((79,122,88,133),'water3');a.r((97,124,112,131),'water3');a.r((120,116,131,141),'white')
  a.l([(136,126),(145,126)],'gold1');a.l([(142,123),(146,126),(142,129)],'gold1')
  for x in (320,336,352):a.d.ellipse((x-6,154,x+6,166),outline=P['water2'])
  a.l([(168,68),(296,68)],'rose3',2)
  for x in range(172,296,16):a.p([(x,68),(x+7,76),(x+14,68)],'rose4')
 elif n==66:
  for x,y,ww,hh in SOLIDS[n]:wood(a,x,y,ww,hh)
  # Tall draped sheet has a visibly unpainted continuous road, echoed in samples.
  for y in range(32,280,8):a.l([(218,y),(232,y+2)],'gold3')
  a.p([(212,20),(236,20),(236,276),(212,278)],'water3');a.l([(224,22),(218,82),(229,140),(220,210),(226,275)],'white',5)
  for x in (144,176,208):a.r((x-8,73,x+8,87),'stone2');a.r((x-6,75,x+6,85),'gold4')
  for x,i in [(144,2),(176,1),(208,0)]:motif(a,x,80,i,'white' if i==2 else 'water2')
  a.l([(132,242),(220,242)],'stone1',2);a.l([(132,254),(220,254)],'stone1',2)
  for x in (144,176,208):a.l([(x,239),(x,257)],'gold2')
  # A broad scored sign points toward the canyon entrance.
  a.r((184,282,226,296),'wood1');a.r((186,283,224,294),'gold4');a.l([(190,289),(196,289)],'wood2',2);a.l([(202,289),(218,289)],'wood2',2)
 elif n==67:
  # Layered sea/mountain vista is confined above the usable transfer ground.
  a.r((4,4,475,21),'water3');a.l([(5,17),(475,17)],'water4')
  for x in range(10,470,51):a.p([(x,19),(x+18,4),(x+35,19)],'bg_sunlit_stone3');a.l([(x+16,6),(x+20,6),(x+25,11)],'bg_sunlit_stone5')
  for x,y,ww,hh in SOLIDS[n]:stone(a,x,y,ww,hh)
  a.e((204,68,275,123),'wood1');a.e((209,73,270,118),'wood4');a.l([(216,114),(263,78)],'wood2',3)
  for x in (80,112,144):a.r((x-8,218,x+8,230),'stone2');a.l([(x,210),(x,235)],'gold2')
  a.l([(64,246),(168,246)],'white',3);a.l([(264,197),(328,197)],'wood1',2)
  a.r((276,202,324,213),'gold2');a.r((276,211,324,214),'wood2');a.l([(304,202),(308,208),(304,213)],'gold4',2)
 elif n==68:
  wood(a,88,20,64,16);a.l([(32,40),(208,40)],'wood2',2)
  for x,c in [(48,'rose3'),(120,'gold2'),(192,'water3')]:
   a.p([(x-14,43),(x+14,43),(x+12,50),(x-12,50)],c);a.l([(x-16,49),(x+16,49)],'wood1')
  for x,y in [(32,106),(72,130),(120,126),(208,130)]:a.r((x-7,y-3,x+7,y+2),'wood2');a.l([(x-7,y-3),(x+7,y-3)],'wood4')
  path(a,[(120,151),(120,100),(160,100)],25);a.l([(99,150),(99,104)],'white',2)
 elif n==69:
  for x,y,ww,hh in SOLIDS[n]:
   a.p([(x,y+5),(x+ww//2,y),(x+ww-1,y+6),(x+ww-1,y+hh-1),(x,y+hh-1)],'gold1');a.l([(x+3,y+12),(x+ww-4,y+7)],'gold3',2)
   for yy in range(y+17,y+hh-2,11):a.l([(x+2,yy),(x+ww-3,yy-3)],'wood2')
  for x,y in [(48,48),(192,32),(40,80)]:vase(a,x,y,'rose3');a.l([(x-7,y+11),(x+7,y+11)],'gold3',2)
  a.r((25,18,73,29),'gold4');a.l([(30,24),(38,24)],'wood1',2);a.l([(47,24),(66,24)],'wood1',2)
  for x in range(188,234,8):a.l([(x,101),(x+4,108)],'wood3');a.l([(x,99),(x,109)],'gold1')
 depth(a,r)
 decor(a,r)
 roads.draw(a,n,P)
 # Static object aprons are restrained; actual state and object sprites are runtime.
 for x,y in r['field_targets']:ring(a,x,y,12,'gold1')
 for x,y in r['objects']:a.d.ellipse((x-9,y-5,x+9,y+5),outline=P['bg_sunlit_dirt2'])
 x,y=r['reset'];a.r((x-10,y-8,x+10,y+8),'bg_sunlit_stone4')
 return a

def tuft(a,x,y,tone='pine3'):
 for dx,dy in [(-6,0),(-2,-3),(3,-1),(7,2)]:
  a.l([(x+dx-2,y+dy),(x+dx,y+dy-4),(x+dx+1,y+dy)],tone)
  a.dot(x+dx,y+dy-4,'bg_sunlit_leaflight')
def bolt(a,x,y,c):
 a.r((x-8,y-4,x+8,y+4),'wood1');a.r((x-7,y-4,x+7,y+2),c)
 a.e((x-8,y-4,x-3,y+4),'gold4');a.e((x-7,y-3,x-5,y+2),'wood2')
 for xx in range(x-1,x+7,3):a.l([(xx,y-3),(xx,y+1)],'gold3')
def depth(a,r):
 n=r['id'];w,h=r['width'],r['height'];rng=random.Random(772+n)
 # Material shadows remain inside landmarks or conventional contact shadows,
 # never visually invent a blocking object on a certified walking approach.
 for x,y,ww,hh in SOLIDS[n]:
  a.l([(x+2,y+hh),(x+ww+2,y+hh)],'dirt1' if n in (62,65,67,69) else 'stone3',3)
  a.l([(x,y),(x,y+hh-1),(x+ww-1,y+hh-1),(x+ww-1,y)],'wood1' if n in (62,63,64,65,66,68) else 'stone1',2)
  if n in (62,63,65,66,68):
   for xx in [x+3,x+ww-5]:a.r((xx,y+hh-7,xx+3,y+hh-1),'wood1');a.dot(xx+1,y+hh-6,'gold2')
  if n==67:
   for yy in range(y+8,y+hh-3,11):a.l([(x+2,yy),(x+ww-3,yy)],'stone2');a.l([(x+2,yy-1),(x+ww-3,yy-1)],'stone4')
   a.l([(x+2,y+2),(x+ww-3,y+2)],'stone5',2)
 if n in (63,64):
  # Every visible floor board has a dark staggered join and occasional pegs.
  for y in range(8,h-5,12):
   for x in range(8+(y//12%3)*19,w-9,58):
    if not any(xx-4<=x<xx+ww+4 and yy-4<=y<yy+hh+5 for xx,yy,ww,hh in SOLIDS[n]):
     a.l([(x,y),(x+min(37,w-x-7),y)],'wood2');a.l([(x,y+1),(x,y+8)],'wood2');a.dot(x+3,y+3,'wood1');a.l([(x+7,y+6),(x+19,y+6)],'wood4')
 if n==62:
  # Woven booth skirts and hanging maker pennants form a lived-in crescent.
  for x,y,ww,hh in SOLIDS[n][3:]:
   c='water2' if x<200 else 'rose2'
   a.r((x+4,y+12,x+ww-5,y+hh-4),c)
   for xx in range(x+6,x+ww-5,6):a.l([(xx,y+13),(xx,y+hh-5)],'water3' if x<200 else 'rose3')
   for xx in range(x+10,x+ww-5,12):a.l([(xx-3,y+hh-9),(xx,y+hh-12),(xx+3,y+hh-9)],'gold3')
   a.l([(x+3,y+hh-4),(x+ww-4,y+hh-4)],'wood1',2)
   bolt(a,x+ww//2,y+9,'water4' if x<200 else 'rose4')
  for x in (172,308):
   a.r((x-10,74,x+10,84),'stone2');a.r((x-9,84,x+9,103),'stone3');a.l([(x-8,87),(x+8,87)],'stone1');a.l([(x-8,96),(x+8,96)],'stone1');a.l([(x-7,75),(x-7,101)],'stone5')
  for x in range(188,295,18):a.p([(x,53),(x+8,65),(x+16,53)],'rose3' if x%36 else 'water3');a.l([(x+1,53),(x+15,53)],'gold4')
  for x,y in [(20,28),(112,24),(446,26),(28,116),(446,120),(20,218),(438,236),(112,306),(370,308),(380,190)]:tuft(a,x,y)
  # Picnic cloths lie flush, their fringes unmistakably fabric on the ground.
  for x,y,c in [(40,214,'water3'),(392,276,'rose3')]:
   a.r((x,y,x+25,y+13),c)
   for yy in range(y+2,y+13,4):a.l([(x,yy),(x+25,yy)],'gold4')
   for xx in range(x+2,x+25,5):a.l([(xx,y-2),(xx,y+15)],'gold3')
 elif n==63:
  for k,(x,y,ww,hh) in enumerate(SOLIDS[n]):
   bolt(a,x+14,y+11,['rose4','water3','gold2'][k]);a.r((x+29,y+5,x+42,y+19),'wood2');a.l([(x+30,y+6),(x+40,y+16)],'wood5',2)
   for xx in range(x+3,x+ww-2,7):a.l([(xx,y+hh-2),(xx,y+hh+2)],'silver')
  # Three broad, different painted load emblems can be read from the promenade.
  for i,x in enumerate([136,280,440]):a.r((x-7,49,x+7,58),'wood1');motif(a,x,53,i,'gold4')
  for x in range(176,305,8):a.dot(x,67,'silver');a.dot(x,77,'silver')
  a.l([(12,113),(468,113)],'wood1');a.l([(12,115),(468,115)],'white',3)
 elif n==64:
  # A low stage rim, theatre knots, and a stitched program give the gauze depth.
  a.l([(42,44),(198,44)],'wood0',3);a.l([(44,42),(196,42)],'wood5')
  for x in (44,196):a.r((x-2,44,x+2,58),'wood1');a.dot(x,48,'gold3')
  for x in (64,120,176):a.e((x-3,39,x+3,44),'gold1');a.dot(x,41,'gold4')
  for x,y in [(72,126),(96,133),(120,137),(144,133),(168,126)]:
   a.l([(x-7,y-3),(x+7,y-3)],'wood0',2);a.l([(x-6,y-5),(x+6,y-5)],'wood5');a.dot(x-4,y,'gold1');a.dot(x+4,y,'gold1')
  for x in range(85,158,8):a.dot(x,21,'gold3')
  a.r((96,22,144,34),'wood1');a.r((98,23,142,33),'white');a.r((100,28,110,32),'rose2');a.r((116,24,126,27),'rose2');a.r((132,28,140,32),'rose2')
 elif n==65:
  # The cup circuit mixes glazed pottery, food cloths, scrolls and spoon rests.
  for x,y,c in [(174,116,'rose3'),(294,139,'water3'),(218,192,'pine3')]:bolt(a,x,y,c)
  for x,y in [(196,91),(220,91),(248,91),(292,122)]:vase(a,x,y,'water3' if x%3 else 'rose3');a.dot(x-2,y-2,'white')
  for x in range(164,302,12):a.l([(x,81),(x+6,81)],'wood5');a.dot(x,100,'wood1')
  a.l([(166,67),(298,67)],'wood1',2)
  for x in range(172,296,16):a.p([(x,68),(x+7,78),(x+14,68)],'rose2');a.l([(x+2,69),(x+12,69)],'rose5')
  for x,y in [(18,32),(444,44),(32,240),(448,288),(144,276),(304,32)]:tuft(a,x,y)
  for x,y in [(56,40),(388,298)]:
   a.l([(x-12,y),(x+12,y)],'dirt1',2);a.l([(x-10,y-2),(x+10,y-2)],'gold3')
 elif n==66:
  for x,y,ww,hh in SOLIDS[n]:
   a.r((x+7,y+3,x+ww-8,y+hh-6),'gold4');a.r((x+9,y+5,x+ww-10,y+hh-8),'water2');a.l([(x+13,y+5),(x+19,y+hh-8),(x+25,y+5)],'white',4)
   for xx in (x+4,x+ww-5):a.dot(xx,y+3,'silver')
  # Print rollers and joined corners on the tall sheet, shadowed to its right.
  a.r((235,20,237,279),'stone1');a.l([(211,19),(237,19)],'wood1',3);a.l([(211,278),(237,278)],'wood1',3)
  for y in range(32,268,28):a.l([(213,y),(217,y+7)],'water1');a.dot(232,y+7,'gold4')
  for y in range(24,293,16):
   a.l([(8,y),(16,y)],'stone3');a.l([(9,y+1),(9,y+5)],'stone5')
  for x in (144,176,208):
   a.l([(x-9,87),(x+9,87)],'stone1',2);a.l([(x-9,73),(x+9,73)],'stone5')
  # The footprint of each press bench remains the certified solid rectangle.
 elif n==67:
  # Heavy masonry base, geared turntable and exposed wheel pegs make the transfer
  # visibly load-bearing; the southern loading lane remains completely bare.
  a.e((205,68,275,124),'wood0');a.e((210,73,270,118),'wood3');a.e((216,79,264,112),'wood4')
  for x,y in [(238,74),(266,94),(238,116),(211,94)]:a.r((x-2,y-2,x+2,y+2),'gold1');a.dot(x,y,'silver')
  a.l([(215,109),(262,79)],'wood1',4);a.l([(218,112),(265,82)],'silver',2)
  for x in (128,328):
   a.r((x+2,81,x+21,89),'stone1');a.l([(x+3,81),(x+20,81)],'stone5');a.l([(x+4,91),(x+4,162)],'stone5');a.l([(x+20,91),(x+20,162)],'stone2')
  for x,y in [(18,40),(456,36),(450,268),(176,280)]:tuft(a,x,y,'pine2')
  for x in (80,112,144):a.r((x-9,216,x+9,231),'stone1');a.r((x-7,218,x+7,227),'stone3');a.l([(x-6,217),(x+6,217)],'gold3')
  a.l([(264,198),(329,198)],'wood0',2);a.l([(276,215),(324,215)],'wood1',2)
 elif n==68:
  for x in (48,120,192):
   a.r((x-16,40,x-13,53),'wood1');a.r((x+13,40,x+16,53),'wood1');a.dot(x-14,43,'gold3');a.dot(x+14,43,'gold3')
  for x,y in [(20,20),(216,20),(12,74),(225,90),(16,144)]:tuft(a,x,y)
  for x,y in [(32,106),(72,130),(120,126),(208,130)]:a.l([(x-8,y+3),(x+8,y+3)],'wood1',2);a.l([(x-7,y-4),(x+7,y-4)],'wood5')
 elif n==69:
  for x,y,ww,hh in SOLIDS[n]:
   a.l([(x+ww-2,y+8),(x+ww-2,y+hh-1)],'wood1',3);a.l([(x+2,y+7),(x+ww//2,y+2),(x+ww-4,y+7)],'gold3',2)
   for yy in range(y+16,y+hh-3,12):a.l([(x+2,yy),(x+ww-3,yy-3)],'gold0',2);a.dot(x+6,yy-3,'gold3')
  for x,y in [(48,48),(192,32),(40,80)]:vase(a,x,y,'rose3');a.l([(x-4,y+1),(x+4,y+1)],'gold2');a.dot(x-3,y-1,'rose5')
  for x,y in [(16,16),(224,16),(16,116),(128,142)]:tuft(a,x,y,'pine2')

def decor(a,r):
 n=r['id']
 for x,y,w,h in DECOR_SOLIDS[n]:
  if n==62:
   # Trees have joined trunks and layered living crowns; their whole footprint
   # is explicitly solid, so a path can never pass through painted foliage.
   a.e((x,y+h-10,x+w-1,y+h-1),'bg_sunlit_grass1')
   a.r((x+w//2-3,y+h//2,x+w//2+3,y+h-3),'wood1');a.l([(x+w//2-1,y+h//2),(x+w//2-1,y+h-5)],'wood4')
   for yy,rx in [(y+h//2,w//2),(y+h//3,w//2-1),(y+10,w//2-3)]:
    a.e((x+w//2-rx,yy-10,x+w//2+rx-1,yy+12),'pine1');a.e((x+w//2-rx+1,yy-10,x+w//2+rx-2,yy+7),'pine3');a.e((x+w//2-rx+3,yy-10,x+w//2+rx-4,yy+1),'bg_sunlit_pine4')
    a.l([(x+w//2-5,yy-7),(x+w//2-1,yy-9),(x+w//2+3,yy-8)],'bg_sunlit_leaflight')
   for dx,dy in [(4,14),(w-7,29),(5,h//2+5)]:a.e((x+dx,y+dy,x+dx+3,y+dy+3),'rose3');a.dot(x+dx,y+dy,'rose5')
  elif n==65:
   a.r((x,y,x+w-1,y+h-1),'wood1');a.r((x+2,y+2,x+w-3,y+h-4),'dirt0')
   for xx in range(x+6,x+w-5,9):
    for yy in (y+7,y+15):
     a.l([(xx,yy+4),(xx,yy-2)],'pine1');a.e((xx-4,yy-4,xx+4,yy+2),'pine3');a.l([(xx-3,yy-3),(xx,yy-4),(xx+2,yy-2)],'pine5');a.dot(xx,yy-3,'gold3')
   a.l([(x+1,y+1),(x+w-2,y+1)],'wood4');a.l([(x+1,y+h-2),(x+w-2,y+h-2)],'wood2',2)
  elif n==67:
   a.p([(x,y+h-1),(x+3,y+11),(x+w//2,y),(x+w-4,y+9),(x+w-1,y+h-1)],'stone1');a.p([(x+3,y+h-4),(x+6,y+12),(x+w//2,y+3),(x+w-7,y+11),(x+w-5,y+h-4)],'stone3');a.p([(x+6,y+13),(x+w//2,y+3),(x+w-7,y+11),(x+w//2,y+16)],'stone5')
   for yy in range(y+20,y+h-5,9):a.l([(x+5,yy),(x+w-5,yy-3)],'stone2',2)
  else:
   wood(a,x,y,w,h);a.l([(x+2,y+2),(x+w-3,y+h-3)],'wood5',2);a.l([(x+w-3,y+2),(x+2,y+h-3)],'wood2',2)

def sprite(n):
 a=Art(16,16,'transparent')
 if n in NAMES[:7]:
  a.e((2,13,14,15),'shadow');a.r((4,11,6,14),'wood1');a.r((10,11,12,14),'wood1');a.p([(4,7),(11,7),(13,12),(3,12)],'water3' if n in ('SCRIBE','HOST','HOST_WORK') else 'rose3' if n=='STORYTELLER' else 'gold2');a.r((5,2,11,7),'skin2');a.r((4,1,12,3),'wood1');a.dot(7,5,'ink');a.dot(10,5,'ink');a.l([(8,7),(10,7)],'skin0')
  if n in ('PORTER','PORTER_WORK'):a.r((0,6,4,12),'wood2');a.l([(1,8),(4,8)],'gold3')
  elif n=='SCRIBE':a.r((11,8,15,12),'white');a.l([(12,9),(14,11)],'water1')
  elif n=='STORYTELLER':a.p([(2,2),(7,0),(13,2)],'rose4');a.l([(0,9),(4,8)],'skin2',2)
  elif n=='JOINER':a.r((12,5,14,13),'wood1');a.r((10,5,15,7),'silver')
  else:a.r((3,2,13,3),'water4')
  if n.endswith('WORK'):a.l([(10,8),(15,6)],'skin2',2)
 elif n in ('REST','REST_LIT','WAX'):
  a.e((1,10,14,15),'stone2');a.l([(3,12),(12,9),(3,9),(12,12)],'wood2',2);a.p([(5,11),(4,6),(7,8),(8,2),(12,9),(10,12)],'fire2' if n!='REST' else 'gold1');a.p([(7,11),(8,6),(10,10)],'gold3')
 elif n in ('RESET','TRIAL','NOTICE'):
  a.r((7,10,9,15),'wood2');a.r((1,1,14,11),'wood1');a.r((2,2,13,10),'gold4')
  if n=='RESET':a.l([(4,6),(6,3),(10,4),(11,7),(8,9),(5,8)],'water2',2);a.p([(3,5),(7,5),(4,8)],'water2')
  elif n=='TRIAL':a.l([(4,8),(8,3),(12,8)],'gold1',2)
  else:a.l([(4,4),(11,4)],'wood2');a.l([(4,7),(10,7)],'wood2')
 elif n in ('CUP','BOWL'):a.e((1,5,14,14),'wood1');a.e((2,4,13,12),'water3');a.e((3,4,12,8),'gold4');a.e((5,5,10,7),'water2')
 elif n=='CARRIAGE':
  a.r((2,3,13,12),'wood2');a.r((3,2,12,10),'rose3');a.l([(4,4),(11,4)],'gold4');a.e((1,11,5,15),'wood1');a.e((10,11,14,15),'wood1')
 elif n=='PANEL':a.l([(1,1),(14,1)],'wood1');a.r((2,2,13,12),'rose4');a.l([(3,4),(12,10)],'gold4');a.l([(3,12),(12,12)],'rose2')
 elif n=='DONE':a.e((1,1,14,14),'pine3');a.l([(4,7),(7,11),(12,4)],'gold4',2)
 else:a.e((2,11,14,15),'shadow');a.r((3,4,12,12),'stone2');a.r((4,3,11,10),'gold2');a.l([(7,5),(7,9),(11,9)],'wood1',2)
 return a

def audit(r):
 w,h=r['width'],r['height'];b=occupancy(r,False);p=r['spawns']['0'];seen=bytearray(w*h);start=p[1]*w+p[0];q=deque([start]);seen[start]=1
 while q:
  p=q.popleft();x=p%w
  for z in (p-1,p+1,p-w,p+w):
   if 0<=z<w*h and abs(z%w-x)+abs(z//w-p//w)==1 and not b[z] and not seen[z]:seen[z]=1;q.append(z)
 for name,xy in list(r['spawns'].items())+[('reset',r['reset'])]:assert seen[xy[1]*w+xy[0]] and not b[xy[1]*w+xy[0]],(r['id'],name,xy)
 for x,y in r['objects']+r['field_targets']:
  assert any(0<=x+dx*d<w and 0<=y+dy*d<h and seen[(y+dy*d)*w+x+dx*d] and not b[(y+dy*d)*w+x+dx*d] for dx,dy in ((1,0),(-1,0),(0,1),(0,-1)) for d in range(16,27)),(r['id'],'approach',x,y)
 return {'reachable_pixels':sum(seen),'all_spawns_reset_and_cardinal_work_approaches':True}

def main():
 OUT.mkdir(exist_ok=True);plan=json.loads((ROOT/'docs/horizons-design/shared_horizons_plan.json').read_text());rooms=[];lines=[];budget=0;proof={};sheet=Image.new('RGB',(960,1280));cameras=Image.new('RGB',(960,640))
 header='''/* Generated Shared Horizons original pixels. */\n#ifndef EMBERBOND_HORIZONS_ART_H\n#define EMBERBOND_HORIZONS_ART_H\ntypedef struct { short x,y,w,h; } HorizonsArtRect;\ntypedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const HorizonsArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } HorizonsArtRoom;\nextern const HorizonsArtRoom horizons_art_rooms[8];\nenum {\n'''+''.join(f' HORIZONS_SPR_{n}={i},\n' for i,n in enumerate(NAMES))+' HORIZONS_SPR_COUNT=20 };\nextern const unsigned char horizons_sprites[20][256];\n#endif\n'
 for i,area in enumerate(plan['areas']):
  n=area['id'];w,h=area['size'];r={'id':n,'key':'room'+str(n),'width':w,'height':h,'safe_spine':area['safe_spine'],'spawns':{str(s['id']):s['center'] for s in area['spawns']},'solids':[{'rect':s} for s in SOLIDS[n]+DECOR_SOLIDS[n]],'objects':EXTRA[n],'field_targets':TARGETS[n],'reset':area['reset_point']}
  roads.open_borders(r);proof[str(n)]=audit(r);a=draw_room(r);raw=a.im.tobytes();assert min(raw)>0;a.im.save(OUT/f'room{n}.png');sheet.paste(a.im.convert('RGB'),((i%2)*480,(i//2)*320));cameras.paste(a.im.convert('RGB').crop((0,0,240,160)),((i%2)*480,(i//2)*160));cameras.paste(a.im.convert('RGB').crop((w-240,h-160,w,h)),((i%2)*480+240,(i//2)*160));r['bitmap_sha256']=hashlib.sha256(raw).hexdigest()
  for suffix,data in [('',raw)]+([('_odd',odd_bitmap(raw,w,h))] if w>240 else []):cbytes(lines,'horizons_background_'+r['key']+suffix,data);budget+=len(data)
  k=r['key'];lines.append('static const HorizonsArtRect horizons_'+k+'_solids[] = {'+','.join('{'+','.join(map(str,s))+'}'for s in SOLIDS[n]+DECOR_SOLIDS[n])+'};\n');rr,bb,stats=collision_bands(r)
  for suffix,values in [('rows',rr),('bands',bb)]:
   lines.append(f'static const unsigned short horizons_{k}_{suffix}[] = {{\n');lines.extend(' '+','.join(map(str,values[j:j+24]))+',\n'for j in range(0,len(values),24));lines.append('};\n');budget+=len(values)*2
  r['collision_lookup']=stats;rooms.append(r)
 lines.append('const unsigned char horizons_sprites[20][256] __attribute__((aligned(4))) = {\n');ss=Image.new('RGB',(160,32))
 for i,n in enumerate(NAMES):
  s=sprite(n);data=s.im.tobytes();ss.paste(s.im.convert('RGB'),((i%10)*16,(i//10)*16));lines.append(' {\n');lines.extend(' '+','.join(map(str,data[j:j+32]))+',\n'for j in range(0,256,32));lines.append(' },\n')
 lines.append('};\n');budget+=5120;lines.append('const HorizonsArtRoom horizons_art_rooms[8] = {\n')
 for r in rooms:
  k=r['key'];odd='horizons_background_'+k+'_odd' if r['width']>240 else '0';lines.append(f' {{{r["width"]},{r["height"]},horizons_background_{k},{odd},horizons_{k}_solids,{len(r["solids"])},horizons_{k}_rows,horizons_{k}_bands}},\n')
 lines.append('};\n');parts=[];p=''
 for line in lines:
  if len(p)+len(line)>32000:parts.append(p);p=''
  p+=line
 if p:parts.append(p)
 folder=SRC/'horizons_art_data';folder.mkdir(exist_ok=True)
 for old in folder.glob('part_*.inc'):old.unlink()
 for i,p in enumerate(parts):(folder/f'part_{i:03}.inc').write_text(p)
 (SRC/'horizons_art.h').write_text(header);(SRC/'horizons_art.c').write_text('#include "horizons_art.h"\n'+''.join(f'#include "horizons_art_data/part_{i:03}.inc"\n'for i in range(len(parts))))
 rom_bound=budget+sum(len(r['solids'])*8 for r in rooms)+len(rooms)*28+64
 sheet.save(OUT/'region_native.png');cameras.save(OUT/'camera_native.png');ss.save(OUT/'actors_native.png');ss.resize((960,192),Image.Resampling.NEAREST).save(OUT/'actors_6x.png')
 (OUT/'geometry.json').write_text(json.dumps({'rooms':rooms},indent=1)+'\n');(OUT/'validation.json').write_text(json.dumps({'scope':'Host geometry/art only; controller path separate','rooms':proof,'rom_art_bytes':rom_bound,'rom_art_bytes_kind':'Conservative ARM data bound including structures and64 alignment bytes; exact object size is measured separately','payload_bytes':budget,'cap':1310720},indent=1)+'\n');assert rom_bound<=1310720,rom_bound
 print('Horizons art payload',budget,'bytes; ARM bound',rom_bound,'bytes; 8 rooms certified')
if __name__=='__main__':main()
