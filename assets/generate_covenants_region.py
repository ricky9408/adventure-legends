#!/usr/bin/env python3
"""The Roads That Stay: original indexed-pixel places, actor props and geometry.
Authored primitives only. Does not read or alter an accepted earlier map raster.
Run with --check to prove byte-exact deterministic reproduction without writing.
"""
from pathlib import Path
from collections import deque
from PIL import Image, ImageDraw
import connected_road_art as roads
import argparse, hashlib, io, json, random, sys
sys.dont_write_bytecode=True
from generate_assets import Art,P
from generate_region import odd_bitmap,cbytes,occupancy
from generate_northern_region import collision_bands
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets/covenants_world';SRC=ROOT/'src'
PLAN=json.loads((OUT/'source_plan.json').read_text())
# These additional town footprints give households their own small street fronts.
# They never occupy a work origin, portal or the permanent perimeter route.
EXTRA_SOLIDS={70:[[40,72,72,40],[360,72,72,40],[48,184,48,24],[384,184,48,24]],74:[[40,40,56,48],[384,40,56,48],[48,192,40,24],[392,192,40,24]]}
NAMES=['STEWARD','GROWER','KILN_KEEPER','WALKER','REPAIRER','SEED_KEEPER','FERRY_KEEPER','WATCHER','NEIGHBOR','PASSENGER','REST','REST_LIT','RESET','NOTICE','MANUAL','FULFILLED','INVITE','WAITING_PLACE','STRAINER','HOT_PLATE','WARM_SEAM','BALLAST','QUIET_PIN','WATER_INLET','LENS','SHADE_SCREEN','FERRY','VENT_OPEN','VENT_CLOSED','SHUTTER','SHUTTER_LOOSE','BOWL','BOWL_COOL','PORCH_LEFT','PORCH_RIGHT','PORCH_MARKS','TRIAL','PRACTICE','WALKER_STEP_A','WALKER_STEP_B','SEED_KEEPER_STEP_A','SEED_KEEPER_STEP_B','PASSENGER_STEP_A','PASSENGER_STEP_B']
CLEANUPS=[]
def rect(a,r,c):
 x,y,w,h=r;a.r((x,y,x+w-1,y+h-1),c)
def outline(a,r,c='wood1',width=1):
 x,y,w,h=r;a.d.rectangle((x,y,x+w-1,y+h-1),outline=P[c],width=width)
def path(a,points,width=24,tone='bg_sunlit_dirt4'):
 a.l(points,'bg_sunlit_dirt1',width+4);a.l(points,'bg_sunlit_dirt2',width+2);a.l(points,tone,width)
