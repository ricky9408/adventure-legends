#!/usr/bin/env python3
"""Generate Emberbond's original, continuous Sunmere Grove overworld.

The 480x320 indexed artwork shares generate_assets.py's unmodified RGB555 palette.
Everything is authored from geometric pixel-art primitives, without raster inputs.
Static geometry, a collision overlay, and finite-radius route proofs are emitted
from the same obstacle definitions as the C asset. Run with Python 3 and Pillow.
"""
from collections import deque
from pathlib import Path
import hashlib
import json
import random

from PIL import Image, ImageDraw
from generate_assets import Art, COLORS, P, PAL, color_background, tree, bush, flowers, stone

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets'
SRC = ROOT / 'src'
W, H = 480, 320
SEED = 73419
RIVER = (0, 156, W, 20)
BRIDGE = (228, 156, 24, 20)
LANDMARKS = {
    'spawn': (240, 287),
    'village_exit': (240, 304),
    'bridge': (240, 166),
    'camp': (120, 248),
    'chest': (92, 72),
    'temple': (368, 24),
}
COMBAT_GLADES = [(180, 230), (318, 245), (290, 100), (400, 90)]
# These corridors and landmark clearings are checked before adding solid props.
# The southern and northern strips have different shapes, never repeated panels.
PATH_LINES = [
    ([(240, 320), (240, 286), (241, 247), (240, 209), (240, 178)], 24),
    ([(120, 248), (164, 248), (204, 248), (240, 248)], 17),
    ([(240, 152), (240, 122), (240, 92)], 24),
    ([(92, 72), (92, 92), (153, 92), (216, 92), (286, 92), (345, 92), (399, 92)], 20),
    ([(368, 92), (368, 67), (368, 40), (368, 22)], 25),
]
SOLIDS = []
TREES = []
PROPS = []


def add_solid(kind, box):
    x, y, w, h = box
    x1, y1 = max(0, x), max(0, y)
    x2, y2 = min(W, x + w), min(H, y + h)
    if x2 > x1 and y2 > y1:
        clipped = [x1, y1, x2 - x1, y2 - y1]
        SOLIDS.append(clipped)
        PROPS.append({'kind': kind, 'rect': clipped})


def make_path_mask(extra=0):
    mask = Image.new('1', (W, H))
    d = ImageDraw.Draw(mask)
    for pts, width in PATH_LINES:
        d.line(pts, fill=1, width=width + 2 * extra)
        r = (width + 2 * extra) // 2
        for x, y in pts:
            d.ellipse((x - r, y - r, x + r, y + r), fill=1)
    return mask


CLEAR_MASK = make_path_mask(10)
clear_draw = ImageDraw.Draw(CLEAR_MASK)
for x, y, r in [(120, 248, 30), (92, 72, 24), (240, 287, 19)]:
    clear_draw.ellipse((x-r, y-r, x+r, y+r), fill=1)
for x, y in COMBAT_GLADES:
    clear_draw.ellipse((x-28, y-24, x+28, y+24), fill=1)
# Keep both bridge approaches readable and free of foreground canopy overlap.
clear_draw.rectangle((210, 128, 270, 210), fill=1)


