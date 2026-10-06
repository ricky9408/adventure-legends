#!/usr/bin/env python3
"""Original Hearthwake chapter pixels; no outside raster input or palette changes.
Architecture: fictional gabled timber waterfront, painted plank walls, galleries,
overlapping hull ribs and pale counterworks. Reference boundary in chapter brief.
"""
from pathlib import Path
from collections import deque
import hashlib,json,random,sys
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True
from generate_assets import Art,P,PAL,COLORS,color_background,tree,flowers
from generate_region import paths,terrace,water,bridge,soft_ground,verify_room,odd_bitmap,cbytes,paste_sprite
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/northern_region';SRC=ROOT/'src'
CONTRACT=json.loads((OUT/'contract.json').read_text());ROOMS=[];SPRITES=[]
NAMES=['EDDA','TOVE','NERI','PELL','IVEN','RESET','HANDLE','HANDLE_DONE','CART_LIGHT','CART_HEAVY','JUNCTION_NS','JUNCTION_EW','WEIGHT_UP','WEIGHT_DOWN','REEL','REEL_HELD','BEARING','TENDER','MARKER','HEAT_COLD','HEAT_WARM','CHART_DAMP','CHART_DRY','REST','REST_LIT','FERRY_SIGN','MACHINE_IDLE','MACHINE_WARN','MACHINE_OPEN','BEACON_LIT','FORECAST','SOCKET']
def solid(r,k,b):r['solids'].append({'kind':k,'rect':list(b)})
def obj(r,k,xy,s,approach=None):r['objects'].append({'key':k,'center':list(xy),'sprite':s,'sprite_index':NAMES.index(s),'approach':list(approach or (xy[0],xy[1]+16)),'interaction_radius':24})
def ex(r,k,b,xy,target):r['exits'].append({'key':k,'rect':list(b),'approach':list(xy),'target':target})
def new(i):
 c=CONTRACT['rooms'][i];w,h=c['size'];r={**c,'width':w,'height':h,'solids':[],'dynamic_rectangles':[],'objects':[],'exits':[],'landmarks':[],'camera_crops':[[0,0],[120,80],[240,160],[1,1]] if i<2 else [[0,0]]};ROOMS.append(r)
 a=Art(w,h,'grass3' if i<2 else 'dirt3');soft_ground(a,712+i) if i<2 else None
 for x in(0,w-8):solid(r,'world_edge',(x,0,8,h))
 if i<2:
  solid(r,'north_edge_left',(8,0,216,8));solid(r,'north_edge_right',(256,0,216,8));solid(r,'south_edge_left',(8,h-8,216,8));solid(r,'south_edge_right',(256,h-8,216,8))
 else:
  a.r((0,0,239,29),'stone1');a.r((5,4,234,25),'stone4');a.r((8,27,231,31),'wood2')
  for x in range(12,230,24):a.r((x,5,x+16,20),'plaster');a.l([(x,21),(x+16,21)],'stone2')
  solid(r,'upper_wall',(8,0,224,30));solid(r,'south_left',(8,152,96,8));solid(r,'south_right',(136,152,96,8))
  a.r((8,32,231,151),'dirt3')
  for y in range(36,152,12):a.l([(9,y),(230,y)],'dirt2')
  for x in(8,228):a.r((x,30,x+3,151),'wood2')
  terrace(a,(107,143,27,17));ex(r,'south',(108,144,24,16),(120,144),22 if i<4 else 23 if i==4 else 21+i)
  obj(r,'reset',(32,132),'RESET', (48,132))
 return r,a

