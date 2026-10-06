#!/usr/bin/env python3
"""Original native-pixel Kilnstep art. Frozen palette, no imported game assets.
All pictures are authored with code-native vector/pixel primitives. The same
half-open solids generate the engine's exact radius-five collision row tables.
"""
from pathlib import Path
import hashlib,json,random,sys
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True
from generate_assets import Art,P,PAL,COLORS,color_background
from generate_region import odd_bitmap,cbytes,verify_room,paste_sprite
from generate_northern_region import collision_bands
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/magma_region';SRC=ROOT/'src'
NAMES=['RESSA','NEMI','OMI','TAVI','SEN','PELL','REST','REST_LIT','LIFT','BRICK','BRICK_HOT','BAFFLE','SHOE','HOOD','HOOD_OPEN','WHEEL','SHELF','BOWL','TRAY','HOOK','PIN','CATCH','SPRING','RIBBON','GRILLE','RESET','TRIAL','NOTICE','GATE','DONE','REGULATOR','REG_WARN','REG_OPEN','REG_DONE','GRAB','RESSA_WORK','NEMI_WORK','OMI_WORK','TAVI_WORK','SEN_STEP','PELL_WORK']
NPCS=set(NAMES[:6]);DYNAMIC=NPCS|{'REST','REST_LIT','LIFT','BRICK','BRICK_HOT','BAFFLE','SHOE','HOOD','HOOD_OPEN','GATE','REGULATOR','REG_WARN','REG_OPEN','REG_DONE','GRAB'}
KEYS=['kilnstep_commons','pumice_terraces','potters_walk','cloudwell_grotto','intake_ledger','breathing_vault','return_flue_gallery','caldera_bell']
TITLES=['Kilnstep Commons','Pumice Terraces','Potters Walk','Cloudwell Grotto','Intake Ledger','Breathing Vault','Return-Flue Gallery','Caldera Bell']
# Current-r6 return landing only; all prior spawn rows and pixels are unchanged.
SPAWNS=[{'0':[240,284],'1':[304,32],'2':[80,152],'3':[112,264],'4':[416,240]},{'0':[240,284],'1':[80,104],'2':[400,72],'3':[80,280]}]+[{'0':[120,136]} for _ in range(6)]
ROOMS=[]
def solid(r,key,b):r['solids'].append({'kind':key,'rect':list(b)})
def obj(r,key,kind,x,y,approach=None,**extra):
 r['objects'].append(dict(key=key,kind=kind,center=[x,y],approach=approach or [x,y+16],interaction_radius=23,static_baked=kind not in DYNAMIC,**extra))
def exit_(r,key,x,y,target,spawn=0):r['exits'].append({'key':key,'approach':[x,y],'target':target,'target_spawn':spawn})
def paving(a,x,y,w,h,tone='dirt4'):
 a.r((x,y,x+w-1,y+h-1),tone)
 # Worn individually cut flags. Broken joints and tiny corner highlights avoid
 # an endless perfect grid while keeping native character contrast quiet.
 R=random.Random(x*13+y*17+w)
 for yy in range(y+7,y+h,16):
  for xx in range(x-16+(8 if yy%32 else 0),x+w,32):
   lo=max(x,xx);hi=min(x+w-1,xx+28)
   if lo<=hi:
    a.l([(lo,yy),(hi,yy)],'dirt3');a.l([(lo+3,yy-1),(min(hi,lo+12),yy-1)],'plaster')
    if xx>=x:a.l([(xx,yy+2),(xx,min(yy+12,y+h-1))],'dirt3')
    if R.randrange(3)==0:a.l([(lo+5,yy+6),(min(hi,lo+9),yy+5)],'plaster')
    if R.randrange(5)==0:a.dot(min(hi,lo+15),min(y+h-1,yy+9),'dirt3')
def path(a,pts,w=26):a.l(pts,'purple1',w+5);a.l(pts,'dirt3',w+2);a.l(pts,'plaster',w-2)
def channel(a,pts,w=5):
 a.l(pts,'stone1',w+7);a.l(pts,'stone5',w+4);a.l(pts,'water2',w);a.l([(x,y-1)for x,y in pts],'water4',1)
 for (x,y),(xx,yy) in zip(pts,pts[1:]):
  n=max(abs(xx-x),abs(yy-y))
  for k in range(7,n,19):
   sx=x+(xx-x)*k/n;sy=y+(yy-y)*k/n;a.l([(int(sx)-2,int(sy)),(int(sx)+2,int(sy))],'water3')
def green(a,x,y,w,h):
 a.r((x,y,x+w,y+h),'pine1');a.r((x+2,y+2,x+w-2,y+h-2),'grass3')
 for yy in range(y+5,y+h-2,8):
  for xx in range(x+5,x+w-2,9):a.e((xx-2,yy-3,xx+3,yy+3),'pine3');a.l([(xx,yy),(xx+1,yy-4)],'leaflight');a.dot(xx+2,yy-2,'flower1')
def wall(a,r,x,y,w,h,kind='terrace_wall'):
 a.r((x+2,y+3,x+w+3,y+h+4),'purple1');a.r((x,y,x+w-1,y+h-1),'stone1');a.r((x,y,x+w-1,y+2),'stone5')
 for xx in range(x+5,x+w,12):a.l([(xx,y+3),(xx,y+h-1)],'stone3')
 solid(r,kind,(x,y,w,h))
