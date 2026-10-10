#!/usr/bin/env python3
"""Original code-native campaign pixel art for Emberbond, deterministically authored.

Install beside generate_assets.py, then run this script. For an isolated bundle:
  python assets/generate_campaign.py --base /path/to/assets/generate_assets.py
Uses only the existing RGB555 palette; never modifies/import-runs its main().
All coordinates in campaign_layouts.json are half-open [x,y,w,h]. Actors and
stateful props are NOT baked into backgrounds. Every exported C array is const.
"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import argparse, importlib.util, io, json, hashlib, math, random, sys
# Do not write Python bytecode beside a read-only or externally supplied base.
sys.dont_write_bytecode = True

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
SRC = ROOT / 'src'
P = {}; PAL = []; RGB = []; Art = None
import connected_road_art as roads
DIRECTIONS = ('down', 'up', 'left', 'right')
PROP_NAMES = ('VANE','WEIGHT','WELL','FIRE_SOCKET','NATURE_SOCKET','WIND_SOCKET',
              'STONE_SOCKET','BRAZIER','LAMP','REST','SIGN','CHIME')


def rect(a, r, c):
    x,y,w,h=r
    a.r((x,y,x+w-1,y+h-1),c)


def clipped(a,r,fn):
    """Draw architecture without letting raised silhouettes change its footprint."""
    b=Art(240,160,'transparent'); fn(b)
    x,y,w,h=r
    a.im.paste(b.im.crop((x,y,x+w,y+h)),(x,y))
    a.d=ImageDraw.Draw(a.im)


def stroke_ellipse(a,box,c,width=1):
    a.d.ellipse(box, outline=P[c], width=width)


def cloud(a,x,y,w=40):
    a.e((x,y+4,x+w,y+13),'blue3')
    a.e((x+3,y+1,x+w-8,y+11),'watergleam')
    a.e((x+12,y-3,x+w-16,y+9),'bg_temple_stone5')
    a.r((x+7,y+5,x+w-6,y+9),'bg_temple_stone5')
    a.l([(x+9,y+11),(x+w-8,y+11)],'water4')


def sky_void(a,seed):
    a.r((0,0,239,159),'blue3')
    a.r((0,0,239,40),'water4')
    for x,y,w in [(-18,20,70),(178,18,73),(-24,76,47),(221,63,56),(-11,139,61),(174,149,87)]:
        cloud(a,x,y+(seed%3),w)
    # Glimpses of lower ridges read as airy distance outside the playable terrace.
    a.p([(0,121),(6,116),(17,122),(25,142),(0,150)],'bg_twilight_stone2')
    a.p([(224,126),(233,113),(240,117),(240,154),(219,153)],'bg_twilight_stone3')


def warm_void(a,seed):
    a.r((0,0,239,159),'bg_twilight_dusk2')
    a.r((0,0,239,25),'bg_twilight_dusk4')
    for side in (0,232):
        a.r((side,25,side+7,159),'purple1')
        for y in range(30,160,22):
            a.p([(side,y+2),(side+5,y),(side+7,y+13),(side+2,y+17)],'bg_twilight_stone1')
            a.l([(side+1,y+2),(side+4,y+1),(side+6,y+10)],'dusk3')
    a.r((0,153,239,159),'purple1')
    a.l([(8,154),(99,154)],'dusk2');a.l([(141,154),(231,154)],'dusk2')


def floor(a,room,sky=True):
    rid=room['id']; R=random.Random(0xC41A+rid)
    if sky: sky_void(a,rid)
    else: warm_void(a,rid)
    # Boundaries: bevel faces remain OUTSIDE the [8,28,224,124] playable plane.
    rect(a,[8,28,224,124],'bg_temple_stone3' if sky else 'bg_sunlit_dirt2')
    a.r((8,45,10,151),'bg_temple_stone1' if sky else 'wood1')
    a.r((229,45,231,151),'bg_temple_stone1' if sky else 'wood1')
    a.r((11,45,228,148),'bg_temple_stone4' if sky else 'bg_sunlit_dirt3')
    a.r((11,149,103,151),'bg_temple_stone2' if sky else 'wood2')
    a.r((136,149,228,151),'bg_temple_stone2' if sky else 'wood2')
    a.l([(12,46),(102,46)],'bg_temple_stone5' if sky else 'gold3')
    a.l([(137,46),(227,46)],'bg_temple_stone5' if sky else 'gold3')
    # Sparse rectangular tesserae, deliberately quiet where actors will stand.
    grout='bg_temple_stone3' if sky else 'bg_sunlit_dirt2'
    hi='bg_temple_stone5' if sky else 'bg_sunlit_dirt4'
    for y in range(50,146,16):
        offset=0 if (y//16)%2 else 12
        for x in range(15+offset,228,24):
            if R.random()<.67:
                a.l([(x,y),(min(226,x+15),y)],grout)
                a.l([(x+1,y+1),(min(226,x+14),y+1)],hi)
    for _ in range(32):
        x=R.randrange(15,225);y=R.randrange(48,146)
        a.r((x,y,x+R.randrange(1,4),y),hi)
    # Continuous north/south exit thresholds have no baked doors.
    for y in (28,32,36,40,144,148):
        a.r((105,y,134,y+2),'bg_temple_stone2' if sky else 'bg_sunlit_wood3')
        a.r((106,y,133,y),'bg_temple_stone5' if sky else 'bg_sunlit_dirt4')


def parapet(a,r,sky=True,detail=0):
    x,y,w,h=r
    c0='bg_temple_stone1' if sky else 'purple1'
    c1='blue2' if sky else 'wood2'
    c2='bg_temple_stone3' if sky else 'dusk3'
    c3='bg_temple_stone5' if sky else 'bg_sunlit_plaster'
    rect(a,r,c0)
    a.r((x+1,y+1,x+w-2,y+h-5),c1)
    a.r((x+1,y+1,x+w-2,y+6),c2)
    a.r((x+2,y+1,x+w-3,y+2),c3)
    a.r((x+1,y+h-4,x+w-2,y+h-3),c2)
    for xx in range(x+12,x+w-3,16):
        a.l([(xx,y+7),(xx,y+h-6)],c0)
        a.dot(xx+1,y+7,c3)
    for xx in range(x+8,x+w-6,24):
        a.p([(xx-2,y+5),(xx+3,y+5),(xx+3,y+10),(xx,y+13),(xx-2,y+10)],'wood2' if sky else 'purple2')
        a.p([(xx-1,y+5),(xx+2,y+5),(xx+2,y+9),(xx,y+11),(xx-1,y+9)],'gold2' if sky else 'gold1')
        a.dot(xx,y+6,'gold4')


def pillar(a,r,sky=True,kind=0):
    x,y,w,h=r
    edge='bg_temple_stone1' if sky else 'purple1'
    shade='blue2' if sky else 'wood1'
    face='bg_temple_stone3' if sky else 'wood3'
    lit='bg_temple_stone5' if sky else 'gold3'
    rect(a,r,edge)
    a.r((x+1,y+1,x+w-2,y+h-3),shade)
    a.r((x+3,y+2,x+w-5,y+h-5),face)
    a.r((x+4,y+2,x+w-6,y+4),lit)
    a.r((x+1,y+h-5,x+w-2,y+h-3),face)
    a.l([(x+2,y+h-5),(x+w-3,y+h-5)],lit)
    for yy in range(y+8,y+h-8,12):
        a.l([(x+4,yy),(x+w-6,yy)],edge)
        a.dot(x+5,yy+1,lit)
    if w>=28:
        cx=x+w//2;cy=y+h//2
        a.p([(cx,cy-5),(cx+5,cy),(cx,cy+5),(cx-5,cy)],shade)
        a.l([(cx-4,cy),(cx,cy-4),(cx+4,cy)],'gold2')
        a.dot(cx,cy,'gold4')


def cliff_rock(a,r,sky=True):
    x,y,w,h=r
    # Full footprint carries color; faceted silhouette remains within the solid.
    rect(a,r,'bg_sunlit_stone1' if sky else 'purple1')
    a.p([(x,y+5),(x+5,y),(x+w-7,y),(x+w-1,y+7),(x+w-1,y+h-4),(x+w-7,y+h-1),(x+4,y+h-1),(x,y+h-5)],'bg_sunlit_stone2' if sky else 'wood2')
    a.p([(x+2,y+4),(x+6,y+1),(x+w-7,y+1),(x+w-3,y+6),(x+w-8,y+h-8),(x+7,y+h-7)],'bg_sunlit_stone4' if sky else 'wood4')
    a.p([(x+3,y+4),(x+7,y+2),(x+w-8,y+2),(x+w-6,y+4),(x+w-12,y+7),(x+7,y+7)],'bg_sunlit_stone5' if sky else 'gold3')
    a.l([(x+7,y+8),(x+10,y+11),(x+8,y+h-5)],'bg_sunlit_stone2' if sky else 'wood1')
    if sky:
        a.r((x+2,y+1,x+7,y+2),'bg_sunlit_pine3');a.dot(x+6,y,'bg_sunlit_leafwarm')


def gap(a,r,sky=True):
    x,y,w,h=r
    rect(a,r,'blue1' if sky else 'purple0')
    a.r((x,y,x+w-1,y+3),'blue2' if sky else 'wood1')
    a.r((x,y+4,x+w-1,y+h-3),'blue3' if sky else 'purple1')
    a.r((x,y+h-2,x+w-1,y+h-1),'water4' if sky else 'purple2')
    # Quiet flowing clouds/water below. No bridge is baked into this closed state.
    for xx in range(x+7,x+w-5,21):
        a.l([(xx,y+7),(min(x+w-2,xx+11),y+7)],'watergleam' if sky else 'water1')
        a.l([(xx+3,y+8),(min(x+w-2,xx+13),y+8)],'water4' if sky else 'water2')


def ring_floor(a,cx,cy,rx,ry,sky=True,spokes=8):
    dark='bg_temple_stone3' if sky else 'bg_sunlit_dirt2'
    light='bg_temple_stone5' if sky else 'bg_sunlit_dirt4'
    stroke_ellipse(a,(cx-rx,cy-ry,cx+rx,cy+ry),dark,2)
    stroke_ellipse(a,(cx-rx+4,cy-ry+3,cx+rx-4,cy+ry-3),light)
    stroke_ellipse(a,(cx-rx+7,cy-ry+5,cx+rx-7,cy+ry-5),dark)
    for i in range(spokes):
        angle=math.pi*2*i/spokes
        p=(int(cx+rx*math.cos(angle)),int(cy+ry*math.sin(angle)))
        q=(int(cx+(rx-6)*math.cos(angle)),int(cy+(ry-4)*math.sin(angle)))
        a.l([p,q],light)


def breeze_scroll(a,x,y,flip=False):
    points=[(0,2),(9,2),(12,0),(12,-3),(9,-5),(6,-4),(5,-1)]
    a.l([(x+(-dx if flip else dx),y+dy) for dx,dy in points],'bg_temple_stone3')
    a.l([(x,y+5),(x+(-17 if flip else 17),y+5)],'bg_temple_stone5')


def pad(a,x,y,sky):
    # Flat 16px interaction discs; dynamic sprite sits above this low contrast rim.
    color='bg_temple_stone3' if sky else 'bg_sunlit_dirt2'
    light='bg_temple_stone5' if sky else 'bg_sunlit_dirt4'
    stroke_ellipse(a,(x-10,y-6,x+10,y+6),color)
    a.l([(x-6,y+5),(x+6,y+5)],light)


def background(room):
    rid=room['id']; sky=rid<9
    a=Art(); floor(a,room,sky)
    if rid==4:
        # A sunlit grass-and-stone ridge with a winding chalk path.
        a.r((11,45,228,148),'bg_sunlit_grass2')
        path=[(103,44),(137,44),(135,65),(117,84),(115,103),(135,128),(135,151),(104,151),(104,134),(86,111),(87,83),(106,63)]
        a.p(path,'bg_sunlit_dirt1')
        a.p([(108,44),(132,44),(130,64),(111,83),(110,105),(131,130),(130,151),(109,151),(109,133),(93,109),(93,85),(111,63)],'bg_sunlit_dirt3')
        R=random.Random(404)
        for _ in range(56):
            x=R.randrange(15,225);y=R.randrange(47,147)
            if a.im.getpixel((x,y))==P['bg_sunlit_grass2']:
                a.l([(x-2,y),(x-1,y-2),(x,y),(x+2,y-1)],'bg_sunlit_grass4')
                if _%9==0:a.dot(x,y-3,'flower1');a.dot(x+1,y-2,'gold2')
        for x,y in [(30,82),(194,137),(158,52),(27,141)]:
            a.p([(x-5,y),(x-3,y-3),(x+7,y-3),(x+9,y),(x+5,y+3),(x-3,y+3)],'bg_sunlit_grass3')
        for r in room['static_solids'][2:]:
            if r not in room.get('trial_entrance_solids',[]):cliff_rock(a,r,True)
    elif rid==5:
        for x,y in [(36,61),(196,122)]:breeze_scroll(a,x,y,x>120)
        # Saffron sail strips are painted on the deck, not raised obstacles.
        for x in (24,208):
            a.r((x,48,x+5,84),'bg_sunlit_dirt2');a.r((x+1,48,x+4,83),'bg_sunlit_dirt3')
            a.p([(x+1,78),(x+4,78),(x+3,84)],'bg_sunlit_wood3')
        for r in room['static_solids'][2:]:gap(a,r,True)
        gap(a,room['dynamic_solids'][0]['rect'],True)
        for x in (96,140):
            a.r((x,84,x+3,87),'wood2');a.r((x,104,x+3,107),'wood3')
            a.l([(x,84),(x+3,84)],'gold3')
    elif rid==6:
        ring_floor(a,120,92,72,43,True,12)
        for x in (40,200):
            a.p([(x-6,100),(x,91),(x+6,100),(x,97)],'bg_temple_stone3')
        for r in room['static_solids'][2:]:pillar(a,r,True)
    elif rid==7:
        # Inlaid relay conduits are inactive decorative gold. On-state is engine-owned.
        for pts in [[(56,112),(56,56)],[(184,112),(184,56)],[(120,112),(56,112)],[(120,112),(184,112)]]:
            a.l(pts,'bg_temple_stone3',3);a.l(pts,'bg_temple_gold1')
        ring_floor(a,120,110,36,19,True,6)
        for r in room['static_solids'][2:]:pillar(a,r,True)
        for x in (29,204):breeze_scroll(a,x,78,x>120)
    elif rid==8:
        ring_floor(a,120,95,89,48,True,16)
        ring_floor(a,120,95,53,29,True,8)
        a.p([(120,57),(131,83),(170,95),(131,105),(120,134),(109,105),(70,95),(109,84)],'bg_temple_stone3')
        a.p([(120,62),(127,87),(159,95),(127,101),(120,129),(113,101),(81,95),(113,88)],'bg_temple_stone4')
        for x,y,f in [(34,59,False),(205,59,True),(34,129,False),(205,129,True)]:breeze_scroll(a,x,y,f)
    elif rid==9:
        a.r((11,45,228,148),'bg_sunlit_dirt2')
        a.p([(102,44),(138,44),(146,68),(131,85),(131,109),(148,134),(139,151),(102,151),(110,131),(102,109),(106,82),(123,66)],'bg_sunlit_dirt3')
        for x,y in [(31,66),(192,56),(39,139),(211,120),(167,139)]:
            a.l([(x-4,y),(x-2,y-4),(x,y),(x+3,y-3)],'bg_sunlit_moss1')
            a.dot(x+1,y-3,'bg_sunlit_moss3')
        for r in room['static_solids'][2:]:
            if r not in room.get('trial_entrance_solids',[]):parapet(a,r,False)
    elif rid==10:
        ring_floor(a,56,80,27,20,False,8);ring_floor(a,184,80,27,20,False,8)
        for x in (56,184):
            a.l([(x,47),(x,72)],'wood4',2);a.l([(x,88),(x,139)],'wood4',2)
            a.l([(x-1,48),(x-1,71)],'bg_sunlit_dirt4')
        for r in room['static_solids'][2:]:pillar(a,r,False)
        # Central counterweight shaft, entire tower remains within its collider.
        a.r((113,68,126,104),'purple1');a.r((116,70,122,103),'wood1')
        for y in range(70,103,5):a.l([(119,y),(119,y+2)],'gold2')
        a.p([(111,104),(128,104),(125,112),(114,112)],'wood3')
        a.l([(112,104),(127,104)],'gold3')
    elif rid==11:
        # Both banks and the center unbridged gap are visibly closed.
        for r in room['static_solids'][2:4]:gap(a,r,False)
        gap(a,room['dynamic_solids'][1]['rect'],False)
        for r in room['static_solids'][4:]:parapet(a,r,False)
        # Dormant root channels point from the well toward the bridge.
        for pts in [[(52,117),(72,117),(80,112),(97,112),(108,105)],[(168,116),(185,120),(209,117)],[(34,74),(61,77),(88,74)]]:
            a.l(pts,'bg_sunlit_dirt2',3);a.l(pts,'wood4')
        a.l([(157,75),(178,72),(213,74)],'bg_sunlit_moss1')
        a.dot(182,72,'bg_sunlit_moss3')
    elif rid==12:
        # Four flat flame/leaf/swirl/stone channels converge on the lantern plinth.
        for x,y in [(56,64),(184,64),(56,112),(184,112)]:
            a.l([(x,y),(x,84),(120,84)],'bg_sunlit_dirt2',3)
            a.l([(x,y),(x,84),(120,84)],'gold2')
            ring_floor(a,x,y,22,13,False,8)
        for r in room['static_solids'][2:]:pillar(a,r,False)
        a.p([(120,76),(124,81),(122,87),(117,89),(115,84)],'wood1')
        a.p([(120,77),(122,82),(120,86),(118,86)],'gold3')
    elif rid==13:
        ring_floor(a,120,94,90,48,False,16)
        ring_floor(a,120,94,61,34,False,12)
        # A warm segmented solar mosaic leaves a quiet center for the boss.
        for i in range(12):
            t=i*math.pi/6
            pts=[]
            for rx,ry,dt in [(51,28,-.05),(57,31,0),(51,28,.05),(42,23,0)]:
                pts.append((int(120+rx*math.cos(t+dt)),int(94+ry*math.sin(t+dt))))
            a.p(pts,'bg_sunlit_wood3')
        a.p([(120,77),(135,85),(135,103),(120,112),(105,103),(105,85)],'bg_sunlit_dirt2')
        a.p([(120,80),(132,87),(132,101),(120,109),(108,101),(108,87)],'bg_sunlit_dirt3')
    roads.draw(a,rid,P)
    # Real side destinations belong to the surrounding architecture.
    if rid==4:
        # A little walled wind courtyard shares the ridge's north parapet.
        a.r((186,44,231,68),'bg_temple_stone4')
        for yy in (49,58,66):a.l([(189,yy),(228,yy)],'bg_temple_stone3')
        for box in room['trial_entrance_solids']:parapet(a,box,True)
        a.r((196,57,214,70),'bg_temple_stone1');a.r((199,59,211,69),'shadow')
        a.l([(197,70),(213,70)],'bg_temple_stone5',2)
        a.l([(204,72),(204,89)],'bg_sunlit_dirt3',18)
        for x in (181,229):
            a.l([(x,38),(x,49)],'wood2',2);a.p([(x+1,38),(x+9,40),(x+1,44)],'gold3')
    elif rid==9:
        # Amber workshop is recessed into the existing eastern rock arcade.
        a.p([(184,112),(184,91),(191,84),(225,84),(232,92),(232,112)],'bg_sunlit_stone1')
        a.p([(188,110),(188,94),(194,87),(222,87),(228,94),(228,110)],'bg_sunlit_stone3')
        a.p([(196,113),(196,97),(201,92),(215,92),(220,97),(220,113)],'wood0')
        a.r((199,99,217,113),'deep');a.l([(198,96),(200,94),(216,94),(218,97)],'bg_sunlit_wood4',2)
        a.r((194,114,222,116),'bg_sunlit_stone4')
        a.l([(195,114),(221,114)],'bg_sunlit_stone5')
        a.r((201,85,214,89),'wood1');a.l([(204,87),(212,87)],'gold3')
    # Old village return was on the south edge. Close that false opening.
    if rid in (4,9):
        parapet(a,[105,149,30,11],sky)
    # North parapet and all footprints come directly from the design JSON.
    for r in room['static_solids'][:2]:parapet(a,r,sky)
    # Add a distant architectural skyline above the blocking parapet.
    for x in ((25,72,159,206) if sky else (22,63,176,217)):
        a.r((x-2,19,x+2,27),'bg_temple_stone2' if sky else 'wood2')
        a.r((x-3,18,x+3,20),'bg_temple_stone5' if sky else 'gold3')
        if sky:
            a.l([(x,8),(x,17)],'wood3')
            a.p([(x+1,8),(x+13,10),(x+8,14),(x+1,13)],'gold2')
            a.l([(x+2,9),(x+10,10)],'gold4')
        else:
            a.p([(x-4,17),(x,12),(x+4,17)],'bg_sunlit_plaster')
    # Interactive objects get only flat floor discs; no actors, signs, lamps, or UI.
    seen=set()
    for ob in room['objects']:
        x,y=ob['at']
        if (x,y) in seen or y<46:continue
        seen.add((x,y))
        # Objects on solid/dynamic obstacles retain their obstacle geometry.
        if any(rx<=x<rx+w and ry<=y<ry+h for rx,ry,w,h in room['static_solids']):continue
        if ob['kind'] in ('cracked_stone','burnable'):continue
        pad(a,x,y,sky)
    return a


def fuuri(direction,frame):
    a=Art(16,16,'transparent'); bob=(0,-1,0,1)[frame]
    # Cream moth-spirit with lavender feather wings, small face, split ribbon tail.
    def p(pts,c):a.p([(x,y+bob) for x,y in pts],c)
    def l(pts,c):a.l([(x,y+bob) for x,y in pts],c)
    def dot(x,y,c):a.dot(x,y+bob,c)
    if direction in ('down','up'):
        wing=(0,1,2,1)[frame]
        p([(6,6),(3,2+wing),(1,3+wing),(0,7),(2,10),(5,10),(6,8)],'purple1')
        p([(6,6),(3,3+wing),(1,4+wing),(1,7),(3,9),(5,8)],'white')
        p([(1,7),(3,5+wing),(5,7),(4,9)],'purple3')
        p([(9,6),(12,2+wing),(14,3+wing),(15,7),(13,10),(10,10),(9,8)],'purple1')
        p([(9,6),(12,3+wing),(14,4+wing),(14,7),(12,9),(10,8)],'white')
        p([(14,7),(12,5+wing),(10,7),(11,9)],'purple3')
        p([(6,10),(5+frame%2,14),(7,12),(8,10),(10,13),(10-frame%2,15),(8,12)],'wood4')
        l([(6,11),(6,13)],'white');l([(9,11),(10,13)],'white')
        p([(7,3),(9,4),(10,6),(10,10),(8,12),(5,10),(5,6),(6,4)],'purple1')
        p([(7,4),(9,5),(9,10),(7,11),(6,9),(6,5)],'flower1')
        p([(6,3),(4,1),(5,0),(7,3)],'white');p([(9,3),(11,1),(10,0),(8,3)],'white')
        if direction=='down':
            dot(6,7,'ink');dot(9,7,'ink');dot(7,9,'gold2')
            dot(6,6,'white');dot(9,6,'white')
        else:
            l([(7,5),(7,9),(8,10)],'purple3');dot(8,6,'white')
    else:
        # Author right-facing view, mirror for left.
        shift=(0,1,2,1)[frame]
        p([(6,7),(4,2+shift),(1,3+shift),(2,7),(5,10)],'purple1')
        p([(5,7),(3,3+shift),(2,4+shift),(3,7),(5,9)],'white')
        p([(7,8),(5,4+shift),(3,6+shift),(5,11),(7,10)],'purple3')
        p([(5,10),(2,12),(0,11),(1,14),(4,13),(7,11)],'wood4')
        l([(1,12),(3,12),(6,10)],'white')
        p([(8,4),(11,4),(13,6),(13,10),(10,12),(7,11),(6,7)],'purple1')
        p([(9,5),(11,5),(12,7),(12,10),(10,11),(8,10),(7,7)],'flower1')
        p([(10,4),(9,1),(10,0),(12,4)],'white')
        dot(12,7,'ink');dot(11,6,'white');dot(13,9,'gold2')
        if direction=='left':a.im=a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);a.d=ImageDraw.Draw(a.im)
    return a


def kohaku(direction,frame):
    a=Art(16,16,'transparent'); bob=-1 if frame==2 else 0
    def p(pts,c):a.p([(x,y+bob) for x,y in pts],c)
    def l(pts,c):a.l([(x,y+bob) for x,y in pts],c)
    def dot(x,y,c):a.dot(x,y+bob,c)
    # Three segmented amber shell plates and two tiny moss sprouts, not a turtle.
    if direction in ('down','up'):
        p([(4,11),(3-(frame==1),14),(6,14),(7,12)],'wood0')
        p([(10,11),(9,14),(12+(frame==3),14),(12,11)],'wood0')
        p([(3,6),(5,3),(10,3),(13,6),(14,10),(11,13),(5,13),(1,10)],'wood1')
        p([(4,5),(6,3),(10,4),(12,6),(13,10),(10,12),(5,12),(2,9)],'gold1')
        p([(4,5),(7,4),(10,4),(12,7),(10,9),(5,9),(3,7)],'gold3')
        l([(6,4),(5,7),(6,11)],'wood3');l([(9,4),(10,7),(9,11)],'wood3')
        l([(3,8),(5,9),(10,9),(12,8)],'gold0')
        p([(4,4),(3,1),(5,2),(6,4)],'pine2');dot(3,1,'pine5')
        p([(9,4),(11,1),(12,2),(11,5)],'pine2');dot(11,1,'pine5')
        if direction=='down':
            p([(5,8),(10,8),(11,10),(9,13),(6,13),(4,11)],'wood1')
            p([(5,9),(9,9),(10,10),(8,12),(6,12)],'wood4')
            dot(5,10,'ink');dot(9,10,'ink');dot(7,12,'gold4')
        else:
            p([(6,12),(7,15),(9,14),(9,12)],'wood2');dot(8,14,'gold2')
            l([(4,7),(7,5),(10,7)],'gold4')
    else:
        step=(0,1,0,-1)[frame]
        p([(4,10),(3+step,14),(6+step,14),(7,11)],'wood0')
        p([(10,10),(9-step,14),(12-step,14),(12,11)],'wood0')
        p([(2,9),(0,11),(0,12),(4,11)],'wood2')
        p([(3,4),(7,2),(11,4),(13,8),(12,12),(5,13),(1,10),(1,7)],'wood1')
        p([(4,4),(7,3),(10,5),(11,8),(10,11),(5,12),(2,9),(2,7)],'gold2')
        p([(4,4),(7,3),(10,5),(9,7),(4,7),(2,8)],'gold3')
        l([(5,4),(4,7),(5,11)],'wood3');l([(8,4),(7,7),(8,11)],'wood3')
        p([(10,7),(13,7),(15,9),(14,12),(10,12),(8,10)],'wood1')
        p([(11,8),(13,8),(14,10),(13,11),(10,11),(9,10)],'wood4')
        dot(13,9,'ink');dot(14,11,'gold4')
        p([(10,7),(10,4),(12,5),(12,8)],'pine2');dot(10,4,'pine5')
        if direction=='left':a.im=a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);a.d=ImageDraw.Draw(a.im)
    return a


def kazane():
    a=Art(32,32,'transparent')
    # Wide diamond/kite silhouette, four feathered sails, long braided tassels.
    for flip in (False,True):
        def pp(pts,c):a.p([(31-x if flip else x,y) for x,y in pts],c)
        pp([(14,10),(8,4),(2,2),(4,8),(0,11),(3,15),(0,19),(7,21),(13,17)],'purple0')
        pp([(13,10),(8,5),(4,4),(6,9),(2,11),(5,14),(2,18),(7,19),(12,16)],'white')
        pp([(12,11),(7,8),(6,10),(4,11),(7,14),(4,17),(8,17),(12,15)],'purple3')
        pp([(12,16),(7,22),(4,27),(8,26),(11,21),(14,19)],'purple1')
        pp([(12,17),(8,22),(7,25),(10,23),(14,18)],'gold2')
    a.p([(14,5),(12,1),(15,3),(16,0),(18,4),(20,2),(19,8),(21,12),(20,20),(17,24),(12,22),(11,16),(12,9)],'purple0')
    a.p([(14,6),(16,3),(18,6),(18,9),(20,12),(19,19),(16,22),(13,19),(12,15),(13,10)],'purple2')
    a.p([(14,8),(18,8),(19,11),(18,15),(14,15),(12,11)],'white')
    a.p([(12,10),(15,11),(15,13),(13,12)],'blue0');a.p([(17,11),(20,10),(19,12),(17,13)],'blue0')
    a.dot(14,11,'gold4');a.dot(18,11,'gold4')
    a.p([(16,13),(18,16),(16,19),(14,16)],'gold0');a.p([(16,14),(17,16),(16,18),(15,16)],'gold4')
    a.l([(14,22),(13,27),(10,30),(14,29),(16,25)],'white',2)
    a.l([(18,21),(20,26),(18,30),(21,29),(22,25)],'gold2',2)
    a.dot(16,5,'gold4')
    return a


def core_keeper():
    a=Art(32,32,'transparent')
    # Hexagonal lantern beetle with short masonry legs and a cold central ember.
    for pts in [[(5,18),(1,23),(1,28),(5,28),(8,24)],[(25,18),(30,23),(30,28),(26,28),(23,24)],[(10,23),(8,29),(12,30),(14,25)],[(20,23),(22,29),(18,30),(16,25)]]:
        a.p(pts,'purple0')
    a.l([(3,23),(3,26),(5,26)],'wood3',2);a.l([(28,23),(28,26),(26,26)],'wood3',2)
    a.l([(10,26),(10,28),(12,28)],'gold2');a.l([(20,26),(20,28),(18,28)],'gold2')
    a.p([(10,3),(21,3),(28,10),(28,20),(22,26),(9,26),(3,20),(3,10)],'purple0')
    a.p([(10,4),(21,4),(27,10),(27,20),(21,25),(9,25),(4,20),(4,10)],'wood2')
    a.p([(10,5),(21,5),(26,10),(23,13),(8,13),(5,10)],'wood4')
    a.l([(11,5),(20,5),(24,9)],'gold4',2)
    a.p([(8,11),(12,8),(20,8),(24,12),(24,20),(20,23),(11,23),(7,19)],'purple1')
    a.p([(12,10),(19,10),(22,13),(22,19),(19,21),(12,21),(9,18),(9,13)],'purple0')
    # Heavy asymmetric seams keep the shell chunky, avoid a generic robot face.
    a.l([(8,8),(7,11),(4,13)],'wood1');a.l([(24,7),(24,11),(27,14)],'wood1')
    a.l([(4,18),(8,18),(10,23)],'wood1');a.l([(26,18),(23,18),(21,24)],'wood1')
    a.p([(14,13),(18,12),(20,15),(19,19),(15,20),(12,17)],'blue2')
    a.p([(16,13),(18,15),(17,18),(14,17)],'water4');a.dot(17,14,'white')
    a.r((11,10,13,11),'gold3');a.r((19,10,21,11),'gold3')
    a.r((13,1,18,3),'purple0');a.r((14,1,17,3),'gold1');a.r((14,1,17,1),'gold4')
    a.r((12,26,19,27),'wood1');a.r((13,26,18,26),'gold3')
    return a


def element(a,kind,on):
    c={'FIRE_SOCKET':'fire2','NATURE_SOCKET':'pine4','WIND_SOCKET':'purple3','STONE_SOCKET':'gold2'}[kind]
    if not on:c={'FIRE_SOCKET':'fire0','NATURE_SOCKET':'pine1','WIND_SOCKET':'purple1','STONE_SOCKET':'gold0'}[kind]
    if kind=='FIRE_SOCKET':
        a.p([(8,3),(9,6),(11,5),(11,9),(9,11),(6,11),(4,9),(6,6),(6,8)],c)
        if on:a.p([(8,7),(9,9),(8,10),(7,9)],'gold4')
    elif kind=='NATURE_SOCKET':
        a.p([(10,3),(11,6),(9,10),(5,11),(4,8),(6,5)],c);a.l([(5,11),(9,6)],'pine5' if on else 'moss1')
    elif kind=='WIND_SOCKET':
        a.l([(4,7),(10,7),(11,6),(11,4),(9,3),(7,4)],c,2);a.l([(4,10),(9,10),(10,9)],c)
    else:
        a.p([(7,3),(11,6),(10,10),(6,11),(3,8),(4,5)],c);a.l([(7,4),(6,7),(8,8),(7,10)],'gold4' if on else 'wood1')


def prop(name,on):
    a=Art(16,16,'transparent')
    if name in ('FIRE_SOCKET','NATURE_SOCKET','WIND_SOCKET','STONE_SOCKET'):
        a.p([(3,2),(12,2),(14,5),(14,11),(11,14),(4,14),(1,11),(1,5)],'purple0')
        a.p([(4,3),(11,3),(13,5),(13,11),(10,13),(5,13),(2,10),(2,5)],'stone2')
        a.r((4,4,11,11),'stone0');a.l([(4,2),(11,2),(13,4)],'gold3' if on else 'stone5')
        element(a,name,on)
        a.dot(7,13,'gold4' if on else 'stone1');return a
    if name=='VANE':
        a.e((3,11,12,14),'stone0');a.l([(5,12),(10,12)],'stone4')
        a.r((7,5,8,12),'wood2');a.r((7,5,7,11),'wood4')
        a.p([(7,5),(4,1),(1,2),(4,5)],'purple1');a.p([(7,5),(10,1),(14,2),(11,5)],'purple1')
        a.p([(7,5),(3,7),(4,10),(7,7)],'purple1');a.p([(8,5),(12,7),(12,10),(8,7)],'purple1')
        c='white' if on else 'purple3';a.p([(7,4),(4,2),(2,2),(5,4)],c);a.p([(9,4),(11,2),(13,2),(11,4)],c)
        a.p([(6,6),(4,8),(5,9),(7,6)],'gold3' if on else 'wood4');a.p([(9,6),(11,8),(11,9),(8,6)],'gold3' if on else 'wood4')
        a.r((7,4,8,6),'gold4' if on else 'gold1')
    elif name=='WEIGHT':
        a.e((1,10,14,15),'purple0');a.e((3,10,12,13),'stone2');a.l([(4,12),(11,12)],'stone5')
        if on:
            a.p([(5,4),(10,4),(13,11),(11,13),(4,13),(2,11)],'wood1');a.p([(6,5),(9,5),(11,11),(4,11)],'gold2')
            a.r((6,1,9,5),'wood1');a.r((7,2,8,3),'gold3');a.l([(6,6),(9,6)],'gold4')
            a.l([(6,8),(8,7),(10,9)],'gold0')
        else:a.p([(7,6),(11,10),(7,13),(3,10)],'stone0');a.p([(7,7),(9,10),(7,11),(5,10)],'gold0')
    elif name=='WELL':
        a.e((1,3,14,14),'stone0');a.e((1,2,14,11),'stone3');a.e((3,3,12,9),'water0' if on else 'purple0')
        a.l([(2,10),(3,12),(12,12),(13,10)],'stone2');a.l([(3,3),(5,2),(10,2),(12,3)],'stone5')
        if on:
            a.l([(4,6),(10,6)],'water3');a.l([(4,11),(2,14),(1,13)],'pine3');a.l([(12,10),(14,14)],'pine3')
        else:a.l([(4,7),(10,7)],'purple1')
    elif name in ('BRAZIER','LAMP','REST'):
        a.r((6,10,9,14),'wood1');a.r((4,14,11,15),'stone1');a.l([(5,14),(10,14)],'stone4')
        a.p([(3,8),(12,8),(11,11),(4,11)],'gold0');a.l([(3,8),(12,8)],'gold2')
        if on or name=='REST':
            a.p([(8,0),(9,4),(12,3),(12,6),(10,9),(5,9),(3,6),(6,2),(6,5)],'fire1')
            a.p([(8,2),(9,5),(10,4),(10,7),(8,9),(5,7),(7,4)],'gold2')
            a.p([(8,5),(9,7),(7,8),(6,7)],'gold4')
        else:
            a.p([(7,5),(9,5),(10,7),(5,7)],'wood0');a.dot(8,6,'fire0')
        if name=='REST':a.dot(1,5,'gold4');a.dot(14,4,'gold3')
        if name=='LAMP':a.r((2,1,3,7),'wood3');a.r((12,1,13,7),'wood1');a.l([(3,1),(12,1)],'gold2')
    elif name=='SIGN':
        a.r((7,9,8,15),'wood1');a.r((2,2,13,10),'wood0');a.r((2,2,12,8),'wood3');a.l([(3,2),(11,2)],'wood5')
        a.l([(4,4),(9,4)],'wood1');a.l([(4,6),(10,6)],'wood1');a.dot(11,4,'gold2')
        if on:a.dot(13,1,'gold4')
    elif name=='CHIME':
        a.l([(3,14),(5,9),(8,6),(8,1)],'pine1');a.l([(8,4),(12,4),(13,6)],'pine3')
        a.p([(10,6),(14,6),(15,10),(9,10)],'gold1');a.l([(10,6),(13,6)],'gold4');a.dot(12,12,'gold2')
        a.p([(4,7),(1,4),(2,2),(5,3),(6,6)],'flower0' if on else 'purple3');a.dot(3,3,'flower1')
        if on:a.dot(14,2,'gold4');a.dot(6,1,'white')
    return a


def emit_array(f,name,data):
    f.write(f'const unsigned char {name}[{len(data)}] = {{\n')
    for i in range(0,len(data),32):f.write('  '+','.join(map(str,data[i:i+32]))+',\n')
    f.write('};\n\n')


def emit_tensor(f,name,tensor,dims):
    f.write('const unsigned char '+name+''.join(f'[{n}]' for n in dims)+' = {\n')
    def rec(items,depth):
        for value in items:
            f.write('  '*depth+'{\n')
            if isinstance(value,Art):
                data=value.im.tobytes()
                for i in range(0,len(data),32):f.write('  '*(depth+1)+','.join(map(str,data[i:i+32]))+',\n')
            else:rec(value,depth+1)
            f.write('  '*depth+'},\n')
    rec(tensor,1);f.write('};\n\n')


def split_source(content):
    folder=SRC/'campaign_art_data';folder.mkdir(exist_ok=True)
    chunks=[];lines=[];size=0
    for line in content.splitlines(keepends=True):
        n=len(line.encode())
        if size+n>32768:chunks.append(''.join(lines));lines=[];size=0
        lines.append(line);size+=n
    if lines:chunks.append(''.join(lines))
    for old in folder.glob('part_*.inc'):old.unlink()
    for i,c in enumerate(chunks):(folder/f'part_{i:03d}.inc').write_text(c)
    (SRC/'campaign_art.c').write_text('#include "campaign_art.h"\n/* Generated by assets/generate_campaign.py. */\n'+''.join(f'#include "campaign_art_data/part_{i:03d}.inc"\n' for i in range(len(chunks))))
    return len(chunks)


def paste_sprite(dst,spr,pos):
    dst.paste(spr.im.convert('RGB'),pos,Image.frombytes('L',spr.im.size,bytes(255 if p else 0 for p in spr.im.tobytes())))


def previews(rooms,bgs,companions,bosses,props,base):
    # Native art previews, not emulator captures. Labels are outside game artwork.
    sheet=Image.new('RGB',(240*5,176*2),(27,34,48));draw=ImageDraw.Draw(sheet)
    geometry=Image.new('RGB',(240*5,176*2),(27,34,48))
    for i,(r,bg) in enumerate(zip(rooms,bgs)):
        x=(i%5)*240;y=(i//5)*176
        sheet.paste(bg.im.convert('RGB'),(x,y));draw.text((x+5,y+162),f"{r['id']:02d}  {r['key']}",fill=(243,232,201))
        qa=bg.im.convert('RGB');d=ImageDraw.Draw(qa)
        for rx,ry,w,h in r['static_solids']:d.rectangle((rx,ry,rx+w-1,ry+h-1),outline=(255,60,140))
        for ds in r['dynamic_solids']:
            rx,ry,w,h=ds['rect'];d.rectangle((rx,ry,rx+w-1,ry+h-1),outline=(255,125,24))
        for ob in r['objects']:
            ox,oy=ob['at'];d.ellipse((ox-2,oy-2,ox+2,oy+2),outline=(15,250,80))
        for sp in r['spawn'].values():d.ellipse((sp[0]-4,sp[1]-4,sp[0]+4,sp[1]+4),outline=(32,255,255))
        geometry.paste(qa,(x,y))
    sheet.save(OUT/'campaign_contact_sheet.png');sheet.resize((2400,704),Image.Resampling.NEAREST).save(OUT/'campaign_contact_sheet_2x.png')
    geometry.resize((2400,704),Image.Resampling.NEAREST).save(OUT/'campaign_geometry_proof_2x.png')
    for r,bg in zip(rooms,bgs):
        bg.im.save(OUT/f"campaign_{r['key']}.png")
        bg.im.resize((960,640),Image.Resampling.NEAREST).save(OUT/f"campaign_{r['key']}_4x.png")
    sprites=Image.new('RGB',(128,128),RGB[P['night']])
    for ci,comp in enumerate(companions):
        for di,row in enumerate(comp):
            for fi,sp in enumerate(row):paste_sprite(sprites,sp,(ci*64+fi*16,di*16))
    for i,b in enumerate(bosses):paste_sprite(sprites,b,(i*32,64))
    for i,pp in enumerate(props):
        for on,p in enumerate(pp):paste_sprite(sprites,p,((i%8)*16,96+(i//8)*16)) if on==0 else None
    sprites.save(OUT/'campaign_sprite_sheet.png');sprites.resize((768,768),Image.Resampling.NEAREST).save(OUT/'campaign_sprite_sheet_6x.png')
    propview=Image.new('RGB',(16*12,32),RGB[P['night']])
    for i,pp in enumerate(props):
        for on,p in enumerate(pp):paste_sprite(propview,p,(i*16,on*16))
    propview.resize((1152,192),Image.Resampling.NEAREST).save(OUT/'campaign_props_6x.png')
    frames=[]
    for f in range(4):
        view=Image.new('RGB',(144,92),RGB[P['bg_sunlit_dirt3']])
        for ci,c in enumerate(companions):
            for di,row in enumerate(c):
                pos=(di*32+10,ci*30+6)
                ImageDraw.Draw(view).ellipse((pos[0]+3,pos[1]+13,pos[0]+12,pos[1]+15),fill=RGB[P['bg_sunlit_dirt1']])
                paste_sprite(view,row[f],pos)
        for i,b in enumerate(bosses):paste_sprite(view,b,(32+i*48,60))
        frames.append(view.resize((864,552),Image.Resampling.NEAREST))
    frames[0].save(OUT/'campaign_walk_cycles.gif',save_all=True,append_images=frames[1:],duration=140,loop=0,disposal=2)
    # Composition proof only: props and actors are pasted into a separate review
    # image, NEVER into the opaque background or exported background arrays.
    composition=Image.new('RGB',(240*5,180*2),(27,34,48));cd=ImageDraw.Draw(composition)
    kindmap={'rest':'REST','wind_vane':'VANE','lamp':'LAMP','return_lantern':'LAMP',
             'brazier':'BRAZIER','weight_socket':'WEIGHT','root_socket':'WELL',
             'sign':'SIGN','optional':'CHIME'}
    companionmap={'HOMURA':'FIRE_SOCKET','MIDORI':'NATURE_SOCKET','FUURI':'WIND_SOCKET','KOHAKU':'STONE_SOCKET'}
    for i,(room,bg) in enumerate(zip(rooms,bgs)):
        view=bg.im.convert('RGB');d=ImageDraw.Draw(view)
        for ob in room['objects']:
            name=companionmap[ob['companion']] if ob['kind']=='bond_socket' else kindmap.get(ob['kind'])
            if name and not ob.get('visible_if'):
                x,y=ob['at'];paste_sprite(view,props[PROP_NAMES.index(name)][0],(x-8,y-8))
        paste_sprite(view,base.hero('up',0),(112,124))
        paste_sprite(view,companions[0 if room['id']<9 else 1][1][1],(130,125))
        if room['id'] in (8,13):paste_sprite(view,bosses[0 if room['id']==8 else 1],(104,52))
        x=(i%5)*240;y=(i//5)*180;composition.paste(view,(x,y))
        cd.text((x+4,y+162),f"ART MOCKUP | {room['id']:02d} {room['key']}",fill=(243,232,201))
    composition.resize((2400,720),Image.Resampling.NEAREST).save(OUT/'campaign_scene_mockups_2x.png')


def main():
    global P,PAL,RGB,Art
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base',type=Path,default=OUT/'generate_assets.py')
    parser.add_argument('--layouts',type=Path,default=OUT/'campaign_layouts.json')
    args=parser.parse_args()
    spec=importlib.util.spec_from_file_location('emberbond_base_art',args.base.resolve())
    base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
    P=base.P;PAL=base.PAL;RGB=base.rgb;Art=base.Art
    assert len(base.COLORS)==178, 'Campaign is authored against the existing 178-color palette'
    assert base.BASE_PALETTE_SIZE==97, 'Actor palette slots 0..96 must remain unchanged'
    OUT.mkdir(exist_ok=True);SRC.mkdir(exist_ok=True)
    layout_bytes=args.layouts.read_bytes();layout=json.loads(layout_bytes)
    rooms=sorted(layout['rooms'],key=lambda r:r['id'])
    assert [r['id'] for r in rooms]==list(range(4,14))
    assert all(r['size']==[240,160] and r['play_bounds']==[8,28,224,124] for r in rooms)
    bgs=[background(r) for r in rooms]
    companions=[[[fn(d,f) for f in range(4)] for d in DIRECTIONS] for fn in (fuuri,kohaku)]
    bosses=[kazane(),core_keeper()]
    props=[[prop(n,on) for on in range(2)] for n in PROP_NAMES]
    for bg in bgs:assert 0 not in bg.im.tobytes() and max(bg.im.tobytes())<178
    actor_images=[sp for comp in companions for row in comp for sp in row]+bosses+[p for pair in props for p in pair]
    for sp in actor_images:assert 0 in sp.im.tobytes() and max(sp.im.tobytes())<=96
    for comp in companions:
        for row in comp:assert len({sp.im.tobytes() for sp in row})==4, 'Each direction needs four distinct poses'
    header='''/* Original Emberbond campaign art. Generated by assets/generate_campaign.py. */
#ifndef EMBERBOND_CAMPAIGN_ART_H
#define EMBERBOND_CAMPAIGN_ART_H
#define CAMPAIGN_ART_FIRST_ROOM 4
#define CAMPAIGN_BACKGROUND_COUNT 10
#define CAMPAIGN_COMPANION_COUNT 2
#define CAMPAIGN_BOSS_COUNT 2
/* All images are linear row-major palette indices using existing game_palette.
 * Backgrounds: opaque 240x160. Sprite zero is transparent. No new RAM buffers.
 * Companion order: Fuuri, Kohaku. Direction order: down, up, left, right.
 * Frames: idle, first contact/wing beat, raised passing, second contact/beat.
 * Sprite anchors: center (draw 16x16 at x-8,y-8; 32x32 at x-16,y-16).
 * Engine owns all dynamic obstacle/bridge/prop states and all actor drawing.
 */
enum { CAMPAIGN_COMP_FUURI, CAMPAIGN_COMP_KOHAKU };
enum { CAMPAIGN_BOSS_KAZANE, CAMPAIGN_BOSS_CORE };
'''
    header+='enum { '+', '.join('CAM_PROP_'+n.removesuffix('_SOCKET') for n in PROP_NAMES)+', CAM_PROP_COUNT };\n'
    header+=''.join(f"extern const unsigned char campaign_background_{r['key']}[38400];\n" for r in rooms)
    header+='''extern const unsigned char * const campaign_backgrounds[CAMPAIGN_BACKGROUND_COUNT];
extern const unsigned char campaign_companion_direction_frames[2][4][4][256];
extern const unsigned char campaign_boss_data[2][1024];
/* Prop state [0]=off/unlatched, [1]=on/latched. Props are optional engine utilities. */
extern const unsigned char campaign_prop_data[CAM_PROP_COUNT][2][256];
#endif
'''
    (SRC/'campaign_art.h').write_text(header)
    f=io.StringIO()
    for r,bg in zip(rooms,bgs):emit_array(f,'campaign_background_'+r['key'],bg.im.tobytes())
    f.write('const unsigned char * const campaign_backgrounds[CAMPAIGN_BACKGROUND_COUNT] = {'+','.join('campaign_background_'+r['key'] for r in rooms)+'};\n\n')
    emit_tensor(f,'campaign_companion_direction_frames',companions,[2,4,4,256])
    emit_tensor(f,'campaign_boss_data',bosses,[2,1024])
    emit_tensor(f,'campaign_prop_data',props,[12,2,256])
    chunks=split_source(f.getvalue())
    previews(rooms,bgs,companions,bosses,props,base)
    manifest={
      'schema':1,'generator':'assets/generate_campaign.py','rights':'Original code-native pixel art. No third-party images, screenshots, sprite extractions, ROM data, or raster model inputs.',
      'palette_count':len(base.COLORS),'palette_slots_preserved':[0,177],'actor_palette_slots':[0,96],
      'palette_sha256':hashlib.sha256(json.dumps(base.COLORS).encode()).hexdigest(),
      'layout_sha256':hashlib.sha256(layout_bytes).hexdigest(),
      'backgrounds':{str(r['id']):{'key':r['key'],'size':[240,160],'sha256':hashlib.sha256(bg.im.tobytes()).hexdigest(),'static_solids':r['static_solids'],'dynamic_solids':r['dynamic_solids']} for r,bg in zip(rooms,bgs)},
      'sprites':{'companions':['Fuuri','Kohaku'],'directions':list(DIRECTIONS),'frames_per_direction':4,'base_palette_only':True,'bosses':['Kazane','Closed Core keeper'],'prop_order':list(PROP_NAMES),'prop_states':['off','on'],'transparent_index':0},
      'closed_pits':[{'room':5,'rect':[8,88,224,16],'engine_bridge_rect':[96,88,48,16]},{'room':11,'rect':[8,84,224,20],'engine_bridge_rect':[104,84,32,20]}],
      'engine_contract':'Backgrounds contain floor below dynamic gates, cracked arches, well caps and thorns; engine must draw/erase these. Pits are closed voids until engine paints the bridge. Interactive props are not baked in. Flat decorative pads and inlaid channels are walkable. Top 17px may be covered by HUD. Scenery uses exact static footprint rectangles from campaign_layouts.json.',
      'data_bytes':38400*10+2*4*4*256+2*1024+12*2*256,
      'pointer_bytes_gba':40,'rom_bytes_total_gba':38400*10+2*4*4*256+2*1024+12*2*256+40,
      'generated_c_chunks':chunks,'max_chunk_bytes':max(p.stat().st_size for p in (SRC/'campaign_art_data').glob('part_*.inc')),
      'verification':{'opaque_backgrounds':True,'palette_unchanged':True,'all_sprite_colors_in_base_palette':True,'four_distinct_frames_per_direction':True,'geometry_copied_from_master':True},
    }
    (OUT/'campaign_art_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'CAMPAIGN_CREDITS.txt').write_text(manifest['rights']+'\nDeterministic Python/Pillow geometry with the existing Emberbond RGB555 palette.\n')
    print(json.dumps({k:manifest[k] for k in ('data_bytes','rom_bytes_total_gba','generated_c_chunks','max_chunk_bytes','verification')},indent=2))

if __name__=='__main__':main()
