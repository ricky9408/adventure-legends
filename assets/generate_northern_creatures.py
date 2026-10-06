#!/usr/bin/env python3
"""Original native-pixel Northern companions; no extracted/raster source art.

Only writes assets/northern_creatures and src/northern_creature_art.{h,c}/data.
Art does not enable catalog forms, grant companions, or implement their powers.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import tempfile
from PIL import Image, ImageDraw
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/northern_creatures'
SRC = ROOT / 'src'
DIRECTIONS = ('down', 'up', 'left', 'right')
FORM_IDS = (19, 20, 22, 23, 73, 74, 75, 76, 77, 78)
NAMES = ('Spoolbud', 'Loomcrown', 'Cindertray', 'Kilnbarrow', 'Keelkip', 'Wakecradle', 'Cairncricket', 'Archspring', 'Rivetfoil', 'Gimbalcloak')
KEYS = tuple(s.lower() for s in NAMES)
spec = importlib.util.spec_from_file_location('northern_art_base', ROOT / 'assets/generate_assets.py')
base = importlib.util.module_from_spec(spec); spec.loader.exec_module(base)
Art, P, PAL, RGB = base.Art, base.P, base.PAL, base.rgb
assert len(base.COLORS) == 178 and base.BASE_PALETTE_SIZE == 97

class Pen:
    """Pixel-space authoring only; never rotates a front drawing into other views."""
    def __init__(self, a, dy=0): self.a, self.dy = a, dy
    def p(self, pts, c): self.a.p([(x,y+self.dy) for x,y in pts],c)
    def l(self, pts, c, w=1): self.a.l([(x,y+self.dy) for x,y in pts],c,w)
    def e(self, b, c): self.a.e((b[0],b[1]+self.dy,b[2],b[3]+self.dy),c)
    def r(self, b, c): self.a.r((b[0],b[1]+self.dy,b[2],b[3]+self.dy),c)
    def dot(self,x,y,c): self.a.dot(x,y+self.dy,c)


def eye(q, x, y, look=0):
    q.r((x,y,x+1,y+2),'white'); q.dot(x+look,y+1,'ink'); q.dot(x+look,y+2,'ink')


def finish(a,d):
    if d == 'right': a.im = a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT); a.d = ImageDraw.Draw(a.im)
    return a


def motion(frame, ability):
    return ((0,0,-1,0)[frame], (0,-1,0,1)[frame]) if ability is None else ((0,-1)[ability],(-1,1)[ability])


def ability_accent(a,d,pose,c,bright):
    # A small directional indicator stays outside the face and main silhouette.
    coords={'down':[(6,14),(7,15),(9,14)],'up':[(6,1),(7,0),(9,1)],
            'left':[(1,6),(0,7),(1,9)],'right':[(14,6),(15,7),(14,9)]}[d]
    for k,(x,y) in enumerate(coords):
        if k != (2 if pose == 0 else 0): a.dot(x,y,bright if k == 1 else c)


def spoolbud(d,f,ability=None):
    a=Art(16,16,'transparent'); lift,s=motion(f,ability); q=Pen(a,lift)
    side=d in ('left','right')
    # Three root paws step independently beneath a soft bobbin belly.
    for x,y,dx in ((4,13,s),(10,13,-s),(7,14,0)):
        a.l([(x,10+lift),(x+dx,y-1),(x+dx+1,y)],'wood0'); a.dot(x+dx,y-1,'wood4')
    if side:
        q.l([(11,8),(13,6+s),(14,4+s),(12,3+s),(11,4+s)],'pine0')
        q.l([(12,6+s),(13,4+s)],'pine4')
        q.p([(4,5),(8,4),(11,5),(12,8),(11,11),(7,12),(4,11),(2,9),(2,7)],'wood0')
        q.p([(4,6),(8,5),(10,6),(11,8),(10,10),(7,11),(4,10),(3,8)],'wood3')
        q.l([(8,5),(7,7),(8,10)],'wood1'); q.l([(10,6),(9,8),(10,10)],'wood5')
        q.p([(3,6),(1,4),(2,2),(5,3),(6,6)],'pine0'); q.p([(3,5),(2,3),(4,4)],'pine5')
        q.p([(5,5),(6,2),(9,2),(8,4)],'pine0'); q.l([(6,4),(7,3),(8,3)],'pine4')
        eye(q,3,7); q.dot(2,9,'ink'); q.dot(5,10,'rose4'); q.dot(6,6,'wood5')
    else:
        q.l([(11,9),(13,7+s),(13,4+s),(11,3+s),(10,4+s)],'pine0');q.l([(12,6+s),(12,4+s)],'pine5')
        q.p([(4,5),(10,5),(12,7),(12,10),(10,12),(4,12),(2,10),(2,7)],'wood0')
        q.p([(4,6),(10,6),(11,7),(11,10),(9,11),(5,11),(3,10),(3,7)],'wood3')
        q.l([(4,6),(4,10),(6,11)],'wood5');q.l([(10,6),(10,10),(8,11)],'wood1')
        q.p([(5,5),(2,4),(1,1),(4,2),(6,4)],'pine0');q.l([(3,2),(4,3),(5,4)],'pine5')
        q.p([(7,5),(8,2),(11,1),(11,3),(9,5)],'pine0');q.l([(8,4),(10,2)],'pine4')
        if d=='down':
            eye(q,4,7,1);eye(q,8,7);q.l([(6,10),(7,10)],'wood0');q.dot(3,10,'rose4');q.dot(10,10,'rose4')
        else:
            q.e((5,7,9,10),'wood1');q.l([(6,7),(8,7),(8,9),(6,9)],'wood5');q.dot(11,5,'pine4')
    if ability is not None:
        # The living vine is an arm, curling before the tether releases.
        q.l([(11,10),(13,11),(14,9-ability),(13,8-ability)],'pine4')
    finish(a,d)
    if ability is not None: ability_accent(a,d,ability,'pine5','leafwarm')
    return a


def loomcrown(d,f,ability=None):
    a=Art(16,16,'transparent'); lift,s=motion(f,ability);q=Pen(a,lift);side=d in ('left','right')
    # Tall living antler-trellis; legs sway the suspended seed, not a bobbin roll.
    feet=((3+s,14),(11-s,14)) if not side else ((5+s,14),(11-s,13))
    for x,y in feet:
        a.l([(x,10+lift),(x,y-1),(x-1,y)],'wood0');a.l([(x,11+lift),(x,y-1)],'wood4')
    if side:
        q.p([(5,10),(4,6),(5,3),(8,1),(10,2),(12,5),(12,10),(10,11),(10,5),(8,3),(7,5),(7,10)],'wood0')
        q.l([(5,9),(5,5),(6,3),(8,2)],'wood4');q.l([(10,3),(11,5),(11,9)],'wood3')
        q.l([(5,5),(10,5)],'pine3');q.dot(8+s,6,'wood5')
        q.p([(4,7),(7,7),(9,9),(8,12),(5,13),(2,11),(2,9)],'pine0')
        q.p([(4,8),(6,8),(8,9),(7,11),(5,12),(3,10)],'pine4')
        eye(q,3,9);q.dot(2,11,'wood0');q.dot(6,11,'mint')
        q.p([(7,2),(5,1),(3,2),(3,4),(6,4)],'pine0');q.l([(4,2),(5,2),(6,3)],'pine5')
        q.p([(9,2),(11,1),(14,2),(13,4),(11,4)],'pine0');q.l([(11,2),(13,2)],'pine4')
        q.l([(11,9),(14,10+s),(14,12+s)],'pine0');q.dot(14,10+s,'pine5')
    else:
        q.p([(2,11),(2,6),(4,3),(6,2),(9,2),(12,4),(13,7),(13,12),(11,12),(11,7),(9,4),(6,4),(4,7),(4,11)],'wood0')
        q.l([(3,10),(3,6),(5,3),(7,3)],'wood4');q.l([(10,4),(12,7),(12,11)],'wood3')
        q.l([(4,6),(11,6)],'pine2');q.l([(7+s,6),(7+s,8)],'wood5')
        q.p([(5,8),(8,7),(10,9),(10,11),(8,13),(5,12),(4,10)],'pine0')
        q.p([(6,8),(8,8),(9,9),(9,11),(7,12),(5,10)],'pine4')
        q.p([(5,3),(1,3),(1,1),(4,1),(6,2)],'pine0');q.l([(2,2),(4,2)],'pine5')
        q.p([(9,3),(10,1),(13,1),(14,3),(11,4)],'pine0');q.l([(11,2),(12,2),(13,3)],'pine5')
        q.dot(8,1,'gold3')
        if d=='down':eye(q,5,9,1);eye(q,8,9);q.dot(7,12,'wood0')
        else:q.l([(6,9),(8,9),(8,11),(6,11)],'pine2');q.dot(7,8,'mint');q.dot(2,5,'pine4')
    if ability is not None:
        q.l([(3,7),(1,8+ability),(1,11+ability),(4,12)],'mint');q.dot(12,5,'leafwarm')
    finish(a,d)
    if ability is not None:ability_accent(a,d,ability,'pine5','leafwarm')
    return a


def cindertray(d,f,ability=None):
    a=Art(16,16,'transparent');lift,s=motion(f,ability);q=Pen(a,lift);side=d in ('left','right')
    # Warm tortoise-like quadruped with a triangular ceramic dorsal shell.
    for x,y,k in ((3,12,s),(10,12,-s),(5,13,-s),(12,13,s)):
        a.r((x+k,y-1,x+k+1,y),'wood0');a.dot(x+k,y-1,'fire2')
    if side:
        q.p([(4,8),(6,3),(8,2),(11,4),(13,8),(12,11),(5,12),(3,10)],'wood0')
        q.p([(5,8),(7,4),(8,3),(10,5),(12,8),(11,10),(6,11)],'fire1')
        q.l([(7,4),(8,4),(11,8)],'skin2');q.l([(5,8),(11,8)],'wood0');q.l([(7,9),(10,9)],'gold2')
        q.p([(3,7),(5,8),(6,10),(4,12),(1,11),(1,8)],'wood0');q.p([(2,8),(4,8),(5,10),(3,11),(2,10)],'fire3')
        eye(q,2,8);q.dot(1,10,'wood0');q.dot(4,11,'rose3')
        q.l([(12,10),(14,9+s),(14,7+s)],'wood0');q.dot(14,8+s,'fire2')
    else:
        q.p([(3,7),(6,3),(8,2),(11,5),(13,8),(12,11),(10,12),(4,12),(2,10)],'wood0')
        q.p([(4,7),(6,4),(8,3),(10,6),(12,8),(11,10),(5,11),(3,9)],'fire1')
        q.l([(6,4),(8,4),(10,7)],'skin2');q.l([(4,8),(11,8)],'wood0');q.dot(5,9,'gold3');q.dot(10,9,'gold3')
        if d=='down':
            q.p([(5,8),(9,8),(11,10),(10,12),(8,13),(5,12),(4,10)],'wood0');q.p([(5,9),(9,9),(10,10),(9,12),(6,12),(5,11)],'fire3')
            eye(q,5,9,1);eye(q,8,9);q.dot(7,12,'wood0')
        else:q.l([(5,10),(7,11),(10,10)],'fire0');q.l([(8,12),(9,14),(11,14)],'wood0');q.dot(10,13,'fire2')
    if ability is not None:
        q.l([(6,7-ability),(8,6-ability),(10,7-ability)],'gold4');q.dot(8,5-ability,'ember')
    finish(a,d)
    if ability is not None:ability_accent(a,d,ability,'fire3','gold4')
    return a


def kilnbarrow(d,f,ability=None):
    a=Art(16,16,'transparent');lift,s=motion(f,ability);q=Pen(a,lift);side=d in ('left','right')
    # Broad-legged long ceramic salamander; hinged dorsal plates breathe sideways.
    for x,y,k in ((2,12,s),(11,12,-s),(4,14,-s),(10,14,s)):
        a.p([(x,9+lift),(x+k-1,y),(x+k+2,y),(x+2,10+lift)],'wood0');a.l([(x,11),(x+k,y-1),(x+k+1,y-1)],'fire2')
    if side:
        q.l([(12,9),(14,7+s),(14,5+s),(13,4+s)],'wood0');q.l([(13,8),(13,6+s)],'fire2')
        q.p([(4,5),(9,4),(12,5),(13,7),(12,11),(8,12),(4,11),(2,8)],'wood0')
        q.p([(5,6),(9,5),(11,6),(12,7),(11,10),(8,11),(4,10),(3,8)],'fire1')
        q.l([(6,6),(8,5),(10,6)],'skin2');q.l([(8,6),(8,9)],'wood0');q.l([(10,7),(11,7)],'gold3')
        q.p([(5+s,4),(8+s,2),(11+s,3),(12+s,5),(8,6),(5,6)],'wood0');q.l([(6+s,4),(8+s,3),(10+s,4)],'fire3')
        q.p([(3,6),(5,7),(6,10),(4,12),(1,11),(0,9),(1,7)],'wood0');q.p([(2,7),(4,8),(5,10),(3,11),(1,9)],'fire3')
        eye(q,1,8);q.dot(0,10,'wood0');q.dot(4,10,'rose4');q.dot(3,7,'gold4')
    else:
        q.p([(4,4),(9,3),(12,5),(13,8),(12,11),(9,13),(4,12),(2,9),(2,6)],'wood0')
        q.p([(4,5),(9,4),(11,6),(12,8),(11,10),(8,12),(5,11),(3,8),(3,6)],'fire1')
        q.p([(3+s,4),(6+s,2),(9+s,2),(12+s,4),(10,6),(5,6)],'wood0');q.p([(4+s,4),(6+s,3),(9+s,3),(11+s,4),(9,5),(5,5)],'fire3')
        q.l([(4,7),(11,7)],'wood0');q.l([(5,8),(10,8)],'gold3');q.l([(7,6),(7,9)],'wood0')
        if d=='down':
            q.p([(5,9),(9,9),(11,11),(10,13),(8,14),(5,13),(4,11)],'wood0');q.p([(5,10),(9,10),(10,11),(9,13),(6,13)],'fire3')
            eye(q,5,10,1);eye(q,8,10);q.dot(7,13,'wood0')
        else:q.l([(5,10),(9,10)],'fire0');q.l([(8,12),(10,14),(13,13)],'wood0');q.l([(9,12),(11,13)],'fire3');q.dot(3,4,'skin2')
    if ability is not None:
        # Bright slit widens into the tilted upper shell without masking eyes.
        q.l([(5,6-ability),(9,6-ability),(11,5-ability)],'gold4');q.dot(10,3-ability,'ember')
    finish(a,d)
    if ability is not None:ability_accent(a,d,ability,'fire2','gold4')
    return a


def keelkip(d,f,ability=None):
    a=Art(16,16,'transparent');lift,s=motion(f,ability);q=Pen(a,lift);side=d in ('left','right')
    # A seal pup, overlapping translucent belly ribs and paddling skates.
    if side:
        q.p([(10,10),(13,8+s),(15,9+s),(13,11),(11,12)],'water0');q.l([(12,10),(14,9+s)],'water4')
        q.p([(3,7),(5,5),(7,6),(9,8),(12,10),(11,12),(5,13),(2,11),(1,9)],'water0')
        q.p([(3,8),(5,6),(6,7),(8,9),(11,10),(10,11),(5,12),(2,10)],'blue2')
        q.p([(3,8),(5,7),(6,9),(8,10),(5,11),(2,10)],'blue3')
        q.l([(8,9),(7,11),(9,11)],'water4');q.l([(10,10),(9,12)],'water1')
        q.p([(5,11),(7,11),(7+s,14),(4+s,14),(3,13)],'water0');q.l([(5,12),(5+s,13)],'water4')
        q.p([(3,5),(5,4),(7,5),(7,8),(5,10),(2,9),(1,7)],'water0');q.p([(3,6),(5,5),(6,6),(6,8),(4,9),(2,8)],'blue3')
        eye(q,2,6);q.dot(1,8,'ink');q.dot(4,8,'watergleam');q.dot(5,5,'water4')
    else:
        q.p([(6,9),(9,9),(11,11),(10,13),(7,14),(4,12)],'water0');q.p([(6,10),(8,10),(10,11),(8,13),(6,12)],'blue2')
        q.l([(5,11),(9,11)],'water4');q.l([(6,13),(8,13)],'water3')
        q.p([(4,9),(2,9+s),(0,12+s),(3,13),(5,11)],'water0');q.l([(2,11+s),(3,11)],'water4')
        q.p([(10,9),(13,9-s),(15,11-s),(12,13),(9,11)],'water0');q.l([(11,11),(13,10-s)],'water4')
        if d=='down':
            q.p([(5,4),(9,4),(11,6),(11,9),(9,11),(5,11),(3,9),(3,6)],'water0');q.p([(5,5),(8,5),(10,6),(10,9),(8,10),(5,10),(4,8),(4,6)],'blue3')
            eye(q,4,6,1);eye(q,8,6);q.dot(7,9,'ink');q.l([(6,10),(8,10)],'water1');q.dot(4,9,'watergleam');q.dot(10,9,'water4')
        else:
            q.p([(5,3),(8,2),(10,4),(10,7),(8,9),(5,8),(3,6),(3,4)],'water0');q.p([(5,4),(8,3),(9,4),(9,6),(7,8),(5,7),(4,5)],'blue3');q.l([(6,4),(8,4)],'watergleam');q.l([(5,6),(7,7),(9,6)],'blue2')
            q.p([(6,12),(4,14),(6,15),(8,14),(10,15),(11,13),(9,12)],'water0');q.l([(6,13),(8,13),(9,14)],'water4')
    if ability is not None:q.l([(4,12),(7,13),(11,12)],'watergleam')
    finish(a,d)
    if ability is not None:ability_accent(a,d,ability,'water4','watergleam')
    return a


def wakecradle(d,f,ability=None):
    a=Art(16,16,'transparent');lift,s=motion(f,ability);q=Pen(a,lift);side=d in ('left','right')
    # Long-necked seal with two crescent flippers: an open sling, not a hoop.
    if side:
        q.p([(7,9),(10,7),(13,4+s),(14,6+s),(13,10),(11,13),(7,14),(5,12)],'water0')
        q.p([(8,10),(11,8),(13,6+s),(12,10),(10,12),(7,13),(6,12)],'blue2')
        q.l([(9,11),(11,10),(12,8)],'watergleam')
        q.p([(4,9),(5,5),(4,3),(5,1),(8,1),(9,3),(8,5),(7,7),(7,11),(5,13),(2,12),(1,10)],'water0')
        q.p([(5,9),(6,5),(5,3),(6,2),(8,2),(8,4),(7,5),(6,8),(6,11),(4,12),(2,11)],'blue3')
        eye(q,5,2);q.dot(4,4,'ink');q.dot(7,4,'water4')
        q.p([(5,11),(6,12),(4+s,14),(1+s,14),(1,12)],'water0');q.l([(2,12),(4,12),(3+s,13)],'water4')
        q.l([(8,12),(10,13),(13,12)],'water3');q.dot(14,10+s,'water4')
    else:
        q.p([(4,8),(2,5+s),(1,6+s),(1,10),(3,13),(5,14),(7,13),(6,11)],'water0')
        q.p([(3,8),(2,7+s),(2,10),(4,12),(5,13),(6,12)],'blue2')
        q.p([(10,8),(12,4-s),(14,5-s),(14,10),(12,13),(10,14),(8,13),(9,11)],'water0')
        q.p([(11,8),(13,6-s),(13,10),(11,12),(10,13),(9,12)],'blue3')
        q.l([(3,10),(4,11),(5,12)],'watergleam');q.l([(12,9),(11,11)],'water4')
        q.l([(5,12),(7,13),(10,12)],'water0');q.l([(5,11),(7,12),(10,11)],'water4')
        # Head and narrow upright chest do not fill the flipper apertures.
        q.p([(5,2),(8,1),(10,3),(10,5),(8,7),(8,10),(7,11),(6,10),(6,7),(4,5),(4,3)],'water0')
        q.p([(5,3),(7,2),(9,3),(9,5),(7,6),(7,10),(6,6),(5,5)],'blue3')
        if d=='down':eye(q,5,3,1);eye(q,8,3);q.dot(7,6,'ink');q.dot(5,6,'watergleam')
        else:q.l([(6,3),(8,3),(8,5),(6,5)],'blue2');q.dot(6,2,'watergleam');q.dot(4,2,'water3')
    if ability is not None:
        q.l([(2,11),(3,13),(7,14),(12,12)],'watergleam');q.dot(13,7,'water4')
    finish(a,d)
    if ability is not None:ability_accent(a,d,ability,'water3','watergleam')
    return a


def cairncricket(d,f,ability=None):
    a=Art(16,16,'transparent');lift,s=motion(f,ability);q=Pen(a,lift);side=d in ('left','right')
    # Long angular haunch, plate-gap abdomen, antennae and small inquisitive face.
    if side:
        a.l([(9,7+lift),(13,10),(10+s,13),(13+s,14)],'stone0',2);a.l([(10,8+lift),(12,10),(9+s,13)],'wood4')
        a.l([(5,10+lift),(3-s,13),(1-s,13)],'stone0');a.dot(3-s,12,'stone4')
        q.p([(7,5),(10,4),(12,6),(11,8),(8,9),(5,8)],'stone0');q.p([(7,6),(10,5),(11,6),(9,8),(6,7)],'wood4')
        q.l([(8,9),(10,9),(11,10)],'stone4')
        q.l([(4,5),(2,3),(2,1)],'stone0');q.dot(2,1,'gold2');q.l([(6,5),(7,2),(9,1)],'stone0');q.dot(9,1,'gold3')
        q.p([(3,5),(6,5),(8,7),(7,10),(4,11),(1,9),(1,7)],'stone0');q.p([(3,6),(5,6),(7,7),(6,9),(4,10),(2,8)],'stone4')
        eye(q,2,7);q.dot(1,9,'wood0');q.dot(5,9,'gold2')
    else:
        for x,k in ((3,s),(12,-s)):
            a.l([(5 if x==3 else 10,8+lift),(x,10),(x+k,13),(x+k+(-1 if x==3 else 1),14)],'stone0',2)
            a.l([(5 if x==3 else 10,8+lift),(x,10),(x+k,12)],'wood4')
        q.p([(5,5),(9,5),(11,7),(10,9),(5,9),(4,7)],'stone0');q.p([(6,6),(9,6),(10,7),(8,8),(5,7)],'wood4')
        q.l([(6,10),(9,10)],'stone4')
        q.l([(5,5),(3,3),(3,1)],'stone0');q.dot(3,1,'gold2');q.l([(9,5),(11,3),(12,2)],'stone0');q.dot(12,2,'gold3')
        if d=='down':
            q.p([(5,8),(9,8),(11,10),(9,12),(5,12),(3,10)],'stone0');q.p([(5,9),(9,9),(10,10),(8,11),(5,11),(4,10)],'stone4')
            eye(q,4,9,1);eye(q,8,9);q.dot(7,12,'wood0')
        else:q.p([(6,3),(9,3),(10,5),(8,7),(5,6),(5,4)],'stone0');q.l([(6,4),(8,4),(9,5)],'stone4');q.dot(8,6,'gold2');q.dot(6,12,'stone0')
    if ability is not None:q.l([(3,14),(7,13),(11,14)],'gold3');q.dot(12,11,'stone5')
    finish(a,d)
    if ability is not None:ability_accent(a,d,ability,'wood4','gold4')
    return a


def archspring(d,f,ability=None):
    a=Art(16,16,'transparent');lift,s=motion(f,ability);q=Pen(a,lift);side=d in ('left','right')
    # Cricket evolution opens/closes two arching haunches above a hanging thorax.
    if side:
        q.p([(6,7),(8,3),(11,2),(14,5),(14,8),(12,11),(12-s,14),(10-s,14),(11,10),(12,7),(10,5),(8,8)],'stone0')
        q.l([(8,6),(9,4),(11,3),(13,5),(13,7),(11,10)],'wood4',2);q.dot(11,4,'stone5')
        a.l([(6,9+lift),(4+s,13),(2+s,14)],'stone0',2);a.l([(6,10+lift),(4+s,12),(3+s,13)],'stone4')
        q.l([(4,6),(2,3),(3,1)],'stone0');q.dot(3,1,'gold3');q.l([(6,5),(7,2),(6,1)],'stone0');q.dot(6,1,'gold2')
        q.p([(3,6),(6,5),(8,7),(8,9),(6,12),(3,11),(1,9),(1,7)],'stone0');q.p([(3,7),(5,6),(7,7),(7,9),(5,11),(3,10),(2,8)],'stone4')
        eye(q,2,7);q.dot(1,9,'wood0');q.l([(5,8),(6,9),(5,10)],'gold2');q.dot(4,6,'stone5')
        q.l([(8,9),(10,10),(9,12),(7,12)],'stone0');q.dot(9,11,'wood4')
    else:
        for right in (False,True):
            pts=[(6,5),(4,2),(2,3),(0,7),(1,10),(2+s,14),(4+s,14),(3,10),(2,7),(3,5),(5,7)]
            if right: pts=[(15-x,y-(1 if y==2 else 0)) for x,y in pts]
            q.p(pts,'stone0')
            line=[(5,5),(4,3),(2,4),(1,7),(2,10),(3+s,13)]
            q.l([(15-x,y) if right else (x,y) for x,y in line],'wood4')
        q.l([(5,6),(10,6)],'stone0');q.l([(7,6),(7,8)],'gold2')
        q.l([(5,7),(4,4),(6,1)],'stone0');q.dot(6,1,'gold3');q.l([(9,7),(11,4),(10,2)],'stone0');q.dot(10,2,'gold3')
        q.p([(6,8),(9,8),(11,10),(10,12),(8,14),(5,12),(4,10)],'stone0');q.p([(6,9),(8,9),(10,10),(9,12),(7,13),(5,11)],'stone4')
        if d=='down':eye(q,5,9,1);eye(q,8,9);q.dot(7,12,'wood0');q.dot(8,13,'gold2')
        else:
            q.l([(6,10),(8,9),(9,11),(7,12)],'wood3');q.dot(7,9,'stone5');q.dot(6,8,'stone4')
            q.p([(7,12),(9,12),(10,14),(8,15),(7,14)],'stone0');q.l([(8,13),(9,14)],'wood4')
    if ability is not None:q.l([(3,14),(6,15),(10,15),(13,14)],'gold3');q.dot(8,7,'gold4')
    finish(a,d)
    if ability is not None:ability_accent(a,d,ability,'wood4','gold4')
    return a


def rivetfoil(d,f,ability=None):
    a=Art(16,16,'transparent');lift,s=motion(f,ability);q=Pen(a,lift);side=d in ('left','right')
    # Perky folded-metal wren: pleated wings, beak and two forked bird feet.
    for x,k in ((5,s),(10,-s)):
        a.l([(x,10+lift),(x+k,13),(x+k-1,14),(x+k+1,14)],'wood0');a.dot(x+k,13,'gold2')
    if side:
        q.p([(10,9),(13,6+s),(14,8+s),(12,11)],'stone0');q.l([(12,9),(13,8+s)],'silver')
        q.p([(4,5),(7,3),(10,5),(12,8),(10,11),(6,12),(3,10),(2,7)],'stone0')
        q.p([(4,6),(7,4),(9,5),(11,8),(9,10),(6,11),(3,9)],'silver')
        q.p([(7,6),(10,5),(11,8),(8,10),(6,9)],'stone0');q.p([(8,6),(10,6),(10,8),(8,9)],'blue3');q.l([(7,7),(9,8)],'white')
        q.p([(3,7),(0,8),(3,9)],'wood0');q.dot(1,8,'gold3')
        eye(q,3,6);q.dot(6,5,'white');q.dot(6,10,'gold2');q.dot(7,10,'gold4')
        q.l([(8,11),(9+s,12)],'stone0');q.dot(9+s,13,'gold3')
    else:
        q.p([(7,2),(10,4),(12,7),(11,11),(8,12),(4,11),(2,8),(4,4)],'stone0')
        q.p([(7,3),(9,5),(11,7),(10,10),(7,11),(4,10),(3,8),(5,5)],'silver')
        q.p([(4,6),(2,7),(1,10+s),(5,11),(6,9)],'stone0');q.l([(4,7),(3,9+s),(5,10)],'blue3')
        q.p([(10,6),(13,7),(14,10-s),(10,11),(9,9)],'stone0');q.l([(11,7),(12,9-s),(10,10)],'white')
        if d=='down':eye(q,4,5,1);eye(q,8,5);q.p([(6,8),(8,8),(7,10)],'wood0');q.dot(7,8,'gold3');q.dot(4,10,'gold2')
        else:q.p([(5,5),(8,4),(10,7),(8,10),(5,9)],'stone0');q.l([(6,6),(8,5),(9,7),(7,9)],'blue3');q.l([(7,11),(8+s,13)],'stone0');q.dot(8+s,13,'gold3')
    if ability is not None:q.l([(2,6),(1,4+ability),(3,3+ability)],'white');q.dot(12,6,'gold4')
    finish(a,d)
    if ability is not None:ability_accent(a,d,ability,'silver','white')
    return a


def gimbalcloak(d,f,ability=None):
    a=Art(16,16,'transparent');lift,s=motion(f,ability);q=Pen(a,lift);side=d in ('left','right')
    # Broad folded bird canopy around a suspended breast-ring and tiny talons.
    if side:
        q.p([(6,5),(8,1),(10,2),(10,5),(14,3+s),(14,7),(12,10),(9,11),(5,9)],'stone0')
        q.p([(7,5),(9,2),(9,6),(13,5+s),(13,7),(11,9),(8,10),(6,8)],'silver')
        q.l([(9,6),(11,8),(13,6+s)],'blue3');q.l([(8,4),(8,6),(10,8)],'white')
        q.p([(4,4),(7,4),(8,6),(7,9),(4,10),(2,8),(2,6)],'stone0');q.p([(4,5),(6,5),(7,6),(6,8),(4,9),(3,7)],'silver')
        eye(q,3,5);q.p([(3,7),(0,8),(3,9)],'wood0');q.dot(1,8,'gold3')
        q.e((5,9,10,14),'wood0');q.e((6,10,9,13),'gold2');q.r((7,11,8,12),'transparent');q.dot(6,10,'gold4')
        a.l([(6,13+lift),(4+s,14),(3+s,14)],'stone0');a.l([(10,12+lift),(12-s,13)],'stone0');a.dot(12-s,14,'gold2')
    else:
        q.p([(6,5),(3,1),(1,2),(2,6),(0,6+s),(1,10+s),(4,12),(7,9),(8,7)],'stone0')
        q.p([(5,5),(3,2),(3,6),(1,7+s),(2,9+s),(4,10),(6,8)],'silver');q.l([(3,6),(4,8+s),(5,7)],'white')
        q.p([(9,5),(12,1),(14,2),(13,6),(15,7-s),(14,11-s),(11,12),(8,9),(7,7)],'stone0')
        q.p([(10,5),(12,2),(12,6),(14,8-s),(13,10-s),(11,11),(9,8)],'blue2');q.l([(12,6),(11,8-s),(10,7)],'blue3')
        q.e((5,9,10,14),'wood0');q.e((6,10,9,13),'gold2');q.r((7,11,8,12),'transparent');q.dot(6,10,'gold4')
        q.p([(6,3),(9,3),(11,5),(10,8),(8,10),(5,8),(4,5)],'stone0');q.p([(6,4),(8,4),(10,5),(9,7),(7,9),(5,6)],'silver')
        if d=='down':eye(q,5,4,1);eye(q,8,4);q.p([(6,7),(8,7),(7,9)],'wood0');q.dot(7,7,'gold3')
        else:q.l([(6,5),(8,4),(9,6),(7,8),(6,6)],'blue2');q.dot(6,4,'white');q.dot(10,3,'silver')
        a.l([(5,12+lift),(4+s,14),(3+s,14)],'stone0');a.dot(4+s,13,'gold2');a.l([(10,12+lift),(11-s,14),(12-s,14)],'stone0');a.dot(11-s,13,'gold2')
    if ability is not None:q.l([(1,8),(1,11),(3,12)],'white');q.l([(14,7),(14,11),(12,12)],'blue3')
    finish(a,d)
    if ability is not None:ability_accent(a,d,ability,'silver','gold4')
    return a

FIELD_FUNCTIONS=(spoolbud,loomcrown,cindertray,kilnbarrow,keelkip,wakecradle,cairncricket,archspring,rivetfoil,gimbalcloak)
ABILITY_FUNCTIONS=tuple((lambda d,p,fn=fn:fn(d,p,ability=p)) for fn in FIELD_FUNCTIONS)

def mask(im):return Image.frombytes('L',im.size,bytes(255 if n else 0 for n in im.tobytes()))
def paste(target,sprite,xy):
    im=sprite if isinstance(sprite,Image.Image) else sprite.im
    target.paste(im.convert(target.mode),xy,mask(im))

def concept_sheet():
    OUT.mkdir(parents=True,exist_ok=True)
    sheet=Image.new('RGB',(800,310),RGB[P['deep']]);d=ImageDraw.Draw(sheet)
    d.text((12,8),'NORTHERN COMPANIONS / NATIVE SILHOUETTE REVIEW / ORIGINAL ART',fill=RGB[P['white']])
    for i,fn in enumerate(FIELD_FUNCTIONS):
        x=(i%5)*160;y=30+(i//5)*140
        d.text((x+6,y),f'{FORM_IDS[i]} {NAMES[i]}',fill=RGB[P['gold3']])
        for j,di in enumerate(DIRECTIONS):
            im=fn(di,0).im;paste(sheet,im.resize((32,32),Image.Resampling.NEAREST),(x+4+j*38,y+22))
            m=mask(im).resize((32,32),Image.Resampling.NEAREST)
            sheet.paste(Image.new('RGB',(32,32),RGB[P['ink']]),(x+4+j*38,y+70),m)
            # Light rectangle behind silhouette keeps all contour pixels readable.
            under=Image.new('RGB',(32,32),RGB[P['dirt4']]);under.paste(Image.new('RGB',(32,32),RGB[P['ink']]),(0,0),m);sheet.paste(under,(x+4+j*38,y+70))
        d.text((x+7,y+112),'D     U     L     R',fill=RGB[P['silver']])
    save_review(sheet,OUT/'silhouette_review.png')



def portrait_eye(a,x,y,look=1):
    a.p([(x+1,y),(x+3,y),(x+4,y+2),(x+3,y+5),(x+1,y+5),(x,y+3),(x,y+1)],'white')
    a.r((x+look,y+2,x+look+1,y+5),'ink');a.dot(x+look,y+2,'blue3')


def portrait_spoolbud():
    a=Art(32,32,'transparent')
    # Three root paws and a looping tail suggest a playful, living seed spool.
    for x,y in ((7,27),(21,26),(15,29)):
        a.p([(x,22),(x+3,22),(x+4,y),(x+2,y+2),(x-2,y+2),(x-3,y)],'wood0');a.l([(x+1,24),(x+2,y),(x,y+1)],'wood4',2)
    a.l([(24,18),(28,15),(29,10),(27,7),(24,7),(23,9),(25,10)],'pine0',3)
    a.l([(25,17),(27,14),(28,10),(26,8),(24,8)],'pine4')
    a.p([(8,10),(20,9),(25,12),(27,18),(25,24),(20,27),(9,26),(4,22),(3,16),(5,12)],'wood0')
    a.p([(8,11),(20,10),(24,13),(25,18),(23,23),(19,25),(10,25),(5,21),(4,16),(6,13)],'wood3')
    a.p([(8,12),(17,11),(19,15),(18,20),(14,24),(9,24),(5,20),(5,16)],'wood4')
    a.l([(20,11),(22,14),(21,19),(22,23)],'wood1',2);a.l([(24,14),(23,18),(24,20)],'wood5')
    a.l([(7,13),(6,17),(7,21)],'wood5')
    a.p([(10,12),(5,10),(2,5),(3,2),(8,3),(12,7),(13,11)],'pine0')
    a.p([(9,10),(5,8),(4,4),(7,4),(10,7)],'pine4');a.l([(5,4),(7,6),(10,9)],'mint')
    a.p([(15,11),(16,6),(20,3),(25,2),(26,5),(23,9),(18,12)],'pine0')
    a.p([(17,9),(19,6),(24,4),(23,7),(20,9)],'pine4');a.l([(18,8),(22,5),(24,4)],'pine5')
    portrait_eye(a,7,14,2);portrait_eye(a,15,13,1)
    a.l([(11,22),(13,23),(16,21)],'wood0');a.r((6,21,8,22),'rose4');a.r((19,20,21,21),'rose4');a.dot(12,12,'gold4')
    return a


def portrait_loomcrown():
    a=Art(32,32,'transparent')
    # Open antler-trellis belongs to an animal, with a smiling suspended seed.
    a.p([(5,26),(4,17),(6,10),(10,5),(16,3),(23,5),(27,11),(28,21),(26,28),(22,29),(23,24),(24,17),(22,10),(18,7),(13,7),(9,12),(8,20),(9,27)],'wood0')
    a.l([(6,25),(5,18),(7,11),(11,6),(16,5)],'wood4',2);a.l([(22,7),(25,12),(26,20),(24,27)],'wood3',2)
    a.l([(7,13),(22,12)],'pine2',2);a.l([(15,12),(16,17)],'wood5',2)
    a.l([(6,24),(3,29),(7,30),(10,28)],'wood0',2);a.l([(24,25),(28,29),(25,30),(22,29)],'wood0',2)
    a.l([(8,20),(3,18),(1,20),(2,23),(4,22)],'pine0',2);a.dot(2,20,'pine5')
    a.p([(11,17),(18,15),(22,18),(22,23),(19,27),(14,28),(10,25),(8,21)],'pine0')
    a.p([(12,18),(18,16),(20,18),(21,22),(18,26),(14,26),(10,23),(10,20)],'pine4')
    a.p([(12,18),(17,17),(18,19),(15,22),(11,22)],'pine5')
    portrait_eye(a,11,19,2);portrait_eye(a,17,18,1);a.l([(14,25),(16,26),(18,24)],'pine0');a.dot(10,24,'mint');a.dot(20,23,'mint')
    a.p([(12,7),(7,8),(2,6),(1,3),(5,1),(9,3),(13,5)],'pine0');a.p([(4,3),(7,3),(10,5),(7,6),(3,5)],'pine4');a.l([(4,3),(7,4),(9,5)],'mint')
    a.p([(18,6),(20,2),(24,1),(29,3),(29,6),(24,8),(20,8)],'pine0');a.p([(20,5),(23,3),(26,3),(27,5),(23,6)],'pine4');a.l([(22,4),(25,4)],'pine5')
    a.p([(14,5),(14,2),(16,1),(18,3),(17,5)],'wood0');a.dot(16,2,'gold3')
    return a


def portrait_cindertray():
    a=Art(32,32,'transparent')
    for x,y in ((7,25),(23,25),(11,28),(25,27)):
        a.p([(x-1,22),(x+2,22),(x+3,y),(x+1,y+2),(x-3,y+1)],'wood0');a.l([(x,24),(x+1,y),(x-1,y)],'fire2',2)
    a.l([(25,22),(29,20),(29,16),(27,14)],'wood0',3);a.l([(26,21),(28,19),(28,16)],'fire2')
    a.p([(5,18),(8,12),(13,6),(17,3),(21,7),(26,15),(28,20),(26,25),(22,27),(10,26),(5,23)],'wood0')
    a.p([(7,18),(10,12),(14,7),(17,5),(20,8),(25,16),(26,20),(24,24),(21,25),(11,24),(7,22)],'fire1')
    a.p([(10,14),(14,8),(17,6),(21,12),(23,17),(16,18),(8,19)],'fire2')
    a.l([(14,8),(17,7),(21,13)],'skin2',2);a.l([(7,19),(15,20),(25,18)],'wood0',2)
    a.l([(17,21),(21,21),(24,20)],'gold3');a.dot(18,22,'gold4');a.dot(23,21,'gold4')
    a.p([(6,16),(12,16),(16,19),(16,24),(12,28),(7,28),(3,25),(2,21),(3,18)],'wood0')
    a.p([(6,17),(11,17),(14,20),(14,24),(11,26),(7,26),(4,23),(4,20)],'fire3')
    portrait_eye(a,4,18,2);portrait_eye(a,11,19,1);a.l([(7,25),(9,26),(11,25)],'wood0');a.dot(3,24,'rose4');a.dot(14,25,'rose3')
    a.l([(6,17),(8,17)],'gold4');a.dot(20,10,'gold4')
    return a


def portrait_kilnbarrow():
    a=Art(32,32,'transparent')
    # Wide back and unfurled shell plates replace the triangular pup silhouette.
    for x,y in ((5,23),(24,23),(8,28),(23,28)):
        a.p([(x,19),(x+3,20),(x+3,y),(x+1,y+2),(x-3,y+2),(x-4,y)],'wood0');a.l([(x,23),(x+1,y),(x-2,y+1)],'fire2',2)
    a.l([(26,20),(29,17),(29,12),(27,10)],'wood0',3);a.l([(27,18),(28,16),(28,12)],'fire3')
    a.p([(7,11),(13,8),(21,9),(26,12),(28,17),(26,23),(21,26),(12,25),(6,22),(3,17)],'wood0')
    a.p([(8,12),(13,10),(21,10),(25,13),(26,17),(24,22),(20,24),(12,23),(7,21),(5,17)],'fire1')
    a.l([(14,12),(16,16),(15,21)],'wood0',2);a.l([(20,13),(21,17),(20,22)],'fire0',2)
    a.l([(17,16),(23,15)],'gold3',2);a.l([(18,18),(23,17)],'gold4')
    a.p([(8,11),(9,7),(14,3),(20,2),(25,5),(27,9),(23,12),(16,13)],'wood0')
    a.p([(10,10),(11,7),(15,5),(20,4),(23,6),(25,9),(22,10),(16,11)],'fire2')
    a.l([(12,7),(16,5),(20,5),(23,7)],'skin2',2);a.l([(14,9),(19,10),(23,9)],'fire0')
    a.p([(4,15),(10,14),(15,17),(16,22),(13,27),(8,29),(3,27),(1,23),(1,19)],'wood0')
    a.p([(4,17),(9,16),(13,18),(14,22),(12,25),(8,27),(4,25),(3,22),(3,19)],'fire3')
    portrait_eye(a,3,18,2);portrait_eye(a,10,18,1);a.l([(6,25),(8,26),(11,24)],'wood0');a.r((3,24,5,25),'rose4');a.dot(13,24,'rose3')
    a.l([(5,17),(8,16)],'gold4');a.dot(22,6,'gold4')
    return a


def portrait_keelkip():
    a=Art(32,32,'transparent')
    a.p([(20,21),(25,17),(29,17),(31,20),(27,24),(22,25)],'water0');a.p([(23,21),(26,19),(29,19),(27,22),(24,23)],'water3');a.l([(25,20),(28,19)],'watergleam')
    a.p([(7,13),(14,12),(20,16),(25,22),(23,26),(17,28),(9,27),(4,24),(3,18)],'water0')
    a.p([(7,15),(13,13),(18,16),(23,22),(21,25),(16,26),(9,25),(5,23),(5,18)],'blue2')
    a.p([(9,18),(15,17),(19,20),(21,23),(17,25),(10,24),(7,22)],'blue3')
    a.l([(16,18),(14,22),(16,25)],'water4',2);a.l([(20,21),(18,24),(19,25)],'water1')
    a.p([(10,23),(14,22),(16,25),(14,29),(8,30),(5,28),(6,25)],'water0');a.p([(9,25),(13,24),(14,26),(12,28),(8,28),(7,27)],'water3');a.l([(8,26),(11,25)],'watergleam')
    a.p([(7,5),(13,4),(18,7),(20,12),(18,18),(14,21),(8,21),(3,18),(1,13),(2,9)],'water0')
    a.p([(7,7),(13,6),(16,8),(18,12),(16,17),(13,19),(8,19),(4,17),(3,13),(4,10)],'blue3')
    a.p([(8,6),(12,6),(14,8),(11,10),(6,10)],'water4');a.l([(8,7),(11,7)],'watergleam')
    portrait_eye(a,4,10,2);portrait_eye(a,12,10,1)
    a.p([(8,16),(11,16),(10,18),(9,18)],'ink');a.l([(7,18),(9,19),(11,19),(13,17)],'water1');a.l([(2,16),(5,16)],'watergleam');a.l([(15,16),(18,15)],'watergleam');a.dot(4,18,'rose5')
    return a


def portrait_wakecradle():
    a=Art(32,32,'transparent')
    # Tall seal rises between open crescent flippers; full silhouette is U-shaped.
    a.p([(12,19),(8,17),(5,12),(3,10),(1,13),(1,20),(4,26),(9,30),(14,29),(16,25)],'water0')
    a.p([(11,21),(7,19),(4,15),(3,13),(3,19),(6,25),(10,28),(13,27),(14,25)],'blue2');a.l([(4,19),(6,23),(10,26)],'watergleam',2)
    a.p([(18,20),(22,17),(26,10),(28,7),(30,9),(30,17),(27,24),(23,28),(18,29),(15,26)],'water0')
    a.p([(19,22),(23,19),(27,12),(28,10),(28,17),(25,23),(21,26),(18,27),(17,25)],'blue3');a.l([(27,16),(25,21),(22,23)],'watergleam',2)
    a.l([(10,26),(15,28),(22,25)],'water0',3);a.l([(10,25),(15,26),(21,24)],'water4',2)
    a.p([(12,9),(17,8),(21,12),(20,16),(18,19),(18,22),(16,25),(13,24),(12,21),(13,17),(10,14)],'water0')
    a.p([(13,10),(17,10),(19,12),(18,16),(16,19),(16,22),(14,23),(14,18),(12,14)],'blue3')
    a.p([(11,2),(16,1),(21,4),(23,8),(21,12),(18,14),(13,14),(9,12),(7,8),(8,4)],'water0')
    a.p([(11,4),(16,3),(20,5),(21,8),(19,11),(17,12),(13,12),(10,10),(9,7),(10,5)],'blue3')
    portrait_eye(a,10,5,2);portrait_eye(a,17,5,1);a.p([(14,10),(17,10),(16,12),(15,12)],'ink');a.dot(12,11,'watergleam');a.dot(20,10,'water4');a.l([(13,4),(16,4)],'watergleam')
    a.l([(14,16),(16,16)],'watergleam');a.dot(28,11,'water4');a.dot(7,25,'water4')
    return a


def portrait_cairncricket():
    a=Art(32,32,'transparent')
    a.p([(18,14),(23,12),(28,18),(27,22),(23,27),(28,29),(27,31),(20,30),(18,27),(23,21),(21,18)],'stone0')
    a.l([(22,15),(26,19),(24,23),(21,27),(24,29)],'wood4',2);a.dot(24,17,'stone5')
    a.l([(12,21),(8,26),(4,27),(3,29)],'stone0',3);a.l([(11,22),(8,25),(5,26)],'stone4')
    a.p([(13,11),(18,8),(23,9),(26,13),(24,17),(20,19),(15,18),(11,15)],'stone0')
    a.p([(14,12),(18,10),(22,10),(24,13),(23,15),(19,17),(15,16),(13,14)],'wood4');a.l([(17,11),(21,11),(23,13)],'stone5')
    a.p([(16,19),(20,20),(24,18),(24,21),(21,23),(16,22),(14,21)],'stone0');a.l([(16,20),(20,21),(23,19)],'stone4')
    a.l([(9,13),(5,8),(4,3),(6,1)],'stone0',2);a.dot(6,1,'gold3');a.l([(14,12),(15,6),(19,2),(21,2)],'stone0',2);a.dot(21,2,'gold2')
    a.p([(7,12),(12,11),(17,14),(19,18),(17,23),(12,26),(7,25),(2,21),(1,17),(3,14)],'stone0')
    a.p([(7,14),(12,13),(15,15),(17,18),(15,22),(12,24),(7,23),(4,20),(3,17),(5,15)],'stone4')
    portrait_eye(a,4,15,2);portrait_eye(a,11,15,1);a.l([(7,22),(10,23),(13,21)],'wood0');a.r((3,21,5,22),'gold2');a.dot(15,22,'gold3');a.l([(8,13),(11,13)],'stone5')
    return a


def portrait_archspring():
    a=Art(32,32,'transparent')
    # Bent cricket haunches, antennae and low suspended face, unlike Archwarden.
    a.p([(12,12),(10,6),(6,3),(3,5),(0,12),(1,18),(4,25),(3,29),(7,30),(9,27),(6,20),(4,15),(6,10),(8,12),(10,16)],'stone0')
    a.l([(10,12),(8,7),(5,6),(2,12),(3,17),(6,24),(6,28)],'wood4',2);a.l([(5,7),(4,10)],'stone5')
    a.p([(18,12),(20,5),(25,2),(29,5),(31,11),(30,18),(27,24),(28,29),(24,30),(22,27),(25,20),(27,14),(26,9),(23,8),(21,15)],'stone0')
    a.l([(20,12),(22,6),(25,4),(28,6),(29,11),(28,17),(25,24),(25,28)],'wood4',2);a.l([(24,5),(26,5),(28,8)],'stone5')
    a.l([(9,14),(15,12),(23,14)],'stone0',2);a.l([(15,13),(15,18)],'gold2',2)
    a.l([(12,18),(10,12),(11,8),(13,5)],'stone0',2);a.dot(13,5,'gold3');a.l([(19,18),(22,12),(20,8),(20,5)],'stone0',2);a.dot(20,5,'gold3')
    a.p([(11,17),(17,15),(22,18),(24,22),(22,27),(17,30),(12,28),(8,24),(7,21)],'stone0')
    a.p([(11,19),(17,17),(20,19),(22,22),(20,26),(17,28),(12,26),(9,23),(9,21)],'stone4')
    portrait_eye(a,10,19,2);portrait_eye(a,17,18,1);a.l([(13,26),(16,27),(19,25)],'wood0');a.r((9,25,11,26),'gold2');a.dot(21,24,'gold3')
    a.l([(13,18),(16,17)],'stone5');a.dot(16,29,'gold2')
    return a


def portrait_rivetfoil():
    a=Art(32,32,'transparent')
    for x,y in ((12,27),(21,26)):
        a.l([(x,22),(x-1,y),(x-3,y+2),(x+1,y+2)],'wood0',2);a.dot(x-1,y,'gold3')
    a.p([(22,18),(27,12),(29,12),(30,16),(27,21),(23,23)],'stone0');a.p([(24,18),(27,14),(28,14),(28,17),(25,20)],'silver')
    a.p([(11,6),(16,3),(22,6),(26,12),(26,18),(22,24),(16,27),(9,25),(5,20),(4,14),(6,9)],'stone0')
    a.p([(11,8),(16,5),(21,7),(24,12),(24,18),(20,22),(16,25),(10,23),(7,19),(6,14),(8,10)],'silver')
    a.p([(17,12),(22,8),(25,13),(24,18),(18,22),(13,20),(13,16)],'stone0')
    a.p([(18,13),(21,10),(23,13),(22,17),(18,20),(15,18)],'blue3');a.l([(17,13),(17,16),(20,18)],'white');a.l([(21,13),(20,16)],'blue2')
    a.p([(7,14),(2,16),(1,18),(7,20),(10,18)],'wood0');a.p([(7,16),(4,17),(7,18),(9,17)],'gold3')
    portrait_eye(a,7,11,1);portrait_eye(a,14,9,1);a.l([(10,9),(12,8),(15,7)],'white');a.dot(9,21,'gold2');a.dot(10,21,'gold4')
    a.l([(17,23),(19,26),(18,28)],'stone0');a.p([(17,27),(20,28),(19,30),(16,29)],'gold2');a.dot(18,28,'gold4')
    return a


def portrait_gimbalcloak():
    a=Art(32,32,'transparent')
    # Huge pleated bird wings frame a hollow gimbal at its breast.
    a.p([(13,12),(10,5),(4,1),(2,3),(4,10),(1,9),(0,15),(3,21),(9,25),(14,20)],'stone0')
    a.p([(11,12),(8,6),(4,3),(6,12),(2,11),(2,15),(5,20),(9,22),(12,18)],'silver')
    a.l([(6,10),(8,15),(10,16)],'white',2);a.l([(3,14),(6,18),(9,20)],'blue3')
    a.p([(18,11),(23,3),(28,1),(30,4),(27,11),(30,10),(31,16),(28,22),(23,25),(17,20)],'stone0')
    a.p([(20,12),(24,5),(28,3),(28,5),(25,13),(29,12),(29,16),(26,21),(23,22),(19,18)],'blue2')
    a.l([(25,10),(23,15),(21,16)],'blue3',2);a.l([(28,14),(26,18),(23,21)],'white')
    a.e((10,19,23,31),'wood0');a.e((12,21,21,29),'gold2');a.e((14,23,19,27),'transparent');a.l([(13,22),(15,21),(18,21)],'gold4');a.l([(21,24),(20,27),(18,29)],'gold0')
    a.p([(11,7),(17,5),(22,8),(24,13),(22,18),(18,22),(12,20),(8,16),(7,12)],'stone0')
    a.p([(11,9),(17,7),(20,9),(22,13),(20,17),(17,20),(12,18),(10,15),(9,12)],'silver')
    portrait_eye(a,10,10,2);portrait_eye(a,17,9,1);a.p([(13,16),(17,15),(18,17),(15,20),(13,18)],'wood0');a.p([(14,16),(16,16),(16,18),(15,18)],'gold3')
    a.l([(12,8),(16,7)],'white');a.dot(10,17,'blue3');a.dot(21,16,'blue3')
    a.l([(10,23),(7,27),(5,27)],'stone0',2);a.dot(7,27,'gold2');a.l([(23,23),(27,26),(29,26)],'stone0',2);a.dot(27,26,'gold2')
    return a

PORTRAIT_FUNCTIONS=(portrait_spoolbud,portrait_loomcrown,portrait_cindertray,portrait_kilnbarrow,portrait_keelkip,portrait_wakecradle,portrait_cairncricket,portrait_archspring,portrait_rivetfoil,portrait_gimbalcloak)


def save_indexed(im,path):im.save(path,transparency=0,optimize=False)

def save_review(im,path):
    # Fixed-palette review compression preserves native sprite pixels exactly.
    palette=Image.new('P',(1,1));palette.putpalette(PAL)
    im.quantize(palette=palette,dither=Image.Dither.NONE).save(path,optimize=True)

def make_previews(fields,abilities,portraits):
    concept_sheet()
    walk=Art(640,64,'transparent').im;cast=Art(320,64,'transparent').im
    for i,key in enumerate(KEYS):
        w=Art(64,64,'transparent').im;c=Art(32,64,'transparent').im
        for d in range(4):
            for f in range(4):w.paste(fields[i][d][f].im,(f*16,d*16))
            for f in range(2):c.paste(abilities[i][d][f].im,(f*16,d*16))
        save_indexed(w,OUT/f'{key}_walk.png');save_indexed(c,OUT/f'{key}_ability.png');save_indexed(portraits[i].im,OUT/f'{key}_portrait.png')
        walk.paste(w,(i*64,0));cast.paste(c,(i*32,0))
    save_indexed(walk,OUT/'walk_sheet.png');save_indexed(cast,OUT/'ability_sheet.png')
    # Five family columns: bases above, evolved companions directly beneath.
    contact=Image.new('RGB',(1000,620),RGB[P['deep']]);cd=ImageDraw.Draw(contact)
    cd.text((12,8),'ORIGINAL NORTHERN COMPANIONS / 160 WALK POSES + 80 CAST POSES + 10 PORTRAITS / ART ONLY',fill=RGB[P['white']])
    for i in range(10):
        x=(i//2)*200;y=28+(i%2)*292
        cd.text((x+8,y),f'{FORM_IDS[i]}  {NAMES[i]}',fill=RGB[P['gold3']])
        paste(contact,portraits[i].im.resize((96,96),Image.Resampling.NEAREST),(x+50,y+18))
        cd.text((x+8,y+117),'D/U/L/R: walk x4 + cast x2',fill=RGB[P['silver']])
        for d in range(4):
            for f,sp in enumerate(fields[i][d]+abilities[i][d]):paste(contact,sp.im.resize((32,32),Image.Resampling.NEAREST),(x+1+f*33,y+136+d*34))
    save_review(contact,OUT/'contact_sheet.png')
    native=Image.new('RGB',(720,438),RGB[P['night']]);nd=ImageDraw.Draw(native)
    nd.text((8,5),'NATIVE 16x16 + 32x32 / DARK AND LIGHT PIXEL REVIEW',fill=RGB[P['white']])
    for bg,yy,fg in (('deep',25,'white'),('dirt4',230,'ink')):
        nd.rectangle((0,yy,719,yy+202),fill=RGB[P[bg]])
        for i in range(10):
            x=(i//2)*144;y=yy+(i%2)*100
            nd.text((x+3,y+3),NAMES[i],fill=RGB[P[fg]])
            for d in range(4):
                for f,sp in enumerate(fields[i][d]+abilities[i][d]):paste(native,sp,(x+2+f*16,y+20+d*16))
            paste(native,portraits[i],(x+104,y+24))
    save_review(native,OUT/'native_dark_light.png');save_review(native.resize((1440,876),Image.Resampling.NEAREST),OUT/'native_dark_light_2x.png')
    # A native-pixel motion proof, not an emulator capture.
    frames=[]
    for f in range(4):
        im=Image.new('RGB',(720,232),RGB[P['dirt4']]);ad=ImageDraw.Draw(im)
        ad.text((7,5),'ORIGINAL ART / NATIVE WALK AND CAST MOTION',fill=RGB[P['ink']])
        for i in range(10):
            x=(i//2)*144;y=26+(i%2)*99
            ad.text((x+4,y),NAMES[i],fill=RGB[P['ink']])
            for d in range(4):paste(im,fields[i][d][f],(x+8+d*30,y+22));paste(im,abilities[i][d][f%2],(x+8+d*30,y+52))
        frames.append(im)
    frames[0].save(OUT/'motion_native.gif',save_all=True,append_images=frames[1:],duration=150,loop=0,disposal=2,optimize=False)



def make_scene_review(fields,abilities):
    """Exact 1:1 sprites over actual chapter grass/water/timber. Art proof only."""
    sources=(('GRASS',ROOT/'assets/northern_region/headland_roads.png',(118,170,150,202)),
             ('WATER',ROOT/'assets/northern_region/hearthwake_quay.png',(116,271,148,303)),
             ('TIMBER',ROOT/'assets/northern_region/hearthwake_quay.png',(104,190,136,222)))
    patches=[];provenance=[]
    for name,path,box in sources:
        with Image.open(path) as im:patches.append(im.convert('RGB').crop(box))
        provenance.append({'terrain':name,'path':str(path.relative_to(ROOT)),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'crop':list(box)})
    sheet=Image.new('RGB',(692,558),RGB[P['deep']]);draw=ImageDraw.Draw(sheet)
    draw.text((8,7),'ART COMPOSITE / ACTUAL CHAPTER TERRAINS / 1:1 PIXELS / NOT GAMEPLAY',fill=RGB[P['white']])
    for terrain,(name,_,_) in enumerate(sources):draw.text((114+terrain*192,26),name+'  WALK x4 + CAST x2',fill=RGB[P['gold3']])
    for i in range(10):
        y=48+i*50;draw.text((5,y+5),NAMES[i],fill=RGB[P['white']])
        for j,d in enumerate((0,2)):
            for t,patch in enumerate(patches):
                for f,sp in enumerate(fields[i][d]+abilities[i][d]):
                    tile=patch.crop((4,4,28,28));paste(tile,sp,(4,4));sheet.paste(tile,(114+t*192+f*30,y+j*24))
    save_review(sheet,OUT/'scene_readability_native.png')
    save_review(sheet.resize((1384,1116),Image.Resampling.NEAREST),OUT/'scene_readability_2x.png')
    return provenance

def emit_code(fields,abilities,portraits):
    upper=', '.join('NORTHERN_CREATURE_'+key.upper() for key in KEYS)
    header=f'''/* Generated original art; edit assets/generate_northern_creatures.py. */
#ifndef EMBERBOND_NORTHERN_CREATURE_ART_H
#define EMBERBOND_NORTHERN_CREATURE_ART_H
#define NORTHERN_CREATURE_ART_COUNT 10
#define NORTHERN_CREATURE_ART_FRAME_BYTES 256
#define NORTHERN_CREATURE_ART_PORTRAIT_BYTES 1024
#define NORTHERN_CREATURE_ART_DIRECTION_COUNT 4
#define NORTHERN_CREATURE_ART_WALK_FRAME_COUNT 4
#define NORTHERN_CREATURE_ART_ABILITY_FRAME_COUNT 2
enum {{ {upper} }};
/* Stable, noncontiguous form IDs: 19,20,22,23,73,74,75,76,77,78.
 * Directions: down/up/left/right. Four walk beats, two cast poses per direction.
 * Native row-major 8bpp palette indices. Transparent zero. Field anchor (8,8).
 * Existing 178-entry game_palette, no runtime palette mutation or buffers.
 * All art lives in const ROM: no mutable data/BSS. No gameplay unlocks.
 */
extern const unsigned char northern_creature_form_ids[NORTHERN_CREATURE_ART_COUNT];
extern const unsigned char northern_creature_direction_frames[NORTHERN_CREATURE_ART_COUNT][4][4][256];
extern const unsigned char northern_creature_ability_frames[NORTHERN_CREATURE_ART_COUNT][4][2][256];
extern const unsigned char northern_creature_portraits[NORTHERN_CREATURE_ART_COUNT][1024];
/* Unsupported IDs return -1/NULL. Invalid direction or pose returns NULL. */
int northern_creature_art_index(unsigned int form_id);
const unsigned char *northern_creature_art_frame(unsigned int form_id,unsigned int direction,unsigned int frame);
const unsigned char *northern_creature_art_ability_frame(unsigned int form_id,unsigned int direction,unsigned int pose);
const unsigned char *northern_creature_art_portrait(unsigned int form_id);
#endif
'''
    (SRC/'northern_creature_art.h').write_text(header)
    buf=io.StringIO();buf.write('const unsigned char northern_creature_form_ids[10] = {'+','.join(map(str,FORM_IDS))+'};\n\n')
    base.emit_image_tensor(buf,'northern_creature_direction_frames',fields,[10,4,4,256])
    base.emit_image_tensor(buf,'northern_creature_ability_frames',abilities,[10,4,2,256])
    base.emit_image_tensor(buf,'northern_creature_portraits',portraits,[10,1024])
    chunks=[];lines=[];size=0
    for line in buf.getvalue().splitlines(keepends=True):
        n=len(line.encode())
        if lines and size+n>30000:chunks.append(''.join(lines));lines=[];size=0
        lines.append(line);size+=n
    if lines:chunks.append(''.join(lines))
    folder=SRC/'northern_creature_art_data';folder.mkdir(exist_ok=True)
    for old in folder.glob('part_*.inc'):old.unlink()
    for i,chunk in enumerate(chunks):(folder/f'part_{i:03d}.inc').write_text(chunk)
    code='#include "northern_creature_art.h"\n/* Generated original ROM pixels. */\n'
    code+=''.join(f'#include "northern_creature_art_data/part_{i:03d}.inc"\n' for i in range(len(chunks)))
    code+='\nint northern_creature_art_index(unsigned int form_id) {\n    switch(form_id) {\n'
    code+=''.join(f'    case {id}: return NORTHERN_CREATURE_{key.upper()};\n' for id,key in zip(FORM_IDS,KEYS))
    code+='''    default: return -1;
    }
}
const unsigned char *northern_creature_art_frame(unsigned int form_id,unsigned int direction,unsigned int frame) {
    int i=northern_creature_art_index(form_id);
    if(i<0 || direction>=4 || frame>=4) return (const unsigned char *)0;
    return northern_creature_direction_frames[i][direction][frame];
}
const unsigned char *northern_creature_art_ability_frame(unsigned int form_id,unsigned int direction,unsigned int pose) {
    int i=northern_creature_art_index(form_id);
    if(i<0 || direction>=4 || pose>=2) return (const unsigned char *)0;
    return northern_creature_ability_frames[i][direction][pose];
}
const unsigned char *northern_creature_art_portrait(unsigned int form_id) {
    int i=northern_creature_art_index(form_id);
    return i<0 ? (const unsigned char *)0 : northern_creature_portraits[i];
}
'''
    (SRC/'northern_creature_art.c').write_text(code)
    return [len(c.encode()) for c in chunks]


def validate_pixels(fields,abilities,portraits):
    sprites=[sp for forms in (fields,abilities) for row in forms for direction in row for sp in direction]+portraits
    for sp in sprites:
        im=sp.im;assert im.mode=='P' and im.getpalette()==PAL
        assert im.size in ((16,16),(32,32)) and 0 in im.tobytes()
        assert max(im.tobytes())<base.BASE_PALETTE_SIZE
        assert im.getpixel((0,0))==0 and im.getpixel((im.width-1,0))==0
    for i,rows in enumerate(fields):
        assert len({mask(r[0].im).tobytes() for r in rows})==4,(NAMES[i],'direction silhouettes')
        for d,row in enumerate(rows):
            action=abilities[i][d]
            assert len({s.im.tobytes() for s in row+action})==6,(NAMES[i],DIRECTIONS[d],'six poses')
            assert len({mask(s.im).tobytes() for s in row})==4,(NAMES[i],DIRECTIONS[d],'four silhouettes')
            assert len({mask(s.im).tobytes() for s in action})==2,(NAMES[i],DIRECTIONS[d],'two cast silhouettes')
            assert all(60<=sum(bool(n) for n in sp.im.tobytes())<=215 for sp in row+action)
        assert portraits[i].im.tobytes()!=rows[0][0].im.resize((32,32),Image.Resampling.NEAREST).tobytes()
    assert len({mask(rows[0][0].im).tobytes() for rows in fields})==10
    return {'field_dimensions':[10,4,4,256],'ability_dimensions':[10,4,2,256],'portrait_dimensions':[10,1024],
            'palette_entries':178,'existing_actor_palette_only':True,'transparent_zero':True,
            'palette_indices':sorted({n for s in sprites for n in s.im.tobytes()}),
            'distinct_direction_silhouettes_per_form':4,'distinct_walk_silhouettes_per_direction':4,
            'additional_cast_poses_per_direction':2,'distinct_form_silhouettes':10,'independent_portraits':True}

MOTIONS=(
 'Three root paws alternate under a rolling living seed-bobbin; loose vine curls',
 'Tall antler-trellis sways on two root feet around a suspended expressive seed',
 'Ceramic tortoise pup rocks on four paws; tail curls as its shell stores warmth',
 'Long ceramic salamander steps on broad bent legs; hinged shell opens sideways',
 'Seal pup paddles with asymmetric skates and overlapping translucent belly ribs',
 'Long-necked seal rocks inside two curved flippers and an open water sling',
 'Stone cricket hops on a long folded haunch; antennae frame its curious face',
 'Tall cricket opens and closes paired arching haunches around its hanging thorax',
 'Folded metal wren skips on forked toes; pleated wings and pendulum swing',
 'Wide metal bird canopy flexes above an open breast-gimbal and stepping talons')


def output_hashes():
    files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='validation.json')
    files+=sorted((SRC/'northern_creature_art_data').glob('*.inc'))+[SRC/'northern_creature_art.c',SRC/'northern_creature_art.h']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def generate():
    OUT.mkdir(parents=True,exist_ok=True)
    fields=[[[fn(d,f) for f in range(4)] for d in DIRECTIONS] for fn in FIELD_FUNCTIONS]
    abilities=[[[fn(d,p) for p in range(2)] for d in DIRECTIONS] for fn in ABILITY_FUNCTIONS]
    portraits=[fn() for fn in PORTRAIT_FUNCTIONS]
    validation=validate_pixels(fields,abilities,portraits)
    chunks=emit_code(fields,abilities,portraits);make_previews(fields,abilities,portraits)
    scene_sources=make_scene_review(fields,abilities)
    png_sizes={p.name:p.stat().st_size for p in sorted(OUT.glob('*.png'))}
    assert max(png_sizes.values())<70000,png_sizes
    manifest={'schema_version':1,'generator':'assets/generate_northern_creatures.py','form_ids':list(FORM_IDS),'names':list(NAMES),'directions':list(DIRECTIONS),
              'status':'ART ONLY. Native rendering, catalog enablement, acquisition and powers are separate integration work.',
              'rights':'Original code-native pixel art, authored from pixel geometry. No extracted game art, tracing, downloaded or generated raster creature inputs.',
              'palette_sha256':hashlib.sha256(json.dumps(base.COLORS).encode()).hexdigest(),
              'data_bytes':71690,'runtime_data_bytes':0,'runtime_bss_bytes':0,'include_bytes':chunks,'max_include_bytes':max(chunks),
              'scene_review_sources':scene_sources,'anchor':[8,8],'frame_ticks_suggestion':8,'ability_poses':['gather','release'],'motions':list(MOTIONS),'png_sizes':png_sizes,'validation':validation}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'CREDITS.txt').write_text(manifest['rights']+'\nAll pixels authored at native resolution in Python/Pillow.\nExisting 178-entry RGB555 game palette reused verbatim; no extra palette.\nPreviews are art reviews, not emulator screenshots or proof of playable acquisition.\n')
    return manifest


def verify(manifest):
    before=output_hashes();generate();assert before==output_hashes(),'Nondeterministic regeneration'
    report={'deterministic_regeneration':True,'pixel_validation':manifest['validation'],'output_sha256':output_hashes()}
    with tempfile.TemporaryDirectory(prefix='northern-art-') as td:
        td=Path(td);arm=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc'
        if not arm.exists():
            arm=shutil.which('arm-none-eabi-gcc')
            if not arm:raise RuntimeError('ARM toolchain missing; target budget not verified')
        obj=td/'northern_art.o'
        subprocess.run([str(arm),'-std=c99','-mcpu=arm7tdmi','-mthumb','-O2','-ffreestanding','-fno-builtin','-fstack-usage','-Wall','-Wextra','-Werror','-c',str(SRC/'northern_creature_art.c'),'-o',str(obj)],check=True,capture_output=True)
        size=subprocess.check_output([str(arm).replace('gcc','size'),str(obj)],text=True)
        sections=list(map(int,size.splitlines()[-1].split()[:3]));assert sections[1:]==[0,0] and sections[0]<=73728
        stack=[int(line.split('\t')[1]) for p in td.glob('*.su') for line in p.read_text().splitlines()]
        assert stack and max(stack)<=24
        report.update({'arm_compile':'passed','arm_rom_object_bytes':sections[0],'arm_data_bytes':sections[1],'arm_bss_bytes':sections[2],'max_arm_stack_bytes':max(stack),'max_include_bytes':manifest['max_include_bytes']})
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return {k:v for k,v in report.items() if k not in ('output_sha256','pixel_validation')}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');parser.add_argument('--concept',action='store_true');args=parser.parse_args()
    if args.concept:concept_sheet();return
    manifest=generate();print(json.dumps(verify(manifest) if args.verify else {'generated_forms':FORM_IDS,'data_bytes':manifest['data_bytes'],'max_include_bytes':manifest['max_include_bytes']},indent=2))

if __name__=='__main__':main()
