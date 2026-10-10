#!/usr/bin/env python3
"""Original native-pixel Nacreway and Palinode Archive scenery.

Every pixel is code-authored in the existing RGB555 palette. No imported,
traced, AI raster or third-party art is used. Backgrounds, exact half-open
collision rectangles and five-pixel-foot lookup tables have one source.
All dynamic glyphs stream through the existing twenty regional OBJ slots.
"""
from pathlib import Path
from collections import deque
import hashlib, json, math, random, sys
from PIL import Image, ImageDraw
import connected_road_art as roads
sys.dont_write_bytecode = True
from generate_assets import Art, P, PAL, COLORS
from generate_region import odd_bitmap, cbytes, verify_room, paste_sprite
from generate_northern_region import collision_bands
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/underwater_region'; SRC=ROOT/'src'
KEYS=['nacreway','siltglass_commons','kelp_promenade','hollow_oyster_garden','palinode_vestibule','countercurrent_stacks','listening_chamber','vestige_court']
TITLES=['Nacreway','Siltglass Commons','Kelp Promenade','Hollow Oyster Garden','Palinode Vestibule','Countercurrent Stacks','Listening Chamber','Vestige Court']
NAMES=['KEEPER','SHELLWRIGHT','COOK','FRAMER','DANCER','KEEPER_WORK','WORKER_WORK','REST','REST_LIT','RESET','TRIAL','NOTICE','LEAF','SHELF','BAFFLE','GATE','DONE','GUARDIAN','GUARDIAN_WARN','GUARDIAN_OPEN']
NPCS=set(NAMES[:5])
ROOMS=[]
# Distinct materials, all mapped into the immutable pre-existing palette.
C={'deep':'water0','shadow':'shadow','ink':'ink','jade_dark':'pine1','jade':'water2','jade_lit':'water3','jade_glow':'water4','pearl':'bg_temple_stone5','pearl_mid':'bg_temple_stone4','pearl_shade':'bg_temple_stone3','sand':'bg_sunlit_dirt4','sand_shade':'bg_sunlit_dirt3','brass':'gold1','brass_lit':'gold3','brass_dark':'gold0','coral':'rose4','coral_shade':'rose3','coral_lit':'rose5','kelp':'bg_sunlit_pine3','kelp_dark':'bg_sunlit_pine1','kelp_lit':'bg_sunlit_pine5'}
def c(k):return C.get(k,k)
def rect(a,b,k):a.r(b,c(k))
def line(a,p,k,w=1):a.l([(int(x),int(y))for x,y in p],c(k),w)
def ell(a,b,k):a.e(b,c(k))
def poly(a,p,k):a.p([(int(x),int(y))for x,y in p],c(k))
def dot(a,x,y,k):a.dot(x,y,c(k))
def solid(r,kind,b):r['solids'].append({'kind':kind,'rect':list(b)})
def obj(r,key,kind,x,y,approach=None,static=False,**extra):r['objects'].append(dict(key=key,kind=kind,center=[x,y],approach=approach or [x,y+18],interaction_radius=23,static_baked=static,**extra))
def exit_(r,key,x,y,target,spawn=0):r['exits'].append({'key':key,'approach':[x,y],'target':target,'target_spawn':spawn})
def route(a,points,w=32,brass=False):
 line(a,points,'jade',w+8);line(a,points,'pearl_shade',w+4);line(a,points,'sand',w)
 if brass:
  for (x,y),(xx,yy) in zip(points,points[1:]):
   if x==xx:
    for sy in range(min(y,yy)+6,max(y,yy),18):line(a,[(x-w//2+3,sy),(x-w//2+6,sy)],'brass')
   elif y==yy:
    for sx in range(min(x,xx)+6,max(x,xx),18):line(a,[(sx,y-w//2+3),(sx,y-w//2+6)],'brass')
def paving(a,x,y,w,h,shade='sand',pattern=0):
 rect(a,(x,y,x+w-1,y+h-1),shade)
 # Sparse broken joints are subordinate to outlines and actors.
 for yy in range(y+14,y+h,22):
  for xx in range(x-16+(12 if (yy//22)&1 else 0),x+w,42):
   lo=max(x+2,xx);hi=min(x+w-3,xx+29)
   if lo<hi:line(a,[(lo,yy),(hi,yy)],'sand_shade' if shade=='sand' else 'pearl_shade');line(a,[(lo+3,yy-1),(min(lo+11,hi),yy-1)],shade)
   if x+2<xx<x+w-2:line(a,[(xx,yy+2),(xx,min(y+h-2,yy+7))],'sand_shade'if shade=='sand'else'pearl_shade')
def seabed(a,w,h,seed,base='jade_lit'):
 rect(a,(0,0,w-1,h-1),base);R=random.Random(seed)
 for i in range(w*h//900):
  x=R.randrange(7,w-8);y=R.randrange(9,h-6)
  line(a,[(x-4,y),(x,y-1),(x+7,y-1)],'jade_glow'if i%3 else'jade',1)
 for i in range(w*h//2200):
  x=R.randrange(8,w-8);y=R.randrange(8,h-8);dot(a,x,y,'watergleam');dot(a,x+1,y,'water4')
def pool(a,r,x,y,w,h,kind='teaching_pool',blocking=True):
 ell(a,(x+2,y+4,x+w+3,y+h+5),'deep');ell(a,(x,y,x+w,y+h),'brass_dark');ell(a,(x+2,y,x+w-2,y+h-3),'pearl');ell(a,(x+5,y+3,x+w-5,y+h-6),'jade');ell(a,(x+9,y+5,x+w-9,y+h-10),'jade_lit')
 line(a,[(x+w//4,y+7),(x+w//2,y+5),(x+w*3//4,y+7)],'jade_glow');line(a,[(x+11,y+h-12),(x+20,y+h-10)],'watergleam')
 for dx,dy in[(13,12),(w-18,17),(w//2,h-13)]:ell(a,(x+dx-2,y+dy-1,x+dx+3,y+dy+1),'pearl_shade')
 if blocking:solid(r,kind,(x+4,y+4,w-7,h-7))
def coral(a,x,y,s=1,color='coral'):
 # Fan branches, rounded distinct tips and a grounded root silhouette.
 line(a,[(x,y),(x,y-22*s)],'coral_shade',max(2,int(4*s)))
 for dx,dy in[(-14,-17),(-10,-28),(11,-24),(17,-13)]:
  line(a,[(x,y-7*s),(x+dx*s,y+dy*s)],color,max(2,int(3*s)));line(a,[(x+dx*s,y+dy*s),(x+dx*s,y+(dy-6)*s)],color,max(2,int(3*s)));ell(a,(x+(dx-2)*s,y+(dy-8)*s,x+(dx+2)*s,y+(dy-4)*s),'coral_lit')
 line(a,[(x,y-5*s),(x+1,y-24*s)],'coral_lit');ell(a,(x-6*s,y-2*s,x+7*s,y+3*s),'pearl_shade')
def kelp(a,x,y,height=40,lean=1,seed=0):
 for i in range(3):
  root=x+(i-1)*5;top=y-height+(i%2)*6;pts=[(root,y),(root+lean*5,y-height//3),(root-lean*4,y-2*height//3),(root+lean*5,top)]
  line(a,pts,'kelp_dark',3);line(a,[(px+1,py)for px,py in pts],'kelp',1)
  for j in range(3):
   yy=y-9-j*(height-9)//3;xx=root+(4 if j%2==0 else-3)*lean;d=(1 if(j+i)%2 else-1)
   poly(a,[(xx,yy+4),(xx+d*10,yy-2),(xx+d*12,yy-9),(xx+d*4,yy-5)],'kelp');line(a,[(xx,yy+2),(xx+d*8,yy-5)],'kelp_lit')
def planter(a,r,x,y,w,h,flora='kelp'):
 rect(a,(x+2,y+3,x+w+2,y+h+3),'deep');rect(a,(x,y,x+w,y+h),'brass_dark');rect(a,(x+2,y+1,x+w-2,y+h-2),'pearl_mid');rect(a,(x+4,y+3,x+w-4,y+h-5),'jade_dark');line(a,[(x+3,y+1),(x+w-3,y+1)],'pearl')
 for xx in range(x+12,x+w-5,20):
  if flora=='coral':coral(a,xx,y+h-6,.65)
  else:kelp(a,xx,y+h-6,max(18,h+5),1 if xx%3 else-1)
 solid(r,'living_'+flora+'_planter',(x,y,w+1,h+1))
def shell_roof(a,x,y,w,h,color='coral'):
 # Fan-vault silhouette assembled from scallops and radiating rib inlay.
 ell(a,(x+3,y+6,x+w+5,y+h+5),'deep');ell(a,(x,y,x+w,y+h),'coral_shade'if color=='coral'else'jade');ell(a,(x+2,y,x+w-2,y+h-4),color)
 for k in range(1,8):
  ang=math.pi+(math.pi*k/8);ex=x+w/2+math.cos(ang)*(w/2-3);ey=y+h*.70+math.sin(ang)*(h*.68)
  line(a,[(x+w/2,y+h-4),(ex,ey)],'coral_lit'if color=='coral'else'jade_glow',2)
 for j in range(7):
  xx=x+5+j*(w-10)//6;ell(a,(xx-4,y+h-9,xx+4,y+h-2),'coral_lit'if color=='coral'else'jade_glow')
 line(a,[(x+5,y+h-3),(x+w-5,y+h-3)],'brass_dark',2)
def house(a,r,x,y,w,h,door,color='coral',label='shell_vault'):
 rect(a,(x+7,y+18,x+w+7,y+h+6),'deep');rect(a,(x,y+18,x+w,y+h),'brass_dark');rect(a,(x+2,y+19,x+w-2,y+h-1),'pearl_mid');rect(a,(x+5,y+22,x+w-5,y+h-3),'pearl')
 shell_roof(a,x-5,y-12,w+10,max(31,h//2),color)
 for xx in range(x+12,x+w-12,26):
  if abs(xx+5-door)<18:continue
  ell(a,(xx,y+h-27,xx+11,y+h-13),'brass');ell(a,(xx+2,y+h-25,xx+9,y+h-14),'deep');line(a,[(xx+4,y+h-24),(xx+4,y+h-16)],'jade_lit');line(a,[(xx+1,y+h-19),(xx+10,y+h-19)],'brass_lit')
 ell(a,(door-11,y+h-25,door+11,y+h-3),'brass');rect(a,(door-11,y+h-13,door+11,y+h),'brass');ell(a,(door-8,y+h-22,door+8,y+h-4),'deep');rect(a,(door-8,y+h-13,door+8,y+h),'deep');line(a,[(door-7,y+h-13),(door-7,y+h-2)],'jade_lit');rect(a,(door-13,y+h,door+13,y+h+3),'pearl_shade')
 # Exteriors have inhabited detail: tied kelp awnings and ceramic bottles.
 line(a,[(x+4,y+h-7),(x+4,y+h+2)],'brass');ell(a,(x+4,y+h-5,x+10,y+h+2),'coral');line(a,[(x+w-8,y+h-2),(x+w-8,y+h-10)],'brass');dot(a,x+w-7,y+h-11,'brass_lit')
 solid(r,label,(x-4,y-12,w+9,h+13))
def bench(a,r,x,y,w=36,blocking=True):
 rect(a,(x+3,y+7,x+w+3,y+12),'deep');rect(a,(x+3,y+3,x+6,y+11),'brass_dark');rect(a,(x+w-6,y+3,x+w-3,y+11),'brass_dark');rect(a,(x,y,x+w,y+5),'brass');rect(a,(x+1,y-2,x+w-1,y+2),'pearl');line(a,[(x+5,y),(x+w-5,y)],'pearl_shade')
 if blocking:solid(r,'listening_bench',(x,y-2,w+1,11))
def shelf(a,r,x,y,w,h=24,orient=0,blocking=True):
 rect(a,(x+4,y+4,x+w+3,y+h+4),'deep');rect(a,(x,y,x+w-1,y+h-1),'brass_dark');rect(a,(x+2,y+1,x+w-3,y+h-3),'pearl_mid')
 for yy in range(y+5,y+h-3,10):
  rect(a,(x+4,yy,x+w-5,yy+5),'jade_dark');line(a,[(x+4,yy+6),(x+w-5,yy+6)],'brass')
  for xx in range(x+8,x+w-5,11):rect(a,(xx,yy-2,xx+5,yy+4),'pearl');line(a,[(xx+1,yy-1),(xx+3,yy+2)],'coral'if(xx//11)%2 else'jade_lit')
 line(a,[(x+2,y+1),(x+w-3,y+1)],'brass_lit')
 if blocking:solid(r,'archive_shell_shelf',(x,y,w,h))
def mural(a,x,y,w,h,version=0):
 rect(a,(x+2,y+2,x+w+2,y+h+2),'deep');rect(a,(x,y,x+w,y+h),'brass');rect(a,(x+2,y+2,x+w-2,y+h-2),'pearl');line(a,[(x+5,y+h-6),(x+w-5,y+h-6)],'jade')
 for k in range(3):
  xx=x+8+k*(w-15)//3;yy=y+h//2+(2 if k&1 else-1);ell(a,(xx-2,yy-7,xx+2,yy-3),'coral');line(a,[(xx,yy-2),(xx,yy+4)],'jade',2);line(a,[(xx,yy),(xx-4,yy+2),(xx-6,yy)],'jade');line(a,[(xx,yy+4),(xx+4,yy+7)],'brass_dark')
 line(a,[(x+6,y+5),(x+w//2,y+8+version*2),(x+w-6,y+4)],'jade_lit')
def etched_ring(a,x,y,rx,ry,dotted=False,tone='brass'):
 # Quiet outlined floor information, never filled combat telegraphs.
 for k in range(40):
  if dotted and k%2:continue
  t=k*math.tau/40;tt=(k+.65)*math.tau/40
  line(a,[(x+math.cos(t)*rx,y+math.sin(t)*ry),(x+math.cos(tt)*rx,y+math.sin(tt)*ry)],tone)
def lamp(a,x,y):
 line(a,[(x,y),(x,y-13)],'brass_dark',2);ell(a,(x-4,y-20,x+4,y-12),'brass');ell(a,(x-2,y-18,x+2,y-13),'gold4');dot(a,x-1,y-17,'white');ell(a,(x-5,y-1,x+5,y+2),'pearl_shade')
def motif(a,x,y,kind=0,tone='jade'):
 if kind==0:
  for dx in(-5,0,5):line(a,[(x+dx,y+4),(x+dx-2,y-3),(x,y-6)],tone)
 elif kind==1:
  line(a,[(x-7,y+2),(x-3,y-3),(x+1,y+1),(x+6,y-5)],tone,2);dot(a,x+7,y+4,tone)
 else:
  for dx,dy in[(-5,-2),(1,2),(6,-2)]:ell(a,(x+dx-1,y+dy-2,x+dx+1,y+dy+2),tone)

SPAWNS=[{'0':[240,288],'1':[240,32],'2':[80,272],'3':[448,160]},
 {'0':[240,288],'1':[400,48],'2':[64,272]},
 {'0':[240,288],'1':[240,32],'2':[448,160]}, {'0':[120,140],'1':[208,112]},
 {'0':[120,140],'1':[208,112]}, {'0':[240,288],'1':[432,112],'2':[32,160]},
 {'0':[120,140],'1':[208,112],'2':[32,112]}, {'0':[120,140],'1':[208,112]}]
# Target spawn is part of the route contract; doorway geometry stays exact.
DOORS=[ [('south',240,304,38,4),('east',464,160,47,0),('north',240,16,48,0)],
 [('south',240,304,46,3),('north',400,16,50,0)],
 [('south',240,304,46,1),('north',240,16,49,0),('east',464,160,51,2)],
 [('south',120,146,48,1),('east',224,112,52,2)],
 [('south',120,146,47,1),('east',224,112,51,0)],
 [('south',240,304,50,1),('east',464,112,52,0),('west',16,160,48,2)],
 [('south',120,146,51,1),('east',224,112,53,0),('west',16,112,49,1)],
 [('south',120,146,52,1),('east',224,112,46,1)]]
def boundary(a,r):
 w,h=r['width'],r['height'];doors=[]
 # Exterior mouths share the runtime adjacency source; only the shell lift stays transport.
 for road in roads.DATA['roads']:
  for e,other in [road['ends'],list(reversed(road['ends']))]:
   if e['room']!=r['id']:continue
   side={'N':'north','S':'south','W':'west','E':'east'}[e['edge']]
   x,y={'N':(e['center'],16),'S':(e['center'],h-16),'W':(16,e['center']),'E':(w-16,e['center'])}[e['edge']]
   doors.append((side,x,y,other['room'],other['saved_spawn']))
 if r['id']==46:doors.append(('south',240,304,38,4))
 gaps={'north':[],'south':[],'east':[],'west':[]}
 for side,x,y,target,spawn in doors:gaps[side].append((x if side in('north','south')else y)-24)
 for side in gaps:
  length=w if side in('north','south')else h;pieces=[(0,length)]
  for lo in gaps[side]:
   parts=[]
   for start,end in pieces:
    if start<lo:parts.append((start,min(end,lo)))
    if end>lo+48:parts.append((max(start,lo+48),end))
   pieces=parts
  for start,end in pieces:
   if end<=start:continue
   b=(start,0,end-start,8)if side=='north'else(start,h-8,end-start,8)if side=='south'else(0,start,8,end-start)if side=='west'else(w-8,start,8,end-start)
   x,y,bw,bh=b;rect(a,(x,y,x+bw-1,y+bh-1),'deep');rect(a,(x+1,y+1,x+bw-2,y+bh-2),'jade');solid(r,side+'_boundary',b)
 for side,x,y,target,spawn in doors:
  if side in('south','north'):
   yy=h-26 if side=='south'else 0;rect(a,(x-18,yy,x+18,yy+26),'pearl_mid')
   for dy in(3,9,15,21):line(a,[(x-16,yy+dy),(x+16,yy+dy)],'pearl_shade');line(a,[(x-16,yy+dy-1),(x+16,yy+dy-1)],'pearl')
   for xx in(x-22,x+22):rect(a,(xx-2,yy,xx+2,yy+25),'brass');line(a,[(xx-1,yy),(xx-1,yy+25)],'brass_lit')
  else:
   xx=w-28 if side=='east'else 0;rect(a,(xx,y-18,xx+28,y+18),'pearl_mid')
   for dx in(3,9,15,21):line(a,[(xx+dx,y-16),(xx+dx,y+16)],'pearl_shade');line(a,[(xx+dx-1,y-16),(xx+dx-1,y+16)],'pearl')
   for yy in(y-22,y+22):rect(a,(xx,yy-2,xx+27,yy+2),'brass');line(a,[(xx,yy-1),(xx+27,yy-1)],'brass_lit')
  exit_(r,side,x,y,target,spawn)
def make(i):
 w,h=(480,320)if i in(0,1,2,5)else(240,160)
 r={'id':46+i,'key':KEYS[i],'name':TITLES[i],'width':w,'height':h,'spawns':SPAWNS[i],'solids':[],'objects':[],'exits':[],'dynamic_rectangles':[],'enemy_spawns':[],'reserved_runtime_targets':[]}
 a=Art(w,h,'water3');seabed(a,w,h,446+i)
 if w==480:paving(a,25,25,w-50,h-50,'sand'if i==0 else'pearl_mid')
 else:paving(a,8,22,224,134,'pearl_mid'if i in(3,6)else'sand')
 ROOMS.append(r);return r,a

def public_markers(a,r):
 big=r['width']==480
 for key,kind,x,y in [('reset','RESET',40 if big else 24,276 if big else 132),('trial_left','TRIAL',80 if big else 48,240 if big else 112),('trial_right','TRIAL',400 if big else 192,240 if big else 112)]:
  obj(r,key,kind,x,y,[x+18,y]if key=='reset'else[x,y+16]);ell(a,(x-12,y-6,x+12,y+8),'pearl_shade');line(a,[(x-9,y+8),(x+9,y+8)],'brass');motif(a,x,y+1,0,'pearl')

def town():
 r,a=make(0)
 # Three shell vaults have their own material, doorway and recognizable purpose.
 route(a,[(240,0),(240,154),(240,320)],38,True);route(a,[(34,154),(480,154)],36,True)
 house(a,r,42,24,140,42,112,'coral','market_shell_vault')
 house(a,r,288,23,145,43,352,'jade_lit','sanctuary_shell_vault')
 # Paired teaching basins are inset transparent floors, so no hidden colliders.
 pool(a,r,75,83,89,46,'echo_teaching_pool',False);pool(a,r,300,83,88,46,'buoyancy_teaching_pool',False)
 for x in(106,120,134):motif(a,x,107,0 if x!=120 else 1,'pearl')
 # The lesson diorama is visibly diagrammatic with outlined, unequal shelves.
 rect(a,(319,99,337,107),'pearl');rect(a,(345,108,371,114),'pearl');line(a,[(328,96),(328,92),(358,92),(358,105)],'brass',2)
 for x,y in[(70,137),(182,137),(295,137),(404,137),(210,267),(270,267)]:lamp(a,x,y)
 # Real inhabited market counters, family-size weaving mats, bowls and frames.
 shelf(a,r,96,168,54,24);shelf(a,r,324,184,62,24)
 for x,y in[(106,164),(123,164),(137,164),(336,180),(352,180),(370,180)]:ell(a,(x-3,y-4,x+4,y+3),'coral');line(a,[(x-2,y-3),(x+3,y-3)],'coral_lit')
 for x,y in[(84,205),(284,202)]:
  poly(a,[(x,y),(x+72,y),(x+80,y+41),(x-5,y+41)],'jade');poly(a,[(x+2,y+2),(x+70,y+2),(x+76,y+38),(x-1,y+38)],'pearl')
  for yy in range(y+5,y+38,6):line(a,[(x+3,yy),(x+71,yy)],'sand_shade')
  for xx in(x+5,x+12,x+61,x+68):line(a,[(xx,y+3),(xx+2,y+36)],'coral')
 mural(a,168,32,39,31,0);mural(a,260,32,20,31,1)
 # Side coves remain outside the primary promenade and have readable low edges.
 planter(a,r,32,78,21,52);planter(a,r,424,216,20,48,'coral')
 bench(a,r,44,184,34);bench(a,r,408,88,29)
 for x,y in[(47,257),(440,284),(35,302),(445,57)]:coral(a,x,y,.65)
 etched_ring(a,240,222,32,18,True,'pearl_shade');motif(a,240,222,1,'brass')
 for key,k,x,y in [('keeper','KEEPER',120,72),('shellwright','SHELLWRIGHT',340,72),('cook','COOK',160,176),('framer','FRAMER',304,176),('dancer','DANCER',240,240),('rest','REST',80,256),('sanctuary','REST_LIT',320,144),('solid_plaque','LEAF',96,104),('hollow_plaque','LEAF',144,104),('ballast_lesson','SHELF',340,108),('procession_wall','NOTICE',240,104)]:obj(r,key,k,x,y)
 public_markers(a,r);boundary(a,r);return r,a

def commons():
 r,a=make(1)
 # Lagoon fork and a permanent two-sided causeway, distinct from town streets.
 route(a,[(240,320),(240,258),(210,220),(210,156),(280,112),(400,48),(400,0)],36)
 route(a,[(210,218),(111,246),(72,224),(72,147),(178,118),(210,156)],32)
 route(a,[(280,112),(349,148),(408,212),(355,270),(240,258)],32)
 # Raised reef beds clearly own their colliders; everyone can walk around them.
 planter(a,r,96,72,62,36,'coral');planter(a,r,320,208,72,32)
 # Low cut-shell causeway has two stable walkable landings and quiet markings.
 for x,y in[(188,144),(216,150),(244,156),(272,150)]:
  ell(a,(x-13,y-8,x+13,y+8),'jade');ell(a,(x-12,y-9,x+12,y+5),'pearl');line(a,[(x-7,y),(x+7,y)],'pearl_shade')
 line(a,[(176,170),(288,170)],'brass',2)
 for x in range(180,289,18):line(a,[(x,170),(x+6,170)],'brass_lit')
 house(a,r,274,27,78,30,314,'jade_lit','echo_practice_pavilion')
 shell_roof(a,28,16,82,39,'coral');solid(r,'low_reef_cove',(31,20,74,31))
 mural(a,165,29,76,29,1)
 # Warm ordinary-combat meadow has quiet texture and sparse fallen chart marks.
 ell(a,(264,68,294,80),'jade_lit');line(a,[(270,74),(279,69),(286,74)],'pearl')
 for x,y in[(55,65),(448,74),(432,278),(130,276),(282,286),(32,205)]:kelp(a,x,y,25)
 for x,y in[(53,120),(433,130),(44,283),(444,47)]:coral(a,x,y,.75)
 bench(a,r,32,120,23);bench(a,r,413,252,31)
 for x,y in[(64,244),(280,96),(426,173)]:lamp(a,x,y)
 motif(a,184,204,1,'brass');motif(a,300,244,0,'brass')
 for key,k,x,y in [('return_loop','NOTICE',240,164),('echo_practice','LEAF',288,96),('fallen_chart','NOTICE',136,232),('rest','REST',64,256),('ballast','SHELF',272,176)]:obj(r,key,k,x,y)
 r['enemy_spawns']=[[320,80],[392,160],[184,264],[296,248]]
 public_markers(a,r);boundary(a,r);return r,a

def promenade():
 r,a=make(2)
 # Living green corridors use curved screens and open crossings, not stone plazas.
 route(a,[(240,320),(240,253),(288,209),(240,154),(240,0)],34)
 route(a,[(240,252),(105,264),(64,221),(72,145),(184,144),(240,154),(352,160),(480,160)],34)
 route(a,[(184,144),(181,74),(240,43),(301,71),(294,118),(352,160),(400,250),(288,209)],31)
 planter(a,r,64,64,48,32);planter(a,r,400,64,32,48);planter(a,r,40,168,48,32)
 # The shoal migration ribbon remains fully walkable and visibly continues.
 line(a,[(40,181),(117,184),(161,161),(231,181),(302,182),(373,207),(446,200)],'jade_lit',13)
 line(a,[(40,182),(117,185),(161,162),(231,182),(302,183),(373,208),(446,201)],'jade_glow',2)
 for x,y in[(96,183),(152,166),(208,176),(275,183),(340,198),(404,205)]:
  poly(a,[(x-4,y),(x+2,y-2),(x+5,y),(x+2,y+2)],'jade');poly(a,[(x-5,y),(x-8,y-2),(x-8,y+2)],'jade');dot(a,x+3,y,'deep')
 # Woven frond awnings crown the corridor with knotted warm brass supports.
 for x,y,w in[(45,22,125),(284,19,129)]:
  poly(a,[(x,y+12),(x+12,y),(x+w-10,y+3),(x+w,y+28),(x+3,y+30)],'kelp_dark')
  for xx in range(x+10,x+w-5,9):line(a,[(xx,y+7),(xx+6,y+26)],'kelp',4);line(a,[(xx+1,y+8),(xx+6,y+24)],'kelp_lit')
  line(a,[(x+3,y+30),(x+w-1,y+28)],'brass',2);solid(r,'woven_frond_awning',(x,y,w,32))
 for x,y in[(40,119),(425,99),(49,282),(433,284),(401,54),(50,59)]:kelp(a,x,y,45,-1 if x%2 else 1)
 for x,y in[(423,141),(55,255),(157,267)]:coral(a,x,y,.7)
 bench(a,r,32,226,27);bench(a,r,404,219,36)
 mural(a,271,35,31,22,1)
 for key,k,x,y in [('shoal_window','LEAF',112,184),('far_screen','BAFFLE',384,184),('observation','NOTICE',416,248),('quiet_seat','NOTICE',72,208),('weaver','FRAMER',160,160),('garden_hint','NOTICE',240,56)]:obj(r,key,k,x,y)
 r['enemy_spawns']=[[296,264],[144,64],[392,144]]
 public_markers(a,r);boundary(a,r);return r,a

def top_arch(a,r,color='coral',double=False):
 # Upright masonry lives in the top strip; broad readable floor stays open.
 for x,w in[(23,78),(140,78)]if double else[(28,184)]:
  if r['id']==50:
   rect(a,(x,0,x+w,25),'brass_dark');rect(a,(x+2,0,x+w-2,23),'jade')
   for xx in range(x+7,x+w-6,15):
    rect(a,(xx,4,xx+8,19),'pearl');ell(a,(xx-1,2,xx+9,7),'pearl_mid');line(a,[(xx+3,8),(xx+5,16)],'coral');line(a,[(xx-1,21),(xx+9,21)],'brass_lit')
  elif r['id']==52:
   rect(a,(x,0,x+w,24),'deep');rect(a,(x+1,2,x+w-1,22),'jade')
   for j,xx in enumerate(range(x+5,x+w-4,11)):
    hh=12+(j%3)*4;rect(a,(xx,22-hh,xx+5,22),'pearl_mid');ell(a,(xx-2,18-hh,xx+7,24-hh),'pearl');ell(a,(xx,19-hh,xx+5,22-hh),'deep');line(a,[(xx+1,24-hh),(xx+1,20)],'brass_lit')
  elif r['id']==53:
   rect(a,(x,0,x+w,24),'jade');rect(a,(x+2,2,x+w-2,22),'pearl_shade')
   for xx in range(x+5,x+w-3,18):
    poly(a,[(xx,2),(xx+9,0),(xx+12,7),(xx+8,14),(xx+10,22),(xx+2,22),(xx+3,13),(xx,8)],'pearl');line(a,[(xx+3,7),(xx+8,7)],'brass')
  else:shell_roof(a,x,0,w,26,color)
  solid(r,'upper_shell_vault',(x,0,w+1,25))
 for x in(12,221):
  rect(a,(x,8,x+6,36),'brass_dark');rect(a,(x+1,8,x+5,34),'pearl');line(a,[(x+2,9),(x+2,32)],'brass_lit')
 # Mural fragments look like actual architecture, not UI over the playfield.

def garden():
 r,a=make(3);top_arch(a,r,'coral',True)
 # Hollow shells, branching low water ribbons, and a transparent nursery.
 route(a,[(120,160),(120,118),(96,89),(120,55),(178,67),(224,112)],29)
 pool(a,r,29,40,53,35,'nursery_floor',False);pool(a,r,151,40,55,35,'hollow_shell_floor',False)
 for x,y in[(44,54),(58,60),(70,51)]:
  ell(a,(x-3,y-4,x+3,y+3),'pearl');line(a,[(x-3,y+2),(x-1,y+5),(x+1,y+2),(x+3,y+5)],'jade_glow');dot(a,x,y-2,'coral')
 for x,y in[(161,56),(177,60),(193,54)]:motif(a,x,y,0,'pearl')
 # Two outlined acoustic shadows differ by shape, not merely color.
 poly(a,[(34,89),(64,86),(82,103),(61,110),(35,101)],'pearl_shade');poly(a,[(152,88),(174,82),(202,93),(192,104),(165,103)],'jade_glow')
 for pts in[[(42,98),(52,92),(63,97),(73,102)],[(159,96),(172,91),(187,94)]]:line(a,pts,'jade',1)
 mural(a,96,6,41,17,1)
 for x,y in[(20,82),(220,81),(19,141),(223,38)]:kelp(a,x,y,20)
 for x,y in[(31,36),(215,36)]:coral(a,x,y,.45)
 etched_ring(a,120,93,20,11,True,'brass')
 for key,k,x,y in [('etching','NOTICE',176,64),('nursery','LEAF',48,56),('quiet_bench','NOTICE',80,96),('warm_nook','SHELF',160,96)]:obj(r,key,k,x,y,[x,y+16])
 public_markers(a,r);boundary(a,r);return r,a

def vestibule():
 r,a=make(4);top_arch(a,r,'jade_lit')
 # Overlapping positive/negative leaves are floor projection motifs, never walls.
 poly(a,[(47,41),(114,36),(140,99),(65,112)],'pearl_mid');poly(a,[(110,41),(185,44),(179,112),(102,102)],'pearl')
 line(a,[(48,43),(114,38),(138,99),(66,110),(48,43)],'brass')
 line(a,[(111,43),(183,46),(177,110),(104,100),(111,43)],'jade')
 line(a,[(62,53),(82,58),(91,49),(111,68),(103,80),(119,92)],'jade_lit',2)
 for x,y in[(122,53),(127,59),(131,65),(130,73),(136,79),(132,87),(140,96)]:line(a,[(x,y),(x+2,y+2)],'jade')
 for x,y in[(88,72),(152,72),(120,104)]:etched_ring(a,x,y,12,9,True,'brass')
 # Paired top archive drawers, empty bindings and a lost shoreline frieze.
 mural(a,57,5,124,15,0)
 for x in(18,212):lamp(a,x,55)
 for x,y in[(38,124),(204,45)]:motif(a,x,y,1,'pearl_shade')
 for key,k,x,y in [('echo_leaf','LEAF',88,72),('ballast_leaf','SHELF',152,72),('rotate_leaf','NOTICE',120,104)]:obj(r,key,k,x,y,[x,y+16])
 public_markers(a,r);boundary(a,r);return r,a

def stacks():
 r,a=make(5)
 # An inhabited archive library rather than another broad symmetric room.
 route(a,[(240,320),(240,230),(280,199),(280,130),(320,96),(400,96),(480,112)],34)
 route(a,[(0,160),(62,160),(66,230),(152,254),(240,230)],32)
 route(a,[(62,160),(62,76),(176,56),(240,80),(280,130)],32)
 route(a,[(280,199),(414,218),(418,158),(400,96)],32)
 shelf(a,r,96,96,44,96);shelf(a,r,344,176,44,56)
 shelf(a,r,48,26,132,29);shelf(a,r,288,24,135,30)
 # Split-level shelf platforms are flat inlay. The actual moving shelf is OBJ.
 rect(a,(150,124,199,161),'jade');rect(a,(152,126,197,159),'pearl_shade');rect(a,(154,128,195,157),'pearl')
 for y in range(128,158,6):line(a,[(156,y),(193,y)],'sand_shade')
 rect(a,(292,122,315,163),'jade');rect(a,(294,124,313,161),'pearl_shade')
 for y in range(129,160,7):line(a,[(296,y),(311,y)],'pearl')
 line(a,[(176,123),(176,110),(304,110),(304,123)],'brass',2)
 for x in(176,240,304):ell(a,(x-3,107,x+3,113),'brass_lit');dot(a,x,110,'deep')
 # Refuge carpeting, lifted floor rails and an observed procession fragment.
 poly(a,[(318,249),(420,249),(432,280),(312,280)],'jade');poly(a,[(321,252),(417,252),(427,277),(317,277)],'pearl')
 for y in(255,261,267,273):line(a,[(323,y),(418,y)],'sand_shade')
 mural(a,212,28,57,30,1);mural(a,423,29,22,27,0)
 bench(a,r,417,248,26);bench(a,r,42,255,27)
 for x,y in[(70,67),(422,77),(290,266),(64,218)]:lamp(a,x,y)
 for x,y in[(448,49),(33,112),(441,281)]:kelp(a,x,y,27)
 for key,k,x,y in [('wide_shelf','SHELF',176,144),('narrow_shelf','SHELF',304,144),('procession_sketch','LEAF',240,80),('far_reset','RESET',424,76),('quiet_refuge','REST',368,264)]:obj(r,key,k,x,y,[x,y+16])
 r['enemy_spawns']=[[192,208],[392,144],[296,72]]
 public_markers(a,r);boundary(a,r);return r,a

def listening():
 r,a=make(6);top_arch(a,r,'jade_lit',True)
 # Concentric sound paths visibly terminate in an intentional quiet wedge.
 for rx,ry in[(90,47),(74,39),(57,30)]:
  for k in range(38):
   t=k*math.tau/40
   if 1.05<t<2.13:continue
   tt=(k+.7)*math.tau/40;line(a,[(120+math.cos(t)*rx,77+math.sin(t)*ry),(120+math.cos(tt)*rx,77+math.sin(tt)*ry)],'jade_glow'if rx==74 else'pearl_shade')
 poly(a,[(120,82),(93,117),(147,117)],'pearl')
 for x,y in[(113,98),(122,103),(115,109),(124,113)]:ell(a,(x-1,y-2,x+1,y+2),'brass')
 etched_ring(a,80,72,15,12,True,'brass');etched_ring(a,160,72,15,12,True,'brass')
 line(a,[(76,52),(67,65),(69,80),(79,89)],'jade',2);line(a,[(164,52),(173,65),(171,80),(161,89)],'jade',2)
 mural(a,96,5,42,18,1)
 for x,y in[(26,53),(212,53)]:lamp(a,x,y)
 for x,y in[(14,102),(225,102)]:kelp(a,x,y,18)
 for key,k,x,y in [('left_baffle','BAFFLE',80,72),('right_baffle','BAFFLE',160,72),('echo_outline','LEAF',120,48),('quiet_motif','NOTICE',120,112)]:obj(r,key,k,x,y,[x,y+16])
 public_markers(a,r);boundary(a,r);return r,a

def court():
 r,a=make(7);top_arch(a,r,'coral')
 # Broken procession relief crowns the chamber. Lower field stays telegraph-clean.
 mural(a,36,5,68,18,0);mural(a,143,5,60,18,1)
 poly(a,[(105,5),(122,2),(137,11),(129,26),(110,23)],'brass');poly(a,[(109,7),(121,5),(133,12),(127,22),(113,20)],'pearl')
 line(a,[(120,6),(116,12),(123,15),(118,21)],'jade')
 # Different asymmetric side alcoves, flat white shell landings, safe outer ring.
 poly(a,[(35,55),(75,49),(89,85),(73,105),(35,103)],'jade_lit');poly(a,[(37,58),(73,53),(85,84),(71,101),(37,100)],'pearl')
 poly(a,[(149,55),(184,51),(202,61),(199,100),(151,102)],'jade_lit');poly(a,[(153,59),(183,55),(198,64),(195,96),(155,98)],'pearl')
 for x,y in[(64,80),(176,80)]:etched_ring(a,x,y,13,11,True,'brass')
 # No filled radial markings behind the guardian: only one calm stone dais.
 ell(a,(100,34,140,64),'pearl_shade');ell(a,(104,35,136,59),'pearl');motif(a,120,47,0,'brass')
 for x,y in[(31,48),(207,47)]:lamp(a,x,y)
 for x,y in[(21,139),(219,139)]:coral(a,x,y,.4)
 for key,k,x,y in [('guardian','GUARDIAN',120,48),('ballast_alcove','SHELF',64,80),('memory_leaf','LEAF',176,80)]:obj(r,key,k,x,y,[x,y+16])
 public_markers(a,r);boundary(a,r);return r,a

def sprite(n):
 a=Art(16,16,'transparent')
 if n in NPCS or n in('KEEPER_WORK','WORKER_WORK'):
  base='KEEPER'if n=='KEEPER_WORK'else'SHELLWRIGHT'if n=='WORKER_WORK'else n
  coat={'KEEPER':'jade','SHELLWRIGHT':'coral','COOK':'pearl','FRAMER':'brass','DANCER':'coral_shade'}[base]
  ell(a,(2,12,13,15),'shadow');rect(a,(4,11,6,14),'deep');rect(a,(9,11,11,14),'deep')
  poly(a,[(4,7),(10,7),(13,11),(11,13),(4,13),(2,10)],coat);line(a,[(5,9),(6,12)],'pearl_mid'if base!='COOK'else'jade')
  rect(a,(5,3,10,8),'skin2');rect(a,(4,2,11,4),'wood1');dot(a,6,6,'ink');dot(a,9,6,'ink');line(a,[(7,8),(9,8)],'skin1')
  if base=='KEEPER':
   poly(a,[(3,3),(5,0),(10,0),(12,3)],'pearl');line(a,[(6,1),(8,3),(10,1)],'jade');rect(a,(10,8,14,11),'brass');rect(a,(11,8,13,10),'pearl');line(a,[(12,8),(12,10)],'jade')
  elif base=='SHELLWRIGHT':
   rect(a,(3,2,12,3),'brass_lit');rect(a,(6,8,10,12),'jade_dark');line(a,[(12,7),(13,12)],'brass');line(a,[(11,7),(14,7)],'pearl',2)
  elif base=='COOK':
   ell(a,(3,0,11,4),'pearl');ell(a,(6,0,13,4),'pearl');rect(a,(5,4,11,4),'jade');rect(a,(5,9,10,13),'coral');ell(a,(0,9,5,12),'brass_lit');dot(a,2,9,'jade')
  elif base=='FRAMER':
   line(a,[(5,1),(10,1)],'jade');rect(a,(11,7,15,12),'brass');rect(a,(12,8,14,11),'deep');line(a,[(2,7),(3,12)],'pearl_mid')
  else:
   poly(a,[(3,4),(1,1),(5,2),(7,0),(8,3)],'coral_lit');line(a,[(4,9),(1,7)],'skin2',2);line(a,[(11,8),(14,5)],'skin2',2);poly(a,[(3,11),(12,10),(14,13),(9,12),(6,14)],'jade_glow')
  if n.endswith('_WORK'):
   rect(a,(10,8,14,10),'skin2');line(a,[(10,7),(15,7)],'pearl'if base=='KEEPER'else'brass_lit');dot(a,14,6,'white')
  return a
 if n in('REST','REST_LIT'):
  ell(a,(1,10,14,15),'shadow');ell(a,(1,8,14,13),'brass');ell(a,(2,7,13,11),'pearl');ell(a,(4,7,11,10),'jade')
  for dx,dy in[(-4,-1),(0,-4),(4,-1)]:line(a,[(8,8),(8+dx,4+dy)],'jade_glow'if n=='REST'else'brass_lit',2)
  ell(a,(6,5,10,9),'pearl');dot(a,8,5,'white')
 elif n=='RESET':
  ell(a,(2,12,13,15),'shadow');rect(a,(5,10,10,14),'brass_dark');poly(a,[(1,8),(2,3),(5,1),(8,3),(11,1),(14,4),(14,8),(8,12)],'pearl')
  for x in(4,7,10):line(a,[(8,10),(x,4)],'jade_lit')
  line(a,[(5,6),(7,4),(10,5),(10,7),(7,8)],'jade');poly(a,[(6,7),(8,8),(6,9)],'jade')
 elif n in('NOTICE','TRIAL'):
  ell(a,(3,13,12,15),'shadow');rect(a,(7,8,9,14),'brass');poly(a,[(1,3),(4,1),(13,2),(15,5),(13,11),(3,11),(1,8)],'brass_dark');poly(a,[(2,3),(5,2),(12,3),(14,5),(12,10),(4,10),(2,7)],'pearl')
  if n=='TRIAL':line(a,[(5,8),(5,5),(8,3),(11,5),(11,8)],'jade');dot(a,8,7,'coral');line(a,[(7,10),(9,10)],'brass_lit')
  else:line(a,[(5,4),(11,4)],'jade');line(a,[(5,6),(10,6)],'jade');line(a,[(5,8),(8,8)],'jade')
 elif n=='LEAF':
  ell(a,(2,12,14,15),'shadow');poly(a,[(1,4),(6,2),(9,4),(14,2),(14,12),(9,14),(6,12),(1,13)],'brass_dark');poly(a,[(2,3),(6,2),(8,4),(13,2),(13,11),(9,12),(6,11),(2,12)],'pearl');line(a,[(8,4),(8,12)],'brass');line(a,[(3,6),(5,5),(6,7)],'jade');line(a,[(10,5),(11,6),(10,8),(12,9)],'coral');dot(a,4,9,'jade')
 elif n=='SHELF':
  ell(a,(1,12,14,15),'shadow');rect(a,(2,6,13,13),'brass_dark');rect(a,(3,7,12,12),'jade');rect(a,(1,4,14,7),'pearl');line(a,[(2,4),(13,4)],'white');line(a,[(3,6),(12,6)],'brass_lit');line(a,[(8,8),(8,12)],'pearl');poly(a,[(5,11),(8,8),(11,11)],'pearl')
 elif n=='BAFFLE':
  ell(a,(1,12,14,15),'shadow');poly(a,[(4,1),(9,0),(13,3),(14,7),(12,12),(7,14),(3,11),(1,7),(2,3)],'brass_dark');poly(a,[(5,2),(9,1),(12,4),(12,8),(10,11),(6,12),(3,9),(3,5)],'jade');line(a,[(6,3),(9,3),(11,6),(10,9),(7,11)],'pearl',2);line(a,[(5,4),(4,7),(5,9)],'jade_glow')
 elif n=='GATE':
  rect(a,(1,4,4,14),'brass_dark');rect(a,(12,4,14,14),'brass_dark');poly(a,[(0,5),(2,2),(7,0),(13,2),(15,5)],'pearl');line(a,[(3,4),(7,2),(12,4)],'coral');rect(a,(2,6,3,13),'brass_lit');rect(a,(12,6,13,13),'brass_lit');line(a,[(6,12),(9,9),(6,6)],'jade_glow',2)
 elif n=='DONE':
  ell(a,(2,3,13,14),'jade_dark');ell(a,(3,2,12,12),'jade');line(a,[(5,7),(7,10),(11,4)],'pearl',2)
 else:
  # A native 16px jointed shell guardian. Shape carries warn/open state too.
  warn=n=='GUARDIAN_WARN';opened=n=='GUARDIAN_OPEN'
  ell(a,(0,12,15,15),'shadow');poly(a,[(3,4),(1,8),(2,12),(6,13),(8,15),(11,12),(14,11),(15,6),(11,2),(7,0)],'brass_dark')
  poly(a,[(4,4),(3,7),(4,11),(7,12),(8,14),(10,11),(13,10),(13,6),(10,3),(7,1)],'coral'if warn else'pearl')
  for x,y in[(4,5),(7,2),(10,4)]:line(a,[(8,9),(x,y)],'brass')
  line(a,[(1,9),(0,6),(2,3)],'coral_lit'if warn else'jade',2);line(a,[(13,9),(15,5),(14,2)],'coral_lit'if warn else'jade',2)
  if opened:rect(a,(5,7,10,10),'deep');line(a,[(6,8),(9,8)],'jade_glow');dot(a,8,9,'white')
  else:dot(a,6,7,'deep');dot(a,10,7,'deep');line(a,[(7,10),(9,10)],'coral_shade')
  if warn:line(a,[(5,0),(7,2),(10,0)],'brass_lit');dot(a,1,1,'brass_lit');dot(a,14,0,'brass_lit')
 return a

def emit(sprites):
 h='''/* Generated original Underwater art. Frozen RGB555 palette; shared OBJ cache. */
#ifndef EMBERBOND_UNDERWATER_ART_H
#define EMBERBOND_UNDERWATER_ART_H
#define UNDERWATER_ART_FIRST_ROOM 46
#define UNDERWATER_ART_ROOM_COUNT 8
#define UNDERWATER_ART_FOOT_RADIUS 5
typedef struct { short x,y,w,h; } UnderwaterArtRect;
typedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const UnderwaterArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } UnderwaterArtRoom;
extern const UnderwaterArtRoom underwater_art_rooms[UNDERWATER_ART_ROOM_COUNT];
/* Half-open solids. collision_rows[y] indexes [count,x0,x1,...] in
 * collision_bands. Entries already include the exact radius-five foot. */
/* Native row-major 16px glyphs, zero transparent. Stream existing OBJ slots. */
enum {
'''+''.join(f' UNDERWATER_SPR_{n}={i},\n'for i,n in enumerate(NAMES))+f' UNDERWATER_SPR_COUNT={len(NAMES)}\n}};\nextern const unsigned char underwater_sprites[UNDERWATER_SPR_COUNT][256];\n'
 lines=[];total=0;collision=0
 for r in ROOMS:
  k=r['key'];w=r['width'];ht=r['height'];data=r['art'].im.tobytes();r['bitmap_sha256']=hashlib.sha256(data).hexdigest();assert min(data)>0 and max(data)<len(COLORS)
  for suffix,b in [('',data)]+([('_odd',odd_bitmap(data,w,ht))]if w>240 else[]):
   name='underwater_background_'+k+suffix;h+=f'extern const unsigned char {name}[{len(b)}];\n';cbytes(lines,name,b);total+=len(b)
  lines.append(f'static const UnderwaterArtRect underwater_{k}_solids[] = {{\n');lines.extend(' {'+','.join(map(str,s['rect']))+'},\n'for s in r['solids']);lines.append('};\n');total+=8*len(r['solids'])
  rows,bands,stats=collision_bands(r);r['collision_lookup']=stats
  for suffix,values in [('collision_rows',rows),('collision_bands',bands)]:
   lines.append(f'static const unsigned short underwater_{k}_{suffix}[{len(values)}] = {{\n')
   for at in range(0,len(values),24):lines.append(' '+','.join(map(str,values[at:at+24]))+',\n')
   lines.append('};\n');total+=2*len(values);collision+=2*len(values)
 lines.append('const unsigned char underwater_sprites[UNDERWATER_SPR_COUNT][256] __attribute__((aligned(4))) = {\n')
 for n in NAMES:
  lines.append(' { /* '+n+' */\n');b=sprites[n].im.tobytes()
  for at in range(0,256,32):lines.append(' '+','.join(map(str,b[at:at+32]))+',\n')
  lines.append(' },\n')
 lines.append('};\nconst UnderwaterArtRoom underwater_art_rooms[UNDERWATER_ART_ROOM_COUNT] = {\n')
 for r in ROOMS:
  k=r['key'];odd='underwater_background_'+k+'_odd'if r['width']>240 else'0';lines.append(f' {{{r["width"]},{r["height"]},underwater_background_{k},{odd},underwater_{k}_solids,{len(r["solids"])},underwater_{k}_collision_rows,underwater_{k}_collision_bands}},\n')
 lines.append('};\n');folder=SRC/'underwater_art_data';folder.mkdir(exist_ok=True);chunks=[];buf=''
 for ln in lines:
  if len(buf)+len(ln)>30000:chunks.append(buf);buf=''
  buf+=ln
 if buf:chunks.append(buf)
 for p in folder.glob('*.inc'):p.unlink()
 for i,b in enumerate(chunks):(folder/f'part_{i:03}.inc').write_text(b)
 (SRC/'underwater_art.h').write_text(h+'#endif\n');(SRC/'underwater_art.c').write_text('#include "underwater_art.h"\n'+''.join(f'#include "underwater_art_data/part_{i:03}.inc"\n'for i in range(len(chunks))))
 return {'rom_payload_bytes':total+len(NAMES)*256+224,'collision_lookup_bytes':collision,'sprite_bytes':len(NAMES)*256,'permanent_new_obj_bytes':0,'maximum_streamed_obj_slots':20,'ambient_obj_limit':8,'largest_include_bytes':max(map(len,chunks))}

def finishing_detail(r,a):
 # Sparse shafts use native palette swaps only on floor planes, preserving all
 # contour shadows, structures, glyph contrast, and combat warning colors.
 lookup={P[c('sand_shade')]:P[c('sand')],P[c('pearl_mid')]:P[c('pearl')],P[c('jade_lit')]:P[c('jade_glow')]}
 w,h=a.im.size
 for x0,bw,slope in [(w//4,11,.22),(w*3//4,7,-.16)]:
  for y in range(8,h-8):
   center=int(x0+slope*y)
   for x in range(max(8,center),min(w-8,center+bw)):
    old=a.im.getpixel((x,y))
    if old in lookup:a.im.putpixel((x,y),lookup[old])
 if r['id']==46:
  # Market and sanctuary windows show shelves, working cloth, warm bowls and
  # framed keepsakes. The open cutaways occupy existing building geometry.
  for x,y in [(55,41),(297,39)]:
   rect(a,(x,y,x+35,y+20),'brass_dark');rect(a,(x+2,y+2,x+33,y+18),'jade_dark')
   line(a,[(x+2,y+12),(x+33,y+12)],'brass');line(a,[(x+3,y+18),(x+33,y+18)],'pearl')
   for dx in(8,20,29):ell(a,(x+dx-3,y+6,x+dx+3,y+11),'coral'if dx==20 else'pearl');line(a,[(x+dx-2,y+6),(x+dx+2,y+6)],'brass_lit')
  for x,y in[(165,72),(290,70)]:
   line(a,[(x-10,y-9),(x+9,y-9)],'brass');poly(a,[(x-7,y-8),(x+6,y-8),(x+5,y+2),(x+1,y),(x-3,y+3),(x-6,y)],'jade_glow');line(a,[(x-4,y-6),(x-4,y)],'pearl')
  for x,y in[(38,235),(440,196)]:coral(a,x,y,.75)
 elif r['id']==49:
  for x,y in[(37,67),(191,75)]:line(a,[(x-5,y),(x,y-3),(x+6,y)],'pearl');line(a,[(x-3,y+3),(x+4,y+3)],'brass')
 elif r['id']==50:
  for x,y in[(40,35),(201,35)]:
   rect(a,(x-8,y-5,x+7,y+2),'brass');rect(a,(x-6,y-7,x+5,y),'pearl');line(a,[(x-4,y-4),(x+3,y-4)],'coral')
 elif r['id']==52:
  for x in(36,204):
   line(a,[(x,31),(x,42)],'brass',2);ell(a,(x-5,38,x+5,47),'pearl');ell(a,(x-3,40,x+3,43),'jade')
 elif r['id']==53:
  # Broken sculpture fragments remain thin low-lying mosaic pieces at the rim.
  for x,y in[(38,34),(191,34),(30,119),(204,128)]:poly(a,[(x-4,y),(x+2,y-3),(x+7,y+1),(x+2,y+4)],'pearl_shade');line(a,[(x-2,y),(x+3,y+1)],'brass')

def audit_runtime_targets(r):
 from generate_region import occupancy
 w,h=r['width'],r['height'];blocked=occupancy(r,False);start=tuple(r['spawns']['0']);seen={start};q=deque([start])
 while q:
  x,y=q.popleft()
  for xx,yy in((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<w and 0<=yy<h and not blocked[yy*w+xx] and (xx,yy) not in seen:seen.add((xx,yy));q.append((xx,yy))
 for x,y in RUNTIME_TARGETS[r['id']]:
  candidates=[]
  for distance in range(16,27):
   for dx,dy in[(0,distance),(distance,0),(-distance,0),(0,-distance)]:
    if (x+dx,y+dy) in seen:candidates.append([x+dx,y+dy])
  assert candidates,(r['id'],'runtime A has no facing approach',x,y)
  r['reserved_runtime_targets'].append({'center':[x,y],'approach':candidates[0]})

# Runtime A targets, authoring snapshot; changes are caught by the audit test.
RUNTIME_TARGETS={46: [(64, 72), (64, 104), (80, 256), (96, 104), (120, 72), (144, 104), (160, 176), (240, 104), (240, 240), (240, 272), (304, 176), (340, 72), (340, 108), (384, 128), (384, 160), (416, 72), (416, 108)], 47: [(64, 112), (64, 256), (112, 112), (240, 164), (352, 160), (376, 184), (392, 240), (416, 264)], 48: [(64, 224), (96, 224), (112, 92), (144, 92), (240, 80), (272, 80), (280, 224), (304, 80), (336, 80), (368, 112), (368, 208), (368, 256), (432, 256)], 49: [(64, 56), (64, 88), (80, 88), (112, 88), (120, 48), (144, 52), (172, 52), (208, 64), (208, 96)], 50: [(88, 72), (120, 104), (152, 72)], 51: [(144, 96), (160, 80), (160, 112), (240, 80), (384, 64), (400, 96), (416, 64)], 52: [(80, 72), (120, 112), (160, 72)], 53: [(120, 112), (176, 80), (208, 112)]}

def main():
 ROOMS.clear();OUT.mkdir(exist_ok=True);sprites={n:sprite(n)for n in NAMES};proof={}
 for fn in [town,commons,promenade,garden,vestibule,stacks,listening,court]:
  r,a=fn();finishing_detail(r,a);roads.draw(a,r['id'],P);roads.open_borders(r);audit_runtime_targets(r);r['art']=a
  proof[r['key']],_=verify_room({**r,'spawns':{**r['spawns'],**{'enemy'+str(i):p for i,p in enumerate(r['enemy_spawns'])}}})
 budget=emit(sprites);(OUT/'sprites').mkdir(exist_ok=True);(OUT/'camera').mkdir(exist_ok=True)
 sheet=Image.new('RGB',(160,32),(32,40,66))
 for i,(n,a) in enumerate(sprites.items()):
  a.im.save(OUT/'sprites'/f'{n.lower()}.png',transparency=0);paste_sprite(sheet,a,(i%10)*16+8,(i//10)*16+8)
 sheet.save(OUT/'sprites_native.png');sheet.resize((960,192),Image.Resampling.NEAREST).save(OUT/'sprites_6x.png')
 overview=Image.new('RGB',(960,1280),(25,65,77));d=ImageDraw.Draw(overview)
 camera_sheet=Image.new('RGB',(960,640),(25,65,77))
 for idx,r in enumerate(ROOMS):
  im=r['art'].im;im.save(OUT/(r['key']+'.png'));im.resize((im.width*4,im.height*4),Image.Resampling.NEAREST).save(OUT/(r['key']+'_4x.png'));stage=im.convert('RGB')
  for o in r['objects']:paste_sprite(stage,sprites[o['kind']],*o['center'])
  stage.save(OUT/(r['key']+'_staged.png'));stage.resize((stage.width*4,stage.height*4),Image.Resampling.NEAREST).save(OUT/(r['key']+'_staged_4x.png'))
  for x,y in ([[0,0],[240,0],[0,160],[240,160],[120,80],[120,160],[1,1]]if r['width']>240 else[[0,0]]):
   stage.crop((x,y,x+240,y+160)).save(OUT/'camera'/f'{r["key"]}_{x}_{y}.png')
  ox=(idx%2)*480;oy=(idx//2)*320
  overview.paste(stage,(ox,oy));d.text((ox+12,oy+8),r['name'],fill=(255,243,211))
  cams=[(0,0),(120,80)]if r['width']>240 else[(0,0),(0,0)]
  for q,(x,y) in enumerate(cams):camera_sheet.paste(stage.crop((x,y,x+240,y+160)),((idx%2)*480+q*240,(idx//2)*160))
 layout={'schema':1,'palette_entries':len(COLORS),'palette_sha256':hashlib.sha256(bytes(PAL)).hexdigest(),'coordinate_contract':'half-open solids; five-pixel-radius square foot; 16px centered actors','rooms':[{k:v for k,v in r.items()if k!='art'}for r in ROOMS],'sprites':{'names':NAMES,'maximum_visible_runtime_actors':20,'ambient_limit':8},'generated':budget,'authorship':'Original code-native pixel primitives; no imported or traced game assets'}
 (OUT/'layout.json').write_text(json.dumps(layout,separators=(',',':'))+'\n');(OUT/'validation.json').write_text(json.dumps({'kind':'static host geometry, not native controller QA','routes':proof,'budget':budget},separators=(',',':'))+'\n')
 (OUT/'contract.json').write_text(json.dumps({'rooms':[{'id':r['id'],'name':r['name'],'size':[r['width'],r['height']],'spawns':r['spawns']}for r in ROOMS]},indent=1)+'\n')
 (OUT/'CREDITS.txt').write_text('Original Nacreway / Palinode Archive pixel art authored from Python pixel primitives.\nFrozen shared RGB555 palette from Emberbond; no Nintendo art, traced assets, extraction tools or external raster inputs.\nNative and nearest-neighbor 4x previews are generated from exactly the ROM source bytes.\nStatic art host proofs do not substitute for native movement, combat or visual QA.\n')
 overview.save(OUT/'region_native.png');overview.resize((1920,2560),Image.Resampling.NEAREST).save(OUT/'region_2x.png');camera_sheet.save(OUT/'camera_native.png');camera_sheet.resize((1920,1280),Image.Resampling.NEAREST).save(OUT/'camera_2x.png')
 print(json.dumps(budget))
if __name__=='__main__':main()
