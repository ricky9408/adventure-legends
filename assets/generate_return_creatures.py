#!/usr/bin/env python3
"""Return I: original, articulated native pixel geometry, using existing RGB555.
No image extraction, tracing, raster generation or external creature artwork.
Legacy pixels are read only for explicit side-by-side lineage review. Only writes
Return companion art, its review material and src/return_creature_art arrays.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, subprocess, sys, tempfile
from PIL import Image, ImageDraw
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'assets/return_creatures'
sys.path.insert(0,str(ROOT/'assets'))
from magma_palette import Art as BaseArt, P, PAL, rgb as RGB, COLORS
BRIEFS=json.loads((OUT/'briefs.json').read_text())
FORM_IDS=(3,6,9,12,15,17,18,21,24,27,30,101,102,103,104)
NAMES=tuple(f['name'] for f in BRIEFS);KEYS=tuple(n.lower().replace(' ','_') for n in NAMES)
DIRECTIONS=('down','up','left','right')
WALK_TICKS=((9,7,9,8),(12,10,12,9),(7,7,7,9),(12,9,12,10),(7,9,8,10),(6,9,6,12),(11,9,13,10),(10,8,11,8),(12,10,12,10),(6,7,6,9),(10,8,9,11),(6,5,7,6),(7,5,8,6),(8,10,8,12),(11,8,12,9))
class Art(BaseArt):
    """Pixel surfaces fail loudly on off-canvas geometry; no implicit clipping."""
    def check(self,pts):
        assert all(0<=x<self.im.width and 0<=y<self.im.height for x,y in pts), (self.im.size,pts)
    def p(self,pts,c):self.check(pts);super().p(pts,c)
    def l(self,pts,c,w=1):self.check(pts);super().l(pts,c,w)
    def e(self,b,c):self.check(((b[0],b[1]),(b[2],b[3])));super().e(b,c)
    def r(self,b,c):self.check(((b[0],b[1]),(b[2],b[3])));super().r(b,c)
    def dot(self,x,y,c):self.check(((x,y),));super().dot(x,y,c)
class Pen:
    """A bounded one-pixel native joint offset; width is part of the contract."""
    def __init__(self,a,dy=0,lean=0):self.a,self.dy,self.lean=a,dy,lean
    def pt(self,x,y):return max(1,min(14,x+self.lean if y<9 else x)),max(1,min(14,y+self.dy))
    def p(self,pts,c):self.a.p([self.pt(x,y) for x,y in pts],c)
    def l(self,pts,c,w=1):
        pad=2 if w>1 else 1
        self.a.l([(max(pad,min(15-pad,x)),max(pad,min(15-pad,y))) for x,y in [self.pt(x,y) for x,y in pts]],c,w)
    def e(self,b,c):
        x,y=self.pt(b[0],b[1]);xx,yy=self.pt(b[2],b[3]);self.a.e((min(x,xx),min(y,yy),max(x,xx),max(y,yy)),c)
    def r(self,b,c):
        x,y=self.pt(b[0],b[1]);xx,yy=self.pt(b[2],b[3]);self.a.r((min(x,xx),min(y,yy),max(x,xx),max(y,yy)),c)
    def dot(self,x,y,c):self.a.dot(*self.pt(x,y),c)
def gait(f,cast):
    # The first two values articulate opposing joints; the third is the torso.
    return ((-1,0,1,0)[f],(0,1,0,-1)[f],(0,-1,0,0)[f]) if cast is None else ((-1,2,1)[cast],(1,-1,1)[cast],(1,-1,0)[cast])
def finish(a,d):return a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if d=='right' else a.im

def eye(q,x,y):
    q.r((x,y,x+1,y+1),'white');q.dot(x,y+1,'ink')
def face(q,d,x,y,w,c,cast=None):
    q.p([(x,y+1),(x+1,y),(x+w-1,y),(x+w,y+2),(x+w-1,y+4),(x+1,y+4),(x,y+3)],'ink')
    q.p([(x+1,y+1),(x+w-1,y+1),(x+w-1,y+3),(x+2,y+3)],c)
    if d=='up':q.l([(x+2,y+1),(x+w-2,y+2)],'white')
    elif d in ('left','right'):
        eye(q,x+1,y+1);q.dot(x,y+3,'ink');q.dot(x+3,y+3,'rose4')
    else:
        eye(q,x+1,y+1);eye(q,x+w-2,y+1);q.dot(x+w//2,y+3,'ink')
    if cast==0 and d!='up':q.dot(x+1,y+1,'ink')
def leg(q,x,y,s,c='wood4',length=3):
    q.l([(x,y),(x+s,y+length-1),(x+s-1,y+length)],'ink',2)
    q.l([(x,y),(x+s,y+length-1)],c);q.dot(x+s-1,y+length,c)

def fox(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h-1 if d=='up' else h,1 if d=='up' else 0);feet=Pen(a);side=d in ('left','right')
    # Exactly one continuous sweeping wick tail, connected at the hindquarters.
    q.p([(10,9),(12,8),(12+t,4),(14,3),(14,9),(12,11),(10,11)],'ink')
    q.l([(11,10),(13,8),(13,5+t)],'fire2',2);q.dot(13,4+t,'white')
    for x,z in ((4,s),(7,-t),(10,-s)):leg(feet,x,10,z,'fire2',3)
    q.p([(3,8),(6,6),(10,6),(12,8),(11,11),(4,11)],'ink');q.p([(4,8),(7,7),(10,7),(11,9),(10,10),(4,10)],'fire1')
    # Open ivory horseshoe mantle: shoulder pixels and dark throat stay visible.
    q.l([(5,8),(5,5),(7,3),(10,3),(12,5),(12,8)],'ink',3)
    q.l([(5,7),(6,5),(7,4),(10,4),(11,5),(11,7)],'white')
    q.dot(7,3,'silver');q.dot(10,3,'silver');q.dot(7,6,'gold3')
    if side:
        q.p([(1,7),(2,3),(4,5),(5,4),(6,7),(5,10),(3,12),(1,10)],'ink')
        q.p([(2,7),(2,5),(4,7),(5,6),(5,9),(3,11),(2,9)],'fire2')
        q.l([(2,10),(3,10),(4,9)],'white');eye(q,2,7);q.dot(1,9,'ink')
    elif d=='up':
        q.p([(4,7),(4,3),(6,5),(9,5),(11,3),(11,7),(8,9)],'ink')
        q.p([(5,6),(5,5),(7,6),(9,6),(10,5),(10,7),(7,8)],'fire2')
        q.l([(5,10),(7,11),(10,10)],'wood4')
    else:
        q.p([(4,9),(4,5),(6,7),(9,7),(11,5),(11,10),(8,12),(6,12)],'ink')
        q.p([(5,9),(5,7),(6,8),(9,8),(10,7),(10,10),(8,11),(6,11)],'fire2')
        eye(q,5,8);eye(q,9,8);q.l([(6,10),(8,11),(9,10)],'white');q.dot(7,10,'ink')
    return finish(a,d)

def orchard(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h-1 if d=='up' else h,1 if d=='up' else 0);p=Pen(a);side=d in ('left','right')
    # Split root arch remains open underneath the expressive blue seed.
    p.l([(7,9),(5,11),(4+s,13),(2+s,14)],'ink',2);p.l([(8,9),(10,11),(11-s,13),(13-s,14)],'ink',2)
    p.l([(6,10),(5,12),(3+s,13)],'teal2');p.l([(9,10),(10,12),(12-s,13)],'water4')
    p.l([(6,10),(6+t,13)],'wood4');p.l([(9,10),(9-t,13)],'wood4')
    q.l([(7,8),(6,5),(3,4),(2,3+t)],'ink',3);q.l([(8,8),(9,5),(12,5),(13,4-t)],'ink',3)
    q.p([(6,5),(3,1+t),(1,2+t),(1,5),(5,7)],'ink');q.p([(5,5),(3,2+t),(2,3+t),(3,5),(5,6)],'teal1');q.l([(2,3+t),(4,4),(5,5)],'water4')
    q.p([(8,5),(10,2),(12,1),(13,3),(11,5),(9,6)],'ink');q.p([(9,4),(11,2),(12,2),(12,3),(10,5)],'teal2');q.dot(11,3,'white')
    q.p([(9,6),(12,5-t),(14,6),(13,8),(10,8)],'ink');q.p([(10,6),(12,6-t),(13,6),(12,7),(10,7)],'teal1');q.dot(12,6,'water4')
    face(q,d,4 if side else 5,6,5,'blue3',cast)
    if d=='up':q.l([(6,8),(8,9),(9,7)],'teal0')
    return finish(a,d)

def moth(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h-1 if d=='up' else h,1 if d=='up' else 0);side=d in ('left','right')
    # One unbroken trailing loop, below the two steering sails.
    q.l([(7,9),(4+s,11),(5+s,13),(8,14),(11,12),(10,10),(8,9)],'ink')
    q.l([(6,10),(5+s,11),(6+s,13),(8,13),(10,12),(9,10)],'wood4')
    for x,sg in ((6,-1),(9,1)):
        fold=2 if side and sg==1 else 0
        q.p([(x,7),(x+sg*(4-fold),2+t*sg),(x+sg*(5-fold),3+t*sg),(x+sg*(4-fold),6),(x+sg*2,8)],'ink')
        q.p([(x,6),(x+sg*(3-fold),3+t*sg),(x+sg*(4-fold),3+t*sg),(x+sg*(3-fold),6),(x+sg,7)],'white')
        q.l([(x,7),(x+sg*2,5)],'purple3')
        q.p([(x,8),(x+sg*(4-fold),8+s*sg),(x+sg*(3-fold),11),(x,10)],'purple1')
        q.l([(x,9),(x+sg*(3-fold),9+s*sg)],'flower1')
    q.l([(7,4),(6,2),(5,1)],'ink');q.l([(8,4),(9,2),(10,1)],'ink');q.dot(5,1,'white');q.dot(10,1,'white')
    q.p([(7,4),(9,5),(9,9),(7,11),(6,9),(6,5)],'ink');q.l([(7,5),(8,6),(7,9)],'flower1',2)
    if d=='up':q.l([(7,5),(8,8)],'purple3')
    elif side:q.dot(6,6,'ink');q.dot(6,7,'white')
    else:q.dot(6,6,'ink');q.dot(8,6,'ink');q.dot(7,8,'gold2')
    return finish(a,d)

def waystone(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h-1 if d=='up' else h,1 if d=='up' else 0);p=Pen(a);side=d in ('left','right')
    for x,z in ((3,s),(6,-t),(10,-s),(12,t)):leg(p,x,10,z,'gold2',3)
    # Two offset shoulder arches enclose distinct tall windows.
    q.l([(3,10),(3,5),(5,2),(8,2),(9,5),(9,10)],'ink',3)
    q.l([(3,9),(4,5),(5,3),(7,3),(8,5),(8,9)],'gold2')
    q.l([(7,10),(7,6),(10,3),(12,4),(13,7),(13,10)],'ink',2)
    q.l([(8,9),(8,6),(10,4),(11,4),(12,7),(12,9)],'gold3')
    q.dot(5,2,'white');q.dot(9,3,'wood5');q.dot(4,4,'pine4');q.dot(7,2,'pine5')
    if d=='up':q.l([(4,10),(7,11),(11,10)],'gold0');q.dot(8,10,'gold3')
    else:
        x=1 if side else 4
        q.p([(x,9),(x+2,7),(x+5,8),(x+6,10),(x+3,12)],'ink');q.p([(x+1,9),(x+2,8),(x+4,9),(x+4,10),(x+3,11)],'wood4')
        eye(q,x+1,8)
        if not side:eye(q,x+4,8)
        q.dot(x+3,11,'gold4')
    return finish(a,d)

def river(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h-1 if d=='up' else h,1 if d=='up' else 0);p=Pen(a);side=d in ('left','right')
    for x,z in ((5,s),(10,-s)):
        p.l([(x,9),(x+z,12),(x+z-2,13),(x+z+1,14)],'ink');p.l([(x,10),(x+z,12),(x+z-1,13)],'water3');p.dot(x+z+1,14,'water4')
    # Sideways linked loops; central droplet is the living connecting node.
    q.l([(7,6),(4,3+t),(2,4+t),(1,7),(3,9),(6,8),(8,6),(11,4-t),(13,5-t),(14,8),(12,10),(9,9),(7,6)],'ink',3)
    q.l([(6,6),(4,4+t),(2,5+t),(2,7),(4,8),(6,7)],'water3')
    q.l([(8,6),(11,5-t),(12,5-t),(13,8),(11,9),(9,8)],'water4')
    q.dot(2,5+t,'white');q.dot(12,6-t,'white')
    x=3 if side else 5;face(q,d,x,6,5,'blue3',cast)
    q.p([(x+2,6),(x+3,3),(x+4,4),(x+3,7)],'water4')
    if d=='up':q.l([(x+1,8),(x+3,9),(x+4,7)],'blue1')
    return finish(a,d)

def bell(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h-1 if d=='up' else h,1 if d=='up' else 0);p=Pen(a);side=d in ('left','right')
    if v==0:
        # Rear prongs and continuous spring torso, then the responsive clappers.
        for x,sg in ((5,-1),(10,1)):
            p.l([(x,9),(x+sg,11),(x+sg*(2+s),13),(x+sg*(2+s),10)],'ink');p.l([(x,10),(x+sg,12),(x+sg*(2+s),12)],'gold2')
        q.p([(5,5),(9,4),(11,7),(10,10),(7,12),(5,10)],'ink');q.l([(6,6),(9,6),(7,8),(9,9),(7,10)],'gold2',2)
        q.l([(5,6),(3,7+t),(3,9+t),(5,9)],'ink',2);q.dot(3,8+t,'gold3')
        q.l([(10,6),(12,7-t),(12,9-t),(10,9)],'ink',2);q.dot(12,8-t,'wood4')
        q.l([(7,5),(6,2),(9,2),(10,3)],'ink');q.l([(7,3),(8,2),(9,3)],'silver')
        face(q,d,3 if side else 5,4,5,'gold3',cast)
    else:
        for x,z in ((4,s),(8,t),(11,-s)):
            p.l([(8,9),(x,11),(x+z,13),(x+z-1,14)],'ink',2);p.l([(8,10),(x,12),(x+z,13)],'gold2')
        q.p([(6,4),(9,4),(10,11),(7,12),(5,10)],'ink');q.l([(7,5),(8,9),(7,10)],'wood4',2)
        # Deliberately broad OPEN bell collar, not a solid bell with a face decal.
        q.l([(5,8),(2,6+t),(3,3+t),(6,2),(9,2),(12,3-t),(13,6-t),(10,8)],'ink',2)
        q.l([(4,7),(3,5+t),(4,3+t),(6,3),(9,3),(11,4-t),(12,6-t),(10,7)],'gold3')
        q.dot(5,2,'white');q.dot(10,3,'white')
        face(q,d,3 if side else 5,5,5,'wood5',cast)
        if d=='up':q.l([(6,7),(7,8),(9,6)],'gold0')
    return finish(a,d)

def arbour(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h-1 if d=='up' else h,1 if d=='up' else 0);p=Pen(a);side=d in ('left','right')
    # A single vine tail returns through its open living shoulder arch.
    q.l([(10,9),(13,10),(14,7+t),(13,4),(11,4),(10,6),(12,7)],'ink')
    q.l([(11,9),(13,9),(13,7+t),(12,5),(11,6)],'pine4')
    for x,z in ((4,s),(6,-t),(10,-s),(12,t)):leg(p,x,9,z,'wood4',4)
    q.l([(4,8),(7,7),(11,8)],'ink',3);q.l([(5,8),(8,8),(10,9)],'pine3',2)
    q.l([(5,8),(5,5),(7,2),(10,3),(11,6),(11,8)],'ink',2)
    q.l([(6,6),(6,4),(7,3),(9,4),(10,6)],'wood4')
    q.p([(6,3),(3,1+t),(3,3),(5,4)],'pine5');q.p([(9,3),(12,1-t),(12,3),(10,4)],'pine4')
    face(q,d,1 if side else 3,7,5,'leafwarm',cast)
    q.p([(3,7),(2,5+t),(4,6)],'pine4');q.p([(6,7),(7,5-t),(8,6)],'mint')
    return finish(a,d)

def hearth(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h-1 if d=='up' else h,1 if d=='up' else 0);p=Pen(a);side=d in ('left','right')
    for x,z in ((4,s),(6,-t),(10,-s),(12,t)):leg(p,x,10,z,'fire3',3)
    q.p([(4,8),(7,6),(11,7),(14,10),(13,12),(8,11),(4,11)],'ink');q.l([(8,9),(11,9),(13,11)],'fire1',2)
    # Joined tall kiln at the shoulder, opening on inhale; separate soft muzzle.
    q.p([(5,8),(5,4),(7,2),(10,2),(12,5),(11,10),(8,11)],'ink');q.p([(6,8),(6,4),(8,3),(10,3),(11,5),(10,9),(8,10)],'fire0')
    q.l([(6,4),(8,3),(10,4)],'fire3');q.l([(6,6+t),(10,6-t)],'ink');q.dot(8,6,'gold3')
    q.l([(9,9),(11,10),(13,10+s)],'wood4')
    face(q,d,1 if side else 3,7,7,'skin2',cast)
    if d=='up':q.l([(4,9),(7,10),(9,8)],'fire1')
    else:q.l([(4 if side else 6,10),(6 if side else 8,10)],'wood1')
    return finish(a,d)

def gecko(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h-1 if d=='up' else h,1 if d=='up' else 0);p=Pen(a);side=d in ('left','right')
    q.l([(10,8),(12,9),(13,12+t),(11+s,13)],'ink',2);q.l([(10,8),(12,10),(12,12+t),(11+s,12)],'pine5')
    for x,sg in ((5,-1),(10,1)):
        p.l([(x,8),(x+sg*(2+s),10),(x+sg*2,12)],'ink',2);p.dot(x+sg*2-1,13,'mint');p.dot(x+sg*2+1,13,'mint')
        p.p([(x,8),(x+sg*(2+s),10),(x+sg,12),(x,10)],'ink');p.p([(x,9),(x+sg*(1+s),10),(x+sg,11)],'teal2')
    q.p([(5,7),(7,5),(10,6),(11,9),(8,11),(5,10)],'ink');q.p([(6,7),(8,6),(10,7),(9,10),(6,9)],'pine4')
    # Single high back fin, open lower leg membranes, tapering tail.
    q.p([(7,7),(7,2),(9,1),(10,5),(11,8)],'ink');q.l([(8,5),(8,3),(9,4),(10,6)],'leaflight')
    face(q,d,1 if side else 4,5,6,'pine5',cast)
    if d=='up':q.l([(5,7),(7,8),(9,6)],'pine2')
    return finish(a,d)

def dune(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h-1 if d=='up' else h,1 if d=='up' else 0);p=Pen(a);side=d in ('left','right')
    q.l([(11,9),(13,8),(13,4+t),(11,3+t)],'ink',2);q.l([(11,9),(12,7),(12,4+t)],'wood4');q.dot(11,3+t,'gold3')
    for x,z in ((5,t),(10,-t)):leg(p,x,10,z,'wood3',3)
    q.p([(3,8),(5,6),(10,6),(12,8),(11,11),(4,11)],'ink');q.p([(4,8),(6,7),(9,7),(11,9),(10,10),(5,10)],'wood3')
    for x,sg in ((4,-1),(10,1)):
        p.p([(x,9),(x+sg*(2+s),10),(x+sg*(2+s),12),(x+sg,13),(x,11)],'ink')
        p.l([(x,10),(x+sg*(1+s),11),(x+sg,12)],'wood5');p.dot(x+sg*(2+s),12,'gold3')
    q.p([(4,7),(3,2),(5,3),(6,6)],'ink');q.l([(4,3),(5,5)],'skin1')
    q.p([(8,6),(9,2+t),(11,3),(10,7)],'ink');q.l([(10,3),(9,5)],'skin2')
    face(q,d,1 if side else 4,6,6,'wood5',cast)
    if d=='up':q.l([(5,8),(8,9),(9,7)],'gold0')
    return finish(a,d)

def shrew(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h-1 if d=='up' else h,1 if d=='up' else 0);p=Pen(a);side=d in ('left','right')
    # One attached copper curl: shrew nose and tiny four-foot gait stay organic.
    q.l([(11,10),(13,10),(14,8+t),(13,6),(12,7),(13,8)],'ink');q.l([(11,10),(13,9),(13,7)],'wood3')
    for x,z in ((5,s),(7,-t),(10,-s)):leg(p,x,10,z,'skin1',3)
    if v==0:
        q.p([(4,8),(7,5),(10,6),(12,9),(10,11),(5,11)],'ink');q.p([(5,8),(7,6),(10,7),(11,9),(10,10),(5,10)],'silver')
        q.l([(7,6),(8,8),(7,10)],'slate');q.l([(9,7),(10,8),(9,10)],'wood3')
        q.p([(5,7),(5,2+t),(7,1+t),(8,4),(7,7)],'ink');q.l([(6,6),(6,3+t),(7,3)],'skin1');q.dot(6,2+t,'white')
        q.p([(4,8),(3,6),(2,9),(1,10),(5,11),(7,9)],'ink');q.p([(4,8),(3,7),(3,9),(2,10),(5,10),(6,9)],'skin2')
        if d!='up':eye(q,3,8);q.dot(1,10,'rose0')
        else:q.l([(3,8),(5,9),(6,8)],'wood3')
        q.l([(3,10),(1,12)],'silver');q.l([(4,10),(2,13)],'wood4')
    else:
        q.p([(3,9),(5,7),(8,6),(11,7),(13,10),(11,12),(5,11)],'ink');q.p([(5,8),(8,7),(11,8),(12,10),(10,11),(5,10)],'silver')
        for x in (7,9,11):q.l([(x,7),(x+1,9),(x,10)],'slate');q.dot(x,7,'white')
        # Open crescent ears extend above a connected curved neck, unequal fold.
        q.l([(5,8),(3,5+t),(4,2),(6,1),(7,3),(6,5)],'ink',2);q.l([(5,7),(4,5+t),(5,2),(6,3)],'wood4')
        q.l([(7,7),(8,4),(11,2-t),(12,4),(11,6),(9,7)],'ink',2);q.l([(8,6),(9,4),(11,3-t),(11,5)],'skin2')
        if side:
            q.l([(6,8),(4,8),(3,10),(1,11),(4,12),(6,10)],'ink',2);q.l([(5,8),(4,9),(3,10),(2,11),(4,11)],'skin2')
            eye(q,3,9);q.dot(1,11,'rose0')
            q.l([(4,11),(2,13),(1,13)],'silver');q.l([(5,11),(4,14)],'wood4')
        else:
            q.p([(4,9),(6,7),(9,8),(11,10),(8,12),(6,12)],'ink');q.p([(5,9),(6,8),(9,9),(9,10),(7,11)],'skin2')
            if d=='down':eye(q,5,9);eye(q,8,9);q.dot(7,11,'rose0')
            q.l([(5,11),(3,12),(2,11)],'silver');q.l([(9,11),(11,13),(12,12)],'wood4')
    if d=='down':q.dot(6,9,'ink');q.dot(5,10,'white')
    elif d=='up':q.l([(5,8),(7,9),(9,8)],'slate')
    # Directional perspective: front retains shorter muzzle and exposed other eye.
    if d in ('down','up'):
        q.dot(9,11,'skin1');q.dot(2,8,'transparent')
    return finish(a,d)

def skipper(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h-1 if d=='up' else h,1 if d=='up' else 0);p=Pen(a);side=d in ('left','right')
    if v==0:
        q.p([(9,8),(12,5+t),(14,6+t),(13,8),(14,10),(11,11),(9,10)],'ink');q.l([(10,9),(12,7+t),(13,7+t)],'water4');q.l([(11,9),(13,10)],'blue3')
        # Two bowed pectoral fins physically step; no conventional hind legs.
        p.l([(6,8),(3,10+s),(2,13),(4,14)],'ink',2);p.l([(6,9),(4,11+s),(3,13)],'water4')
        p.l([(9,8),(11,11-s),(10,14)],'ink',2);p.l([(9,9),(10,11-s),(10,13)],'water3')
        q.p([(3,7),(5,5),(8,5),(10,7),(11,9),(8,11),(4,10)],'ink');q.p([(4,7),(6,6),(8,6),(9,8),(8,10),(4,9)],'water3')
        face(q,d,2 if side else 3,5,6,'water4',cast)
        q.dot(4,4,'ink');q.dot(4,5,'white');q.dot(7,4,'ink');q.dot(7,5,'white')
    else:
        # Continuous alternating crest reads as braided tail, not two tails.
        q.l([(8,9),(11,9),(13,7+t),(12,4),(14,3)],'ink',2);q.l([(9,9),(11,8),(12,7+t),(12,5),(13,4)],'water3')
        q.dot(11,8,'white');q.dot(13,6+t,'blue3');q.dot(12,4,'white')
        for x,sg in ((6,-1),(9,1)):
            p.l([(x,8),(x+sg*2,9+s*sg),(x+sg*3,12),(x+sg*2,14)],'ink',2)
            p.l([(x,9),(x+sg*2,10+s*sg),(x+sg*2,12)],'water4')
            p.l([(x+sg,11),(x+sg*2,12),(x+sg,13)],'blue3')
        q.p([(3,6),(6,4),(9,6),(11,9),(8,11),(4,10)],'ink');q.p([(4,6),(6,5),(8,6),(9,8),(8,10),(5,9)],'water3')
        face(q,d,1 if side else 3,5,6,'water4',cast)
        q.dot(3,4,'ink');q.dot(3,5,'white');q.dot(6,4,'ink');q.dot(6,5,'white')
    if d=='up':q.l([(5,7),(7,8),(8,6)],'water1')
    elif d=='down':q.l([(5,8),(6,9),(7,8)],'water0')
    return finish(a,d)

DRAW={3:fox,6:orchard,9:moth,12:waystone,15:river,17:lambda d,f,c:bell(0,d,f,c),18:lambda d,f,c:bell(1,d,f,c),21:arbour,24:hearth,27:gecko,30:dune,101:lambda d,f,c:shrew(0,d,f,c),102:lambda d,f,c:shrew(1,d,f,c),103:lambda d,f,c:skipper(0,d,f,c),104:lambda d,f,c:skipper(1,d,f,c)}
def field(form_id,d,f,cast=None):
    if type(form_id)!=int or form_id not in FORM_IDS or d not in DIRECTIONS or type(f)!=int or not 0<=f<4 or (cast is not None and (type(cast)!=int or not 0<=cast<3)):raise ValueError('Invalid Return art identity/direction/frame/pose')
    return DRAW[form_id](d,f,cast)

# Portraits are separately composed at 32px, with cheek planes, pupils, joints,
# ribs and negative spaces that do not exist in the 16px field frames.
def big_eye(a,x,y):
    a.e((x,y,x+3,y+5),'ink');a.e((x,y,x+2,y+4),'white');a.r((x,y+2,x+1,y+4),'ink');a.dot(x+1,y+1,'white')
def big_face(a,x,y,w,c):
    a.p([(x,y+2),(x+3,y),(x+w-3,y),(x+w,y+3),(x+w-2,y+8),(x+3,y+9),(x,y+6)],'ink')
    a.p([(x+1,y+3),(x+3,y+1),(x+w-3,y+1),(x+w-1,y+3),(x+w-3,y+7),(x+3,y+8),(x+1,y+5)],c)
    big_eye(a,x+2,y+2);big_eye(a,x+w-5,y+2)
    a.l([(x+5,y+7),(x+6,y+8),(x+8,y+7)],'ink');a.dot(x+2,y+7,'rose4')
def portrait(form_id):
    if type(form_id)!=int or form_id not in FORM_IDS:raise ValueError('Invalid Return portrait form')
    a=Art(32,32,'transparent')
    if form_id==3:
        a.p([(22,21),(27,19),(27,10),(30,7),(30,22),(26,26),(21,25)],'ink');a.l([(23,23),(28,21),(28,12)],'fire2',3);a.l([(28,12),(29,9)],'white')
        for x in (8,15,23):a.l([(x,22),(x,28),(x-2,29)],'ink',3);a.l([(x,23),(x,27)],'fire2')
        a.p([(7,15),(12,10),(22,11),(26,18),(23,25),(10,25)],'ink');a.p([(10,15),(14,12),(21,13),(24,18),(21,23),(10,23)],'fire1')
        a.l([(10,17),(11,9),(16,5),(23,6),(26,11),(25,17)],'ink',5);a.l([(10,16),(12,10),(16,7),(22,8),(24,11),(24,16)],'white',3)
        a.l([(12,11),(15,9),(16,9)],'wood4');a.l([(21,9),(23,12)],'silver');a.dot(17,6,'white')
        a.p([(3,18),(3,8),(8,11),(10,14),(13,10),(15,13),(14,22),(10,26),(5,24),(1,21)],'ink')
        a.p([(4,18),(4,11),(7,13),(9,17),(12,14),(13,15),(12,22),(9,24),(5,22),(3,20)],'fire2')
        a.p([(3,20),(6,21),(9,23),(12,21),(10,24),(7,25),(4,23)],'white');big_eye(a,5,16);a.dot(2,20,'ink');a.l([(5,12),(6,14)],'rose3')
    elif form_id==6:
        a.l([(15,19),(10,24),(8,29),(4,30)],'ink',3);a.l([(18,19),(22,24),(24,28),(29,29)],'ink',3)
        a.l([(15,20),(11,25),(7,29)],'teal2');a.l([(18,20),(21,24),(26,28)],'water4',2)
        a.l([(15,16),(13,10),(8,8),(4,8)],'ink',3);a.l([(17,16),(20,9),(25,7)],'ink',3)
        a.p([(13,11),(7,3),(2,4),(1,8),(6,11),(12,12)],'ink');a.p([(11,10),(7,5),(3,5),(3,8),(7,10)],'teal1');a.l([(3,6),(7,7),(10,10)],'water4')
        a.p([(18,11),(21,3),(27,1),(29,4),(27,8),(22,12)],'ink');a.p([(20,10),(23,4),(27,3),(27,6),(24,9)],'teal2');a.l([(22,8),(25,5),(27,4)],'white')
        a.p([(20,13),(25,10),(30,11),(29,15),(26,17),(21,16)],'ink');a.p([(22,13),(26,12),(28,12),(27,15),(23,15)],'teal1')
        big_face(a,10,14,13,'blue3');a.l([(13,16),(16,15),(18,16)],'watergleam');a.dot(19,22,'water4')
        a.l([(14,23),(13,28),(11,28)],'wood4');a.l([(19,23),(21,28),(23,28)],'wood3')
    elif form_id==9:
        a.l([(15,20),(9,24),(11,28),(16,30),(22,27),(22,23),(18,20)],'ink',2);a.l([(14,21),(11,24),(12,27),(16,28),(20,26),(20,23)],'wood4')
        for sg,x in ((-1,14),(1,18)):
            a.p([(x,15),(x+sg*9,2),(x+sg*12,3),(x+sg*10,9),(x+sg*5,16)],'ink')
            a.p([(x,13),(x+sg*8,4),(x+sg*10,4),(x+sg*8,9),(x+sg*4,14)],'flower1');a.l([(x+sg*3,12),(x+sg*7,7)],'white',2)
            a.p([(x,17),(x+sg*10,17),(x+sg*11,22),(x+sg*5,23),(x,20)],'ink');a.p([(x+sg,18),(x+sg*9,18),(x+sg*8,21),(x+sg*4,21)],'purple3');a.l([(x+sg*3,19),(x+sg*7,19)],'white')
        a.p([(15,7),(19,10),(19,20),(16,24),(13,19),(13,11)],'ink');a.p([(15,9),(17,10),(18,18),(16,22),(14,18)],'flower1')
        a.l([(15,9),(12,5),(12,2)],'ink');a.l([(17,9),(20,5),(23,4)],'ink');a.dot(12,2,'white');a.dot(23,4,'white')
        big_eye(a,13,11);big_eye(a,17,11);a.dot(16,18,'gold2');a.l([(15,20),(16,21),(17,20)],'purple1')
    elif form_id==12:
        for x in (5,12,22,27):a.l([(x,22),(x,28),(x-2,29)],'ink',3);a.l([(x,23),(x,27)],'gold2')
        a.l([(5,23),(5,10),(9,3),(16,3),(19,9),(18,22)],'ink',5);a.l([(5,22),(6,10),(10,5),(15,5),(17,10),(17,20)],'gold2',3)
        a.l([(17,23),(17,13),(22,7),(26,8),(28,14),(28,23)],'ink',4);a.l([(18,21),(18,13),(22,9),(25,10),(27,15),(27,22)],'wood4',2)
        a.l([(7,9),(10,5),(14,5)],'gold4');a.l([(21,10),(23,9),(25,11)],'white');a.l([(8,4),(8,2),(11,3)],'pine4',2)
        a.p([(4,20),(8,15),(15,16),(19,21),(14,25),(9,27)],'ink');a.p([(6,20),(9,17),(14,18),(16,21),(13,24),(10,25)],'wood4');big_eye(a,7,18);big_eye(a,13,18);a.dot(11,24,'gold4')
    elif form_id==15:
        a.l([(13,21),(9,25),(7,28),(3,29),(9,30)],'ink',2);a.l([(19,21),(23,25),(22,28),(27,30)],'ink',2);a.l([(12,22),(9,26),(6,28)],'water4');a.l([(20,22),(23,25),(24,28)],'water3')
        a.l([(15,12),(9,5),(4,6),(1,12),(4,18),(10,19),(16,13),(23,8),(28,10),(30,17),(26,21),(21,21),(15,12)],'ink',3)
        a.l([(14,12),(9,7),(5,8),(3,12),(5,16),(9,17),(14,13)],'water3',2);a.l([(17,13),(23,10),(27,11),(28,16),(25,19),(21,19),(18,16)],'water4',2)
        a.l([(4,10),(5,8),(8,8)],'white');a.l([(24,11),(27,13)],'white')
        big_face(a,10,13,13,'blue3');a.p([(14,14),(16,6),(19,5),(18,9),(19,13)],'ink');a.l([(15,13),(17,8),(18,7)],'water4',2)
    elif form_id in (17,18):
        evolved=form_id==18
        if not evolved:
            for x,sg in ((11,-1),(22,1)):
                a.l([(x,22),(x+sg*3,28),(x+sg*6,29),(x+sg*6,21)],'ink',2);a.l([(x,23),(x+sg*3,27),(x+sg*5,27)],'gold2')
            a.p([(11,11),(21,11),(24,18),(21,24),(15,27),(10,23)],'ink');a.l([(13,13),(20,14),(15,18),(21,20),(15,24)],'wood4',3)
            a.l([(11,12),(5,13),(4,19),(8,22),(12,20)],'ink',3);a.l([(21,12),(27,14),(27,19),(23,22)],'ink',3)
            a.l([(6,14),(6,18),(9,20)],'gold2',2);a.l([(26,15),(25,19),(24,20)],'gold3',2)
            a.l([(15,10),(13,4),(15,2),(20,3),(21,6)],'ink',2);a.l([(15,5),(16,3),(19,4)],'silver')
            big_face(a,10,8,14,'gold3')
        else:
            for x in (6,16,25):a.l([(16,19),(x,25),(x-1,30)],'ink',3);a.l([(16,21),(x,26),(x,28)],'gold2')
            a.p([(12,8),(19,8),(21,23),(17,26),(12,23),(10,15)],'ink');a.l([(14,10),(17,15),(15,21),(17,23)],'wood4',3)
            a.l([(10,17),(3,13),(4,6),(10,2),(20,2),(27,7),(28,13),(22,17)],'ink',3)
            a.l([(9,15),(5,12),(6,7),(11,4),(20,4),(25,8),(26,12),(22,15)],'gold3',2);a.l([(7,7),(11,4),(17,4)],'white');a.l([(22,6),(25,9)],'wood5')
            big_face(a,10,11,13,'wood5');a.l([(13,12),(17,12)],'white')
    elif form_id==21:
        for x in (6,12,23,27):a.l([(x,20),(x-1,25),(x-2,29)],'ink',2);a.l([(x,21),(x-1,25),(x-1,27)],'wood4')
        a.l([(22,19),(28,22),(30,16),(28,9),(24,9),(22,13),(26,15)],'ink',2);a.l([(23,19),(27,20),(28,16),(27,11),(24,11),(24,13)],'pine4')
        a.l([(8,19),(14,17),(24,20)],'ink',5);a.l([(10,19),(16,18),(22,20)],'pine3',3)
        a.l([(10,19),(10,10),(15,3),(20,5),(24,13),(24,19)],'ink',3);a.l([(11,15),(12,10),(15,5),(19,7),(22,14)],'wood4')
        a.p([(13,7),(8,2),(4,3),(8,7),(12,9)],'pine4');a.l([(6,3),(10,6)],'mint')
        a.p([(20,8),(25,3),(29,4),(27,7),(23,10)],'pine5');a.dot(26,5,'white')
        big_face(a,3,15,13,'leafwarm');a.p([(5,16),(2,10),(7,13)],'pine3');a.p([(12,15),(16,10),(18,12),(15,17)],'pine5')
    elif form_id==24:
        for x in (7,13,23,27):a.l([(x,22),(x,28),(x-2,29)],'ink',3);a.l([(x,24),(x,27)],'fire3')
        a.p([(8,16),(16,14),(24,17),(30,24),(28,27),(20,25),(8,25)],'ink');a.p([(10,18),(18,17),(24,19),(28,24),(24,25),(10,23)],'fire1')
        a.p([(11,19),(10,9),(14,3),(21,2),(26,8),(25,21),(19,24)],'ink');a.p([(12,17),(12,9),(15,5),(21,4),(24,9),(23,20),(19,22)],'fire0')
        a.l([(13,8),(16,5),(21,6),(23,9)],'fire3',2);a.l([(13,12),(18,11),(23,13)],'ink',2);a.l([(16,12),(20,12)],'gold3')
        a.l([(22,21),(25,22),(28,24)],'wood4')
        big_face(a,2,16,17,'skin2');a.l([(7,23),(9,24),(12,23)],'wood1');a.dot(4,22,'rose4')
    elif form_id==27:
        a.l([(21,17),(27,20),(28,26),(24,29),(20,28)],'ink',3);a.l([(22,18),(26,21),(26,26),(23,27)],'pine5',2)
        for x,sg in ((10,-1),(22,1)):
            a.l([(x,16),(x+sg*5,21),(x+sg*4,28)],'ink',2)
            a.p([(x,17),(x+sg*5,21),(x+sg*3,24),(x,21)],'teal2');a.l([(x+sg*4,27),(x+sg*6,29)],'mint');a.l([(x+sg*4,27),(x+sg*2,29)],'mint')
        a.p([(10,13),(16,10),(22,14),(24,21),(19,24),(11,21)],'ink');a.p([(12,14),(16,12),(21,15),(21,21),(17,22),(12,20)],'pine4')
        a.p([(15,14),(15,4),(19,1),(22,8),(23,16)],'ink');a.p([(17,12),(17,5),(19,4),(21,10),(21,14)],'leaflight');a.l([(18,7),(20,12)],'pine3')
        big_face(a,4,10,16,'pine5');a.dot(7,18,'teal1');a.dot(16,18,'teal1')
    elif form_id==30:
        a.l([(23,20),(28,18),(28,8),(24,6),(23,9)],'ink',3);a.l([(23,20),(26,17),(26,9),(24,8)],'wood4');a.dot(24,6,'gold3')
        for x in (11,23):a.l([(x,21),(x+1,27),(x-2,29)],'ink',3);a.l([(x,23),(x,27)],'wood3')
        a.p([(6,16),(12,12),(23,15),(26,21),(23,25),(10,24)],'ink');a.p([(8,17),(14,14),(22,17),(24,21),(22,23),(10,22)],'wood3')
        a.p([(6,19),(1,23),(1,27),(5,28),(10,22)],'ink');a.l([(6,21),(3,24),(3,26),(6,25)],'wood5',2);a.l([(3,25),(5,25)],'wood1')
        a.p([(19,20),(23,22),(25,27),(21,29),(17,26)],'ink');a.l([(19,22),(22,24),(23,27),(20,27)],'wood5',2);a.dot(22,26,'wood1')
        a.p([(7,14),(5,3),(9,2),(12,13)],'ink');a.l([(8,5),(9,10)],'skin1',2);a.p([(16,13),(18,2),(22,4),(20,15)],'ink');a.l([(19,5),(18,10)],'skin2',2)
        big_face(a,5,12,16,'wood5')
    elif form_id in (101,102):
        v=form_id==102
        a.l([(24,23),(29,22),(30,16),(28,13),(26,16),(28,18)],'ink',2);a.l([(25,23),(28,21),(29,16),(28,15)],'wood3')
        for x in (10,16,24):a.l([(x,22),(x-1,27),(x-3,28)],'ink',2);a.dot(x-1,26,'skin2')
        a.p([(6,20),(12,12),(20,12),(26,18),(26,24),(20,26),(9,25)],'ink');a.p([(10,19),(14,14),(20,14),(24,19),(24,23),(18,24),(10,23)],'silver')
        for x in (14,19,23):a.l([(x,14),(x+1,18),(x-1,22)],'slate',2);a.l([(x-1,15),(x,16)],'white')
        if v:
            a.l([(10,17),(5,11),(6,4),(10,1),(13,5),(11,10)],'ink',3);a.l([(10,14),(7,10),(8,5),(10,4),(11,6)],'wood4')
            a.l([(13,15),(17,6),(23,2),(25,7),(22,12),(17,15)],'ink',3);a.l([(16,12),(18,7),(22,5),(23,7),(21,10)],'skin2')
        else:
            a.p([(10,17),(8,5),(12,1),(15,4),(16,10),(13,16)],'ink');a.p([(11,14),(10,6),(12,4),(14,5),(14,10)],'skin1');a.l([(11,5),(12,4),(13,5)],'white')
        a.p([(9,17),(6,15),(4,19),(1,22),(6,25),(12,23),(15,20)],'ink');a.p([(9,18),(6,17),(5,20),(3,22),(7,23),(12,21)],'skin2')
        big_eye(a,7,17);a.dot(2,22,'rose0');a.dot(5,23,'rose4');a.l([(7,23),(2,26),(1,26)],'silver');a.l([(9,23),(6,28),(3,29)],'wood4');a.l([(10,23),(10,28)],'silver')
    elif form_id in (103,104):
        v=form_id==104
        if v:
            a.l([(20,20),(26,19),(29,13),(26,7),(29,3)],'ink',3);a.l([(20,20),(25,18),(27,13),(26,8),(28,5)],'water3',2)
            for x,y in ((24,19),(28,14),(26,9),(28,5)):a.l([(x-1,y-1),(x+1,y)],'white')
        else:
            a.p([(20,17),(26,9),(30,10),(28,16),(31,20),(27,24),(22,23)],'ink');a.p([(22,18),(27,12),(28,12),(26,17),(29,20),(27,22),(23,21)],'water3');a.l([(24,19),(27,15)],'watergleam');a.l([(24,20),(27,21)],'blue3')
        for x,sg in ((12,-1),(20,1)):
            a.l([(x,17),(x+sg*6,22),(x+sg*7,27),(x+sg*4,30)],'ink',2);a.l([(x,19),(x+sg*4,23),(x+sg*5,27),(x+sg*4,28)],'water4')
            if v:a.l([(x+sg*2,22),(x+sg*3,26),(x+sg*1,28)],'blue3')
        a.p([(5,14),(11,9),(19,11),(24,19),(20,25),(10,23),(5,20)],'ink');a.p([(7,15),(12,11),(18,13),(21,19),(18,23),(11,21),(7,19)],'water3')
        big_face(a,3,11,17,'water4');a.e((5,8,9,14),'ink');a.e((6,9,8,12),'white');a.dot(6,11,'ink');a.e((14,8,18,14),'ink');a.e((15,9,17,12),'white');a.dot(15,11,'ink')
        a.l([(8,19),(11,21),(15,19)],'water0');a.dot(7,18,'rose4');a.l([(11,13),(13,13)],'watergleam')
    return a.im

def mask(im):return Image.frombytes('L',im.size,bytes(255 if n else 0 for n in im.tobytes()))
def paste(target,im,xy):target.paste(im.convert(target.mode),xy,mask(im))
def normalized_mask(im):
    m=mask(im);box=m.getbbox();return (box[2]-box[0],box[3]-box[1],m.crop(box).tobytes())
def save_image(im,path):
    if im.mode=='P':im.save(path,transparency=0,optimize=False)
    else:im.save(path,optimize=False)
def validate_pixels(fields,abilities,portraits):
    assert tuple(f['id'] for f in BRIEFS)==FORM_IDS
    assert {f['phase'] for f in BRIEFS}=={'water','earth','wood','metal','fire'}
    assert {f['polarity'] for f in BRIEFS}=={'yin','yang'}
    allimgs=[im for group in (fields,abilities)for row in group for direction in row for im in direction]+portraits
    for im in allimgs:assert im.mode=='P' and im.getpalette()==PAL and 0 in im.tobytes() and max(im.tobytes())<97
    for i,row in enumerate(fields):
        for d in range(4):
            walk=row[d];cast=abilities[i][d];group=walk+cast
            assert len({im.tobytes() for im in group})==7,(NAMES[i],DIRECTIONS[d],'seven unique poses')
            assert len({normalized_mask(im) for im in walk})==4,(NAMES[i],DIRECTIONS[d],'four articulated walk masks')
            assert len({normalized_mask(im) for im in cast})==3,(NAMES[i],DIRECTIONS[d],'three articulated cast masks')
            for im in group:
                assert im.size==(16,16)
                assert all(im.getpixel((x,y))==0 for x in range(16) for y in (0,15)),(NAMES[i],'vertical bounds')
                assert all(im.getpixel((x,y))==0 for x in (0,15) for y in range(16)),(NAMES[i],'horizontal bounds')
                assert 35<=sum(bool(n) for n in im.tobytes())<=205,(NAMES[i],'occupancy')
        assert len({im[0].tobytes() for im in row})==4,(NAMES[i],'four unique views')
        assert len({mask(im[0]).tobytes() for im in row})==4,(NAMES[i],'four unique directional silhouettes')
        assert all(row[3][f].tobytes()==row[2][f].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()for f in range(4))
        assert portraits[i].size==(32,32) and portraits[i].tobytes()!=row[0][0].resize((32,32),Image.Resampling.NEAREST).tobytes()
    assert len({normalized_mask(im)for im in portraits})==15
    return {'images':435,'field_dimensions':[15,4,4,256],'ability_dimensions':[15,4,3,256],'portrait_dimensions':[15,1024],
      'actor_palette_entries':97,'palette_indices':sorted({n for im in allimgs for n in im.tobytes()}),'transparent_zero':True,
      'transparent_outer_field_boundary':True,'unique_direction_masks_per_form':4,'articulated_walk_masks_per_direction':4,
      'articulated_cast_masks_per_direction':3,'independently_composed_native_portraits':True,'design_identity_match':True}
SCENE_SOURCES=(('OLD GRASS','assets/southern_region/frondshore_commons.png',(276,262,300,286)),
 ('OLD CREAM','assets/southern_region/sunlace_anchorage.png',(40,96,64,120)),
 ('OLD TEAL','assets/southern_region/sunlace_anchorage.png',(32,287,56,311)),
 ('RETURN GRASS','assets/return_region/greenwake_common.png',(208,192,232,216)),
 ('RETURN CREAM','assets/return_region/sunlace_shade_terraces.png',(264,112,288,136)),
 ('RETURN TEAL','assets/return_region/overflow_gardens.png',(152,104,176,128)))
LINEAGE=((2,3,'evolutions/hearthkeeper_field.png','evolutions/hearthkeeper_portrait.png'),
 (5,6,'evolutions/canopykeeper_field.png','evolutions/canopykeeper_portrait.png'),
 (8,9,'evolutions/windweaver_field.png','evolutions/windweaver_portrait.png'),
 (11,12,'evolutions/archwarden_field.png','evolutions/archwarden_portrait.png'),
 (14,15,'regional_creatures/tidewheel_walk.png','regional_creatures/tidewheel_portrait.png'),
 (16,17,'regional_creatures/chimeclasp_walk.png','regional_creatures/chimeclasp_portrait.png'),
 (17,18,None,None),(20,21,'northern_creatures/loomcrown_walk.png','northern_creatures/loomcrown_portrait.png'),
 (23,24,'northern_creatures/kilnbarrow_walk.png','northern_creatures/kilnbarrow_portrait.png'),
 (26,27,'southern_creatures/boughvault_walk.png','southern_creatures/boughvault_portrait.png'),
 (29,30,'southern_creatures/dunescoop_walk.png','southern_creatures/dunescoop_portrait.png'),
 (101,102,None,None),(103,104,None,None))
def make_lineage(fields,portraits):
    sheet=Image.new('RGB',(440,24+len(LINEAGE)*70),RGB[P['dirt4']]);dr=ImageDraw.Draw(sheet)
    dr.text((4,4),'LINEAGE / OLD PIXELS READ ONLY / RETURN ART REVIEW',fill=RGB[1]);sources=[]
    for i,(before,after,wpath,ppath)in enumerate(LINEAGE):
        y=24+i*70;j=FORM_IDS.index(after);dr.text((3,y),f'{before} > {after}: '+NAMES[j],fill=RGB[1])
        if wpath:
            with Image.open(ROOT/'assets'/wpath) as im:walk=im.copy()
            with Image.open(ROOT/'assets'/ppath) as im:por=im.copy()
            old=[walk.crop((0,d*16,16,d*16+16))for d in range(4)]
            for p in(wpath,ppath):sources.append({'path':'assets/'+p,'sha256':hashlib.sha256((ROOT/'assets'/p).read_bytes()).hexdigest()})
        else:
            k=FORM_IDS.index(before);old=[fields[k][d][0]for d in range(4)];por=portraits[k]
        paste(sheet,por,(4,y+16));paste(sheet,portraits[j],(50,y+16))
        for d in range(4):paste(sheet,old[d],(100+d*32,y+20));paste(sheet,fields[j][d][0],(252+d*32,y+20))
        dr.text((102,y+42),'predecessor D U L R',fill=RGB[1]);dr.text((254,y+42),'Return D U L R',fill=RGB[1])
    save_image(sheet,OUT/'lineage_native.png');save_image(sheet.resize((880,sheet.height*2),Image.Resampling.NEAREST),OUT/'lineage_2x.png')
    return sources

def make_previews(fields,abilities,portraits):
    patches=[];sources=[]
    for name,rel,box in SCENE_SOURCES:
        path=ROOT/rel
        with Image.open(path)as im:
            assert box[0]>=0 and box[1]>=0 and box[2]<=im.width and box[3]<=im.height
            patches.append(im.convert('RGB').crop(box))
        sources.append({'name':name,'path':rel,'crop':list(box),'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    roster=Image.new('RGB',(600,270),RGB[P['dirt4']]);rd=ImageDraw.Draw(roster)
    allframes=Image.new('RGB',(384,15*92+20),RGB[P['dirt4']]);ad=ImageDraw.Draw(allframes);ad.text((3,3),'ART REVIEW: WALK x4 | ANTICIPATE RELEASE SETTLE',fill=RGB[1])
    for i,(fid,key,name)in enumerate(zip(FORM_IDS,KEYS,NAMES)):
        w=Art(64,64,'transparent').im;c=Art(48,64,'transparent').im
        for d in range(4):
            for f in range(4):w.paste(fields[i][d][f],(f*16,d*16))
            for p in range(3):c.paste(abilities[i][d][p],(p*16,d*16))
        save_image(w,OUT/f'{key}_walk.png');save_image(c,OUT/f'{key}_ability.png');save_image(portraits[i],OUT/f'{key}_portrait.png')
        native=Image.new('RGB',(240,176),RGB[P['deep']]);nd=ImageDraw.Draw(native);nd.text((4,3),f'{fid} {name} / ART',fill=RGB[P['white']]);paste(native,portraits[i],(204,28))
        for bg,y in (('deep',24),('dirt4',105)):
            nd.rectangle((0,y-2,199,y+65),fill=RGB[P[bg]])
            for d in range(4):
                for n,im in enumerate(fields[i][d]+abilities[i][d]):paste(native,im,(2+n*28,y+d*16))
        save_image(native,OUT/f'{key}_native.png');save_image(native.resize((720,528),Image.Resampling.NEAREST),OUT/f'{key}_3x.png')
        terrain=Image.new('RGB',(len(patches)*168,116),RGB[P['deep']]);td=ImageDraw.Draw(terrain)
        for t,(label,_,_)in enumerate(SCENE_SOURCES):
            td.text((t*168+3,2),label+' / '+str(fid),fill=RGB[P['white']])
            for d in range(4):
                for f,im in enumerate(fields[i][d]+abilities[i][d]):
                    tile=patches[t].copy();paste(tile,im,(4,4));terrain.paste(tile,(t*168+f*24,18+d*24))
        save_image(terrain,OUT/f'{key}_terrain_native.png')
        # Pure walk-only GIF is precisely four native 16px views, no enlargement.
        walks=[]
        for f in range(4):
            tile=Image.new('RGB',(64,16),RGB[P['dirt4']])
            for d in range(4):paste(tile,fields[i][d][f],(d*16,0))
            walks.append(tile)
        walks[0].save(OUT/f'{key}_walk_native.gif',save_all=True,append_images=walks[1:],duration=[n*1000//60 for n in WALK_TICKS[i]],loop=0,disposal=2,optimize=False)
        anim=[]
        for f in range(11):
            tile=Image.new('RGB',(180,48),RGB[P['dirt4']]);td=ImageDraw.Draw(tile);td.text((2,1),f'{fid} {name}',fill=RGB[1])
            for d in range(4):paste(tile,(fields[i][d]+abilities[i][d]+fields[i][d])[f],(8+d*42,23))
            anim.append(tile)
        anim[0].save(OUT/f'{key}_motion.gif',save_all=True,append_images=anim[1:],duration=[n*1000//60 for n in WALK_TICKS[i]]+[180,110,180]+[n*1000//60 for n in WALK_TICKS[i]],loop=0,disposal=2,optimize=False)
        x=(i%5)*120;y=(i//5)*90;rd.text((x+2,y+2),f'{fid} '+name.split()[-1],fill=RGB[1]);paste(roster,portraits[i],(x+4,y+18))
        for d in range(4):paste(roster,fields[i][d][0],(x+4+d*25,y+60))
        ay=20+i*92;ad.text((3,ay),f'{fid} {name}',fill=RGB[1]);paste(allframes,portraits[i],(338,ay+30))
        for d in range(4):
            ad.text((3,ay+13+d*18),DIRECTIONS[d][0].upper(),fill=RGB[1])
            for n,im in enumerate(fields[i][d]+abilities[i][d]):paste(allframes,im,(20+n*42,ay+13+d*18))
    save_image(roster,OUT/'roster_native.png');save_image(roster.resize((1200,540),Image.Resampling.NEAREST),OUT/'roster_2x.png')
    save_image(allframes,OUT/'all_frames_native.png');save_image(allframes.resize((768,allframes.height*2),Image.Resampling.NEAREST),OUT/'all_frames_2x.png')
    sources+=make_lineage(fields,portraits)
    with Image.open(ROOT/'assets/return_region/greenwake_common.png')as im:scene=im.convert('RGB').crop((216,64,456,224))
    gifs=[]
    for f in range(4):
        frame=scene.copy()
        for i in range(15):
            x=10+(i%5)*44;y=12+(i//5)*47
            ImageDraw.Draw(frame).ellipse((x+4,y+13,x+12,y+15),fill=RGB[P['shadow']]);paste(frame,fields[i][i%4][f],(x,y))
        gifs.append(frame)
    save_image(gifs[0],OUT/'greenwake_composite_native.png');save_image(gifs[0].resize((720,480),Image.Resampling.NEAREST),OUT/'greenwake_composite_3x.png')
    gifs[0].save(OUT/'roster_walk_native.gif',save_all=True,append_images=gifs[1:],duration=135,loop=0,disposal=2,optimize=False)
    return sources,patches

def silhouette_metrics(fields):
    current=[mask(row[0][0]).tobytes()for row in fields];assert len(set(current))==15
    # Exact read-only released sheet. Legacy images never feed Return authoring.
    prior=json.loads((ROOT/'assets/underwater_creatures/manifest.json').read_text())
    oldids=prior['silhouette_comparison']['released_form_ids']+prior['form_ids'];assert len(oldids)==89
    with Image.open(ROOT/'assets/underwater_creatures/released89_silhouettes_native.png')as im:src=im.convert('RGB')
    oldmasks=[];sheet=Image.new('RGB',(560,24+15*42),RGB[P['white']]);dr=ImageDraw.Draw(sheet)
    dr.text((4,3),'104 NATIVE SILHOUETTES / RELEASED89 + RETURN15 / ART ONLY',fill=RGB[1])
    for i,fid in enumerate(oldids+list(FORM_IDS)):
        x=i%7*80;y=24+i//7*42;dr.text((x+4,y),str(fid),fill=RGB[1])
        for d in range(4):
            if i<89:
                xx=i%7*80+4+d*18;yy=24+i//7*42+13;tile=src.crop((xx,yy,xx+16,yy+16))
                data=bytes(255 if px==RGB[1]else 0 for px in getattr(tile,'get_flattened_data',tile.getdata)());m=Image.frombytes('L',(16,16),data)
                if d==0:oldmasks.append(data)
            else:m=mask(fields[i-89][d][0])
            sheet.paste(Image.new('RGB',(16,16),RGB[1]),(x+4+d*18,y+13),m)
    assert not set(current).intersection(oldmasks),'Released front silhouette duplicated'
    save_image(sheet,OUT/'released104_silhouettes_native.png');save_image(sheet.resize((1120,sheet.height*2),Image.Resampling.NEAREST),OUT/'released104_silhouettes_2x.png')
    nearest=[]
    for i,ma in enumerate(current):
        pool=list(zip(oldids,oldmasks))+[(FORM_IDS[j],v)for j,v in enumerate(current)if j!=i]
        dist,fid=min((sum(x!=y for x,y in zip(ma,m)),fid)for fid,m in pool)
        nearest.append({'form_id':FORM_IDS[i],'nearest_form_id':fid,'different_front_mask_pixels':dist})
    return {'current_unique_front_masks':15,'released_form_ids':oldids,'cross_release_front_mask_matches':0,'nearest_front_masks':nearest}
def terrain_metrics(fields,abilities,patches):
    rows=[]
    for i,fid in enumerate(FORM_IDS):
        for t,patch in enumerate(patches):
            ratios=[];edges=[]
            for group in(fields[i],abilities[i]):
                for direction in group:
                    for im in direction:
                        n=good=en=egood=0
                        for y in range(1,15):
                            for x in range(1,15):
                                px=im.getpixel((x,y))
                                if not px:continue
                                visible=sum((v-w)**2 for v,w in zip(RGB[px],patch.getpixel((x+4,y+4))))>=48**2;n+=1;good+=visible
                                if any(im.getpixel((xx,yy))==0 for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))):en+=1;egood+=visible
                        ratios.append(good/n);edges.append(egood/en)
            rows.append({'form_id':fid,'terrain':SCENE_SOURCES[t][0],'minimum_distinct_opaque_fraction':round(min(ratios),4),'minimum_distinct_boundary_fraction':round(min(edges),4)})
    return {'metric':'Native RGB555 distance >=48; all28 poses per terrain. Heuristic readability only, never emulator/gameplay/performance evidence.',
      'samples':15*28*len(patches),'rows':rows,'minimum_opaque_fraction':min(r['minimum_distinct_opaque_fraction']for r in rows),'minimum_boundary_fraction':min(r['minimum_distinct_boundary_fraction']for r in rows)}
def validate_legacy_prefix(world_successor=None):
    from legacy_art_successor import validate_legacy_prefix as validate
    return validate(ROOT,OUT/'legacy_prefix_sha256.json',world_successor)
def output_hashes():
    files=sorted(p for p in OUT.iterdir()if p.is_file()and p.suffix in('.png','.gif','.json','.txt')and p.name not in('validation.json',))
    files+=sorted((ROOT/'src/return_creature_art_data').glob('*.inc'))+[ROOT/'src/return_creature_art.c',ROOT/'src/return_creature_art.h']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}
def generate(world_successor=None):
    OUT.mkdir(exist_ok=True);legacy=validate_legacy_prefix(world_successor)
    fields=[[[field(fid,d,f)for f in range(4)]for d in DIRECTIONS]for fid in FORM_IDS]
    abilities=[[[field(fid,d,p,p)for p in range(3)]for d in DIRECTIONS]for fid in FORM_IDS];portraits=[portrait(fid)for fid in FORM_IDS]
    validation=validate_pixels(fields,abilities,portraits)
    spec=importlib.util.spec_from_file_location('return_creature_codegen',OUT/'codegen.py');cg=importlib.util.module_from_spec(spec);spec.loader.exec_module(cg)
    chunks=cg.emit_code(ROOT,FORM_IDS,NAMES,fields,abilities,portraits)
    sources,patches=make_previews(fields,abilities,portraits);comparison=silhouette_metrics(fields);terrain=terrain_metrics(fields,abilities,patches)
    (OUT/'terrain_readability.json').write_text(json.dumps(terrain,indent=2)+'\n')
    manifest={'schema_version':1,'design_version':'RETURN_I_DESIGN_R2','design_manifest_sha256':'52f5f2a7213da4540eb31c85dbe85a1f2a7468ccba9812e78fac3133fee0a4c9',
      'generator':'assets/generate_return_creatures.py','form_ids':list(FORM_IDS),'names':list(NAMES),'directions':list(DIRECTIONS),
      'status':'ART ONLY: sprite sheets and composites are not emulator captures, proof of obtainability, live rendering, frame budget or VRAM/state acceptance.',
      'rights':'Original code-native pixel geometry. No Nintendo/Pokemon extraction, tracing, image extraction or third-party raster inputs.',
      'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'codegen_sha256':hashlib.sha256((OUT/'codegen.py').read_bytes()).hexdigest(),
      'palette_sha256':hashlib.sha256(json.dumps(COLORS).encode()).hexdigest(),'data_bytes':cg.DATA_BYTES,'runtime_data_bytes':0,'runtime_bss_bytes':0,
      'persistent_obj_allocation_bytes':0,'rom_budget_bytes':cg.ROM_BUDGET_BYTES,'include_bytes':chunks,'max_include_bytes':max(chunks),'scene_review_sources':sources,
      'anchor':[8,8],'shadow_anchor':[8,13],'shadow_in_sprite':False,'idle_frame':0,'walk_ticks_by_form':dict(zip(map(str,FORM_IDS),WALK_TICKS)),
      'ability_poses':['anticipation','release','settle'],'recovery':'Caller returns to authored walking after settle. Recovery is not a fourth cast frame.',
      'briefs':BRIEFS,'validation':validation,'legacy_prefix':legacy,'silhouette_comparison':comparison,
      'terrain_visibility_minimum_opaque':terrain['minimum_opaque_fraction'],'terrain_visibility_minimum_boundary':terrain['minimum_boundary_fraction']}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'CREDITS.txt').write_text(manifest['rights']+'\n435 original indexed images. All16px fields leave a transparent one-pixel rim. Portraits separately composed at32px.\nShared existing RGB555 palette unchanged. Read-only original legacy art used solely in lineage/review sheets. Art reviews are not emulator evidence.\n')
    validate_legacy_prefix(world_successor);return manifest

def verify(manifest,world_successor=None):
    before=output_hashes();generate(world_successor);assert before==output_hashes(),'Nondeterministic regeneration'
    report={'deterministic_regeneration':True,'pixel_validation':manifest['validation'],'legacy_prefix':validate_legacy_prefix(world_successor),'output_sha256':output_hashes()}
    with tempfile.TemporaryDirectory(prefix='return-art-')as td:
        td=Path(td);sys.path.insert(0,str(ROOT/'tools'));from arm_toolchain import resolve_arm_tools
        tc=resolve_arm_tools('gcc','size',root=ROOT);obj=td/'return_creature_art.o'
        subprocess.run([tc['gcc'],'-std=c99','-mcpu=arm7tdmi','-mthumb','-O2','-ffreestanding','-fno-builtin','-fstack-usage','-Wall','-Wextra','-Werror','-c',str(ROOT/'src/return_creature_art.c'),'-o',str(obj)],check=True,capture_output=True)
        size=subprocess.check_output([tc['size'],str(obj)],text=True);sections=list(map(int,size.splitlines()[-1].split()[:3]));assert sections[1:]==[0,0]and sections[0]<=manifest['rom_budget_bytes']
        stack=[int(line.split('\t')[1])for p in td.glob('*.su')for line in p.read_text().splitlines()];assert stack and max(stack)<=24
        report.update({'arm_compile':'passed','arm_rom_object_bytes':sections[0],'arm_data_bytes':sections[1],'arm_bss_bytes':sections[2],'max_arm_stack_bytes':max(stack),'max_include_bytes':manifest['max_include_bytes']})
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');return {k:v for k,v in report.items()if k not in('output_sha256','pixel_validation')}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');p.add_argument('--world-successor',choices=['connected-roads-c4']);args=p.parse_args();m=generate(args.world_successor)
    print(json.dumps(verify(m,args.world_successor)if args.verify else {'generated_forms':FORM_IDS,'data_bytes':m['data_bytes'],'max_include_bytes':m['max_include_bytes']},indent=2))
if __name__=='__main__':main()