def ground(a):
    rng = random.Random(SEED)
    a.r((0, 0, W-1, H-1), 'grass2')
    # Irregular broad terrain planes distinguish glades from deep woodland.
    glades = [(166, 235, 76, 43), (318, 245, 79, 47), (287, 100, 62, 39),
              (403, 91, 55, 43), (100, 73, 53, 42), (239, 293, 60, 28)]
    for x, y, rx, ry in glades:
        a.p([(x-rx,y-ry//3),(x-rx+8,y-ry+6),(x-rx//3,y-ry),
             (x+rx//2,y-ry+3),(x+rx,y-ry//3),(x+rx-3,y+ry//2),
             (x+rx//2,y+ry),(x-rx//2,y+ry-2),(x-rx,y+ry//3)], 'grass3')
    # Sparse clustered mottling: large plain areas remain calm behind actors.
    for _ in range(190):
        x, y = rng.randrange(W), rng.randrange(H)
        rx, ry = rng.randrange(4, 15), rng.randrange(2, 5)
        a.p([(x-rx,y),(x-rx+3,y-ry),(x+rx-4,y-ry),(x+rx,y),
             (x+rx-3,y+ry),(x-rx+4,y+ry)], rng.choice(['grass2','grass3','grass3','grass4']))
    for _ in range(880):
        x, y = rng.randrange(2,W-3), rng.randrange(2,H-3)
        a.r((x, y, x+rng.randrange(1,4), y), rng.choice(['grass1','grass2','grass3','grass4']))
    for _ in range(155):
        x, y = rng.randrange(4,W-4), rng.randrange(6,H-4)
        a.l([(x-2,y),(x-1,y-2),(x,y),(x+2,y-1)],'grass4')
        a.dot(x-1,y+1,'grass1')


def woodland_floor(a):
    # Darker moss beds gather under tree islands, not across the travel route.
    beds = [(0,0,63,143),(0,197,75,319),(423,0,479,137),(419,194,479,319),
            (130,0,211,61),(133,118,197,143),(269,14,313,58),
            (67,190,139,209),(340,198,390,218),(62,289,183,319)]
    for x1,y1,x2,y2 in beds:
        a.p([(x1,y1+8),(x1+8,y1),(x2-9,y1+2),(x2,y1+12),
             (x2-3,y2-6),(x2-16,y2),(x1+9,y2-2),(x1,y2-12)],'grass1')
        for x in range(x1+7,x2,15):
            a.r((x,y2-3,x+4,y2-3),'grass3')


def paths(a):
    # Layered mask dilation gives a warm worn rim and softly stepped silhouettes.
    for extra, color in [(3,'grass1'),(2,'dirt1'),(1,'dirt2'),(0,'dirt3')]:
        mask = make_path_mask(extra)
        a.im.paste(P[color], (0,0), mask)
    core = make_path_mask(-3)
    a.im.paste(P['dirt4'], (0,0), core)
    a.d = ImageDraw.Draw(a.im)
    mask = make_path_mask(-2)
    rng = random.Random(SEED + 1)
    for _ in range(180):
        x,y = rng.randrange(5,W-5),rng.randrange(5,H-5)
        if mask.getpixel((x,y)):
            a.r((x,y,x+rng.randrange(2,5),y),rng.choice(['dirt2','dirt3']))
    # A few shallow stepping stones suggest an old road without obstructing it.
    for x,y in [(230,302),(238,276),(231,220),(231,196),(231,125),
                (134,89),(181,88),(286,87),(340,89),(359,63),(87,82),
                (137,245),(198,243)]:
        stone(a,x,y,7,3)


def clearing(a,x,y,rx,ry):
    # Walkable packed-earth clearing; centers stay empty for engine-owned props.
    a.e((x-rx-3,y-ry-2,x+rx+3,y+ry+2),'grass1')
    a.e((x-rx-1,y-ry-1,x+rx+1,y+ry+1),'dirt1')
    a.e((x-rx,y-ry,x+rx,y+ry),'dirt2')
    a.e((x-rx+3,y-ry+2,x+rx-3,y+ry-2),'dirt3')
    a.e((x-rx+6,y-ry+4,x+rx-6,y+ry-4),'dirt4')


def river(a):
    rng=random.Random(SEED+2)
    # Banks are decorative and walkable; the exact water collision is y156..175.
    a.r((0,150,W-1,155),'grass0')
    a.r((0,151,W-1,155),'dirt1')
    a.r((0,152,W-1,154),'dirt2')
    a.r((0,154,W-1,155),'stone1')
    a.r((0,156,W-1,175),'water1')
    a.r((0,156,W-1,158),'water0')
    a.r((0,159,W-1,161),'water2')
    a.r((0,163,W-1,171),'water2')
    a.r((0,174,W-1,175),'water0')
    a.r((0,176,W-1,179),'dirt1')
    a.r((0,176,W-1,177),'stone3')
    a.r((0,180,W-1,182),'grass0')
    a.r((0,180,W-1,180),'grass4')
    # Asymmetric banks make the imposed horizontal water strip feel natural.
    for x in range(-3,W,17):
        yy=151+rng.randrange(-2,2)
        a.p([(x,yy),(x+6,yy-2),(x+13,yy),(x+15,154),(x,154)],'dirt2')
        a.l([(x+2,yy),(x+6,yy-2),(x+11,yy-1)],'grass4')
        xx=x+rng.randrange(2,8)
        a.r((xx,178,xx+6,180),'dirt2')
        a.dot(xx+1,180,'grass3')
    for y in (161,165,170,173):
        for x in range(-20,W,42):
            xx=x+rng.randrange(0,23)
            a.l([(xx,y),(xx+9,y),(xx+11,y-1),(xx+18,y-1)],'water3')
            a.r((xx+3,y,xx+6,y),'water4')
            if y==165:a.r((xx+11,y-1,xx+13,y-1),'watergleam')
    # Broken crossing stubs stop at the water; the engine grows the bridge.
    for y1,y2 in [(148,155),(176,183)]:
        a.r((227,y1,252,y2),'wood0')
        a.r((229,y1,250,y2),'wood2')
        for yy in range(y1,y2+1,3):
            a.r((229,yy,250,yy+1),'wood4')
            a.r((232,yy,246,yy),'wood5')
    for x in (225,253):
        for y in (152,180):
            a.r((x-1,y-4,x+1,y+2),'wood0')
            a.r((x,y-4,x+1,y),'wood3')
            a.dot(x,y-4,'wood5')
    # Reeds flank banks without blocking a single passage or hiding the gap.
    for x in (15,38,76,116,161,193,282,311,349,410,447,469):
        for dx,dy in [(-2,0),(1,-2),(4,1)]:
            yy=151 if x%2 else 183
            a.l([(x+dx,yy),(x+dx,yy-5+dy)],'pine2')
            a.r((x+dx,yy-6+dy,x+dx+1,yy-4+dy),'moss2')


def ruins(a):
    # North-east temple gate. Its lintel and pillars are real collidable geometry;
    # entrance x352..384 is clear at y28..35 for the engine's transition trigger.
    a.e((321,34,414,49),'shadowsoft')
    for x1,y1,x2,y2 in [(330,42,406,46),(333,37,403,42),(337,32,399,37)]:
        a.r((x1,y1,x2,y2),'stone1')
        a.r((x1+1,y1,x2-1,y2-2),'stone3')
        a.l([(x1+1,y1),(x2-1,y1)],'stone5')
        for x in range(x1+10,x2-2,17):a.r((x,y1,x,y2-2),'stone2')
    a.r((350,0,386,32),'stone0')
    a.r((352,9,384,33),'pine0')
    a.r((356,15,380,33),'shadow')
    a.r((360,20,376,33),'shadowsoft')
    a.r((352,30,384,34),'dirt2')
    a.r((354,32,382,35),'dirt3')
    for x in (334,386):
        a.r((x-3,28,x+19,36),'stone0')
        a.r((x-2,28,x+18,33),'stone3')
        a.l([(x-1,28),(x+17,28)],'stone5')
        a.r((x,4,x+16,30),'stone0')
        a.r((x+2,5,x+14,29),'stone2')
        a.r((x+3,5,x+7,28),'stone4')
        a.r((x+5,6,x+7,25),'stone5')
        for yy in (11,21):a.r((x+2,yy,x+14,yy),'stone1')
        a.r((x-3,1,x+19,7),'stone1')
        a.r((x-2,1,x+18,5),'stone4')
        a.l([(x-1,1),(x+17,1)],'stone5')
        add_solid('temple_pillar',(x-3,1,23,36))
    a.r((328,0,408,6),'stone0')
    a.r((330,0,406,3),'stone4')
    a.r((338,7,398,11),'stone1')
    a.r((340,7,396,9),'stone3')
    a.p([(358,0),(368,-4),(378,0),(375,9),(368,14),(361,9)],'stone0')
    a.p([(360,0),(368,-2),(376,0),(373,7),(368,11),(363,7)],'gold1')
    a.p([(368,0),(372,4),(368,9),(364,4)],'gold3')
    a.dot(368,3,'gold4')
    add_solid('temple_lintel',(352,0,33,20))
    # Ivy clings to stone rather than obscuring the entry point.
    for x,y in [(332,7),(331,13),(338,20),(399,5),(402,12),(401,24)]:
        a.r((x,y,x+4,y+2),'pine2');a.r((x+1,y-1,x+4,y),'pine4')
        a.dot(x+2,y-1,'leaflight')
    # Low ruined walls frame the approach, leaving central plaza open.
    for x,y,w in [(291,44,31),(411,43,29),(291,55,14)]:
        a.e((x-2,y+5,x+w+3,y+13),'shadowsoft')
        a.r((x,y,x+w,y+10),'stone0')
        a.r((x+1,y,x+w-1,y+8),'stone2')
        a.r((x+1,y,x+w-1,y+2),'stone4')
        for xx in range(x+8,x+w,11):a.r((xx,y+3,xx,y+8),'stone1')
        a.r((x+3,y-1,x+10,y),'moss2')
        add_solid('ruined_wall',(x,y,w+1,11))


def chest_garden(a):
    # The optional relic sits in a sunny grove, not behind an invisible barrier.
    clearing(a,92,72,23,18)
    # A walkable incomplete ring of flat, pale old paving surrounds the chest.
    for x,y,w,h in [(72,60,8,4),(86,54,11,4),(103,59,8,4),
                    (110,72,7,4),(70,75,7,4),(77,85,7,3),(101,86,8,3)]:
        stone(a,x,y,w,h)
    for x,y in [(63,65),(66,78),(119,62),(121,76),(102,47)]:
        flowers(a,x,y,'flower1')


def stump(a,x,y):
    a.e((x-10,y-2,x+11,y+5),'shadowsoft')
    a.p([(x-7,y+1),(x-6,y-9),(x+6,y-9),(x+8,y+2),(x+3,y+4),(x-4,y+4)],'wood0')
    a.r((x-5,y-7,x+5,y+2),'wood2')
    a.r((x-4,y-6,x-2,y+1),'wood3')
    a.e((x-7,y-12,x+7,y-5),'wood1')
    a.e((x-5,y-11,x+5,y-6),'wood4')
    a.e((x-2,y-10,x+3,y-7),'wood2')
    a.r((x-1,y-9,x+2,y-8),'wood5')
    add_solid('stump',(x-6,y-11,13,15))


def boulder(a,x,y,w=20,h=12):
    a.e((x-2,y+h-3,x+w+3,y+h+4),'shadowsoft')
    stone(a,x,y,w,h)
    a.p([(x+3,y),(x+w-5,y),(x+w-2,y+3),(x+5,y+4)],'stone3')
    a.l([(x+4,y),(x+w-6,y)],'stone5')
    a.r((x+2,y+h-2,x+8,y+h-1),'moss1')
    add_solid('boulder',(x+1,y+1,w-1,h))


def trees(a):
    # Deliberately composed canopy islands, varying scale and depth. No tiling.
    placements = [
        (4,36,1.25),(28,31,1.05),(54,30,.95),(78,20,.95),(106,22,1.05),
        (136,28,1.12),(162,26,1.04),(188,31,1.2),(215,21,.98),
        (239,20,1.15),(267,29,1.12),(290,23,.92),(316,24,1.05),
        (436,27,1.12),(461,37,1.15),(487,46,1.3),
        (2,72,1.13),(27,67,1.2),(48,54,.95),
        (0,111,1.15),(27,108,1.2),(49,128,1.05),(12,146,1.1),
        (138,58,.93),(167,53,.99),(193,52,1.04),
        (137,146,.72),(160,147,.78),(184,147,.74),
        (449,75,1.1),(476,86,1.23),(450,131,1.1),(480,140,1.2),
        (11,229,1.25),(39,220,1.15),(64,213,.99),(91,207,.92),(119,210,1.08),
        (276,215,.90),(365,217,.92),(393,210,1.01),(434,221,1.1),(461,217,1.15),(489,230,1.18),
        (9,264,1.15),(36,258,1.07),(63,280,1.02),(29,296,1.25),
        (420,269,1.08),(447,272,1.22),(475,279,1.3),
        (3,337,1.2),(42,337,1.2),(80,333,1.14),(112,337,1.12),(147,333,1.14),(178,339,1.03),
        (278,341,1.1),(308,336,1.13),(341,337,1.14),(375,334,1.09),(409,335,1.21),(447,337,1.2),(479,329,1.23),
    ]
    for x,y,s in sorted(placements,key=lambda t:t[1]):
        # Match art's footprint with an inset canopy body; reject intrusions into
        # travel corridors and landmark clearings at generation time.
        x1=max(0,int(x-12*s)); y1=max(0,int(y-37*s))
        x2=min(W,int(x+12*s)+1); y2=min(H,int(y+2*s)+1)
        if x2<=x1 or y2<=y1:continue
        # Tiny perimeter leaves may overhang a clearing; solid volumes may not.
        if CLEAR_MASK.crop((x1,y1,x2,y2)).getbbox():
            continue
        tree(a,x,y,s)
        add_solid('tree_canopy',(x1,y1,x2-x1,y2-y1))
        TREES.append([x,y,s])


def accents(a):
    # Distinct small scenery vignettes: a camp log, ruined marker, eastern stones.
    stump(a,78,246)
    stump(a,343,281)
    boulder(a,167,184,21,11)
    boulder(a,398,197,23,12)
    boulder(a,321,126,17,10)
    boulder(a,69,111,14,9)
    boulder(a,303,293,17,9)
    for x,y in [(70,232),(61,247),(79,262),(106,285),(145,276),(164,206),
                (203,273),(278,283),(357,261),(389,239),(410,290),
                (77,42),(111,118),(209,62),(256,60),(267,128),(338,113),(418,123)]:
        bush(a,x,y,12)
    # Flowers grouped by local color make the four glades feel like places.
    groups=[(153,216,'flower1'),(200,217,'flower0'),(162,271,'flower1'),
            (305,216,'flower0'),(352,253,'flower1'),(303,269,'flower0'),
            (274,72,'flower1'),(319,104,'flower0'),(385,121,'flower1'),
            (424,74,'flower0'),(124,121,'flower0'),(83,278,'flower1')]
    rng=random.Random(SEED+4)
    path_mask=make_path_mask(2)
    for gx,gy,color in groups:
        for _ in range(7):
            x,y=gx+rng.randrange(-10,11),gy+rng.randrange(-5,6)
            if 0<=x<W and 0<=y<H and not path_mask.getpixel((x,y)):
                flowers(a,x,y,color)
    # Camp rim is decorative. A full radius 24 around the fire remains clear.
    for x,y in [(97,226),(114,222),(137,225),(146,240),(143,263),(114,275),(95,269)]:
        stone(a,x,y,7,3)
    # A few golden falling leaves imply sunshine, never simulated characters.
    for x,y in [(43,184),(98,196),(189,301),(328,197),(442,302),(188,65),(429,138)]:
        a.l([(x-1,y),(x+1,y-1),(x+3,y)],'leafwarm')
        a.dot(x+1,y+1,'moss2')


def collision_mask(bridge_open=False,radius=0):
    mask=Image.new('1',(W,H))
    d=ImageDraw.Draw(mask)
    for x,y,w,h in SOLIDS:
        d.rectangle((x-radius,y-radius,x+w-1+radius,y+h-1+radius),fill=1)
    water=Image.new('1',(W,H))
    wd=ImageDraw.Draw(water)
    wd.rectangle((0,156,W-1,175),fill=1)
    if bridge_open:wd.rectangle((228,156,251,175),fill=0)
    # Square player-foot radius: water must also be inflated around the bridge.
    if radius:
        from PIL import ImageFilter
        water=water.convert('L').point(lambda p:255 if p else 0).filter(ImageFilter.MaxFilter(2*radius+1)).convert('1')
    mask.paste(1,(0,0),water)
    if radius:
        d=ImageDraw.Draw(mask)
        d.rectangle((0,0,W-1,radius-1),fill=1)
        d.rectangle((0,H-radius,W-1,H-1),fill=1)
        d.rectangle((0,0,radius-1,H-1),fill=1)
        d.rectangle((W-radius,0,W-1,H-1),fill=1)
    return mask


def find_route(start,goal,bridge_open,radius=4):
    mask=collision_mask(bridge_open,radius)
    p=mask.load()
    if p[start] or p[goal]:return None
    queue=deque([start]); previous={start:None}
    while queue:
        here=queue.popleft()
        if here==goal:
            route=[]
            while here is not None:route.append(here);here=previous[here]
            return route[::-1]
        x,y=here
        for nx,ny in ((x,y-1),(x-1,y),(x+1,y),(x,y+1)):
            nxt=(nx,ny)
            if 0<=nx<W and 0<=ny<H and not p[nxt] and nxt not in previous:
                previous[nxt]=here;queue.append(nxt)
    return None


def verify_routes():
    cases=[('south_to_bridge_bank',(240,287),(240,184),False,True),
           ('south_to_camp',(240,287),(120,248),False,True),
           ('south_to_north_before_bridge',(240,287),(240,146),False,False),
           ('south_to_north_after_bridge',(240,287),(240,146),True,True),
           ('bridge_to_temple',(240,146),(368,31),True,True),
           ('bridge_to_chest',(240,146),(92,72),True,True),
           ('south_to_west_combat',(240,287),(180,230),False,True),
           ('south_to_east_combat',(240,287),(318,245),False,True),
           ('bridge_to_north_combat',(240,146),(290,100),True,True),
           ('bridge_to_east_combat',(240,146),(400,90),True,True)]
    results=[]; routes={}
    for name,start,goal,opened,expected in cases:
        path=find_route(start,goal,opened)
        assert bool(path)==expected, f'Route assertion failed: {name}'
        results.append({'name':name,'from':start,'to':goal,'bridge_open':opened,
                        'reachable':bool(path),'expected':expected,'steps':len(path)-1 if path else None,
                        'player_foot_radius':4,'passed':True})
        if path:routes[name]=path
    # Exact clearance around the checkpoint is an intentional engine contract.
    for name in ('camp','chest'):
        cx,cy=LANDMARKS[name]
        for x,y,w,h in SOLIDS:
            nx=max(x,min(cx,x+w-1));ny=max(y,min(cy,y+h-1))
            assert (nx-cx)**2+(ny-cy)**2>24**2,f'Solid intrudes into {name} radius 24'
    return results,routes


def camp_sprite(lit):
    a=Art(16,16,'transparent')
    # The stone ring is visibly cold before the checkpoint is activated.
    a.e((1,8,14,14),'shadow')
    for x,y in [(2,10),(3,8),(7,7),(11,8),(13,10),(11,13),(7,14),(3,13)]:
        a.r((x-1,y-1,x+1,y+1),'stone0')
        a.r((x-1,y-1,x,y),'stone3')
        a.dot(x-1,y-1,'stone5')
    a.l([(4,11),(11,9)],'wood0',3)
    a.l([(4,9),(11,12)],'wood1',3)
    a.l([(4,9),(11,12)],'wood3')
    a.dot(4,9,'wood5');a.dot(11,12,'wood4')
    if lit:
        a.p([(4,10),(3,7),(5,3),(7,5),(8,0),(10,4),(12,7),(10,11),(7,12)],'fire0')
        a.p([(5,10),(4,7),(6,4),(7,6),(8,2),(10,6),(11,8),(9,11),(7,11)],'fire1')
        a.p([(6,10),(5,8),(7,5),(8,7),(9,5),(10,9),(8,11)],'fire2')
        a.p([(7,10),(6,8),(8,6),(9,9),(8,11)],'gold3')
        a.dot(8,8,'gold4');a.dot(12,3,'fire2');a.dot(3,2,'gold2')
    else:
        a.r((6,9,9,10),'wood0');a.dot(7,9,'stone2')
    return a


def chest_sprite(opened):
    a=Art(16,16,'transparent')
    a.e((1,12,14,15),'shadow')
    a.r((2,7,13,13),'ink');a.r((3,8,12,12),'wood1')
    a.r((3,9,12,11),'wood3');a.r((4,9,5,11),'wood4')
    a.r((2,8,3,13),'gold0');a.r((12,8,13,13),'gold0')
    a.r((2,8,2,12),'gold2');a.r((12,8,12,12),'gold2')
    a.r((3,13,12,13),'wood0')
    if opened:
        a.p([(2,7),(1,2),(3,0),(12,0),(14,2),(13,7)],'ink')
        a.r((3,1,12,5),'wood2');a.r((4,2,11,5),'wood0')
        a.r((3,1,12,1),'gold2');a.r((2,2,3,5),'gold1');a.r((12,2,13,5),'gold1')
        a.r((3,6,12,9),'ink');a.r((4,7,11,8),'wood0')
        a.r((3,10,12,10),'gold1');a.dot(10,7,'gold3')
    else:
        a.p([(1,8),(1,5),(3,3),(12,3),(14,5),(14,8)],'ink')
        a.r((3,4,12,7),'wood2');a.r((3,4,12,5),'wood4')
        a.r((2,6,13,8),'wood2');a.r((2,8,13,9),'wood0')
        for x in (3,11):
            a.r((x,4,x+1,8),'gold1');a.r((x,4,x,7),'gold3')
        a.r((7,7,9,10),'gold0');a.r((7,7,9,9),'gold3');a.dot(8,8,'wood0')
    return a


def ranger_sprite(windup):
    a=Art(16,16,'transparent')
    # An original coral-bloom seed spitter with a petal hood and root boots.
    a.e((2,12,13,15),'shadow')
    a.p([(3,11),(1,13),(1,14),(5,14),(7,12),(10,12),(11,14),(14,14),(13,12),(11,10)],'pine0')
    a.l([(2,13),(5,12),(6,13)],'pine4');a.l([(10,12),(12,13),(13,13)],'pine3')
    a.p([(2,6),(1,3),(4,1),(6,2),(8,0),(11,1),(11,3),(14,3),(15,6),(13,9),(11,13),(5,13),(2,10)],'rose0')
    a.p([(3,6),(2,3),(4,2),(6,3),(8,1),(10,2),(10,4),(13,4),(14,6),(12,9),(10,11),(5,11),(3,9)],'rose3')
    a.p([(3,3),(4,2),(6,3),(8,1),(10,2),(9,4),(6,5)],'rose5')
    a.p([(11,4),(13,4),(14,6),(12,8),(10,7)],'rose4')
    a.p([(4,6),(6,4),(10,4),(12,6),(11,10),(9,12),(5,11),(3,9)],'pine0')
    a.p([(5,6),(7,5),(10,5),(11,7),(10,10),(8,11),(5,10)],'pine2')
    a.r((5,6,6,7),'white');a.r((10,6,11,7),'white')
    a.dot(6,7,'ink');a.dot(10,7,'ink')
    if windup:
        a.e((5,8,11,13),'gold0');a.e((6,8,10,12),'gold2')
        a.e((7,9,9,11),'gold4');a.dot(8,9,'white')
        a.dot(2,8,'gold3');a.dot(13,10,'gold4');a.dot(12,1,'gold2')
        a.r((5,4,6,4),'gold2');a.r((10,4,11,4),'gold2')
    else:
        a.e((6,9,10,12),'wood0');a.e((7,9,9,11),'gold0')
        a.r((7,10,9,11),'ink');a.dot(7,9,'gold2')
    return a


def make_sprites():
    return [camp_sprite(False),camp_sprite(True),chest_sprite(False),chest_sprite(True),
            ranger_sprite(False),ranger_sprite(True)]


def odd_camera_bitmap(data):
    """One-pixel left shift per row permits aligned DMA16 at odd camera X.

    The final column repeats itself so no row ever reads the following row.
    The regular bitmap remains authoritative artwork and is never changed.
    """
    assert len(data)==W*H
    odd=b''.join(data[y*W+1:(y+1)*W]+data[(y+1)*W-1:(y+1)*W] for y in range(H))
    assert len(odd)==len(data)
    for y in range(H):
        start,end=y*W,(y+1)*W
        assert odd[start:end-1]==data[start+1:end]
        assert odd[end-1]==data[end-1]
    return odd


def emit_assets(a,sprites):
    data=a.im.tobytes()
    assert len(data)==W*H
    assert min(data)>0 and max(data)<len(COLORS)
    assert len(COLORS)==178,'The overworld must retain the existing 178-color palette'
    header='''/* Generated by assets/generate_world.py. Original Sunmere Grove artwork. */
#ifndef EMBERBOND_WORLD_H
#define EMBERBOND_WORLD_H
#define WORLD_W 480
#define WORLD_H 320
#define WORLD_RIVER_Y 156
#define WORLD_RIVER_H 20
#define WORLD_BRIDGE_X 228
#define WORLD_BRIDGE_W 24
#define WORLD_TEMPLE_GATE_X 352
#define WORLD_TEMPLE_GATE_Y 28
#define WORLD_TEMPLE_GATE_W 33
#define WORLD_TEMPLE_GATE_H 8
'''
    for name,(x,y) in LANDMARKS.items():
        if name == 'bridge':
            header+=f'#define WORLD_BRIDGE_CENTER_X {x}\n#define WORLD_BRIDGE_Y {y}\n#define WORLD_BRIDGE_CENTER_Y {y}\n'
        else:
            header+=f'#define WORLD_{name.upper()}_X {x}\n#define WORLD_{name.upper()}_Y {y}\n'
    header+=f'''#define OVERWORLD_SOLID_COUNT {len(SOLIDS)}
#define WORLD_SOLID_COUNT OVERWORLD_SOLID_COUNT
/* Half-open rectangles: x <= point.x < x+w, y <= point.y < y+h.
   These are scenery only. Add world bounds and the dynamic river/bridge in game.c.
   The campfire and chest are drawn and controlled by the engine. */
typedef struct {{ short x,y,w,h; }} WorldRect;
extern const unsigned char overworld_bitmap[WORLD_W * WORLD_H];
/* Row-local one-pixel left shift. For odd camera X, use offset camera_x-1
   into this aligned bitmap for the same pixels with DMA16-safe addressing. */
extern const unsigned char overworld_bitmap_odd[WORLD_W * WORLD_H];
extern const WorldRect overworld_solids[OVERWORLD_SOLID_COUNT];
extern const unsigned int overworld_solid_count;
enum {{
    WORLD_SPR_CAMP_IDLE, WORLD_SPR_CAMP_LIT,
    WORLD_SPR_CHEST_CLOSED, WORLD_SPR_CHEST_OPEN,
    WORLD_SPR_RANGER_IDLE, WORLD_SPR_RANGER_WINDUP, WORLD_SPR_COUNT
}};
extern const unsigned char world_sprites[WORLD_SPR_COUNT][256];
#endif
'''
    (SRC/'world.h').write_text(header)
    lines=['const unsigned char overworld_bitmap[WORLD_W * WORLD_H] __attribute__((aligned(4))) = {\n']
    for start in range(0,len(data),32):
        lines.append('  '+','.join(str(n) for n in data[start:start+32])+',\n')
    lines.append('};\n\n')
    lines.append('const WorldRect overworld_solids[OVERWORLD_SOLID_COUNT] = {\n')
    lines.extend('    {'+','.join(map(str,r))+'},\n' for r in SOLIDS)
    lines.append('};\nconst unsigned int overworld_solid_count = OVERWORLD_SOLID_COUNT;\n')
    lines.append('const unsigned char world_sprites[WORLD_SPR_COUNT][256] __attribute__((aligned(4))) = {\n')
    for sprite in sprites:
        lines.append('  {\n')
        pixels=sprite.im.tobytes()
        for start in range(0,len(pixels),32):
            lines.append('    '+','.join(str(n) for n in pixels[start:start+32])+',\n')
        lines.append('  },\n')
    lines.append('};\n')
    odd=odd_camera_bitmap(data)
    lines.append('\nconst unsigned char overworld_bitmap_odd[WORLD_W * WORLD_H] __attribute__((aligned(4))) = {\n')
    for start in range(0,len(odd),32):
        lines.append('  '+','.join(str(n) for n in odd[start:start+32])+',\n')
    lines.append('};\n')
    folder=SRC/'world_data';folder.mkdir(exist_ok=True)
    chunks=[];chunk=[];size=0
    for line in lines:
        if chunk and size+len(line.encode())>32768:
            chunks.append(''.join(chunk));chunk=[];size=0
        chunk.append(line);size+=len(line.encode())
    if chunk:chunks.append(''.join(chunk))
    for old in folder.glob('part_*.inc'):old.unlink()
    for i,chunk in enumerate(chunks):(folder/f'part_{i:03d}.inc').write_text(chunk)
    (SRC/'world.c').write_text('#include "world.h"\n\n/* Generated data split into deterministic, reviewable chunks. */\n'+
        ''.join(f'#include "world_data/part_{i:03d}.inc"\n' for i in range(len(chunks))))
    return data,odd,chunks


def previews(a,routes,sprites):
    a.im.save(OUT/'overworld.png')
    sprite_sheet=Image.new('RGB',(96,24),(56,68,73))
    for i,sprite in enumerate(sprites):
        mask=Image.frombytes('L',(16,16),bytes(255 if p else 0 for p in sprite.im.tobytes()))
        sprite_sheet.paste(sprite.im.convert('RGB'),(16*i,4),mask)
    sprite_sheet.resize((768,192),Image.Resampling.NEAREST).save(OUT/'overworld_sprites.png')
    a.im.resize((W*3,H*3),Image.Resampling.NEAREST).save(OUT/'overworld_3x.png')
    overlay=a.im.convert('RGBA')
    layer=Image.new('RGBA',(W,H));d=ImageDraw.Draw(layer)
    for x,y,w,h in SOLIDS:d.rectangle((x,y,x+w-1,y+h-1),fill=(239,68,82,65),outline=(239,68,82,200))
    d.rectangle((0,156,W-1,175),fill=(42,126,255,90),outline=(30,80,210,220))
    d.rectangle((228,156,251,175),outline=(255,241,170,255),width=2)
    route_colors={'south_to_bridge_bank':(255,246,220,255),'south_to_camp':(250,120,195,255),
                  'south_to_north_after_bridge':(235,255,138,255),'bridge_to_temple':(255,205,70,255),
                  'bridge_to_chest':(120,244,255,255)}
    for name,col in route_colors.items():d.line(routes[name],fill=col,width=2)
    for name,(x,y) in LANDMARKS.items():
        d.ellipse((x-2,y-2,x+2,y+2),fill=(255,250,220,255),outline=(29,40,55,255))
    overlay=Image.alpha_composite(overlay,layer).convert('RGB')
    overlay.resize((W*3,H*3),Image.Resampling.NEAREST).save(OUT/'overworld_collision_routes.png')
    # Four overlapping camera crops demonstrate continuity rather than four rooms.
    crops=[(120,160),(0,160),(208,0),(0,0)]
    sheet=Image.new('RGB',(W,H))
    for i,(x,y) in enumerate(crops):sheet.paste(a.im.crop((x,y,x+240,y+160)).convert('RGB'),((i%2)*240,(i//2)*160))
    sheet.resize((W*2,H*2),Image.Resampling.NEAREST).save(OUT/'overworld_camera_previews.png')


def main():
    SOLIDS.clear();TREES.clear();PROPS.clear()
    a=Art(W,H,'grass2')
    ground(a);woodland_floor(a);paths(a)
    clearing(a,120,248,26,23)
    chest_garden(a);river(a);ruins(a);trees(a);accents(a)
    color_background(a,'forest')
    results,routes=verify_routes()
    sprites=make_sprites()
    data,odd,chunks=emit_assets(a,sprites)
    previews(a,routes,sprites)
    manifest={
        'name':'Sunmere Grove','canvas':[W,H],'seed':SEED,
        'art':'Original code-native indexed pixel art. One continuously composed scrolling landscape; no imported or traced artwork, baked actors, or repeated room panels.',
        'palette':{'source':'assets/generate_assets.py','count':len(COLORS),'unchanged':True,
                   'transparency_index':0,'background_opaque':True,'scene_ramp':'sunlit'},
        'landmarks':LANDMARKS,'temple_entrance':[352,28,33,8],
        'suggested_enemy_centers':COMBAT_GLADES,
        'dynamic_rectangles':[{'kind':'river','rect':RIVER,'exception_when_bridge_open':BRIDGE}],
        'engine_owned':['bridge animation','campfire/checkpoint','optional relic chest','all actors and effects'],
        'static_collision_rectangles':SOLIDS,'static_props':PROPS,'tree_positions':TREES,
        'collision_notes':'Rectangles are [x,y,width,height], half-open and slightly inset from real solid scenery. Grass, flowers, reeds, flat paving, small bushes and riverbanks are walkable. Add world bounds and dynamic river collision in the engine. A closed bridge is provably impassable; the open crossing and all destination routes are tested with a 4-pixel square foot radius.',
        'interactable_clear_radius':{'camp':24,'chest':24},
        'camp_clear_radius':24,
        'sprites':{'size':[16,16],'anchor':'center; blit at x-8,y-8','transparency_index':0,'names':['CAMP_IDLE','CAMP_LIT','CHEST_CLOSED','CHEST_OPEN','RANGER_IDLE','RANGER_WINDUP'],'bytes':1536},
        'route_proofs':results,
        'generated':{'bitmap_bytes':len(data),'bitmap_sha256':hashlib.sha256(data).hexdigest(),
                     'odd_bitmap_bytes':len(odd),'odd_bitmap_sha256':hashlib.sha256(odd).hexdigest(),
                     'odd_bitmap_shift':'Each row: odd[x]=original[min(x+1,W-1)]. Rows never bleed into the next row.',
                     'bitmap_alignment_bytes':4,
                     'chunks':len(chunks),'largest_chunk_bytes':max(len(c.encode()) for c in chunks),
                     'chunk_limit_bytes':32768},
        'previews':['overworld.png','overworld_3x.png','overworld_collision_routes.png','overworld_camera_previews.png','overworld_sprites.png'],
    }
    (OUT/'world_manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    print(f'Generated {W}x{H} original overworld: {len(SOLIDS)} solids, {len(TREES)} trees, {len(chunks)} chunks, {len(results)} route proofs passed, palette unchanged ({len(COLORS)} entries).')


if __name__=='__main__':main()
