#!/usr/bin/env python3
"""Original Reedhaven regional pixel art and a radius-five collision contract.

All pixels are authored from geometric primitives at native resolution. No
imported game imagery, tracing, raster scaling, dithering or palette changes.
Run: python3 assets/generate_region.py; tests/test_region_art.py verifies assets.
Contract.json belongs to the progression implementation and is never modified.
"""
from collections import deque
from pathlib import Path
import hashlib, json, random, sys
from PIL import Image, ImageDraw, ImageFilter
sys.dont_write_bytecode = True
from generate_assets import Art, COLORS, P, PAL, color_background, tree, flowers, stone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets' / 'region'
SRC = ROOT / 'src'
CHUNK_LIMIT = 32000
RADIUS = 5
CONTRACT = json.loads((OUT / 'contract.json').read_text())
PALETTE_HASH = hashlib.sha256(bytes(PAL)).hexdigest()
ROOM_KEYS = ['reedhaven', 'reedbasin', 'bellfoundry', 'tide_courtyard', 'mira_storehouse', 'surestep_garden']
ROOMS = []
SPRITES = []


def rect(a, box, color):
    x, y, w, h = box
    a.r((x, y, x+w-1, y+h-1), color)


def solid(room, kind, box):
    x,y,w,h = map(int, box)
    assert w > 0 and h > 0 and 0 <= x < x+w <= room['width'] and 0 <= y < y+h <= room['height'], (kind, box)
    room['solids'].append({'kind':kind,'rect':[x,y,w,h]})


def dynamic(room, key, box, why):
    room['dynamic_rectangles'].append({'key':key,'rect':list(box),'closed_by_default':True,'access_hint':why})


def obj(room, key, kind, xy, sprite, variants=(), approach=None, hint=''):
    x,y = xy
    room['objects'].append({'key':key,'type':kind,'center':[x,y],
        'approach':list(approach or (x,y+16)), 'sprite':sprite,
        'state_sprites':list(variants), 'interaction_radius':24,
        'access_hint':hint or 'Approach on the pale walkable floor; state and rewards are engine-owned.'})


def exit_at(room, key, rect_, approach, target):
    room['exits'].append({'key':key,'rect':list(rect_),'approach':list(approach),'target':target})


def new_room(idx):
    c = CONTRACT['rooms'][idx]
    w,h = c['size']
    room={'id':c['id'],'key':ROOM_KEYS[idx],'name':c['name'],'width':w,'height':h,
          'spawns':c['spawns'],'solids':[],'dynamic_rectangles':[], 'objects':[], 'exits':[], 'landmarks':[], 'camera_crops':[]}
    ROOMS.append(room)
    return room, Art(w,h,'grass3' if idx != 2 and idx != 4 else 'dirt3')