def house(a,r,x,y,w,h,door):
 # Tall cream walls, warm shallow parapets, indigo shaded west faces.
 a.r((x+7,y+18,x+w+7,y+h+7),'purple1');a.r((x,y+19,x+w,y+h),'gold1');a.r((x+3,y+20,x+w-3,y+h-1),'plaster')
 a.r((x-3,y+9,x+w+3,y+21),'dirt3');a.r((x-3,y+5,x+w+3,y+12),'dirt4');a.l([(x-3,y+5),(x+w+3,y+5)],'white',2)
 a.r((x+6,y-4,x+w-7,y+5),'gold1');a.r((x+8,y-3,x+w-9,y+1),'plaster')
 for xx in range(x+13,x+w-14,28):
  a.r((xx,y+30,xx+12,y+47),'stone1');a.r((xx+2,y+31,xx+10,y+45),'water1');a.l([(xx+4,y+33),(xx+4,y+43)],'water4')
 a.r((door-11,y+h-23,door+11,y+h),'stone1');a.r((door-8,y+h-21,door+8,y+h),'deep');a.l([(door-9,y+h-21),(door-9,y+h-1)],'gold4');a.r((door-12,y+h+1,door+12,y+h+4),'stone5')
 # Public heat chimneys have wide cowl + visible cool ceramic delivery pipe.
 a.r((x+w-24,y-12,x+w-13,y+5),'stone2');a.p([(x+w-29,y-13),(x+w-8,y-13),(x+w-12,y-18),(x+w-25,y-18)],'gold2');a.l([(x+w-20,y-11),(x+w-20,y+1)],'gold4')
 channel(a,[(x+w-3,y+21),(x+w-3,y+h+10),(x+w+7,y+h+10)],3)
 solid(r,'pale_terraced_building',(x-3,y-18,w+7,h+19))
def tree(a,r,x,y,s=1):
 a.e((x-16*s,y-4*s,x+17*s,y+6*s),'shadowsoft');a.l([(x,y),(x,y-22*s)],'wood2',max(2,int(5*s)))
 for xx,yy,rr in[(-9,-22,11),(9,-24,12),(0,-36,13)]:
  a.e((x+(xx-rr)*s,y+(yy-rr)*s,x+(xx+rr)*s,y+(yy+rr)*s),'pine1');a.e((x+(xx-rr+2)*s,y+(yy-rr)*s,x+(xx+rr-2)*s,y+(yy+rr-4)*s),'pine3');a.l([(x+(xx-5)*s,y+(yy-rr+3)*s),(x+(xx+4)*s,y+(yy-rr+3)*s)],'leaflight',2)
 solid(r,'living_tree_trunk',(x-3,y-11,6,12))
