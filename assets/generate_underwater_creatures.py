#!/usr/bin/env python3
"""Original native Underwater companion art. No borrowed/traced/raster inputs.
Four views, four articulated walk beats, three cast poses, independent portraits.
Only writes Underwater creature art. Existing palette and released pixels are read-only.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, subprocess, sys, tempfile
from PIL import Image, ImageDraw
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'assets/underwater_creatures'
sys.path.insert(0,str(ROOT/'assets'));sys.path.insert(0,str(ROOT/'assets/creatures'))
from magma_palette import Art as BaseArt, P, PAL, rgb as RGB, COLORS
from catalog_source import load_catalog
BRIEFS=json.loads((ROOT/'docs/underwater-design/creature_forms.json').read_text())
FORM_IDS=tuple(range(49,73)); NAMES=tuple(f['name'] for f in BRIEFS); KEYS=tuple(n.lower() for n in NAMES)
DIRECTIONS=('down','up','left','right')
WALK_TICKS=((9,7,9,8),(11,9,11,8),(8,11,8,10),(10,8,12,8),(12,8,10,9),(10,7,10,13),
 (7,8,7,10),(11,8,12,9),(8,10,7,11),(6,7,6,8),(10,9,10,8),(12,8,12,9),
 (10,7,10,8),(12,9,11,8),(6,7,7,6),(9,10,8,10),(11,8,11,9),(6,8,6,9),
 (7,7,6,8),(10,8,11,7),(8,11,7,10),(10,8,9,8),(11,8,12,8),(9,9,10,8))
class Art(BaseArt):
    """Bounded native stroke centre-lines, leaving a transparent safety rim.

    The 16px pen uses an authored one-pixel edge inset. Thick strokes use a
    two-pixel centre-line inset, so rounded/folded limb tips never cross it.
    Portraits use the full independently composed 32px drawing surface.
    """
    def l(self,pts,c,w=1):
        if self.im.width==16:
            pad=2 if w>1 else 1
            pts=[(max(pad,min(15-pad,x)),max(pad,min(15-pad,y))) for x,y in pts]
        super().l(pts,c,w)
class Pen:
    def __init__(self,a,dy=0,compress=False):self.a,self.dy,self.compress=a,dy,compress
    def x(self,x):return x+(1 if x<7 else -1 if x>8 else 0) if self.compress else x
    def y(self,y):return max(1,min(14,y+self.dy))
    def p(self,pts,c):self.a.p([(self.x(x),self.y(y)) for x,y in pts],c)
    def l(self,pts,c,w=1):self.a.l([(self.x(x),self.y(y)) for x,y in pts],c,w)
    def e(self,b,c):self.a.e((self.x(b[0]),self.y(b[1]),self.x(b[2]),self.y(b[3])),c)
    def r(self,b,c):self.a.r((self.x(b[0]),self.y(b[1]),self.x(b[2]),self.y(b[3])),c)
    def dot(self,x,y,c):self.a.dot(self.x(x),self.y(y),c)
def beat(f,cast):
    return ((-1,0,1,0)[f],(0,1,0,-1)[f],0) if cast is None else ((0,-1,1)[cast],(-1,1,0)[cast],(1,-1,1)[cast])
def eye(a,x,y):
    a.r((x,y,x+1,y+2),'white');a.dot(x,y+1,'ink');a.dot(x,y+2,'ink')
def face(a,d,x,y,c,cast=None,w=6):
    a.e((x,y,x+w,y+4),'ink');a.e((x+1,y+1,x+w-1,y+3),c)
    if d=='up':
        a.l([(x+2,y+1),(x+w-2,y+1)],'white');a.dot(x+w-2,y+3,c)
    elif d in ('left','right'):
        eye(a,x+1,y);a.dot(x,y+3,'ink');a.dot(x+3,y+3,'rose4')
    else:
        eye(a,x+1,y);eye(a,x+w-2,y);a.dot(x+w//2,y+3,'rose0')
    if cast==0 and d!='up':a.l([(x+1,y+1),(x+2,y+1)],'ink')
def finish(a,d):return a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if d=='right' else a.im

def cuttle(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=beat(f,cast);side=d in ('left','right');q=Pen(a,h,cast==0)
    if v==0:
        q.p([(7,2),(10,3),(12,7),(11,10),(4,10),(3,7),(5,3)],'ink')
        q.p([(7,3),(9,4),(10,8),(5,8),(5,5)],'purple2');q.l([(7,3),(9,4)],'purple3')
        q.p([(4,5),(2,6+t),(2,9),(4,10)],'water4');q.p([(11,5),(13,6-t),(13,9),(11,10)],'skin2')
        for x in (3,5,7,9,11,13):a.l([(x,10),(x+s,12),(x+s,13)],'ink');a.dot(x+s,12,'water4')
        for x,sg in ((3,-1),(12,1)):a.l([(x,9),(x+sg,11),(x+sg,13),(x,13+t)],'purple3')
        face(q,d,2 if side else 4,7,'water4',cast)
    elif v==1:
        q.r((5,1,10,10),'ink');q.r((6,2,9,9),'purple1');q.l([(6,2),(8,2)],'purple3')
        for x,sg in ((4,-1),(11,1)):
            q.p([(x,2),(x+sg,3),(x,4),(x+sg,6+t*sg),(x,8),(x+sg,9),(x,10)],'water4')
            a.l([(x,10),(x+sg,11),(x+sg,14),(x+1,14)],'ink');a.l([(x,11),(x+sg,12),(x+sg,13)],'skin2')
        a.l([(6,10),(6+s,12),(7+s,13)],'water4');a.l([(9,10),(9-s,12),(8-s,13)],'water4')
        face(q,d,3 if side else 5,7,'water4',cast,5)
    else:
        q.e((5,2,10,8),'ink');q.e((6,3,9,7),'purple2')
        q.p([(6,8),(2,5+t),(1,8),(2,12),(5,13),(7,10)],'ink');q.p([(5,8),(2,7+t),(2,10),(4,12),(6,10)],'skin2')
        q.p([(9,8),(12,4-t),(14,7),(13,12),(10,13),(8,10)],'ink');q.p([(10,8),(12,6-t),(13,8),(12,11),(10,12)],'water4')
        q.l([(2,9),(5,10)],'purple3');q.l([(12,8),(10,10)],'purple3')
        a.l([(5,12),(4+s,14)],'ink');a.l([(10,12),(11-s,14)],'ink')
        face(q,d,3 if side else 5,6,'water4',cast,5)
    return finish(a,d)

def clam(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=beat(f,cast);q=Pen(a,h if cast is not None else t,cast==0);side=d in ('left','right')
    # One broad continuous scalloped muscular foot, never crustacean claws.
    a.p([(4,10),(11,10),(13,12),(12+s,14),(9,13),(6,14),(2+s,13),(2,12)],'ink')
    a.l([(3+s,12),(5,13),(8,12),(11,13),(12,12)],'skin2',2)
    if v==0:
        q.p([(2,8),(3,4),(6,2),(10,3),(13,6),(12,9)],'ink');q.p([(3,7),(4,4),(7,3),(10,4),(12,6),(11,8)],'stone5')
        for x in (5,8,10):q.l([(7,8),(x,4)],'wood4')
        q.p([(2,10),(5,9),(11,9),(13,10),(11,12),(4,12)],'ink');q.l([(3,10),(6,11),(10,11),(12,10)],'wood5')
        face(q,d,2 if side else 5,7,'skin2',cast,5)
    elif v==1:
        q.p([(1,6),(3,4),(9,4),(14,6),(13,9),(2,9)],'ink');q.l([(2,6),(5,5),(10,5),(13,7)],'stone5',2)
        q.p([(1,10),(6,10),(7,12),(8,10),(14,10),(11,13),(9,13),(8,12),(6,13),(3,13)],'ink')
        q.l([(2,10),(4,12),(6,12)],'wood4');q.l([(9,12),(11,12),(13,10)],'stone5')
        face(q,d,1 if side else 4,7,'skin2',cast,7)
        a.dot(3+s,14,'skin1');a.dot(11-s,14,'skin2')
    else:
        q.p([(3,9),(1,5),(2,1),(5,3),(6,7),(7,9)],'ink');q.l([(3,8),(2,5),(3,3),(5,6)],'wood5',2)
        q.p([(8,9),(9,5),(12,1),(14,3),(13,7),(11,10)],'ink');q.l([(10,8),(11,5),(13,3),(12,7)],'stone5')
        a.e((5,11+t,11,14),'ink');a.e((6,12+t,10,13),'skin2')
        face(q,d,2 if side else 5,8,'skin2',cast,5)
    return finish(a,d)

def seahorse(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=beat(f,cast);q=Pen(a,h if cast is not None else (t if v==1 else 0),cast==0);side=d in ('left','right')
    if v==0:
        q.l([(8,7),(9,10),(8,13),(5+s,13),(5+s,11)],'ink',3);q.l([(8,8),(8,11),(7,12),(6+s,12)],'wood4')
        q.p([(6,4),(7,1),(9,3),(11,2),(10,6)],'ink');q.l([(7,4),(8,2),(9,4)],'pine5')
        q.p([(5,8),(2,7+t),(3,10),(5,10)],'pine5');q.p([(10,7),(13,7-t),(12,10),(10,10)],'mint')
        face(q,d,2 if side else 4,4,'wood5',cast)
        if side:q.l([(2,6),(1,6)],'wood5',2)
    elif v==1:
        # Two rails enclosing two separate negative-space ladder windows.
        q.l([(3,10),(2,6),(3,2),(5,1),(6,3),(10,3),(11,1),(13,2),(13,7),(12,10)],'ink')
        q.l([(3,8),(3,4),(5,3)],'pine5');q.l([(11,3),(12,4),(12,8)],'mint')
        q.l([(4,4),(11,4)],'pine3');q.l([(3,7),(12,7)],'pine3')
        a.l([(8,8),(9+s,11),(9,14)],'ink',3);a.l([(8,9),(9+s,12)],'wood4')
        q.p([(6,9),(4-s,10),(5,12)],'pine5');q.p([(10,9),(12+s,10),(11,12)],'mint')
        face(q,d,2 if side else 5,5,'wood5',cast,5)
    else:
        q.l([(5,8),(7,4),(11,4),(13,7),(12,11),(9,13),(6,12),(6,10),(8,9)],'ink',3)
        q.l([(6,7),(8,5),(10,5),(12,7),(11,11),(9,12),(7,11)],'pine5')
        q.l([(10,11),(11+s,9),(10+s,8)],'wood5')
        q.p([(5,7),(4,3+t),(7,4),(7,7)],'pine3');q.p([(9,5),(11,2-t),(12,4),(11,6)],'mint')
        face(q,d,1 if side else 2,6,'wood5',cast)
        a.dot(7+s,14,'wood4')
    return finish(a,d)

def horseshoe(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=beat(f,cast);q=Pen(a,h if cast is not None else (t if v==2 else 0),cast==0);side=d in ('left','right')
    for j,x in enumerate((4,8,11)):
        k=(s,t,-s)[j];a.l([(x,9),(x+k,12),(x+k-1,13)],'ink');a.dot(x+k,12,'skin2')
    a.l([(10,10),(12,12),(13+s,14)],'ink');a.dot(12,12,'silver')
    if v==0:
        q.p([(2,9),(2,6),(4,3),(8,2),(12,4),(13,8),(11,10),(9,7),(6,7),(4,10)],'ink')
        q.l([(3,8),(3,6),(5,4),(8,3),(11,5),(12,8)],'silver',2);q.dot(6,3,'white')
        face(q,d,1 if side else 4,7,'purple3',cast)
    elif v==1:
        q.p([(2,10),(2,4),(4,1),(6,2),(6,5),(4,6),(4,9)],'ink');q.l([(3,8),(3,4),(4,2),(5,3)],'silver')
        q.p([(9,2),(11,1),(13,4),(13,10),(11,9),(11,6),(9,5)],'ink');q.l([(10,3),(11,2),(12,4),(12,8)],'white')
        face(q,d,2 if side else 5,8,'purple3',cast,5)
        a.l([(12,12),(14,12),(13,14)],'silver')
    else:
        q.r((1,3,14,10),'ink');q.r((2,4,13,9),'silver');q.l([(2,4),(13,4)],'white')
        q.r((3,5,5,7),'ink');q.r((3,5,4,6),'transparent')
        q.r((8,5,12,8),'ink');q.r((9,6,11,7),'transparent')
        q.l([(2,9),(12,9)],'purple2');face(q,d,1 if side else 4,9,'purple3',cast)
    return finish(a,d)

def worm(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=beat(f,cast);q=Pen(a,h,cast==0);side=d in ('left','right')
    if v==0:
        for x in (5,8,10):a.l([(8,10),(x+s,13),(x+s,14)],'ink');a.dot(x+s,13,'skin2')
        q.e((5,7,10,12),'ink');q.e((6,8,9,11),'skin2')
        for x,y in ((2,3+s),(5,2),(9,2-t),(13,3)):
            q.l([(7,7),(x,y)],'ink',2);q.l([(7,6),(x,y)],'fire2');q.dot(x,y,'gold4')
        face(q,d,2 if side else 4,6,'skin2',cast)
    elif v==1:
        a.l([(8,10),(10+s,12),(9,14),(5,14),(4,12)],'ink',2);a.l([(8,11),(9+s,12),(8,13),(5,13)],'skin2')
        q.l([(7,10),(8,6)],'ink',4);q.l([(7,10),(8,6)],'skin1',2)
        q.l([(6,7),(2,6),(1,3),(3+t,1),(6,2)],'ink',2);q.l([(5,6),(2,4),(3,2),(5,3)],'fire2')
        q.l([(9,5),(12,5),(14,3),(12,1),(9,1)],'ink',2);q.l([(10,4),(12,4),(13,3),(11,2)],'gold3')
        q.dot(2,5+t,'gold4');q.dot(12,3-t,'fire2')
        face(q,d,2 if side else 5,6,'skin2',cast,5)
    else:
        a.l([(3,11),(6,12),(10,11),(12,10),(14,11+t)],'ink',3);a.l([(3,11),(6,11),(10,10),(12,10)],'skin2')
        for j,x in enumerate((3,6,9,12)):
            y=7+(s if j%2 else t);q.p([(x-1,10),(x-1,y),(x,y-2),(x+1,y),(x+1,10)],'ink');q.l([(x,y+1),(x,y-1)],'fire2' if (j+f)%4 else 'gold4')
        face(a,d,1 if side else 2,9,'skin2',cast,5)
        a.l([(11,12),(12,13),(13,13-s)],'gold3')
    return finish(a,d)

def star(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=beat(f,cast);q=Pen(a,h,cast==0);side=d in ('left','right')
    if v==0:
        pts=[(7,2),(9,5),(13,5+t),(11,9),(12-s,13),(8,11),(4+s,14),(4,10),(1,7),(5,6)]
        q.p(pts,'ink');q.p([(7,3),(8,6),(12,6+t),(10,9),(11-s,12),(8,10),(5+s,12),(5,9),(3,7),(6,7)],'pine4')
        q.l([(3,7),(5,8)],'mint');q.l([(10,10),(11-s,12)],'wood5')
        face(q,d,2 if side else 5,6,'leafwarm',cast,5)
    elif v==1:
        q.p([(6,5),(6+t,1),(8+t,1),(9,5),(13,5),(14,7),(9,8),(10,12),(8,14),(6,9),(2,10),(1,8),(5,6)],'ink')
        q.l([(7,2),(7,7),(8,12)],'pine5',2);q.l([(2,9),(6,7),(12,6)],'pine4',2)
        a.l([(7,10),(5+s,13)],'wood5');a.dot(11,6+t,'mint')
        face(q,d,2 if side else 5,5,'leafwarm',cast,5)
    else:
        q.l([(3,9),(5,12),(8,8),(10,12),(13,8)],'ink',3);q.l([(3,9),(5,11),(8,8),(10,11),(13,8)],'pine4')
        a.l([(5,11),(4+s,14)],'ink',2);a.l([(10,11),(11-s,14)],'ink',2)
        q.l([(3,7),(1,5+t),(3,4)],'ink',2);q.l([(7,7),(8,4-t),(10,4)],'ink',2)
        q.dot(1,5+t,'mint');q.dot(9,4-t,'wood5');face(q,d,1 if side else 2,6,'leafwarm',cast,5)
    return finish(a,d)

def eel(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=beat(f,cast);q=Pen(a,h,cast==0);side=d in ('left','right')
    if v==0:
        q.l([(3,6),(5,8),(8,7+s),(11,9),(12,12),(14,13+t)],'ink',3)
        q.l([(4,6),(5,7),(8,7+s),(11,9),(12,12),(14,13+t)],'purple3')
        for x,y in ((5,8),(8,7+s),(11,9)):q.l([(x-1,y-1),(x,y-1),(x+1,y+1)],'silver');q.dot(x-1,y-1,'white')
        face(q,d,1 if side else 2,4,'purple3',cast,5)
    elif v==1:
        q.l([(4,5),(4,11),(10+s,11),(12,6),(14,7+t)],'ink',3);q.l([(4,6),(4,10),(10+s,10),(12,6)],'purple2')
        q.l([(5,10),(8,10)],'silver');q.l([(12,6),(13,7+t)],'white')
        q.p([(1,3),(3,2),(6,3),(7,6),(6,8),(3,8),(1,6)],'ink');q.l([(2,4),(3,3),(5,4)],'silver')
        face(q,d,1 if side else 2,4,'purple3',cast,5);q.l([(2,8),(5,9),(7,7)],'silver')
    else:
        q.l([(6,6),(3,6),(2,9),(3,12+t),(6,13),(8,11),(8,8),(11,7),(13,8),(13,11),(11,12),(8,10),(7,7),(8,4),(11,3),(12+t,4+s)],'ink',2)
        q.l([(5,7),(3,8),(3,10),(5,12),(7,11),(7,8),(10,8),(12,9),(12,11),(10,11)],'silver')
        q.dot(4,6+t,'white');q.dot(12,9-t,'purple3')
        face(q,d,5 if side else 6,3,'purple3',cast,5)
    return finish(a,d)

def jelly(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=beat(f,cast);q=Pen(a,h,cast==0);side=d in ('left','right')
    if v==0:
        q.e((3+t,2,12,11),'ink');q.e((4+t,3,11,10),'water3')
        for j,x in enumerate((4,6,9,11)):q.l([(x,4),(x+(s if j%2 else t),6),(x,9)],'watergleam' if (j+f)%4 else 'purple3')
        a.l([(6,10),(5+s,13),(7,14)],'ink',2);a.l([(9,10),(10-s,13),(8,14)],'ink',2);a.dot(6+s,13,'water4');a.dot(9-s,13,'watergleam')
        face(q,d,2 if side else 5,7,'water4',cast,5)
    elif v==1:
        q.p([(7,1),(12,5),(11,10),(8,13),(3,9),(2,5)],'ink');q.p([(7,2),(11,5),(10,9),(8,12),(4,8),(3,5)],'blue3')
        q.l([(3,7+t),(6,4),(10,4),(12,7-t),(9,10),(6,9)],'watergleam',2);q.l([(4,8),(10,3)],'purple3')
        a.l([(6,11),(4+s,14)],'ink');a.l([(9,11),(11-s,14)],'ink');a.dot(5+s,13,'water4');a.dot(10-s,13,'watergleam')
        face(q,d,2 if side else 5,6,'watergleam',cast,5)
    else:
        q.p([(7,3),(10,5),(13-s,11),(12-s,13),(3+t,13),(2+t,11),(5,5)],'ink');q.l([(7,4),(12-s,11),(3+t,11),(7,4)],'water4',3)
        q.p([(7,7),(9,10),(5,10)],'transparent');q.l([(3,11),(4+s,13)],'blue3');q.l([(12,11),(11-s,13)],'purple3')
        a.dot(2,12+t,'watergleam');a.dot(13,12-t,'watergleam')
        face(q,d,3 if side else 5,3,'watergleam',cast,5)
    return finish(a,d)
DRAWERS=(cuttle,clam,seahorse,horseshoe,worm,star,eel,jelly)
def field(form_id,d,f,cast=None):
    if type(form_id)!=int or form_id not in FORM_IDS or d not in DIRECTIONS or type(f)!=int or not 0<=f<4 or (cast is not None and (type(cast)!=int or not 0<=cast<3)):raise ValueError('Invalid art identity/direction/frame/pose')
    n=form_id-49;im=DRAWERS[n//3](n%3,d,f,cast)
    # Native actor tiles retain their transparent outer boundary. Deliberately
    # inset to keep neighbour tiles clean when streamed through shared OBJ slots.
    return im

def peye(a,x,y):
    a.e((x,y,x+3,y+5),'ink');a.r((x+1,y,x+2,y+3),'white');a.r((x+1,y+2,x+2,y+4),'ink');a.dot(x+1,y+1,'white')
def pface(a,x,y,c,w=12):
    a.e((x,y,x+w,y+9),'ink');a.e((x+1,y+1,x+w-1,y+8),c)
    peye(a,x+2,y+1);peye(a,x+w-5,y+1);a.l([(x+w//2-1,y+7),(x+w//2+1,y+7)],'rose0');a.dot(x+2,y+6,'rose4')
def portrait(form_id):
    if type(form_id)!=int or form_id not in FORM_IDS:raise ValueError('Invalid portrait form')
    a=Art(32,32,'transparent');family,v=divmod(form_id-49,3)
    # Separate 32px compositions, larger curved anatomy and facial features.
    # These paths are not a nearest-neighbour enlargement of a walk frame.
    if family==0:
        if v==0:
            a.p([(14,2),(20,5),(23,11),(23,18),(18,23),(9,22),(6,15),(9,6)],'ink');a.p([(14,4),(19,7),(21,12),(20,18),(11,19),(9,13),(11,7)],'purple2')
            a.l([(13,6),(15,5),(18,8)],'purple3',2)
            a.p([(7,10),(3,13),(2,19),(7,22)],'water4');a.p([(23,9),(28,13),(29,19),(23,22)],'skin2')
            for x in (6,10,14,18,22,25):a.l([(x,22),(x-1,26),(x+1,29)],'ink',3);a.l([(x,23),(x,27)],'water4')
            a.l([(5,19),(3,23),(3,28),(6,29)],'purple3',2);a.l([(26,19),(29,24),(28,28),(25,29)],'purple3',2)
            pface(a,8,15,'water4',14)
        elif v==1:
            a.r((10,2,21,21),'ink');a.r((11,3,20,20),'purple1');a.l([(12,4),(18,4)],'purple3',2)
            for x,sg in ((9,-1),(22,1)):
                a.p([(x,3),(x+sg*3,5),(x,8),(x+sg*3,11),(x,14),(x+sg*3,18),(x,21)],'water4')
                a.l([(x,22),(x+sg*3,24),(x+sg*3,29),(x+1,30)],'ink',3);a.l([(x,23),(x+sg*2,25),(x+sg*2,28)],'skin2')
            a.l([(12,23),(12,27),(15,28)],'water4',2);a.l([(19,23),(19,27),(17,29)],'water4',2);pface(a,9,15,'water4',13)
        else:
            a.e((11,2,21,15),'ink');a.e((12,3,20,14),'purple2')
            for pts,inside,c in (([(13,16),(4,7),(1,15),(4,24),(11,28),(16,20)],[(11,17),(5,11),(3,16),(6,22),(11,25),(14,20)],'skin2'), ([(18,16),(26,6),(30,13),(28,23),(22,28),(16,21)],[(20,17),(26,9),(28,14),(26,22),(21,25),(18,21)],'water4')):
                a.p(pts,'ink');a.p(inside,c)
            for pts in ([(5,15),(12,21)],[(4,20),(12,23)],[(26,13),(21,20)],[(27,19),(22,23)]):a.l(pts,'purple3')
            pface(a,10,12,'water4',12)
    elif family==1:
        a.p([(6,23),(23,21),(28,26),(24,29),(19,28),(13,30),(4,28),(3,25)],'ink');a.l([(5,26),(10,28),(15,26),(22,27),(26,25)],'skin2',3)
        if v==0:
            a.p([(3,18),(4,11),(9,5),(16,3),(24,8),(28,14),(26,20)],'ink');a.p([(5,17),(6,11),(11,6),(16,5),(22,9),(26,14),(24,18)],'stone5')
            for x in (9,14,20,24):a.l([(15,20),(x,9)],'wood4')
            a.p([(3,22),(10,20),(22,20),(28,22),(24,26),(8,27)],'ink');a.l([(5,23),(11,25),(21,24),(26,22)],'wood5',2);pface(a,8,17,'skin2',14)
        elif v==1:
            a.p([(1,14),(5,8),(16,6),(28,11),(30,16),(25,20),(4,20)],'ink');a.p([(3,14),(6,10),(16,8),(26,12),(28,15),(24,17),(5,17)],'stone5')
            a.l([(7,12),(18,10),(25,13)],'wood4');a.p([(2,23),(12,21),(15,26),(19,21),(30,21),(25,28),(19,29),(15,26),(11,29),(5,28)],'ink');a.l([(4,24),(9,27),(12,26)],'wood5',2);a.l([(19,27),(24,26),(27,23)],'stone5',2);pface(a,5,16,'skin2',17)
        else:
            a.p([(7,21),(2,13),(3,3),(8,5),(13,14),(14,21)],'ink');a.p([(7,18),(4,12),(5,6),(8,8),(11,15)],'wood5')
            a.p([(17,21),(19,11),(26,2),(30,6),(28,15),(23,22)],'ink');a.p([(20,18),(22,12),(27,5),(28,8),(26,15)],'stone5')
            a.e((9,24,23,30),'ink');a.e((10,25,22,29),'skin2');pface(a,9,18,'skin2',13)
    elif family==2:
        if v==0:
            a.l([(17,15),(20,21),(18,28),(12,29),(9,26),(11,23)],'ink',5);a.l([(17,16),(18,22),(16,27),(12,27),(11,25)],'wood4',2)
            a.p([(11,8),(14,2),(18,5),(23,3),(21,12)],'ink');a.p([(13,8),(15,4),(18,7),(21,5),(19,11)],'pine5')
            a.p([(10,17),(3,13),(4,21),(10,22)],'pine5');a.p([(21,16),(28,14),(27,22),(22,22)],'mint');pface(a,7,9,'wood5',14)
        elif v==1:
            a.l([(6,21),(3,13),(5,5),(10,2),(12,6),(22,6),(25,2),(29,6),(29,16),(25,22)],'ink',2)
            a.l([(6,18),(5,10),(8,6),(11,5)],'pine5',2);a.l([(24,5),(27,8),(27,17)],'mint',2)
            for y in (8,13):a.l([(6,y),(26,y)],'pine3',2)
            a.l([(17,20),(20,25),(19,30)],'ink',5);a.l([(17,21),(18,26),(18,29)],'wood4',2)
            a.p([(12,21),(6,25),(10,28)],'pine5');a.p([(22,20),(28,25),(24,27)],'mint');pface(a,10,12,'wood5',13)
        else:
            a.l([(12,17),(15,8),(22,7),(28,12),(27,22),(21,28),(14,27),(12,23),(15,19)],'ink',5)
            a.l([(13,17),(17,10),(22,10),(26,14),(24,23),(20,26),(15,25),(14,22)],'pine5',2)
            a.l([(22,23),(23,18),(20,17)],'wood5',2);a.p([(10,14),(7,5),(13,7),(16,13)],'pine3');a.p([(19,9),(24,2),(27,7),(24,11)],'mint');pface(a,2,13,'wood5',13)
    elif family==3:
        for x in (7,15,23):a.l([(x,20),(x-2,25),(x-4,28)],'ink',3);a.l([(x,21),(x-2,25)],'skin2')
        a.l([(23,21),(27,24),(28,30)],'ink',2)
        if v==0:
            a.p([(3,21),(2,13),(7,5),(16,2),(25,7),(29,16),(26,22),(20,16),(11,16),(6,23)],'ink')
            a.l([(4,18),(5,12),(9,7),(16,4),(23,8),(26,16)],'silver',3);a.l([(9,7),(15,5),(20,7)],'white')
            pface(a,8,16,'purple3',14)
        elif v==1:
            a.p([(3,21),(3,9),(7,2),(12,4),(12,10),(8,13),(8,21)],'ink');a.l([(5,18),(5,9),(8,4),(10,6)],'silver',2)
            a.p([(19,4),(24,2),(29,9),(28,22),(24,20),(24,13),(20,10)],'ink');a.l([(22,6),(24,4),(27,10),(26,19)],'white',2)
            a.l([(26,25),(30,25),(28,29)],'silver',2);pface(a,9,18,'purple3',13)
        else:
            a.r((2,5,29,22),'ink');a.r((3,6,28,21),'silver');a.l([(4,7),(27,7)],'white',2)
            a.r((6,9,13,15),'ink');a.r((7,10,11,13),'transparent');a.r((17,10,26,18),'ink');a.r((18,11,24,16),'transparent')
            a.l([(5,20),(24,20)],'purple2');pface(a,7,20,'purple3',14)
    elif family==4:
        if v==0:
            for x in (8,16,23):a.l([(16,23),(x,27),(x-1,30)],'ink',3);a.dot(x,28,'skin2')
            a.e((11,18,22,27),'ink');a.e((12,19,21,26),'skin2')
            for x,y in ((3,7),(9,2),(19,2),(28,6)):
                a.l([(16,15),(x,y)],'ink',3);a.l([(16,14),(x,y)],'fire2',2);a.dot(x,y,'gold4')
            pface(a,8,13,'skin2',15)
        elif v==1:
            a.l([(16,23),(22,27),(18,30),(10,29),(7,26)],'ink',3);a.l([(16,24),(20,27),(17,28),(11,27)],'skin2',2)
            a.l([(15,23),(17,13)],'ink',7);a.l([(15,23),(17,14)],'skin1',3)
            a.l([(13,13),(5,11),(2,6),(6,2),(12,4)],'ink',3);a.l([(11,11),(5,8),(6,4),(11,6)],'fire2',2)
            a.l([(19,10),(25,9),(29,5),(26,2),(19,2)],'ink',3);a.l([(21,8),(25,7),(27,5),(24,4),(20,4)],'gold3',2);pface(a,10,13,'skin2',13)
        else:
            a.l([(5,22),(11,25),(19,23),(25,20),(29,22)],'ink',5);a.l([(5,22),(11,23),(19,21),(25,20)],'skin2',2)
            for j,x in enumerate((7,13,19,25)):
                y=13+j%2*2;a.p([(x-2,22),(x-3,y),(x,y-5),(x+2,y),(x+2,21)],'ink');a.l([(x,y+4),(x,y-3)],'fire2',2);a.dot(x,y-4,'gold4')
            a.l([(24,24),(27,27),(29,26)],'gold3',2);pface(a,2,19,'skin2',12)
    elif family==5:
        if v==0:
            a.p([(14,2),(19,10),(29,9),(24,18),(27,29),(17,25),(7,30),(7,20),(1,13),(11,11)],'ink')
            a.p([(14,5),(17,13),(26,12),(22,18),(24,26),(17,22),(9,27),(10,20),(4,14),(12,14)],'pine4')
            a.l([(5,14),(10,17)],'mint',2);a.l([(21,21),(23,25)],'wood5',2);pface(a,10,12,'leafwarm',12)
        elif v==1:
            a.p([(12,11),(12,1),(17,2),(19,10),(29,11),(30,16),(20,18),(22,28),(17,30),(12,20),(3,24),(1,18),(10,13)],'ink')
            a.l([(15,4),(15,15),(18,27)],'pine5',4);a.l([(4,20),(13,16),(27,13)],'pine4',3)
            a.l([(14,23),(10,28)],'wood5',2);pface(a,9,10,'leafwarm',13)
        else:
            a.l([(5,20),(10,27),(17,18),(22,25),(29,17)],'ink',5);a.l([(5,20),(10,24),(17,18),(22,23),(28,17)],'pine4',2)
            a.l([(10,26),(8,30)],'ink',3);a.l([(22,25),(25,30)],'ink',3)
            a.l([(6,16),(2,10),(6,7)],'ink',3);a.l([(14,15),(17,6),(22,8)],'ink',3);a.l([(3,10),(5,8)],'mint',2);a.l([(18,7),(21,8)],'wood5',2);pface(a,3,14,'leafwarm',13)
    elif family==6:
        if v==0:
            a.l([(7,12),(12,17),(18,14),(23,19),(25,25),(30,28)],'ink',5);a.l([(8,12),(12,15),(18,13),(24,19),(26,25),(30,27)],'purple3',2)
            for x,y in ((12,17),(18,14),(23,19)):a.l([(x-2,y-3),(x+1,y-2),(x+3,y+2)],'silver',2);a.dot(x-2,y-3,'white')
            pface(a,2,5,'purple3',12)
        elif v==1:
            a.l([(9,10),(9,25),(23,25),(27,12),(30,14)],'ink',5);a.l([(9,12),(10,23),(22,23),(27,12)],'purple2',2)
            a.l([(12,23),(18,23)],'silver',2);a.l([(27,13),(29,14)],'white',2)
            a.p([(2,7),(5,2),(12,4),(16,9),(15,16),(9,19),(3,16)],'ink');a.l([(4,7),(6,4),(11,6)],'silver',2)
            pface(a,3,7,'purple3',12);a.l([(4,17),(10,19),(15,15)],'silver',2)
        else:
            a.l([(13,13),(7,12),(3,18),(6,26),(12,29),(17,24),(17,17),(23,14),(28,17),(28,24),(24,27),(17,22),(14,15),(17,8),(24,6),(27,9)],'ink',4)
            a.l([(11,14),(6,16),(5,21),(8,26),(12,27),(15,23),(15,17),(21,16),(26,18),(26,23),(23,24),(18,21)],'silver',2)
            pface(a,13,4,'purple3',13)
    else:
        if v==0:
            a.e((6,2,26,25),'ink');a.e((7,3,25,24),'water3')
            for x in (9,13,18,23):a.l([(x,6),(x-1,12),(x,20)],'watergleam',2);a.dot(x,9,'purple3')
            a.l([(12,22),(10,27),(14,30)],'ink',3);a.l([(20,22),(23,28),(18,30)],'ink',3);a.l([(12,24),(12,27)],'water4');a.l([(21,24),(21,28)],'watergleam');pface(a,10,16,'water4',13)
        elif v==1:
            a.p([(15,1),(26,9),(24,20),(18,28),(7,22),(3,12)],'ink');a.p([(15,3),(24,10),(22,20),(18,25),(9,20),(5,12)],'blue3')
            a.l([(5,15),(12,7),(22,8),(27,15),(20,23),(12,20)],'watergleam',3);a.l([(7,20),(23,5)],'purple3',2)
            a.l([(12,24),(9,30)],'ink',2);a.l([(21,24),(26,30)],'ink',2);pface(a,10,13,'watergleam',13)
        else:
            a.p([(15,4),(21,9),(30,25),(28,29),(3,29),(1,25),(10,10)],'ink');a.l([(15,7),(26,25),(5,25),(15,7)],'water4',5)
            a.p([(15,15),(21,23),(10,23)],'transparent');a.l([(5,25),(9,28)],'blue3',2);a.l([(26,25),(23,28)],'purple3',2)
            a.dot(5,26,'white');a.dot(27,26,'white');pface(a,10,6,'watergleam',12)
    return a.im

def mask(im):return Image.frombytes('L',im.size,bytes(255 if n else 0 for n in im.tobytes()))
def paste(target,im,xy):target.paste(im.convert(target.mode),xy,mask(im))
def normalized_mask(im):
    m=mask(im);box=m.getbbox();return (box[2]-box[0],box[3]-box[1],m.crop(box).tobytes())
def save_image(im,path):
    if im.mode=='P':im.save(path,transparency=0,optimize=False)
    else:im.save(path,optimize=False)
def validate_pixels(fields,abilities,portraits):
    catalog={f['id']:f for f in load_catalog(ROOT/'assets/creatures/catalog.json')['forms']}
    assert tuple(f['id'] for f in BRIEFS)==FORM_IDS
    assert tuple(catalog[i]['name'] for i in FORM_IDS)==NAMES
    assert {f['phase'] for f in BRIEFS}=={'water','earth','wood','metal','fire'}
    assert {f['polarity'] for f in BRIEFS}=={'yin','yang'}
    allimgs=[s for group in (fields,abilities) for row in group for direction in row for s in direction]+portraits
    for im in allimgs:
        assert im.mode=='P' and im.getpalette()==PAL and 0 in im.tobytes() and max(im.tobytes())<97
    for i,row in enumerate(fields):
        for d in range(4):
            walk=row[d];cast=abilities[i][d];group=walk+cast
            assert len({s.tobytes() for s in group})==7,(NAMES[i],DIRECTIONS[d],'seven poses')
            assert len({normalized_mask(s) for s in walk})==4,(NAMES[i],DIRECTIONS[d],'four articulated walk silhouettes')
            assert len({normalized_mask(s) for s in cast})==3,(NAMES[i],DIRECTIONS[d],'three cast silhouettes')
            for im in group:
                assert im.size==(16,16)
                assert all(im.getpixel((x,y))==0 for x in range(16) for y in (0,15)),(NAMES[i],'horizontal safety boundary')
                assert all(im.getpixel((x,y))==0 for x in (0,15) for y in range(16)),(NAMES[i],'vertical safety boundary')
                assert 35<=sum(bool(n) for n in im.tobytes())<=205,(NAMES[i],'occupancy')
        assert len({s[0].tobytes() for s in row})==4,(NAMES[i],'four views')
        assert all(row[3][f].tobytes()==row[2][f].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes() for f in range(4))
        assert portraits[i].size==(32,32) and portraits[i].tobytes()!=row[0][0].resize((32,32),Image.Resampling.NEAREST).tobytes()
    assert len({mask(p).tobytes() for p in portraits})==24
    return {'images':696,'field_dimensions':[24,4,4,256],'ability_dimensions':[24,4,3,256],'portrait_dimensions':[24,1024],
      'actor_palette_entries':97,'palette_indices':sorted({n for im in allimgs for n in im.tobytes()}),'transparent_zero':True,
      'transparent_outer_field_boundary':True,'articulated_walk_masks_per_direction':4,'articulated_cast_masks_per_direction':3,
      'independently_composed_native_portraits':True,'catalog_identity_match':True}
SCENE_SOURCES=(('NACRE','nacreway.png',(218,236,242,260)),('SILT','siltglass_commons.png',(226,214,250,238)),
 ('KELP','kelp_promenade.png',(184,176,208,200)),('CHALK','hollow_oyster_garden.png',(224,176,248,200)),
 ('SHADE','countercurrent_stacks.png',(102,188,126,212)))
def make_previews(fields,abilities,portraits):
    patches=[];sources=[]
    for name,filename,box in SCENE_SOURCES:
        path=ROOT/'assets/underwater_region'/filename
        with Image.open(path) as im:patches.append(im.convert('RGB').crop(box))
        sources.append({'name':name,'path':str(path.relative_to(ROOT)),'crop':list(box),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    roster=Image.new('RGB',(480,304),RGB[P['dirt4']]);rd=ImageDraw.Draw(roster)
    allframes=Image.new('RGB',(384,24*92+20),RGB[P['dirt4']]);ad=ImageDraw.Draw(allframes);ad.text((3,3),'ART REVIEW: W0 W1 W2 W3 | ANTICIPATE RELEASE SETTLE',fill=RGB[1])
    for i,(fid,key,name) in enumerate(zip(FORM_IDS,KEYS,NAMES)):
        w=Art(64,64,'transparent').im;c=Art(48,64,'transparent').im
        for d in range(4):
            for f in range(4):w.paste(fields[i][d][f],(16*f,16*d))
            for p in range(3):c.paste(abilities[i][d][p],(16*p,16*d))
        save_image(w,OUT/f'{key}_walk.png');save_image(c,OUT/f'{key}_ability.png');save_image(portraits[i],OUT/f'{key}_portrait.png')
        native=Image.new('RGB',(240,176),RGB[P['deep']]);nd=ImageDraw.Draw(native);nd.text((4,3),f'{fid} {name} / ART REVIEW',fill=RGB[P['white']]);paste(native,portraits[i],(204,28))
        for bg,y in (('deep',24),('dirt4',105)):
            nd.rectangle((0,y-2,199,y+65),fill=RGB[P[bg]])
            for d in range(4):
                for n,im in enumerate(fields[i][d]+abilities[i][d]):paste(native,im,(2+n*28,y+d*16))
        save_image(native,OUT/f'{key}_native.png');save_image(native.resize((720,528),Image.Resampling.NEAREST),OUT/f'{key}_3x.png')
        terrain=Image.new('RGB',(len(patches)*168,116),RGB[P['deep']]);td=ImageDraw.Draw(terrain)
        for t,(name,_,_) in enumerate(SCENE_SOURCES):
            td.text((t*168+3,2),name+' / '+str(fid),fill=RGB[P['white']])
            for d in range(4):
                for f,im in enumerate(fields[i][d]+abilities[i][d]):
                    tile=patches[t].copy();paste(tile,im,(4,4));terrain.paste(tile,(t*168+f*24,18+d*24))
        save_image(terrain,OUT/f'{key}_terrain_native.png')
        anim=[]
        for f in range(7):
            tile=Image.new('RGB',(128,48),RGB[P['dirt4']]);td=ImageDraw.Draw(tile);td.text((2,1),f'{fid} {NAMES[i]}',fill=RGB[1])
            for d in range(4):paste(tile,(fields[i][d]+abilities[i][d])[f],(8+d*30,23))
            anim.append(tile)
        anim[0].save(OUT/f'{key}_motion.gif',save_all=True,append_images=anim[1:],duration=[n*1000//60 for n in WALK_TICKS[i]]+[180,110,180],loop=0,disposal=2,optimize=False)
        x=(i%6)*80;y=(i//6)*76;rd.text((x+2,y+2),NAMES[i],fill=RGB[1]);rd.text((x+43,y+22),str(fid),fill=RGB[1]);paste(roster,portraits[i],(x+3,y+17))
        for d in range(4):paste(roster,fields[i][d][0],(x+d*18+2,y+56))
        ay=20+i*92;ad.text((3,ay),f'{fid} {NAMES[i]}',fill=RGB[1]);paste(allframes,portraits[i],(338,ay+30))
        for d in range(4):
            ad.text((3,ay+13+d*18),DIRECTIONS[d][0].upper(),fill=RGB[1])
            for n,im in enumerate(fields[i][d]+abilities[i][d]):paste(allframes,im,(20+n*42,ay+13+d*18))
    save_image(roster,OUT/'roster_native.png');save_image(roster.resize((960,608),Image.Resampling.NEAREST),OUT/'roster_2x.png')
    save_image(allframes,OUT/'all_frames_native.png');save_image(allframes.resize((768,allframes.height*2),Image.Resampling.NEAREST),OUT/'all_frames_2x.png')
    # Review composites preserve scene pixels and scale; not emulator evidence.
    with Image.open(ROOT/'assets/underwater_region/nacreway.png') as im:scene=im.convert('RGB').crop((112,112,352,272))
    gif=[]
    for f in range(4):
        frame=scene.copy()
        for i in range(24):
            x=10+(i%6)*38;y=24+(i//6)*31;dr=ImageDraw.Draw(frame);dr.ellipse((x+4,y+12,x+12,y+15),fill=RGB[P['shadow']]);paste(frame,fields[i][i%4][f],(x,y))
        gif.append(frame)
    save_image(gif[0],OUT/'nacreway_composite_native.png');save_image(gif[0].resize((720,480),Image.Resampling.NEAREST),OUT/'nacreway_composite_3x.png')
    gif[0].save(OUT/'roster_walk_native.gif',save_all=True,append_images=gif[1:],duration=130,loop=0,disposal=2,optimize=False)
    return sources,patches

def silhouette_metrics(fields):
    current=[mask(row[0][0]).tobytes() for row in fields];assert len(set(current))==24
    oldmanifest=json.loads((ROOT/'assets/magma_creatures/manifest.json').read_text());oldids=oldmanifest['silhouette_comparison']['released_form_ids']+oldmanifest['form_ids'];assert len(oldids)==65
    src=Image.open(ROOT/'assets/magma_creatures/released65_silhouettes_native.png').convert('RGB')
    sheet=Image.new('RGB',(560,576),RGB[P['white']]);dr=ImageDraw.Draw(sheet);dr.text((4,3),'89 NATIVE SILHOUETTES / RELEASED65 + UNDERWATER24 / ART REVIEW',fill=RGB[1]);oldmasks=[]
    for i,fid in enumerate(oldids+list(FORM_IDS)):
        x=i%7*80;y=24+i//7*42;dr.text((x+4,y),str(fid),fill=RGB[1])
        for d in range(4):
            if i<65:
                sx=i%7*80+4+d*18;sy=23+i//7*42+13;tile=src.crop((sx,sy,sx+16,sy+16));m=Image.new('L',(16,16));m.putdata([255 if px==RGB[1] else 0 for px in getattr(tile,'get_flattened_data',tile.getdata)()])
                if d==0:oldmasks.append(m.tobytes())
            else:m=mask(fields[i-65][d][0])
            sheet.paste(Image.new('RGB',(16,16),RGB[1]),(x+4+d*18,y+13),m)
    assert not set(current).intersection(oldmasks),'Prior released silhouette duplicated'
    save_image(sheet,OUT/'released89_silhouettes_native.png');save_image(sheet.resize((1120,1152),Image.Resampling.NEAREST),OUT/'released89_silhouettes_2x.png')
    branch=[]
    for i in range(0,24,3):
        distances=[sum(x!=y for x,y in zip(mask(fields[i+1][d][0]).tobytes(),mask(fields[i+2][d][0]).tobytes())) for d in range(4)]
        assert min(distances)>=12,(i,distances)
        branch.append({'family_id':f'F{17+i//3:03}','branches':[FORM_IDS[i+1],FORM_IDS[i+2]],'different_mask_pixels_by_direction':distances})
    return {'current_unique_front_masks':24,'released_form_ids':oldids,'cross_release_front_mask_matches':0,'branch_distances':branch}
def terrain_metrics(fields,abilities,patches):
    rows=[]
    for i,fid in enumerate(FORM_IDS):
        for t,patch in enumerate(patches):
            ratios=[];edge_ratios=[]
            for group in (fields[i],abilities[i]):
                for direction in group:
                    for im in direction:
                        n=good=en=egood=0
                        for y in range(16):
                            for x in range(16):
                                p=im.getpixel((x,y))
                                if not p:continue
                                visible=sum((v-w)**2 for v,w in zip(RGB[p],patch.getpixel((x+4,y+4))))>=48**2;n+=1;good+=visible
                                if any(im.getpixel((xx,yy))==0 for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))):en+=1;egood+=visible
                        ratios.append(good/n);edge_ratios.append(egood/en)
            rows.append({'form_id':fid,'terrain':SCENE_SOURCES[t][0],'minimum_distinct_opaque_fraction':round(min(ratios),4),'minimum_distinct_boundary_fraction':round(min(edge_ratios),4)})
    return {'metric':'Native RGB555 distance >=48; all28 poses per terrain. Visibility heuristic, not emulator/gameplay/performance evidence.',
      'samples':24*28*len(patches),'rows':rows,'minimum_opaque_fraction':min(r['minimum_distinct_opaque_fraction'] for r in rows),'minimum_boundary_fraction':min(r['minimum_distinct_boundary_fraction'] for r in rows)}
def validate_legacy_prefix(world_successor=None):
    from legacy_art_successor import validate_legacy_prefix as validate
    return validate(ROOT,OUT/'legacy_prefix_sha256.json',world_successor)
def output_hashes():
    files=sorted(p for p in OUT.iterdir() if p.is_file() and p.suffix in ('.png','.gif','.json','.txt') and p.name not in ('validation.json',))
    files+=sorted((ROOT/'src/underwater_creature_art_data').glob('*.inc'))+[ROOT/'src/underwater_creature_art.c',ROOT/'src/underwater_creature_art.h']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
def generate(world_successor=None):
    OUT.mkdir(exist_ok=True);legacy=validate_legacy_prefix(world_successor)
    fields=[[[field(fid,d,f) for f in range(4)] for d in DIRECTIONS] for fid in FORM_IDS]
    abilities=[[[field(fid,d,p,cast=p) for p in range(3)] for d in DIRECTIONS] for fid in FORM_IDS];portraits=[portrait(fid) for fid in FORM_IDS]
    validation=validate_pixels(fields,abilities,portraits)
    spec=importlib.util.spec_from_file_location('underwater_creature_codegen',OUT/'codegen.py');cg=importlib.util.module_from_spec(spec);spec.loader.exec_module(cg)
    chunks=cg.emit_code(ROOT,FORM_IDS,NAMES,fields,abilities,portraits)
    sources,patches=make_previews(fields,abilities,portraits);comparison=silhouette_metrics(fields);terrain=terrain_metrics(fields,abilities,patches)
    (OUT/'terrain_readability.json').write_text(json.dumps(terrain,indent=2)+'\n')
    manifest={'schema_version':1,'generator':'assets/generate_underwater_creatures.py','form_ids':list(FORM_IDS),'names':list(NAMES),'directions':list(DIRECTIONS),
      'status':'ART ONLY: sprite sheets and scene composites are not emulator captures or proof of unlocks, live rendering, or acceptance.',
      'rights':'Original code-native pixel geometry. No Nintendo/Pokemon extraction, tracing, or third-party raster inputs.',
      'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'codegen_sha256':hashlib.sha256((OUT/'codegen.py').read_bytes()).hexdigest(),
      'palette_sha256':hashlib.sha256(json.dumps(COLORS).encode()).hexdigest(),'data_bytes':cg.DATA_BYTES,'runtime_data_bytes':0,'runtime_bss_bytes':0,
      'persistent_obj_allocation_bytes':0,'rom_budget_bytes':cg.ROM_BUDGET_BYTES,'include_bytes':chunks,'max_include_bytes':max(chunks),'scene_review_sources':sources,
      'anchor':[8,8],'shadow_anchor':[8,13],'shadow_in_sprite':False,'idle_frame':0,'walk_ticks_by_form':dict(zip(map(str,FORM_IDS),WALK_TICKS)),
      'ability_poses':['anticipation','release','settle'],'briefs':BRIEFS,'validation':validation,'legacy_prefix':legacy,'silhouette_comparison':comparison,
      'terrain_visibility_minimum_opaque':terrain['minimum_opaque_fraction'],'terrain_visibility_minimum_boundary':terrain['minimum_boundary_fraction']}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'CREDITS.txt').write_text(manifest['rights']+'\n696 original indexed images. All16px fields leave a transparent one-pixel rim. Portraits separately composed at32px.\nShared existing RGB555 palette unchanged. Art reviews are not emulator evidence.\n')
    validate_legacy_prefix(world_successor);return manifest

def verify(manifest,world_successor=None):
    before=output_hashes();generate(world_successor);assert before==output_hashes(),'Nondeterministic regeneration'
    report={'deterministic_regeneration':True,'pixel_validation':manifest['validation'],'legacy_prefix':validate_legacy_prefix(world_successor),'output_sha256':output_hashes()}
    with tempfile.TemporaryDirectory(prefix='underwater-art-') as td:
        td=Path(td);sys.path.insert(0,str(ROOT/'tools'));from arm_toolchain import resolve_arm_tools
        tools=resolve_arm_tools('gcc','size',root=ROOT);obj=td/'underwater_creature_art.o'
        subprocess.run([tools['gcc'],'-std=c99','-mcpu=arm7tdmi','-mthumb','-O2','-ffreestanding','-fno-builtin','-fstack-usage','-Wall','-Wextra','-Werror','-c',str(ROOT/'src/underwater_creature_art.c'),'-o',str(obj)],check=True,capture_output=True)
        size=subprocess.check_output([tools['size'],str(obj)],text=True);sections=list(map(int,size.splitlines()[-1].split()[:3]));assert sections[1:]==[0,0] and sections[0]<=manifest['rom_budget_bytes']
        stack=[int(line.split('\t')[1]) for p in td.glob('*.su') for line in p.read_text().splitlines()];assert stack and max(stack)<=24
        report.update({'arm_compile':'passed','arm_rom_object_bytes':sections[0],'arm_data_bytes':sections[1],'arm_bss_bytes':sections[2],'max_arm_stack_bytes':max(stack),'max_include_bytes':manifest['max_include_bytes']})
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');return {k:v for k,v in report.items() if k not in ('output_sha256','pixel_validation')}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');parser.add_argument('--world-successor',choices=['connected-roads-c4']);args=parser.parse_args()
    manifest=generate(args.world_successor);print(json.dumps(verify(manifest,args.world_successor) if args.verify else {'generated_forms':FORM_IDS,'data_bytes':manifest['data_bytes'],'max_include_bytes':manifest['max_include_bytes']},indent=2))
if __name__=='__main__':main()