def edge_collision(room, interior=False):
    w,h=room['width'],room['height']
    solid(room,'west_world_edge',(0,0,8,h))
    solid(room,'east_world_edge',(w-8,0,8,h))
    if interior:
        solid(room,'upper_room_wall',(8,0,w-16,30))
        solid(room,'south_wall_left',(8,h-8,w//2-20,8))
        solid(room,'south_wall_right',(w//2+12,h-8,w//2-20,8))
    else:
        solid(room,'north_edge_left',(8,0,w//2-24,8))
        solid(room,'north_edge_right',(w//2+16,0,w//2-24,8))
        solid(room,'south_edge_left',(8,h-8,w//2-24,8))
        solid(room,'south_edge_right',(w//2+16,h-8,w//2-24,8))


def soft_ground(a, seed):
    r=random.Random(seed);w,h=a.im.size
    # Broad quiet planes; grass flecks are clustered and never become noise.
    for i in range(65 if w>240 else 12):
        x=r.randrange(5,w-5);y=r.randrange(12,h-5);rx=r.randrange(7,21);ry=r.randrange(3,8)
        a.p([(x-rx,y),(x-rx+4,y-ry),(x+rx-5,y-ry),(x+rx,y),(x+rx-4,y+ry),(x-rx+5,y+ry)], 'grass4' if i%3 else 'grass2')
    for i in range(190 if w>240 else 35):
        x=r.randrange(5,w-5);y=r.randrange(12,h-5)
        a.l([(x-2,y),(x,y-2),(x+1,y),(x+3,y-1)],'grasslit' if i%2 else 'grass2')


def paths(a, lines):
    for extra,c in [(5,'grass1'),(3,'dirt1'),(1,'dirt2'),(0,'dirt3')]:
        for pts,width in lines:
            a.l(pts,c,width+extra)
            rr=(width+extra)//2
            for x,y in pts:a.e((x-rr,y-rr,x+rr,y+rr),c)
    for pts,width in lines:
        a.l(pts,'dirt4',max(3,width-9))
    # Paving marks follow route direction without visually fragmenting the path.
    for pts,width in lines:
        for x,y in pts[1:-1]:stone(a,x-5,y-2,9,3)


def terrace(a, box, kind='stone'):
    x,y,w,h=box
    a.r((x+2,y+h-3,x+w+3,y+h+4),'shadowsoft')
    rect(a,(x,y,w,h),'stone1' if kind=='stone' else 'wood1')
    rect(a,(x+1,y+1,w-2,h-4),'stone4' if kind=='stone' else 'wood3')
    a.l([(x+2,y+1),(x+w-3,y+1)],'stone5' if kind=='stone' else 'wood5')
    for xx in range(x+10,x+w-3,16):
        a.l([(xx,y+2),(xx,y+h-6)],'stone3' if kind=='stone' else 'wood2')
    a.l([(x+1,y+h-3),(x+w-2,y+h-3)],'stone2' if kind=='stone' else 'wood0')


def water(a,box,seed=1):
    x,y,w,h=box;r=random.Random(seed)
    rect(a,(x-2,y-3,w+4,h+6),'grass1')
    rect(a,(x-1,y-2,w+2,h+4),'dirt1')
    rect(a,(x,y,w,h),'water2')
    a.l([(x,y),(x+w-1,y)],'water0',2)
    a.l([(x,y+h-1),(x+w-1,y+h-1)],'stone4',2)
    for yy in range(y+5,y+h-3,8):
        for xx in range(x+4,x+w-10,30):
            d=r.randrange(0,8);a.l([(xx+d,yy),(xx+8+d,yy),(xx+10+d,yy-1),(xx+15+d,yy-1)],'water3')
            a.r((xx+2+d,yy,xx+5+d,yy),'water4')


def water_network(a, boxes, seed):
    """One continuous river mask: no false internal bank lines at rectangle joins."""
    w,h=a.im.size;mask=Image.new('L',(w,h));d=ImageDraw.Draw(mask)
    for x,y,rw,rh in boxes:d.rectangle((x,y,x+rw-1,y+rh-1),fill=255)
    # These are only decorative banks outside exact water collision rectangles.
    for grow,c in [(7,'grass1'),(5,'dirt1'),(3,'dirt2')]:a.im.paste(P[c],(0,0),mask.filter(ImageFilter.MaxFilter(grow)))
    a.im.paste(P['water0'],(0,0),mask)
    inner=mask.filter(ImageFilter.MinFilter(3));a.im.paste(P['water2'],(0,0),inner)
    a.d=ImageDraw.Draw(a.im);rng=random.Random(seed)
    for y in range(83,212,8):
        for x in range(13,w-18,27):
            xx=x+rng.randrange(0,8)
            if all(inner.getpixel((xx+dx,y)) for dx in range(16)):
                a.l([(xx,y),(xx+7,y),(xx+9,y-1),(xx+15,y-1)],'water3')
                a.l([(xx+2,y),(xx+4,y)],'water4')
    # Sun-catching southern shores and sparse bank grass soften the authored steps.
    for y in range(8,h-5):
        for x in range(8,w-8):
            if mask.getpixel((x,y)) and not mask.getpixel((x,y+1)):
                a.dot(x,y,'water3');a.dot(x,y+1,'stone4')
    for x,y in [(14,142),(33,78),(67,77),(130,116),(153,142),(202,141),(274,157),(334,157),(439,157),(435,214)]:
        a.p([(x-6,y),(x-4,y-2),(x+3,y-1),(x+7,y+1),(x+6,y+3),(x-2,y+2)],'grass3')
        a.l([(x-4,y),(x+1,y-1),(x+5,y+1)],'grasslit')


def reeds(a,x,y,n=5):
    for i in range(n):
        dx=(i*7)%17-8;dy=(i*3)%5
        a.l([(x+dx,y),(x+dx-1,y-7-dy)],'pine2')
        a.l([(x+dx,y-3),(x+dx+3,y-7)],'pine4')
        a.r((x+dx-2,y-10-dy,x+dx,y-7-dy),'moss2')
        a.dot(x+dx-2,y-10-dy,'moss3')


def bridge(a,box,vertical=True):
    x,y,w,h=box
    rect(a,(x-2,y-2,w+4,h+4),'wood0')
    rect(a,box,'wood3')
    if vertical:
        for yy in range(y,y+h,5):
            a.r((x+1,yy,x+w-2,yy+1),'wood5');a.r((x+2,yy+3,x+w-3,yy+3),'wood1')
        for xx in (x-2,x+w):
            a.r((xx,y-3,xx+1,y+h+1),'wood1');a.l([(xx,y-3),(xx,y+h-1)],'wood4')
            for yy in (y-4,y+h):a.r((xx-1,yy-3,xx+2,yy+3),'wood0');a.r((xx,yy-3,xx+1,yy+1),'wood5')
    else:
        for xx in range(x,x+w,5):a.r((xx,y+1,xx+1,y+h-2),'wood5');a.r((xx+3,y+2,xx+3,y+h-3),'wood1')
        for yy in (y-2,y+h):a.l([(x-3,yy),(x+w+2,yy)],'wood1',2);a.l([(x-3,yy-1),(x+w+2,yy-1)],'wood5')


def lantern(a,x,y):
    a.e((x-4,y+1,x+6,y+4),'shadowsoft')
    a.r((x,y-20,x+1,y+1),'wood0');a.l([(x,y-21),(x+8,y-21)],'wood2',2)
    a.l([(x+7,y-20),(x+7,y-16)],'wood1')
    a.r((x+3,y-16,x+11,y-8),'rose0');a.r((x+4,y-16,x+10,y-8),'gold2')
    a.r((x+5,y-15,x+9,y-9),'gold3');a.r((x+7,y-15,x+7,y-9),'gold4')
    a.r((x+4,y-17,x+10,y-16),'wood1');a.r((x+4,y-8,x+10,y-7),'wood1');a.dot(x+7,y-5,'rose4')


def timber_house(a,room,x,y,w,h,roof='teal',door=None,kind='house'):
    door=door if door is not None else x+w//2
    palettes={'teal':('water0','water1','water2','water3','water4'),
              'red':('rose0','rose1','rose2','rose3','rose5'),
              'jade':('pine0','pine1','pine2','pine3','pine5')}
    r0,r1,r2,r3,r4=palettes[roof]
    a.e((x-4,y+h-8,x+w+6,y+h+6),'shadowsoft')
    a.r((x+3,y+24,x+w-4,y+h),'wood0');a.r((x+5,y+26,x+w-6,y+h-2),'wood3')
    a.r((x+7,y+30,x+w-8,y+h-6),'plaster')
    for xx in (x+6,x+w-10):a.r((xx,y+28,xx+3,y+h-3),'wood1');a.r((xx+1,y+29,xx+1,y+h-5),'wood5')
    a.r((x+6,y+h-6,x+w-7,y+h-4),'wood2')
    for xx in range(x+16,x+w-15,22):
        if abs(xx-door)<14:continue
        a.r((xx-5,y+h-27,xx+6,y+h-14),'wood1');a.r((xx-4,y+h-26,xx+5,y+h-16),'water0')
        a.r((xx-3,y+h-25,xx+4,y+h-22),'gold2')
        for dx in (-1,3):a.l([(xx+dx,y+h-25),(xx+dx,y+h-16)],'wood4')
        a.r((xx-6,y+h-14,xx+7,y+h-13),'wood5')
    # Wide dark doorway and pale approach are a real readable opening.
    a.r((door-9,y+h-23,door+9,y+h),'wood0');a.r((door-7,y+h-22,door+7,y+h-1),'deep')
    a.r((door-6,y+h-21,door-4,y+h-2),'wood2');a.r((door+4,y+h-21,door+6,y+h-2),'wood1')
    a.r((door-10,y+h-24,door+10,y+h-22),'wood4')
    terrace(a,(door-14,y+h+1,29,5))
    # Curving tile silhouette, split roof faces, raised ceramic ridge and eaves.
    a.p([(x-7,y+31),(x-5,y+25),(x+1,y+25),(x+14,y+6),(x+w-15,y+6),(x+w-2,y+25),(x+w+4,y+25),(x+w+6,y+31),(x+w+3,y+35),(x-4,y+35)],r0)
    a.p([(x-5,y+29),(x+1,y+27),(x+15,y+8),(x+w-16,y+8),(x+w-3,y+27),(x+w+4,y+29),(x+w+2,y+31),(x-3,y+31)],r2)
    for row in range(6):
        yy=y+9+row*4;left=x+14-row*3;right=x+w-15+row*3
        a.l([(left,yy),(right,yy)],r4 if row<2 else r3)
        for xx in range(left+3+(row%2)*4,right,9):a.l([(xx,yy+1),(xx-1,yy+3)],r1)
    a.l([(x-4,y+30),(x+w+3,y+30)],r3);a.l([(x-3,y+33),(x+w+2,y+33)],'wood5')
    a.r((x+13,y+4,x+w-14,y+7),r0);a.r((x+14,y+4,x+w-15,y+5),r4)
    for xx,sgn in ((x+13,-1),(x+w-14,1)):
        a.l([(xx,y+5),(xx+3*sgn,y+3),(xx+4*sgn,y)],r0,2);a.dot(xx+4*sgn,y,r4)
    # Storefront solid stops at the sill; the interaction threshold is outside.
    solid(room,kind,(x-3,y+3,w+6,h-2))
    room['landmarks'].append({'kind':kind,'bounds':[x-7,y,w+14,h+8],'door':[door,y+h]})


def scenic_tree(a,room,x,y,s=1):
    tree(a,x,y,s)
    x1=max(8,int(x-14*s));y1=max(8,int(y-41*s));x2=min(room['width']-8,int(x+14*s));y2=min(room['height']-8,int(y+3*s))
    if x2>x1 and y2>y1:solid(room,'tree_island',(x1,y1,x2-x1,y2-y1))


def market_stall(a,room,x,y,w=38,c='rose4'):
    a.e((x-2,y+28,x+w+3,y+34),'shadowsoft')
    a.r((x,y+3,x+2,y+30),'wood1');a.r((x+w-2,y+3,x+w,y+30),'wood1')
    a.r((x-3,y+23,x+w+3,y+29),'wood1');a.r((x-2,y+22,x+w+2,y+25),'wood4')
    a.p([(x-4,y+13),(x+2,y),(x+w-2,y),(x+w+4,y+13)],'wood0')
    for stripe,xx in enumerate(range(x-2,x+w+1,8)):
        a.p([(xx,y+11),(xx+4,y+1),(min(xx+11,x+w-1),y+1),(min(xx+7,x+w+2),y+11)],c if stripe%2 else 'gold4')
    a.r((x-3,y+12,x+w+3,y+15),c)
    for xx in range(x+3,x+w-3,8):a.e((xx,y+18,xx+5,y+22),'gold2');a.dot(xx+1,y+18,'gold4')
    solid(room,'market_counter',(x-3,y+1,w+7,29))


def gate(a,x,y,w=56,color='red'):
    r='rose2' if color=='red' else 'water1'
    for xx in (x-w//2,x+w//2):
        a.r((xx-4,y-24,xx+4,y+1),'stone1');a.r((xx-3,y-23,xx+2,y),'plaster');a.r((xx-5,y,xx+5,y+3),'stone3')
    a.p([(x-w//2-10,y-22),(x-w//2-7,y-30),(x-w//2-3,y-28),(x+w//2+3,y-28),(x+w//2+7,y-30),(x+w//2+10,y-22)],'wood0')
    a.l([(x-w//2-8,y-26),(x+w//2+8,y-26)],r,3)
    a.l([(x-w//2-7,y-24),(x+w//2+7,y-24)],'roofshine' if color=='red' else 'water3')
    a.r((x-8,y-24,x+8,y-14),'wood1');a.r((x-6,y-22,x+6,y-16),'gold3')
    a.l([(x-3,y-20),(x+3,y-20),(x,y-17),(x-3,y-20)],'wood0')


def town():
    room,a=new_room(0);edge_collision(room);soft_ground(a,441)
    paths(a,[([(240,0),(240,52),(240,144),(240,220),(240,274),(240,320)],28),
             ([(88,112),(88,140),(112,148),(240,144),(344,152),(384,144),(448,152)],23),
             ([(240,52),(272,48),(328,48),(360,56)],22),
             ([(112,148),(112,206),(104,232),(152,264),(240,274)],22),
             ([(384,144),(384,212),(344,248),(400,270),(440,280)],25),
             ([(104,232),(172,234),(240,234),(292,248),(344,248)],22)])
    # Hand-built canal network. Three permanent footbridges and two tributary crossings.
    water(a,(8,166,464,25),11)
    for box in [(8,166,88,25),(128,166,96,25),(256,166,112,25),(400,166,72,25)]:solid(room,'canal_water',box)
    for x in (96,224,368):bridge(a,(x,163,32,32))
    water(a,(274,8,20,156),12)
    for box in [(274,8,20,28),(274,60,20,68),(274,156,20,10)]:solid(room,'tributary_water',box)
    bridge(a,(271,36,26,24),False);bridge(a,(271,128,26,28),False)
    for x,y in [(20,163),(53,198),(151,163),(182,198),(302,198),(328,163),(422,198),(452,163),(299,92)]:reeds(a,x,y)
    timber_house(a,room,48,48,80,64,'jade',88,'weaver_cottage')
    timber_house(a,room,302,65,88,71,'teal',344,'workshop')
    timber_house(a,room,156,10,60,58,'red',186,'canal_residence')
    timber_house(a,room,364,8,84,59,'jade',406,'tea_house')
    # Raised workshop chimney, water wheel and visible tools supply its own silhouette.
    a.r((372,44,383,74),'stone1');a.r((373,44,380,72),'stone3');a.r((370,42,385,47),'stone4')
    for yy in (52,63):a.l([(373,yy),(381,yy)],'stone2')
    a.e((295,100,313,126),'wood0');a.e((297,102,311,124),'wood3');a.e((300,106,308,120),'water0')
    for p1,p2 in [((304,102),(304,124)),((297,112),(311,112)),((299,105),(309,121)),((298,120),(310,105))]:a.l([p1,p2],'wood5',2)
    market_stall(a,room,166,99,37,'rose4');market_stall(a,room,165,195,37,'water3')
    # Rest pavilion is airy and welcomes the player from a wide curved lane.
    terrace(a,(62,205,84,24));gate(a,104,205,62,'teal')
    for xx in (67,136):solid(room,'rest_pavilion_post',(xx,183,5,26))
    solid(room,'rest_pavilion_roof',(68,175,73,12))
    a.r((67,176,141,184),'water0');a.r((69,177,139,179),'water3')
    # Training ground: sand, flat practice inlays, and a clear southern approach.
    a.p([(392,220),(462,220),(467,292),(439,302),(391,287)],'dirt1')
    a.p([(395,223),(460,223),(462,290),(438,299),(394,285)],'dirt3')
    for x,y in [(408,240),(432,240),(456,240),(440,280)]:
        a.e((x-9,y-4,x+9,y+5),'dirt2');a.l([(x-7,y+5),(x+7,y+5)],'dirt4')
    # Garden entrance and a small border rockery; no baked movable goal or reward.
    gate(a,344,232,54)
    for xx in (313,371):solid(room,'garden_gate_pillar',(xx,210,6,23))
    solid(room,'garden_gate_crown',(314,200,62,8))
    for x,y,s in [(28,61,1.2),(25,117,1),(33,268,1.1),(57,308,1.1),(153,311,1), (288,313,.9),(452,97,.8),(471,310,1.1),(316,31,.8)]:scenic_tree(a,room,x,y,s)
    # Small cultivated beds, stepping stones, an unoccupied sitting bench, pottery.
    for x,y in [(57,142),(145,287),(306,273),(414,80)]:
        for i in range(3):flowers(a,x+i*5,y+(i%2)*3,'flower1' if i%2 else 'flower0')
    for x,y,w in [(153,72,44),(66,281,62),(305,293,45)]:
        a.r((x,y,x+w,y+14),'dirt1')
        for yy in (y+3,y+9):
            a.l([(x+3,yy),(x+w-3,yy)],'wood3')
            for xx in range(x+5,x+w-2,8):a.e((xx-2,yy-2,xx+2,yy+1),'pine3');a.dot(xx-1,yy-2,'pine5')
    for x,y in [(70,128),(258,73),(213,206),(305,248),(417,153),(151,258)]:lantern(a,x,y)
    terrace(a,(155,147,35,9),'wood');solid(room,'canal_bench',(155,147,35,9))
    for x,y in [(53,123),(399,125),(203,224),(332,218)]:
        a.e((x-4,y-7,x+4,y+1),'wood1');a.e((x-3,y-7,x+3,y-5),'water1');a.l([(x-2,y-4),(x-2,y)],'wood4')
    gate(a,240,34,54)
    for xx in (209,267):solid(room,'north_gate_post',(xx,11,6,26))
    # Actors, functional signs and all state-bearing objects are separate sprites.
    obj(room,'smith','npc',(320,150),'NPC_SMITH',approach=(320,150),hint='Outside the tiled workshop by its water wheel.')
    obj(room,'mira','npc',(88,136),'NPC_WEAVER',approach=(88,136),hint='The teal-thread sign marks the weaver cottage.')
    obj(room,'warden','npc',(264,236),'NPC_WARDEN',approach=(264,252))
    obj(room,'rest','rest',(104,216),'REST_IDLE',('REST_LIT',),approach=(104,232),hint='An open-sided lantern pavilion beside the west bridge.')
    obj(room,'apprentice','npc',(416,264),'NPC_APPRENTICE',approach=(416,280))
    obj(room,'market_keeper','npc',(182,234),'NPC_REST_KEEPER',approach=(182,250))
    for key,xy,spr in [('sword_rack',(408,240),'RACK_SWORD'),('lance_rack',(432,240),'RACK_LANCE'),('bow_rack',(456,240),'RACK_BOW'),('practice_target',(440,280),'TARGET_READY')]:obj(room,key,'equipment_practice',xy,spr,('TARGET_HIT',) if key=='practice_target' else (),approach=(xy[0],xy[1]+16))
    for key,xy,spr in [('workshop_sign',(400,152),'SIGN_WORKSHOP'),('weaver_sign',(64,128),'SIGN_WEAVER'),('garden_sign',(376,248),'SIGN_GARDEN')]:obj(room,key,'sign',xy,spr,approach=(xy[0],xy[1] if key=='workshop_sign' else xy[1]+12))
    exit_at(room,'south_road',(224,298,32,14),(240,304),{'room':'previous_region','spawn':'parent_owned'})
    exit_at(room,'north_basin',(224,14,32,20),(240,28),{'room':17,'spawn':0})
    exit_at(room,'bellfoundry',(332,138,24,10),(344,148),{'room':18,'spawn':0})
    exit_at(room,'mira_storehouse',(76,115,24,10),(88,124),{'room':20,'spawn':0})
    exit_at(room,'surestep_garden',(332,218,24,17),(344,230),{'room':21,'spawn':0})
    room['camera_crops']=[[0,40],[240,56],[0,160],[240,160],[120,0],[120,160]]
    return room,a


def basin():
    room,a=new_room(1);edge_collision(room);solid(room,'north_basin_boundary',(224,0,32,8));soft_ground(a,921)
    paths(a,[([(240,320),(240,284),(204,268),(164,252),(120,232),(108,207),(108,126),(176,104),(240,110),(320,88),(360,72),(360,47)],24),
             ([(240,284),(328,268),(396,234),(396,142),(360,112),(360,72)],23),
             ([(240,268),(240,208),(240,140),(240,110)],21),
             ([(176,104),(176,52),(124,43),(88,44)],17),
             ([(240,110),(272,126),(296,120)],19),
             ([(360,112),(424,104)],20),
             ([(176,104),(184,72)],19)])
    # One river, shaped into low broad pools; permanent west/east loop crossings.
    waters=[(8,144,84,40),(124,144,100,40),(224,152,32,32),(256,160,124,24),(412,160,60,24),(24,80,54,64),(78,80,52,38),(306,184,76,28),(412,184,44,28)]
    water_network(a,waters,140)
    for b in waters:
        if b==(224,152,32,32):continue
        solid(room,'basin_water',b)
    bridge(a,(92,141,32,46));bridge(a,(380,157,32,58))
    # The center crossing remains a visible gap. Only stubs are baked.
    bridge(a,(224,142,32,9));bridge(a,(224,185,32,9))
    dynamic(room,'dry_road_bridge',(224,152,32,32),'Closed water can be bypassed by either permanent loop bridge; engine may tile BRIDGE_WOOD after repair.')
    room['landmarks'].append({'kind':'central_repairable_crossing','bounds':[222,140,36,56]})
    for x,y in [(20,147),(45,78),(75,81),(137,121),(151,186),(193,148),(282,188),(329,157),(446,156),(429,216),(281,175)]:reeds(a,x,y,6)
    # Tide gate sits on a low ruined stair with broad safe approach.
    terrace(a,(324,40,72,17));gate(a,360,48,52,'teal')
    for xx in (330,384):solid(room,'tide_gate_post',(xx,24,6,26))
    solid(room,'tide_gate_lintel',(332,14,56,12))
    for x,y,w in [(307,34,15),(400,36,25),(318,52,13),(398,53,18)]:
        terrace(a,(x,y,w,12));solid(room,'tide_ruin',(x,y,w,12))
    # Two shallow ring basins have opaque rims only. Water state is a sprite.
    for x,y in [(296,120),(424,104)]:
        a.e((x-18,y-13,x+18,y+14),'shadowsoft');a.e((x-17,y-14,x+17,y+11),'stone1');a.e((x-15,y-13,x+15,y+9),'stone4');a.e((x-11,y-9,x+11,y+6),'dirt1');a.e((x-8,y-7,x+8,y+6),'dirt3')
        a.l([(x-12,y-10),(x-4,y-12),(x+5,y-12)],'stone5')
    # Ancient leaning bell-tree and weathered upland cairns create local silhouettes.
    scenic_tree(a,room,218,67,1.35);scenic_tree(a,room,458,83,1.3)
    for x,y,s in [(24,55,1),(151,46,.85),(27,257,1.2),(59,296,1.1),(166,315,1),(300,314,1.1),(454,303,1.2),(449,256,1),(314,71,.8)]:scenic_tree(a,room,x,y,s)
    for x,y,w,h in [(167,186,24,17),(296,224,31,18),(57,202,22,16),(422,38,25,16),(271,35,19,13)]:
        stone(a,x,y,w,h);solid(room,'basin_boulder',(x,y,w,h+1))
    # Hidden nook: a continuous twelve-pixel foot route behind light reeds.
    a.p([(40,22),(72,22),(82,34),(78,55),(46,57),(36,43)],'grasslit')
    a.l([(52,44),(88,44)],'grass4',14)
    for x,y in [(41,31),(44,54),(74,25)]:flowers(a,x,y,'flower1')
    # Standing stones have no readable reward symbols, just local wayfinding.
    for x,y in [(166,77),(204,78)]:
        a.p([(x-5,y),(x-4,y-15),(x+1,y-20),(x+6,y-13),(x+6,y)],'stone1');a.p([(x-3,y-2),(x-2,y-14),(x+1,y-17),(x+3,y-11),(x+3,y-2)],'stone4')
        solid(room,'standing_stone',(x-5,y-19,12,20))
    a.e((164,59,202,85),'grass4')
    # Rest clearing sits by a thatched shade and a still walkable bank.
    terrace(a,(91,206,59,24));lantern(a,142,211)
    terrace(a,(155,214,32,9),'wood');solid(room,'basin_rest_bench',(155,214,32,9))
    for x,y in [(134,241),(347,253),(275,287),(402,132),(159,96)]:
        for i in range(3):flowers(a,x+i*4,y+(i%2)*3,'flower1' if i%2 else 'flower0')
    lantern(a,266,236);lantern(a,334,88)
    obj(room,'basin_rest','rest',(120,216),'REST_IDLE',('REST_LIT',),approach=(120,232))
    obj(room,'sluice_handle','mechanism',(264,200),'SLUICE_CLOSED',('SLUICE_OPEN',),approach=(264,216),hint='The dry road has two visible permanent ways around it.')
    obj(room,'west_tide_pool','pool',(296,120),'POOL_LOW',('POOL_HIGH',),approach=(296,140),hint='Paired rim markings match the second pool across the eastern path.')
    obj(room,'east_tide_pool','pool',(424,104),'POOL_LOW',('POOL_HIGH',),approach=(424,124))
    obj(room,'weaver_nook','discovery',(60,40),'SPINDLE_IDLE',('SPINDLE_LIT',),approach=(72,44),hint='Pale flowers and a break in the reed line continue the upland path.')
    obj(room,'reed_screen','visual_state',(84,44),'REED_SCREEN',('REED_PARTED',),approach=(98,44))
    obj(room,'basin_bond','discovery',(184,72),'BELL_IDLE',('BELL_RING',),approach=(184,88),hint='The two uneven standing stones frame a quiet clearing.')
    obj(room,'basin_warden','npc',(348,268),'NPC_WARDEN',approach=(348,284))
    obj(room,'tide_sign','sign',(384,80),'SIGN_TIDE',approach=(384,96))
    exit_at(room,'south_reedhaven',(224,298,32,14),(240,304),{'room':16,'spawn':1})
    exit_at(room,'tide_courtyard',(348,45,24,15),(360,56),{'room':19,'spawn':0})
    room['camera_crops']=[[0,0],[240,0],[0,160],[240,160],[120,96],[120,160]]
    return room,a


def indoor_frame(a,room,material='stone'):
    edge_collision(room,True)
    w,h=a.im.size
    a.r((8,30,231,151),'stone4' if material=='stone' else 'wood4')
    a.r((8,0,231,29),'stone1' if material=='stone' else 'wood1')
    a.r((10,4,229,25),'stone2' if material=='stone' else 'wood3')
    for x in range(12,230,24):
        a.l([(x,4),(x,23)],'stone1' if material=='stone' else 'wood2')
        a.l([(x+2,5),(x+16,5)],'stone4' if material=='stone' else 'wood5')
    a.r((9,27,230,31),'stone5' if material=='stone' else 'wood5')
    for x in (8,228):
        a.r((x,29,x+3,150),'stone1' if material=='stone' else 'wood1');a.r((x+1,30,x+1,148),'stone5' if material=='stone' else 'wood5')
    for x,wid in ((8,100),(132,100)):
        rect(a,(x,152,wid,8),'stone1' if material=='stone' else 'wood1');a.l([(x,152),(x+wid-1,152)],'stone5' if material=='stone' else 'wood5')
    for y in range(30,151,16):
        for x in range(12+(8 if (y//16)%2 else 0),229,24):
            a.l([(x,y),(min(x+21,227),y)],'stone3' if material=='stone' else 'wood3')
            a.l([(x,y),(x,y+11)],'stone3' if material=='stone' else 'wood3')
    for yy in (142,147,153):a.l([(108,yy),(131,yy)],'stone3' if material=='stone' else 'wood2')
    a.l([(112,145),(119,149),(127,145)],'gold1')
    exit_at(room,'return_door',(108,143,24,13),(120,149),{'room':16 if room['id']!=19 else 17,'spawn':{18:3,19:1,20:4,21:5}[room['id']]})
    room['camera_crops']=[[0,0]]


def ring(a,x,y,rx=12,ry=8):
    a.d.ellipse((x-rx,y-ry,x+rx,y+ry),outline=P['stone2'])
    a.d.ellipse((x-rx+2,y-ry+2,x+rx-2,y+ry-2),outline=P['stone5'])


def foundry():
    room,a=new_room(2);indoor_frame(a,room)
    # Chimney light and copper roof beams have weight above the cool flagstones.
    for x in (23,105,210):
        a.r((x,0,x+5,31),'wood0');a.r((x+1,0,x+3,27),'wood3');a.r((x-3,25,x+8,28),'gold1')
    for x in (63,149):
        a.r((x,4,x+24,22),'wood0');a.r((x+2,5,x+22,20),'water1')
        for xx in range(x+4,x+23,6):a.l([(xx,5),(xx,20)],'gold2')
    # Bellfoundry stove alcove; actual fire/forge state occupies its separate sprite.
    a.p([(18,63),(18,36),(23,26),(58,26),(64,37),(64,63)],'stone0')
    a.p([(20,59),(20,37),(25,29),(55,29),(61,38),(61,59)],'wood2')
    a.p([(30,61),(30,43),(35,38),(52,38),(57,44),(57,61)],'wood0')
    a.r((22,31,57,34),'wood4');a.r((21,60,62,65),'stone3')
    solid(room,'forge_masonry',(17,30,48,29))
    # Tool bench and quench basin, visibly different from the crate storeroom.
    terrace(a,(17,79,30,29),'wood');solid(room,'smith_bench',(17,79,30,29))
    for x,y in [(22,85),(35,87),(28,98)]:
        a.l([(x,y),(x+6,y-3)],'stone1',2);a.r((x+4,y-5,x+9,y-2),'stone4')
    a.e((191,100,220,120),'wood0');a.e((193,99,218,115),'stone3');a.e((196,101,215,112),'water2');a.l([(198,104),(209,104)],'water4')
    solid(room,'quenching_basin',(192,100,28,20))
    # Tall bell gantry is off the main floor. The bell itself is engine-owned.
    for x in (76,112):
        a.r((x,33,x+3,63),'wood1');a.r((x+1,34,x+1,61),'wood5')
        solid(room,'bell_gantry',(x,33,4,23))
    a.r((76,32,115,36),'wood0');a.r((77,32,114,33),'gold2');a.l([(96,36),(96,54)],'gold0')
    # Recessed tracks suggest order without revealing a solved sequence.
    for pts in [[(80,104),(80,124),(171,124),(171,56),(184,56)],[(152,104),(152,80),(184,80),(184,56)],[(96,64),(122,64),(122,46),(178,46)]]:
        a.l(pts,'stone2',3);a.l(pts,'gold1')
    for x,y in [(96,64),(184,56),(80,104),(152,104),(32,128)]:ring(a,x,y)
    a.r((175,31,213,39),'wood0');a.r((177,32,212,36),'gold2')
    for x in (181,189,197,205):a.l([(x,37),(x,45)],'gold1');a.e((x-2,43,x+2,47),'stone3')
    for key,kind,xy,spr,variants,ap in [
        ('bell','mechanism',(96,64),'BELL_IDLE',('BELL_RING',),(96,80)),
        ('forge','mechanism',(48,56),'FURNACE_IDLE',('FURNACE_LIT',),(48,72)),
        ('metal_latch','mechanism',(184,56),'LATCH_CLOSED',('LATCH_OPEN',),(184,72)),
        ('west_plate','pressure_plate',(80,104),'PLATE_UP',('PLATE_DOWN',),(80,120)),
        ('east_plate','pressure_plate',(152,104),'PLATE_UP',('PLATE_DOWN',),(152,120)),
        ('reset','reset',(32,128),'RESET_IDLE',('RESET_LIT',),(48,128))]:obj(room,key,kind,xy,spr,variants,ap)
    return room,a


def courtyard():
    room,a=new_room(3);soft_ground(a,477);indoor_frame(a,room)
    # The open terrace looks onto water beyond its balustrades at native screen edges.
    for x in (0,232):water(a,(x,0,8,152),903+x)
    a.r((12,31,227,149),'stone4')
    for y in range(35,148,18):
        for x in range(16,225,24):a.l([(x,y),(x+19,y)],'stone3');a.dot(x+1,y+1,'stone5')
    # Back wall relief: two wave bowls and a wind-shaped opening, no solution marks.
    a.r((80,5,159,26),'water0');a.r((83,7,156,24),'water2')
    for x in range(88,153,16):a.l([(x,16),(x+4,12),(x+8,16),(x+12,12)],'water4')
    for x in (24,198):
        a.r((x,6,x+16,25),'stone1');a.r((x+2,8,x+14,22),'plaster');a.e((x+5,12,x+11,18),'gold2')
    # Wide raised pool rims surround state-neutral socket floors.
    for x in (64,176):
        a.e((x-26,42,x+26,84),'shadowsoft');a.e((x-25,40,x+25,80),'stone1');a.e((x-23,40,x+23,77),'stone5');a.e((x-19,43,x+19,75),'water0');a.e((x-16,46,x+16,72),'stone3');a.e((x-8,56,x+8,70),'dirt2')
        a.l([(x-18,45),(x-11,42),(x+8,42)],'white')
        # All water collision belongs to the engine; the outer walkways stay generous.
        dynamic(room,'pool_'+str(x),(x-14,48,28,26),'Raised rim water zone; approach the lower lip at y88. State never blocks the reset corridor.')
    # Low dry channels are floor inlays, not walls.
    for pts in [[(64,84),(64,98),(120,98),(120,48)],[(176,84),(176,98),(120,98)]]:
        a.l(pts,'stone2',5);a.l(pts,'water1',3);a.l(pts,'water3')
    for x in (64,176):ring(a,x,112)
    for x,y in [(26,45),(216,123)]:
        a.r((x-9,y-7,x+9,y+10),'stone1');a.r((x-8,y-6,x+8,y+7),'moss2')
        reeds(a,x,y+5,5);solid(room,'reed_planter',(x-9,y-7,19,18))
    for x,y in [(207,47),(28,98)]:flowers(a,x,y,'flower0');flowers(a,x+4,y+2,'flower1')
    ring(a,32,132);a.l([(32,143),(100,143)],'stone3')
    for key,xy,kind,spr,variants,ap in [
        ('west_pool',(64,64),'pool','POOL_LOW',('POOL_HIGH',),(64,86)),
        ('east_pool',(176,64),'pool','POOL_LOW',('POOL_HIGH',),(176,86)),
        ('west_sluice',(64,112),'mechanism','SLUICE_CLOSED',('SLUICE_OPEN',),(64,130)),
        ('east_sluice',(176,112),'mechanism','SLUICE_CLOSED',('SLUICE_OPEN',),(176,130)),
        ('reset',(32,132),'reset','RESET_IDLE',('RESET_LIT',),(48,132))]:obj(room,key,kind,xy,spr,variants,ap)
    return room,a


def storehouse():
    room,a=new_room(4);indoor_frame(a,room,'wood')
    # Back-wall textile rolls, woven reed shutters, and cutaway rafters.
    for x in (16,63,109,170,222):a.r((x,0,x+3,30),'wood0');a.r((x+1,0,x+1,27),'wood5')
    for x,col in [(27,'water3'),(40,'rose4'),(74,'gold2'),(87,'pine4'),(143,'water3'),(156,'flower0'),(192,'gold3'),(205,'pine4')]:
        a.r((x-4,10,x+4,24),'wood1');a.r((x-3,11,x+3,23),col);a.e((x-4,8,x+4,13),'wood5');a.e((x-2,9,x+2,12),'wood2')
    # Deep shelves contain fixed cloth, never interactive crates.
    for x,y,w,h in [(16,40,25,64),(199,35,26,26),(196,110,28,22)]:
        rect(a,(x,y,w,h),'wood0');rect(a,(x+2,y+2,w-4,h-4),'wood3')
        for yy in range(y+7,y+h-4,14):
            a.r((x+2,yy+7,x+w-3,yy+9),'wood5')
            for xx,c in [(x+4,'water3'),(x+12,'flower0')]:a.r((xx,yy,xx+6,yy+6),c);a.l([(xx+1,yy+2),(xx+5,yy+2)],'gold4')
        solid(room,'textile_shelf',(x,y,w,h))
    # Four by eight delivery bays; joints provide an honest tile-grid reading.
    a.r((55,46,185,114),'wood1');a.r((57,48,183,112),'dirt3')
    for y in range(48,113,16):a.l([(57,y),(183,y)],'wood3')
    for x in range(56,185,16):a.l([(x,48),(x,112)],'wood3')
    for y in range(50,110,16):
        for x in range(59,180,16):a.dot(x,y,'dirt4')
    # Inlaid brass channels communicate linked parts without giving the solution.
    for pts in [[(80,56),(80,38),(120,38)],[(160,104),(188,104),(188,78),(208,78)]]:
        a.l(pts,'wood1',3);a.l(pts,'gold3')
    for x,y in [(80,56),(160,104),(208,80),(120,40),(32,128)]:ring(a,x,y,10,7)
    for x,y in [(78,127),(146,126)]:a.l([(x-4,y),(x+2,y),(x+4,y-3),(x+2,y-5)],'wood3')
    dynamic(room,'west_crate',(73,81,14,14),'Movable 16px parcel. Reset returns it to (80,88).')
    dynamic(room,'east_crate',(137,81,14,14),'Movable 16px parcel. Reset returns it to (144,88).')
    for key,kind,xy,spr,variants,ap in [
        ('west_crate','crate',(80,88),'CRATE',(),(80,104)),('east_crate','crate',(144,88),'CRATE',(),(144,104)),
        ('west_plate','pressure_plate',(80,56),'PLATE_UP',('PLATE_DOWN',),(80,72)),
        ('east_plate','pressure_plate',(160,104),'PLATE_UP',('PLATE_DOWN',),(160,120)),
        ('spindle','mechanism',(208,80),'SPINDLE_IDLE',('SPINDLE_LIT',),(208,96)),
        ('latch','mechanism',(120,40),'LATCH_CLOSED',('LATCH_OPEN',),(120,56)),
        ('reset','reset',(32,128),'RESET_IDLE',('RESET_LIT',),(48,128))]:obj(room,key,kind,xy,spr,variants,ap)
    return room,a


def garden():
    room,a=new_room(5);soft_ground(a,482);indoor_frame(a,room)
    a.r((12,31,227,150),'grasslit')
    paths(a,[([(120,160),(120,132),(64,120),(64,96),(72,72),(120,72),(144,104),(168,104),(184,80),(184,48)],19),
             ([(64,120),(200,136),(208,64),(184,48)],16),
             ([(64,96),(40,106),(32,132)],17)])
    # Sunny raised beds shape a real garden loop around the exercise route.
    for x,y,w,h in [(17,34,32,48),(87,91,25,20),(138,38,26,20),(191,94,30,22)]:
        terrace(a,(x,y,w,h));rect(a,(x+3,y+2,w-6,h-8),'moss1')
        for xx in range(x+7,x+w-4,7):
            for yy in range(y+7,y+h-6,10):flowers(a,xx,yy,'flower0' if xx%2 else 'flower1');a.e((xx-3,yy+2,xx+3,yy+4),'pine4')
        solid(room,'raised_flower_bed',(x,y,w,h))
    # A low tea pavilion looks into the sky at the north edge.
    a.r((55,5,185,24),'water1');a.r((57,7,183,22),'water3')
    for x in (63,95,143,177):a.r((x,3,x+3,29),'wood1');a.r((x+1,4,x+1,25),'wood5')
    a.l([(59,12),(90,8),(115,14),(148,9),(182,12)],'wood1')
    for x,y in [(77,12),(123,15),(164,12)]:
        a.r((x-3,y,x+3,y+6),'gold2');a.r((x-2,y+1,x+2,y+5),'gold4');a.dot(x,y+8,'rose3')
    for x,y in [(72,72),(120,72),(168,104),(184,48)]:ring(a,x,y,11,7)
    # Familiar leaf motif indicates the start; no number/order is baked in.
    a.e((56,117,69,124),'moss2');a.l([(58,123),(67,118)],'pine2')
    for x,y in [(122,114),(80,39),(217,38),(52,142)]:flowers(a,x,y,'flower1')
    for key,kind,xy,spr,variants,ap in [
        ('step_west','step',(72,72),'STEP_IDLE',('STEP_LIT',),(72,88)),
        ('step_center','step',(120,72),'STEP_IDLE',('STEP_LIT',),(120,88)),
        ('step_east','step',(168,104),'STEP_IDLE',('STEP_LIT',),(168,120)),
        ('garden_gong','mechanism',(184,48),'BELL_IDLE',('BELL_RING',),(184,64)),
        ('garden_start','sign',(64,120),'SIGN_GARDEN',(),(64,136)),
        ('reset','reset',(32,132),'RESET_IDLE',('RESET_LIT',),(48,132))]:obj(room,key,kind,xy,spr,variants,ap)
    return room,a


def npc_sprite(kind):
    a=Art(16,16,'transparent')
    # Six distinct residents: silhouette, work wear, headwear and carried detail.
    coats=[('wood1','wood3','gold3'),('purple1','purple3','flower1'),('water0','water2','leafwarm'),('rose1','rose4','gold3'),('pine1','pine4','gold4'),('wood2','wood4','water3')]
    edge,body,trim=coats[kind]
    a.e((3,13,13,15),'shadow')
    a.r((5,12,7,14),'wood0');a.r((9,12,11,14),'wood0')
    a.r((5,13,6,13),'wood3');a.r((9,13,10,13),'wood3')
    a.p([(5,6),(10,6),(12,8),(13,12),(10,13),(5,13),(3,11),(4,8)],edge)
    a.r((5,7,10,11),body);a.l([(7,7),(7,11)],trim);a.r((5,11,10,11),trim)
    a.r((3,8,4,11),'skin1');a.r((11,8,12,10),'skin2')
    a.p([(5,2),(10,2),(11,4),(10,7),(6,7),(4,5)],'skin0')
    a.r((5,3,10,5),'skin2');a.r((6,6,9,6),'skin1');a.dot(6,4,'ink');a.dot(9,4,'ink')
    a.r((5,1,10,2),'wood0');a.r((4,2,5,4),'wood0')
    if kind==0: # Broad smith's headscarf, leather apron and hammer.
        a.r((5,1,10,2),'water1');a.r((5,1,10,1),'water4');a.r((5,8,10,12),'wood1');a.r((6,9,9,11),'wood3')
        a.l([(12,11),(13,6)],'wood4');a.r((11,5,15,7),'stone1');a.r((12,5,15,5),'stone4')
    elif kind==1: # Weaver's knot and diagonal teal sash with a visible spool.
        a.e((8,0,12,3),'wood0');a.dot(11,1,'gold3');a.l([(5,7),(10,11)],'water3',2)
        a.r((12,9,14,12),'gold3');a.r((11,8,15,8),'wood3');a.r((11,12,15,12),'wood3');a.l([(12,10),(14,10)],'water2')
    elif kind==2: # Reed warden's broad conical hat and staff.
        a.p([(2,3),(7,0),(9,0),(14,3),(14,4),(2,4)],'wood1');a.p([(3,3),(7,1),(9,1),(13,3)],'wood4');a.l([(5,2),(10,2)],'wood5')
        a.l([(13,6),(13,14)],'wood2');a.dot(13,5,'leafwarm');a.l([(11,7),(13,8)],'skin2')
    elif kind==3: # Shrine keeper's tidy cap and offering tray.
        a.r((5,0,10,2),'rose1');a.r((6,0,9,1),'rose4');a.r((4,9,12,11),'wood1');a.r((4,9,12,9),'gold3');a.dot(8,8,'flower1')
    elif kind==4: # Apprentice's short sleeves and bright training headband.
        a.r((5,1,10,3),'wood0');a.r((4,3,11,3),'rose4');a.dot(3,3,'rose5');a.r((6,8,10,10),'pine4')
        a.l([(12,12),(14,8)],'wood4');a.dot(14,7,'wood5')
    else:
        a.r((5,1,10,2),'wood4');a.r((4,2,11,2),'wood5');a.r((5,8,10,12),'plaster');a.r((6,10,9,11),'water2');a.r((11,10,14,12),'wood2');a.l([(11,10),(14,10)],'gold3')
    return a


def sprite(name):
    a=Art(16,16,'transparent')
    if name.startswith('NPC_'):return npc_sprite(['NPC_SMITH','NPC_WEAVER','NPC_WARDEN','NPC_REST_KEEPER','NPC_APPRENTICE','NPC_MERCHANT'].index(name))
    if name.startswith('RACK_'):
        a.e((1,12,14,15),'shadow');a.r((2,5,13,7),'wood0');a.r((3,5,12,6),'wood4')
        for x in (3,12):a.r((x,4,x+1,13),'wood1');a.dot(x,4,'wood5')
        a.l([(2,13),(5,13)],'wood4');a.l([(11,13),(14,13)],'wood4')
        if name=='RACK_SWORD':
            a.l([(7,11),(7,1)],'stone0',3);a.l([(7,1),(7,8)],'stone5');a.r((5,8,10,9),'gold2');a.r((7,10,8,12),'wood2')
        elif name=='RACK_LANCE':
            a.r((7,2,8,14),'wood2');a.r((7,3,7,13),'wood5');a.p([(6,4),(6,2),(8,0),(10,3),(8,5)],'stone4');a.l([(8,1),(8,4)],'white')
        else:
            a.l([(7,1),(10,3),(11,6),(10,10),(7,12)],'wood0',3);a.l([(7,1),(9,3),(10,6),(9,10),(7,12)],'gold2');a.l([(7,2),(7,11)],'white');a.l([(5,7),(12,7)],'wood3');a.dot(12,7,'stone5')
    elif name.startswith('TARGET_'):
        a.e((2,13,13,15),'shadow');a.r((6,8,9,14),'wood1');a.l([(4,14),(11,14)],'wood3')
        a.e((1,1,14,12),'wood0');a.e((2,2,13,11),'wood4');a.e((4,3,11,10),'rose3');a.e((6,5,9,8),'gold4')
        if name=='TARGET_HIT':a.l([(8,7),(15,3)],'wood0',2);a.l([(8,6),(14,3)],'stone5');a.dot(14,2,'water3')
    elif name.startswith('RESET_'):
        a.e((1,10,14,15),'shadow');a.r((2,10,13,13),'stone0');a.r((3,9,12,12),'stone3');a.r((4,4,11,9),'stone1');a.r((5,4,10,8),'water2' if name.endswith('LIT') else 'stone4')
        a.l([(10,3),(6,2),(3,5),(4,8)],'gold3',2);a.p([(2,7),(6,7),(5,10)],'gold3');a.dot(6,3,'gold4')
        if name.endswith('LIT'):a.dot(12,4,'gold4');a.dot(8,0,'white')
    elif name.startswith('SLUICE_'):
        a.e((1,12,14,15),'shadow');a.r((4,8,11,13),'stone1');a.r((5,8,10,11),'stone4');a.l([(7,4),(7,10)],'wood0',3)
        a.e((2,1,13,10),'wood0');a.e((3,2,12,9),'gold2');a.e((5,4,10,7),'wood0')
        if name=='SLUICE_OPEN':a.l([(4,8),(11,3)],'gold4',2)
        else:a.l([(4,3),(11,8)],'gold4',2)
        a.dot(7,5,'stone5')
    elif name.startswith('BELL_'):
        a.r((7,0,8,3),'gold1');a.p([(5,3),(10,3),(12,6),(12,10),(14,12),(13,13),(2,13),(1,12),(3,10),(3,6)],'wood0')
        a.p([(6,3),(9,3),(11,6),(11,10),(13,12),(3,12),(4,10),(4,6)],'gold1');a.l([(5,6),(6,4),(8,4)],'gold4');a.r((4,10,11,11),'gold3');a.r((7,13,8,14),'wood2')
        if name=='BELL_RING':a.l([(0,4),(0,8)],'gold3');a.l([(15,4),(15,8)],'gold3');a.dot(2,2,'gold4');a.dot(13,2,'gold4')
    elif name.startswith('LATCH_'):
        a.r((2,2,13,13),'stone0');a.r((3,3,12,12),'stone3');a.r((4,4,11,11),'wood1')
        for x in (3,12):
            for y in (3,12):a.dot(x,y,'gold4')
        if name=='LATCH_CLOSED':a.r((3,6,13,9),'gold0');a.r((3,6,12,7),'gold3');a.r((7,5,9,10),'stone1');a.dot(8,7,'white')
        else:a.r((3,6,7,9),'gold0');a.r((3,6,7,7),'gold3');a.p([(9,7),(11,9),(15,4),(14,3),(11,7)],'leafwarm')
    elif name=='CRATE':
        a.e((0,12,15,15),'shadow');a.r((1,1,14,13),'wood0');a.r((2,2,13,12),'wood3');a.r((3,3,12,11),'wood2')
        a.l([(3,3),(12,11)],'wood5',2);a.l([(3,11),(12,3)],'wood4',2);a.r((2,2,13,3),'wood5');a.r((2,11,13,12),'wood1')
        for x in (3,12):
            for y in (3,11):a.dot(x,y,'gold3')
    elif name.startswith('PLATE_'):
        a.p([(1,5),(4,2),(12,2),(15,5),(15,12),(2,13),(1,11)],'stone0');a.p([(2,5),(5,3),(11,3),(14,5),(14,10),(3,11)],'stone3')
        col='water3' if name=='PLATE_DOWN' else 'gold2'
        a.r((4,5,11,9),col);a.p([(7,5),(10,7),(7,9),(5,7)],'gold4' if name=='PLATE_DOWN' else 'wood1');a.l([(3,11),(13,11)],'stone5')
    elif name.startswith('POOL_'):
        a.e((0,1,15,14),'water0');a.e((1,2,14,13),'water2' if name=='POOL_HIGH' else 'stone3')
        if name=='POOL_HIGH':
            a.l([(2,5),(7,5),(9,4),(13,4)],'water4');a.l([(4,10),(9,10),(11,9),(14,9)],'water3');a.dot(3,4,'watergleam')
        else:
            a.e((4,7,12,12),'water1');a.l([(6,9),(10,9)],'water3');a.r((3,3,4,4),'stone5');a.dot(11,5,'stone5')
    elif name.startswith('BRIDGE_'):
        if name=='BRIDGE_WOOD':
            a.r((1,0,14,15),'wood0');a.r((2,0,13,15),'wood3')
            for y in (0,4,8,12):a.r((2,y,13,y+1),'wood5');a.r((3,y+3,12,y+3),'wood1')
        else:
            a.l([(2,15),(5,10),(4,4),(7,0)],'wood0',5);a.l([(12,15),(10,10),(11,4),(9,0)],'wood0',5)
            a.l([(2,15),(5,10),(4,4),(7,0)],'wood3',3);a.l([(12,15),(10,10),(11,4),(9,0)],'wood4',3)
            for y in (3,8,13):a.l([(3,y),(12,y-1)],'wood5',2)
            a.e((0,8,5,11),'pine4');a.e((10,1,15,4),'pine3')
    elif name.startswith('REST_'):
        a.e((1,11,14,15),'shadow');a.r((2,10,13,13),'stone1');a.r((3,10,12,11),'stone4');a.r((6,5,9,10),'wood2')
        a.p([(2,3),(4,1),(11,1),(14,3),(12,5),(3,5)],'wood0');a.r((4,3,11,8),'gold0');a.r((5,4,10,7),'gold4' if name=='REST_LIT' else 'gold2');a.r((7,3,8,8),'wood1')
        a.l([(4,2),(11,2)],'water3');a.dot(8,12,'gold4')
        if name=='REST_LIT':a.dot(1,6,'gold3');a.dot(14,7,'gold4');a.dot(10,0,'white')
    elif name.startswith('SIGN_'):
        a.e((2,13,13,15),'shadow');a.r((7,6,8,14),'wood1');a.r((2,2,13,10),'wood0');a.r((3,3,12,9),'plaster');a.l([(3,3),(12,3)],'wood5')
        if name=='SIGN_WORKSHOP':a.l([(6,8),(10,4)],'wood2',2);a.r((8,4,11,5),'stone1')
        elif name=='SIGN_WEAVER':a.r((6,4,9,8),'water2');a.r((5,4,10,4),'wood2');a.r((5,8,10,8),'wood2');a.l([(6,6),(9,6)],'water4')
        elif name=='SIGN_GARDEN':a.p([(5,7),(5,5),(8,4),(10,5),(9,8),(6,8)],'pine3');a.l([(6,7),(9,5)],'pine5')
        else:a.l([(4,6),(6,5),(8,7),(10,5),(11,6)],'water1');a.l([(5,8),(10,8)],'water3')
    elif name.startswith('REED_'):
        for x,h in [(2,10),(5,13),(8,11),(11,14),(14,9)]:
            bend=-3 if name=='REED_PARTED' and x<8 else 3 if name=='REED_PARTED' else 0
            a.l([(x,15),(x+bend,15-h)],'pine2');a.r((x+bend-1,14-h,x+bend+1,17-h),'moss2');a.dot(x+bend-1,14-h,'moss3');a.l([(x,12),(x-2,9)],'pine4')
    elif name.startswith('SPINDLE_'):
        a.e((2,12,13,15),'shadow');a.r((7,1,8,14),'wood1');a.r((4,4,11,11),'water2' if name=='SPINDLE_IDLE' else 'gold2')
        for y in (5,7,9):a.l([(4,y),(11,y-1)],'water4' if name=='SPINDLE_IDLE' else 'gold4')
        a.r((3,3,12,4),'wood3');a.r((3,11,12,12),'wood3');a.l([(4,3),(11,3)],'wood5');a.dot(7,0,'gold4')
    elif name.startswith('FURNACE_'):
        a.p([(2,14),(2,6),(5,2),(11,2),(14,6),(14,14)],'stone0');a.p([(3,12),(3,6),(6,3),(10,3),(13,6),(13,12)],'wood2');a.r((5,6,11,12),'wood0')
        a.l([(4,5),(11,5)],'wood4');a.r((2,13,14,14),'stone4')
        if name=='FURNACE_LIT':a.p([(5,12),(5,9),(7,10),(8,6),(11,10),(10,12)],'fire1');a.p([(7,12),(8,8),(9,11)],'gold3');a.dot(8,11,'gold4')
        else:a.l([(5,11),(10,11)],'stone1');a.dot(8,10,'stone2')
    elif name.startswith('STEP_'):
        a.p([(1,6),(5,2),(12,2),(15,6),(14,12),(3,13),(1,10)],'stone1');a.p([(2,6),(6,3),(11,3),(14,6),(13,10),(4,11),(2,9)],'stone4');a.l([(4,4),(11,4)],'stone5')
        a.p([(7,4),(11,7),(8,10),(4,8)],'gold2' if name=='STEP_LIT' else 'moss1');a.l([(6,8),(9,5)],'gold4' if name=='STEP_LIT' else 'moss3')
    else:raise ValueError(name)
    return a


SPRITE_NAMES=[
    'NPC_SMITH','NPC_WEAVER','NPC_WARDEN','NPC_REST_KEEPER','NPC_APPRENTICE','NPC_MERCHANT',
    'RACK_SWORD','RACK_LANCE','RACK_BOW','TARGET_READY','TARGET_HIT',
    'RESET_IDLE','RESET_LIT','SLUICE_CLOSED','SLUICE_OPEN','BELL_IDLE','BELL_RING','LATCH_CLOSED','LATCH_OPEN',
    'CRATE','PLATE_UP','PLATE_DOWN','POOL_LOW','POOL_HIGH','BRIDGE_WOOD','BRIDGE_ROOT','REST_IDLE','REST_LIT',
    'SIGN_WORKSHOP','SIGN_WEAVER','SIGN_GARDEN','SIGN_TIDE','REED_SCREEN','REED_PARTED',
    'SPINDLE_IDLE','SPINDLE_LIT','FURNACE_IDLE','FURNACE_LIT','STEP_IDLE','STEP_LIT']


def occupancy(room,closed):
    w,h=room['width'],room['height']
    im=Image.new('1',(w,h),0);d=ImageDraw.Draw(im)
    # Foot square touches each half-open collider exactly as x +/- 5, y +/- 5.
    d.rectangle((0,0,w-1,RADIUS-1),fill=1);d.rectangle((0,h-RADIUS,w-1,h-1),fill=1)
    d.rectangle((0,0,RADIUS-1,h-1),fill=1);d.rectangle((w-RADIUS,0,w-1,h-1),fill=1)
    rects=[v['rect'] for v in room['solids']]
    if closed:rects += [v['rect'] for v in room['dynamic_rectangles'] if v['closed_by_default']]
    for x,y,rw,rh in rects:d.rectangle((x-RADIUS,y-RADIUS,x+rw-1+RADIUS,y+rh-1+RADIUS),fill=1)
    return bytearray(im.tobytes('raw','L'))


def verify_room(room):
    w,h=room['width'],room['height'];results={};saved_routes={}
    targets=[('spawn_'+key,xy) for key,xy in room['spawns'].items()]
    targets += [('exit_'+v['key'],v['approach']) for v in room['exits']]
    targets += [('object_'+v['key'],v['approach']) for v in room['objects']]
    start=room['spawns']['0'];s=start[1]*w+start[0]
    for closed in (False,True):
        blocked=occupancy(room,closed)
        assert not blocked[s], (room['key'],'spawn blocked',start)
        visited=bytearray(w*h);visited[s]=1;q=deque([s]);parent={s:None}
        while q:
            p=q.popleft();x=p%w;y=p//w
            for n in (p-1,p+1,p-w,p+w):
                if 0<=n<w*h and not blocked[n] and not visited[n] and abs(n%w-x)+abs(n//w-y)==1:
                    visited[n]=1;parent[n]=p;q.append(n)
        proof=[]
        for key,(x,y) in targets:
            assert 0<=x<w and 0<=y<h and not blocked[y*w+x],(room['key'],key,'blocked approach',x,y,'closed',closed)
            p=y*w+x;assert visited[p],(room['key'],key,'unreachable',x,y,'closed',closed)
            route=[]
            while p is not None:route.append([p%w,p//w]);p=parent[p]
            route.reverse()
            proof.append({'target':key,'point':[x,y],'cardinal_steps':len(route)-1})
            if not closed and key.startswith('exit_'):saved_routes[key]=route
        results['all_dynamic_closed' if closed else 'all_dynamic_open']={'reachable_pixels':sum(visited),'targets':proof}
    return results,saved_routes


def odd_bitmap(data,w,h):
    return b''.join(data[y*w+1:(y+1)*w]+data[(y+1)*w-1:(y+1)*w] for y in range(h))


def cbytes(lines,name,data,shape=None):
    lines.append(f'const unsigned char {name}[{shape or len(data)}] __attribute__((aligned(4))) = {{\n')
    for s in range(0,len(data),32):lines.append('  '+','.join(map(str,data[s:s+32]))+',\n')
    lines.append('};\n\n')


def emit():
    header='''/* Generated by assets/generate_region.py. Original regional art. */
#ifndef EMBERBOND_REGION_ART_H
#define EMBERBOND_REGION_ART_H
#define REGION_ART_FIRST_ROOM 16
#define REGION_ART_ROOM_COUNT 6
#define REGION_ART_FOOT_RADIUS 5
/* Pixel centers use a five-pixel foot radius. Rectangles are half-open. */
typedef struct { short x, y, w, h; } RegionArtRect;
typedef struct {
    unsigned short width, height;
    const unsigned char *bitmap;
    /* Row-local left-shift atlas; NULL in stationary 240x160 interiors.
       Odd camera X: source = bitmap_odd + y*width + camera_x - 1.
       Even camera X: source = bitmap + y*width + camera_x.
       Source atlases are aligned(4); copy 240 bytes for each of 160 rows. */
    const unsigned char *bitmap_odd;
    const RegionArtRect *solids;
    unsigned short solid_count;
} RegionArtRoom;
extern const RegionArtRoom region_art_rooms[REGION_ART_ROOM_COUNT];
/* All runtime actors/stateful props remain separate. Center anchor: x-8,y-8.
   Zero is transparent. Sprite data is ROW MAJOR, matching obj_upload input. */
enum {
'''
    header += ''.join(f'    REGION_SPR_{name} = {i},\n' for i,name in enumerate(SPRITE_NAMES))
    header += f'    REGION_SPR_COUNT = {len(SPRITE_NAMES)}\n}};\nextern const unsigned char region_sprites[REGION_SPR_COUNT][256];\n'
    lines=[];bitmap_bytes=0;collision_bytes=0
    for room in ROOMS:
        key=room['key'];w,h=room['width'],room['height'];data=room['art'].im.tobytes()
        assert len(data)==w*h and min(data)>0 and max(data)<len(COLORS)
        header += f'extern const unsigned char region_background_{key}[{len(data)}];\n'
        cbytes(lines,'region_background_'+key,data);bitmap_bytes+=len(data)
        room['bitmap_sha256']=hashlib.sha256(data).hexdigest()
        if w>240:
            odd=odd_bitmap(data,w,h);header += f'extern const unsigned char region_background_{key}_odd[{len(odd)}];\n'
            cbytes(lines,'region_background_'+key+'_odd',odd);bitmap_bytes+=len(odd)
            room['odd_bitmap_sha256']=hashlib.sha256(odd).hexdigest()
            # Verify native full-screen copies for camera X 0..240, all four mod4 values.
            checks=0
            for cy in (0,1,79,80,159,160):
                for cx in range(0,241):
                    source=odd if cx&1 else data;offset=cx-1 if cx&1 else cx
                    assert offset%2==0
                    for yy in (0,1,79,159):
                        assert source[(cy+yy)*w+offset:(cy+yy)*w+offset+240]==data[(cy+yy)*w+cx:(cy+yy)*w+cx+240]
                    checks+=1
            room['dma_camera_checks']=checks
        solids=room['solids'];collision_bytes+=8*len(solids)
        header += f'#define REGION_{key.upper()}_SOLID_COUNT {len(solids)}\nextern const RegionArtRect region_{key}_solids[REGION_{key.upper()}_SOLID_COUNT];\n'
        lines.append(f'const RegionArtRect region_{key}_solids[REGION_{key.upper()}_SOLID_COUNT] = {{\n')
        lines += ['  {'+','.join(map(str,s['rect']))+'},\n' for s in solids];lines.append('};\n\n')
    lines.append('const unsigned char region_sprites[REGION_SPR_COUNT][256] __attribute__((aligned(4))) = {\n')
    for name,a in SPRITES:
        data=a.im.tobytes();assert len(data)==256 and 0 in data and max(data)<len(COLORS)
        lines.append(f'  {{ /* REGION_SPR_{name} */\n')
        for s in range(0,256,32):lines.append('    '+','.join(map(str,data[s:s+32]))+',\n')
        lines.append('  },\n')
    lines.append('};\n\nconst RegionArtRoom region_art_rooms[REGION_ART_ROOM_COUNT] = {\n')
    for room in ROOMS:
        key=room['key'];odd='region_background_'+key+'_odd' if room['width']>240 else '0'
        lines.append(f'  {{{room["width"]},{room["height"]},region_background_{key},{odd},region_{key}_solids,REGION_{key.upper()}_SOLID_COUNT}},\n')
    lines.append('};\n')
    (SRC/'region_art.h').write_text(header+'#endif\n')
    folder=SRC/'region_art_data';folder.mkdir(exist_ok=True)
    chunks=[];part=[];size=0
    for line in lines:
        n=len(line.encode())
        if part and size+n>CHUNK_LIMIT:chunks.append(''.join(part));part=[];size=0
        part.append(line);size+=n
    if part:chunks.append(''.join(part))
    for f in folder.glob('part_*.inc'):f.unlink()
    for i,chunk in enumerate(chunks):(folder/f'part_{i:03d}.inc').write_text(chunk)
    (SRC/'region_art.c').write_text('#include "region_art.h"\n\n/* Generated immutable data in bounded <=32000-byte includes. */\n'+''.join(f'#include "region_art_data/part_{i:03d}.inc"\n' for i in range(len(chunks))))
    return {'bitmap_bytes':bitmap_bytes,'sprite_bytes':len(SPRITES)*256,'collision_bytes':collision_bytes,'arm32_room_table_bytes':len(ROOMS)*20,
        'rom_payload_bytes':bitmap_bytes+len(SPRITES)*256+collision_bytes+len(ROOMS)*20,
        'chunks':len(chunks),'largest_chunk_bytes':max(len(c.encode()) for c in chunks),'chunk_limit_bytes':CHUNK_LIMIT}


def paste_sprite(dst,a,x,y):
    mask=Image.frombytes('L',(16,16),bytes(255 if p else 0 for p in a.im.tobytes()))
    dst.paste(a.im.convert('RGB'),(x-8,y-8),mask)


def previews():
    lookup=dict(SPRITES);OUT.mkdir(exist_ok=True)
    (OUT/'sprites').mkdir(exist_ok=True);(OUT/'camera').mkdir(exist_ok=True)
    for name,a in SPRITES:
        a.im.info['transparency']=0;a.im.save(OUT/'sprites'/f'{name.lower()}.png',transparency=0)
    # Native asset sheet has labels in its own margin, never in the game pixels.
    sw=512;sh=24+((len(SPRITES)+7)//8)*52
    sheet=Image.new('RGB',(sw,sh),(29,44,51));d=ImageDraw.Draw(sheet)
    d.text((8,5),'REEDHAVEN - NATIVE 16x16 ORIGINAL SPRITES',(247,236,193))
    for i,(name,a) in enumerate(SPRITES):
        x=(i%8)*64;y=24+(i//8)*52;paste_sprite(sheet,a,x+32,y+10)
        label=name.replace('NPC_','N_').replace('SLUICE','SLUIC').replace('FURNACE','FORGE').replace('WORKSHOP','SMITH')
        d.text((x+2,y+23),f'{i:02}',(176,208,193));d.text((x+2,y+35),label[:10],(247,236,193))
    sheet.save(OUT/'sprite_sheet_native.png');sheet.resize((sw*3,sh*3),Image.Resampling.NEAREST).save(OUT/'sprite_sheet_3x.png')
    # Full-world backgrounds and labeled staged previews. Only the latter include NPCs.
    contact=Image.new('RGB',(976,704),(25,42,47));cd=ImageDraw.Draw(contact)
    cd.text((8,5),'ORIGINAL REEDHAVEN REGION | NATIVE PIXEL ART | staged actors are separate assets',(250,238,192))
    crop_sheet=Image.new('RGB',(736,800),(25,42,47));cspd=ImageDraw.Draw(crop_sheet)
    cspd.text((8,5),'240x160 NATIVE CAMERA CROPS | no stretching or reserved HUD strip',(250,238,192))
    ci=0
    for i,room in enumerate(ROOMS):
        a=room['art'];key=room['key'];a.im.save(OUT/f'{key}.png')
        scene=a.im.convert('RGB')
        for o in room['objects']:paste_sprite(scene,lookup[o['sprite']],*o['center'])
        scene.save(OUT/f'{key}_staged.png')
        if i<2:pos=(8+i*488,40)
        else:pos=(8+(i-2)*244,400)
        cd.text((pos[0],pos[1]-15),f'{room["id"]}: {room["name"]}',(250,238,192));contact.paste(scene,pos)
        collision=a.im.convert('RGBA');layer=Image.new('RGBA',a.im.size);dd=ImageDraw.Draw(layer)
        for s in room['solids']:
            x,y,w,h=s['rect'];dd.rectangle((x,y,x+w-1,y+h-1),fill=(239,68,82,75),outline=(239,68,82,180))
        for s in room['dynamic_rectangles']:
            x,y,w,h=s['rect'];dd.rectangle((x,y,x+w-1,y+h-1),fill=(239,177,35,95),outline=(255,227,89,255))
        for route in room['routes'].values():dd.line([tuple(p) for p in route],fill=(255,247,201,255),width=1)
        for o in room['objects']:
            x,y=o['approach'];dd.ellipse((x-2,y-2,x+2,y+2),fill=(89,255,212,255))
        Image.alpha_composite(collision,layer).convert('RGB').save(OUT/f'{key}_collision.png')
        # Show four representative full-native views for each exterior and one per interior.
        selected=room['camera_crops'][:4]
        for j,(x,y) in enumerate(selected):
            crop=scene.crop((x,y,x+240,y+160));crop.save(OUT/'camera'/f'{key}_{x}_{y}.png')
            px=8+(ci%3)*244;py=40+(ci//3)*188
            cspd.text((px,py-15),f'{room["id"]}: ({x},{y}) 240x160',(250,238,192));crop_sheet.paste(crop,(px,py));ci+=1
    cd.text((8,585),'TOP: 480x320 scrolling town and basin. BOTTOM: four distinct 240x160 puzzle spaces.',(250,238,192))
    cd.text((8,602),'All functional NPCs, equipment racks, handles, bells, latches, crates, plates and pool states are separate sprites.',(185,211,197))
    cd.text((8,619),'Collision proofs: cardinal movement, five-pixel feet; open AND all-default-closed mechanisms.',(185,211,197))
    cd.text((8,636),'Preview only. Quest rules, unlocked states and rewards are implemented by the game.',(185,211,197))
    contact.save(OUT/'region_preview_native.png');contact.resize((1952,1408),Image.Resampling.NEAREST).save(OUT/'region_preview_2x.png')
    crop_sheet.save(OUT/'native_camera_sheet.png');crop_sheet.resize((1472,1600),Image.Resampling.NEAREST).save(OUT/'native_camera_sheet_2x.png')


def main():
    contract_before=(OUT/'contract.json').read_bytes();ROOMS.clear();SPRITES.clear()
    for fn in (town,basin,foundry,courtyard,storehouse,garden):
        room,a=fn();color_background(a,'forest');room['art']=a
    SPRITES.extend((name,sprite(name)) for name in SPRITE_NAMES)
    all_proofs={}
    for room in ROOMS:
        proof,routes=verify_room(room);room['routes']=routes;all_proofs[room['key']]=proof
        for o in room['objects']:
            assert o['sprite'] in SPRITE_NAMES
            assert sum(abs(c-p) for c,p in zip(o['center'],o['approach'])) < o['interaction_radius'], (room['key'],o['key'],'interaction range')
            o['sprite_index']=SPRITE_NAMES.index(o['sprite'])
            o['state_sprite_indices']=[SPRITE_NAMES.index(v) for v in o['state_sprites']]
    budget=emit();previews()
    layout={'schema':1,'art':'Original geometric pixel art with unmodified RGB555 palette; no outside artwork.',
      'coordinate_contract':'All positions are world pixel centers. Rectangles are [x,y,width,height], half-open. Actor sprites center at x-8,y-8. Five-pixel feet use cardinal-only route proofs.',
      'palette':{'source':'assets/generate_assets.py','entries':len(COLORS),'palette_rgb_bytes_sha256':PALETTE_HASH,'transparent_index':0,'native_rgb555_preview':True,'ramp':'sunlit'},
      'background_rules':'Opaque immutable native backgrounds. No moving actors or stateful mechanisms are baked. Foreground export is intentionally absent: silhouettes and clear routes do not require foreground compositing.',
      'sprites':{'size':[16,16],'layout':'row-major','names':SPRITE_NAMES,'indices':{n:i for i,n in enumerate(SPRITE_NAMES)},'anchor':'center','transparency_index':0},
      'rooms':[{k:v for k,v in room.items() if k not in ('art','routes')} for room in ROOMS],
      'generated':budget,'proof_file':'validation.json','public_preview':'region_preview_native.png'}
    (OUT/'layout.json').write_text(json.dumps(layout,indent=2)+'\n')
    validation={'foot_radius':RADIUS,'movement':'four cardinal neighbors at one-pixel steps; no diagonal corner clipping','routes':all_proofs,
        'palette_unchanged':hashlib.sha256(bytes(PAL)).hexdigest()==PALETTE_HASH,'opaque_backgrounds':True,'native_camera_checks':sum(r.get('dma_camera_checks',0) for r in ROOMS),'budget':budget}
    (OUT/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
    (OUT/'README.md').write_text('''# Reedhaven original region artwork

Generated with `python3 assets/generate_region.py`. Test with `python3 tests/test_region_art.py`.

- Running `make assets` also creates `region_preview_native.png`, a labeled native-pixel overview; `_2x` uses nearest-neighbor only. These redundant large contact sheets are generated locally rather than included in the source archive
- The locally generated `native_camera_sheet.png` shows real 240x160 crops, with actors staged separately. Individual room/camera images are included
- Six named backgrounds are opaque indexed PNGs; `_staged` files are previews, never ROM inputs
- `sprites/*.png` are original transparent native 16x16 assets, named by their public enum
- `layout.json` holds exact static geometry, dynamic rectangles, approaches, exits and sprite indices
- `validation.json` proves all exits, spawns and interaction approaches with 5px square feet in both mechanism states
- The fixed `contract.json` is read-only to this generator

## Engine integration

Compile `src/region_art.c`. Include `src/region_art.h`. Room index is `room - REGION_ART_FIRST_ROOM` (16).
`region_art_rooms[index]` supplies width/height, bitmap, bitmap_odd, solids and solid_count.
Exterior atlases are aligned to four bytes. For odd camera X use `bitmap_odd + row*width + camera_x-1`; even X uses `bitmap + row*width + camera_x`. Copy 240 bytes for all 160 rows. Interior cameras stay (0,0), so their odd pointer is null.
All collision rectangles are half-open and include world edges. Building/tree rectangles intentionally exclude their opaque projected roof/canopy silhouettes: without a foreground pass, these are impassable scenery islands. No required route passes behind a roof. Eaves may overhang the exclusion by a few decorative pixels, but all doors and 5px-foot approaches are proved clear. Add only the runtime dynamic rectangles recorded in `layout.json`; never duplicate them as permanent scenery walls. `region_sprites[REGION_SPR_*]` is row-major 16x16 for the existing obj_upload path, with index zero transparent. Dynamic bridge tiles can be repeated over the exact bridge rectangle.

The gate/latch art encodes no quest solution. The background supplies neutral sockets, inlays and local visual clues; runtime state owns all changing props. This is an artwork/navigation contract, not proof of implemented or completed quest logic.
''')
    assert (OUT/'contract.json').read_bytes()==contract_before
    print(json.dumps({'rooms':len(ROOMS),'sprites':len(SPRITES),'proof_targets':sum(len(v['all_dynamic_open']['targets']) for v in all_proofs.values()),**budget},indent=2))


if __name__=='__main__':main()