def sprite(n):
 if n.endswith('_WORK') or n=='SEN_STEP':
  base=n.split('_')[0];a=sprite(base)
  a.r((4,10,6,12),'skin2');a.r((9,8,13,10),'skin2')
  if base=='NEMI':a.e((10,6,14,10),'fire2');a.l([(11,6),(14,6)],'gold3')
  elif base=='OMI':a.l([(12,10),(15,13)],'water3');a.dot(14,14,'water4')
  elif base=='TAVI':a.r((11,6,14,9),'water3');a.l([(12,7),(14,7)],'water4')
  elif base=='PELL':a.l([(1,6),(5,10)],'gold3');a.dot(1,5,'white')
  elif base=='SEN':a.r((4,13,6,15),'wood1');a.r((10,12,12,14),'wood1')
  else:a.r((11,7,14,10),'plaster')
  return a
 a=Art(16,16,'transparent')
 if n in NPCS:
  i=NAMES.index(n);coat=['fire2','water2','pine3','water3','purple2','gold2'][i]
  a.e((2,12,13,15),'shadow');a.r((5,11,7,14),'wood1');a.r((9,11,11,14),'wood1');a.p([(4,7),(11,7),(13,11),(11,13),(4,13),(3,10)],coat);a.r((5,3,11,8),'skin2');a.r((4,2,11,4),'wood1');a.dot(6,6,'ink');a.dot(10,6,'ink');a.l([(7,8),(9,8)],'skin1')
  if n=='RESSA':a.r((2,1,12,3),'gold3');a.r((11,9,14,11),'stone4')
  elif n=='NEMI':a.r((5,9,10,12),'plaster');a.e((0,9,4,13),'fire1')
  elif n=='OMI':a.r((1,3,14,4),'grassgold');a.r((4,1,11,3),'grassgold');a.l([(13,8),(13,15)],'wood3')
  elif n=='TAVI':a.r((4,1,12,3),'water3');a.r((1,10,4,13),'water2')
  elif n=='SEN':a.r((10,7,14,12),'wood3');a.l([(5,8),(10,12)],'gold4')
  else:a.r((2,9,5,12),'gold4');a.dot(3,10,'deep')
  return a
 if n in ['BRICK','BRICK_HOT','BAFFLE','SHOE']:
  a.e((1,11,14,15),'shadow');a.r((2,4,13,13),'stone1');a.r((2,3,13,9),'plaster'if n!='BAFFLE'else'water2');a.l([(3,3),(12,3)],'white');a.l([(4,6),(11,6)],'water3');a.r((6,8,9,10),'deep');a.l([(6,8),(9,8)],'water4')
  if n=='BRICK_HOT':a.r((4,4,11,6),'gold3');a.dot(6,2,'fire2');a.dot(10,1,'gold3')
  if n=='BAFFLE':a.p([(3,2),(11,2),(13,5),(5,5)],'water4')
  if n=='SHOE':a.r((5,1,10,4),'gold2');a.r((5,11,10,14),'purple1')
 elif n.startswith('REG'):
  hot=n=='REG_WARN';opened=n=='REG_OPEN';a.e((1,3,14,14),'stone1');a.e((3,4,12,12),'gold1')
  for pts in[[(7,7),(1,2),(4,0),(9,5)],[(8,7),(15,4),(15,8),(10,10)],[(7,8),(9,15),(4,14),(4,9)]]:a.p(pts,'fire2'if hot else'plaster')
  a.e((5,5,10,10),'water3'if opened else'gold3');a.r((7,6,8,9),'deep');a.dot(6,4,'white')
  if n=='REG_DONE':a.e((4,4,11,11),'pine3');a.l([(5,7),(7,10),(10,5)],'white')
 elif n in ['HOOD','HOOD_OPEN','GATE']:
  a.r((2,3,13,14),'stone1');a.r((4,5,11,14),'deep');a.p([(0,4),(8,0),(15,4)],'gold2');a.r((4,6,11,9 if n=='HOOD_OPEN'else 13),'water2');a.l([(5,6),(10,6)],'water4')
 elif n in ['REST','REST_LIT']:
  a.e((1,9,14,15),'stone1');a.e((2,7,13,12),'stone5');a.e((4,8,11,11),'water3');a.p([(5,7),(6,2),(8,5),(10,1),(11,7)],'gold3'if n=='REST_LIT'else'water4')
 elif n=='LIFT':a.r((1,8,14,14),'wood2');a.l([(1,1),(1,13),(14,13),(14,1)],'gold3',2);a.r((3,7,12,9),'plaster');a.l([(7,0),(7,5)],'stone3')
 elif n=='DONE':a.e((3,3,12,12),'pine2');a.l([(5,7),(7,10),(11,5)],'white',2)
 elif n=='GRAB':a.l([(2,6),(5,3),(5,5),(12,5),(12,8),(5,8),(5,10),(2,6)],'water4')
 else:
  a.e((2,10,13,15),'shadowsoft');a.r((3,3,12,12),'wood1');a.r((4,2,11,10),'plaster')
  if n in ['RESET','TRIAL','NOTICE']:a.r((7,10,9,15),'wood3');a.l([(5,7),(8,4),(10,7)],'water2');a.dot(8,8,'water2')
  elif n in ['BOWL','SPRING']:a.e((2,5,13,12),'stone4');a.e((4,5,11,9),'water2');a.l([(5,6),(10,6)],'water4')
  elif n=='TRAY':a.r((2,6,13,11),'wood3');a.r((3,5,12,8),'pine3');a.dot(5,4,'leaflight');a.dot(10,4,'leaflight')
  elif n=='GRILLE':
   for x in range(4,13,3):a.l([(x,3),(x,11)],'stone1')
   a.dot(6,8,'water4');a.dot(10,8,'water4')
  elif n=='RIBBON':a.l([(4,2),(4,15)],'wood3');a.p([(5,2),(14,4),(9,7),(5,6)],'pine3')
  elif n in ['HOOK','CATCH','PIN']:a.l([(5,3),(5,9),(10,9),(11,6)],'gold2',2);a.dot(6,3,'white')
  elif n=='WHEEL':a.e((3,2,12,11),'gold2');a.e((5,4,10,9),'deep');a.l([(7,2),(7,11)],'gold4');a.l([(3,6),(12,6)],'gold4')
  elif n=='SHELF':a.r((1,8,14,11),'water2');a.r((2,2,5,7),'gold2');a.r((9,3,12,7),'fire2')
 return a

