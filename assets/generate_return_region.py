#!/usr/bin/env python3
"""Return I: eight original lived-in spaces; no external images or traced maps.
Geometry is half-open and feeds exact radius-five row-band collision certificates.
All dynamic actor pixels reuse the existing twenty-slot regional stream.
"""
from pathlib import Path
from collections import deque
from PIL import Image, ImageDraw
import connected_road_art as roads
import sys,json,hashlib,random,math
sys.dont_write_bytecode=True
from generate_assets import Art,P,PAL,COLORS
from generate_region import odd_bitmap,cbytes,occupancy,paste_sprite
from generate_northern_region import collision_bands
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/return_region';SRC=ROOT/'src'
NAMES=['GARDENER','BELLMAKER','PORTER','WEAVER','GUIDE','GARDENER_WORK','PORTER_WORK','REST','REST_LIT','RESET','TRIAL','NOTICE','HANDLE','RECEIVER','SAIL','SKIFF','HEARTH','ROOT','LATCH','DONE']
def ring(a,x,y,r=12,c='gold1'):
 a.l([(x-r,y-3),(x-3,y-r),(x+3,y-r),(x+r,y-3),(x+r,y+3),(x+3,y+r),(x-3,y+r),(x-r,y+3),(x-r,y-3)],c)
def arrow(a,x,y,dx,dy,c='wood2'):
 a.l([(x,y),(x+dx,y+dy)],c,2);xx=x+dx;yy=y+dy
 a.l([(xx-dx//4-dy//4,yy-dy//4+dx//4),(xx,yy),(xx-dx//4+dy//4,yy-dy//4-dx//4)],c,2)
def route(a,points,w=28,tone='bg_sunlit_dirt4'):
 a.l(points,'bg_sunlit_dirt1',w+6);a.l(points,tone,w)
def tree(a,x,y,variant=0):
 # Narrow espalier crowns stay inside the authored orchard's solid footprint.
 a.r((x-3,y-23,x+3,y),'bg_sunlit_wood1')
 a.l([(x,y-3),(x,y-24)],'bg_sunlit_barklight')
 a.l([(x,y-13),(x-10,y-24),(x,y-17),(x+10,y-29)],'bg_sunlit_wood2',2)
 for dx,dy,rx,ry in [(-8,-24,9,11),(7,-28,10,12),(0,-37,12,12)]:
  a.e((x+dx-rx,y+dy-ry,x+dx+rx,y+dy+ry),'bg_sunlit_pine1')
  a.e((x+dx-rx+1,y+dy-ry,x+dx+rx-1,y+dy+ry-4),'bg_sunlit_pine3')
  a.e((x+dx-rx+3,y+dy-ry+1,x+dx+rx-4,y+dy+ry-8),'bg_sunlit_pine4')
  a.l([(x+dx-4,y+dy-5),(x+dx-1,y+dy-7),(x+dx+3,y+dy-7)],'bg_sunlit_pine5')
 for dx,dy in [(-9,-28),(8,-37),(8,-20),(-4,-42)]:
  a.e((x+dx-2,y+dy-2,x+dx+2,y+dy+2),'rose3'if variant else'gold1')
  a.dot(x+dx-1,y+dy-1,'rose5'if variant else'gold3');a.dot(x+dx,y+dy-3,'bg_sunlit_pine1')

def flat_rug(a,box,c1,c2):
 # A woven cloth spread on the floor, with no raised edge or cast shadow.
 x,y,xx,yy=box;a.r(box,c1)
 for q in range(y+2,yy,4):a.l([(x+2,q),(xx-2,q)],c2)
 for q in range(x+2,xx,6):
  a.l([(q,y),(q,y+2)],'bg_sunlit_dirt4');a.l([(q,yy-2),(q,yy+1)],'bg_sunlit_dirt4')
 a.l([(x+1,y+1),(xx-1,y+1)],'bg_sunlit_dirt4')
 for q in range(x+5,xx-4,10):a.l([(q,y+5),(q+3,y+8),(q,y+11),(q-3,y+8),(q,y+5)],c2)

def floor_leaf(a,x,y,c='bg_sunlit_moss1'):
 a.l([(x-2,y),(x,y+1),(x+3,y-2)],c);a.dot(x,y-1,c)

def coil(a,x,y,c='wood4'):
 # Flat rope laid against the deck, never a new blocking prop.
 for rx,ry in [(8,5),(5,3)]:
  a.d.ellipse((x-rx,y-ry,x+rx,y+ry),outline=P[c])
 a.l([(x+8,y),(x+12,y+3),(x+17,y+3)],c)

def floor_texture(a,r):
 """Material wear only. Preserve quiet 32px aprons around all interactions."""
 R=random.Random(r['id']*173);w,h=r['width'],r['height'];points=[o['center']for o in r['objects']]+r.get('field_targets',[])
 for t in r['trial_workspaces']:points += [t['lectern']]+t['manual']+t['targets']+t['walk']
 def quiet(x,y):return any(abs(x-xx)<17 and abs(y-yy)<17 for xx,yy in points)
 def solid(x,y):return any(xx<=x<xx+ww and yy<=y<yy+hh for xx,yy,ww,hh in [s['rect']for s in r['solids']])
 tones={P['bg_sunlit_grass3']:('bg_sunlit_grass4','bg_sunlit_grass2'),P['bg_sunlit_grass2']:('bg_sunlit_grass3','bg_sunlit_grass1'),P['bg_sunlit_dirt3']:('bg_sunlit_dirt4','bg_sunlit_dirt2'),P['bg_sunlit_dirt4']:('bg_sunlit_stone5','bg_sunlit_dirt2'),P['bg_temple_stone4']:('bg_temple_stone5','bg_temple_stone3'),P['bg_temple_stone5']:('bg_sunlit_stone5','bg_temple_stone4'),P['wood3']:('wood4','wood2'),P['wood4']:('wood5','wood3'),P['wood5']:('gold4','wood4')}
 for _ in range(w*h//38):
  x=R.randrange(9,w-9);y=R.randrange(9,h-9)
  if quiet(x,y) or solid(x,y):continue
  p=a.im.getpixel((x,y));pair=tones.get(p)
  if not pair:continue
  c=pair[R.randrange(3)==0];n=R.randrange(1,4)
  for dx in range(n):
   if a.im.getpixel((x+dx,y))==p:a.dot(x+dx,y,c)
  if p in (P['bg_sunlit_grass3'],P['bg_sunlit_grass2']) and R.randrange(4)==0:a.dot(x+1,y-1,pair[0])
 # Worn joints in broad paths read as level pavers, not curbs.
 if r['id']not in(55,57):
  p=P['bg_sunlit_dirt4']
  for y in range(12,h-10,12):
   for x in range(12+(y//12%2)*9,w-10,18):
    if quiet(x,y)or solid(x,y):continue
    if all(a.im.getpixel((xx,yy))==p for xx,yy in[(x,y),(x+5,y),(x,y+3)]):
     a.l([(x,y),(x+5,y)],'bg_sunlit_dirt2');a.l([(x,y),(x,y+3)],'bg_sunlit_dirt2')

def border(a,r):
 w,h=r['width'],r['height'];deck=r['id']in(55,57);water=r['id']in(59,61)
 for v in roads.carve_solids(r['id'],r['solids'][:5]):
  x,y,ww,hh=v['rect'];a.r((x,y,x+ww-1,y+hh-1),'wood1'if deck else'bg_sunlit_stone2')
  a.l([(x,y),(x+ww-1,y)],'wood4'if deck else'bg_sunlit_stone5')
  if ww>hh:
   for xx in range(x+8,x+ww,16):
    a.l([(xx,y+1),(xx,y+hh-1)],'wood2'if deck else'bg_sunlit_stone1');a.dot(xx+2,y+2,'gold2'if deck else'bg_sunlit_stone4')
   a.l([(x,y+hh-2),(x+ww-1,y+hh-2)],'wood2'if deck else'bg_sunlit_stone1')
  else:
   for yy in range(y+8,y+hh,16):a.l([(x+1,yy),(x+ww-2,yy)],'wood2'if deck else'bg_sunlit_stone1')
   a.l([(x+ww-2,y),(x+ww-2,y+hh-1)],'wood4'if deck else'bg_sunlit_stone4')
 if water:
  # Water is beyond the parapet, solely within the non-walkable border.
  a.r((0,0,w-1,4),'water1');a.l([(0,4),(w-1,4)],'water4')
  for x in range(5,w,17):a.l([(x,1),(x+7,1)],'water3')
 elif r['id']in(54,56,58):
  for x in range(18,w-16,28):
   a.l([(x,1),(x+5,4),(x+10,2)],'bg_sunlit_pine2');a.dot(x+3,2,'bg_sunlit_pine4');a.dot(x+8,3,'gold3'if r['id']==54 else'rose4')
 # Building exits retain their door; converted exterior maps close the old south gate.
 if r['id'] in(54,56,57,58,59,61):
  c='wood1'if deck else'bg_sunlit_stone2'
  a.r((w//2-24,h-8,w//2+23,h-1),c)
  a.l([(w//2-24,h-8),(w//2+23,h-8)],'wood4'if deck else'bg_sunlit_stone5')
  return
 route(a,[(w//2,h-28),(w//2,h-1)],32,'wood5'if deck else'bg_sunlit_dirt4')
 a.l([(w//2-13,h-9),(w//2+13,h-9)],'wood4'if deck else'bg_sunlit_dirt2')
 a.l([(w//2-13,h-5),(w//2+13,h-5)],'wood4'if deck else'bg_sunlit_dirt2')

def draw_room(r):
 id=r['id'];w,h=r['width'],r['height'];base='bg_sunlit_grass3'if id==54 else'bg_sunlit_dirt3'if id in(56,58)else'wood3'if id in(55,57)else'bg_temple_stone4';a=Art(w,h,base);R=random.Random(id*173)
 if id==54:
  # Soft canopy dapples and wildflower ground cover keep the commons open.
  for x,y,rx,ry in [(32,40,33,20),(170,43,49,23),(304,107,50,24),(366,184,40,32),(112,285,49,19),(393,294,48,15),(41,195,27,29)]:
   a.e((x-rx,y-ry,x+rx,y+ry),'bg_sunlit_grass2')
   for k in range(12):
    xx=x+R.randrange(-rx,rx);yy=y+R.randrange(-ry,ry);a.e((xx-3,yy-2,xx+4,yy+2),'bg_sunlit_grass3')
  route(a,[(240,320),(240,240),(96,240),(96,32)],34);route(a,[(96,240),(416,240),(416,40),(240,40),(240,240)],30)
  for x,y in [(34,92),(49,172),(115,195),(302,24),(362,27),(380,282),(280,288),(435,212),(348,206)]:
   for k in range(6):
    xx=x+R.randrange(-10,11);yy=y+R.randrange(-5,6);floor_leaf(a,xx,yy,'bg_sunlit_grass1');a.dot(xx,yy-1,'flower1'if k%2 else'gold3')
  # Orchard bed, trellises, roots and crowns are all inside one solid island.
  a.r((156,72,191,215),'bg_sunlit_wood1');a.r((158,74,189,212),'bg_sunlit_dirt1')
  for y in range(82,213,12):a.l([(160,y),(188,y)],'bg_sunlit_wood2')
  for y in[77,208]:a.l([(159,y),(188,y)],'bg_sunlit_wood4')
  for y in[121,168,214]:tree(a,174,y,True)
  for x,y in [(160,202),(184,205),(163,151),(183,105)]:a.dot(x,y,'rose4');a.dot(x+1,y,'gold3')
  # Shared masonry hearth: hearth ring, split fuel and simmering copper pot.
  a.r((288,144,335,191),'bg_sunlit_stone1');a.r((290,144,333,188),'bg_sunlit_stone3');a.r((293,148,330,184),'bg_sunlit_dirt2')
  for y in range(149,188,10):
   a.l([(289,y),(293,y)],'bg_sunlit_stone5');a.l([(330,y+3),(334,y+3)],'bg_sunlit_stone5')
  for x in range(295,332,10):a.l([(x,145),(x,148)],'bg_sunlit_stone1');a.l([(x,185),(x,188)],'bg_sunlit_stone1')
  a.e((297,151,327,181),'wood1');a.e((300,153,324,180),'fire0')
  a.l([(303,174),(321,179),(320,173),(304,180)],'wood3',2)
  a.p([(306,174),(304,166),(309,168),(311,157),(315,164),(319,161),(321,172),(316,178)],'fire2');a.p([(310,176),(311,166),(315,171),(316,178)],'gold3')
  a.l([(300,159),(325,159)],'wood1',2);a.e((307,158,320,168),'stone1');a.l([(309,159),(318,159)],'silver');a.dot(314,156,'white')
  for x in[296,301,324,328]:a.r((x,183,x+3,185),'bg_sunlit_wood2');a.dot(x+1,183,'bg_sunlit_wood4')
  flat_rug(a,(26,206,66,225),'bg_sunlit_dirt2','bg_sunlit_dirt3')
  flat_rug(a,(346,276,384,295),'bg_sunlit_dirt2','bg_sunlit_dirt3')
  # A stitched picnic cloth and scattered petals are level with the grass.
  a.e((34,211,40,216),'bg_sunlit_stone5');a.e((49,216,56,221),'bg_sunlit_stone5');a.dot(37,213,'rose4');a.dot(52,218,'gold2')
  for x,y in[(129,36),(132,39),(124,42),(350,136),(354,139)]:floor_leaf(a,x,y)
 elif id==55:
  # Every plank has staggered joins, pegged nails and restrained wood grain.
  for y in range(8,153,12):
   a.r((8,y,231,y+10),'wood3'if(y//12)%3 else'wood4');a.l([(8,y+10),(231,y+10)],'wood2');a.l([(8,y),(231,y)],'wood4')
   for x in range(12+(y//12%3)*21,232,63):
    a.l([(x,y+1),(x,y+9)],'wood2');a.dot(x+2,y+2,'wood1');a.dot(x-2,y+8,'wood1');a.l([(x+8,y+4),(min(x+29,230),y+4)],'wood3'if(y//12)%3==0 else'wood4')
  # High-window light and rafter shadows fall onto a completely level floor.
  a.p([(12,9),(39,9),(91,48),(60,48)],'wood4');a.p([(190,9),(214,9),(225,40),(201,40)],'wood4')
  for x in[16,224]:a.l([(x,8),(x,145)],'wood2',3);a.l([(x+1,8),(x+1,145)],'wood4')
  # Bellmaking bench is the single fixed footprint. Brass shells sit on it.
  a.r((96,32,143,47),'wood1');a.r((98,33,141,44),'wood4');a.l([(99,34),(140,34)],'wood5');a.l([(98,44),(141,44)],'wood2')
  for x in[106,121,135]:
   a.p([(x-3,35),(x+3,35),(x+5,41),(x-5,41)],'gold1');a.l([(x-4,40),(x+4,40)],'gold3');a.dot(x,34,'gold4');a.dot(x,42,'wood1')
  # Sound circles and staff lines are chalk inlays, not hanging obstacles.
  for x in[64,120,176]:
   a.d.arc((x-19,53,x+19,89),195,340,fill=P['wood4'])
   a.d.arc((x-22,50,x+22,92),205,330,fill=P['wood4'])
   for xx in[-4,0,4]:a.l([(x+xx,19),(x+xx,25-(xx==0)*3)],'gold3')
   a.l([(x-7,28),(x+7,28)],'wood5')
  for y in[99,102,105]:a.l([(32,y),(79,y)],'wood4');a.l([(160,y),(215,y)],'wood4')
  for x in[45,59,70,169,183,198]:a.e((x,100,x+3,102),'wood5');a.l([(x+3,97),(x+3,101)],'wood5')
  flat_rug(a,(97,117,143,130),'wood2','wood3')
  coil(a,30,28,'wood5');coil(a,197,134,'wood4')
  for x,y in[(88,124),(150,26)]:a.l([(x,y),(x+7,y+2),(x+4,y+5)],'wood5')
 elif id==56:
  # A braided public garden: low herbs are ground cover, ponds are true solids.
  for box in[(17,16,195,32),(106,180,190,218),(291,20,390,39),(355,169,398,190),(17,294,195,307),(286,294,451,307)]:
   x,y,xx,yy=box;a.r(box,'bg_sunlit_grass3')
   for q in range(x+4,xx-3,9):
    for z in range(y+4,yy-2,7):floor_leaf(a,q,z,'bg_sunlit_pine2');a.dot(q,z-1,'gold3'if(q+z)%3 else'rose4')
  route(a,[(240,320),(240,48),(80,48),(80,272),(432,272),(432,48),(240,48)],30)
  # Narrow channels are explicitly inset grates, with crossbars to walk over.
  for pts in[[(240,96),(264,120),(264,184),(240,208)],[(32,80),(48,96),(48,184),(32,208)],[(336,128),(356,152),(392,168)]]:
   a.l(pts,'bg_sunlit_stone3',9);a.l(pts,'water3',4);a.l(pts,'water4',1)
  for y in range(125,181,9):a.l([(260,y),(268,y)],'bg_sunlit_stone5')
  for y in range(100,184,9):a.l([(44,y),(52,y)],'bg_sunlit_stone5')
  for x,y,ww,hh in[s['rect']for s in r['solids'][5:]]:
   a.r((x,y,x+ww-1,y+hh-1),'bg_sunlit_stone1');a.r((x+1,y+1,x+ww-2,y+hh-3),'bg_sunlit_stone4');a.r((x+4,y+4,x+ww-5,y+hh-5),'water1');a.r((x+6,y+5,x+ww-6,y+hh-6),'water3')
   for yy in range(y+11,y+hh-9,12):a.l([(x+8,yy),(x+ww-9,yy)],'water4')
   for yy in range(y+4,y+hh-4,12):a.l([(x+1,yy),(x+4,yy)],'bg_sunlit_stone1');a.l([(x+ww-4,yy+3),(x+ww-2,yy+3)],'bg_sunlit_stone1')
   for xx in range(x+8,x+ww-7,12):a.e((xx-4,y+hh-18,xx+5,y+hh-12),'pine3');a.l([(xx,y+hh-14),(xx+3,y+hh-15)],'pine5');a.dot(xx+2,y+hh-17,'flower1')
   for xx in range(x+8,x+ww-5,11):a.l([(xx,y+hh-5),(xx-2,y+hh-12)],'pine2');a.dot(xx-2,y+hh-13,'gold2')
  # Interlaced stone ribbons carry the water garden's knot motif.
  for x,y in[(118,104),(327,52),(346,204),(177,251)]:
   a.l([(x-9,y),(x,y-5),(x+9,y),(x,y+5),(x-9,y)],'bg_sunlit_dirt2');a.l([(x-9,y+6),(x,y+1),(x+9,y+6),(x,y+11),(x-9,y+6)],'bg_sunlit_stone3')
  arrow(a,208,240,16,0);arrow(a,272,240,16,0)
 elif id==57:
  # Sea-worn public deck, with individual planks and repaired joinery.
  for y in range(8,312,12):
   if y//12%4==0:a.r((8,y,471,y+10),'wood4')
   a.l([(8,y+11),(471,y+11)],'wood2');a.l([(8,y),(471,y)],'wood4')
   for x in range(16+(y//12%4)*18,472,72):
    a.l([(x,y+1),(x,y+10)],'wood2');a.dot(x+2,y+2,'wood1');a.dot(x-2,y+9,'wood1')
  # Sun through furled sails throws warm triangular shapes onto the deck.
  for pts in[[(12,16),(183,16),(156,50),(32,65)],[(285,18),(397,18),(377,50),(310,43)],[(96,141),(200,148),(158,180)]]:a.p(pts,'wood4')
  route(a,[(240,320),(240,240),(64,240),(64,32),(416,32),(416,288),(240,288)],28,'wood5')
  for y in range(24,313,12):
   for x in range(12,471,4):
    if a.im.getpixel((x,y))==P['wood5']:a.l([(x,y),(x+2,y)],'wood4')
  # Three strapped freight crates fit the existing high cargo spine exactly.
  a.r((216,88,255,191),'wood1')
  for y,hh in[(89,31),(123,31),(157,33)]:
   a.r((217,y,254,y+hh-1),'wood2');a.r((219,y+1,252,y+hh-4),'wood3');a.l([(220,y+2),(250,y+2)],'wood5')
   for x in[224,247]:a.r((x,y+1,x+2,y+hh-3),'gold1');a.dot(x+1,y+3,'gold4');a.dot(x+1,y+hh-5,'gold4')
   a.l([(228,y+6),(243,y+hh-8),(228,y+hh-8),(243,y+6)],'wood2')
   a.r((231,y+12,240,y+19),'wood5');a.l([(233,y+14),(238,y+14)],'wood2');a.dot(236,y+17,'wood2')
  # Sailmaker's solid bench carries bolts of canvas, needle and tied parcels.
  a.r((288,136,383,159),'wood1');a.r((289,137,382,155),'wood4');a.l([(290,137),(381,137)],'wood5')
  for x in[294,316,338]:
   a.r((x,140,x+17,151),'white'if x!=316 else'rose4');a.l([(x+2,143),(x+14,143)],'bg_sunlit_dirt2'if x!=316 else'rose3');a.l([(x+5,139),(x+5,152)],'gold1');a.e((x+13,140,x+18,151),'bg_sunlit_dirt3'if x!=316 else'rose3')
  a.l([(362,140),(371,151)],'silver',2);a.l([(362,151),(371,140)],'white');coil(a,371,147,'wood2')
  # Stencilled load zones and coiled lines lie flush with the planks.
  for x,y in[(30,158),(138,204),(356,92),(453,47),(271,297)]:coil(a,x,y,'wood4'if x!=453 else'wood5')
  for x,y in[(122,158),(323,107),(365,238)]:
   a.l([(x-13,y-7),(x+13,y-7),(x+13,y+7),(x-13,y+7),(x-13,y-7)],'wood4');a.l([(x-6,y+3),(x,y-3),(x+6,y+3)],'wood4')
  # Tiny wall-hung signal flags sit on the solid north rail only.
  for x in range(20,460,34):a.p([(x,1),(x+10,1),(x+5,6)],'rose4'if x%3 else'water3')
  a.l([(280,176),(432,176)],'wood4')
  for x in range(288,433,24):a.l([(x,177),(x+6,183),(x+12,177)],'wood4')
 elif id==58:
  # Sun-baked terrace tiles are continuous walkable paving at every seam.
  for y in range(8,312,16):
   for x in range(8-(y//16%2)*12,472,24):
    a.l([(x,y+15),(x+22,y+15)],'bg_sunlit_dirt2');a.l([(x+23,y),(x+23,y+14)],'bg_sunlit_dirt2')
    if(x//24+y//16)%4==0:a.l([(x+3,y+2),(x+15,y+2)],'bg_sunlit_dirt4')
  # Shade patterns are pale floor-plane silhouettes without rails or posts.
  for pts in[[(8,12),(144,12),(181,49),(45,49)],[(268,10),(447,10),(471,49),(301,49)],[(9,181),(53,181),(89,236),(45,236)],[(347,177),(469,177),(469,205),(377,205)]]:
   a.p(pts,'bg_sunlit_dirt2')
  route(a,[(240,320),(240,256),(72,256),(72,48),(176,48),(176,176),(432,176),(432,272),(240,272)],30)
  for y in[32,168,272]:
   # Thin alternating tesserae replace the old wall-looking terrace stripes.
   for x in range(16,464,8):a.l([(x,y),(x+4,y)],'bg_sunlit_dirt2');a.dot(x+2,y+2,'bg_sunlit_stone5')
  # The tall linen screen stands entirely on its existing solid plinth.
  a.r((208,56,255,151),'bg_sunlit_stone1');a.r((210,57,253,148),'bg_sunlit_stone3');a.r((214,59,249,145),'wood2');a.r((216,60,247,143),'plaster')
  for y in range(64,142,5):a.l([(218,y),(245,y)],'bg_sunlit_wood4')
  for y,c in[(67,'rose3'),(97,'water2'),(126,'rose3')]:
   a.r((218,y,245,y+8),c)
   for x in range(220,244,6):a.l([(x,y+4),(x+3,y+1),(x+6,y+4),(x+3,y+7),(x,y+4)],'gold3')
  for x in range(217,248,4):a.l([(x,142),(x,146+(x%3))],'gold2')
  a.l([(211,58),(251,58)],'bg_sunlit_stone5');a.l([(211,149),(251,149)],'bg_sunlit_stone2')
  # Mosaic fountain: all rims, reeds and water remain in its 40px footprint.
  a.r((304,192,343,231),'bg_sunlit_stone1');a.r((306,193,341,228),'bg_sunlit_stone4');a.r((310,197,337,224),'water1');a.r((312,199,335,222),'water3')
  for x in range(309,338,6):a.dot(x,194,'water2');a.dot(x,227,'rose3')
  for y in range(201,223,8):a.l([(314,y),(333,y)],'water4')
  a.e((318,204,330,216),'water2');a.d.arc((319,205,329,215),10,270,fill=P['water4']);a.dot(324,209,'white')
  flat_rug(a,(101,177,154,205),'bg_sunlit_dirt2','bg_sunlit_stone3')
  flat_rug(a,(276,34,336,49),'bg_sunlit_dirt2','bg_sunlit_dirt3')
  for x,y in[(32,64),(24,128),(287,153),(452,299),(109,292),(197,290)]:
   for k in range(5):floor_leaf(a,x+k*3,y+(k%2)*3);a.dot(x+k*3,y-1+(k%2)*3,'rose4')
 elif id==59:
  # The landing is a solid timber jetty over the river, with stone aprons.
  a.r((8,8,231,37),'wood3')
  for y in range(10,38,7):
   a.l([(8,y),(231,y)],'wood2');a.l([(8,y+1),(231,y+1)],'wood4')
   for x in range(18+(y//7%2)*17,230,35):a.dot(x,y+2,'wood1');a.l([(x,y+2),(x,y+6)],'wood2')
  # Mooring chest is confined to the one solid rectangle.
  a.r((96,32,127,47),'wood1');a.r((98,33,125,44),'wood3');a.l([(98,33),(125,33)],'wood5')
  for x in[101,121]:a.r((x,33,x+2,44),'gold1');a.dot(x+1,35,'gold3')
  a.r((109,36,115,41),'wood4');a.dot(112,39,'wood1')
  route(a,[(120,160),(120,120),(40,120),(40,48),(208,48),(208,120),(120,120)],25)
  # Riverglass is a shallow floor inlay, with visible slab bridges throughout.
  a.r((48,84,191,92),'bg_sunlit_stone3');a.r((49,86,190,90),'water3');a.l([(49,87),(190,87)],'water4')
  for x in range(54,191,12):a.l([(x,84),(x,92)],'bg_sunlit_stone5',2)
  for x,y in[(29,24),(154,24),(220,24)]:coil(a,x,y,'wood5')
  for y in[62,74,105,135]:
   for x in range(14,230,24):
    if y==105 and 80<x<163:continue
    a.l([(x,y),(x+9,y)],'bg_temple_stone3')
  # Faded fish-and-current floor mosaic says river without a false water pit.
  for x,y in[(77,135),(164,134),(115,64)]:
   a.p([(x-5,y),(x+2,y-3),(x+5,y),(x+2,y+3)],'bg_temple_stone3');a.p([(x-5,y),(x-8,y-3),(x-8,y+3)],'bg_temple_stone3');a.dot(x+2,y,'bg_sunlit_stone5')
  a.l([(73,140),(85,140),(91,137)],'bg_temple_stone3');a.l([(152,139),(167,139)],'bg_temple_stone3')
 elif id==60:
  # Entire room is a flush mosaic, including its border legends and compass.
  for y in range(8,153,12):
   for x in range(8,233,12):
    if(x//12+y//12)%2:a.r((x,y,x+10,y+10),'bg_temple_stone5')
    a.dot(x+10,y+10,'bg_temple_stone3')
  a.e((33,17,207,126),'bg_temple_stone3');a.e((36,20,204,123),'bg_temple_gold1');a.e((38,22,202,121),'bg_temple_stone5')
  for k in range(48):
   t=k*math.pi/24;x=120+int(math.cos(t)*83);y=72+int(math.sin(t)*49);a.dot(x,y,'wood2')
  # Five distinct pieces of a shared map keep their existing target centers.
  regions=[([(44,39),(58,31),(73,41),(72,58),(56,64),(43,54)],'pine4','pine2'),([(80,31),(94,23),(110,29),(113,42),(100,52),(86,46)],'fire2','fire0'),([(130,27),(146,24),(162,33),(156,49),(143,53),(128,42)],'wood3','wood1'),([(169,34),(183,32),(198,43),(195,57),(180,62),(166,49)],'silver','stone2'),([(105,94),(120,88),(136,96),(138,108),(124,117),(108,111)],'water3','water1')]
  for poly,c,edge in regions:
   a.p(poly,edge);cx=sum(p[0]for p in poly)//len(poly);cy=sum(p[1]for p in poly)//len(poly);inner=[(cx+(x-cx)*4//5,cy+(y-cy)*4//5)for x,y in poly];a.p(inner,c)
   for xx,yy in inner[::2]:a.dot(xx,yy,'gold4')
  a.e((84,54,156,91),'bg_temple_gold1');a.e((87,57,153,88),'water3')
  a.p([(112,64),(123,60),(138,68),(130,75),(117,74),(109,81),(98,76)],'bg_sunlit_stone5');a.l([(95,84),(107,82),(116,85),(141,80)],'water4')
  for x,y in[(56,48),(96,40),(144,40),(184,48),(120,104)]:a.l([(x,y),(120,76)],'bg_temple_gold1')
  # Compass points have tile gaps and no beveled tabletop silhouette.
  a.p([(120,63),(123,73),(133,76),(123,79),(120,88),(117,79),(107,76),(117,73)],'gold2');a.p([(120,64),(120,76),(108,76),(118,73)],'gold4')
  for x,c in[(14,'pine3'),(218,'water2')]:
   a.r((x,17,x+8,65),'bg_temple_stone3');a.r((x+1,18,x+7,64),'bg_temple_stone5');a.l([(x+2,22),(x+6,28),(x+2,38),(x+6,47),(x+2,57)],c)
   for y in range(21,62,8):a.dot(x+4,y,'bg_temple_gold1')
  for x in range(56,199,12):a.dot(x,135,'bg_temple_gold1');a.l([(x-2,137),(x+2,137)],'bg_temple_stone3')
 elif id==61:
  # Sea-glass causeway: level stone slabs, tide stains, and a north parapet.
  for y in range(8,151,16):
   for x in range(8-(y//16%2)*16,232,32):
    a.l([(x,y+15),(x+30,y+15)],'bg_temple_stone3');a.l([(x+31,y),(x+31,y+14)],'bg_temple_stone3')
    a.l([(x+3,y+2),(x+19,y+2)],'bg_temple_stone5')
  for x in[16,224]:
   a.l([(x,10),(x,141)],'bg_sunlit_stone3',3)
   for y in range(14,141,12):a.dot(x,y,'water3');a.dot(x+1,y+1,'water4')
  route(a,[(120,160),(120,120),(40,120),(40,56),(80,56)],26);route(a,[(120,120),(208,120),(208,56),(160,56)],26)
  a.r((160,32,191,47),'bg_sunlit_stone1');a.r((161,33,190,45),'bg_sunlit_stone4');a.r((164,34,187,43),'bg_temple_gold1');a.r((166,35,185,41),'gold3');a.l([(169,38),(174,35),(181,39)],'gold1');a.dot(177,42,'white')
  # A braided glass inlay visibly shares the same plane as the slab joints.
  for y in range(56,117,8):
   a.l([(111,y),(120,y+4),(129,y)],'bg_sunlit_stone3');a.l([(111,y+1),(120,y+5),(129,y+1)],'water3');a.dot(120,y+5,'water4')
  a.l([(88,56),(103,56)],'bg_temple_gold1');a.l([(137,56),(152,56)],'bg_temple_gold1')
  for x,y in[(43,27),(196,27),(82,116),(160,116)]:
   a.l([(x-8,y),(x-2,y-3),(x+4,y),(x+10,y-3)],'bg_temple_stone3');a.l([(x-6,y+4),(x+5,y+4)],'bg_temple_stone5')
  for x,y in[(84,144),(156,143),(24,91),(215,99)]:floor_leaf(a,x,y,'bg_sunlit_stone3')
 floor_texture(a,r);border(a,r);roads.draw(a,id,P)
 # Every interactive prop retains its24px marking and clear facing apron.
 for tr in r['trial_workspaces']:
  x,y=tr['lectern'];a.r((x-11,y-8,x+11,y+8),'bg_temple_stone3');a.l([(x-8,y+4),(x,y-5),(x+8,y+4)],'gold4',2)
  for x,y in tr['targets']:ring(a,x,y,12,'bg_sunlit_stone2')
  for x,y in tr['walk']:a.r((x-9,y-5,x+9,y+5),'bg_sunlit_dirt4');arrow(a,x-6,y,12,0,'gold1')
 # Rings finish above nearby walk arrows, which must not erase their24px edge.
 for o in r['objects']:ring(a,*o['center'],12,'gold1')
 return a

def sprite(n):
 a=Art(16,16,'transparent')
 if n in NAMES[:7]:
  base=n.replace('_WORK','');a.e((2,13,14,15),'shadow');a.r((5,11,7,14),'wood1');a.r((10,11,12,14),'wood1');a.p([(4,7),(11,7),(13,12),(3,12)],'pine3'if base=='GARDENER'else'water2'if base=='WEAVER'else'rose3');a.r((5,2,11,7),'skin2');a.r((4,1,12,3),'wood1');a.dot(7,5,'ink');a.dot(10,5,'ink');a.l([(8,7),(10,7)],'skin0')
  if base=='GARDENER':a.r((2,2,14,3),'gold2');a.r((5,0,11,2),'gold1');a.l([(13,8),(14,14)],'wood3')
  elif base=='BELLMAKER':a.r((3,1,13,2),'silver');a.r((12,7,15,9),'gold2')
  elif base=='PORTER':a.r((0,6,4,12),'wood2');a.l([(1,7),(3,10)],'gold3')
  elif base=='WEAVER':a.l([(2,8),(2,12),(13,12)],'gold2');a.r((1,9,3,10),'water4')
  elif base=='GUIDE':a.p([(3,3),(7,0),(12,3)],'rose4');a.r((12,7,15,12),'white')
  if n.endswith('_WORK'):a.l([(10,8),(15,6)],'skin2',2)
 elif n in ['REST','REST_LIT','HEARTH']:
  a.e((1,10,14,15),'stone2');a.l([(3,12),(12,9),(3,9),(12,12)],'wood2',2);a.p([(5,11),(4,6),(7,8),(8,2),(12,9),(10,12)],'fire2'if n!='REST'else'gold1');a.p([(7,11),(8,6),(10,10)],'gold3')
 elif n in ['NOTICE','TRIAL','RESET']:
  a.r((7,10,9,15),'wood2');a.r((1,1,14,11),'wood1');a.r((2,2,13,10),'white')
  if n=='RESET':a.l([(4,6),(6,3),(10,4),(11,7),(8,9),(5,8)],'water2',2);a.p([(3,5),(7,5),(4,8)],'water2')
  elif n=='TRIAL':a.l([(4,8),(8,3),(12,8)],'gold1',2);a.dot(8,7,'pine3')
  else:a.l([(4,4),(11,4)],'wood2');a.l([(4,6),(11,6)],'wood2');a.l([(4,8),(8,8)],'wood2')
 elif n=='SKIFF':
  a.p([(0,8),(15,8),(12,13),(4,13)],'wood2');a.l([(1,8),(14,8)],'gold3');a.l([(8,1),(8,9)],'wood1');a.p([(9,2),(14,6),(9,6)],'white')
 elif n=='SAIL':
  a.l([(7,1),(7,14)],'wood1',2);a.p([(8,1),(15,8),(8,10)],'white');a.p([(6,3),(1,8),(6,10)],'rose4');a.l([(2,14),(12,14)],'wood2',2)
 elif n=='ROOT':
  a.l([(8,14),(8,5),(3,1)],'pine2',3);a.l([(8,8),(13,2)],'pine3',2);a.e((0,1,6,5),'pine5');a.e((10,0,15,4),'pine4')
 elif n=='DONE':a.e((1,1,14,14),'pine3');a.l([(4,7),(7,11),(12,4)],'gold4',2)
 else:
  a.e((2,11,14,15),'shadow');a.r((3,4,12,12),'stone2');a.r((4,3,11,10),'gold2');a.l([(7,5),(7,9),(11,9)],'wood1',2)
 return a

def audit(r):
 w,h=r['width'],r['height'];b=occupancy(r,False);s=r['spawns']['0'];seen=bytearray(w*h);q=deque([s[1]*w+s[0]]);seen[q[0]]=1
 while q:
  p=q.popleft();x=p%w
  for n in [p-1,p+1,p-w,p+w]:
   if 0<=n<w*h and abs(n%w-x)+abs(n//w-p//w)==1 and not b[n] and not seen[n]:seen[n]=1;q.append(n)
 for name,p in [('spawn'+k,v)for k,v in r['spawns'].items()]+[('exit',v['approach'])for v in r['exits']]+[('enemy',v)for v in r['enemy_spawns']]:assert seen[p[1]*w+p[0]] and not b[p[1]*w+p[0]],(r['id'],name,p)
 pts=[v['center']for v in r['objects']]+r.get('field_targets',[])
 for tr in r['trial_workspaces']:
  pts += [tr['lectern']]+tr['manual']+tr['targets']
  for p in tr['walk']:assert seen[p[1]*w+p[0]] and not b[p[1]*w+p[0]],(r['id'],'walk',p)
 for x,y in pts:
  approaches=[[x+dx*d,y+dy*d]for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]for d in range(16,27)if 0<=x+dx*d<w and 0<=y+dy*d<h and seen[(y+dy*d)*w+x+dx*d]and not b[(y+dy*d)*w+x+dx*d]]
  assert approaches,(r['id'],'unreachable target',x,y)
  for ob in r['objects']:
   if ob['center']==[x,y]:ob['approach']=approaches[0]
 return {'reachable_pixels':sum(seen),'target_count':len(pts),'all_spawns_exits_walks_and_cardinal_approaches':True}

def main():
 rooms=json.loads((OUT/'geometry.json').read_text())['rooms'];lines=[];header='''/* Generated original Return world. Immutable shared palette. */
#ifndef EMBERBOND_RETURN_ART_H
#define EMBERBOND_RETURN_ART_H
#define RETURN_ART_FIRST_ROOM 54
#define RETURN_ART_ROOM_COUNT 8
#define RETURN_ART_FOOT_RADIUS 5
typedef struct { short x,y,w,h; } ReturnArtRect;
typedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const ReturnArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } ReturnArtRoom;
extern const ReturnArtRoom return_art_rooms[8];
enum {\n'''+''.join(f' RETURN_SPR_{n}={i},\n'for i,n in enumerate(NAMES))+' RETURN_SPR_COUNT=20 };\nextern const unsigned char return_sprites[20][256];\n';budget=0;proof={};overview=Image.new('RGB',(960,1280));cameras=Image.new('RGB',(960,640))
 for i,r in enumerate(rooms):
  a=draw_room(r)
  if r['id'] in(54,56,57,58,59,61):r['solids'].append({'kind':'retired_south_gate','rect':[r['width']//2-24,r['height']-8,48,8]})
  roads.open_borders(r);proof[str(r['id'])]=audit(r);data=a.im.tobytes();r['bitmap_sha256']=hashlib.sha256(data).hexdigest();key=r['key'];w=r['width'];h=r['height'];assert min(data)>0
  a.im.save(OUT/(key+'.png'));a.im.resize((w*4,h*4),Image.Resampling.NEAREST).save(OUT/(key+'_4x.png'));overview.paste(a.im.convert('RGB'),((i%2)*480,(i//2)*320))
  for j,(cx,cy) in enumerate([(0,0),(120,80)]if w>240 else[(0,0),(0,0)]):cameras.paste(a.im.convert('RGB').crop((cx,cy,cx+240,cy+160)),((i%2)*480+j*240,(i//2)*160))
  for suffix,raw in [('',data)]+([('_odd',odd_bitmap(data,w,h))]if w>240 else[]):cbytes(lines,'return_background_'+key+suffix,raw);budget+=len(raw);header+=f'extern const unsigned char return_background_{key+suffix}[{len(raw)}];\n'
  lines.append('static const ReturnArtRect return_'+key+'_solids[] = {'+','.join('{'+','.join(map(str,s['rect']))+'}'for s in r['solids'])+'};\n')
  rr,bb,stats=collision_bands(r);r['collision_lookup']=stats
  for suffix,values in [('rows',rr),('bands',bb)]:
   lines.append(f'static const unsigned short return_{key}_{suffix}[] = {{\n');lines.extend(' '+','.join(map(str,values[k:k+24]))+',\n'for k in range(0,len(values),24));lines.append('};\n');budget+=len(values)*2
 sprites={n:sprite(n)for n in NAMES};lines.append('const unsigned char return_sprites[20][256] __attribute__((aligned(4))) = {\n')
 for n in NAMES:
  lines.append(' {\n');data=sprites[n].im.tobytes();lines.extend(' '+','.join(map(str,data[k:k+32]))+',\n'for k in range(0,256,32));lines.append(' },\n')
 lines.append('};\n');budget+=5120
 lines.append('const ReturnArtRoom return_art_rooms[8] = {\n')
 for r in rooms:
  k=r['key'];odd='return_background_'+k+'_odd'if r['width']>240 else'0';lines.append(f' {{{r["width"]},{r["height"]},return_background_{k},{odd},return_{k}_solids,{len(r["solids"])},return_{k}_rows,return_{k}_bands}},\n')
 lines.append('};\n');parts=[];p=''
 for line in lines:
  if len((p+line).encode())>32000:parts.append(p);p=''
  p+=line
 if p:parts.append(p)
 folder=SRC/'return_art_data';folder.mkdir(exist_ok=True)
 for f in folder.glob('part_*.inc'):f.unlink()
 for i,p in enumerate(parts):(folder/f'part_{i:03}.inc').write_text(p)
 (SRC/'return_art.h').write_text(header+'#endif\n');(SRC/'return_art.c').write_text('#include "return_art.h"\n'+''.join(f'#include "return_art_data/part_{i:03}.inc"\n'for i in range(len(parts))))
 sheet=Image.new('RGB',(160,32))
 for i,(n,s)in enumerate(sprites.items()):paste_sprite(sheet,s,i%10*16+8,i//10*16+8)
 sheet.save(OUT/'sprites_native.png');sheet.resize((960,192),Image.Resampling.NEAREST).save(OUT/'sprites_6x.png');overview.save(OUT/'region_native.png');cameras.save(OUT/'camera_native.png')
 (OUT/'layout.json').write_text(json.dumps({'schema':1,'rooms':rooms,'sprites':NAMES,'maximum_visible_runtime_actors':20,'art_bytes':budget,'authorship':'Original code-native pixels. No imported, Nintendo, traced or recycled map raster.'},separators=(',',':'))+'\n')
 (OUT/'validation.json').write_text(json.dumps({'kind':'Host authored-geometry certificate; native controller acceptance separate','rooms':proof,'rom_art_bytes':budget},indent=1)+'\n')
 (OUT/'CREDITS.txt').write_text('Original Return I pixel scenery and actor sprites generated from editable Python primitives. Shared native RGB555 palette retained. No external game imagery, raster tracing or copied map layouts.\n')
 print('Return art:',budget,'bytes;',len(parts),'chunks;',len(rooms),'certified rooms')
if __name__=='__main__':main()