def slab(a,r,tone='bg_sunlit_stone4'):
 x,y,w,h=r;rect(a,r,'stone1');rect(a,[x+1,y+1,w-2,h-3],tone)
 a.l([(x+2,y+1),(x+w-3,y+1)],'bg_sunlit_stone5');a.l([(x+1,y+h-2),(x+w-2,y+h-2)],'stone2')
 for yy in range(y+8,y+h-4,10):
  a.l([(x+2,yy),(x+w-3,yy)],'bg_sunlit_stone2')
  for xx in range(x+7+(yy//10%2)*7,x+w-5,17):a.l([(xx,yy),(xx,min(yy+7,y+h-3))],'bg_sunlit_stone3')
def boards(a,r,tone='wood4'):
 x,y,w,h=r;rect(a,r,'wood1');rect(a,[x+1,y+1,w-2,h-3],tone)
 for yy in range(y+5,y+h-2,5):a.l([(x+1,yy),(x+w-2,yy)],'wood2')
 for xx in (x+3,x+w-4):
  for yy in range(y+3,y+h-1,8):a.dot(xx,yy,'wood1')
 a.l([(x+2,y+1),(x+w-3,y+1)],'wood5')
def cloth(a,r,tone='water3',roof=False):
 x,y,w,h=r;rect(a,r,'wood1');rect(a,[x+1,y+1,w-2,h-2],tone)
 for xx in range(x+5,x+w-2,7):a.l([(xx,y+1),(xx-2,y+h-2)],'gold4')
 a.l([(x+2,y+1),(x+w-3,y+1)],'white')
 if roof:
  for xx in range(x+3,x+w-2,8):a.l([(xx,y+h-3),(xx+2,y+h-1)],'wood1')
def house(a,r,tone='water3'):
 x,y,w,h=r;slab(a,r,'plaster');cloth(a,[x,y,w,max(12,h//2)],tone,True)
 for xx in [x+8,x+w-18]:
  rect(a,[xx,y+h//2+3,10,9],'wood1');rect(a,[xx+1,y+h//2+4,8,6],'gold4');a.l([(xx+5,y+h//2+4),(xx+5,y+h//2+9)],'wood3')
 rect(a,[x+w//2-5,y+h-11,10,10],'wood1');rect(a,[x+w//2-4,y+h-10,8,7],'wood3');a.dot(x+w//2+2,y+h-6,'gold4')
def bowl(a,x,y,tone='water3'):
 a.e((x-5,y-3,x+5,y+4),'wood1');a.e((x-4,y-3,x+4,y+2),tone);a.e((x-3,y-3,x+3,y),'gold4');a.l([(x-2,y-1),(x+2,y-1)],'water1')
def flowers(a,x,y):
 for dx,dy,t in [(-4,0,'rose4'),(2,-2,'gold3'),(6,2,'flower1')]:
  a.l([(x+dx,y+dy),(x+dx,y+dy-4)],'pine2');a.dot(x+dx-1,y+dy-5,t);a.dot(x+dx+1,y+dy-5,t);a.dot(x+dx,y+dy-6,'gold4')
def quilt(a,r,tone='rose3'):
 x,y,w,h=r;rect(a,r,tone)
 for yy in range(y+1,y+h,4):a.l([(x,yy),(x+w-1,yy)],'gold4')
 for xx in range(x+2,x+w,6):a.l([(xx,y-1),(xx,y+h)],'gold3')
def leafbed(a,r,tone='pine4',fruit=False):
 x,y,w,h=r;boards(a,r,'wood3');rect(a,[x+3,y+3,w-6,h-7],'dirt1')
 for yy in range(y+7,y+h-5,9):
  for xx in range(x+8,x+w-5,11):
   a.l([(xx,yy+2),(xx,yy-3)],'pine1');a.e((xx-4,yy-4,xx-1,yy-1),tone);a.e((xx+1,yy-5,xx+4,yy-2),'pine5')
   if fruit:a.dot(xx,yy-4,'rose4');a.dot(xx+1,yy-4,'rose5')
def footprints(a,points,tone='bg_sunlit_dirt1'):
 for i,(x,y) in enumerate(points):a.l([(x-3,y),(x-3,y+2)],tone,2);a.l([(x+3,y+2),(x+3,y+4)],tone,2)
def glyph(a,x,y,kind,c='gold4'):
 if kind==0:a.l([(x-4,y+2),(x,y-3),(x+4,y+2)],c,2)
 elif kind==1:a.e((x-3,y-3,x+3,y+3),c);a.e((x-1,y-1,x+1,y+1),'water1')
 elif kind==2:a.l([(x-4,y),(x+4,y)],c,2);a.l([(x,y-4),(x,y+4)],c,2)
 elif kind==3:a.l([(x-4,y-3),(x-4,y+3),(x+4,y+3)],c,2)
 else:a.l([(x-4,y+2),(x-1,y-2),(x+2,y+2),(x+5,y-2)],c,2)
def target(a,t,kind):
 x,y=t['center'];r=t['radius'];a.e((x-r-3,y-r-2,x+r+3,y+r+2),'bg_sunlit_stone2');a.e((x-r-2,y-r-2,x+r+2,y+r+1),'gold4')
 if kind=='hot_plate':a.e((x-r,y-r,x+r,y+r),'fire1');a.l([(x-r,y),(x+r,y)],'gold3')
 elif kind=='warm_seam':a.l([(x-r,y+2),(x,y-2),(x+r,y+2)],'fire1',2)
 elif kind=='quiet_pin':a.l([(x-r,y),(x+r,y)],'wood1',2);a.dot(x,y-2,'silver');a.dot(x,y+2,'silver')
 elif kind=='water_lens':a.e((x-r,y-r,x+r,y+r),'water2');a.l([(x-1,y-2),(x+2,y+1)],'white')
 elif kind=='ballast':a.p([(x-r,y+2),(x-1,y-r),(x+r,y+2)],'stone2');a.l([(x-1,y-r),(x+1,y-r)],'white')
 elif kind=='water_inlet':a.l([(x-r,y-2),(x,y),(x+r,y-2)],'water2',2);a.l([(x-r,y+2),(x+r,y+2)],'water1')
 else:a.l([(x-r,y-r),(x+r,y+r),(x+r,y-r),(x-r,y+r)],'pine2')
 # The target's actual 7x7 visible pixels stay inside its declared rectangle.
def station_contract(area):
 out=[]
 for s in next(s['stations'] for s in PLAN['station_plan'] if s['area']==area):
  x,y=s['approach'];c=s['command'];face=3 if c==108 else 1
  if c==108:centers=[(x+10,y),(x,y+12)];kinds=['hot_plate','warm_seam'];ages=[8,14];beats=[1,2]
  else:
   dx,dy={102:(-8,-20),104:(0,-24),106:(0,-24),110:(0,-20),112:(-6,-24)}[c];centers=[(x+dx,y+dy)];kinds=[{102:'quiet_pin',104:'water_inlet',106:'strainer',110:'ballast',112:'water_lens'}[c]];ages=[{102:8,104:16,106:11,110:6,112:14}[c]];beats=[1]
  if area==74:
   centers=[(x if c==106 else x-8,y-16)];ages=[9 if c==106 else 8]
  targets=[{'center':list(p),'radius':3,'rect':[p[0]-3,p[1]-3,7,7],'kind':k,'expected_age':age,'required_beat':beat} for p,k,age,beat in zip(centers,kinds,ages,beats)]
  out.append({**s,'face':face,'targets':targets,'release_age':10 if c==108 else 0,'origin_kind':'player foot center; effect remains anchored here','manual_aim_change':False})
 return out
SHORTCUTS={70:[178,136,124,16],71:[116,138,16,36],72:[0,0,0,0],73:[74,56,92,16],74:[0,0,0,0],75:[80,210,16,44],76:[168,18,16,76],77:[0,0,0,0]}
SHORTCUT_ENDS={70:[[168,144],[312,144]],71:[[124,128],[124,184]],73:[[64,64],[176,64]],75:[[88,200],[88,264]],76:[[176,12],[176,104]]}
PRACTICE_OFFSETS={70:[(0,-14)],71:[(0,-28),(16,-28)],72:[(0,8),(0,-28)],73:[(0,-24)],74:[(12,-12)],75:[(0,-16)],76:[(0,-28),(24,-28)],77:[(0,-20)]}
MANUAL={70:[[144,264],[352,176]],71:[[120,232]],72:[[336,104]],73:[[120,128]],74:[[120,240],[240,136]],75:[[192,232]],76:[[384,120]],77:[[120,120]]}
HUMANS={70:[['STEWARD',128,272],['NEIGHBOR',64,136],['FERRY_KEEPER',400,144],['GROWER',344,280]],71:[['GROWER',160,232],['NEIGHBOR',48,200]],72:[['KILN_KEEPER',360,128],['NEIGHBOR',48,72]],73:[['WALKER',64,128]],74:[['REPAIRER',136,264],['NEIGHBOR',376,112],['WATCHER',96,120],['SEED_KEEPER',344,280]],75:[['SEED_KEEPER',160,208]],76:[['PASSENGER',112,128],['FERRY_KEEPER',384,88]],77:[['WATCHER',144,120],['NEIGHBOR',104,112]]}
def room_contract(a):
 n=a['id'];r={'id':n,'key':f'room{n}','name':a['name'],'width':a['width'],'height':a['height'],'spawns':{str(s['id']):s['xy'] for s in a['spawns']},'reset':a['reset_xy'],'invitation':a['invitation_xy'],'solids':[{'rect':s} for s in a['static_solids']+EXTRA_SOLIDS.get(n,[])],'dynamic_solid_states':a['dynamic_solid_states'],'stations':station_contract(n),'manual':MANUAL[n],'humans':HUMANS[n],'portals':[],'rest':next((q['xy'] for q in PLAN['rests'] if q['area']==n),None)}
 for road in roads.DATA['roads']:
  for e,other in [road['ends'],list(reversed(road['ends']))]:
   if e['room']==n:r['portals'].append({'center':e['arrival'],'to':other['room'],'spawn':other['saved_spawn']})
 p=next(p for p in PLAN['legendary_field_exhibits'] if p['area']==n);x,y=p['start_xy'];r['practice']={**p,'face':1,'targets':[{'center':[x+dx,y+dy],'radius':3,'rect':[x+dx-3,y+dy-3,7,7]}for dx,dy in PRACTICE_OFFSETS[n]]}
 r['practice']['shortcut_center_strip']=SHORTCUTS[n]
 r['practice']['shortcut_endpoints']=SHORTCUT_ENDS.get(n,[])
 q=SHORTCUTS[n];r['practice']['visible_surface_rect']=[q[0]-5,q[1]-5,q[2]+10,q[3]+10] if q[2] else [0,0,0,0]
 r['practice']['closure_rule']='Do not close while any actor foot overlaps the center strip; no riding moving geometry'
 return r

def floor(a,r):
 n=r['id'];w,h=a.im.size;rng=random.Random(n*10531)
 base='bg_sunlit_grass3' if n in (70,71,75) else 'bg_sunlit_dirt3' if n in (72,77) else 'bg_sunlit_stone4' if n==74 else 'bg_sunlit_grasslit'
 rect(a,[0,0,w,h],base)
 # Sparse flat natural texture, with a bright dry escape route around all work.
 for _ in range(w*h//200):
  x=rng.randrange(6,w-7);y=rng.randrange(6,h-7)
  a.l([(x,y),(x+rng.randrange(1,4),y)],'bg_sunlit_grass2' if n in (70,71,75) else 'bg_sunlit_dirt2' if n in (72,77) else 'bg_sunlit_stone3')
 path(a,[(24,24),(w-24,24),(w-24,h-32),(24,h-32),(24,24)],22)
 if h==320:path(a,[(24,160),(w-24,160)],24)
 else:path(a,[(8,128),(w-8,128)],24)
 for p in r['portals']:
  x,y=p['center'];path(a,[(x,y),(max(24,min(w-24,x)),max(24,min(h-32,y)))],24)
  # The continuous road itself marks the exit; no floating arrow portal remains.
 roads.draw(a,n,P)
 # A measured border stays outside the radius-five walking limit.
 # Border masonry is baked with the same open mouths as collision.
 for yy in (2,h-3):
  for xx in range(2,w-2):
   if not any(x<=xx<x+ww and y<=yy<y+hh for x,y,ww,hh in roads.clear_rects(n)):a.r((xx,yy,xx,yy+1),'bg_sunlit_stone2')

def draw70(a,r):
 # The stepped water commons is the town's unmistakable central landmark.
 slab(a,[184,72,112,144]);rect(a,[192,79,96,128],'bg_sunlit_water1')
 for i,(yy,ww) in enumerate([(83,84),(112,72),(142,58),(173,44)]):
  xx=240-ww//2;rect(a,[xx,yy,ww,24],'bg_sunlit_water3');a.l([(xx,yy+2),(xx+ww-1,yy+2)],'watergleam',2);a.l([(xx,yy+22),(xx+ww-1,yy+22)],'water0')
  for q in range(xx+4,xx+ww-7,17):a.l([(q,yy+10),(q+7,yy+10)],'bg_sunlit_water4')
 # Distribution is painted on broad flush runnels, not uncollided deep water.
 for x in (160,320):
  a.l([(x,92),(x,224)],'bg_sunlit_stone2',7);a.l([(x,94),(x,222)],'bg_sunlit_water2',3)
  for y in (140,196):a.l([(x-6,y),(x+6,y)],'gold4',2)
 for x in (40,360):boards(a,[x,40,72,24]);cloth(a,[x,40,72,13],'water3' if x==40 else 'pine4',True);house(a,[x,72,72,40],'water3' if x==40 else 'pine4')
 for x in (48,384):boards(a,[x,184,48,24]);bowl(a,x+11,192);bowl(a,x+33,192,'rose4');a.l([(x+3,199),(x+44,199)],'gold4')
 for x,y in [(40,128),(432,132),(48,216),(368,216),(128,40),(344,40)]:flowers(a,x,y)
 quilt(a,[104,284,30,12],'water3');quilt(a,[360,280,28,13],'rose3')
 for x,y in [(208,240),(272,240)]:slab(a,[x-11,y-7,22,14]);glyph(a,x,y,1,'water1')
 a.l([(112,52),(152,52)],'wood1');
 for x in range(116,153,8):a.l([(x,53),(x+3,61)],'gold3',2)
 # Public waiting circles and two different household measuring traditions.
 for x in (88,392):a.d.ellipse((x-12,230,x+12,240),outline=P['bg_sunlit_dirt1']);footprints(a,[(x,245)])

def draw71(a,r):
 path(a,[(48,280),(48,112),(192,112),(192,40)],24)
 path(a,[(48,208),(120,208),(192,240)],22)
 for y,fruit in [(64,True),(144,False)]:leafbed(a,[72,y,96,24],fruit=fruit)
 # Reserved empty service gutter: a future root cover never erases a seedling.
 rect(a,[111,144,26,24],'wood1');rect(a,[113,145,22,22],'bg_sunlit_water2');a.l([(114,155),(133,155)],'water4')
 # Roof ribs are flat trial outlines; only the moving panel is a solid.
 for x in (88,120,152):
  a.l([(x,95),(x,127)],'bg_sunlit_stone2',2);a.l([(x-4,96),(x+4,96)],'wood1');a.l([(x-4,126),(x+4,126)],'wood1')
 a.l([(88,104),(176,104)],'gold4',2);a.l([(88,121),(176,121)],'gold1')
 for x in range(80,161,16):a.p([(x,88),(x+8,94),(x+15,88)],'bg_sunlit_grass2')
 a.l([(184,80),(208,80),(208,168),(184,168)],'bg_sunlit_stone2',6);a.l([(184,80),(208,80),(208,168),(184,168)],'bg_sunlit_water3',3)
 for x,y in [(80,190),(96,195),(112,199),(128,204),(144,212)]:footprints(a,[(x,y)])
 # Two generations of graft tags are visible in paired stitched ground sheets.
 quilt(a,[64,32,42,14],'rose3');quilt(a,[132,32,42,14],'water3');glyph(a,85,39,0);glyph(a,153,39,3)
 for x,y in [(32,48),(32,228),(212,204),(208,248),(64,256)]:flowers(a,x,y)
 boards(a,[88,256,42,9]);bowl(a,98,260,'rose4');bowl(a,120,260,'water3')

def draw72(a,r):
 # Unequal chimneys and one shared lower shelf make this a workshop, not a hall.
 for i,x in enumerate((128,240,352)):
  slab(a,[x,24,64,56],'dirt3');rect(a,[x+4,30,56,46],'wood2')
  a.p([(x+6,72),(x+6,50),(x+16,38),(x+46,38),(x+56,50),(x+56,72)],'fire0')
  a.p([(x+14,72),(x+14,54),(x+23,45),(x+40,45),(x+49,55),(x+49,72)],'wood0')
  a.l([(x+6,75),(x+57,75)],'gold3',2)
  for yy in (32,42,54,65):a.l([(x+3,yy),(x+9,yy)],'gold1');a.l([(x+54,yy),(x+60,yy)],'gold1')
  rect(a,[x+24,25,16,7+i*3],'stone1');rect(a,[x+26,25,12,3+i*3],'gold4')
  for j in range(i+1):a.dot(x+28+j*4,36,'gold3')
 boards(a,[128,85,64,7]);boards(a,[240,85,64,7]);boards(a,[352,85,64,7])
 for i,x in enumerate((144,160,176)):bowl(a,x,88,'rose4');glyph(a,x,100,i,'wood2')
 for x,y in [(48,40),(72,40),(32,88)]:quilt(a,[x,y,18,10],'water3')
 for x,y in [(48,44),(72,44)]:bowl(a,x+8,y,'rose4')
 a.l([(232,24),(232,78)],'gold4',2);a.l([(328,24),(328,78)],'gold4',2)
 footprints(a,[(72,128),(200,128),(312,128),(416,136)])
 # Exhibition plaque waits flat on the far threshold, household work faces road.
 quilt(a,[416,34,36,14],'rose3');glyph(a,434,41,2)

def draw73(a,r):
 # Deep water is confined to the exact impassable footprint. Two side galleries
 # and the southern dry walk remain visibly continuous around the mechanism.
 slab(a,[80,32,80,64]);rect(a,[86,38,68,51],'water1')
 for yy in range(42,87,11):a.l([(89,yy),(149,yy)],'water3');a.l([(96,yy+2),(122,yy+2)],'water4')
 boards(a,[96,36,48,13]);a.l([(100,42),(140,42)],'gold4',2)
 for x in (88,148):a.l([(x,48),(x,91)],'wood1',2);a.l([(x+2,48),(x+2,91)],'gold1')
 # Counterweight track is flush and does not imply that the player rides it.
 for yy in (97,108):a.l([(88,yy),(152,yy)],'stone2')
 for x in (96,120,144):a.l([(x,110),(x,115)],'gold1',2)
 for x in (48,192):path(a,[(x,32),(x,128)],22,'bg_sunlit_stone5')
 for x,y in [(24,48),(216,48)]:quilt(a,[x-7,y-4,14,8],'water3')
 footprints(a,[(80,128),(104,128),(128,128),(152,128)])
 # The two pause marks have different silhouettes, readable without color.
 glyph(a,96,119,1,'wood2');glyph(a,144,119,3,'wood2')

def draw74(a,r):
 # Sloping repair-roof row surrounds a real open court, not an empty ring.
 slab(a,[136,48,208,40],'plaster');cloth(a,[136,48,208,19],'rose3',True)
 for x in range(144,330,24):rect(a,[x,72,14,11],'wood1');rect(a,[x+1,73,12,7],'gold4');a.l([(x+7,73),(x+7,80)],'wood3')
 for x in (136,312):boards(a,[x,88,32,72]);
 for y in (99,120,142):
  for x in (144,320):bowl(a,x+8,y,'gold2');a.l([(x-3,y+8),(x+18,y+8)],'wood1')
 house(a,[40,40,56,48],'water3');house(a,[384,40,56,48],'rose4')
 slab(a,[208,184,64,40],'gold2');rect(a,[213,189,54,29],'wood1');rect(a,[216,191,48,24],'gold3')
 for x in range(221,261,8):a.l([(x,193),(x,212)],'gold0');a.dot(x+2,195,'gold4')
 # Three public pulse stones distinguish circle / bar / open corner.
 for i,(x,y) in enumerate([(192,152),(240,160),(288,152)]):a.e((x-7,y-5,x+7,y+5),'bg_sunlit_stone2');glyph(a,x,y,i,'white')
 for x in (48,392):boards(a,[x,192,40,24]);cloth(a,[x+4,196,32,10],'water3');a.l([(x+3,212),(x+36,212)],'gold3')
 # Sound screens have visible hinges and open mouths; runtime supplies angle.
 for x in (184,280):a.l([(x,112),(x+20,128)],'bg_sunlit_stone2',3);a.e((x-2,110,x+2,114),'gold1')
 quilt(a,[356,92,32,12],'water3');a.l([(360,102),(384,102)],'gold4')
 for x,y in [(112,40),(364,40),(36,112),(444,112),(104,208),(376,216)]:flowers(a,x,y)
 quilt(a,[112,284,32,11],'rose3');footprints(a,[(192,244),(240,248),(288,244)])
 # The old prize remains above the public tool list; the new task changes focus.
 glyph(a,240,59,2,'gold4');rect(a,[225,69,30,11],'wood1');rect(a,[227,70,26,8],'gold4')

def draw75(a,r):
 path(a,[(24,272),(136,272),(128,184),(120,112),(120,32),(208,32)],24)
 leafbed(a,[56,56,40,48],'pine4');leafbed(a,[144,120,40,56],'pine5');boards(a,[56,216,64,32])
 for x,y in [(65,227),(84,227),(105,227)]:bowl(a,x,y,'water3')
 # Open seed shelving straddles a reserved irrigation gutter, not planted soil.
 rect(a,[75,216,26,32],'wood1');rect(a,[77,217,22,30],'bg_sunlit_water2');a.l([(78,232),(97,232)],'water4')
 # Leaf-shaped ground shadows are deliberate and never invisible walls.
 for pts in [[(104,80),(130,91),(124,110),(101,102)],[(128,147),(141,165),(136,193),(117,172)]]:a.p(pts,'bg_sunlit_grass2');a.l(pts+[pts[0]],'bg_sunlit_grass1')
 for x,y in [(50,48),(102,48),(138,112),(190,112)]:a.e((x-2,y-2,x+2,y+2),'wood1');a.dot(x,y,'gold3')
 for x,y in [(74,118),(160,187)]:a.l([(x-10,y),(x+10,y)],'gold3',2);a.l([(x-10,y-2),(x-10,y+2)],'wood1');a.l([(x+10,y-2),(x+10,y+2)],'wood1')
 for x,y in [(128,248),(128,224),(120,208),(120,128),(120,104),(120,80)]:footprints(a,[(x,y)],'bg_sunlit_grass0')
 quilt(a,[152,216,24,11],'rose3');quilt(a,[24,184,24,11],'water3')
 for i,(x,y) in enumerate([(36,192),(164,224),(96,264)]):glyph(a,x,y,i,'gold4')
 for x,y in [(32,48),(216,96),(216,208),(48,264)]:flowers(a,x,y)

def draw76(a,r):
 # One shallow canal, exact banks: pale rippled shallows are walkable; only the
 # dark retaining pools match the two supplied collision footprints.
 rect(a,[112,32,272,72],'bg_sunlit_water4')
 for yy in range(36,103,12):
  for xx in range(118,379,31):a.l([(xx,yy),(xx+12,yy)],'bg_sunlit_water3')
 slab(a,[136,24,80,64]);rect(a,[140,28,72,54],'water1')
 for yy in range(33,79,10):a.l([(145,yy),(205,yy)],'water3')
 slab(a,[280,72,72,32]);rect(a,[284,76,64,22],'water1');a.l([(288,88),(344,88)],'water3',2)
 # Safe flat cable deck and separate marked landing shelves.
 boards(a,[220,38,80,7]);a.l([(220,42),(300,42)],'gold4')
 boards(a,[104,72,25,11]);boards(a,[358,72,30,11]);glyph(a,116,77,1);glyph(a,372,77,3)
 a.l([(224,64),(300,64)],'wood1');
 for x in (236,260,284):a.l([(x,62),(x,69)],'gold2',2)
 for x in (96,384):a.l([(x-9,110),(x+9,110)],'gold4',3)
 quilt(a,[48,38,36,15],'rose3');quilt(a,[404,38,36,15],'water3')
 for x in (64,420):glyph(a,x,44,4);bowl(a,x,63,'water3')
 footprints(a,[(112,128),(216,128),(264,128),(360,128)])
 # Matching waiting signs use a shared three-line pattern, no literacy puzzle.
 for x in (88,392):
  for dy in (0,4,8):a.l([(x-5,26+dy),(x+5,26+dy)],'wood2')

def draw77(a,r):
 # A refuge with low stone cheeks and a warm center open toward the road.
 slab(a,[80,32,80,32],'plaster');cloth(a,[80,32,80,16],'rose3',True)
 rect(a,[88,51,64,9],'wood1');a.l([(92,53),(148,53)],'gold3',2)
 for x in (32,184):slab(a,[x,72,24,32]);rect(a,[x+4,76,16,22],'wood3');a.l([(x+7,79),(x+17,94)],'gold4',2)
 # Three loose shutters are runtime overlays; these distinct sockets remain.
 for x,y in [(64,48),(120,24),(176,48)]:a.l([(x-5,y),(x+5,y)],'wood2',2);a.dot(x,y-2,'gold3')
 a.e((82,76,158,133),'bg_sunlit_dirt2');a.e((90,81,150,128),'bg_sunlit_dirt4')
 # Unfilled central hearth is an invitation to stand, not a solid fire pit.
 a.d.ellipse((104,87,136,115),outline=P['gold1'],width=2)
 for x,y in [(96,96),(144,96),(112,128),(136,128)]:a.dot(x,y,'fire2');a.dot(x+1,y,'gold3')
 quilt(a,[16,34,28,14],'water3');quilt(a,[196,34,28,14],'rose3')
 for x,y in [(24,60),(216,60)]:bowl(a,x,y,'water3')
 footprints(a,[(72,136),(96,136),(144,136),(168,136)])
 for x,y in [(20,108),(220,108)]:flowers(a,x,y)

DRAW={70:draw70,71:draw71,72:draw72,73:draw73,74:draw74,75:draw75,76:draw76,77:draw77}
def draw_room(r):
 a=Art(r['width'],r['height']);floor(a,r);DRAW[r['id']](a,r)
 for s in r['stations']:
  for t in s['targets']:target(a,t,t['kind'])
  x,y=s['approach'];a.l([(x-4,y+5),(x+4,y+5)],'gold4',2)
  if s['face']==1:a.l([(x-3,y+8),(x,y+5),(x+3,y+8)],'wood2')
  else:a.l([(x-4,y+7),(x-1,y+10),(x-4,y+13)],'wood2')
 for x,y in r['manual']:a.d.ellipse((x-7,y-4,x+7,y+4),outline=P['gold1'])
 for label in ('reset','invitation','rest'):
  if not r[label]:continue
  x,y=r[label];a.e((x-10,y-6,x+10,y+6),'bg_sunlit_dirt2');a.d.ellipse((x-9,y-5,x+9,y+5),outline=P['bg_sunlit_stone5'])
 return a

def sprite(n):
 a=Art(16,16,'transparent')
 if '_STEP_' in n:
  base,step=n.split('_STEP_');a=sprite(base);a.r((0,12,15,15),'transparent');a.e((2,13,13,15),'shadow')
  a.r((4,11 if step=='A' else 13,6,13 if step=='A' else 14),'wood1');a.r((10,13 if step=='A' else 11,12,14 if step=='A' else 13),'wood1')
  a.l([(4,11),(11,11)],'gold2' if base=='WALKER' else 'rose4' if base=='SEED_KEEPER' else 'pine3')
  return a
 if n in NAMES[:10]:
  idx=NAMES.index(n);skin=['skin2','skin1','skin2','skin0','skin1'][idx%5];coat=['water3','pine4','rose3','gold2','water2','rose4','water3','rose3','purple3','pine3'][idx]
  a.e((2,13,13,15),'shadow');a.r((4,11,6,14),'wood1');a.r((10,11,12,14),'wood1');a.p([(5,7),(10,7),(13,12),(3,12)],coat);a.r((5,2,10,7),skin);a.r((4,1,11,3),'wood1');a.dot(6,5,'ink');a.dot(9,5,'ink');a.l([(7,7),(9,7)],'skin0')
  a.l([(3,9),(4,7)],skin,2);a.l([(11,7),(13,9)],skin,2)
  if n=='STEWARD':a.r((3,1,12,2),'water4');a.r((11,8,15,11),'gold4');a.l([(12,9),(14,9)],'water2')
  if n=='GROWER':a.l([(2,3),(13,3)],'wood4',2);a.r((12,9,15,12),'wood2');a.dot(13,8,'pine5')
  if n=='KILN_KEEPER':a.r((5,8,10,12),'gold4');a.dot(7,10,'rose3');a.r((0,8,3,11),'rose3')
  if n=='WALKER':a.l([(1,7),(1,14)],'wood2');a.l([(12,5),(14,10)],'wood4',2)
  if n=='REPAIRER':a.r((11,8,15,10),'silver');a.l([(13,7),(13,13)],'wood1');a.r((6,8,9,11),'gold3')
  if n=='SEED_KEEPER':a.r((0,8,4,12),'gold4');a.dot(2,9,'pine2');a.l([(2,10),(3,11)],'pine3')
  if n=='FERRY_KEEPER':a.l([(0,3),(0,13)],'wood1');a.r((0,3,3,5),'gold3');a.r((4,1,11,2),'water4')
  if n=='WATCHER':a.r((11,7,14,12),'wood1');a.r((12,8,13,10),'gold3');a.r((3,1,12,2),'rose4')
  if n=='NEIGHBOR':a.r((4,1,11,2),'silver');a.l([(11,8),(14,11)],skin,2)
  if n=='PASSENGER':a.r((0,9,4,13),'wood3');a.l([(1,8),(3,8)],'wood1')
 elif n in ('REST','REST_LIT'):
  a.e((1,11,14,15),'stone2');a.l([(4,11),(11,13),(4,13),(11,11)],'wood1',2);a.p([(4,10),(6,6),(7,9),(9,3),(12,11),(9,13),(6,12)],'fire2' if n=='REST_LIT' else 'gold1');a.p([(7,11),(9,7),(10,11)],'gold4')
 elif n in ('RESET','NOTICE','TRIAL','PRACTICE'):
  a.r((7,10,9,15),'wood1');a.r((1,1,14,11),'wood1');a.r((2,2,13,10),'gold4')
  if n=='RESET':a.l([(4,6),(6,3),(10,4),(11,7),(8,9),(5,8)],'water2',2);a.l([(4,5),(4,8),(7,8)],'water2',2)
  elif n=='TRIAL':glyph(a,8,6,0,'wood2')
  elif n=='PRACTICE':a.l([(4,7),(8,3),(12,7),(8,9),(4,7)],'pine2')
  else:a.l([(4,4),(11,4)],'wood2');a.l([(4,7),(9,7)],'wood2')
 elif n in ('FULFILLED','INVITE','WAITING_PLACE'):
  a.e((1,9,14,15),'stone2');a.e((2,8,13,13),'gold3')
  if n=='FULFILLED':a.l([(4,6),(7,9),(12,2)],'pine3',2)
  elif n=='INVITE':a.l([(3,6),(3,2),(7,2)],'water2',2);a.l([(9,2),(13,2),(13,6)],'water2',2)
  else:a.r((3,6,12,8),'wood4');a.l([(4,8),(4,12)],'wood2');a.l([(11,8),(11,12)],'wood2')
 elif n=='MANUAL':a.r((3,10,13,14),'stone2');a.l([(8,11),(8,3)],'wood1',2);a.l([(3,4),(12,4)],'gold3',3)
 elif n in ('HOT_PLATE','WARM_SEAM','BALLAST','QUIET_PIN','WATER_INLET','LENS','STRAINER'):
  target(a,{'center':[8,8],'radius':3}, {'LENS':'water_lens','STRAINER':'strainer'}.get(n,n.lower()))
 elif n=='SHADE_SCREEN':boards(a,[1,1,14,14]);cloth(a,[2,2,12,10],'pine4');a.r((6,3,9,11),'transparent')
 elif n=='FERRY':a.p([(1,4),(14,4),(12,12),(4,12)],'wood1');a.r((3,5,12,10),'wood4');a.l([(4,7),(11,7)],'wood2');a.l([(7,1),(7,13)],'gold2')
 elif n in ('VENT_OPEN','VENT_CLOSED'):
  a.r((2,2,13,13),'stone1');a.r((3,3,12,12),'wood3');a.r((5,4,10,11),'ink' if n=='VENT_OPEN' else 'gold2');a.l([(3,2),(12,2)],'gold4')
 elif n in ('SHUTTER','SHUTTER_LOOSE'):
  boards(a,[2,2,12,13]);a.l([(4,4),(11,11)] if n=='SHUTTER' else [(1,5),(10,9)],'gold4',2);a.dot(3,3,'silver')
 elif n in ('BOWL','BOWL_COOL'):bowl(a,8,8,'fire2' if n=='BOWL' else 'water3')
 elif n.startswith('PORCH'):
  boards(a,[0,9,16,7]);a.l([(0,9),(15,9)],'gold4')
  if n=='PORCH_LEFT':a.r((1,4,3,12),'wood2');a.l([(2,4),(13,4)],'wood4',2);a.r((3,5,12,8),'wood3')
  elif n=='PORCH_RIGHT':a.r((13,4,15,12),'wood2');a.l([(2,4),(14,4)],'wood4',2);a.r((3,5,12,8),'wood3')
  else:
   for x,c in [(3,'water3'),(8,'rose3'),(13,'pine4')]:a.r((x-1,2,x+1,7),c);a.dot(x,3,'gold4')
 return a

def dynamic_states(r):
 states=[[]]
 for q in r['dynamic_solid_states']:
  if q and q not in states:states.append(q)
 # Every integer intermediate, not only authored detents, is checked.
 nonempty=[q[0] for q in states if q]
 if len(nonempty)>1:
  first,last=nonempty[0],nonempty[-1]
  for x in range(first[0],last[0]+1):
   q=[[x,first[1],first[2],first[3]]]
   if q not in states:states.append(q)
 return states

def flood(r,extra):
 trial={**r,'solids':r['solids']+[{'rect':q}for q in extra]};w,h=r['width'],r['height'];blocked=occupancy(trial,False);p=r['spawns']['0'];start=p[1]*w+p[0]
 assert not blocked[start],(r['id'],'spawn blocked',extra)
 seen=bytearray(w*h);seen[start]=1;q=deque([start])
 while q:
  p=q.popleft();x=p%w;y=p//w
  for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
   if 0<=xx<w and 0<=yy<h:
    z=yy*w+xx
    if not seen[z] and not blocked[z]:seen[z]=1;q.append(z)
 return seen,blocked

def audit(r,a):
 w,h=r['width'],r['height'];targets=list(r['spawns'].values())+[r['reset'],r['invitation']]+[p['center']for p in r['portals']]+[s['approach']for s in r['stations']]+r['manual']+[p[1:]for p in r['humans']]+[r['practice']['start_xy']]
 if r['rest']:targets.append(r['rest'])
 minimum=w*h
 # These strips exempt already-expanded actor-center collision. The visible
 # plank grows by5 in every direction, covering each allowed full foot.
 shortcut=r['practice']['shortcut_center_strip'];ends=r['practice']['shortcut_endpoints']
 if shortcut[2]:
  seen,b=flood(r,[]);sx,sy,sw,sh=shortcut
  assert any(b[y*w+x] for y in range(sy,sy+sh) for x in range(sx,sx+sw)),(r['id'],'shortcut does not cross a real obstacle')
  for x,y in ends:assert seen[y*w+x] and not b[y*w+x],(r['id'],'shortcut endpoint blocked',x,y)
  for y in range(sy,sy+sh):b[y*w+sx:y*w+sx+sw]=bytes(sw)
  # Direct centerline must join both genuine walkable endpoints.
  (x0,y0),(x1,y1)=ends
  assert x0==x1 or y0==y1
  for y in range(min(y0,y1),max(y0,y1)+1):
   for x in range(min(x0,x1),max(x0,x1)+1):assert not b[y*w+x],(r['id'],'shortcut interrupted',x,y)
 for extra in dynamic_states(r):
  seen,b=flood(r,extra);minimum=min(minimum,sum(seen))
  for x,y in targets:assert seen[y*w+x] and not b[y*w+x],(r['id'],'fullfoot unreachable',x,y,extra)
 rows,bands,stats=collision_bands(r)
 for y in range(h):
  offset=rows[y];n=bands[offset];intervals=[bands[offset+1+i*2:offset+3+i*2]for i in range(n)]
  for x in range(w):assert bool(occupancy_cache(r)[y*w+x])==any(lo<=x<hi for lo,hi in intervals),(r['id'],x,y)
 # Actual generated target coverage, not only an unpainted coarse rectangle.
 coverage=[];solid_coverage=[]
 for q in r['solids']:
  x,y,sw,sh=q['rect'];values=set(a.im.crop((x,y,x+sw,y+sh)).tobytes());assert len(values)>=3,(r['id'],'invisible solid',q);solid_coverage.append({'rect':q['rect'],'native_palette_values':len(values)})
 for s in r['stations']:
  for t in s['targets']:
   x,y,tw,th=t['rect'];pixels=set(a.im.crop((x,y,x+tw,y+th)).tobytes());assert len(pixels)>=2,(r['id'],'invisible target',t)
   coverage.append({'key':s['key'],'kind':t['kind'],'rect':t['rect'],'native_palette_values':len(pixels)})
 return {'shortcut_connects_walkable_endpoints':bool(shortcut[2]),'shortcut_center_strip':shortcut,'full_11_by_11_foot':True,'dynamic_states_checked':len(dynamic_states(r)),'minimum_reachable_centers':minimum,'critical_points':len(targets),'all_spawns_portals_manual_rest_invitation_stations_and_people_reachable':True,'row_lookup_exact_for_every_pixel':True,'target_pixel_coverage':coverage,'solid_pixel_coverage':solid_coverage}
_OCC={}
def occupancy_cache(r):
 if r['id'] not in _OCC:_OCC[r['id']]=occupancy(r,False)
 return _OCC[r['id']]

def png(im):
 b=io.BytesIO();im.save(b,format='PNG',optimize=False);return b.getvalue()
def js(x):return (json.dumps(x,ensure_ascii=False,indent=1)+'\n').encode()
def build():
 files={};rooms=[];lines=[];budget=0;proof={};sheet=Image.new('RGB',(960,1280),(23,33,49));native=Image.new('RGB',(960,640),(23,33,49));actor_sheet=Image.new('RGB',(16*10,16*5),(23,33,49))
 for i,a in enumerate(PLAN['areas']):
  r=room_contract(a);roads.open_borders(r);im=draw_room(r);raw=im.im.tobytes();assert min(raw)>0 and len(set(raw))>=20;proof[str(r['id'])]=audit(r,im);r['bitmap_sha256']=hashlib.sha256(raw).hexdigest();w,h=im.im.size;k=r['key']
  files[OUT/f'{k}.png']=png(im.im);files[OUT/f'{k}_4x.png']=png(im.im.resize((w*4,h*4),Image.Resampling.NEAREST));files[OUT/f'{k}_gray.png']=png(im.im.convert('L'));files[OUT/f'{k}_gray_4x.png']=png(im.im.convert('L').resize((w*4,h*4),Image.Resampling.NEAREST))
  # Developer staging uses original small residents, leaves guardian identities out.
  staged=im.im.copy()
  for name,x,y in r['humans']+[('RESET',*r['reset']),('WAITING_PLACE',*r['invitation'])]+([('REST',*r['rest'])] if r['rest'] else []):
   sp=sprite(name).im;staged.paste(sp,(x-8,y-15),Image.frombytes('L',(16,16),bytes(255 if v else 0 for v in sp.tobytes())))
  files[OUT/f'{k}_staged.png']=png(staged);files[OUT/f'{k}_staged_4x.png']=png(staged.resize((w*4,h*4),Image.Resampling.NEAREST));sheet.paste(staged.convert('RGB'),((i%2)*480,(i//2)*320))
  for ci,(cx,cy) in enumerate([(0,0),(w-240,h-160)]):
   crop=staged.crop((cx,cy,cx+240,cy+160));native.paste(crop.convert('RGB'),((i%2)*480+ci*240,(i//2)*160));files[OUT/'camera'/f'{k}_{cx}_{cy}.png']=png(crop)
  for suffix,data in [('',raw)]+([('_odd',odd_bitmap(raw,w,h))]if w>240 else []):cbytes(lines,'covenants_background_'+k+suffix,data);budget+=len(data)
  lines.append('static const CovenantsArtRect covenants_'+k+'_solids[] = {'+','.join('{'+','.join(map(str,s['rect']))+'}'for s in r['solids'])+'};\n');budget+=8*len(r['solids'])
  rows,bands,stats=collision_bands(r);r['collision_lookup']=stats
  for suffix,values in [('rows',rows),('bands',bands)]:
   lines.append(f'static const unsigned short covenants_{k}_{suffix}[] = {{\n');lines.extend(' '+','.join(map(str,values[j:j+24]))+',\n'for j in range(0,len(values),24));lines.append('};\n');budget+=2*len(values)
  rooms.append(r)
 lines.append(f'const unsigned char covenants_sprites[{len(NAMES)}][256] __attribute__((aligned(4))) = {{\n')
 for i,n in enumerate(NAMES):
  a=sprite(n);raw=a.im.tobytes();actor_sheet.paste(a.im.convert('RGB'),((i%10)*16,(i//10)*16));files[OUT/'sprites'/f'{n.lower()}.png']=png(a.im);lines.append(' {\n');lines.extend(' '+','.join(map(str,raw[j:j+32]))+',\n'for j in range(0,256,32));lines.append(' },\n');budget+=256
 lines.append('};\n');lines.append('const CovenantsArtRoom covenants_art_rooms[8] = {\n')
 for r in rooms:
  k=r['key'];odd='covenants_background_'+k+'_odd'if r['width']>240 else '0';lines.append(f' {{{r["width"]},{r["height"]},covenants_background_{k},{odd},covenants_{k}_solids,{len(r["solids"])},covenants_{k}_rows,covenants_{k}_bands}},\n')
 lines.append('};\n');lines.append('const short covenants_practice_shortcuts[8][4] = {'+','.join('{'+','.join(map(str,SHORTCUTS[n]))+'}'for n in range(70,78))+'};\n');budget+=8*28+64+8*4*2
 header='''/* Generated original The Roads That Stay pixels; no new RAM allocation. */
#ifndef EMBERBOND_COVENANTS_ART_H
#define EMBERBOND_COVENANTS_ART_H
#define COVENANTS_ART_FIRST_ROOM 70
#define COVENANTS_ART_ROOM_COUNT 8
#define COVENANTS_ART_FOOT_RADIUS 5
typedef struct { short x,y,w,h; } CovenantsArtRect;
typedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const CovenantsArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } CovenantsArtRoom;
/* collision_rows[y] is an offset into half-open merged x intervals:
 * [count,lo0,hi0,...]. This already expands every static solid by radius5.
 * Dynamic objects must be tested separately with that identical foot rule.
 * bitmap_odd exists ONLY when width>240, no buffer or unpack step needed. */
extern const CovenantsArtRoom covenants_art_rooms[COVENANTS_ART_ROOM_COUNT];
/* Optional practice only: half-open allowed CENTER strips, indexed area-70.
 * Paint the visible plank five pixels beyond each edge for the full foot. */
extern const short covenants_practice_shortcuts[COVENANTS_ART_ROOM_COUNT][4];
enum {
'''+''.join(f' COVENANTS_SPR_{n}={i},\n'for i,n in enumerate(NAMES))+f' COVENANTS_SPR_COUNT={len(NAMES)}\n}};\nextern const unsigned char covenants_sprites[COVENANTS_SPR_COUNT][256];\n#endif\n'
 files[SRC/'covenants_art.h']=header.encode();parts=[];part=''
 for line in lines:
  if len(part)+len(line)>29000:parts.append(part);part=''
  part+=line
 if part:parts.append(part)
 for i,s in enumerate(parts):files[SRC/'covenants_art_data'/f'part_{i:03}.inc']=s.encode()
 files[SRC/'covenants_art.c']=('#include "covenants_art.h"\n'+''.join(f'#include "covenants_art_data/part_{i:03}.inc"\n'for i in range(len(parts)))).encode()
 assert budget<=1300000,budget
 files[OUT/'developer_scene_sheet_native.png']=png(sheet);files[OUT/'developer_scene_sheet_4x.png']=png(sheet.resize((3840,5120),Image.Resampling.NEAREST));files[OUT/'developer_scene_sheet_gray.png']=png(sheet.convert('L'));files[OUT/'camera_native.png']=png(native);files[OUT/'camera_4x.png']=png(native.resize((3840,2560),Image.Resampling.NEAREST));files[OUT/'actors_native.png']=png(actor_sheet);files[OUT/'actors_4x.png']=png(actor_sheet.resize((640,320),Image.Resampling.NEAREST));files[OUT/'actors_gray_4x.png']=png(actor_sheet.convert('L').resize((640,320),Image.Resampling.NEAREST))
 # Public previews are restricted to the first town and carry no legend or ending.
 for name,crop in [('water_steps',draw_room(rooms[0]).im.crop((120,64,360,224))),('reed_homes',draw_room(rooms[0]).im.crop((0,0,240,160)))]:files[OUT/'spoiler_free'/f'{name}_native.png']=png(crop);files[OUT/'spoiler_free'/f'{name}_4x.png']=png(crop.resize((960,640),Image.Resampling.NEAREST))
 files[OUT/'geometry.json']=js({'schema':1,'coordinate_contract':'all actor coordinates are foot centers; rects half-open; full foot radius5; sprite top-left=(x-8,y-15)','rooms':rooms,'corrections':['108 gathers at local f8, so proposed north24 plate replaced by faceRIGHT gather(x+10,y), radial release(x,y+12)','102 uses its actual offset quiet-side line: target offset(-8,-20), default side-left, faceUP','112 uses its actual default-left blade lane: target offset(-6,-24)','Area71 form122 second practice target moved to(64,84) to keep its center outside expanded bed', 'Area74 targets moved below expanded workshop wall:106=(192,96),102=(280,96);125 practice=(204,100)', 'Two town household footprints added outside all required approach and perimeter lanes'],'moving_resident_frames':{n:[n,n+'_STEP_A',n,n+'_STEP_B']for n in ['WALKER','SEED_KEEPER','PASSENGER']},'village_porch':{'area':0,'blocking':False,'sprites':['PORCH_LEFT','PORCH_MARKS','PORCH_RIGHT'],'proposed_foot_centers':[[96,136],[112,136],[128,136]],'semantic':'After confirmed shared-porch commitment and homecoming only; flat shared bench and eight craft marks. Main should verify against existing actor positions before drawing.'}})
 files[OUT/'validation.json']=js({'scope':'Generated art and full-foot host geometry only; native controller routing and stateful gameplay are separate','rooms':proof,'rom_art_upper_bound_bytes':budget,'budget_bytes':1300000,'includes_max_bytes':max(map(len,parts)),'generated_includes':len(parts),'new_ewram_bytes':0,'new_iwram_bytes':0,'odd_atlases':[r['id']for r in rooms if r['width']>240]})
 files[OUT/'CREDITS.txt']=b'All Covenants room pixels, residents and props authored from original geometric primitives in generate_covenants_region.py. Existing original game RGB555 palette is shared. No commercial assets, external raster inputs, traced layouts, borrowed melodies or generated-image inputs. Developer sheets show future scenes; spoiler_free previews only show the first town. Previews are art staging, not controller screenshots.\n'
 files[OUT/'manifest.json']=js({'schema':1,'title':'The Roads That Stay','generator':'assets/generate_covenants_region.py','room_ids':list(range(70,78)),'art_budget_bytes':1300000,'rom_art_upper_bound_bytes':budget,'sprites':NAMES,'provenance':'Original authored geometry and indexed native RGB555 palette','input_sha256':{'assets/generate_covenants_region.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'assets/covenants_world/source_plan.json':hashlib.sha256((OUT/'source_plan.json').read_bytes()).hexdigest()},'files':{str(p.relative_to(ROOT)):{'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}for p,data in sorted(files.items())}})
 return files

def main():
 p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();files=build()
 if args.check:
  bad=[str(p.relative_to(ROOT))for p,b in files.items()if not p.exists() or p.read_bytes()!=b]
  assert not bad,'Regeneration differs: '+', '.join(bad)
  print('Covenants art: all deterministic output bytes match, all geometry/resources pass')
 else:
  for p,b in files.items():p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(b)
  expected=set(files)
  for old in (SRC/'covenants_art_data').glob('part_*.inc'):
   if old not in expected:old.unlink()
  print('Covenants art: generated',len(files),'files; all eight full-foot geometries pass')
if __name__=='__main__':main()