def make(i):
 w,h=(480,320)if i<2 else(240,160);r={'id':38+i,'key':KEYS[i],'name':TITLES[i],'width':w,'height':h,'spawns':SPAWNS[i],'solids':[],'objects':[],'exits':[],'dynamic_rectangles':[],'enemy_spawns':[]};a=Art(w,h,'dirt4');ROOMS.append(r)
 if i<2:
  R=random.Random(138+i);a.r((0,0,w-1,h-1),'grass3'if i else'dirt3')
  for _ in range(w*h//150):
   x=R.randrange(w);y=R.randrange(h);a.l([(x,y),(x+3,y)],R.choice(['grass4','leaflight','grassgold'])if i else'dirt4')
  for x in(0,w-8):solid(r,'world_edge',(x,0,8,h))
  gap=304 if i==0 else 240
  solid(r,'north_left',(8,0,gap-24,8));solid(r,'north_right',(gap+16,0,w-gap-24,8));solid(r,'south_left',(8,h-8,216,8));solid(r,'south_right',(256,h-8,216,8))
 else:
  paving(a,8,24,224,132,'stone5'if i==3 else'dirt4')
  for x in(0,232):solid(r,'side_wall',(x,0,8,160));a.r((x,0,x+7,159),'purple1');a.l([(x+4,25),(x+4,155)],'stone3')
  solid(r,'upper_wall',(8,0,224,20));a.r((8,0,231,19),'stone1');a.r((10,2,229,15),'plaster');a.l([(8,18),(231,18)],'white')
  solid(r,'south_left',(8,156,96,4));solid(r,'south_right',(136,156,96,4));a.r((8,156,103,159),'stone2');a.r((136,156,231,159),'stone2')
  for yy in(147,152,157):a.l([(108,yy),(132,yy)],'stone3')
  obj(r,'reset','RESET',24,136,[24,120]);obj(r,'trial_key1','TRIAL',24,112,[24,128]);obj(r,'trial_key2','TRIAL',216,112,[216,128]);exit_(r,'south',120,148,38 if i==2 else 39 if i in(3,4)else 37+i,2 if i in(2,4)else 1 if i==3 else 0)
 return r,a

def town():
 r,a=make(0);paving(a,12,141,456,163)
 path(a,[(304,0),(304,164),(240,230),(240,320)],30)
 house(a,r,28,41,104,95,80);house(a,r,176,29,92,85,222);house(a,r,348,40,100,89,398)
 # Slope depth from two cut stone terrace edges with broad staircase gaps.
 wall(a,r,16,167,89,7);wall(a,r,352,166,113,8)
 for yy in range(170,187,4):a.l([(111,yy),(140,yy)],'stone5');a.l([(274,yy),(322,yy)],'stone5')
 channel(a,[(146,25),(146,126),(166,144),(166,270),(215,285)],5);channel(a,[(323,37),(323,123),(340,138),(340,263),(408,277)],5)
 green(a,32,212,61,47);green(a,362,208,89,47)
 wall(a,r,30,261,64,6);wall(a,r,360,258,91,6)
 # Public ceramic kiln and open cool workbench; backgrounds never bake movable jar.
 a.e((184,146,225,165),'purple1');a.r((186,133,220,157),'stone2');a.e((187,122,219,145),'plaster');a.r((197,141,209,158),'deep');a.r((194,133,212,136),'gold3')
 solid(r,'public_kiln',(186,123,35,36))
 a.r((120,205,204,213),'stone1');a.r((120,202,204,206),'stone5')
 for x in (128,184):a.r((x,212,x+4,219),'stone2')
 solid(r,'cool_lesson_bench',(120,202,85,13))
 a.r((232,261,248,304),'wood3');a.l([(226,263),(226,303)],'gold2',3);a.l([(253,263),(253,303)],'gold2',3)
 tree(a,r,26,296,.8);tree(a,r,451,300,.8)
 for key,k,x,y in [('ressa','RESSA',160,176),('nemi','NEMI',96,176),('pell','PELL',384,176),('lift','LIFT',240,268),('rest','REST',112,248),('lesson_jar','BRICK',144,232),('lesson_shelf','SHELF',192,232),('public_hood','HOOD',224,208),('clapper_marks','NOTICE',384,208),('branch_board','NOTICE',304,208),('trial_key1','TRIAL',432,280),('trial_key2','TRIAL',400,280),('quiet_catch','CATCH',288,248)]:obj(r,key,k,x,y)
 exit_(r,'field',304,16,39);exit_(r,'workshop',80,152,40);exit_(r,'lift',240,284,30,0)
 return r,a

def field():
 r,a=make(1)
 for pts,w in [([(240,320),(240,252),(208,220),(208,170),(148,142),(80,104)],28), ([(208,168),(292,148),(357,117),(400,72)],28), ([(148,142),(142,95),(212,76),(290,83),(358,117)],26), ([(208,220),(128,242),(72,262),(64,194),(148,142)],25), ([(240,250),(318,263),(406,248),(410,181),(357,117)],26)]:path(a,pts,w)
 for x,y,w,h in[(58,143,57,42),(168,34,83,23),(265,173,100,44),(290,282,128,19)]:green(a,x,y,w,h);wall(a,r,x,y+h+2,w,6)
 # Walkable cool rills retain color, moss and inhabited crop pockets.
 channel(a,[(118,36),(119,90),(149,117),(185,144),(258,150),(292,136),(356,137),(391,173),(441,198)],6)
 channel(a,[(355,31),(353,80),(301,102),(276,127)],4)
 house(a,r,363,15,71,39,400)
 a.p([(49,35),(82,24),(110,40),(120,77),(103,85),(52,81),(42,59)],'purple1');a.p([(50,37),(81,29),(108,42),(115,75),(102,81),(55,78),(47,58)],'stone4');a.r((69,61,91,84),'stone1');a.r((73,63,88,84),'deep');solid(r,'grotto_entrance',(47,29,67,55))
 tree(a,r,33,120,.7);tree(a,r,452,130,.8);tree(a,r,445,295,.7)
 for key,k,x,y in [('omi','OMI',304,232),('sen','SEN',136,216),('rest','REST',80,264),('handwheel','WHEEL',192,192),('goat_guide','NOTICE',240,192),('goat_invite','SHELF',288,192),('fallen_screen','BAFFLE',128,264),('screen_bay','SHELF',176,264),('outer_return','GATE',104,112),('seed_tray','TRAY',72,208),('pika_shelter','CATCH',104,208),('second_pika','TRAY',80,232),('wind_hood','HOOD',392,208),('kite_shelter','RIBBON',424,208),('second_kite','HOOD',424,240),('spring_brush','SPRING',304,96),('tracks','NOTICE',272,96),('wind_ribbon','RIBBON',368,264),('seed_landing','TRAY',336,240),('trial_key1','TRIAL',208,248),('trial_key2','TRIAL',272,248),('reset','RESET',48,280)]:obj(r,key,k,x,y)
 r['enemy_spawns']=[[184,116],[256,264],[424,120],[328,56],[56,232]]
 exit_(r,'town',240,300,38,1);exit_(r,'grotto',80,104,41);exit_(r,'intake',400,72,42);exit_(r,'worker_door',104,128,40);r['exits'][-1]['requires_q35_objectives']=2
 return r,a

def interior(i):
 r,a=make(i)
 if i==2:
  # Potter's real divided drying hall; broad lower working passage.
  for x,w in[(44,48),(144,48)]:
   a.r((x,28,x+w,41),'wood1');a.r((x+2,29,x+w-2,35),'wood4');solid(r,'drying_shelf',(x,28,w,14))
   for xx in range(x+6,x+w-5,13):a.e((xx,23,xx+7,31),'fire1');a.l([(xx+1,24),(xx+6,24)],'gold3')
  a.r((105,4,136,17),'water2');a.r((108,6,133,15),'pine3')
  for key,k,x,y in [('nemi','NEMI',208,80),('pot_tags','NOTICE',48,64),('shelf_choice','SHELF',88,64),('dry_baffle','HOOD',128,64),('practice_set','TRAY',168,64),('clapper_hook','HOOK',48,96),('clapper_left','CATCH',80,96),('clapper_right','CATCH',112,96),('sample1','PIN',144,96),('sample2','PIN',176,96),('ore_basket','BOWL',192,112),('second_ore','BOWL',160,112),('line_hook1','HOOK',56,112),('line_hook2','HOOK',88,112),('moss_invite','TRAY',120,112),('return_window','NOTICE',208,136)]:obj(r,key,k,x,y, [x,y+16] if y<=112 else [x-16,y])
  exit_(r,'worker_return',192,136,39,1);r['exits'][-1]['requires_q35_objectives']=2
 elif i==3:
  # Offset lava-tube skylights and scalloped former-flow walls, cool water pockets.
  a.p([(8,24),(58,24),(66,34),(53,44),(21,42),(8,52)],'stone3');a.p([(152,20),(226,20),(230,47),(215,40),(180,44),(161,35)],'stone3')
  a.e((87,23,129,36),'water3');a.e((94,23,124,30),'white')
  channel(a,[(29,37),(44,48),(70,44),(101,53),(122,43),(157,52),(191,43),(210,55)],7)
  for key,k,x,y in [('tavi','TAVI',208,80),('flow_arrows','NOTICE',48,64),('bypass','WHEEL',80,64),('public_bowl','BOWL',112,64),('catch_bowl','BOWL',144,64),('second_bowl','BOWL',176,64),('listening_sign','NOTICE',48,96),('sound_left','HOOD',80,96),('sound_right','HOOD',144,96),('clapper_return','HOOK',176,96),('grille_face','GRILLE',192,112)]:obj(r,key,k,x,y)
  r['enemy_spawns']=[[56,120],[184,136]]
 elif i in(4,5,6):
  # Different silhouettes: cold straight divider, broken buttress, split flues.
  if i==4:wall(a,r,112,20,16,61,'cold_divider');channel(a,[(116,26),(116,72)],3)
  elif i==5:wall(a,r,108,20,24,31,'pressure_buttress');a.p([(105,29),(119,22),(136,29)],'plaster')
  else:wall(a,r,108,20,24,39,'split_flue');channel(a,[(111,27),(96,22),(65,22)],3);channel(a,[(128,27),(144,22),(180,22)],3)
  # The 7x5 inset slide rests are geometry, never a menu board.
  for y in range(32,105,18):
   for x in range(48,193,24):a.l([(x-5,y+7),(x+5,y+7)],'stone3');a.dot(x-5,y+6,'stone5')
  for key,k,x,y in [('source','SPRING',48,68),('receiver','SHELF',192,68),('brace','CATCH',168,104),('forward','GATE',216,56),('clue','NOTICE',24,64)]:obj(r,key,k,x,y, [x,y+16])
  if i==4:obj(r,'brick','BRICK',48,68,[32,68])
  else:obj(r,'brick'if i==6 else'baffle','BRICK'if i==6 else'BAFFLE',48 if i==6 else 96,68 if i==6 else 86,[32,68]if i==6 else[80,86]);obj(r,'baffle'if i==6 else'shoe','BAFFLE'if i==6 else'SHOE',168,86,[184,86])
  if i==6:obj(r,'pin','PIN',192,104,[208,104]);obj(r,'shortcut','GATE',216,136,[200,136]);obj(r,'upper_hood','HOOD',72,112,[56,112])
  r['enemy_spawns']=[[24,88]] if i<6 else[[24,88],[216,88]]
  exit_(r,'forward',216,72,39+i)
  if i==6:exit_(r,'shortcut',200,136,39,2)
 else:
  # Three ceramic vanes radiate around a central coupling with broad safe lanes.
  for x in(51,171):
   a.r((x,27,x+18,55),'stone2');a.r((x+2,27,x+16,35),'plaster');a.p([(x-3,28),(x+9,19),(x+21,28)],'gold2');solid(r,'regulator_pier',(x,27,19,29))
  a.e((81,29,159,79),'purple1');a.e((84,27,156,73),'stone4');a.e((94,32,146,67),'plaster');a.e((104,37,136,61),'gold1')
  for y in(78,102):a.l([(48,y),(192,y)],'gold1')
  channel(a,[(64,64),(64,115),(176,115),(176,64)],4)
  for key,k,x,y in [('regulator','REGULATOR',120,64),('start','WHEEL',120,112),('left_handle','HOOD',32,80),('right_handle','HOOD',208,80),('report_return','LIFT',208,136),('clue','NOTICE',24,48)]:obj(r,key,k,x,y,[x,y+16]if y<136 else[x-16,y])
 return r,a

def detail_scene(r,a):
 """Small handcrafted environmental stories; no new collision or palette."""
 area=r['id']
 def pot(x,y,c='fire1'):
  a.e((x-4,y-7,x+4,y+2),'purple1');a.e((x-3,y-7,x+3,y),'gold1'if c=='gold1'else c);a.l([(x-2,y-7),(x+2,y-7)],'plaster');a.l([(x-2,y-5),(x-2,y-2)],'gold3')
 def footprint(x,y):
  a.e((x-3,y-1,x-1,y+1),'wood2');a.e((x+2,y+2,x+4,y+4),'wood2')
 def shape(x,y,k,c='water2'):
  if k==0:a.e((x-3,y-3,x+3,y+3),c);a.e((x-1,y-1,x+1,y+1),'plaster')
  elif k==1:a.l([(x-4,y+3),(x,y-4),(x+4,y+3),(x-4,y+3)],c)
  else:a.l([(x-3,y-3),(x+3,y-3),(x+3,y+3),(x-3,y+3),(x-3,y-3)],c)
 if area==38:
  # The shared cooling court has a deep striped canvas canopy over its
  # existing solid bench, with shadow bands kept away from the lesson handles.
  a.p([(116,182),(201,182),(211,196),(112,196)],'water1')
  for xx in range(117,202,17):a.p([(xx,182),(xx+8,182),(xx+10,195),(xx-1,195)],'water3')
  a.l([(112,196),(211,196)],'water0',2)
  for xx in(123,200):a.r((xx,196,xx+3,210),'wood2');a.l([(xx,197),(xx,209)],'wood4')
  a.r((126,213,199,216),'purple1');a.l([(126,216),(198,216)],'stone3')
  # Arrival landing is broad pale decking. Its two side ropes never cover
  # the player's world240,284 center or the unconditional approach corridor.
  a.r((220,271,260,305),'stone1');a.r((222,272,258,304),'plaster')
  for yy in range(275,305,6):a.l([(223,yy),(257,yy)],'dirt3');a.l([(224,yy+1),(256,yy+1)],'stone5')
  for xx in(217,263):a.r((xx,269,xx+2,305),'wood1');a.l([(xx,270),(xx,303)],'gold3')
  a.l([(215,279),(220,277)],'gold2');a.l([(259,277),(265,279)],'gold2')
  # Low moss carpets and flowering cracks are walkable living ground cover.
  for xx,yy in[(173,281),(182,286),(194,290),(285,281),(302,293),(315,281),(160,258),(329,260)]:
   a.e((xx-9,yy-3,xx+8,yy+4),'grass3');a.e((xx-7,yy-3,xx+5,yy+1),'grasslit');a.l([(xx-4,yy),(xx-2,yy-3)],'pine3');a.dot(xx+2,yy-2,'flower1');a.dot(xx+3,yy-3,'plaster')
  # The board stands above a woven ground mat, a useful civic gathering place.
  a.p([(273,225),(329,225),(335,252),(270,252)],'water2');a.p([(276,227),(327,227),(331,249),(274,249)],'plaster')
  for yy in(228,234,240,246):a.l([(277,yy),(329,yy)],'dirt3')
  for xx in(279,321):a.l([(xx,228),(xx+2,248)],'water3')
  # Terrace roof planters, cooling pots and hanging work aprons tell habitation.
  for x,y in[(49,52),(62,52),(190,39),(205,39),(359,51),(373,51),(389,51)]:pot(x,y)
  for x,y in[(102,58),(238,49),(422,58)]:
   a.r((x-7,y-6,x+7,y),'wood3');a.e((x-7,y-13,x+1,y-4),'pine3');a.e((x,y-16,x+6,y-3),'pine2');a.l([(x-4,y-11),(x,y-8)],'leaflight')
  a.l([(274,78),(337,84)],'wood2')
  for x,y,c in[(282,80,'water2'),(304,82,'fire2'),(326,84,'plaster')]:a.p([(x-6,y),(x+6,y),(x+5,y+14),(x-4,y+16)],c);a.l([(x-3,y+3),(x-2,y+12)],'white')
  for x in(132,153,177,194):pot(x,201,'gold1')
  shape(144,247,0);shape(192,247,2)
  a.l([(201,159),(201,187),(222,187)],'gold1',4);a.l([(202,161),(202,186),(222,186)],'gold3',1)
  for x,y in[(42,204),(372,200),(442,203)]:pot(x,y);a.l([(x,y-7),(x,y-14)],'pine2');a.p([(x,y-10),(x-6,y-13),(x-4,y-8)],'pine3')
  a.r((287,193,322,199),'wood2');a.r((289,191,319,197),'plaster')
  for i,c in enumerate(['fire2','pine3','water2','gold2']):a.r((291+i*7,192,295+i*7,195),c)
 elif area==39:
  # Leaf nibbles + moved tray, ribbon + sheltered shadow, tracks + bubbles.
  for x,y in[(78,195),(87,192),(96,197)]:a.l([(x-3,y),(x,y-3),(x+4,y)],'pine1');a.dot(x,y-2,'dirt4');a.dot(x+2,y-1,'dirt4')
  for x,y in[(88,218),(93,223),(100,228),(281,106),(291,104),(298,102)]:footprint(x,y)
  a.p([(382,191),(399,191),(404,198),(390,202)],'purple1');a.l([(397,181),(403,186),(399,192),(405,196)],'pine3',2);a.l([(403,186),(408,184)],'pine3')
  for x,y in[(300,91),(307,89),(311,95)]:a.e((x-2,y-2,x+2,y+2),'water4');a.dot(x,y,'water2')
  for x,y in[(27,43),(30,157),(26,202),(453,168),(443,273),(20,286)]:
   a.p([(x-8,y+3),(x-7,y-3),(x,y-6),(x+8,y-1),(x+5,y+6)],'stone2');a.l([(x-6,y-3),(x,y-5),(x+6,y-1)],'stone5');a.dot(x-2,y,'stone1');a.dot(x+3,y+2,'stone1')
  for x in range(160,264,16):a.l([(x,13),(x+10,13)],'stone5');a.l([(x+2,17),(x+13,17)],'purple1')
  for x in(200,224,248,272):a.l([(x,198),(x+6,198)],'water2');a.p([(x+5,196),(x+8,198),(x+5,200)],'water2')
 elif area==40:
  for x in(55,70,83,154,169,184):pot(x,30)
  for x,y,k in[(48,51,0),(87,51,1),(167,51,2)]:shape(x,y,k)
  a.l([(49,44),(89,44)],'wood2');a.l([(145,44),(187,44)],'wood2')
  a.p([(196,23),(217,23),(217,43),(195,43)],'water2');a.r((198,26,214,39),'pine3');a.l([(205,24),(205,41)],'plaster')
  # Clear shadows underneath high drying racks, with clay coils on wall hooks.
  for x in(17,222):a.l([(x,38),(x,51)],'gold1');a.e((x-3,44,x+3,50),'gold2')
  a.l([(45,85),(118,85)],'wood2');a.l([(80,80),(80,89)],'gold2');a.l([(111,80),(111,89)],'gold2');a.p([(92,82),(99,82),(97,89),(94,89)],'gold3')
  shape(141,84,1,'stone1');shape(173,84,2,'stone1')
  for x,y in[(108,112),(114,110),(124,111)]:a.e((x,y-3,x+6,y+1),'pine3');a.dot(x+2,y-2,'leaflight')
  a.l([(55,105),(87,104),(119,106)],'wood2')
 elif area==41:
  # Undulating cooled tube ribbons and scalloped reflected pools.
  a.l([(11,32),(31,27),(47,33),(57,29)],'stone1',2);a.l([(164,25),(181,32),(195,27),(220,33)],'stone1',2)
  a.p([(40,40),(55,35),(70,39),(72,47),(57,52),(43,48)],'water2');a.l([(44,42),(57,39),(67,41)],'water4')
  a.p([(158,41),(181,38),(201,45),(192,53),(173,55),(160,49)],'water3');a.l([(169,43),(184,42),(194,46)],'water4')
  for x,y in[(18,59),(227,58),(22,145),(211,24)]:a.e((x-5,y-3,x+4,y+3),'moss1');a.dot(x-2,y-2,'leaflight')
  for x in(46,79,111):a.l([(x,53),(x+9,53)],'water2');a.p([(x+7,51),(x+10,53),(x+7,55)],'water2')
  shape(80,108,1);shape(144,108,2)
  for x in(178,183,188,193,198):a.e((x,101,x+2,104),'water2')
  a.l([(50,87),(59,85),(68,87)],'water2');a.l([(157,85),(166,87),(175,85)],'water2')
 else:
  # Inset diagrams, blue refuges and thick decorated top manifolds vary by room.
  for x in(40,72,168,200):a.r((x-7,4,x+7,14),'stone2');a.r((x-5,5,x+5,12),'gold1'if area!=43 else'water2');a.l([(x-4,6),(x+4,6)],'plaster')
  for x in(16,220):a.r((x,23,x+3,47),'stone3');a.l([(x,23),(x,47)],'white')
  if area==42:
   shape(48,81,0,'gold2');shape(192,81,2);a.l([(50,52),(79,52)],'gold1',3);a.p([(76,48),(84,52),(76,56)],'gold3');a.r((94,24,105,38),'water3');a.l([(97,25),(97,36)],'water4')
  elif area==43:
   shape(144,44,2);shape(144,80,0);a.l([(121,52),(121,61),(149,61),(149,49)],'water2',3);a.p([(145,52),(149,46),(153,52)],'water3');a.r((61,22,83,29),'stone2');a.l([(64,24),(79,24)],'water4')
  elif area==44:
   shape(144,44,2);shape(192,81,2);a.l([(140,19),(164,19),(164,27),(193,27)],'gold1',3);a.l([(141,18),(165,18),(165,26),(193,26)],'gold3');a.l([(174,116),(195,116)],'water2')
  else:
   a.p([(100,35),(80,28),(67,30),(84,45)],'plaster');a.p([(139,35),(160,26),(171,30),(153,45)],'plaster');a.p([(116,38),(109,23),(125,23),(128,38)],'gold2')
   for x in(28,205):a.l([(x,47),(x,61),(x+7,65)],'water2',4);a.l([(x-1,47),(x-1,60)],'water4')
   for x in(40,194):shape(x,127,2)

def emit(sprites):
 h='''/* Generated original Magma art: same palette, shared streamed OBJ slots. */
#ifndef EMBERBOND_MAGMA_ART_H
#define EMBERBOND_MAGMA_ART_H
#define MAGMA_ART_FIRST_ROOM 38
#define MAGMA_ART_ROOM_COUNT 8
#define MAGMA_ART_FOOT_RADIUS 5
typedef struct { short x,y,w,h; } MagmaArtRect;
typedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const MagmaArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } MagmaArtRoom;
extern const MagmaArtRoom magma_art_rooms[8];
enum {\n'''+''.join(f' MAGMA_SPR_{n}={i},\n'for i,n in enumerate(NAMES))+f' MAGMA_SPR_COUNT={len(NAMES)}\n}};\nextern const unsigned char magma_sprites[MAGMA_SPR_COUNT][256];\n'
 lines=[];total=0;collision=0
 for r in ROOMS:
  k=r['key'];w=r['width'];ht=r['height'];data=r['art'].im.tobytes();r['bitmap_sha256']=hashlib.sha256(data).hexdigest();assert min(data)>0 and max(data)<len(COLORS)
  for suffix,b in [('',data)]+([('_odd',odd_bitmap(data,w,ht))]if w>240 else[]):
   name='magma_background_'+k+suffix;h+=f'extern const unsigned char {name}[{len(b)}];\n';cbytes(lines,name,b);total+=len(b)
  lines.append(f'static const MagmaArtRect magma_{k}_solids[] = {{\n');lines.extend(' {'+','.join(map(str,s['rect']))+'},\n'for s in r['solids']);lines.append('};\n');total+=8*len(r['solids'])
  rows,bands,stats=collision_bands(r);r['collision_lookup']=stats
  for suffix,values in [('collision_rows',rows),('collision_bands',bands)]:
   lines.append(f'static const unsigned short magma_{k}_{suffix}[{len(values)}] = {{\n')
   for at in range(0,len(values),24):lines.append(' '+','.join(map(str,values[at:at+24]))+',\n')
   lines.append('};\n');total+=2*len(values);collision+=2*len(values)
 lines.append('const unsigned char magma_sprites[MAGMA_SPR_COUNT][256] __attribute__((aligned(4))) = {\n')
 for n in NAMES:
  lines.append(' { /* '+n+' */\n');b=sprites[n].im.tobytes()
  for at in range(0,256,32):lines.append(' '+','.join(map(str,b[at:at+32]))+',\n')
  lines.append(' },\n')
 lines.append('};\nconst MagmaArtRoom magma_art_rooms[8] = {\n')
 for r in ROOMS:
  k=r['key'];odd='magma_background_'+k+'_odd'if r['width']>240 else'0';lines.append(f' {{{r["width"]},{r["height"]},magma_background_{k},{odd},magma_{k}_solids,{len(r["solids"])},magma_{k}_collision_rows,magma_{k}_collision_bands}},\n')
 lines.append('};\n');folder=SRC/'magma_art_data';folder.mkdir(exist_ok=True);chunks=[];buf=''
 for line in lines:
  if len(buf)+len(line)>30000:chunks.append(buf);buf=''
  buf+=line
 if buf:chunks.append(buf)
 for p in folder.glob('*.inc'):p.unlink()
 for i,b in enumerate(chunks):(folder/f'part_{i:03}.inc').write_text(b)
 (SRC/'magma_art.h').write_text(h+'#endif\n');(SRC/'magma_art.c').write_text('#include "magma_art.h"\n'+''.join(f'#include "magma_art_data/part_{i:03}.inc"\n'for i in range(len(chunks))))
 return {'rom_payload_bytes':total+len(NAMES)*256+224,'collision_lookup_bytes':collision,'sprite_bytes':len(NAMES)*256,'permanent_new_obj_bytes':0,'largest_include_bytes':max(map(len,chunks))}

def main():
 ROOMS.clear();OUT.mkdir(exist_ok=True);sprites={n:sprite(n)for n in NAMES};proof={}
 for fn in [town,field]+[lambda i=i:interior(i)for i in range(2,8)]:
  r,a=fn();detail_scene(r,a);a=color_background(a,'forest'if r['id']<40 else'temple')
  for o in r['objects']:
   if o['static_baked']:
    im=sprites[o['kind']].im;mask=Image.frombytes('L',(16,16),bytes(255 if v else 0 for v in im.tobytes()));a.im.paste(im,(o['center'][0]-8,o['center'][1]-8),mask)
  r['art']=a
  proof[r['key']],_=verify_room({**r,'spawns':{**r['spawns'],**{'enemy'+str(i):p for i,p in enumerate(r['enemy_spawns'])}}})
 budget=emit(sprites);(OUT/'sprites').mkdir(exist_ok=True);(OUT/'camera').mkdir(exist_ok=True)
 for n,a in sprites.items():a.im.save(OUT/'sprites'/f'{n.lower()}.png',transparency=0)
 for r in ROOMS:
  r['art'].im.save(OUT/(r['key']+'.png'));stage=r['art'].im.convert('RGB')
  for o in r['objects']:
   if not o['static_baked']:paste_sprite(stage,sprites[o['kind']],*o['center'])
  stage.save(OUT/(r['key']+'_staged.png'))
  for x,y in ([[0,0],[240,0],[0,160],[240,160],[120,80],[120,160],[1,1]]if r['width']>240 else[[0,0]]):stage.crop((x,y,x+240,y+160)).save(OUT/'camera'/f'{r["key"]}_{x}_{y}.png')
 layout={'schema':1,'palette_entries':len(COLORS),'palette_sha256':hashlib.sha256(bytes(PAL)).hexdigest(),'coordinate_contract':'half-open solids; five-pixel-radius square foot; 16px centered actors','rooms':[{k:v for k,v in r.items()if k!='art'}for r in ROOMS],'sprites':{'names':NAMES,'maximum_visible_runtime_actors':20},'generated':budget}
 (OUT/'layout.json').write_text(json.dumps(layout,separators=(',',':'))+'\n');(OUT/'validation.json').write_text(json.dumps({'kind':'static host geometry, not native controller QA','routes':proof,'budget':budget},separators=(',',':'))+'\n')
 (OUT/'contract.json').write_text(json.dumps({'rooms':[{'id':r['id'],'name':r['name'],'size':[r['width'],r['height']],'spawns':r['spawns']}for r in ROOMS]},indent=1)+'\n')
 print(json.dumps(budget))
if __name__=='__main__':main()
