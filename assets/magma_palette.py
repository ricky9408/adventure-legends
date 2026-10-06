#!/usr/bin/env python3
"""Emberbond: original, code-native pixel art. Authored from geometric primitives.
No external art, game sprites, traced assets, or generated raster inputs are used.
Run with Python 3 + Pillow. The shared palette is quantized to native GBA RGB555.
"""
from pathlib import Path
from PIL import Image, ImageDraw
import math, random, json
ROOT=Path(__file__).resolve().parents[1]
# Read-only palette/primitives extracted verbatim; no output side effects.
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
