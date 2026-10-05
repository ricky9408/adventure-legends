#!/usr/bin/env python3
"""Original, deterministic evolved companion art for Adventure Legends.

Uses existing palette indices only. No extracted/traced raster inputs. Field art
is authored directly at 16x16; portraits are separately authored at 32x32.
Run: python3 assets/generate_evolutions.py [--verify]
Only writes assets/evolutions and src/evolution_art.{h,c}/evolution_art_data.
Art and scene mockups alone do not implement playable evolution.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import io
import json
import subprocess
import sys
import tempfile
from PIL import Image, ImageDraw, ImageFont

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'assets/evolutions'
SRC = ROOT / 'src'
DIRECTIONS = ('down', 'up', 'left', 'right')
FORM_IDS = (2, 5, 8, 11)
NAMES = ('Homura Hearthkeeper', 'Midori Canopykeeper', 'Fuuri Windweaver', 'Kohaku Archwarden')
KEYS = ('hearthkeeper', 'canopykeeper', 'windweaver', 'archwarden')


def load_module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


base = load_module('evolution_base', ROOT / 'assets/generate_assets.py')
Art, P, PAL, RGB = base.Art, base.P, base.PAL, base.rgb
assert base.BASE_PALETTE_SIZE == 97


def mirrored(a):
    a.im = a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
    a.d = ImageDraw.Draw(a.im)
    return a


def hearthkeeper(direction, frame):
    """Low ceramic-mantled fox; three ash fins and exactly one wick tail."""
    a = Art(16, 16, 'transparent')
    lift = -1 if frame == 2 else 0
    wag = (0, -1, 0, 1)[frame]
    def p(pts, c): a.p([(x, y + lift) for x, y in pts], c)
    def l(pts, c): a.l([(x, y + lift) for x, y in pts], c)
    def dot(x, y, c): a.dot(x, y + lift, c)
    if direction in ('left', 'right'):
        # Left profile: broad mantle is behind the forward cheek and muzzle.
        a.p([(11,10),(13,9),(13,6+wag),(15,5+wag),(15,10),(13,12),(11,12)],'ink')
        a.l([(12,10),(14,9),(14,7+wag)],'fire2',2)
        a.dot(14,6+wag,'white')
        for x, phase in ((4, frame == 1), (10, frame == 3)):
            a.r((x,12,x+1,14-int(phase)),'ink')
            a.dot(x,13-int(phase),'fire2')
        p([(4,7),(7,5),(11,5),(13,8),(12,12),(5,12),(3,10)],'ink')
        p([(5,7),(8,6),(11,6),(12,8),(11,11),(5,11)],'fire0')
        p([(5,7),(8,6),(11,6),(11,8),(9,10),(5,9)],'white')
        l([(5,10),(9,11),(11,9)],'wood3')
        dot(8,8,'gold2')
        # Three separately readable ash fins; the head ears remain orange.
        for x, y in ((6,4),(9,3),(12,4)):
            p([(x-1,y+2),(x,y),(x+1,y+2),(x+1,y+3)],'slate')
            dot(x,y+1,'silver')
        p([(1,7),(1,3),(3,4),(4,6),(5,4),(6,5),(6,9),(4,12),(2,11),(0,9),(0,8)],'ink')
        p([(2,7),(2,5),(3,7),(5,6),(5,9),(3,11),(1,9),(1,8)],'fire2')
        l([(1,9),(3,10),(4,9)],'white')
        dot(3,8,'ink'); dot(0,9,'ink'); dot(2,5,'rose2')
        if direction == 'right': mirrored(a)
    else:
        a.p([(11,10),(13,8+wag),(13,5+wag),(15,6+wag),(14,11),(12,13),(10,12)],'ink')
        a.l([(11,11),(13,10),(14,7+wag)],'fire2')
        a.dot(14,6+wag,'white')
        for x, phase in ((4, frame == 1), (10, frame == 3)):
            a.r((x,11,x+1,14-int(phase)),'ink');a.dot(x,13-int(phase),'fire2')
        p([(2,6),(4,4),(11,4),(13,7),(12,11),(10,12),(4,12),(2,10)],'ink')
        p([(3,6),(5,5),(10,5),(12,7),(11,10),(4,10)],'fire0')
        p([(3,6),(5,5),(10,5),(11,7),(10,9),(4,9)],'white')
        l([(3,9),(5,10),(10,10),(12,9)],'wood3')
        for x,y in ((3,3),(7,2),(11,3)):
            p([(x-1,y+2),(x,y),(x+1,y+2),(x+1,y+3)],'slate')
            dot(x,y+1,'silver')
        if direction == 'down':
            p([(4,9),(4,6),(6,7),(9,7),(11,6),(11,10),(9,13),(6,13),(3,11)],'ink')
            p([(5,9),(5,8),(7,9),(9,8),(10,8),(10,10),(8,12),(6,12),(4,10)],'fire2')
            l([(5,11),(7,12),(9,11)],'white')
            dot(5,10,'ink');dot(10,10,'ink');dot(7,11,'ink')
        else:
            p([(4,6),(4,3),(6,5),(9,5),(11,3),(11,6),(9,8),(6,8)],'ink')
            p([(5,5),(5,4),(6,6),(9,6),(10,4),(10,6),(8,7),(6,7)],'fire2')
            l([(5,9),(7,10),(10,9)],'fire0');dot(7,9,'gold2')
    return a


def canopykeeper(direction, frame):
    """Three teal leaves form an inverted canopy over a suspended blue seed."""
    a=Art(16,16,'transparent')
    bob=(0,-1,0,0)[frame]; lean=(0,0,1,-1)[frame]
    side=direction in ('left','right')
    def p(pts,c):a.p([(x,y+bob) for x,y in pts],c)
    def l(pts,c):a.l([(x,y+bob) for x,y in pts],c)
    def dot(x,y,c):a.dot(x,y+bob,c)
    # A quiet empty band makes the seed visibly hang rather than form a torso.
    seedx=8 if side else 7
    l([(7,7),(seedx,10)],'teal0')
    l([(seedx,8),(seedx,10)],'water4')
    # Back/center leaf has its own pointed silhouette.
    p([(5,6),(5,3),(7,1),(9,2),(11,5),(9,7)],'ink')
    p([(6,5),(6,3),(7,2),(9,3),(10,5),(8,6)],'teal1')
    l([(7,2),(7,5),(8,6)],'water4')
    # Outer leaves open on alternate beats, with no whole-sprite scaling.
    ly=(0,1,0,-1)[frame];ry=(0,-1,1,0)[frame]
    p([(7,6),(4,3+ly),(1,3+ly),(0,5+ly),(2,7),(6,8),(8,7)],'ink')
    p([(6,6),(4,4+ly),(1,4+ly),(2,6),(6,7)],'teal1')
    l([(1,4+ly),(4,5+ly),(6,6)],'teal2');dot(2,4+ly,'water4')
    p([(7,6),(10,4+ry),(14,3+ry),(15,5+ry),(13,7),(9,8),(7,7)],'ink')
    p([(9,6),(11,5+ry),(14,4+ry),(13,6),(10,7)],'teal2')
    l([(10,6),(12,5+ry),(14,4+ry)],'water4')
    # Woven hem is a shallow V under the canopy, not a solid skirt.
    l([(2,7),(4,8),(6,7),(8,8),(10,7),(12,8),(14,6)],'teal0')
    dot(4,7,'water4');dot(11,7,'water4')
    p([(seedx-1,10),(seedx+2,10),(seedx+3,12),(seedx+1,14),(seedx-1,13),(seedx-2,12)],'ink')
    p([(seedx-1,11),(seedx+1,10),(seedx+2,12),(seedx+1,13),(seedx-1,12)],'blue2')
    l([(seedx-1,11),(seedx+1,11)],'blue3')
    if direction=='down':dot(seedx-1,12,'ink');dot(seedx+2,12,'ink');dot(seedx,13,'white')
    elif direction=='up':dot(seedx,12,'blue1');dot(seedx+1,13,'teal2')
    else:dot(seedx+2,12,'ink');dot(seedx,13,'white')
    l([(seedx-1,13),(seedx-2+lean,14),(seedx-3+lean,14)],'teal0')
    l([(seedx+1,13),(seedx+2-lean,14),(seedx+3-lean,14)],'teal2')
    if side:
        # Side leaf conceals part of the back panel; seed is off-axis.
        l([(6,4),(8,5),(11,6)],'teal0')
        if direction=='left':mirrored(a)
    elif direction=='up':l([(5,5),(7,6),(10,5)],'teal0')
    return a


def windweaver(direction, frame):
    """Four narrow, sequenced silk sails around a spindle and open woven loop."""
    a=Art(16,16,'transparent')
    side=direction in ('left','right')
    bob=-1 if frame==2 else 0
    def p(pts,c):a.p([(x,y+bob) for x,y in pts],c)
    def l(pts,c):a.l([(x,y+bob) for x,y in pts],c)
    def dot(x,y,c):a.dot(x,y+bob,c)
    shifts=((0,0,0,0),(1,0,-1,0),(1,1,-1,-1),(0,1,0,-1))[frame]
    # Open loop stays two pixels wide inside even when its trailing end swings.
    swing=(0,1,0,-1)[frame]
    l([(7,10),(5,12),(5+swing,14),(7+swing,15),(10,14),(10,12),(8,10)],'purple1')
    l([(6,12),(6+swing,14),(8+swing,14),(9,13),(9,12)],'wood4')
    dot(6+swing,13,'white');dot(9,12,'white')
    panels=[
      [(6,6),(2,1+shifts[0]),(1,3+shifts[0]),(4,7)],
      [(9,6),(12,1+shifts[1]),(14,2+shifts[1]),(11,7)],
      [(6,8),(1,8+shifts[2]),(2,11+shifts[2]),(6,10)],
      [(9,8),(14,8+shifts[3]),(13,11+shifts[3]),(9,10)],
    ]
    for i,pts in enumerate(panels):
        if side and i%2==0:pts=[(min(7,x+2),y) for x,y in pts]
        p(pts,'purple1')
        q=[(x+(1 if x<7 else -1),y) for x,y in pts]
        p(q,'white')
        l([pts[0],pts[2]],'purple3')
    # Separate spindle has no enlarged round head or conventional large wings.
    p([(7,3),(9,5),(9,9),(7,12),(6,9),(6,5)],'purple1')
    p([(7,4),(8,5),(8,9),(7,11),(7,8)],'flower1')
    dot(7,5,'white');dot(7,10,'gold2')
    l([(7,4),(6,2),(6,1)],'white');l([(8,4),(9,2),(10,2)],'white')
    if direction=='down':dot(6,6,'ink');dot(8,6,'ink')
    elif direction=='up':l([(7,5),(7,9)],'purple3')
    else:
        dot(8,6,'ink');dot(9,7,'gold2')
        if direction=='left':mirrored(a)
    return a


def archwarden(direction, frame):
    """Living amber vault: expressive keystone, four toe feet, open aperture."""
    a=Art(16,16,'transparent')
    lift=-1 if frame==2 else 0
    side=direction in ('left','right')
    def p(pts,c):a.p([(x,y+lift) for x,y in pts],c)
    def l(pts,c):a.l([(x,y+lift) for x,y in pts],c)
    def dot(x,y,c):a.dot(x,y+lift,c)
    # Far pair moves diagonally against the near pair. Warm toes separate the
    # four limbs from the architecture instead of looking like straight posts.
    for x,raised in ((4,frame==3),(10,frame==1)):
        y=12-int(raised)
        a.r((x,9+lift,x+1,y),'wood0')
        a.r((x,10+lift,x,y-1),'gold0')
        a.r((x-1,y,x+1,y),'wood3');a.dot(x,y-1,'gold2')
    p([(1,12),(1,7),(3,4),(6,2),(10,2),(13,4),(14,7),(14,12),(11,12),(11,8),(9,6),(6,6),(4,8),(4,12)],'wood0')
    p([(2,11),(2,7),(4,5),(6,3),(10,3),(12,5),(13,7),(13,11),(12,11),(12,7),(9,5),(6,5),(3,8),(3,11)],'gold1')
    l([(3,6),(6,3),(10,3),(12,5)],'gold3')
    l([(4,6),(6,4),(9,4),(11,5)],'gold4')
    l([(2,8),(2,11)],'gold2');l([(13,8),(13,11)],'wood3')
    l([(6,3),(6,5)],'wood3');l([(10,3),(9,5)],'wood3')
    p([(5,3),(4,1),(6,2),(7,1),(9,2),(11,1),(10,4),(7,3)],'pine2')
    l([(5,2),(6,2),(7,1)],'pine5');dot(10,2,'moss3')
    # Squared little paws extend outside the narrow column, with a dark seam.
    for x,raised in ((1,frame==1),(12,frame==3)):
        y=14-2*int(raised)
        a.r((x,10+lift,x+2,y-1),'wood0')
        a.r((x+1,10+lift,x+1,y-2),'gold2')
        a.r((max(0,x-1),y-1,min(15,x+2),y),'wood0')
        a.r((max(0,x-1),y-1,min(15,x+1),y-1),'wood4')
        a.dot(x+1,y-1,'gold3')
    if direction=='down':
        # Rounded hanging keystone is a face, not a decoration on two pillars.
        p([(5,4),(7,3),(10,4),(11,6),(9,7),(6,7),(4,6)],'wood0')
        p([(6,4),(9,4),(10,6),(8,7),(6,6),(5,5)],'wood4')
        l([(6,4),(9,4)],'gold3')
        dot(6,5,'ink');dot(9,5,'ink');dot(8,6,'wood1')
        dot(7,7,'gold4')
    elif direction=='up':
        l([(5,5),(7,4),(10,5)],'gold0')
    else:
        # One-eyed projecting cheek makes the left/right facing legible.
        p([(10,4),(12,4),(15,6),(14,8),(11,7),(10,6)],'wood0')
        p([(11,5),(12,5),(14,6),(13,7),(11,6)],'wood4')
        dot(12,5,'ink');dot(14,7,'gold4')
        l([(3,7),(4,5),(6,4)],'wood3')
        if direction=='left':mirrored(a)
    return a


def portrait_hearthkeeper():
    a=Art(32,32,'transparent')
    # Independent 32px composition: low prow, kiln-glazed mantle, long single tail.
    a.p([(22,21),(26,19),(27,14),(26,9),(29,7),(30,10),(30,19),(28,24),(22,26)],'ink')
    a.p([(24,22),(28,19),(28,13),(27,10),(29,9),(29,18),(27,23),(24,24)],'fire1')
    a.l([(28,12),(28,10),(29,8)],'white',2)
    for x,y in ((10,24),(21,25)):
        a.p([(x,y-2),(x+3,y-2),(x+2,y+4),(x-2,y+4),(x-2,y+2)],'ink')
        a.r((x-1,y+1,x+1,y+2),'fire2')
    a.p([(8,17),(13,11),(22,11),(26,16),(25,23),(21,27),(11,26),(7,22)],'ink')
    a.p([(9,17),(14,12),(22,12),(25,17),(24,22),(20,25),(11,24),(8,21)],'fire0')
    a.p([(10,16),(14,12),(21,12),(24,16),(23,20),(19,22),(12,21),(9,19)],'wood3')
    a.p([(11,15),(15,12),(21,13),(23,16),(21,19),(18,20),(12,19),(10,17)],'white')
    a.l([(12,20),(17,23),(21,22),(24,19)],'gold2')
    a.l([(13,15),(14,16),(13,18)],'fire0');a.l([(18,14),(20,16),(18,18)],'gold1')
    for x,y in ((13,8),(18,5),(23,8)):
        a.p([(x-2,y+5),(x,y),(x+2,y+2),(x+2,y+6)],'ink')
        a.p([(x-1,y+4),(x,y+1),(x+1,y+3),(x+1,y+5)],'slate')
        a.dot(x,y+2,'silver')
    a.p([(3,16),(3,7),(6,8),(8,13),(11,9),(13,10),(13,18),(11,23),(7,25),(4,23),(1,20),(1,18)],'ink')
    a.p([(4,16),(4,9),(6,11),(7,15),(11,11),(12,12),(11,19),(9,22),(6,23),(2,20),(2,18)],'fire2')
    a.p([(4,13),(4,10),(6,13)],'rose2')
    a.l([(5,16),(8,15),(10,16)],'fire3')
    a.p([(2,19),(6,19),(8,21),(10,20),(8,23),(5,22)],'white')
    a.r((7,17,8,18),'ink');a.dot(7,17,'white');a.dot(1,19,'ink')
    return a


def portrait_canopykeeper():
    a=Art(32,32,'transparent')
    # Three leaves and the open band below their braided rim stay recognizable.
    a.p([(10,12),(10,6),(15,1),(19,3),(23,11),(18,16)],'ink')
    a.p([(12,11),(12,6),(15,3),(18,4),(21,10),(18,13)],'teal1')
    a.l([(15,3),(15,8),(18,12)],'water4');a.l([(15,8),(18,7)],'teal2')
    a.p([(16,13),(9,6),(4,5),(1,7),(2,12),(7,16),(14,17),(17,15)],'ink')
    a.p([(14,13),(8,7),(4,6),(2,8),(3,11),(8,14),(14,16)],'teal1')
    a.p([(3,7),(7,7),(11,11),(6,10)],'teal2')
    a.l([(3,8),(8,11),(14,14)],'water4');a.l([(7,11),(8,8)],'teal0')
    a.p([(16,13),(23,7),(28,5),(30,7),(29,12),(25,16),(18,17),(15,15)],'ink')
    a.p([(18,13),(24,8),(28,7),(29,8),(27,12),(23,14),(18,16)],'teal2')
    a.l([(28,7),(25,11),(18,14)],'water4');a.l([(25,11),(26,13)],'teal0')
    a.l([(5,14),(8,17),(11,15),(14,18),(17,16),(20,18),(23,15),(26,16)],'teal0')
    a.l([(7,14),(9,16),(12,15)],'water4');a.l([(18,16),(20,17),(23,15)],'water4')
    a.l([(15,16),(15,20),(16,22)],'teal0');a.l([(16,16),(16,21)],'water4')
    a.p([(13,21),(17,20),(21,23),(21,26),(17,29),(13,28),(10,25),(11,22)],'ink')
    a.p([(13,22),(17,21),(19,23),(20,25),(17,27),(13,27),(11,25),(12,23)],'blue1')
    a.p([(13,22),(17,22),(19,24),(16,25),(12,24)],'blue2')
    a.l([(13,22),(16,22)],'blue3');a.dot(13,25,'ink');a.dot(18,24,'ink');a.dot(16,27,'white')
    a.l([(13,27),(11,29),(8,28)],'teal0');a.l([(16,28),(17,30),(20,30),(21,28)],'teal2')
    a.l([(17,28),(15,30),(12,30)],'teal0')
    return a


def portrait_windweaver():
    a=Art(32,32,'transparent')
    # Four separate silk blades have varied angles; open woven loop trails below.
    a.l([(14,21),(10,24),(10,28),(14,30),(19,29),(22,25),(20,22),(17,21)],'purple1',3)
    a.l([(14,22),(11,25),(12,28),(16,29),(20,26),(20,24),(18,22)],'wood4')
    a.l([(12,25),(12,27),(15,29)],'white');a.l([(20,25),(18,28)],'white')
    sails=[([(13,12),(5,2),(2,3),(3,7),(10,15)],[(12,12),(5,4),(3,4),(5,8),(10,13)]),
           ([(18,12),(25,2),(29,3),(28,7),(21,15)],[(19,12),(25,4),(28,4),(26,8),(21,13)]),
           ([(12,17),(3,16),(1,20),(5,23),(13,21)],[(11,18),(4,17),(3,20),(5,21),(12,20)]),
           ([(19,17),(28,14),(30,18),(27,22),(19,21)],[(20,18),(27,16),(29,18),(26,20),(20,20)])]
    for outer,inner in sails:
        a.p(outer,'purple1');a.p(inner,'white')
        a.l([inner[0],inner[2]],'purple3')
    a.l([(5,7),(9,10)],'flower1');a.l([(25,7),(22,10)],'flower1')
    a.p([(15,6),(18,10),(19,15),(18,21),(15,25),(12,20),(12,13),(13,9)],'purple1')
    a.p([(15,8),(17,11),(17,19),(15,23),(14,19),(14,12)],'flower1')
    a.l([(15,9),(15,13)],'white');a.l([(14,19),(15,21),(16,19)],'gold2')
    a.l([(14,9),(11,5),(11,2)],'white');a.l([(17,9),(20,5),(21,4)],'white')
    a.dot(13,14,'ink');a.dot(17,13,'ink');a.dot(16,16,'gold2')
    return a


def portrait_archwarden():
    a=Art(32,32,'transparent')
    # Four supports, with an asymmetrically raised back foot and broad toes.
    for x,y,foot in ((9,20,26),(23,20,28)):
        a.r((x,y,x+2,foot),'wood0');a.r((x,y,x+1,foot-2),'gold0')
        a.r((x-2,foot-1,x+2,foot),'wood0');a.r((x-1,foot-1,x+1,foot-1),'wood4')
    a.p([(2,24),(2,14),(5,8),(11,4),(21,4),(27,8),(29,14),(29,24),(23,24),(23,15),(20,11),(12,11),(8,15),(8,24)],'wood0')
    a.p([(3,23),(3,14),(6,9),(12,5),(21,5),(26,9),(28,14),(28,23),(25,23),(25,14),(20,9),(12,9),(6,15),(6,23)],'gold1')
    a.p([(4,14),(7,9),(12,6),(20,6),(25,10),(26,13),(23,12),(20,8),(12,8),(8,11),(6,15)],'gold3')
    a.l([(7,10),(12,7),(19,7),(23,10)],'gold4',2)
    a.l([(4,15),(4,23)],'gold2',2);a.l([(27,15),(27,23)],'wood3')
    a.l([(10,6),(12,10)],'wood3');a.l([(20,6),(19,10)],'wood3');a.l([(5,13),(8,15)],'gold0')
    a.p([(8,6),(7,3),(10,4),(12,2),(15,3),(18,2),(20,4),(24,3),(22,7),(17,6),(14,7),(11,5)],'pine1')
    a.l([(9,4),(11,5),(13,3),(16,4),(18,3),(21,5)],'pine4');a.dot(13,3,'pine5');a.dot(21,4,'moss3')
    for x,y in ((2,27),(24,30)):
        a.p([(x,22),(x+5,22),(x+5,y-2),(x+4,y),(x-2,y),(x-2,y-2),(x,y-3)],'wood0')
        a.r((x+1,23,x+3,y-2),'gold1');a.l([(x+1,23),(x+1,y-3)],'gold3')
        a.r((x-1,y-1,x+3,y-1),'wood4');a.dot(x+1,y-1,'gold4');a.dot(x+3,y-1,'wood1')
    # Friendly tapered keystone borrows Kohaku's small amber cheek, below moss.
    # Its face terminates at y=14; the large y=15..23 aperture stays open.
    a.p([(12,7),(18,7),(22,10),(21,13),(17,15),(13,14),(10,11)],'wood0')
    a.p([(13,8),(18,8),(20,10),(20,12),(17,14),(13,13),(11,11)],'wood4')
    a.p([(13,8),(18,8),(19,10),(14,10),(12,11)],'gold3')
    a.r((13,10,14,11),'ink');a.r((18,10,19,11),'ink')
    a.dot(13,10,'gold4');a.dot(18,10,'gold4')
    a.l([(15,12),(16,13),(17,12)],'wood1');a.dot(16,14,'gold4')
    return a


FIELD_FUNCTIONS=(hearthkeeper,canopykeeper,windweaver,archwarden)
PORTRAIT_FUNCTIONS=(portrait_hearthkeeper,portrait_canopykeeper,portrait_windweaver,portrait_archwarden)


def mask(im):
    return Image.frombytes('L',im.size,bytes(255 if n else 0 for n in im.tobytes()))


def paste(target, sprite, xy):
    im=sprite if isinstance(sprite,Image.Image) else sprite.im
    target.paste(im.convert(target.mode),xy,mask(im))


def save_indexed(im,path):
    im.save(path,transparency=0,optimize=False)


def array(f,name,data):
    f.write(f'const unsigned char {name}[{len(data)}] = {{\n')
    for i in range(0,len(data),32):f.write('  '+','.join(map(str,data[i:i+32]))+',\n')
    f.write('};\n\n')


def emit_code(fields,portraits):
    header='''/* Generated original evolved companion art; edit assets/generate_evolutions.py. */
#ifndef EMBERBOND_EVOLUTION_ART_H
#define EMBERBOND_EVOLUTION_ART_H
#define EVOLUTION_ART_COUNT 4
#define EVOLUTION_ART_FRAME_BYTES 256
#define EVOLUTION_ART_PORTRAIT_BYTES 1024
enum { EVOLUTION_HOMURA_HEARTHKEEPER, EVOLUTION_MIDORI_CANOPYKEEPER,
       EVOLUTION_FUURI_WINDWEAVER, EVOLUTION_KOHAKU_ARCHWARDEN };
/* Order is stable IDs 2,5,8,11. Directions: down, up, left, right.
 * Four frames: idle, first motion beat, raised/turning beat, second beat.
 * Row-major palette indices into existing game_palette; zero is transparent.
 * 16x16 field anchor is center (x-8,y-8); 32x32 portrait is top-left blitted.
 * All arrays are immutable ROM data. No new palette, buffers or BSS.
 * These sheets do not themselves enable evolution or change collision boxes.
 */
extern const unsigned char evolution_form_ids[EVOLUTION_ART_COUNT];
extern const unsigned char evolution_companion_direction_frames[EVOLUTION_ART_COUNT][4][4][EVOLUTION_ART_FRAME_BYTES];
extern const unsigned char evolution_portraits[EVOLUTION_ART_COUNT][EVOLUTION_ART_PORTRAIT_BYTES];
/* Fail closed: unknown stable ID returns -1/null; invalid direction/frame null. */
int evolution_art_index(unsigned int form_id);
const unsigned char *evolution_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame);
const unsigned char *evolution_art_portrait(unsigned int form_id);
#endif
'''
    (SRC/'evolution_art.h').write_text(header)
    f=io.StringIO();array(f,'evolution_form_ids',FORM_IDS)
    base.emit_image_tensor(f,'evolution_companion_direction_frames',fields,[4,4,4,256])
    base.emit_image_tensor(f,'evolution_portraits',portraits,[4,1024])
    # Keep chunks strictly below 32 KiB, split only at line boundaries.
    chunks=[];current=[];size=0
    for line in f.getvalue().splitlines(keepends=True):
        if current and size+len(line.encode())>=32768:
            chunks.append(''.join(current));current=[];size=0
        current.append(line);size+=len(line.encode())
    if current:chunks.append(''.join(current))
    folder=SRC/'evolution_art_data';folder.mkdir(exist_ok=True)
    for old in folder.glob('part_*.inc'):old.unlink()
    for i,chunk in enumerate(chunks):(folder/f'part_{i:03d}.inc').write_text(chunk)
    code='#include "evolution_art.h"\n/* Generated by assets/generate_evolutions.py. */\n'
    code+=''.join(f'#include "evolution_art_data/part_{i:03d}.inc"\n' for i in range(len(chunks)))
    code+='''
int evolution_art_index(unsigned int form_id) {
    switch (form_id) {
    case 2: return EVOLUTION_HOMURA_HEARTHKEEPER;
    case 5: return EVOLUTION_MIDORI_CANOPYKEEPER;
    case 8: return EVOLUTION_FUURI_WINDWEAVER;
    case 11: return EVOLUTION_KOHAKU_ARCHWARDEN;
    default: return -1;
    }
}
const unsigned char *evolution_art_frame(unsigned int form_id, unsigned int direction, unsigned int frame) {
    int index = evolution_art_index(form_id);
    if (index < 0 || direction >= 4 || frame >= 4) return (const unsigned char *)0;
    return evolution_companion_direction_frames[index][direction][frame];
}
const unsigned char *evolution_art_portrait(unsigned int form_id) {
    int index = evolution_art_index(form_id);
    return index < 0 ? (const unsigned char *)0 : evolution_portraits[index];
}
'''
    (SRC/'evolution_art.c').write_text(code)
    return [len(x.encode()) for x in chunks]


def make_previews(fields,portraits):
    campaign=load_module('evolution_campaign',ROOT/'assets/generate_campaign.py')
    campaign.P=P;campaign.PAL=PAL;campaign.RGB=RGB;campaign.Art=Art
    originals=(base.fox_direction('down',0),base.leaf_direction('down',0),campaign.fuuri('down',0),campaign.kohaku('down',0))
    sheet=Image.new('P',(256,64),0);sheet.putpalette(PAL)
    for i,rows in enumerate(fields):
        single=Image.new('P',(64,64),0);single.putpalette(PAL)
        for d,row in enumerate(rows):
            for frame,sp in enumerate(row):single.paste(sp.im,(frame*16,d*16))
        sheet.paste(single,(i*64,0));save_indexed(single,OUT/f'{KEYS[i]}_field.png')
        save_indexed(portraits[i].im,OUT/f'{KEYS[i]}_portrait.png')
    save_indexed(sheet,OUT/'field_sheet.png')
    sheet.resize((1024,256),Image.Resampling.NEAREST).save(OUT/'field_sheet_4x.png',transparency=0)
    contact=Image.new('RGB',(864,448),RGB[P['night']]);d=ImageDraw.Draw(contact)
    d.text((16,10),'EVOLVED COMPANIONS / ORIGINAL PIXEL ART',fill=RGB[P['white']])
    d.text((16,27),'64 field poses + four separately drawn portraits | Art preview, not gameplay proof',fill=RGB[P['silver']])
    for i in range(4):
        x=12+i*214
        d.rounded_rectangle((x,50,x+204,431),radius=5,fill=RGB[P['deep']])
        d.text((x+8,59),f'{FORM_IDS[i]:03d}  {NAMES[i].split()[0].upper()}',fill=RGB[P['gold3']])
        d.text((x+8,75),NAMES[i].split()[1],fill=RGB[P['white']])
        paste(contact,portraits[i].im.resize((96,96),Image.Resampling.NEAREST),(x+72,96))
        paste(contact,originals[i].im.resize((32,32),Image.Resampling.NEAREST),(x+14,139))
        d.text((x+14,175),'BASE',fill=RGB[P['silver']])
        d.text((x+8,205),'DOWN / UP / LEFT / RIGHT',fill=RGB[P['silver']])
        for di,row in enumerate(fields[i]):
            for f,sp in enumerate(row):paste(contact,sp.im.resize((48,48),Image.Resampling.NEAREST),(x+8+f*48,218+di*48))
        d.text((x+8,416),'4 distinct motion beats',fill=RGB[P['silver']])
    contact.save(OUT/'contact_sheet.png')
    # Flat single-color silhouette test, base beside evolved, no palette cues.
    sil=Image.new('RGB',(512,112),RGB[P['deep']]);sd=ImageDraw.Draw(sil)
    for i in range(4):
        sd.text((i*128+6,5),KEYS[i],fill=RGB[P['silver']])
        for j,sp in enumerate((originals[i],fields[i][0][0])):
            flat=Image.new('RGB',(16,16),RGB[P['white']]);flat.putalpha(mask(sp.im))
            sil.paste(flat.resize((48,48),Image.Resampling.NEAREST),(i*128+7+j*60,30),flat.getchannel('A').resize((48,48),Image.Resampling.NEAREST))
    sd.text((8,94),'Base / evolved silhouettes. Original code-native designs.',fill=RGB[P['silver']])
    sil.save(OUT/'silhouette_comparison.png')
    scenes=[]
    for i,bgname in enumerate(('village','forest','campaign_sky_path','campaign_core_path')):
        view=Image.open(ROOT/f'assets/{bgname}.png').convert('RGB')
        paste(view,base.shadow_sprite(),(106,104));paste(view,base.hero('down',0),(106,100))
        paste(view,base.shadow_sprite(),(130,108));paste(view,fields[i][0][0],(130,104))
        sd=ImageDraw.Draw(view);sd.rectangle((0,145,239,159),fill=RGB[P['deep']])
        sd.text((5,147),'ART MOCK / '+KEYS[i].upper(),fill=RGB[P['white']])
        view.save(OUT/f'scene_{KEYS[i]}_240x160.png');scenes.append(view)
    scene_sheet=Image.new('RGB',(480,320))
    for i,scene in enumerate(scenes):scene_sheet.paste(scene,((i%2)*240,(i//2)*160))
    scene_sheet.save(OUT/'native_scene_mocks.png')
    scene_sheet.resize((960,640),Image.Resampling.NEAREST).save(OUT/'scene_mocks_2x.png')
    # Deterministic animation proof keeps transparent gaps visible against floor.
    animation=[]
    for f in range(4):
        frame=Image.new('RGB',(256,96),RGB[P['bg_sunlit_grass1']]);fd=ImageDraw.Draw(frame)
        for i in range(4):
            for di in range(4):
                paste(frame,fields[i][di][f],(i*64+di*16,39))
            fd.text((i*64+3,13),NAMES[i].split()[0],fill=RGB[P['ink']])
        animation.append(frame.resize((768,288),Image.Resampling.NEAREST))
    animation[0].save(OUT/'motion_preview.gif',save_all=True,append_images=animation[1:],duration=140,loop=0,disposal=2,optimize=False)
    return originals


def validate_pixels(fields,portraits,originals):
    images=[sp for rows in fields for row in rows for sp in row]+list(portraits)
    for sp in images:
        data=sp.im.tobytes()
        assert 0 in data and max(data)<base.BASE_PALETTE_SIZE
        assert sp.im.mode=='P' and sp.im.getpalette()==PAL
        assert sp.im.getpixel((0,0))==0 and sp.im.getpixel((sp.im.width-1,0))==0
    for rows in fields:
        for row in rows:
            assert len({sp.im.tobytes() for sp in row})==4
            # Animation must change the silhouette, not just colors/eye sparkles.
            assert len({mask(sp.im).tobytes() for sp in row})>=3
        assert len({rows[d][0].im.tobytes() for d in range(4)})==4
    for i in range(4):
        assert mask(originals[i].im).tobytes()!=mask(fields[i][0][0].im).tobytes()
        assert portraits[i].im.size==(32,32)
        assert portraits[i].im.tobytes()!=fields[i][0][0].im.resize((32,32),Image.Resampling.NEAREST).tobytes()
    # The signature arch aperture is transparent in every animation view.
    for row in fields[3]:
        for sp in row:
            assert all(sp.im.getpixel((x,y))==0 for x in range(6,10) for y in range(8,10))
    # Hollow silk loop contains an actual empty interior in all four idle views.
    assert all(fields[2][d][0].im.getpixel((7,13))==0 for d in range(4))
    return {'field_dimensions':[4,4,4,256], 'portrait_dimensions':[4,1024],
            'palette_indices':sorted({n for sp in images for n in sp.im.tobytes()}),
            'transparent_zero':True,'existing_actor_palette_only':True,
            'four_distinct_frames_per_direction':True,'articulated_silhouette_motion':True,
            'four_distinct_idle_views':True,'independent_portraits':True,
            'arch_aperture_clear_all_16_frames':True,'loop_interior_clear':True,
            'base_evolved_silhouettes_distinct':True}


def output_hashes():
    files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name not in ('validation.json',))
    files+=sorted((SRC/'evolution_art_data').glob('*.inc'))+[SRC/'evolution_art.c',SRC/'evolution_art.h']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}


def generate():
    OUT.mkdir(parents=True,exist_ok=True)
    fields=[[[fn(d,f) for f in range(4)] for d in DIRECTIONS] for fn in FIELD_FUNCTIONS]
    portraits=[fn() for fn in PORTRAIT_FUNCTIONS]
    originals=make_previews(fields,portraits)
    pixels=validate_pixels(fields,portraits,originals)
    chunks=emit_code(fields,portraits)
    manifest={'schema_version':1,'names':list(NAMES),'form_ids':list(FORM_IDS),'directions':list(DIRECTIONS),
      'generator':'assets/generate_evolutions.py','rights':'Original code-native pixel art. No external art, extracted characters, traced silhouettes, or raster model input.',
      'status':'Art assets only; playable evolution and journal integration are separate engine work.',
      'palette_sha256':hashlib.sha256(json.dumps(base.COLORS).encode()).hexdigest(),
      'data_bytes':4*4*4*256+4*1024+4,'runtime_bss_bytes':0,'max_include_bytes':max(chunks),
      'include_bytes':chunks,'frame_ticks_suggestion':8,'anchor':[8,8],
      'motions':['Mantle plants, paired paw beats, single tail sways','Three leaves open in sequence; suspended seed and root hem sway','Four silk sails tilt sequentially around a spindle; woven loop trails','Four pillar feet step in opposing pairs; open amber vault rises and locks'],
      'validation':pixels}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'CREDITS.txt').write_text(manifest['rights']+'\nAuthored for Adventure Legends using deterministic Python/Pillow geometry.\nExisting game_palette is reused verbatim. Art mockups are not emulator screenshots.\n')
    return manifest


def verify(manifest):
    before=output_hashes();generate();after=output_hashes()
    assert before==after,'Regeneration must be byte-identical'
    report={'pixel_validation':manifest['validation'],'deterministic_regeneration':True,
            'output_sha256':after,'max_include_bytes':manifest['max_include_bytes']}
    # Compile and exercise the full lookup domain. Objects are temporary, not assets.
    test='''#include "evolution_art.h"
#include <assert.h>
int main(void) {
 unsigned i,d,f,k,id;
 assert(sizeof evolution_companion_direction_frames == 16384);
 assert(sizeof evolution_portraits == 4096);
 for(id=0;id<512;id++) {
  int expected=(id==2?0:id==5?1:id==8?2:id==11?3:-1);
  assert(evolution_art_index(id)==expected);
  assert((evolution_art_portrait(id)!=0)==(expected>=0));
  assert((evolution_art_frame(id,0,0)!=0)==(expected>=0));
 }
 assert(evolution_art_index(~0u)==-1);
 for(i=0;i<4;i++) {
  id=evolution_form_ids[i];
  assert(evolution_art_portrait(id)==evolution_portraits[i]);
  for(d=0;d<4;d++) for(f=0;f<4;f++) {
   const unsigned char *p=evolution_art_frame(id,d,f);
   assert(p==evolution_companion_direction_frames[i][d][f]);
   for(k=0;k<256;k++) assert(p[k]<=96);
  }
  assert(evolution_art_frame(id,4,0)==0);
  assert(evolution_art_frame(id,0,4)==0);
  assert(evolution_art_frame(id,~0u,~0u)==0);
 }
 return 0;
}
'''
    with tempfile.TemporaryDirectory(prefix='evolution-art-') as td:
        td=Path(td);(td/'test.c').write_text(test)
        host=['gcc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-I',str(SRC)]
        subprocess.run(host+[str(td/'test.c'),str(SRC/'evolution_art.c'),'-o',str(td/'test')],check=True,capture_output=True)
        subprocess.run([str(td/'test')],check=True,capture_output=True)
        report['host_compile_and_lookup_tests']='passed'
        arm=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc'
        if not arm.exists(): raise RuntimeError('ARM toolchain missing; ARM compilation not verified')
        subprocess.run([str(arm),'-std=c99','-mcpu=arm7tdmi','-mthumb','-O2','-ffreestanding','-fno-builtin','-Wall','-Wextra','-Werror','-c',str(SRC/'evolution_art.c'),'-o',str(td/'evolution_art.o')],check=True,capture_output=True)
        size=subprocess.run([str(arm).replace('gcc','size'),str(td/'evolution_art.o')],check=True,capture_output=True,text=True).stdout
        sections=list(map(int,size.splitlines()[-1].split()[:3]))
        assert sections[1:]==[0,0],size
        report['arm_compile']='passed';report['arm_size_output']=size.strip().replace(str(td/'evolution_art.o'),'evolution_art.o');report['arm_data_bytes']=sections[1];report['arm_bss_bytes']=sections[2]
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n')
    return {k:v for k,v in report.items() if k not in ('output_sha256','pixel_validation')}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    manifest=generate()
    if args.verify:print(json.dumps(verify(manifest),indent=2))
    else:print(json.dumps({'generated_forms':FORM_IDS,'data_bytes':manifest['data_bytes'],'max_include_bytes':manifest['max_include_bytes']},indent=2))


if __name__=='__main__':main()
