#!/usr/bin/env python3
"""Original Sunlace coastal pixels, geometric code art with the frozen palette.
No external raster, borrowed scene or culturally specific ornament is used.
The authoritative fixture/spawn contracts are inputs, never rewritten here.
"""
from pathlib import Path
import hashlib,json,random,sys
from PIL import Image,ImageDraw
import connected_road_art as roads
sys.dont_write_bytecode=True
from generate_assets import Art,P,PAL,COLORS,color_background
from generate_region import verify_room,odd_bitmap,cbytes,paste_sprite
from generate_northern_region import collision_bands
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/southern_region';SRC=ROOT/'src'
CONTRACT=json.loads((OUT/'contract.json').read_text());SCENE=json.loads((OUT/'scene.json').read_text());ROOMS=[];SPRITES=[]
from southern_region.sprite_art import NAMES,NPCS,sprite
DYNAMIC=NPCS|{'REST','FERRY','HOOD','MIRROR_SLASH','MIRROR_BACK','CLOCK','SHADE_CLOSED','SHADE_OPEN','GATE','WATER_LENS','MACHINE_IDLE','MACHINE_WARN','MACHINE_OPEN'}
# Static neutral fixtures receive small DONE actors at completion. Optical and
# shade states are never baked, so their changing diagonals cannot ghost.
def solid(r,k,b):r['solids'].append({'kind':k,'rect':list(b)})
def ex(r,k,b,p,target):r['exits'].append({'key':k,'rect':list(b),'approach':list(p),'target':target})
def landmark(r,k,b):r['landmarks'].append({'kind':k,'bounds':list(b)})
def ground(a,seed,base='grass3'):
 R=random.Random(seed);a.r((0,0,a.im.width-1,a.im.height-1),base)
 for _ in range(a.im.width*a.im.height//190):
  x=R.randrange(a.im.width);y=R.randrange(a.im.height)
  a.l([(x,y),(x+R.randrange(2,6),y)],R.choice(['grass4','grasslit','grassgold']) if base.startswith('grass') else R.choice(['dirt2','dirt4','plaster']))
def paving(a,b,tone='dirt4'):
 x,y,w,h=b;a.r((x,y,x+w-1,y+h-1),tone)
 for yy in range(y+4,y+h,12):
  a.l([(x,yy),(x+w-1,yy)],'dirt3')
  for xx in range(x+(6 if yy%24 else 0),x+w,24):a.l([(xx,yy),(xx,min(yy+10,y+h-1))],'dirt3')
def path(a,pts,width=24):
 a.l(pts,'dirt1',width+5);a.l(pts,'dirt3',width+2);a.l(pts,'dirt4',width-3)
def sea(a,b,seed=0):
 x,y,w,h=b;a.r((x,y,x+w-1,y+h-1),'water1');R=random.Random(seed)
 for _ in range(w*h//100):
  xx=R.randrange(x,x+w);yy=R.randrange(y,y+h);a.l([(xx,yy),(min(x+w-1,xx+R.randrange(3,13)),yy)],R.choice(['water2','water3','water4']))
def deck(a,b):
 x,y,w,h=b;a.r((x,y,x+w-1,y+h-1),'wood1');a.r((x+2,y,x+w-3,y+h-1),'wood4')
 for yy in range(y,y+h,5):a.l([(x+2,yy),(x+w-3,yy)],'wood2');a.l([(x+3,yy+1),(x+w-4,yy+1)],'wood5')
def runnel(a,pts,width=5):
 a.l(pts,'dirt1',width+6);a.l(pts,'stone5',width+3);a.l(pts,'water2',width);a.l([(x,y-1)for x,y in pts],'water4',1)
def shrub(a,x,y,s=1):
 for dx,dy,rr in[(-8,1,7),(0,-3,9),(8,1,7)]:
  a.e((x+(dx-rr)*s,y+(dy-rr)*s,x+(dx+rr)*s,y+(dy+rr)*s),'pine2');a.e((x+(dx-rr+2)*s,y+(dy-rr)*s,x+(dx+rr-1)*s,y+(dy+2)*s),'pine4');a.l([(x+(dx-3)*s,y+(dy-rr+2)*s),(x+(dx+2)*s,y+(dy-rr+2)*s)],'leaflight')
def frond(a,r,x,y,scale=1,collision=True):
 # A bent trunk and radial palm-like blades, designed anew for this coastline.
 def pts(v):return[(int(x+px*scale),int(y+py*scale))for px,py in v]
 a.e((x-17*scale,y-5*scale,x+18*scale,y+7*scale),'shadowsoft')
 a.l(pts([(0,0),(-3,-14),(1,-35)]),'wood1',max(2,int(6*scale)));a.l(pts([(-1,-2),(-4,-14),(0,-35)]),'barklight',max(1,int(2*scale)))
 for dy in(-5,-13,-21):a.l(pts([(-4,dy),(0,dy+1)]),'wood2')
 for xx,yy in[(-25,-35),(-19,-48),(-2,-53),(19,-48),(29,-31),(16,-21),(-19,-22)]:
  a.p(pts([(0,-35),(xx//2,yy-5),(xx,yy),(xx//2,yy+3)]),'pine1');a.l(pts([(0,-36),(xx//2,yy-3),(xx,yy)]),'pine4',max(1,int(3*scale)));a.l(pts([(0,-37),(xx,yy)]),'leaflight')
 a.e((x-4*scale,y-38*scale,x+4*scale,y-31*scale),'gold1')
 if collision:solid(r,'living_frond_trunk',(x-4,y-13,8,15))
 landmark(r,'living_coastal_frond',[int(x-29*scale),int(y-54*scale),int(58*scale),int(62*scale)])
def shade_tree(a,r,x,y,scale=1,collision=True):
 a.e((x-24*scale,y-8*scale,x+28*scale,y+9*scale),'shadowsoft');a.l([(x,y),(x-2,y-28*scale)],'wood1',max(3,int(8*scale)));a.l([(x-1,y-2),(x-3,y-25*scale)],'wood3',max(1,int(3*scale)))
 for dx,dy in[(-10,-24),(12,-24),(0,-38)]:
  a.l([(x,y-14*scale),(x+dx*scale,y+dy*scale)],'wood2',max(1,int(4*scale)))
  shrub(a,x+dx*scale,y+dy*scale,scale*1.1)
 if collision:solid(r,'living_shade_tree_trunk',(x-5,y-16,10,18))
 landmark(r,'living_wide_canopy',[int(x-32*scale),int(y-54*scale),int(64*scale),int(63*scale)])
def awning(a,x,y,w,depth=14):
 a.p([(x,y),(x+w,y),(x+w+5,y+depth),(x-4,y+depth)],'fire0')
 for dx in range(0,w,12):a.p([(x+dx,y),(x+min(w,dx+6),y),(x+min(w+3,dx+8),y+depth),(x+dx-2,y+depth)],'fire2')
 a.l([(x-4,y+depth),(x+w+5,y+depth)],'fire1',2)
 for xx in(x-3,x+w+3):a.l([(xx,y+depth),(xx,y+depth+15)],'wood1',2);a.dot(xx,y+depth,'wood5')
def shutter(a,x,y,w=13,h=18):
 a.r((x-2,y-2,x+w+2,y+h+2),'gold1');a.r((x,y,x+w,y+h),'water0');a.r((x+1,y+1,x+w-1,y+h-1),'water2')
 for xx in range(x+2,x+w,3):a.l([(xx,y+2),(xx,y+h-2)],'water4')
 a.l([(x,y+h//2),(x+w,y+h//2)],'water1',2)
def plaster_house(a,r,x,y,w,h,door=None,canopy=False):
 # Flat, receding parapets and massive lime-colored piers, no gable roofs.
 a.p([(x+5,y+15),(x+w+10,y+15),(x+w+12,y+h+8),(x+5,y+h+8)],'purple1')
 a.r((x,y+16,x+w,y+h),'gold1');a.r((x+3,y+17,x+w-3,y+h-2),'plaster');a.r((x+4,y+18,x+w-5,y+25),'dirt4')
 a.r((x-3,y+11,x+w+3,y+19),'wood3');a.r((x-3,y+8,x+w+3,y+13),'dirt4')
 a.r((x+7,y,x+w-10,y+10),'gold1');a.r((x+9,y+1,x+w-12,y+7),'plaster');a.l([(x+8,y),(x+w-11,y)],'white',2)
 a.r((x+20,y-6,x+w-25,y+1),'dirt4');a.l([(x+20,y-6),(x+w-25,y-6)],'white',2)
 # Small drain spouts, deliberately geometric civic details.
 a.r((x+6,y+14,x+9,y+29),'stone3');a.r((x+w-10,y+14,x+w-7,y+25),'stone3')
 for xx in range(x+16,x+w-13,32):shutter(a,xx,y+34,12,17)
 dd=door if door is not None else x+w//2
 a.r((dd-12,y+h-30,dd+12,y+h),'gold1');a.r((dd-9,y+h-29,dd+9,y+h),'wood0');a.r((dd-6,y+h-26,dd+8,y+h),'deep');a.l([(dd-8,y+h-26),(dd-8,y+h-1)],'wood3');a.r((dd-11,y+h,dd+12,y+h+3),'stone5')
 if canopy:awning(a,x+10,y+h-38,w-20,10)
 for yy in range(y+61,y+h-8,16):a.l([(x+5,yy),(x+15,yy)],'dirt3');a.l([(x+w-14,yy+6),(x+w-5,yy+6)],'dirt3')
 solid(r,'stepped_plaster_mass',(x-3,y-6,w+7,h+7));landmark(r,'original_stepped_plaster_courtyard',[x-4,y-6,w+18,h+16])
def new(i):
 c=CONTRACT['rooms'][i];w,h=c['size'];r={**c,'width':w,'height':h,'solids':[],'dynamic_rectangles':[],'objects':[],'exits':[],'landmarks':[],'camera_crops':[[0,0],[240,0],[0,160],[240,160],[120,80],[1,1]] if i<2 else [[0,0]]};ROOMS.append(r)
 a=Art(w,h,'dirt4')
 for x in(0,w-8):solid(r,'world_edge',(x,0,8,h))
 if i<2:
  gap=304 if i==0 else 240
  solid(r,'north_edge_left',(8,0,gap-24,8));solid(r,'north_edge_right',(gap+16,0,w-gap-24,8))
  solid(r,'south_edge_left',(8,h-8,216,8));solid(r,'south_edge_right',(256,h-8,216,8))
 else:
  # Beacon y32 in the loft remains accessible at y48; top masonry ends y24.
  solid(r,'upper_wall',(8,0,224,24));solid(r,'south_left',(8,156,96,4));solid(r,'south_right',(136,156,96,4))
  ex(r,'south',(108,144,24,16),(120,144),30 if i==2 else 31 if i in(3,4) else 29+i)
  paving(a,(8,24,224,132),'dirt4')
 r['enemy_spawns']={1:[[208,264],[320,272],[432,128],[208,64],[336,64]],3:[[80,120],[184,136]]}.get(i,[])
 for o in SCENE['objects'][i]:
  k=o['kind'];r['objects'].append({**o,'sprite':k,'static_baked':k not in DYNAMIC and k!='CREATURE'})
 return r,a

def town():
 r,a=new(0);ground(a,930,'dirt3');paving(a,(12,138,456,140));path(a,[(304,0),(304,140),(268,164),(240,216),(240,290)],30)
 roads.draw(a,30,P)
 # Waterfront terraces continue around a pier, with open views to clear sea.
 sea(a,(8,280,464,32),31);a.r((8,272,471,279),'stone2');a.l([(8,271),(471,271)],'stone5',3)
 solid(r,'harbor_water_west',(8,280,216,32));solid(r,'harbor_water_east',(256,280,216,32));deck(a,(224,267,32,53))
 for xx in(220,257):
  for yy in(278,301):a.r((xx,yy,xx+2,yy+8),'wood1');a.r((xx,yy,xx+2,yy+1),'wood5')
 # Inland town is stepped upward, with shaded civic courtyards below.
 plaster_house(a,r,32,32,104,96,80,False);plaster_house(a,r,176,25,88,96,220,True);plaster_house(a,r,344,32,112,92,400,True)
 a.r((66,128,94,134),'stone3');a.l([(66,132),(94,132)],'stone5',2)
 # A short outdoor stair rises to the loft without blocking its approach.
 for yy in(133,137,141):a.l([(69,yy),(91,yy)],'dirt1');a.l([(70,yy-1),(90,yy-1)],'stone5')
 runnel(a,[(143,104),(143,137),(169,146),(169,251),(217,259),(220,276)],3)
 runnel(a,[(319,108),(319,140),(367,150),(367,241),(398,259),(406,278)],3)
 # Shaded central civic rain court. Collector is scenery north of interaction lanes.
 a.r((194,129,254,153),'purple1');a.r((192,126,251,149),'dirt4');a.e((208,125,237,146),'stone2');a.e((211,127,234,142),'stone5');a.e((215,129,231,139),'water2');a.l([(216,130),(228,130)],'watergleam')
 solid(r,'civic_rain_collector',(208,125,30,20));landmark(r,'shaded_civic_rain_courtyard',[182,119,80,35])
 # Market canopies sit north of their shaded workstations, leaving foot routes.
 for x in(270,302,334):awning(a,x,185,21,9)
 a.r((272,199,288,202),'wood3');a.r((304,199,320,202),'wood3');a.r((336,199,352,202),'wood3')
 # Trees bracket clear openings rather than hiding doors or NPCs.
 frond(a,r,24,126,.85);shade_tree(a,r,438,159,.75);frond(a,r,282,86,.8);shade_tree(a,r,36,252,.75)
 for x,y in[(19,186),(449,231),(422,267),(93,251)]:shrub(a,x,y,.55)
 # A bright ferry with a striped cover and plainly open landing at center.
 a.p([(298,291),(348,286),(369,298),(344,309),(306,306)],'wood1');a.p([(304,292),(346,290),(361,299),(343,305),(309,302)],'plaster');a.l([(310,299),(353,299)],'wood3',2);awning(a,314,283,29,9)
 # Fictional fish shop board: a creature shape, never real script or sacred art.
 a.r((383,127,415,139),'wood1');a.r((385,128,413,137),'plaster');a.e((392,130,405,135),'water2');a.p([(405,132),(410,129),(410,136)],'water2');a.dot(395,131,'ink')
 for x,y in[(24,196),(416,210)]:a.r((x,y,x+20,y+4),'wood2');a.l([(x,y),(x+20,y)],'wood5');solid(r,'low_court_bench',(x,y,21,5))
 # Paired delivery trays are readable work sites, with a removable central tie.
 for x,y in[(128,248),(384,248)]:
  deck(a,(x-15,y-11,30,20));a.r((x-13,y-9,x-8,y-3),'plaster');a.r((x+8,y-9,x+13,y-3),'fire2');a.l([(x-7,y-5),(x+7,y+4)],'wood1');a.l([(x+7,y-5),(x-7,y+4)],'wood1')
 ex(r,'commons',(288,0,32,16),(304,16),31);ex(r,'loft',(68,125,24,16),(80,148),32);ex(r,'ferry',(224,256,32,32),(240,284),22)
 return r,a

def field():
 r,a=new(1);ground(a,931);sea(a,(8,8,34,304),48);solid(r,'living_mangrove_water',(8,8,28,304));a.l([(42,10),(47,75),(40,138),(50,198),(41,274),(45,311)],'water4',4)
 # A winding upland walking network, independent of companion ownership.
 for pts,w in[([(240,320),(240,269),(208,227),(240,182),(299,147),(361,112),(400,72)],29), ([(240,184),(176,163),(116,132),(80,104)],24), ([(208,225),(160,245),(80,264)],24), ([(112,130),(152,99),(192,96),(248,103),(304,99),(359,111)],23), ([(240,228),(301,234),(358,265),(421,266)],23)]:path(a,pts,w)
 # Shallow water remains walkable; raised planks make crossing direction clear.
 runnel(a,[(216,60),(219,110),(245,131),(272,176),(311,191),(336,231),(345,276),(401,297)],7)
 runnel(a,[(328,87),(319,111),(273,139),(257,144),(224,144),(181,118)],5)
 deck(a,(227,164,38,20));deck(a,(294,222,30,24));deck(a,(230,91,41,15))
 # White dune shoulder and hollow doorway retain the exact approach at80,104.
 a.p([(53,38),(68,28),(107,30),(122,51),(115,75),(100,87),(55,83),(45,67)],'dirt1');a.p([(54,37),(70,30),(105,33),(119,52),(111,73),(99,80),(56,77),(49,65)],'white')
 a.r((68,56,93,82),'stone2');a.r((71,60,90,82),'wood0');a.r((74,63,88,82),'deep');a.l([(69,58),(69,80)],'stone5');solid(r,'chalkspring_entrance',(49,30,66,53));landmark(r,'white_dune_hollow',[45,28,79,59])
 # Dune cut habitat, adjacent to visible manual drain and pawprints.
 a.p([(117,50),(176,52),(184,79),(169,95),(134,95),(114,83)],'dirt3');a.l([(120,55),(154,57),(178,67)],'white',3)
 for x,y in[(152,105),(155,111),(160,116)]:a.dot(x,y,'wood2');a.dot(x+3,y-1,'wood2')
 plaster_house(a,r,364,10,72,45,400,False)
 # Mangroves have live leaves and visible stilt roots, never felled stumps.
 for x,y in[(30,75),(34,143),(31,218),(30,300)]:
  a.l([(x,y-9),(x-11,y+7)],'wood2',2);a.l([(x,y-9),(x+12,y+4)],'wood2',2);shade_tree(a,r,x,y,.6,False)
 deck(a,(48,119,16,103));landmark(r,'live_mangrove_fringe',[8,22,56,282])
 for x,y,s in[(198,56,.8),(347,64,.7),(448,133,.9),(195,298,.8),(336,285,.75),(446,298,.85)]:frond(a,r,x,y,s)
 shade_tree(a,r,288,84,.7,False);a.l([(267,96),(309,96)],'wood3',3)
 # Shaded crab alcove, open civic inspection stand, rest canopy.
 awning(a,372,196,57,8);a.l([(366,158),(438,158)],'wood3',3)
 for x in(366,438):a.r((x,157,x+3,170),'wood2')
 awning(a,61,220,39,11);a.r((64,236,70,239),'wood2');a.r((91,236,97,239),'wood2')
 for x,y in[(111,219),(174,221),(328,157),(369,296),(91,293),(174,37),(450,190),(64,171)]:shrub(a,x,y,.55)
 # Living root supports tie into a visible low bough; no rail/cart vocabulary.
 a.l([(116,199),(129,187),(148,185),(175,139)],'wood2',3);a.l([(119,199),(131,189),(148,188),(178,140)],'leaflight')
 ex(r,'town',(224,304,32,16),(240,300),30);ex(r,'hollow',(68,76,24,16),(80,104),33);ex(r,'intake',(388,48,24,16),(400,72),34)
 return r,a

def wall(a,kind='plaster'):
 a.r((8,0,231,23),'gold1');a.r((10,3,229,20),'plaster' if kind=='plaster' else 'stone5');a.l([(10,22),(229,22)],'white',2)
 for x in(9,228):a.r((x,24,x+2,155),'wood3');a.l([(x+1,25),(x+1,153)],'plaster')
 for x in(42,106,170):shutter(a,x,5,26,13)
 for xx in(8,136):a.r((xx,156,xx+95,159),'stone2');a.l([(xx,155),(xx+95,155)],'stone5')
 for yy in(145,150,155):a.l([(108,yy),(131,yy)],'stone3');a.l([(109,yy-1),(130,yy-1)],'stone5')
def emitter(a,x,y,d='east'):
 a.r((x-10,y-12,x+3,y+10),'stone2');a.r((x-8,y-10,x+1,y+8),'plaster');a.e((x-5,y-6,x+5,y+5),'gold1');a.e((x-3,y-4,x+4,y+3),'gold4');a.p([(x+5,y-3),(x+12,y),(x+5,y+3)],'fire2')
def optical_floor(a,pts):
 # Inset measuring lines are thin and quiet; live ray is a runtime overlay.
 for p,q in zip(pts,pts[1:]):a.l([p,q],'stone3')
 for x,y in pts:a.e((x-9,y-7,x+9,y+7),'dirt2');a.e((x-7,y-5,x+7,y+5),'dirt4')
def shortcut_arch(a,r,x,y,key,target,spawn,requirement):
 # Neutral inset behind a runtime gate. Its floor stays physically traversable.
 a.r((x-14,y-22,x+14,y+11),'gold1');a.r((x-12,y-20,x+12,y+9),'plaster');a.r((x-9,y-18,x+9,y+8),'wood0');a.r((x-7,y-17,x+7,y+8),'deep');a.l([(x-12,y-21),(x+12,y-21)],'white',2)
 for yy in(y+10,y+13):a.l([(x-12,yy),(x+12,yy)],'stone3');a.l([(x-11,yy-1),(x+11,yy-1)],'stone5')
 a.p([(x-4,y-22),(x,y-26),(x+4,y-22)],'water2')
 ex(r,key,(x-10,y-9,20,20),(x,y+16),target);r['exits'][-1].update({'target_spawn':spawn,**requirement})

def interior(i):
 r,a=new(i);wall(a)
 if i==2:
  # Open upstairs workroom: timber planks, folded cloth, airy wall windows.
  a.r((12,24,227,154),'wood4')
  for yy in range(28,154,7):a.l([(12,yy),(227,yy)],'wood3');a.l([(13,yy+1),(226,yy+1)],'wood5')
  for xx in range(30,224,32):
   for yy in range(30+(xx%3)*6,150,28):a.l([(xx,yy),(xx,yy+5)],'wood2')
  a.p([(154,24),(216,24),(211,109),(183,132),(132,116)],'dirt4')
  awning(a,18,1,58,15);awning(a,153,1,62,15)
  # Screen rails and cords are display mountings, not blocking room partitions.
  a.l([(29,64),(210,64)],'wood2',2);a.l([(29,65),(210,65)],'wood5')
  for xx in(29,209):a.r((xx,62,xx+2,108),'wood1')
  a.r((13,31,22,107),'wood2');a.r((14,33,20,105),'wood3');solid(r,'loft_side_storage',(13,31,9,76))
  for yy,c in[(39,'water2'),(54,'fire2'),(72,'plaster'),(89,'water3')]:a.r((13,yy,21,yy+6),c);a.l([(14,yy),(20,yy)],'white')
  a.l([(29,110),(80,110)],'wood2',2);a.r((88,119,105,125),'plaster');a.l([(90,120),(102,120)],'fire2',2)
  landmark(r,'airy_awning_workplace',[13,24,214,104]);shortcut_arch(a,r,208,64,'market_shortcut',30,4,{'requires_quest_ready':29})
 elif i==3:
  # Chalk cave has organic white ledges and three clearly separated wet runnels.
  a.r((8,0,231,23),'stone3');a.p([(8,25),(18,4),(60,0),(93,12),(133,2),(169,14),(205,1),(231,13),(231,28)],'stone5');a.l([(10,24),(29,17),(59,23),(91,17),(130,22),(169,17),(205,23),(229,19)],'white',3)
  a.r((12,26,227,154),'dirt4')
  for x in(82,137):
   a.p([(x,35),(x+12,37),(x+8,59),(x+10,76),(x+7,97),(x+12,116),(x+7,137),(x-5,143),(x-7,126),(x-3,103),(x-6,84),(x-2,62)],'stone3');a.l([(x+2,37),(x+2,62),(x,86),(x+2,112),(x-2,136)],'water3',6);a.l([(x,38),(x,61),(x-2,84),(x,111),(x-4,135)],'watergleam',2)
  a.e((83,121,99,141),'water2');a.e((135,117,150,141),'water3')
  for x in(56,112,168):a.l([(x,51),(x,111)],'dirt2',3);a.l([(x-7,62),(x+8,62)],'white');a.l([(x-7,93),(x+8,93)],'white')
  a.p([(181,25),(224,25),(224,107),(198,99),(191,70)],'sun');a.r((195,7,218,20),'water1');a.r((198,8,215,18),'water4')
  for x,y in[(16,44),(21,88),(218,35)]:a.p([(x,y),(x+8,y-5),(x+11,y+3),(x+3,y+6)],'white')
  landmark(r,'chalk_spring_runnels_and_dry_ledges',[12,26,216,118])
 elif i==4:
  # Intake: one broad light lane, vertical service pit and civic water-lens dock.
  a.r((16,32,49,114),'stone2');a.r((18,34,45,110),'water1')
  for yy in range(35,110,9):a.l([(19,yy),(44,yy)],'water3')
  a.r((19,44,38,69),'plaster');emitter(a,32,56);solid(r,'intake_water_trough',(16,76,30,37))
  a.p([(46,45),(106,45),(106,68),(49,69)],'gold4');optical_floor(a,[(32,56),(112,56),(112,104)])
  a.r((136,29,179,42),'stone2');a.r((138,30,177,38),'plaster');a.r((148,30,166,35),'water3');solid(r,'intake_upper_service_basin',(136,29,44,14))
  a.l([(112,106),(146,112),(157,111)],'water3',3);a.e((148,105,166,117),'stone3');a.e((151,107,163,114),'water4')
  a.r((204,25,213,43),'water0');a.r((206,26,211,43),'deep');landmark(r,'single_bend_light_intake',[18,32,160,86])
 elif i==5:
  # Split-Shade: two shallow separated terrace levels with a broad return aisle.
  a.r((15,28,191,38),'stone3');a.r((17,29,188,33),'plaster');a.l([(17,37),(188,37)],'white');solid(r,'splitshade_upper_planter',(15,28,176,9))
  for x in range(22,188,17):a.l([(x,32),(x+8,32)],'pine4');a.dot(x+3,30,'leaflight')
  a.p([(22,40),(93,40),(93,82),(22,82)],'gold4');a.p([(130,88),(219,88),(219,116),(130,116)],'purple3')
  a.l([(14,85),(82,85)],'stone3',4);a.l([(140,85),(224,85)],'stone3',4);a.l([(14,83),(82,83)],'white');a.l([(140,83),(224,83)],'white')
  # A twelve-pixel-high terrace lip is visual only, crossed via broad steps.
  for y in(83,86,89):a.l([(86,y),(134,y)],'stone4')
  optical_floor(a,[(32,56),(80,56),(112,56),(112,104),(192,104)]);emitter(a,32,56)
  a.e((74,50,86,62),'wood1');a.e((76,52,84,60),'gold4');a.p([(78,55),(82,55),(80,59)],'water2')
  # Hinge mounting connects both ray-height arms; moving arm is not baked.
  a.l([(152,56),(176,80),(152,104)],'stone3');a.e((172,76,180,84),'gold1')
  landmark(r,'two_terrace_splitshade_walk',[14,28,210,91])
 elif i==6:
  # Tree gallery: a live trunk blocks the direct optical path and has a real
  # collision island; the two-turn light route is open west then north.
  a.r((16,27,221,35),'wood1');a.r((18,28,219,32),'wood4')
  for x in range(21,220,12):a.l([(x,27),(x,34)],'wood2')
  a.r((17,37,25,108),'plaster');a.r((216,37,223,111),'plaster');solid(r,'gallery_west_pier',(17,37,8,57));solid(r,'gallery_east_pier',(216,37,7,58))
  a.e((104,81,150,109),'stone3');a.e((107,82,147,105),'dirt1');a.e((112,85,142,103),'grass2')
  a.p([(112,97),(117,76),(121,70),(133,75),(136,100),(128,96),(124,87),(119,98)],'wood1');a.l([(116,95),(120,79),(122,74)],'wood4',2);a.l([(131,97),(130,81),(126,77)],'wood3',3)
  for x,y,s in[(108,65,.95),(134,61,.85),(122,49,1.0)]:shrub(a,x,y,s)
  solid(r,'living_optical_tree',(112,72,24,28));landmark(r,'living_tree_optical_obstruction',[89,34,65,75])
  optical_floor(a,[(32,104),(80,104),(80,48),(192,48)]);emitter(a,32,104)
  a.l([(152,48),(176,104),(152,104)],'stone3');a.e((172,100,180,108),'gold1');shortcut_arch(a,r,208,112,'field_shortcut',31,1,{'requires_sunwell_objectives':4})
 elif i==7:
  # Open crown is a pale terraced conservatory roof, sea all around its edges.
  sea(a,(0,0,240,160),938);a.p([(19,26),(51,10),(187,10),(221,29),(227,131),(211,159),(29,159),(13,133)],'purple1');a.p([(19,24),(51,9),(187,9),(221,28),(223,129),(209,155),(31,155),(17,131)],'plaster');a.p([(24,32),(54,17),(184,17),(214,32),(216,128),(204,148),(36,148),(24,128)],'stone5')
  for yy in range(38,145,15):a.l([(25,yy),(214,yy)],'stone4')
  # Transparent-looking lens chassis is only a surrounding structural frame.
  a.e((74,30,166,98),'stone3');a.e((79,33,161,95),'gold1');a.e((84,36,156,90),'plaster');a.e((91,41,149,86),'water1');a.e((94,42,146,82),'water4');a.p([(100,44),(124,42),(111,80),(99,75)],'watergleam');a.l([(120,35),(120,91)],'stone2',2);a.l([(83,63),(157,63)],'stone2',2)
  for x in(66,170):a.r((x,33,x+4,99),'gold1');a.l([(x+1,34),(x+1,98)],'gold4')
  a.l([(68,34),(173,34)],'wood3',3)
  # Safe side lanes are broad, unlike the telegraphed central attack lane.
  a.l([(54,111),(86,111)],'water2',2);a.l([(151,111),(177,111)],'water2',2)
  for x in(40,198):a.r((x,26,x+3,45),'wood2');a.l([(x,27),(x+3,27)],'white')
  landmark(r,'open_sea_conservatory_lens_crown',[18,10,206,140])
  for b in[(8,24,11,108),(222,24,10,108),(8,132,16,12),(217,132,15,12),(8,144,24,12),(208,144,24,12)]:solid(r,'crown_outer_sea',b)
 # Exit threshold remains physically open regardless of every optical state.
 if i!=7:
  for y in(146,151):a.l([(108,y),(131,y)],'stone3')
 return r,a


def fixtures(r,a,lookup):
 for o in r['objects']:
  x,y=o['center'];n=o['kind']
  if n=='CREATURE':continue
  if o['static_baked']:
   im=lookup[n].im;mask=Image.frombytes('L',(16,16),bytes(255 if v else 0 for v in im.tobytes()));a.im.paste(im,(x-8,y-8),mask)
  elif n not in NPCS and n not in{'REST','FERRY','MACHINE_IDLE'}:
   a.e((x-10,y+3,x+10,y+9),'stone3');a.l([(x-8,y+4),(x+8,y+4)],'stone5')
 # Main-ray shade blocking arms occupy their exact logical horizontal lane.
 # The two sockets are scenery; active screen strips are runtime state art.
 if r['id'] in(35,36):
  for x,y in([(152,56),(152,104)]if r['id']==35 else[(152,48),(152,104)]):a.e((x-3,y-3,x+3,y+3),'stone3');a.dot(x,y,'gold3')
 a.d=ImageDraw.Draw(a.im)

def emit():
 h='''/* Generated original Southern chapter art. */
#ifndef EMBERBOND_SOUTH_ART_H
#define EMBERBOND_SOUTH_ART_H
#define SOUTH_ART_FIRST_ROOM 30
#define SOUTH_ART_ROOM_COUNT 8
#define SOUTH_ART_FOOT_RADIUS 5
typedef struct { short x,y,w,h; } SouthArtRect;
typedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const SouthArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } SouthArtRoom;
extern const SouthArtRoom south_art_rooms[SOUTH_ART_ROOM_COUNT];
/* Exact radius-five collision: rows[y] is a u16 offset into records
 * [count,lo0,hi0,...], with sorted merged half-open x intervals. */
enum {
'''+''.join(f' SOUTH_SPR_{n} = {i},\n'for i,n in enumerate(NAMES))+f' SOUTH_SPR_COUNT = {len(NAMES)}\n}};\nextern const unsigned char south_sprites[SOUTH_SPR_COUNT][256];\n'
 lines=[];total=0;collision_bytes=0;alignment=0;bitmap_bytes=0
 for r in ROOMS:
  k=r['key'];w=r['width'];ht=r['height'];data=r['art'].im.tobytes();r['bitmap_sha256']=hashlib.sha256(data).hexdigest();assert min(data)>0 and max(data)<len(COLORS)
  for suffix,b in [('',data)]+([('_odd',odd_bitmap(data,w,ht))]if w>240 else[]):
   pad=(-total)&3;total+=pad;alignment+=pad;name='south_background_'+k+suffix;h+=f'extern const unsigned char {name}[{len(b)}];\n';cbytes(lines,name,b);total+=len(b);bitmap_bytes+=len(b)
  lines.append(f'const SouthArtRect south_{k}_solids[] = {{\n');lines.extend(' {'+','.join(map(str,s['rect']))+'},\n'for s in r['solids']);lines.append('};\n');total+=8*len(r['solids'])
  rows,bands,stats=collision_bands(r);r['collision_lookup']=stats
  for suffix,values in [('collision_rows',rows),('collision_bands',bands)]:
   lines.append(f'static const unsigned short south_{k}_{suffix}[{len(values)}] = {{\n')
   for at in range(0,len(values),24):lines.append(' '+','.join(map(str,values[at:at+24]))+',\n')
   lines.append('};\n');total+=2*len(values);collision_bytes+=2*len(values)
 pad=(-total)&3;total+=pad;alignment+=pad;lines.append('const unsigned char south_sprites[SOUTH_SPR_COUNT][256] __attribute__((aligned(4))) = {\n')
 for n,a in SPRITES:
  lines.append(' { /* '+n+' */\n');data=a.im.tobytes()
  for at in range(0,256,32):lines.append(' '+','.join(map(str,data[at:at+32]))+',\n')
  lines.append(' },\n')
 lines.append('};\nconst SouthArtRoom south_art_rooms[SOUTH_ART_ROOM_COUNT] = {\n')
 for r in ROOMS:
  k=r['key'];odd='south_background_'+k+'_odd'if r['width']>240 else '0';lines.append(f' {{{r["width"]},{r["height"]},south_background_{k},{odd},south_{k}_solids,{len(r["solids"])},south_{k}_collision_rows,south_{k}_collision_bands}},\n')
 lines.append('};\n');folder=SRC/'south_art_data';folder.mkdir(exist_ok=True);chunks=[];buf=''
 for line in lines:
  if len(buf)+len(line)>30000:chunks.append(buf);buf=''
  buf+=line
 if buf:chunks.append(buf)
 for old in folder.glob('*.inc'):old.unlink()
 for i,buf in enumerate(chunks):(folder/f'part_{i:03}.inc').write_text(buf)
 (SRC/'south_art.h').write_text(h+'#endif\n');(SRC/'south_art.c').write_text('#include "south_art.h"\n'+''.join(f'#include "south_art_data/part_{i:03}.inc"\n'for i in range(len(chunks))))
 return {'bitmap_bytes':bitmap_bytes,'rom_payload_bytes':total+len(SPRITES)*256+224,'collision_lookup_bytes':collision_bytes,'alignment_bytes':alignment,'arm32_room_table_bytes':224,'largest_include_bytes':max(map(len,chunks)),'sprite_bytes':len(SPRITES)*256}

def creature_preview(o):
 # Use Southern authored form pixels when the parallel creature work is ready.
 # Otherwise a clearly documented footprint-only staging mark is preview-only.
 name={25:'tangleaper',28:'duneroll',79:'skimkip',81:'warmcroak',83:'shellwaddle',85:'clipmantis',87:'swaylemur',89:'rillnewt',91:'glimmerbat',93:'needletrot'}.get(o.get('form'),'')
 p=ROOT/'assets/southern_creatures'/f'{name}_walk.png'
 if p.exists():
  im=Image.open(p);im.seek(0);art=Art(16,16,'transparent');art.im=im.crop((0,0,16,16)).convert('P');return art,True
 a=Art(16,16,'transparent');a.e((3,10,7,13),'pine1');a.e((9,6,13,9),'pine1');a.dot(4,8,'pine3');a.dot(10,4,'pine3');return a,False

def main():
 ROOMS.clear();SPRITES.clear();SPRITES.extend((n,sprite(n))for n in NAMES);lookup=dict(SPRITES)
 for fn in[town,field]+[lambda i=i:interior(i)for i in range(2,8)]:
  r,a=fn();roads.open_borders(r);a=color_background(a,'forest'if r['id']<34 else'temple');fixtures(r,a,lookup);r['art']=a
 proofs={}
 for r in ROOMS:
  check={**r,'spawns':{**r['spawns'],**{'enemy_'+str(j):p for j,p in enumerate(r['enemy_spawns'])}}}
  proofs[r['key']],_=verify_room(check)
 budget=emit();(OUT/'sprites').mkdir(exist_ok=True);(OUT/'camera').mkdir(exist_ok=True)
 for n,a in SPRITES:a.im.save(OUT/'sprites'/f'{n.lower()}.png',transparency=0)
 preview=Image.new('RGB',(976,820),(26,54,62));draw=ImageDraw.Draw(preview);draw.text((8,8),'SUNLACE / original Southern coastal art / native staged pixels',(255,237,193))
 staged_creatures=[]
 for i,r in enumerate(ROOMS):
  a=r['art'];a.im.save(OUT/(r['key']+'.png'));stage=a.im.convert('RGB')
  for o in r['objects']:
   if o['kind']=='CREATURE':
    pic,authored=creature_preview(o);paste_sprite(stage,pic,*o['center']);staged_creatures.append({'room':r['id'],'form':o['form'],'authored':authored});continue
   if not o['static_baked']:paste_sprite(stage,lookup[o['sprite']],*o['center'])
  stage.save(OUT/(r['key']+'_staged.png'))
  for x,y in r['camera_crops']:stage.crop((x,y,x+240,y+160)).save(OUT/'camera'/f'{r["key"]}_{x}_{y}.png')
  pos=(8+i*488,36)if i<2 else(8+(i-2)%4*244,389+(i-2)//4*200)
  draw.text((pos[0],pos[1]-14),r['name'],(255,237,193));preview.paste(stage,pos)
 (ROOT/'build').mkdir(exist_ok=True);preview.save(ROOT/'build/southern_preview_native.png')
 layout={'schema':1,'palette':{'entries':len(COLORS),'sha256':hashlib.sha256(bytes(PAL)).hexdigest()},'coordinate_contract':'world centers; half-open rectangles; exact five-pixel foot; actors x-8,y-8','sprites':{'names':NAMES,'indices':{n:i for i,n in enumerate(NAMES)},'size':[16,16],'maximum_visible_runtime_actors':20},'rooms':[{k:v for k,v in r.items()if k!='art'}for r in ROOMS],'generated':budget}
 # Compact JSON stays portable below the source-archive per-file byte cap.
 (OUT/'layout.json').write_text(json.dumps(layout,separators=(',',':'))+'\n');(OUT/'validation.json').write_text(json.dumps({'routes':proofs,'budget':budget,'staged_creatures':staged_creatures},separators=(',',':'))+'\n')
 assert budget['rom_payload_bytes']<1.35*1024*1024
 assert all(p.stat().st_size<=30000 for p in OUT.glob('*.json')if p.name not in{'contract.json','scene.json','ui_additions.json'})
 assert all(p.stat().st_size<70000 for p in OUT.rglob('*.png'))
 print(json.dumps(budget))
if __name__=='__main__':main()