def gable(a,r,x,y,w,h,c='rose3',gallery=False):
 # Tall gable faces, steep straight ridge, overlapping timber boards: distinct
 # from the curved ceramic-roof Reedhaven silhouettes.
 a.e((x-4,y+h-6,x+w+6,y+h+8),'shadowsoft');a.r((x,y+25,x+w,y+h),'wood0');a.r((x+2,y+27,x+w-2,y+h-2),c)
 for yy in range(y+31,y+h-3,5):a.l([(x+3,yy),(x+w-3,yy)],'wood1')
 a.p([(x-5,y+33),(x+w//2,y),(x+w+5,y+33)],'wood0');a.p([(x-2,y+30),(x+w//2,y+3),(x+w+2,y+30)],'wood2')
 for dy in range(7,30,5):a.l([(x+w//2-dy, y+dy),(x+w//2+dy,y+dy)],'wood4')
 a.l([(x-3,y+32),(x+w//2,y+2),(x+w+3,y+32)],'wood5',2)
 a.r((x+w//2-5,y+15,x+w//2+5,y+25),'wood0');a.r((x+w//2-3,y+17,x+w//2+3,y+23),'gold3')
 for xx in(x+11,x+w-21):
  a.r((xx,y+42,xx+10,y+56),'wood0');a.r((xx+1,y+43,xx+9,y+54),'water1');a.l([(xx+2,y+44),(xx+7,y+44)],'water4');a.l([(xx+5,y+43),(xx+5,y+54)],'wood5')
 door=x+w//2;a.r((door-8,y+h-24,door+8,y+h),'wood0');a.r((door-5,y+h-22,door+5,y+h),'deep');terrace(a,(door-14,y+h+1,29,6))
 if gallery:
  a.r((x-4,y+62,x+w+4,y+66),'wood1');a.l([(x-4,y+62),(x+w+4,y+62)],'wood5',2)
  for xx in range(x-3,x+w+5,9):a.l([(xx,y+54),(xx,y+68)],'wood2',2)
 solid(r,'painted_gabled_timber',(x-3,y,w+6,h+1));r['landmarks'].append({'kind':'original_gabled_timber_gallery' if gallery else 'original_gabled_timber','bounds':[x-5,y,w+10,h+7]})

def hull(a,x,y,w=70):
 a.e((x-3,y+14,x+w+4,y+23),'shadowsoft')
 for i,c in enumerate(['wood0','wood1','wood2','wood3']):
  a.p([(x+i*4,y+i*2),(x+w//2,y+13-i),(x+w-i*4,y+i*2),(x+w-12-i*3,y+17-i),(x+w//2,y+24-i*3),(x+12+i*3,y+17-i)],c)
 a.l([(x+6,y+3),(x+w//2,y+16),(x+w-6,y+3)],'wood5',2)
 for dx in range(14,w-12,12):a.l([(x+dx,y+7),(x+dx,y+15)],'wood1')

def rail(a,pts):
 a.l(pts,'stone1',7);a.l(pts,'wood2',5)
 for dx in(-2,2):a.l([(x,y+dx) for x,y in pts],'stone5')
 for x,y in pts:a.e((x-5,y-5,x+5,y+5),'wood1');a.e((x-3,y-3,x+3,y+3),'gold3')
def glyph(a,x,y,n):
 if n==0:a.p([(x,y-4),(x+4,y+3),(x-4,y+3)],'wood1')
 elif n==1:a.r((x-3,y-3,x+3,y+3),'water0')
 else:a.p([(x,y-4),(x+4,y),(x,y+4),(x-4,y)],'rose1')

def barrel(a,x,y):
 a.e((x-5,y+5,x+6,y+9),'shadowsoft');a.e((x-5,y-6,x+5,y+6),'wood1');a.r((x-5,y-3,x+5,y+4),'wood3');a.e((x-5,y-7,x+5,y-2),'wood0');a.e((x-4,y-6,x+4,y-3),'wood4');a.l([(x-4,y),(x+4,y)],'stone1');a.l([(x-4,y+4),(x+4,y+4)],'stone1');a.l([(x-1,y-3),(x-1,y+4)],'wood5')
def timber_stack(a,x,y):
 for j in range(3):
  a.r((x+j*2,y-j*4,x+28+j*2,y+3-j*4),'wood0');a.r((x+j*2+1,y-j*4,x+27+j*2,y+1-j*4),'wood4')
def banner(a,x,y,c='rose3'):
 a.l([(x,y),(x,y+24)],'wood1',2);a.p([(x+1,y+1),(x+16,y+3),(x+11,y+7),(x+1,y+7)],c);a.l([(x+2,y+2),(x+11,y+3)],'gold4')
def rope_coil(a,x,y):
 for j in range(3):a.e((x-6+j,y-3+j//2,x+7-j,y+4-j//2),'wood2');a.e((x-4+j,y-2+j//2,x+5-j,y+3-j//2),'wood4')
def shrubs(a,x,y):
 for dx,dy in [(-8,2),(-2,-2),(5,1)]:
  a.e((x+dx-4,y+dy-6,x+dx+5,y+dy+3),'pine2');a.e((x+dx-3,y+dy-6,x+dx+4,y+dy),'pine4');a.dot(x+dx-1,y+dy-4,'leaflight')
def detail_town(a,r):
 # Deliberately clustered work props, leaving every tested approach clear.
 for x,y in[(25,199),(452,214),(137,164),(280,157)]:barrel(a,x,y);solid(r,'work_barrel',(x-5,y-5,11,13))
 for x,y in[(185,158),(348,220)]:timber_stack(a,x,y);solid(r,'timber_stack',(x,y-8,33,12))
 for x,y in[(30,216),(272,214),(436,194)]:rope_coil(a,x,y)
 for x,y in[(215,163),(266,162),(26,236),(453,238)]:banner(a,x,y,'water2' if x%2 else 'rose3')
 # A sheltered kitchen garden and rope-drying frame make the rear passage useful.
 a.r((281,83,316,125),'wood1');a.r((284,86,313,123),'dirt1')
 for y in(90,100,110,120):
  for x in(287,297,307):a.l([(x-2,y),(x,y-3),(x+2,y)],'pine3',2);a.dot(x,y-2,'gold2')
 solid(r,'sheltered_garden',(281,83,36,43))
 a.l([(133,68),(133,117)],'wood1',2);a.l([(147,68),(147,117)],'wood1',2)
 for y in(74,84,94,104):a.l([(134,y),(146,y+4)],'wood4',2)
 solid(r,'rope_drying_frame',(131,68,18,50))
 for x,y in[(22,34),(442,40),(326,171),(143,275)]:shrubs(a,x,y)
 for x in range(8,473,32):
  if 216<=x<=264:continue
  a.r((x,233,x+3,242),'wood1');a.r((x,232,x+3,234),'wood5')
 # Tide strakes on wall and multiple dock faces imply depth without snow/darkness.
 a.l([(8,239),(221,239)],'stone5',2);a.l([(259,239),(471,239)],'stone5',2)
 for y in(243,247):a.l([(10,y),(219,y)],'water0');a.l([(261,y),(469,y)],'water0')

def detail_field(a,r):
 # Uneven cliff face opens onto sea; pale caps, dark ledges, sheltered coves.
 a.p([(92,8),(122,8),(118,31),(108,46),(107,64),(93,64)],'stone2');a.l([(120,8),(116,31),(105,46),(105,63)],'stone5',3)
 solid(r,'upper_cliff',(92,8,18,50))
 a.p([(93,144),(105,151),(99,180),(114,195),(105,222),(87,236),(92,206)],'stone2');a.l([(103,151),(97,180),(112,195),(103,221)],'stone5',3)
 for x,y in[(24,224),(42,239),(25,252)]:a.e((x-8,y-4,x+9,y+3),'stone2');a.l([(x-5,y-3),(x+5,y-3)],'stone5')
 # Beacon base is a layered masonry portal with a timber hoist and flag.
 a.r((365,13,434,54),'stone1');a.r((368,16,431,51),'stone4')
 for yy in(20,31,42):
  a.l([(368,yy),(431,yy)],'stone2')
  for xx in range(372+(yy%2)*7,430,16):a.l([(xx,yy),(xx,yy+9)],'stone3')
 a.p([(389,54),(389,33),(393,27),(407,27),(412,33),(412,54)],'wood1');a.r((394,33,407,56),'deep');a.l([(396,34),(396,53)],'wood3')
 terrace(a,(386,55,28,5));banner(a,434,19,'rose3')
 for x,y in[(300,275),(448,183),(140,26),(344,33),(203,266)]:shrubs(a,x,y)
 for x,y in[(360,282),(439,113)]:timber_stack(a,x,y);solid(r,'headland_stored_planks',(x,y-8,33,12))
 for x,y in[(118,239),(324,134),(208,92)]:banner(a,x,y,'water2')
 # Terrace marks and cairns are visible geography, independent from quest signs.
 for x,y in[(406,280),(422,293),(304,43)]:a.p([(x-6,y),(x-3,y-7),(x+4,y-8),(x+9,y),(x+4,y+5),(x-4,y+4)],'stone2');a.l([(x-3,y-6),(x+3,y-7),(x+7,y-1)],'stone5')

def town():
 r,a=new(0);paths(a,[([(240,0),(240,228),(240,320)],30), ([(64,152),(88,144),(160,176),(384,144),(416,176)],22)])
 water(a,(8,240,464,72),721);solid(r,'harbor_water_west',(8,240,214,72));solid(r,'harbor_water_east',(258,240,214,72));bridge(a,(224,234,32,86));terrace(a,(8,176,464,62),'wood')
 gable(a,r,52,40,72,88,'rose3',True);gable(a,r,338,40,92,88,'water1');gable(a,r,160,28,56,72,'gold1')
 hull(a,28,265,70);hull(a,346,274,98)
 for x,y in[(24,122),(288,56),(452,152)]:tree(a,x,y,.8);solid(r,'tree_trunk',(x-10,y-28,20,30))
 for k,xy,s in [('edda',(168,192),'EDDA'),('neri',(312,192),'NERI'),('pell',(64,192),'PELL'),('tove',(384,160),'TOVE'),('iven',(416,208),'IVEN'),('rest',(104,192),'REST'),('line_triangle',(160,224),'HANDLE'),('line_square',(304,224),'HANDLE'),('forecast',(240,192),'FORECAST'),('ferry',(240,264),'FERRY_SIGN')]:obj(r,k,xy,s,(xy[0],xy[1]+16) if k=='ferry' else (xy[0],xy[1]-16) if k.startswith('line_') else None)
 rail(a,[(144,224),(192,224)]);rail(a,[(280,224),(328,224)])
 for x,n in [(144,0),(328,1)]:glyph(a,x,214,n)
 detail_town(a,r)
 ex(r,'headland',(224,0,32,16),(240,16),23);ex(r,'boathouse',(76,130,24,15),(88,144),24);ex(r,'kiln',(372,130,24,15),(384,144),25);ex(r,'ferry',(224,260,32,32),(240,284),16)
 return r,a

def field():
 r,a=new(1);paths(a,[([(240,320),(240,192),(352,144),(400,72)],28), ([(80,264),(144,248),(240,192),(144,112),(112,80)],22), ([(144,112),(256,80),(320,80),(400,72)],20)])
 water(a,(8,8,84,208),723);solid(r,'coastal_water',(8,8,84,208));a.p([(95,8),(111,8),(110,208),(94,230)],'stone2');a.l([(98,10),(99,210),(87,234)],'stone5',3)
 # Wind shelter and rocky headland are deliberately sunny and passable.
 for x,y in[(178,58),(332,260),(420,240)]:tree(a,x,y,.85);solid(r,'headland_tree',(x-10,y-28,20,30))
 terrace(a,(370,14,60,45));a.r((374,16,425,54),'stone3');a.r((393,31,407,58),'wood0');a.r((396,33,404,58),'deep');solid(r,'beacon_entrance',(370,14,60,42))
 rail(a,[(208,192),(240,192),(320,192),(320,160)]);rail(a,[(240,192),(240,144)])
 hull(a,17,73,63)
 for k,xy,s in [('junction',(240,192),'JUNCTION_NS'),('bearing',(320,192),'BEARING'),('neri',(352,160),'NERI'),('tender_clue',(112,96),'FERRY_SIGN'),('tender',(144,112),'TENDER'),('shelter',(176,144),'FORECAST'),('rest',(80,248),'REST'),('marker_triangle',(176,224),'MARKER'),('marker_square',(288,112),'MARKER'),('marker_diamond',(368,240),'MARKER')]:obj(r,k,xy,s)
 for xy,n in [((176,224),0),((288,112),1),((368,240),2)]:glyph(a,xy[0]+12,xy[1],n)
 detail_field(a,r)
 ex(r,'town',(224,304,32,16),(240,300),22);ex(r,'counterworks',(388,57,24,16),(400,72),26)
 return r,a

def interior(i):
 r,a=new(i)
 if i==2:
  # Stored boat has a readable stair/gallery behind it, all walkable routes clear.
  hull(a,45,36,145);terrace(a,(32,36,177,10),'wood')
  for xx in(44,196):a.r((xx,35,xx+3,55),'wood2')
  rail(a,[(64,80),(120,80),(176,80)]);glyph(a,64,65,0);glyph(a,176,65,1)
  for k,xy,s in [('tether_left',(64,80),'REEL'),('tether_right',(176,80),'REEL'),('parcel',(120,80),'CART_LIGHT'),('roof_parcel',(120,48),'CART_LIGHT'),('edda',(208,112),'EDDA')]:obj(r,k,xy,s)
 elif i==3:
  a.p([(31,55),(37,35),(81,35),(89,55)],'stone1');a.p([(34,54),(40,38),(78,38),(85,54)],'stone4');a.r((46,42,73,54),'fire0');a.r((50,45,69,54),'gold2')
  for x in(64,120,176):
   a.l([(x,56),(x,108)],'wood2',3);obj(r,'vent_'+str(x),(x,64),'HEAT_COLD');obj(r,'chart_'+str(x),(x,104),'CHART_DAMP')
  obj(r,'tove',(208,112),'TOVE')
 elif i in(4,5,6):
  # The two lanes never cross walkways; carts are stateful separate actors.
  rail(a,[(64,64),(120,64),(176,64)]);rail(a,[(64,96),(120,96),(176,96)])
  a.l([(120,40),(120,102)],'wood2',3)
  for x,n in[(64,0),(176,1)]:glyph(a,x,47,n)
  for k,xy,s in [('junction',(120,96),'JUNCTION_NS'),('reel',(64,64),'REEL'),('manual_weight',(176,96),'WEIGHT_UP'),('cart_a',(80,64),'CART_LIGHT'),('cart_b',(160,64),'CART_HEAVY'),('next',(208,56),'HANDLE')]:obj(r,k,xy,s,(xy[0],xy[1]+16))
  a.r((197,31,219,42),'wood1');a.r((200,32,216,40),'gold3');ex(r,'next',(196,44,24,25),(208,72),23+i)
  if i==5:obj(r,'trial_pan',(208,112),'WEIGHT_UP')
  if i==6:obj(r,'compass',(208,112),'FORECAST')
 elif i==7:
  a.e((66,33,174,107),'stone1');a.e((70,35,170,104),'stone4');a.e((84,40,156,95),'dirt3')
  for x in(76,160):a.r((x,33,x+3,101),'wood2');a.l([(x+1,34),(x+1,100)],'wood5')
  a.l([(78,38),(162,38)],'wood0',3);a.l([(78,37),(162,37)],'gold3')
  for k,xy,s in [('wood_coupling',(64,108),'REEL'),('metal_coupling',(176,108),'JUNCTION_NS'),('start',(120,108),'HANDLE'),('machine',(120,68),'MACHINE_IDLE')]:obj(r,k,xy,s,(xy[0],xy[1]+16))
  # Machine is purposefully non-solid: wall-first bow collision reaches coupling.
 # Individually authored room structures. The low central work lanes and south
 # reset/exit walk remain shared as a readable safety convention.
 if i==4:
  # Freight bay: slatted pier deck, inset loading shutter and rear storage racks.
  a.r((13,32,47,113),'wood1');a.r((16,35,44,110),'wood3')
  for yy in range(36,112,6):a.l([(17,yy),(43,yy)],'wood5')
  solid(r,'loading_rack',(13,32,34,79));timber_stack(a,15,49);timber_stack(a,16,76);barrel(a,29,97)
  a.r((151,4,211,26),'wood0');a.r((154,6,208,24),'wood3')
  for xx in range(157,208,6):a.l([(xx,6),(xx,24)],'wood1')
  a.l([(13,115),(226,115)],'wood4',2);banner(a,220,70,'water2')
 elif i==5:
  # Crossbeam: raised northern balcony with a visibly braced timber span.
  a.r((12,32,190,42),'stone1');a.r((14,33,188,36),'stone5');a.r((16,37,186,40),'wood2')
  for xx in(23,184):
   a.r((xx,38,xx+5,91),'wood1');a.l([(xx+1,39),(xx+1,88)],'wood5')
   a.l([(xx+3,43),(xx+16 if xx<100 else xx-12,53)],'wood2',3)
  # Braces are optical architectural supports; explicit collider islands stop
  # the projected beam feet while preserving every mechanism approach.
  solid(r,'crossbeam_west_post',(23,38,6,54));solid(r,'crossbeam_east_post',(184,38,6,42))
  for yy in range(42,62,4):a.r((196,yy,220,yy+1),'stone4')
  a.r((10,117,92,120),'stone2');a.r((10,116,92,117),'stone5');a.r((145,117,226,120),'stone2');a.r((145,116,226,117),'stone5')
 elif i==6:
  # Relay Gallery: a high U-shaped timber gallery outlines a lower service pit.
  a.r((12,32,227,42),'wood1');a.r((14,33,225,38),'wood4')
  for xx in range(18,226,12):a.l([(xx,32),(xx,39)],'wood2')
  for xx in(16,220):
   a.r((xx,40,xx+3,104),'wood1');a.l([(xx+1,40),(xx+1,102)],'wood5')
  a.p([(88,113),(104,105),(160,105),(176,113),(160,119),(104,119)],'stone2');a.l([(91,113),(106,107),(158,107),(172,113)],'stone5')
  # Zigzag return rail is visually separate from the two cargo stop tracks.
  a.l([(72,44),(96,44),(96,50),(152,50),(152,44),(175,44)],'stone1',3)
  a.l([(72,43),(96,43),(96,49),(152,49),(152,43),(175,43)],'gold3')
  for xx in(28,212):banner(a,xx,75,'rose3')
 elif i==7:
  # Open-air cliff crown. No indoor wall or repeated room silhouette.
  water(a,(0,0,240,160),732)
  a.p([(18,29),(51,19),(198,19),(224,40),(220,135),(194,159),(47,159),(18,132)],'stone1')
  a.p([(20,29),(51,22),(196,22),(220,41),(216,130),(192,153),(49,153),(22,129)],'stone3')
  a.p([(25,33),(54,27),(194,27),(215,44),(211,128),(189,147),(52,147),(27,126)],'stone5')
  for yy in range(44,145,16):a.l([(28,yy),(210,yy)],'stone3')
  for x,y in[(26,44),(211,48),(24,120),(209,126)]:a.r((x,y,x+3,y+15),'wood1');a.r((x,y,x+3,y+2),'wood5')
  a.l([(27,43),(54,30),(193,30),(214,45)],'wood2',2)
  # Large static machinery frame: the moving weak point remains a small OBJ.
  a.e((80,37,160,97),'stone1');a.e((84,40,156,94),'gold1');a.e((91,45,149,87),'stone4');a.e((99,50,141,81),'wood1');a.e((103,53,137,78),'stone3')
  for x in(72,164):a.r((x,35,x+4,101),'wood0');a.r((x+1,36,x+2,99),'wood3')
  a.l([(74,37),(166,37)],'wood0',4);a.l([(75,36),(165,36)],'gold3',2)
  a.r((49,44,62,81),'stone1');a.r((50,45,60,77),'gold1');a.l([(55,31),(55,46)],'wood0',2)
  a.r((178,50,192,93),'stone1');a.r((179,51,190,88),'gold1');a.l([(185,31),(185,51)],'wood0',2)
  a.l([(64,108),(72,108),(72,96)],'wood2',2);a.l([(176,108),(166,108),(166,98)],'wood2',2)
  bridge(a,(107,144,27,16));banner(a,204,27,'rose3')
  solid(r,'crown_cliff_west',(8,30,12,114));solid(r,'crown_cliff_east',(220,30,12,114))
 if i in(4,5,6):
  # A real door silhouette, stepped threshold and matching release handle.
  a.r((195,13,221,43),'wood0');a.r((198,16,218,42),'wood2');a.r((201,17,215,42),'deep');a.l([(202,18),(202,40)],'wood4')
  terrace(a,(195,43,27,7));a.r((199,51,217,53),'stone4')
 return r,a

def sprite(n):
 a=Art(16,16,'transparent')
 if n in NAMES[:5]:
  coats=['rose3','gold1','water2','pine3','purple2'];c=coats[NAMES.index(n)]
  a.e((2,12,13,15),'shadow');a.r((4,11,6,14),'wood0');a.r((9,11,11,14),'wood0');a.p([(4,6),(11,6),(13,11),(10,13),(4,12),(2,10)],c);a.r((5,2,10,6),'skin1');a.r((4,1,11,3),'wood1');a.dot(9,4,'ink');a.l([(5,7),(9,7)],'gold4')
  if n=='EDDA':a.l([(2,8),(1,3)],'wood3');a.e((0,0,3,4),'gold2')
  if n=='NERI':a.r((10,7,14,9),'stone4')
 elif n.startswith('CART') or n=='TENDER':
  a.e((0,12,15,15),'shadow');a.r((2,3,13,11),'wood0');a.r((3,4,12,10),'wood3');a.l([(3,4),(12,4)],'wood5');a.r((3,12,5,14),'stone1');a.r((10,12,12,14),'stone1');glyph(a,8,7,0 if n=='CART_LIGHT' else 1)
  if n=='TENDER':a.p([(0,6),(7,11),(15,6),(12,12),(7,14),(3,12)],'water2');a.l([(1,7),(7,12),(14,7)],'water4')
 elif n.startswith('MACHINE'):
  a.e((0,1,15,15),'wood0');a.e((1,2,14,14),'stone2');a.r((3,4,12,11),'gold1');a.r((5,5,10,10),'fire1' if n.endswith('WARN') else 'water3' if n.endswith('OPEN') else 'stone0');a.dot(6,6,'gold4');a.l([(1,8),(3,8)],'stone5');a.l([(12,8),(14,8)],'stone5')
 elif n.startswith('JUNCTION') or n=='FORECAST':
  a.e((0,1,15,14),'wood0');a.e((1,2,14,13),'stone3');a.e((3,4,12,11),'wood1');a.l([(8,3),(8,12)] if n.endswith('NS') else [(3,8),(12,8)],'gold3',3);a.dot(8,8,'gold4')
 elif n.startswith('REEL'):
  a.r((4,1,11,13),'wood0');a.r((5,2,10,12),'wood3')
  for y in(3,6,9):a.l([(4,y),(11,y-1)],'gold3' if n.endswith('HELD') else 'pine5')
  a.r((2,1,13,3),'wood4');a.r((2,11,13,13),'wood4')
 elif n.startswith('WEIGHT'):
  a.l([(7,1),(7,13)],'wood0',2);a.r((2,9,13,14),'stone1');a.r((3,10,12,13),'stone4');a.p([(4,5),(7,2),(11,5),(10,9),(5,9)],'gold2' if n.endswith('DOWN') else 'stone2')
 elif n.startswith('CHART'):
  a.r((2,1,13,14),'wood0');a.r((3,2,12,13),'gold4');a.l([(5,4),(9,5),(6,8),(10,10)],'wood2');a.e((4,7,9,12),'water2') if n.endswith('DAMP') else a.l([(4,10),(7,12),(12,6)],'pine3',2)
 elif n.startswith('HEAT'):
  a.r((2,4,13,13),'stone1');a.r((3,5,12,11),'stone4');a.r((5,6,10,10),'fire1' if n.endswith('WARM') else 'water1');a.l([(3,2),(12,2)],'wood2',2)
 elif n.startswith('REST'):
  a.r((2,10,13,14),'stone1');a.r((5,3,10,11),'wood1');a.r((4,3,11,8),'gold3' if n.endswith('LIT') else 'gold1');a.r((6,4,9,7),'gold4');a.l([(2,2),(13,2)],'water3',2)
 elif n=='BEACON_LIT':
  a.p([(3,14),(4,4),(7,1),(11,4),(12,14)],'gold1');a.r((5,5,10,12),'gold3');a.r((7,3,8,11),'gold4');a.dot(1,4,'gold3');a.dot(14,3,'gold3')
 elif n=='BEARING':
  a.e((2,2,13,13),'stone0');a.e((3,3,12,12),'gold3');a.e((6,6,9,9),'wood0');a.dot(4,4,'gold4')
 elif n=='MARKER':
  a.p([(2,14),(3,4),(7,1),(12,4),(13,14)],'stone1');a.p([(3,13),(4,5),(7,3),(11,5),(12,13)],'stone4');glyph(a,8,8,2)
 elif n=='FERRY_SIGN':
  a.r((7,8,8,15),'wood1');a.r((1,1,14,10),'wood0');a.r((2,2,13,9),'gold4');a.p([(3,5),(7,8),(12,5)],'water1');a.l([(7,2),(7,6)],'wood1')
 elif n=='SOCKET':a.e((1,2,14,13),'wood1');a.e((3,4,12,11),'gold2');glyph(a,8,8,0)
 else:
  a.r((2,9,13,14),'stone1');a.r((3,10,12,12),'stone4');a.l([(8,10),(4,3) if n=='RESET' else (11,3)],'wood0',3);a.e((1,0,6,5),'rose4' if n=='RESET' else 'gold3');a.dot(3,1,'gold4')
  if n=='HANDLE_DONE':a.l([(8,6),(10,8),(14,3)],'pine5',2)
 return a

def collision_bands(room):
 """Exact old predicate, compiled into deduplicated merged interval rows.

 Each u16 y-table entry is an offset to a record in the u16 band stream:
 [interval_count, x0, x1, ...]. Intervals are half-open, sorted, disjoint and
 include world-edge foot limits. Offsets avoid a second descriptor lookup.
 """
 w,h=room['width'],room['height'];rows=[];stream=[];known={};max_spans=0
 for y in range(h):
  ranges=[(0,w)] if y<5 or y>h-6 else [(0,5),(w-5,w)]
  for solid_ in room['solids']:
   x,sy,sw,sh=solid_['rect']
   if sy-5<=y<sy+sh+5:ranges.append((max(0,x-5),min(w,x+sw+5)))
  merged=[]
  for lo,hi in sorted(ranges):
   if lo>=hi:continue
   if merged and lo<=merged[-1][1]:merged[-1]=(merged[-1][0],max(hi,merged[-1][1]))
   else:merged.append((lo,hi))
  key=tuple(merged);max_spans=max(max_spans,len(key))
  if key not in known:
   known[key]=len(stream);stream.append(len(key))
   for lo,hi in key:stream.extend((lo,hi))
  rows.append(known[key])
 assert max(rows)<65536 and max(stream)<65536
 return rows,stream,{'unique_bands':len(known),'maximum_intervals':max_spans,'row_bytes':2*len(rows),'band_bytes':2*len(stream)}

def emit():
 h='''/* Generated original Northern chapter art. */
#ifndef EMBERBOND_NORTH_ART_H
#define EMBERBOND_NORTH_ART_H
#define NORTH_ART_FIRST_ROOM 22
#define NORTH_ART_ROOM_COUNT 8
#define NORTH_ART_FOOT_RADIUS 5
typedef struct { short x,y,w,h; } NorthArtRect;
typedef struct { unsigned short width,height; const unsigned char *bitmap,*bitmap_odd; const NorthArtRect *solids; unsigned short solid_count; const unsigned short *collision_rows,*collision_bands; } NorthArtRoom;
extern const NorthArtRoom north_art_rooms[NORTH_ART_ROOM_COUNT];
/* Exact five-pixel-foot collision. collision_rows[y] indexes a u16 stream
 * record [count,lo0,hi0,...] of sorted merged half-open x intervals.
 * Bounds-check x/y first. No RAM unpacking or additional expansion. */
/* Row-major native 16px actors; zero transparent. Existing OBJ cache only. */
enum {
'''+''.join(f' NORTH_SPR_{n} = {i},\n' for i,n in enumerate(NAMES))+f' NORTH_SPR_COUNT = {len(NAMES)}\n}};\nextern const unsigned char north_sprites[NORTH_SPR_COUNT][256];\n'
 lines=[];total=0;collision_lookup_bytes=0;alignment_bytes=0
 for r in ROOMS:
  k=r['key'];w=r['width'];ht=r['height'];d=r['art'].im.tobytes();r['bitmap_sha256']=hashlib.sha256(d).hexdigest()
  assert min(d)>0 and max(d)<178
  for suffix,b in [('',d)]+([('_odd',odd_bitmap(d,w,ht))] if w>240 else []):
   padding=(-total)&3;total+=padding;alignment_bytes+=padding
   name='north_background_'+k+suffix;h+=f'extern const unsigned char {name}[{len(b)}];\n';cbytes(lines,name,b);total+=len(b)
  lines.append(f'const NorthArtRect north_{k}_solids[] = {{\n');lines.extend(' {'+','.join(map(str,v['rect']))+'},\n' for v in r['solids']);lines.append('};\n');total+=len(r['solids'])*8
  rows,bands,stats=collision_bands(r);r['collision_lookup']=stats
  for suffix,values in [('collision_rows',rows),('collision_bands',bands)]:
   lines.append(f'static const unsigned short north_{k}_{suffix}[{len(values)}] = {{\n')
   for start in range(0,len(values),24):lines.append(' '+','.join(map(str,values[start:start+24]))+',\n')
   lines.append('};\n');total+=len(values)*2;collision_lookup_bytes+=len(values)*2
 padding=(-total)&3;total+=padding;alignment_bytes+=padding
 lines.append('const unsigned char north_sprites[NORTH_SPR_COUNT][256] __attribute__((aligned(4))) = {\n')
 for n,a in SPRITES:
  lines.append(' { /* '+n+' */\n');d=a.im.tobytes()
  for i in range(0,256,32):lines.append(' '+','.join(map(str,d[i:i+32]))+',\n')
  lines.append(' },\n')
 lines.append('};\nconst NorthArtRoom north_art_rooms[NORTH_ART_ROOM_COUNT] = {\n')
 for r in ROOMS:
  k=r['key'];odd='north_background_'+k+'_odd' if r['width']>240 else '0';lines.append(f' {{{r["width"]},{r["height"]},north_background_{k},{odd},north_{k}_solids,{len(r["solids"])},north_{k}_collision_rows,north_{k}_collision_bands }},\n')
 lines.append('};\n');folder=SRC/'north_art_data';folder.mkdir(exist_ok=True);chunks=[];p=''
 for ln in lines:
  if len(p)+len(ln)>32000:chunks.append(p);p=''
  p+=ln
 if p:chunks.append(p)
 for old in folder.glob('*.inc'):old.unlink()
 for i,p in enumerate(chunks):(folder/f'part_{i:03}.inc').write_text(p)
 (SRC/'north_art.h').write_text(h+'#endif\n');(SRC/'north_art.c').write_text('#include "north_art.h"\n'+''.join(f'#include "north_art_data/part_{i:03}.inc"\n' for i in range(len(chunks))))
 return {'bitmap_bytes':844800,'rom_payload_bytes':total+len(SPRITES)*256+224,'collision_lookup_bytes':collision_lookup_bytes,'alignment_bytes':alignment_bytes,'arm32_room_table_bytes':224,'largest_include_bytes':max(map(len,chunks)),'sprite_bytes':len(SPRITES)*256}

def main():
 ROOMS.clear();SPRITES.clear()
 for fn in [town,field]+[lambda i=i:interior(i) for i in range(2,8)]:
  r,a=fn();r['art']=color_background(a,'forest')
 SPRITES.extend((n,sprite(n)) for n in NAMES)
 proofs={}
 for r in ROOMS:proofs[r['key']],_=verify_room(r)
 budget=emit();(OUT/'sprites').mkdir(exist_ok=True);(OUT/'camera').mkdir(exist_ok=True)
 for n,a in SPRITES:a.im.save(OUT/'sprites'/f'{n.lower()}.png',transparency=0)
 lookup=dict(SPRITES)
 preview=Image.new('RGB',(976,900),(28,46,55));draw=ImageDraw.Draw(preview);draw.text((8,7),'HEARTHWAKE / ORIGINAL NORTHERN CHAPTER / native staged pixels',(247,236,193))
 for i,r in enumerate(ROOMS):
  a=r['art'];a.im.save(OUT/(r['key']+'.png'));scene=a.im.convert('RGB')
  for o in r['objects']:paste_sprite(scene,lookup[o['sprite']],*o['center'])
  scene.save(OUT/(r['key']+'_staged.png'))
  for x,y in r['camera_crops']:scene.crop((x,y,x+240,y+160)).save(OUT/'camera'/f'{r["key"]}_{x}_{y}.png')
  pos=(8+i*488,40) if i<2 else (8+(i-2)%4*244,390+(i-2)//4*200)
  draw.text((pos[0],pos[1]-15),r['name'],(247,236,193));preview.paste(scene,pos)
 # Large collage is local generated evidence, not a source-archive input.
 (ROOT/'build').mkdir(exist_ok=True);preview.save(ROOT/'build/northern_preview_native.png')
 layout={'schema':1,'palette':{'entries':178,'sha256':hashlib.sha256(bytes(PAL)).hexdigest()},'coordinate_contract':'world centers; half-open rectangles; five-pixel foot; row-major actors x-8,y-8','sprites':{'names':NAMES,'indices':{n:i for i,n in enumerate(NAMES)},'size':[16,16]},'rooms':[{k:v for k,v in r.items() if k!='art'} for r in ROOMS],'generated':budget}
 (OUT/'layout.json').write_text(json.dumps(layout,indent=2)+'\n');(OUT/'validation.json').write_text(json.dumps({'routes':proofs,'budget':budget},indent=2)+'\n')
 assert all(p.stat().st_size<70000 for p in OUT.rglob('*.png'))
 print(json.dumps(budget))
if __name__=='__main__':main()
