#!/usr/bin/env python3
"""Emberbond: original, code-native pixel art. Authored from geometric primitives.
No external art, game sprites, traced assets, or generated raster inputs are used.
Run with Python 3 + Pillow. The shared palette is quantized to native GBA RGB555.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import math, random, json
try:
    import connected_road_art as roads
except ModuleNotFoundError:
    # Palette-only test imports load this module by absolute file path.
    import importlib.util
    _roads_spec=importlib.util.spec_from_file_location('connected_road_art',Path(__file__).with_name('connected_road_art.py'))
    roads=importlib.util.module_from_spec(_roads_spec);_roads_spec.loader.exec_module(roads)
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'assets'; SRC=ROOT/'src'; OUT.mkdir(exist_ok=True); SRC.mkdir(exist_ok=True)
# Index zero is reserved for transparency, including sprite backgrounds.
COLORS=[
('transparent','#14182c'),('ink','#172039'),('deep','#202843'),('night','#293453'),('slate','#3d4b69'),('fog','#65738a'),('silver','#93a5b0'),('white','#fff1d0'),
('pine0','#133d3c'),('pine1','#1a5147'),('pine2','#246752'),('pine3','#32815b'),('pine4','#56a86b'),('pine5','#8dce81'),('mint','#b4e1a0'),('grass0','#24554c'),
('grass1','#306b54'),('grass2','#3b7e58'),('grass3','#589469'),('grass4','#75ac75'),('dirt0','#6b5c54'),('dirt1','#9a8060'),('dirt2','#b8a070'),('dirt3','#d6bc87'),
('dirt4','#ecd6a1'),('wood0','#463544'),('wood1','#705049'),('wood2','#986349'),('wood3','#c18955'),('wood4','#e4b96f'),('wood5','#f7da8e'),('stone0','#34404f'),
('stone1','#495961'),('stone2','#62767a'),('stone3','#859796'),('stone4','#afbab0'),('stone5','#d3d5bb'),('rose0','#49283d'),('rose1','#6c334f'),('rose2','#983f5d'),
('rose3','#c25569'),('rose4','#e37c7c'),('rose5','#ffa18d'),('gold0','#996139'),('gold1','#c28a40'),('gold2','#e5b451'),('gold3','#ffda75'),('gold4','#fff0af'),
('fire0','#a44837'),('fire1','#d66537'),('fire2','#ef8d43'),('fire3','#ffc361'),('water0','#184558'),('water1','#23627a'),('water2','#308499'),('water3','#52adbb'),
('water4','#8dd6d4'),('blue0','#264169'),('blue1','#3766a1'),('blue2','#5195cb'),('blue3','#88c6e4'),('skin0','#b07765'),('skin1','#e7ab84'),('skin2','#ffcea0'),
('purple0','#383354'),('purple1','#544675'),('purple2','#766099'),('purple3','#a88dba'),('flower0','#db87ad'),('flower1','#ffe1c6'),('moss0','#526149'),('moss1','#718655'),
('moss2','#9caf69'),('moss3','#c9d78f'),('ember','#ed655b'),('heart','#ed697b'),('heartlight','#ff9a9c'),('shadow','#1c393e'),('teal0','#176579'),('teal1','#2794a0'),
('teal2','#65c4bc'),('cloud','#acacc0'),('dusk0','#473859'),('dusk1','#73526e'),('dusk2','#a66e83'),('dusk3','#d19796'),('dusk4','#efc9ad'),('sun','#ffe2a3'),('leaflight','#b8db82'),('leafwarm','#d8e79b'),('grasslit','#709d68'),('grassgold','#8ca977'),('plaster','#f2cf93'),('roofshine','#f69283'),('shadowsoft','#284d48'),('barklight','#d8a566'),('watergleam','#b6e4d4')]
# Preserve the original palette slots verbatim: UI, actors, combat effects and
# shadows all continue to use indices 0..96. Only scenery uses these new ramps.
# These are hand-authored material colors, not a gamma/brightness filter: cool
# contour shadows remain deep while grass, paths and stone catch more sunlight.
BASE_PALETTE_SIZE=len(COLORS)
SCENE_RAMPS={
    'sunlit':{
        'pine0':'#21513b','pine1':'#327144','pine2':'#459157',
        'pine3':'#67b263','pine4':'#8acd78','pine5':'#b4e294',
        'leaflight':'#d7eba7','leafwarm':'#e2edb2',
        'grass0':'#487b4d','grass1':'#6c9d51','grass2':'#7fb15a',
        'grass3':'#9ac36b','grass4':'#b2d581','grasslit':'#b5d37c',
        'grassgold':'#c1d48a',
        'dirt0':'#917758','dirt1':'#bd9c65','dirt2':'#ddc58b',
        'dirt3':'#eeddaa','dirt4':'#f7eac0',
        'stone0':'#506572','stone1':'#6d7e80','stone2':'#99aaa1',
        'stone3':'#bdc8b3','stone4':'#dbe0c4','stone5':'#ecebd0',
        'moss0':'#6d8451','moss1':'#94ab66','moss2':'#bbcd7d',
        'moss3':'#dce4a4',
        'wood1':'#875849','wood2':'#b4794f','wood3':'#d99f65',
        'wood4':'#efd093','barklight':'#e4bd7e','plaster':'#f7dda7',
        'shadow':'#284c42','shadowsoft':'#3d714e',
        'water0':'#24647a','water1':'#388fa4','water2':'#5bb3bc',
        'water3':'#86d4d2','water4':'#b6e8df','watergleam':'#d2eee0',
    },
    'temple':{
        'stone0':'#526873','stone1':'#7e9292','stone2':'#a3b3ae',
        'stone3':'#c4cebe','stone4':'#e0e4d0','stone5':'#eff0d8',
        'night':'#344553','moss0':'#6d8451','moss1':'#94ab66',
        'gold0':'#b78b50','gold1':'#d8aa64','gold2':'#eed080',
        'shadow':'#284c42',
    },
    'twilight':{
        'night':'#3d466c','dusk0':'#655076','dusk1':'#956e8c',
        'dusk2':'#c38ca0','dusk3':'#e8b2ad','dusk4':'#f7d9b6',
        'fog':'#93a7bb','purple1':'#746c96',
        'water0':'#376879','water1':'#418fa1','water2':'#63b1bf',
        'water3':'#91d7d8','water4':'#c1e8df',
        'stone0':'#4e6371','stone1':'#77878e','stone2':'#a0aca9',
        'stone3':'#c1cbb9','stone4':'#dbe0c4',
        'pine1':'#2c684e','pine2':'#38845b','pine3':'#5ba474',
        'pine4':'#84c88b','pine5':'#addc9c','leaflight':'#d3e6af',
    },
}
BACKGROUND_RAMPS={'village':'sunlit','forest':'sunlit','temple':'temple',
                  'boss':'sunlit','title':'twilight'}
for ramp,colors in SCENE_RAMPS.items():
    COLORS.extend((f'bg_{ramp}_{base}',color) for base,color in colors.items())
assert len(COLORS)<=256, 'Scene colors must fit one native GBA palette'
P={n:i for i,(n,c) in enumerate(COLORS)}
rgb=[]
for n,h in COLORS:
    # Use the exact native 5-bit palette in previews to avoid misleading colors.
    rgb.append(tuple((int(h[k:k+2],16)>>3)*255//31 for k in (1,3,5)))
rgb += [(0,0,0)]*(256-len(rgb))
PAL=[x for c in rgb for x in c]
class Art:
    def __init__(self,w=240,h=160,bg='grass1'):
        self.im=Image.new('P',(w,h),P[bg]); self.im.putpalette(PAL); self.d=ImageDraw.Draw(self.im)
    def r(self,box,c): self.d.rectangle(tuple(map(int,box)),fill=P.get(c,c))
    def l(self,pts,c,w=1): self.d.line(pts,fill=P.get(c,c),width=w)
    def p(self,pts,c): self.d.polygon(pts,fill=P.get(c,c))
    def e(self,box,c): self.d.ellipse(tuple(map(int,box)),fill=P.get(c,c))
    def dot(self,x,y,c): self.im.putpixel((int(x),int(y)),P[c]) if 0<=x<self.im.width and 0<=y<self.im.height else None

def color_background(art,scene):
    """Change palette indices only, retaining every original geometry pixel."""
    ramp=BACKGROUND_RAMPS[scene];lookup=list(range(256))
    for base in SCENE_RAMPS[ramp]:lookup[P[base]]=P[f'bg_{ramp}_{base}']
    art.im=art.im.point(lookup)
    art.d=ImageDraw.Draw(art.im)
    return art

def terrain(a,seed=1,base='grass1'):
    R=random.Random(seed)
    a.r((0,0,239,159),base)
    # Quiet floor planes make creatures and interactable silhouettes easy to read.
    # Detail is arranged into islands rather than uniform screen-wide noise.
    for i in range(31):
        x=R.randrange(240);y=R.randrange(24,160);w=R.randrange(7,19)
        a.p([(x-w,y),(x-w+4,y-3),(x+w-3,y-3),(x+w,y),(x+w-4,y+3),(x-w+3,y+2)],'grass1' if base=='grass0' else 'grass2')
    for i in range(160):
        x=R.randrange(240); y=R.randrange(25,160)
        c=R.choice(['grass0','grass2','grass2','grass3'])
        a.r((x,y,x+2,y),c)
        if R.random()<.25: a.dot(x+1,y-1,c)
    for i in range(44):
        x=R.randrange(240);y=R.randrange(25,160)
        a.l([(x-2,y),(x-1,y-2),(x,y),(x+2,y-1)],'grass3')
        a.dot(x-1,y+1,'grass0')

def light_pool(a,x,y,rx=13,ry=8):
    """Palette-only dappled warm light: no alpha buffers and no extra VRAM."""
    remap={P['grass0']:P['grass1'],P['grass1']:P['grass2'],P['grass2']:P['grass3'],P['grass3']:P['grasslit'],P['dirt1']:P['dirt2'],P['dirt2']:P['dirt3'],P['dirt3']:P['dirt4'],P['stone1']:P['stone2'],P['stone2']:P['stone3']}
    for yy in range(max(0,y-ry),min(a.im.height,y+ry+1)):
        for xx in range(max(0,x-rx),min(a.im.width,x+rx+1)):
            d=((xx-x)/rx)**2+((yy-y)/ry)**2
            if d<.7 or (d<1 and (xx+yy)%3==0):
                c=a.im.getpixel((xx,yy))
                if c in remap:a.im.putpixel((xx,yy),remap[c])

def flowers(a,x,y,color='flower0'):
    a.r((x,y,x,y+2),'pine1');a.dot(x-1,y-1,color);a.dot(x+1,y-1,color);a.dot(x,y-2,color);a.dot(x,y,'gold3')

def path(a,boxes,seed=5):
    R=random.Random(seed)
    for x1,y1,x2,y2 in boxes:
        a.r((x1-2,y1,x2+2,y2),'grass0');a.r((x1,y1,x2,y2),'dirt1');a.r((x1+2,y1,x2-2,y2),'dirt2')
        for y in range(y1+3,y2-1,9):
            xx=R.randrange(x1+2,max(x1+3,x2-2));a.r((xx,y,xx+3,y),'dirt3')
        for y in range(y1,y2,6):
            a.dot(x1-1,y,'dirt2');a.dot(x2+1,y+3,'dirt2')

def stone(a,x,y,w=12,h=7):
    a.p([(x+2,y),(x+w-3,y),(x+w,y+2),(x+w-1,y+h-1),(x+2,y+h),(x,y+h-2),(x,y+2)],'stone0')
    a.p([(x+2,y+1),(x+w-3,y+1),(x+w-1,y+3),(x+w-2,y+h-2),(x+2,y+h-1),(x+1,y+3)],'stone2')
    a.l([(x+3,y+1),(x+w-4,y+1),(x+w-2,y+2)],'stone4')
    a.r((x+3,y+h-2,x+w-3,y+h-2),'stone1')

def leaf_cluster(a,x,y,r=9,lit=False,s=1):
    # Interlocking scallops describe volumes; tiny veins follow each leaf surface.
    def poly(points,c): a.p([(x+dx*s,y+dy*s) for dx,dy in points],c)
    poly([(-r,-2),(-r+1,-6),(-r+4,-7),(-r+5,-r),(0,-r-1),(3,-r+2),(r-2,-r+3),(r, -3),(r-1,2),(r-4,4),(r-5,7),(0,8),(-4,6),(-r+2,5)],'pine0')
    poly([(-r+1,-3),(-r+2,-6),(-r+4,-6),(-r+5,-r+1),(0,-r),(3,-r+3),(r-2,-r+2),(r-1,-3),(r-2,1),(r-5,3),(r-6,5),(-1,6),(-4,4),(-r+2,4)],'pine2')
    poly([(-r+2,-4),(-r+4,-6),(-r+5,-r+2),(0,-r+1),(3,-r+4),(r-3,-r+3),(r-1,-4),(r-4,-1),(-1,0),(-4,3),(-r+3,1)],'pine3')
    poly([(-r+3,-5),(-r+5,-r+2),(0,-r+1),(3,-r+4),(1,-4),(-2,-4),(-4,-1),(-r+3,-2)],'pine4')
    if lit:
        poly([(-r+3,-5),(-r+5,-r+2),(0,-r+1),(2,-r+4),(-2,-r+4),(-4,-3),(-r+3,-3)],'pine5')
        a.l([(x+(-r+5)*s,y+(-r+2)*s),(x-1*s,y+(-r+2)*s)],'leaflight')
    for dx,dy in [(-5,-3),(1,-2),(-3,3),(4,2)]:
        a.l([(x+dx*s,y+dy*s),(x+(dx+2)*s,y+(dy-1)*s),(x+(dx+3)*s,y+dy*s)],'pine4' if dy<0 else 'pine1')
    a.dot(x-3*s,y-5*s,'leaflight' if lit else 'pine5')

def tree(a,x,y,s=1,seed=0):
    # Footprint and collision geometry are unchanged from the original route.
    a.e((x-13*s,y-3*s,x+13*s,y+3*s),'shadowsoft')
    a.e((x-8*s,y-2*s,x+8*s,y+2*s),'shadow')
    a.p([(x-4*s,y),(x-3*s,y-13*s),(x-7*s,y-19*s),(x-3*s,y-16*s),(x+1*s,y-18*s),(x+3*s,y-12*s),(x+3*s,y-2*s),(x+6*s,y+1*s)],'wood0')
    a.p([(x-2*s,y-1*s),(x-1*s,y-12*s),(x-4*s,y-16*s),(x+1*s,y-13*s),(x+2*s,y-2*s),(x+4*s,y)],'wood2')
    a.l([(x-1*s,y-2*s),(x,y-8*s),(x-1*s,y-12*s)],'wood3')
    a.l([(x+2*s,y-7*s),(x+1*s,y-4*s),(x+2*s,y-2*s)],'wood1')
    a.l([(x-6*s,y+1*s),(x-3*s,y-2*s),(x-3*s,y-5*s)],'wood1')
    a.dot(x,y-5*s,'barklight');a.dot(x+3*s,y,'wood3')
    # Lower shadow lobes, then staggered illuminated masses, like a layered canopy.
    leaf_cluster(a,x-6*s,y-18*s,9,False,s)
    leaf_cluster(a,x+6*s,y-20*s,9,False,s)
    leaf_cluster(a,x-5*s,y-27*s,10,True,s)
    leaf_cluster(a,x+6*s,y-28*s,9,False,s)
    leaf_cluster(a,x-1*s,y-33*s,8,True,s)
    leaf_cluster(a,x,y-20*s,8,False,s)
    # A few leaves on the ground visually tie the canopy to its cast shadow.
    a.r((x-9*s,y,x-7*s,y),'pine2');a.dot(x+8*s,y+1*s,'pine3')

def bush(a,x,y,w=16):
    a.e((x-w//2,y-3,x+w//2,y+3),'shadow')
    leaf_cluster(a,x-w//5,y-6,6,True,.8)
    leaf_cluster(a,x+w//5,y-5,6,False,.8)
    a.l([(x-3,y-2),(x,y-3),(x+3,y-2)],'pine1')

def house(a,x,y,w=61,h=48):
    # The roof eaves are a hand-stepped silhouette over golden plaster.
    a.e((x-4,y+h-8,x+w+5,y+h+5),'shadow')
    a.r((x+5,y+17,x+w-5,y+h),'ink');a.r((x+7,y+18,x+w-7,y+h-2),'wood3')
    a.r((x+8,y+24,x+w-8,y+h-6),'wood4');a.r((x+9,y+26,x+w-10,y+h-8),'plaster');a.r((x+7,y+27,x+w-7,y+30),'wood2')
    for yy in range(y+34,y+h-4,7):
        for xx in (x+9,x+w-15):a.r((xx,yy,xx+4,yy),'wood3')
    for xx in (x+8,x+w-10): a.r((xx,y+20,xx+2,y+h-3),'wood1');a.r((xx+1,y+21,xx+1,y+h-4),'wood2')
    a.p([(x-3,y+23),(x+10,y+2),(x+w-11,y+2),(x+w+3,y+23),(x+w+3,y+27),(x-3,y+27)],'ink')
    a.p([(x-1,y+22),(x+11,y+4),(x+w-12,y+4),(x+w+1,y+22)],'rose1')
    # Five irregular overlapping rows of copper-rose shingles.
    for j in range(5):
        yy=y+5+j*4;left=x+10-j*2;right=x+w-11+j*2
        a.r((left,yy,right,yy+2),'rose3' if j<2 else 'rose2')
        a.l([(left,yy),(right,yy)],'rose4' if j<2 else 'rose3')
        for xx in range(left+(j%2)*5,right,10): a.l([(xx,yy+1),(xx-1,yy+3)],'rose1')
    a.r((x-1,y+23,x+w+1,y+24),'rose0');a.r((x,y+25,x+w,y+25),'wood4');a.r((x+3,y+26,x+w-3,y+27),'wood0');a.dot(x,y+23,'roofshine')
    a.r((x+12,y+1,x+w-13,y+2),'rose5');a.l([(x+2,y+21),(x+12,y+5)],'roofshine')
    # Tiny arched attic inset and raised copper ridge reinforce the roof plane.
    cx=x+w//2;a.e((cx-5,y+9,cx+5,y+17),'rose0');a.e((cx-3,y+10,cx+3,y+16),'gold1');a.r((cx-2,y+11,cx+2,y+15),'water0');a.l([(cx-2,y+11),(cx+1,y+11)],'water3');a.r((cx,y+11,cx,y+15),'wood2');a.r((cx-4,y+17,cx+4,y+18),'rose4')
    # Stone chimney, no smoke obstruction in the top walkway.
    a.r((x+w-18,y-3,x+w-11,y+7),'stone0');a.r((x+w-17,y-2,x+w-12,y+5),'stone2');a.r((x+w-19,y-4,x+w-10,y-2),'stone1');a.l([(x+w-18,y-4),(x+w-11,y-4)],'stone4')
    # Door and 2 warm little windows.
    door=x+w//2-5
    a.r((door-1,y+h-19,door+10,y+h-1),'wood0');a.r((door+1,y+h-18,door+8,y+h-2),'wood2')
    a.l([(door+3,y+h-17),(door+3,y+h-3)],'wood3');a.dot(door+7,y+h-10,'gold3')
    for wx in (x+14,x+w-22):
        a.r((wx-1,y+29,wx+8,y+38),'wood0');a.r((wx,y+30,wx+7,y+36),'water0');a.r((wx+1,y+30,wx+6,y+32),'gold2');a.dot(wx+1,y+34,'gold4');a.l([(wx+3,y+30),(wx+3,y+36)],'wood2');a.r((wx-2,y+38,wx+9,y+39),'wood5')
    a.r((door-3,y+h,door+12,y+h+2),'stone2');a.l([(door-2,y+h),(door+11,y+h)],'stone4')

def fence(a,x,y,w):
    a.r((x,y+3,x+w,y+4),'wood0');a.r((x,y+7,x+w,y+8),'wood1')
    for xx in range(x,x+w,9): a.r((xx,y,xx+2,y+12),'wood1');a.r((xx,y,xx+1,y+9),'wood4');a.dot(xx,y-1,'wood5')

def shrine(a,x,y):
    a.e((x-14,y+5,x+14,y+11),'shadow')
    a.r((x-13,y+2,x+13,y+8),'stone0');a.r((x-11,y+2,x+11,y+6),'stone2');a.l([(x-10,y+2),(x+10,y+2)],'stone4')
    a.p([(x-8,y+1),(x-7,y-19),(x,y-26),(x+7,y-19),(x+8,y+1)],'ink')
    a.p([(x-6,y),(x-5,y-18),(x,y-22),(x+5,y-18),(x+6,y)],'stone2')
    a.l([(x-4,y-17),(x,y-21),(x+3,y-18)],'stone4')
    a.p([(x,y-16),(x+4,y-10),(x,y-5),(x-4,y-10)],'gold0');a.p([(x,y-15),(x+2,y-10),(x,y-7),(x-2,y-10)],'gold3');a.dot(x,y-11,'gold4')
    a.r((x-4,y-3,x+4,y-2),'stone1')

def lamp(a,x,y,lit=True):
    if lit:light_pool(a,x,y+1,13,7)
    a.e((x-7,y+4,x+7,y+7),'shadow');a.r((x-4,y+1,x+4,y+5),'stone0');a.r((x-2,y-5,x+2,y+2),'stone2');a.l([(x-1,y-4),(x-1,y+1)],'stone4')
    a.p([(x-6,y-9),(x+6,y-9),(x+4,y-4),(x-4,y-4)],'wood0');a.r((x-4,y-9,x+4,y-7),'gold1')
    if lit:
        a.p([(x-3,y-8),(x-5,y-12),(x-2,y-17),(x-1,y-13),(x+2,y-20),(x+4,y-13),(x+3,y-8)],'fire1')
        a.p([(x-2,y-8),(x-2,y-12),(x+1,y-16),(x+2,y-11),(x+1,y-8)],'gold3');a.dot(x,y-10,'white')
    else: a.r((x-3,y-9,x+3,y-8),'night')

def village():
    a=Art();terrain(a,8)
    for x,y,rx,ry in [(78,112,29,12),(176,124,30,10),(120,62,22,13)]:light_pool(a,x,y,rx,ry)
    path(a,[(105,20,135,159),(40,106,200,128)],9)
    roads.draw(a,0,P)
    # Dappled stone lane detail.
    for x,y in [(112,35),(122,53),(112,75),(120,97),(116,130),(118,147),(76,111),(162,119)]: stone(a,x,y,9,5)
    for x,y,s in [(7,40,1.1),(34,32,.9),(61,31,1.0),(88,29,.85),(152,29,.85),(181,31,1.1),(213,34,1),(241,42,1.1)]: tree(a,x,y,s,2)
    house(a,25,47,61,47);house(a,154,50,61,45)
    # The maproom is inside the east house: a dark open doorway and stone sill.
    a.r((180,78,188,94),'wood0');a.r((182,80,186,94),'deep')
    a.l([(178,95),(190,95)],'stone4');a.l([(177,97),(191,97)],'stone2')
    # The hamlet's gathering altar sits off the traversable center lane.
    shrine(a,53,141);a.r((40,148,66,150),'stone1');a.r((42,147,64,148),'stone3')
    fence(a,163,140,46)
    for x,y in [(23,102),(91,96),(148,98),(218,103),(16,145),(83,143),(229,146),(153,149)]: bush(a,x,y)
    for x,y in [(30,108),(31,136),(72,136),(84,130),(150,135),(205,132),(212,111),(25,119),(191,149)]: flowers(a,x,y)
    for x,y in [(99,91),(143,91)]: lamp(a,x,y)
    # Welcome banner across the road has posts well clear of the center.
    a.r((98,27,100,49),'wood0');a.r((140,27,142,49),'wood0');a.l([(99,28),(120,32),(141,28)],'wood4')
    for x in (104,112,120,128,136): a.p([(x-2,30),(x+2,31),(x,35)],'rose3' if x%16 else 'gold2')
    return a

def forest():
    a=Art();terrain(a,26,'grass0')
    # Mossy forest clearing, unobstructed central path and north/south exits.
    a.e((24,25,214,158),'grass1')
    for x,y,rx,ry in [(80,63,30,13),(157,121,37,18),(122,137,26,11)]:light_pool(a,x,y,rx,ry)
    path(a,[(107,24,133,159),(55,100,180,114)],19)
    for x,y in [(111,36),(121,61),(114,83),(126,110),(112,132),(119,149)]: stone(a,x,y,9,5)
    # The river is a real traversal puzzle: the center stays water until Leaf builds it.
    a.p([(0,75),(39,74),(79,76),(119,75),(160,76),(200,74),(239,76),(239,95),(198,94),(159,95),(119,94),(78,95),(39,93),(0,95)],'shadow')
    a.p([(0,77),(39,76),(79,78),(119,77),(160,78),(200,76),(239,78),(239,93),(198,92),(159,93),(119,92),(78,93),(39,91),(0,93)],'stone1')
    a.r((0,78,239,90),'water0');a.r((0,80,239,89),'water1')
    for x in range(-6,240,23):
        a.r((x,81,x+11,81),'water2');a.r((x+9,86,x+17,86),'water3');a.dot(x+7,87,'water2');a.r((x+4,80,x+7,80),'water4');a.r((x+11,88,x+15,88),'water2')
    a.r((108,76,131,77),'stone3');a.r((108,92,131,93),'stone2')
    a.r((110,76,129,76),'stone4');a.r((110,92,129,92),'stone4')
    # Undercut banks and grouped reeds create a shallow, sunlit water plane.
    for xx in (42,70,158,178):
        a.l([(xx,77),(xx-1,73),(xx+1,76),(xx+3,72)],'pine4');a.dot(xx+3,71,'leaflight')
    # A sliver of stream on the east boundary.
    a.p([(219,21),(229,34),(221,59),(231,83),(222,105),(230,126),(222,160),(240,160),(240,21)],'stone0')
    a.p([(223,20),(233,35),(225,58),(235,82),(226,104),(234,126),(226,160),(240,160),(240,20)],'water1')
    for y in range(33,160,16): a.l([(231,y),(237,y)],'water3');a.l([(228,y+7),(232,y+7)],'water2')
    for x,y,s in [(5,44,1.3),(31,43,1.15),(61,33,1.2),(90,27,.9),(151,25,1),(181,36,1.2),(212,43,1.1),(18,85,1.2),(48,74,1),(199,79,1),(9,135,1.3),(46,144,1.1),(200,144,1.1),(235,145,1.2),(27,174,1.1),(75,176,1.1),(169,174,1.1),(217,177,1.2)]: tree(a,x,y,s,6)
    # Low ruined arch entrance to the temple, centered opening 106..134.
    for x in (92,138):
        a.r((x,19,x+10,42),'stone0');a.r((x+1,19,x+9,40),'stone2')
        for yy in (22,29,36): a.l([(x+1,yy),(x+9,yy)],'stone1')
        a.l([(x+2,20),(x+2,39)],'stone4');a.r((x-2,17,x+12,20),'stone1');a.l([(x-1,17),(x+11,17)],'stone3')
    a.p([(94,16),(101,10),(138,10),(146,16),(146,21),(94,21)],'stone0');a.r((101,12,138,18),'stone2');a.l([(102,12),(137,12)],'stone4');a.p([(120,12),(123,15),(120,18),(117,15)],'gold2')
    for x,y in [(77,52),(164,54),(66,129),(179,127)]: bush(a,x,y,18)
    for x,y in [(85,73),(157,78),(77,114),(163,115),(91,140),(150,143),(65,95),(180,97)]: flowers(a,x,y,'blue3')
    for x,y in [(90,47),(150,47)]: lamp(a,x,y)
    # Fallen silverwood branch on side, deliberately clear of corridor.
    a.r((48,116,73,120),'wood0');a.r((50,116,72,118),'wood3');a.r((52,117,65,117),'wood4');a.dot(69,116,'wood1')
    return a

def masonry(a,box):
    x1,y1,x2,y2=box;a.r(box,'stone0')
    for row,y in enumerate(range(y1,y2,9)):
        for x in range(x1-16*(row%2),x2,32):
            xx=max(x1,x);xe=min(x2,x+30)
            if xx<=xe:
                a.r((xx,y,xe,min(y+7,y2)),'stone1');a.l([(xx+1,y),(xe,y)],'stone3');a.l([(xx+1,y+1),(xx+1,min(y+6,y2))],'stone2')

def temple():
    a=Art(bg='stone1')
    # Staggered worn flagstone floor.
    R=random.Random(49)
    for yy in range(16,160,16):
        for xx in range(-12 if (yy//16)%2 else 0,240,24):
            a.r((xx,yy,xx+22,yy+14),R.choice(['stone1','stone1','stone2']))
            a.l([(xx+1,yy+1),(xx+21,yy+1)],'stone2');a.r((xx+3,yy+12,xx+18,yy+13),'stone1')
            if R.random()<.3: a.l([(xx+15,yy+2),(xx+12,yy+5),(xx+15,yy+7)],'stone0')
    masonry(a,(0,0,102,30));masonry(a,(138,0,239,30));masonry(a,(0,31,19,159));masonry(a,(221,31,239,159))
    a.r((20,31,23,159),'night');a.r((216,31,220,159),'night')
    a.r((25,32,27,156),'gold0');a.r((212,32,214,156),'gold0');a.r((28,32,29,156),'stone3');a.r((214,32,215,156),'stone0')
    # Central ceremonial carpet is tile inlay, not a blocked prop.
    a.r((104,31,136,159),'stone0');a.r((106,31,134,159),'stone2');a.l([(108,31),(108,159)],'gold0');a.l([(132,31),(132,159)],'gold0')
    for y in range(41,151,21): a.p([(120,y-3),(124,y),(120,y+3),(116,y)],'stone4');a.dot(120,y,'gold2')
    # Large ritual disc, centered below braziers.
    a.e((82,80,158,140),'night');a.e((83,77,157,137),'stone0');a.e((85,78,155,134),'stone2');a.e((88,81,152,131),'gold0');a.e((90,83,150,129),'stone1')
    a.p([(120,87),(127,103),(143,106),(129,113),(120,127),(111,113),(97,106),(113,103)],'stone2')
    a.l([(92,91),(97,85),(113,81)],'stone4');a.l([(141,123),(130,129),(114,131)],'stone0');a.p([(120,98),(128,106),(120,115),(112,106)],'stone3');a.p([(120,102),(124,106),(120,110),(116,106)],'gold2')
    for x,y in [(40,43),(195,43),(41,136),(196,136)]:
        a.r((x-5,y-5,x+5,y+7),'stone0');a.r((x-4,y-6,x+4,y+5),'stone2');a.r((x-6,y-7,x+6,y-5),'stone3');a.l([(x-5,y-7),(x+5,y-7)],'stone5');a.r((x-1,y-4,x+1,y+4),'stone1')
    # Braziers at the requested centers, unlit so game logic can light them.
    for x in (64,176):
        a.e((x-14,57,x+14,73),'stone0');a.e((x-12,56,x+12,69),'stone3');a.e((x-10,58,x+10,68),'stone1');lamp(a,x,64,False)
    # North gate shows a portcullis; engine overlays its open state.
    a.r((103,12,137,29),'night');a.r((102,10,105,31),'stone4');a.r((135,10,138,31),'stone4');a.r((102,10,138,13),'stone3')
    for x in range(109,135,6): a.r((x,15,x+1,29),'gold1');a.dot(x,15,'gold3')
    a.r((106,21,134,22),'gold0')
    for x,y in [(33,75),(208,114),(34,153),(202,33)]:
        a.r((x,y,x+6,y+2),'moss0');a.r((x+2,y-1,x+4,y),'moss1')
    return a

def boss():
    a=Art();terrain(a,73,'grass0')
    # Wide, sacred circle leaves center x40..200/y40..140 obstacle-free.
    a.e((37,26,203,154),'shadow');a.e((39,27,201,151),'stone0');a.e((42,30,198,148),'stone2');a.e((46,33,194,145),'moss0');a.e((52,37,188,142),'grass0');a.e((60,43,180,137),'grass1')
    for theta in range(0,360,30):
        t=math.radians(theta);x=120+76*math.cos(t);y=89+56*math.sin(t)
        a.l([(int(x-4*math.cos(t)),int(y-3*math.sin(t))),(int(x+4*math.cos(t)),int(y+3*math.sin(t)))],'stone0',2)
        a.r((x-2,y-1,x+2,y),'stone4')
    # Sparse broken tesserae and moss sit inside the old ring, never on the route.
    for xx,yy in [(70,58),(166,60),(62,96),(176,89),(87,128),(151,128)]:
        a.l([(xx-3,yy),(xx,yy-2),(xx+3,yy-1)],'grass2');a.dot(xx-3,yy+1,'grass0')
    # Compass sigil worn into floor.
    a.e((97,72,143,112),'grass0');a.e((100,74,140,110),'grass1')
    a.p([(120,66),(125,84),(145,92),(125,97),(120,117),(115,97),(95,92),(115,84)],'grass2');a.p([(120,78),(129,92),(120,102),(111,92)],'grass0');a.p([(120,86),(125,92),(120,98),(115,92)],'gold0')
    for x,y,s in [(3,47,1.3),(32,30,1.2),(67,17,1.2),(105,9,1),(137,10,1),(176,18,1.2),(211,31,1.2),(238,52,1.3),(2,103,1.2),(237,102,1.2),(5,161,1.2),(35,191,1.2),(73,199,1.2),(167,199,1.2),(207,193,1.2),(239,160,1.2)]:tree(a,x,y,s,4)
    # Four edge guardian markers outside the open fight area.
    for x,y in [(24,72),(216,72),(24,131),(216,131)]: shrine(a,x,y)
    for x,y in [(47,66),(193,113),(68,143),(172,45),(79,36),(156,142),(43,112),(190,63)]:flowers(a,x,y,'flower1')
    path(a,[(108,145,132,159)],3)
    return a

def title():
    a=Art(bg='dusk0')
    for y,c in [(0,'night'),(21,'dusk0'),(45,'dusk1'),(65,'dusk2'),(79,'dusk3'),(97,'dusk4')]: a.r((0,y,239,159),c)
    # Stars and the amber rising moon.
    for x,y in [(17,17),(44,32),(83,16),(158,13),(213,29),(227,13),(190,39),(109,28)]:a.dot(x,y,'gold4')
    a.e((174,25,202,53),'dusk3');a.e((177,27,199,49),'sun');a.r((175,46,203,49),'dusk2')
    a.p([(0,81),(17,61),(35,68),(65,40),(94,75),(120,54),(157,89),(178,68),(211,78),(239,52),(239,115),(0,115)],'purple1')
    a.p([(36,73),(65,40),(89,71),(74,60),(68,61),(63,52),(56,65),(53,62)],'fog')
    a.p([(0,101),(26,89),(47,100),(75,78),(103,102),(126,87),(162,105),(184,81),(215,99),(239,84),(239,124),(0,124)],'water0')
    a.r((0,113,239,159),'water1')
    for y in range(115,158,4):
        for x in range((y%3)*9,240,37):a.r((x,y,x+12+(y%7),y),'water2')
    for x,y,w in [(160,116,35),(169,120,21),(172,126,16),(179,131,9),(164,115,25)]:a.r((x,y,x+w,y),'dusk3')
    # Far ruin with waterfall.
    a.p([(156,107),(161,86),(166,81),(188,82),(195,107)],'stone0');a.r((166,67,171,92),'stone1');a.r((183,68,188,91),'stone1');a.p([(164,69),(174,61),(181,61),(190,69)],'stone2');a.r((170,69,184,72),'stone3');a.r((173,72,181,92),'night')
    a.p([(165,107),(167,101),(173,102),(173,119),(169,123),(164,121)],'water3');a.l([(169,106),(169,119)],'water4')
    # Foreground hero lookout cliff, fern silhouettes, firelit shrine.
    a.p([(0,117),(31,114),(42,119),(62,114),(75,122),(105,121),(120,132),(127,160),(0,160)],'ink')
    a.p([(0,114),(31,110),(42,114),(61,110),(74,118),(103,117),(118,129),(125,134),(0,138)],'pine1')
    a.l([(0,114),(31,110),(42,114),(61,110),(74,118),(103,117),(118,129)],'pine3',2)
    a.r((24,139,86,142),'stone0');a.l([(28,137),(92,137)],'stone1')
    shrine(a,30,116);tree(a,5,137,1.6,12)
    for x in (3,20,94,109,118,230):
        a.l([(x,159),(x-2,145),(x+1,150),(x+5,144)],'pine0',2)
    a.p([(204,160),(207,144),(214,138),(220,143),(225,131),(232,127),(240,134),(240,160)],'pine0')
    return a

SPR_NAMES=['HERO_DOWN_0','HERO_DOWN_1','HERO_UP_0','HERO_UP_1','HERO_LEFT_0','HERO_LEFT_1','HERO_RIGHT_0','HERO_RIGHT_1','FOX_0','FOX_1','LEAF_0','LEAF_1','SLIME_0','SLIME_1','ELDER','HEART_FULL','HEART_EMPTY','FLAME_0','FLAME_1','PROJECTILE']

def hero(direction,frame):
    """Four authored walk poses. 0 is the stable idle/passing silhouette."""
    a=Art(16,16,'transparent');b=-1 if frame==2 else 0
    # These opposite contacts and the raised passing frame eliminate paper sliding.
    leftfoot=(4,13,6,15);rightfoot=(9,13,11,15)
    if frame==1:leftfoot=(3,13,6,15);rightfoot=(9,12,11,13)
    if frame==3:leftfoot=(4,12,6,13);rightfoot=(9,13,12,15)
    if frame==2:leftfoot=(5,13,7,14);rightfoot=(9,13,11,14)
    for x0,y0,x1,y1 in (leftfoot,rightfoot):
        a.r((x0,y0,x1,y1),'ink');a.r((x0+1,y0,x1,y0),'wood2');a.dot(x0+1,y1-1,'wood3')
    # Golden scarf is physically trailing instead of attached to the front face.
    sy=9+b+(1 if frame==3 else 0)
    if direction in ('right','left'):
        a.p([(7,8+b),(4,sy-1),(1,sy-2),(1,sy),(4,sy+1),(7,10+b)],'gold0')
        a.l([(2,sy-1),(4,sy),(6,9+b)],'gold3')
    else:
        a.p([(10,8+b),(12,sy),(14,sy-1),(14,sy+1),(11,sy+2),(9,9+b)],'gold0')
        a.l([(11,sy),(13,sy+1),(14,sy)],'gold3')
    # Coat, leather belt, satchel strap, and opposed arm swing.
    a.p([(5,8+b),(10,8+b),(12,10+b),(11,13+b),(4,13+b),(3,10+b)],'ink')
    a.r((4,9+b,11,11+b),'teal0');a.r((5,9+b,10,12+b),'teal1');a.l([(5,10+b),(5,11+b)],'teal2');a.r((4,12+b,11,12+b),'blue0')
    arm=1 if frame==1 else -1 if frame==3 else 0
    a.r((3,9+b+arm,3,11+b+arm),'ink');a.dot(3,10+b+arm,'skin1')
    a.r((12,9+b-arm,12,11+b-arm),'ink');a.dot(12,10+b-arm,'skin2')
    a.l([(9,9+b),(7,11+b)],'wood0');a.dot(8,10+b,'wood4');a.r((8,12+b,9,12+b),'gold2')
    if direction=='up':
        a.p([(3,4+b),(4,2+b),(6,1+b),(10,1+b),(12,3+b),(12,7+b),(10,9+b),(5,9+b),(3,7+b)],'ink')
        a.p([(4,4+b),(5,2+b),(10,2+b),(11,4+b),(11,7+b),(9,8+b),(5,7+b)],'fire0')
        a.p([(4,4+b),(6,2+b),(10,2+b),(11,4+b),(9,3+b),(8,5+b),(6,4+b),(5,6+b)],'fire1')
        a.l([(6,2+b),(9,2+b)],'fire3');a.dot(5,3+b,'fire2');a.r((5,8+b,10,9+b),'gold2');a.dot(5,8+b,'gold4')
        # Small clasp, rather than accidental rear-facing eyes.
        a.r((6,10+b,9,11+b),'teal0');a.dot(7,10+b,'teal2')
    elif direction=='down':
        a.p([(3,4+b),(4,2+b),(6,1+b),(10,1+b),(12,3+b),(12,7+b),(10,9+b),(5,9+b),(3,7+b)],'ink')
        a.r((4,4+b,11,7+b),'skin1');a.r((5,4+b,10,8+b),'skin2')
        a.p([(3,4+b),(5,1+b),(10,1+b),(12,3+b),(12,5+b),(10,4+b),(9,3+b),(7,4+b),(5,4+b),(4,6+b),(3,6+b)],'fire0')
        a.p([(4,3+b),(6,2+b),(10,2+b),(11,3+b),(8,3+b),(7,4+b),(5,4+b)],'fire2');a.r((5,2+b,8,2+b),'fire3')
        a.dot(5,6+b,'ink');a.dot(10,6+b,'ink');a.dot(7,8+b,'skin0');a.dot(4,7+b,'skin0')
        a.r((5,9+b,10,9+b),'gold2');a.dot(5,9+b,'gold4')
    else:
        # True profile: one eye, protruding nose, back hair, near-side arm.
        a.p([(3,4+b),(5,1+b),(9,1+b),(11,2+b),(12,4+b),(12,5+b),(13,6+b),(13,7+b),(11,8+b),(10,9+b),(5,9+b),(3,7+b)],'ink')
        a.p([(8,4+b),(11,4+b),(11,6+b),(12,6+b),(12,7+b),(11,7+b),(10,8+b),(7,8+b)],'skin2')
        a.p([(3,4+b),(5,1+b),(9,1+b),(11,2+b),(12,4+b),(10,4+b),(9,3+b),(8,5+b),(7,6+b),(8,8+b),(5,8+b),(3,6+b)],'fire0')
        a.p([(4,3+b),(6,2+b),(9,2+b),(10,3+b),(7,3+b),(6,5+b),(4,5+b)],'fire2')
        a.r((6,2+b,8,2+b),'fire3');a.dot(11,5+b,'ink');a.dot(10,8+b,'skin0');a.dot(7,6+b,'skin1')
        a.r((6,9+b,10,9+b),'gold2');a.dot(9,9+b,'gold4')
        a.r((8+arm,10+b,10+arm,12+b),'teal0');a.dot(10+arm,12+b,'skin2')
        if direction=='left':a.im=a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return a

def fox_direction(direction,frame):
    a=Art(16,16,'transparent');b=-1 if frame==2 else 0;t=(0,1,0,-1)[frame]
    if direction in ('left','right'):
        # Side gait has a clear forward muzzle and separately moving tipped tail.
        a.p([(5,9+b),(3,8+b),(2,5+t),(0,4+t),(0,10+t),(3,12+b),(6,12+b)],'ink')
        a.p([(4,9+b),(2,8+b),(1,6+t),(1,10+b),(4,11+b)],'fire2');a.r((0,4+t,1,6+t),'white')
        a.r((4,10+b,10,13+b),'ink');a.r((4,10+b,9,12+b),'fire1');a.r((5,9+b,10,11+b),'fire2')
        for x,y in ((5-(frame==1),13+(frame==3)),(9+(frame==1),13+(frame==1))):
            a.r((x,y-1,x+1,min(15,y+1)),'ink');a.dot(x,y,'fire2')
        a.p([(7,7+b),(7,1+b),(9,2+b),(10,4+b),(12,2+b),(13,3+b),(13,6+b),(15,7+b),(15,9+b),(12,11+b),(9,11+b),(7,9+b)],'ink')
        a.p([(8,7+b),(8,3+b),(10,5+b),(12,4+b),(12,7+b),(14,8+b),(12,10+b),(9,10+b)],'fire2')
        a.dot(8,3+b,'rose2');a.r((10,6+b,12,7+b),'fire3');a.dot(12,7+b,'ink');a.dot(15,8+b,'ink');a.l([(11,9+b),(13,9+b)],'white');a.dot(10,10+b,'white')
        if direction=='left':a.im=a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    else:
        a.p([(9,11),(12,10+t),(14,6+t),(15,7+t),(15,12),(12,14),(8,13)],'ink');a.p([(10,11),(13,11),(14,8+t),(14,12),(11,13)],'fire2');a.r((14,7+t,15,9+t),'white')
        a.r((3,12,5,14+(frame==1)),'ink');a.r((8,12,10,14+(frame==3)),'ink');a.dot(4,13,'fire2');a.dot(9,13,'fire2')
        a.r((4,9+b,10,12+b),'fire0');a.r((5,9+b,9,12+b),'fire2')
        a.p([(2,7+b),(2,1+b),(4,2+b),(6,5+b),(8,5+b),(10,1+b),(12,1+b),(12,7+b),(11,10+b),(8,12+b),(4,11+b),(2,9+b)],'ink')
        a.p([(3,6+b),(3,2+b),(5,5+b),(9,5+b),(11,2+b),(11,7+b),(10,9+b),(8,11+b),(4,10+b),(3,9+b)],'fire2')
        a.r((4,5+b,10,7+b),'fire3');a.dot(3,3+b,'rose2');a.dot(11,3+b,'rose2')
        if direction=='down':
            a.dot(4,7+b,'ink');a.dot(10,7+b,'ink');a.p([(4,9+b),(6,8+b),(8,9+b),(10,8+b),(9,10+b),(7,11+b),(5,10+b)],'white');a.dot(7,9+b,'ink')
        else:
            a.p([(4,8+b),(7,6+b),(10,8+b),(8,11+b),(5,10+b)],'fire1');a.r((6,7+b,8,8+b),'fire2')
    return a

def fox(frame):return fox_direction('down',frame)

def leaf_direction(direction,frame):
    a=Art(16,16,'transparent');b=(0,-1,0,1)[frame];t=(0,1,0,-1)[frame]
    a.p([(6,5+b),(3,4+b),(2,2+b),(5,2+b),(7,4+b),(10,1+b),(13,1+b),(12,4+b),(10,6+b)],'ink')
    a.p([(6,4+b),(3,3+b),(4,2+b),(7,5+b),(10,2+b),(12,2+b),(10,4+b),(9,5+b)],'teal2');a.dot(10,2+b,'white')
    if frame==2:
        a.dot(2,2+b,'transparent');a.dot(3,2+b,'teal2');a.dot(12,1+b,'transparent');a.dot(13,2+b,'teal2')
    a.e((2,5+b,13,13+b),'ink');a.e((3,6+b,12,12+b),'blue1');a.e((4,6+b,11,10+b),'blue2');a.r((5,6+b,9,7+b),'blue3')
    a.l([(1,10+b),(2,9+b-(frame==2)),(3,10+b)],'teal2');a.l([(12,10+b),(13,9+b+t),(14,10+b+t)],'teal2')
    if direction=='down':
        a.dot(5,9+b,'ink');a.dot(10,9+b,'ink');a.dot(7,11+b,'white');a.dot(4,10+b,'teal2')
    elif direction=='up':
        a.r((6,8+b,9,8+b),'blue1');a.l([(5,9+b),(7,11+b),(10,9+b)],'blue1')
    else:
        a.dot(10,9+b,'ink');a.dot(12,10+b,'white');a.dot(5,10+b,'teal2')
        if direction=='left':a.im=a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    a.r((4,13+b,5,13+b),'teal0');a.r((9,13+b,11,13+b),'teal0')
    return a

def leaf(frame):return leaf_direction('down',frame)

def shadow_sprite(w=16,h=16):
    a=Art(w,h,'transparent')
    if w==16:
        a.e((2,11,13,15),'shadowsoft');a.e((4,12,11,14),'shadow')
    else:
        a.e((2,3,29,12),'shadowsoft');a.e((6,5,25,10),'shadow')
    return a

def foreground_canopy(room,side):
    a=Art(32,32,'transparent')
    # Thin edge-only, raised foreground boughs, never over the central route.
    a.l([(-3,31),(3,20),(5,8),(8,0)],'wood0',3)
    leaf_cluster(a,1,8,10,False,1.2);leaf_cluster(a,9,17,9,True,1.15)
    leaf_cluster(a,-3,29,10,False,1.15);leaf_cluster(a,6,30,7,False,1)
    if room==3:
        a.dot(12,12,'flower1');a.dot(13,13,'flower0');a.dot(11,13,'flower0')
    if side:a.im=a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    return a

def slime(frame):
    a=Art(16,16,'transparent');top=4+frame
    a.e((1,top,14,14),'ink');a.e((2,top+1,13,13),'purple1');a.e((3,top+1,12,11),'purple2');a.e((4,top+1,8,top+3),'purple3')
    a.r((4,9,5,10),'ink');a.r((10,9,11,10),'ink');a.dot(5,9,'white');a.dot(11,9,'white');a.r((7,12,8,12),'rose0')
    return a

def elder():
    a=Art(16,16,'transparent')
    a.r((11,4,12,15),'wood0');a.r((11,4,11,14),'wood4');a.p([(5,8),(9,8),(12,14),(3,14)],'ink');a.p([(5,9),(9,9),(10,13),(4,13)],'purple2');a.r((7,10,8,13),'gold2')
    a.e((2,1,12,10),'ink');a.e((3,2,11,9),'silver');a.r((4,4,10,7),'skin1');a.r((5,4,9,7),'skin2');a.dot(5,5,'ink');a.dot(9,5,'ink');a.r((4,2,10,3),'white');a.p([(4,7),(6,6),(7,7),(9,6),(10,7),(8,10),(6,10)],'white');a.dot(7,7,'skin0');a.r((3,14,5,15),'wood0');a.r((8,14,10,15),'wood0');a.dot(11,3,'gold3')
    return a

def heart(full):
    a=Art(16,16,'transparent');pts=[(2,3),(5,2),(8,4),(11,2),(14,3),(15,6),(13,9),(8,14),(3,9),(1,6)]
    a.p(pts,'ink');a.p([(2,4),(5,3),(8,5),(11,3),(13,4),(14,6),(12,8),(8,12),(4,8),(2,6)],'heart' if full else 'slate')
    if full:a.r((3,4,5,5),'heartlight');a.dot(3,6,'white');a.r((11,4,12,4),'heartlight');a.l([(5,9),(8,12),(12,8)],'rose2')
    return a

def flame(frame):
    a=Art(16,16,'transparent');a.p([(8,1),(11,5),(11,8),(13,6),(14,10),(12,14),(7,15),(3,13),(2,9),(5,5),(5,9),(8,6)],'fire0')
    a.p([(8,2+frame),(10,6),(9,10),(12,8),(12,12),(10,14),(6,14),(4,12),(4,9),(7,7)],'fire2');a.p([(8,8),(10,12),(8,14),(6,12)],'gold4');a.dot(8,11,'white')
    return a

def projectile():
    a=Art(16,16,'transparent');a.p([(2,8),(6,5),(7,3),(11,4),(13,7),(12,11),(8,12),(4,10)],'fire0');a.e((5,5,12,11),'fire2');a.e((7,6,11,9),'gold4');a.dot(9,7,'white');a.dot(2,10,'gold1');return a

def golem():
    a=Art(32,32,'transparent')
    # A compact moss golem, with slab shoulders, roots, and amber heart.
    a.r((7,24,13,30),'ink');a.r((20,24,26,30),'ink');a.r((8,24,12,28),'stone2');a.r((21,24,25,28),'stone2');a.r((7,29,13,30),'stone0');a.r((20,29,26,30),'stone0')
    a.p([(6,10),(12,6),(22,6),(27,11),(27,23),(23,27),(10,27),(6,23)],'ink');a.p([(8,11),(12,8),(21,8),(25,12),(25,22),(22,25),(11,25),(8,22)],'stone1');a.p([(9,11),(13,9),(21,9),(23,12),(23,19),(19,23),(10,22)],'stone2')
    # Massive arms, asymmetrical vegetation.
    for x,y in [(1,11),(25,12)]:
        a.p([(x,y+2),(x+2,y),(x+5,y),(x+6,y+3),(x+5,y+12),(x+1,y+12),(x,y+9)],'ink');a.r((x+1,y+2,x+4,y+10),'stone2');a.r((x+1,y+2,x+3,y+4),'stone4');a.r((x+1,y+9,x+4,y+11),'stone0')
    a.p([(8,7),(10,2),(22,2),(25,7),(23,13),(10,13)],'ink');a.p([(10,7),(11,3),(21,3),(23,7),(22,11),(11,11)],'stone2');a.r((12,4,20,5),'stone4');a.r((11,8,22,10),'stone0');a.r((12,8,14,9),'gold2');a.r((19,8,21,9),'gold2');a.dot(13,8,'gold4');a.dot(20,8,'gold4')
    a.p([(16,13),(22,18),(17,24),(11,19)],'stone0');a.p([(16,14),(21,18),(17,22),(12,19)],'gold0');a.p([(16,15),(19,18),(17,21),(14,19)],'gold2');a.p([(16,16),(18,18),(17,20),(15,19)],'gold4')
    for x,y,w in [(9,3,6),(17,2,6),(5,11,5),(24,12,6),(8,22,4),(21,24,4)]:
        a.r((x,y,x+w,y+2),'pine1');a.r((x+1,y-1,x+w-1,y),'moss1');a.r((x+2,y-1,x+w-2,y-1),'moss3')
    a.l([(10,14),(9,17),(11,20)],'stone0');a.l([(22,14),(23,17),(22,20)],'stone1');a.r((3,22,5,23),'moss1');a.dot(22,4,'flower0');a.dot(23,3,'flower1')
    return a

def split_generated_source(source_path):
    """Keep generated C in deterministic, reviewable line-aligned chunks."""
    text = source_path.read_text()
    prefix = '#include "assets.h"\n\n'
    assert text.startswith(prefix)
    chunks, current, size = [], [], 0
    for line in text[len(prefix):].splitlines(keepends=True):
        if current and size + len(line.encode()) > 32768:
            chunks.append(''.join(current)); current, size = [], 0
        current.append(line); size += len(line.encode())
    if current:
        chunks.append(''.join(current))
    folder = source_path.parent / 'asset_data'
    folder.mkdir(exist_ok=True)
    for old in folder.glob('part_*.inc'):
        old.unlink()
    for index, content in enumerate(chunks):
        (folder / f'part_{index:03d}.inc').write_text(content)
    includes = ''.join(f'#include "asset_data/part_{i:03d}.inc"\n' for i in range(len(chunks)))
    source_path.write_text(prefix + '/* Generated by assets/generate_assets.py; edit the generator. */\n' + includes)

def emit_array(f,name,data,ctype='unsigned char'):
    f.write(f'const {ctype} {name}[{len(data)}] = {{\n')
    for i in range(0,len(data),32): f.write('  '+','.join(str(x) for x in data[i:i+32])+',\n')
    f.write('};\n\n')

def emit_image_tensor(f,name,tensor,dims):
    f.write('const unsigned char '+name+''.join('['+str(n)+']' for n in dims)+' = {\n')
    def recur(items,depth):
        for value in items:
            if isinstance(value,Art):
                f.write('  '*depth+'{\n');data=value.im.tobytes()
                for i in range(0,len(data),32):f.write('  '*(depth+1)+','.join(str(x) for x in data[i:i+32])+',\n')
                f.write('  '*depth+'},\n')
            else:
                f.write('  '*depth+'{\n');recur(value,depth+1);f.write('  '*depth+'},\n')
    recur(tensor,1);f.write('};\n\n')

def main():
    backgrounds=[village(),forest(),temple(),boss(),title()]
    bnames=['village','forest','temple','boss','title']
    for name,bg in zip(bnames,backgrounds):color_background(bg,name)
    sprites=[hero(d,f) for d in ('down','up','left','right') for f in (0,1)]
    sprites += [fox(0),fox(1),leaf(0),leaf(1),slime(0),slime(1),elder(),heart(True),heart(False),flame(0),flame(1),projectile()]
    big=golem()
    directions=('down','up','left','right')
    hero_anim=[[hero(d,f) for f in range(4)] for d in directions]
    companion_anim=[[fn('down',f) for f in range(4)] for fn in (fox_direction,leaf_direction)]
    companion_dir=[[[fn(d,f) for f in range(4)] for d in directions] for fn in (fox_direction,leaf_direction)]
    small_shadow=shadow_sprite();large_shadow=shadow_sprite(32,16)
    canopy_positions=[(0,112,0),(208,112,0),(0,112,1),(208,112,1),(0,112,3),(208,112,3)]
    canopies=[color_background(Art(32,32,'transparent') if room==0 else foreground_canopy(room,int(x>0)),bnames[room]) for x,y,room in canopy_positions]
    # Paste actors AFTER scenery remapping so their exact original colors also
    # remain unchanged in the title illustration.
    for spr,pos in [(sprites[0],(72,103)),(sprites[8],(88,108))]:
        backgrounds[4].im.paste(spr.im,pos,Image.frombytes('L',spr.im.size,bytes(255 if p else 0 for p in spr.im.tobytes())))
    for name,bg in zip(bnames,backgrounds):
        bg.im.save(OUT/f'{name}.png');bg.im.resize((960,640),Image.Resampling.NEAREST).save(OUT/f'{name}_4x.png')
    sheet=Image.new('RGB',(16*10,16*4),rgb[P['night']])
    for i,s in enumerate(sprites):sheet.paste(s.im.convert('RGB'),((i%10)*16,(i//10)*16))
    sheet.paste(big.im.convert('RGB'),(0,32));sheet.resize((800,320),Image.Resampling.NEAREST).save(OUT/'sprites_preview.png')
    contact=Image.new('RGB',(720,320))
    for i,bg in enumerate(backgrounds):contact.paste(bg.im.convert('RGB'),((i%3)*240,(i//3)*160))
    contact.resize((1440,640),Image.Resampling.NEAREST).save(OUT/'world_preview.png')
    h='''/* Original Emberbond pixel art, generated by assets/generate_assets.py. */
#ifndef EMBERBOND_ASSETS_H
#define EMBERBOND_ASSETS_H
enum { BACK_VILLAGE, BACK_FOREST, BACK_TEMPLE, BACK_BOSS, BACK_TITLE, BACK_COUNT };
enum {\n'''
    h+='  '+',\n  '.join('SPR_'+n for n in SPR_NAMES)+',\n  SPR_COUNT\n};\n'
    h+='extern const unsigned short game_palette[256];\n'
    h+='#define EMBERBOND_POLISHED_ART 1\n#define FOREGROUND_CANOPY_COUNT 6\n'
    h+='/* Direction order: down, up, left, right. Frame 0 is the idle pose. */\nextern const unsigned char hero_frames[4][4][256];\nextern const unsigned char companion_frames[2][4][256];\nextern const unsigned char companion_direction_frames[2][4][4][256];\nextern const unsigned char hero_shadow[256];\nextern const unsigned char boss_shadow[512];\n'
    h+='typedef struct { short x,y; unsigned char room; } ForegroundCanopy;\nextern const ForegroundCanopy foreground_canopies[FOREGROUND_CANOPY_COUNT];\nextern const unsigned char foreground_canopy_data[FOREGROUND_CANOPY_COUNT][1024];\n'
    h+=''.join(f'extern const unsigned char background_{name}[38400];\n' for name in bnames)
    h+='extern const unsigned char * const backgrounds[BACK_COUNT];\nextern const unsigned char sprite_data[SPR_COUNT][256];\nextern const unsigned char boss_data[1024];\n'
    h+='\n/* Named palette indices, including colors useful for HUD and overlays. */\n'
    h+=''.join(f'#define PAL_{name.upper()} {i}\n' for i,(name,_) in enumerate(COLORS))
    h+='\n#endif\n';(SRC/'assets.h.tmp').write_text(h);(SRC/'assets.h.tmp').replace(SRC/'assets.h')
    with (SRC/'assets.c.tmp').open('w') as f:
        f.write('#include "assets.h"\n\n')
        raw555=[]
        for name,hx in COLORS:raw555.append((int(hx[1:3],16)>>3)|((int(hx[3:5],16)>>3)<<5)|((int(hx[5:7],16)>>3)<<10))
        emit_array(f,'game_palette',raw555+[0]*(256-len(raw555)),'unsigned short')
        for name,bg in zip(bnames,backgrounds):emit_array(f,'background_'+name,list(bg.im.tobytes()))
        f.write('const unsigned char * const backgrounds[BACK_COUNT] = {'+','.join('background_'+n for n in bnames)+'};\n\n')
        f.write('const unsigned char sprite_data[SPR_COUNT][256] = {\n')
        for name,s in zip(SPR_NAMES,sprites):
            f.write('  { /* '+name+' */\n');data=list(s.im.tobytes())
            for i in range(0,256,32):f.write('    '+','.join(str(x) for x in data[i:i+32])+',\n')
            f.write('  },\n')
        f.write('};\n\n');emit_array(f,'boss_data',list(big.im.tobytes()))
        emit_image_tensor(f,'hero_frames',hero_anim,[4,4,256])
        emit_image_tensor(f,'companion_frames',companion_anim,[2,4,256])
        emit_image_tensor(f,'companion_direction_frames',companion_dir,[2,4,4,256])
        emit_array(f,'hero_shadow',list(small_shadow.im.tobytes()))
        emit_array(f,'boss_shadow',list(large_shadow.im.tobytes()))
        emit_image_tensor(f,'foreground_canopy_data',canopies,[6,1024])
        f.write('const ForegroundCanopy foreground_canopies[FOREGROUND_CANOPY_COUNT] = {'+','.join('{'+','.join(str(v) for v in p)+'}' for p in canopy_positions)+'};\n')
    (SRC/'assets.c.tmp').replace(SRC/'assets.c')
    split_generated_source(SRC/'assets.c')
    manifest={
      'canvas':[240,160],'sprite_size':[16,16],'sprite_anchor':'center; blit at position minus (8,8)','boss_size':[32,32],
      'palette':'shared RGB555; index 0 transparent; all backgrounds opaque nonzero','hud_safe_strip':[0,0,240,17],
      'village':{'spawn':[120,126],'solid_rectangles':[[25,48,61,50],[154,51,61,46],[41,117,25,32],[163,140,46,12],[0,21,20,140],[223,20,17,140]],'north_exit':[108,18,24,14],'props':{'houses':[[25,47,61,47],[154,50,61,45]],'shrine':[53,141],'lamps':[[99,91],[143,91]],'elder_suggested':[120,92]}},
      'forest':{'spawn':[120,140],'solid_rectangles':[[0,20,35,140],[207,20,33,140],[35,36,31,37],[180,40,27,37],[35,119,29,35],[182,120,25,32],[92,19,11,24],[138,19,11,24]],'north_exit':[107,19,26,14],'south_exit':[107,150,26,10],'props':{'gate_opening':[106,20,29,23],'lamps':[[90,47],[150,47]],'river':[0,78,240,13],'bridge_zone':[108,76,24,18],'bridge_requires_leaf':True}},
      'temple':{'spawn':[120,140],'solid_rectangles':[[0,0,23,160],[217,0,23,160],[23,0,80,31],[138,0,79,31],[55,56,18,18],[167,56,18,18],[34,36,14,16],[188,36,14,16],[35,129,14,16],[189,129,14,16]],'north_exit':[107,16,26,17],'south_exit':[106,150,28,10],'props':{'braziers':[[64,64],[176,64]],'gate':[103,12,35,20],'gate_closed_is_visual_only':True,'ritual_disc':[120,106]}},
      'boss':{'spawn':[120,139],'solid_rectangles':[[0,0,25,160],[215,0,25,160],[25,0,190,24]],'south_exit':[108,150,24,10],'props':{'boss_spawn':[120,67],'central_arena_clear':[40,40,160,100]}},
      'title':{'text_safe_zone':[20,32,137,70]},
      'credits':'All character, environment, and prop artwork is original code-native pixel art authored for Emberbond. No third-party art assets used.'}
    # Accurate collision footprints. Foliage tufts and tiny bushes are decorative;
    # tree canopy silhouettes, buildings, monuments, fences, and columns are solid.
    # Rectangles are [x,y,width,height], NOT inclusive x2/y2 coordinates.
    trees={
      'village':[(7,40,1.1),(34,32,.9),(61,31,1.0),(88,29,.85),(152,29,.85),(181,31,1.1),(213,34,1),(241,42,1.1)],
      'forest':[(5,44,1.3),(31,43,1.15),(61,33,1.2),(90,27,.9),(151,25,1),(181,36,1.2),(212,43,1.1),(18,85,1.2),(48,74,1),(199,79,1),(9,135,1.3),(46,144,1.1),(200,144,1.1),(235,145,1.2),(27,174,1.1),(75,176,1.1),(169,174,1.1),(217,177,1.2)],
      'boss':[(3,47,1.3),(32,30,1.2),(67,17,1.2),(105,9,1),(137,10,1),(176,18,1.2),(211,31,1.2),(238,52,1.3),(2,103,1.2),(237,102,1.2),(5,161,1.2),(35,191,1.2),(73,199,1.2),(167,199,1.2),(207,193,1.2),(239,160,1.2)]}
    fixed={
      'village':[[22,44,67,53],[151,47,67,50],[40,115,27,36],[163,139,46,14],[97,27,4,24],[140,27,4,24],[94,80,11,15],[138,80,11,15]],
      'forest':[[92,19,11,24],[138,19,11,24],[85,37,11,17],[145,37,11,17],[223,21,17,139]],
      'temple':[[0,0,24,160],[216,0,24,160],[24,0,79,31],[138,0,78,31],[34,36,13,15],[189,36,13,15],[35,129,13,15],[190,129,13,15]],
      'boss':[[11,46,27,36],[203,46,27,36],[11,105,27,36],[203,105,27,36]]}
    for name in ('village','forest','temple','boss'):
        manifest[name]['solid_rectangles']=fixed[name][:]
        manifest[name]['tree_positions']=trees.get(name,[])
        for x,y,scale in trees.get(name,[]):
            # Slightly inset rectangular canopy: outermost leaf pixels remain forgiving.
            x1=max(0,int(x-12*scale));y1=max(0,int(y-37*scale));x2=min(240,int(x+12*scale)+1);y2=min(160,int(y+2*scale)+1)
            if x2>x1 and y2>y1:manifest[name]['solid_rectangles'].append([x1,y1,x2-x1,y2-y1])
    manifest['collision_notes']='Static obstacle rectangles approximate opaque geometry. Engine should add world bounds and dynamic river/bridge, gate, and brazier obstacles. Small bushes, grass, floor rings, flowers, and fallen branch are decorative and walkable. Tree rects are inset slightly from foliage. Coordinates are x,y,width,height.'
    manifest['forest']['dynamic_rectangles']=[{'kind':'river','rect':[0,76,240,18],'exception_when_bridge_open':[108,76,24,18]}]
    manifest['forest']['suggested_enemy_centers']=[[77,120],[174,118],[167,65]]
    manifest['temple']['dynamic_rectangles']=[{'kind':'brazier','rect':[55,56,18,18]},{'kind':'brazier','rect':[167,56,18,18]},{'kind':'closed_gate','rect':[103,12,35,20]}]
    manifest['art_direction']={'revision':3,'principles':['Layered scalloped leaf volumes and visible trunk roots','Warm sunlit planes against cool contour shadows','Sparse clustered floor detail and unobstructed routes','Original auburn-haired teal-coat hero with golden trailing scarf','Four directional contact/passing walk poses; directional fox and hovering leaf companion'], 'reference_links':[{'kind':'Official screenshot page','url':'https://www.nintendo.com/jp/games/feature/nintendo-classics/a-8665_j/index.html'},{'kind':'Official Nintendo UK trailer','url':'https://www.youtube.com/watch?v=cSIDghMWVMA'},{'kind':'Official product page','url':'https://www.nintendo.com/en-gb/Games/Game-Boy-Advance/The-Legend-of-Zelda-The-Minish-Cap-267486.html'}],'rights':'Reference pages were used for high-level aesthetic research only. No screenshot pixels, maps, sprites, audio, ROMs, or animation frames are included or traced.'}
    manifest['art_direction']['background_palette']={
        'style':'Sunlit grass and foliage, warm cream paths, lighter temple stone, warm twilight',
        'method':'Hand-authored per-material scene ramps; palette-index remapping only',
        'colors_used':len(COLORS),'palette_capacity':256,
        'preserved_base_indices':[0,BASE_PALETTE_SIZE-1],
        'scenes':BACKGROUND_RAMPS,
        'preservation':'All original sprite, UI, combat-effect and shadow colors remain unchanged. Title actors are composited after remapping. Foreground canopies use the matching room ramp. Background geometry and collision rectangles are unchanged.'}
    manifest['animation']={'direction_order':list(directions),'hero_frames':[4,4,256],'companion_frames':[2,4,256],'companion_direction_frames':[2,4,4,256],'walk_phase':['idle/passing','left contact','raised passing','right contact'],'suggested_frame_ticks':6,'hero_shadow':[16,16],'boss_shadow':[32,16],'foreground_canopies': [{'room':r,'position':[x,y],'size':[32,32]} for x,y,r in canopy_positions],'transparency_index':0,'added_rom_data_bytes':4*4*256+2*4*256+2*4*4*256+256+512+6*1024+36}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    ch='/* Generated static collisions. Dynamic obstacles remain engine-owned. */\n#ifndef EMBERBOND_ASSET_COLLISIONS_H\n#define EMBERBOND_ASSET_COLLISIONS_H\ntypedef struct { short x,y,w,h; } AssetRect;\n'
    for name in ('village','forest','temple','boss'):
        rects=manifest[name]['solid_rectangles']
        ch+=f'static const AssetRect asset_solids_{name}[{len(rects)}] = {{\n'
        ch+=''.join('    {'+','.join(map(str,r))+'},\n' for r in rects)+'};\n'
        ch+=f'#define ASSET_SOLIDS_{name.upper()}_COUNT {len(rects)}\n'
    ch+='static const AssetRect * const asset_solids[4] = {asset_solids_village,asset_solids_forest,asset_solids_temple,asset_solids_boss};\n'
    ch+='static const unsigned char asset_solids_count[4] = {'+','.join(str(len(manifest[n]['solid_rectangles'])) for n in ('village','forest','temple','boss'))+'};\n#endif\n'
    (SRC/'asset_collisions.h.tmp').write_text(ch);(SRC/'asset_collisions.h.tmp').replace(SRC/'asset_collisions.h')
    (OUT/'CREDITS.txt').write_text(manifest['credits']+'\nGenerated by assets/generate_assets.py using Pillow.\n')
    # Native-pixel contact sheet and four-pose animation proof. These are art previews, not emulator captures.
    anim_sheet=Image.new('RGB',(64,192),rgb[P['night']])
    rows=hero_anim+companion_dir[0]+companion_dir[1]
    for y,row in enumerate(rows):
        for x,spr in enumerate(row):anim_sheet.paste(spr.im.convert('RGB'),(x*16,y*16))
    anim_sheet.save(OUT/'animation_sheet.png');anim_sheet.resize((384,1152),Image.Resampling.NEAREST).save(OUT/'animation_sheet_6x.png')
    anim_frames=[]
    for f in range(4):
        view=Image.new('RGB',(128,96),rgb[P['grass1']])
        for row in range(3):
            for d in range(4):
                sp=rows[d+row*4][f];pos=(d*32+8,row*32+8)
                view.paste(small_shadow.im.convert('RGB'),pos,Image.frombytes('L',(16,16),bytes(255 if p else 0 for p in small_shadow.im.tobytes())))
                view.paste(sp.im.convert('RGB'),pos,Image.frombytes('L',(16,16),bytes(255 if p else 0 for p in sp.im.tobytes())))
        anim_frames.append(view.resize((512,384),Image.Resampling.NEAREST))
    anim_frames[0].save(OUT/'walk_cycles.gif',save_all=True,append_images=anim_frames[1:],duration=100,loop=0,disposal=2)
    canopy_sheet=Image.new('RGB',(192,32),rgb[P['night']])
    for i,sp in enumerate(canopies):canopy_sheet.paste(sp.im.convert('RGB'),(i*32,0))
    canopy_sheet.resize((768,128),Image.Resampling.NEAREST).save(OUT/'foreground_canopies_preview.png')
    print('Generated 5 opaque native backgrounds; 20 fallback sprites; 16 hero poses; 32 directional companion poses; 6 foreground boughs; 2 shadows; boss; RGB555 palette; manifest; C sources; PNG/GIF art previews.')

if __name__=='__main__':main()
