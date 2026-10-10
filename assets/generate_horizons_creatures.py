#!/usr/bin/env python3
"""Original Shared Horizons pixel animals, directly drawn in existing RGB555.
Only writes assets/horizons_creatures and src/horizons_creature_art{.c,.h,_data}.
No downloaded, traced, extracted, image-generated, or external creature pixels.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, subprocess, sys, tempfile
from PIL import Image, ImageDraw
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/horizons_creatures'
sys.path.insert(0,str(ROOT/'assets'))
from magma_palette import Art as BaseArt, P, PAL, rgb as RGB, COLORS
PLAN=ROOT/'docs/horizons-design/shared_horizons_plan.json'
BRIEFS=json.loads(PLAN.read_text())['forms']
FORM_IDS=tuple(range(105,121));NAMES=tuple(f['name'] for f in BRIEFS);KEYS=tuple(n.lower() for n in NAMES)
DIRECTIONS=('down','up','left','right')
WALK_TICKS=((7,5,7,6),(9,7,9,8),(10,8,10,8),(12,9,12,10),(6,5,10,8),(11,9,12,10),(8,7,8,7),(10,7,10,8),(8,6,8,7),(7,6,7,6),(5,6,5,7),(12,10,12,10),(5,4,5,4),(10,8,10,9),(8,7,8,7),(6,5,9,5))
class Art(BaseArt):
    def check(self,pts):
        assert all(0<=x<self.im.width and 0<=y<self.im.height for x,y in pts),(self.im.size,pts)
    def p(self,pts,c):self.check(pts);super().p(pts,c)
    def l(self,pts,c,w=1):self.check(pts);super().l(pts,c,w)
    def r(self,b,c):self.check(((b[0],b[1]),(b[2],b[3])));super().r(b,c)
    def e(self,b,c):self.check(((b[0],b[1]),(b[2],b[3])));super().e(b,c)
    def dot(self,x,y,c):self.check(((x,y),));super().dot(x,y,c)
class Pen:
    """Joint coordinates explicitly bounded to the transparent native actor rim."""
    def __init__(self,a,dy=0):self.a,self.dy=a,dy
    def pt(self,x,y):return max(1,min(14,x)),max(1,min(14,y+self.dy))
    def p(self,pts,c):self.a.p([self.pt(x,y)for x,y in pts],c)
    def l(self,pts,c,w=1):
        pts=[self.pt(x,y)for x,y in pts]
        if w>1:pts=[(max(2,min(13,x)),max(2,min(13,y)))for x,y in pts]
        self.a.l(pts,c,w)
    def r(self,b,c):
        x,y=self.pt(*b[:2]);xx,yy=self.pt(*b[2:]);self.a.r((min(x,xx),min(y,yy),max(x,xx),max(y,yy)),c)
    def e(self,b,c):
        x,y=self.pt(*b[:2]);xx,yy=self.pt(*b[2:]);self.a.e((min(x,xx),min(y,yy),max(x,xx),max(y,yy)),c)
    def dot(self,x,y,c):self.a.dot(*self.pt(x,y),c)
def gait(f,cast):
    if cast is None:return (-1,0,1,0)[f],(0,1,0,-1)[f],(0,-1,0,0)[f]
    return (-2,2,1)[cast],(1,-2,2)[cast],(1,-1,0)[cast]
def finish(a,d):return a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)if d=='right'else a.im
def eye(q,x,y):q.dot(x,y,'white');q.dot(x,y+1,'ink')
def face(q,d,x,y,w,c):
    q.p([(x,y+1),(x+1,y),(x+w-1,y),(x+w,y+2),(x+w-1,y+4),(x+2,y+4)],'ink')
    q.p([(x+1,y+1),(x+w-1,y+1),(x+w-1,y+3),(x+2,y+3)],c)
    if d=='up':q.l([(x+2,y+1),(x+w-1,y+2)],'wood3')
    elif d in ('left','right'):eye(q,x+1,y+1);q.dot(x,y+3,'ink')
    else:eye(q,x+1,y+1);eye(q,x+w-1,y+1);q.dot(x+w//2,y+3,'ink')
def leg(q,x,y,s,c,length=3):
    q.l([(x,y),(x+s,y+length-1),(x+s-1,y+length)],'ink',2)
    q.l([(x,y),(x+s,y+length-1)],c);q.dot(x+s-1,y+length,c)

def marten(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h);p=Pen(a);side=d in ('left','right')
    # One attached tail ends in two tapering leaf lobes, never two detached tails.
    tx=12 if not v else 11
    q.l([(10,10),(tx,9),(13,7+t)],'ink',2)
    q.p([(12,8),(11,5+t),(12,2+t),(14,4+t),(13,8),(14,10),(12,10)],'ink')
    q.p([(12,7),(12,4+t),(13,4+t),(13,6),(13,8),(14,9),(12,9)],'pine5')
    if cast==1:q.l([(10,8),(12,5),(13,2)],'leafwarm')
    if not v:
        for x,z in ((4,s),(7,-t),(10,-s)):leg(p,x,10,z,'pine4',3)
        q.p([(3,8),(6,6),(10,6),(12,8),(11,11),(4,11)],'ink')
        q.p([(4,8),(7,7),(10,7),(11,9),(10,10),(4,10)],'pine4')
        x=1 if side else 3;y=6 if d!='up'else 4
        q.e((x+1,y-2,x+3,y),'ink');q.e((x+4,y-2,x+6,y),'ink')
        q.p([(x,y+1),(x+2,y),(x+6,y),(x+6,y+3),(x+3,y+5),(x,y+3)],'ink')
        q.p([(x+1,y+1),(x+5,y+1),(x+4,y+3),(x+3,y+4),(x+1,y+2)],'leafwarm')
        if d=='down':eye(q,x+1,y+1);eye(q,x+4,y+1);q.dot(x+3,y+3,'ink')
        elif side:eye(q,x+1,y+1);q.dot(x,y+3,'ink')
        else:q.l([(x+2,y+1),(x+4,y+3)],'pine3')
    else:
        for x,z in ((6,s),(9,-s)):leg(p,x,10,z,'wood4',3)
        # Visible waist, lifted arms, and open armpits make the evolution vertical.
        q.p([(6,6),(9,6),(10,8),(9,12),(6,12),(5,9)],'ink');q.l([(7,7),(8,9),(7,11)],'pine4',2)
        for x,sg in ((5,-1),(10,1)):
            q.l([(7 if sg<0 else 8,8),(x,7),(x+sg,4+t)],'ink');q.dot(x+sg,4+t,'wood4')
            q.p([(x,6),(x+sg*2,2+t),(x+sg*3,4+t),(x+sg,7)],'ink')
            q.l([(x,5),(x+sg*2,3+t),(x+sg*2,4+t)],'pine5')
        x=3 if side else 5;y=2 if d!='up'else 1
        q.e((x,y,x+2,y+2),'ink');q.e((x+4,y,x+6,y+2),'ink')
        face(q,d,x,y+2,5,'leafwarm')
    return finish(a,d)

def bird(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h);p=Pen(a);side=d in ('left','right')
    for x,z in ((5,s),(10,-t)):
        if v:p.l([(x,9),(x+z,12)],'wood3')
        else:p.l([(x,10),(x+z,12)],'slate')
        p.l([(x+z-1,13),(x+z+1,13)],'ink',2);p.dot(x+z-1,12,'slate')
    if not v:
        q.e((4,5,11,12),'ink');q.e((5,6,10,11),'fire2')
        for x,sg in ((4,-1),(11,1)):
            q.l([(x,7),(x+sg,9+t),(x,10)],'ink',2);q.dot(x+sg,8+t,'fire1')
        # Pale open bowl collar surrounds orange living breast.
        q.l([(4,5),(5,8),(8,9),(11,7),(11,5)],'ink',2)
        q.l([(4,5),(6,7),(9,7),(11,5)],'white');q.dot(8,8,'gold3')
        x=3 if side else 5;y=3 if d!='up'else 2
        q.e((x,y,x+5,y+4),'ink');q.e((x+1,y,x+4,y+3),'fire2')
        if d=='down':eye(q,x+1,y+1);eye(q,x+4,y+1);q.l([(7,y+3),(8,y+3)],'slate')
        elif side:eye(q,x+1,y+1);q.r((x-1,y+2,x,y+3),'slate')
        else:q.dot(x+3,y+1,'fire3')
    else:
        q.e((5,7,11,11),'ink');q.e((6,8,10,10),'fire1')
        q.l([(7,9),(7,4),(8,3)],'ink',3);q.l([(7,8),(7,5)],'fire3')
        # Hood is continuous around head; long neck remains visible below it.
        x=3 if side else(6 if d=='up'else 5)
        q.p([(x,6),(x-1,3),(x+1,1),(x+4,1),(x+6,4),(x+5,7),(x+3,6)],'ink')
        q.l([(x,5),(x,3),(x+1,2),(x+4,2),(x+5,4),(x+4,6)],'white',2)
        q.e((x+1,3,x+4,6),'fire2')
        if d=='down':eye(q,x+1,3);eye(q,x+4,3);q.dot(x+3,5,'slate')
        elif side:eye(q,x+1,3);q.r((x-1,4,x,5),'slate')
        else:q.l([(x+1,3),(x+3,4)],'gold2')
        for x,sg in ((5,-1),(11,1)):
            q.l([(x,8),(x+sg,9+t),(x,10)],'ink',2);q.dot(x+sg,9+t,'fire2')
        if cast==1:q.dot(4,10,'gold3')
    return finish(a,d)

def dillo(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h);p=Pen(a);side=d in ('left','right')
    if v:
        # Open upright fan exposes a slit of sky between its ribs.
        q.p([(10,9),(10,3+t),(12,1+t),(14,3),(14,8),(12,11)],'ink')
        q.l([(11,8),(11,4+t),(12,3+t)],'wood4');q.l([(12,9),(13,5),(13,3)],'gold2');q.dot(12,6,'transparent')
    else:
        q.p([(10,10),(12,7+t),(14,7+t),(14,11),(12,12)],'ink')
        q.l([(11,10),(13,8+t)],'wood4');q.l([(11,10),(13,10)],'gold2')
    for x,z in ((4,s),(7,-t),(10,-s)):leg(p,x,10,z,'wood3',3)
    if v:
        for x,z in ((3,s),(6,-t)):
            p.l([(x,10),(x+z,12),(x+z-1,13)],'ink',2);p.l([(x+z-1,13),(x+z+1,13)],'wood5')
    q.p([(3,9),(5,6 if v else 5),(8,4),(11,6),(12,10),(10,12),(4,11)],'ink')
    q.p([(4,9),(6,6),(8,5),(10,7),(11,10),(9,11),(4,10)],'wood2')
    for x,y in (((5,7),(7,5),(9,6),(11,8))if v else((5,7),(7,6),(9,7))):
        q.l([(x,y),(x+1,y+1),(x,y+4)],'stone4');q.dot(x,y,'wood4')
    x=1 if side else 2;y=8 if d!='up'else 5
    q.p([(x+1,y+1),(x+1,y-2),(x+2,y-3),(x+3,y),(x+5,y),(x+5,y+3),(x+2,y+4),(x,y+3)],'ink')
    q.p([(x+2,y),(x+2,y-1),(x+3,y+1),(x+4,y+1),(x+4,y+2),(x+1,y+3)],'skin2')
    if d=='up':q.dot(x+3,y+1,'wood3')
    else:eye(q,x+2,y+1);q.dot(x,y+3,'rose0')
    if d=='down':eye(q,x+4,y+1)
    return finish(a,d)

def ray(v,d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h);p=Pen(a);side=d in ('left','right')
    q.l([(8,8),(11,6),(12,3+t),(11,1+t)],'ink',2);q.l([(8,8),(11,5),(11,3+t)],'water3')
    if v:q.p([(11,4),(9,2+t),(11,1),(14,2),(13,4)],'ink');q.l([(10,2+t),(13,2)],'water4')
    if v:
        # Connected asymmetric W: face bridges fins, open fin arches remain empty.
        q.l([(7,8),(4,5+t),(2,7),(1,11),(3,12),(5,10)],'ink',2)
        q.l([(8,8),(10,4-t),(13,6),(14,10),(12,12),(10,10)],'ink',2)
        q.l([(6,8),(4,6+t),(3,7),(2,10)],'water4',2);q.l([(9,8),(11,5-t),(12,6),(13,9)],'water3',2)
        p.l([(2,10),(2+s,13),(4+s,13)],'ink');p.dot(3+s,13,'water4')
        p.l([(13,10),(13-t,12),(11-t,13)],'ink');p.dot(11-t,12,'water3')
        q.p([(5,8),(7,6),(9,7),(11,10),(8,12),(5,11)],'ink');q.p([(6,8),(8,7),(10,10),(8,11),(6,10)],'watergleam')
    else:
        q.p([(7,5),(11,7),(12 if side else(13 if d=='up'else 14),10+t),(12,12),(9,11),(7,13),(4,11),(2 if d=='up'else 1,10-s),(4,7)],'ink')
        q.p([(7,6),(10,8),(11 if side else 12,10+t),(10,10),(8,11),(7,12),(4,10),(2,10-s),(5,8)],'blue3')
        q.l([(4,10),(6,11),(8,11),(10,10)],'watergleam')
        p.l([(2,10-s),(2+s,12),(4+s,13)],'ink');p.dot(3+s,12,'water4')
        p.l([(12,10+t),(13-t,12),(11-t,13)],'ink');p.dot(11-t,12,'water4')
    x=4 if side else 5;y=7 if d!='up'else 5
    q.e((x,y,x+5,y+4),'water4')
    if d=='up':q.l([(x+1,y+1),(x+3,y+2)],'water2')
    elif side:eye(q,x,y);q.l([(x,y+3),(x+2,y+3)],'water0')
    else:eye(q,x,y);eye(q,x+4,y);q.l([(x+1,y+3),(x+2,y+4),(x+3,y+3)],'water0')
    return finish(a,d)

def boar(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h);p=Pen(a);side=d in ('left','right')
    q.l([(11,9),(14,8),(14,5+t),(12,5+t),(12,7)],'ink');q.dot(13,6+t,'wood3')
    for x,z in ((4,s),(7,-t),(10,-s),(12,t)):leg(p,x,10,z,'fire0',3)
    q.p([(3,8),(4,4),(10,4),(12,7),(12,11),(4,11)],'ink');q.r((5,5,10,8),'wood1');q.e((4,6,12,11),'fire0');q.l([(6,6),(9,6)],'fire1')
    x=1 if side else 3;y=7 if d!='up'else 5
    q.p([(x,y+1),(x+1,y-2),(x+3,y),(x+5,y-1),(x+7,y+2),(x+5,y+5),(x+1,y+5)],'ink')
    q.p([(x+1,y+1),(x+3,y),(x+5,y+1),(x+6,y+3),(x+4,y+4),(x+1,y+4)],'wood3')
    if d!='up':
        eye(q,x+1,y+1)
        if not side:eye(q,x+5,y+1)
        q.r((x+1,y+3,x+4,y+4),'skin1');q.dot(x+1,y+3,'ink');q.dot(x+3,y+3,'ink')
        q.l([(x,y+4),(x,y+2),(x+1,y+2)],'silver');q.l([(x+5,y+4),(x+6,y+2),(x+6,y)],'white')
    else:q.l([(x+2,y+2),(x+4,y+3)],'fire0')
    return finish(a,d)

def lace(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h);p=Pen(a);side=d in ('left','right')
    for y,z in ((8,s),(10,t),(12,-s)):
        p.l([(7,y),(5+z,y+1)],'ink');p.l([(8,y),(10-z,y+1)],'ink')
    # Broad scallops and open net cells are unlike four rigid dragonfly paddles.
    spread=0 if cast!=0 else 2
    for x,sg in ((6,-1),(9,1)):
        reach=4-spread-(1 if side and sg==1 else 0)
        q.p([(x,6),(x+sg*reach,3+t*sg),(x+sg*(reach+1),5+t*sg),(x+sg*reach,7),(x+sg*reach,9),(x+sg*(reach-1),11),(x,10)],'ink')
        q.p([(x,6),(x+sg*(reach-1),4+t*sg),(x+sg*reach,5+t*sg),(x+sg*(reach-1),7),(x+sg*(reach-1),9),(x+sg,10)],'leaflight')
        q.l([(x,7),(x+sg*(reach-1),6)],'pine3');q.l([(x,8),(x+sg*(reach-1),9)],'pine3');q.dot(x+sg,7,'white')
    q.l([(7,6),(5,2),(3,1)],'ink');q.l([(5,2),(6,1)],'ink');q.l([(8,6),(10,2),(12,1)],'ink');q.l([(10,2),(9,1)],'ink')
    q.l([(7,6),(8,9),(7,12)],'ink',3);q.l([(7,7),(8,9),(7,11)],'pine5')
    x=5 if side else 6;y=4 if d!='up'else 3
    q.e((x,y,x+3,y+3),'ink');q.l([(x+1,y+1),(x+2,y+2)],'leafwarm')
    if d!='up':q.dot(x,y+1,'white');q.dot(x+2,y+1,'white');q.dot(x+1,y+3,'pine2')
    return finish(a,d)

def scorpion(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h);p=Pen(a);side=d in ('left','right')
    # Four pairs ripple independently under the continuous segmented abdomen.
    for y,z in ((7,s),(9,t),(11,-s),(12,-t)):
        p.l([(6,y),(3+z,y-1),(2+z,y)],'ink');p.dot(3+z,y-1,'fire1')
        p.l([(9,y),(12-z,y-1),(13-z,y)],'ink');p.dot(12-z,y-1,'fire1')
    q.l([(9,10),(12,8),(13,5),(12+t,2),(10+t,2)],'ink',2);q.l([(9,10),(11,8),(12,5),(11+t,3)],'fire0')
    q.e((8+t,1,11+t,4),'ink');q.e((9+t,2,10+t,3),'fire3');q.dot(10+t,2,'gold4')
    q.e((5,6,10,12),'ink');q.e((6,7,9,11),'fire0')
    for y in (8,10):q.l([(6,y),(9,y)],'fire2')
    x=4 if side else 5;y=5 if d!='up'else 3
    q.e((x,y,x+5,y+4),'ink');q.e((x+1,y+1,x+4,y+3),'fire1')
    if d!='up':eye(q,x+1,y);eye(q,x+4,y);q.dot(x+2,y+3,'wood5')
    for x,sg in ((5,-1),(10,1)):
        q.l([(x,7),(x+sg*2,5+s),(x+sg*3,5+s),(x+sg*3,7+s)],'ink');q.dot(x+sg*2,5+s,'fire3')
    return finish(a,d)

def ox(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h);p=Pen(a);side=d in ('left','right')
    q.l([(12,7),(14,8),(14,11+t)],'ink');q.dot(14,11+t,'wood2')
    for x,z in ((3,s),(6,-t),(10,-s),(12,t)):leg(p,x,10,z,'stone4',3);p.dot(x+z,13,'slate')
    q.p([(2,6),(4,4),(11,4),(13,6),(13,11),(3,11)],'ink');q.r((4,5,11,10),'stone4');q.l([(5,5),(10,5)],'white')
    x=1 if side else 3;y=6 if d!='up'else 3
    q.p([(x+1,y+3),(x+2,y+7),(x+4,y+6),(x+5,y+7),(x+6,y+3)],'ink')
    q.p([(x+2,y+3),(x+3,y+5),(x+4,y+4),(x+5,y+5),(x+5,y+3)],'stone4')
    for hx,sg in ((x+1,-1),(x+6,1)):
        q.l([(hx,y+1),(hx+sg*2,y),(hx+sg*2,y-2)],'ink');q.dot(hx+sg,y,'wood4')
    q.r((x,y,x+7,y+4),'ink');q.r((x+1,y,x+6,y+3),'stone4')
    if d!='up':
        eye(q,x+1,y+1)
        if not side:eye(q,x+6,y+1)
        q.r((x+1,y+3,x+6,y+4),'stone2');q.dot(x+2,y+3,'ink');q.dot(x+5,y+3,'ink')
    else:q.l([(x+2,y+1),(x+5,y+2)],'stone3')
    return finish(a,d)

def dragonfly(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h);p=Pen(a);side=d in ('left','right')
    q.l([(7,7),(8,10),(7+s,12),(8+s,14)],'ink',2)
    for x,y in ((8,9),(7+s,11),(8+s,13)):q.dot(x,y,'gold2')
    inset=1 if cast==0 else 0
    for y,z in ((6,t),(9,-t)):
        for x,sg in ((6,-1),(9,1)):
            reach=4-inset-(1 if side and sg==1 else 0)
            q.p([(x,y),(x+sg*(reach-1),y-2+z),(x+sg*reach,y-2+z),(x+sg*reach,y+z),(x+sg*2,y+1)],'ink')
            q.l([(x+sg,y),(x+sg*(reach-1),y-1+z),(x+sg*reach,y-1+z)],'silver');q.dot(x+sg*(reach-1),y-2+z,'white')
    q.l([(7,6),(8,9)],'ink',3);q.dot(7,7,'wood3')
    x=4 if side else 5;y=3 if d!='up'else 2
    q.e((x,y,x+3,y+4),'ink');q.e((x+1,y+1,x+2,y+3),'watergleam')
    q.e((x+4,y,x+6,y+4),'ink');q.e((x+5,y+1,x+5,y+3),'water4')
    if d!='up':q.dot(x+1,y+2,'ink');q.dot(x+5,y+2,'ink');q.dot(x+3,y+4,'wood4')
    else:q.dot(x+2,y+1,'silver');q.dot(x+5,y+1,'silver')
    return finish(a,d)

def turtle(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h);p=Pen(a);side=d in ('left','right')
    for x,y,z,sg in ((4,8,s,-1),(11,8,-s,1),(4,11,t,-1),(11,11,-t,1)):
        p.p([(x,y),(x+sg*2,y+z),(x+sg*2,y+z+2),(x,y+2)],'ink');p.dot(x+sg,y+z+1,'water4')
    q.l([(11,8),(13,6+t)],'ink');q.dot(12,7+t,'water3')
    q.e((2,5,13,12),'ink');q.e((3,6,12,11),'watergleam');q.e((4,6,11,10),'teal1');q.l([(5,7),(8,6),(10,7)],'water3')
    x=1 if side else 5;y=8 if d!='up'else 2
    q.l([(7,9),(x+2,y+2),(x+1,y+3)],'ink',3);q.l([(7,9),(x+2,y+2)],'water4')
    q.e((x,y,x+4,y+3),'ink');q.e((x+1,y,x+3,y+2),'water4')
    if d!='up':eye(q,x+1,y);q.l([(x,y+2),(x-1,y+3)],'water3')
    if d=='down':eye(q,x+3,y)
    if d=='up':q.dot(x+2,y,'teal2')
    return finish(a,d)

def snake(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h);side=d in ('left','right')
    # One tapered tail is continuous with an asymmetric S, no loops of hardware.
    q.l([(11,13),(13,12),(11+s,10),(7,11),(4,9),(5+t,7),(9,6),(10,4)],'ink',3)
    q.l([(11,13),(12,12),(10+s,10),(7,11),(5,9),(6+t,7),(9,6),(10,4)],'pine4')
    for x,y,z in ((6,10,s),(6,7,t),(10,5,-t)):
        q.p([(x,y+1),(x-2,y),(x-1,y-2+z),(x+1,y-1),(x+2,y),(x+1,y+2)],'ink')
        q.p([(x,y),(x-1,y-1+z),(x,y-1),(x+1,y),(x,y+1)],'leaflight')
    x=3 if side else 6;y=3 if d!='up'else 1
    q.l([(9,6),(x+3,y+2)],'ink',3);q.l([(9,6),(x+3,y+2)],'pine4')
    q.p([(x,y+1),(x+2,y),(x+5,y),(x+6,y+2),(x+4,y+4),(x+1,y+3)],'ink')
    q.p([(x+1,y+1),(x+3,y+1),(x+5,y+2),(x+4,y+3),(x+1,y+2)],'pine5')
    if d!='up':eye(q,x+1,y+1);q.dot(x+1,y+3,'wood5')
    if d=='down':eye(q,x+4,y+1)
    if d=='up':q.l([(x+2,y+1),(x+4,y+2)],'pine3')
    return finish(a,d)

def rabbit(d,f,cast):
    a=Art(16,16,'transparent');s,t,h=gait(f,cast);q=Pen(a,h);p=Pen(a);side=d in ('left','right')
    q.e((11,8+t,14,11+t),'ink');q.e((12,9+t,13,10+t),'white')
    for x,z in ((5,s),(10,-t)):p.l([(x,10),(x+z,12),(x+z-1,13)],'ink',2);p.dot(x+z,12,'silver')
    q.e((4,6,12,12),'ink');q.e((5,7,11,11),'silver');q.l([(6,9),(8,10)],'white')
    # Round offset discs are living ears: soft neck joins below each silver rim.
    q.l([(6,7),(4,5),(4,3+t)],'ink',2);q.e((2,1+t,6,5+t),'ink');q.e((3,2+t,5,4+t),'wood4');q.dot(4,2+t,'white')
    q.l([(9,7),(11,5),(11,3-t)],'ink',2);q.e((9,2-t,13,6-t),'ink');q.e((10,3-t,12,5-t),'gold2');q.dot(11,3-t,'white')
    x=2 if side else 4;y=6 if d!='up'else 4
    face(q,d,x,y,6,'stone5')
    if d!='up':q.dot(x+3,y+3,'rose4');q.dot(x+2,y+4,'white')
    return finish(a,d)

DRAW={105:lambda d,f,c:marten(0,d,f,c),106:lambda d,f,c:marten(1,d,f,c),107:lambda d,f,c:bird(0,d,f,c),108:lambda d,f,c:bird(1,d,f,c),109:lambda d,f,c:dillo(0,d,f,c),110:lambda d,f,c:dillo(1,d,f,c),111:lambda d,f,c:ray(0,d,f,c),112:lambda d,f,c:ray(1,d,f,c),113:boar,114:lace,115:scorpion,116:ox,117:dragonfly,118:turtle,119:snake,120:rabbit}
def field(fid,d,f,cast=None):
    if type(fid)is not int or fid not in FORM_IDS or d not in DIRECTIONS or type(f)is not int or not 0<=f<4 or(cast is not None and(type(cast)is not int or not 0<=cast<3)):raise ValueError('Invalid form, direction, walking frame or cast pose')
    return DRAW[fid](d,f,cast)

def big_eye(a,x,y):
    a.e((x,y,x+3,y+4),'ink');a.r((x+1,y,x+2,y+2),'white');a.dot(x+1,y+2,'ink')
def portrait(fid):
    """Separate 32px compositions: larger faces and anatomy, not scaled frames."""
    if type(fid)is not int or fid not in FORM_IDS:raise ValueError('Unsupported portrait form')
    a=Art(32,32,'transparent')
    if fid in (105,106):
        v=fid==106
        a.l([(22,24),(27,21),(27,16)],'ink',3);a.l([(22,24),(26,21),(27,17)],'pine4',2)
        a.p([(26,19),(23,12),(24,6),(28,10),(28,15),(30,14),(30,21),(27,24)],'ink')
        a.p([(26,17),(25,12),(25,9),(27,11),(27,17),(29,17),(29,20),(27,22)],'pine5');a.l([(26,12),(27,19)],'leaflight')
        if not v:
            for x,y in ((8,23),(13,24),(21,22)):
                a.l([(x,y),(x-1,28),(x-4,29)],'ink',3);a.l([(x,y),(x-1,27)],'pine4')
            a.p([(5,19),(11,13),(20,14),(26,19),(24,24),(10,25),(5,23)],'ink');a.p([(8,19),(13,15),(20,16),(24,20),(22,23),(10,23)],'pine4')
            a.e((4,9,10,15),'ink');a.e((6,10,8,13),'wood4');a.e((14,8,20,14),'ink');a.e((16,9,18,12),'wood4')
            a.p([(3,16),(6,13),(14,12),(20,16),(17,21),(11,25),(5,21)],'ink');a.p([(5,16),(8,14),(14,14),(18,17),(15,21),(11,23),(6,20)],'leafwarm')
            big_eye(a,6,15);big_eye(a,14,15);a.l([(10,20),(12,20),(11,21)],'ink');a.dot(5,19,'rose4')
        else:
            for x in (13,19):a.l([(x,23),(x-1,28),(x-4,29)],'ink',3);a.l([(x,24),(x-1,27)],'wood4')
            a.p([(12,12),(18,11),(21,18),(19,25),(13,25),(11,20)],'ink');a.p([(14,14),(17,14),(19,19),(17,23),(14,22)],'pine4')
            a.l([(13,17),(8,14),(6,8)],'ink',3);a.l([(19,17),(24,14),(25,7)],'ink',3)
            a.p([(10,13),(5,5),(2,5),(3,12),(7,16)],'ink');a.p([(9,12),(5,7),(4,7),(5,12),(7,14)],'pine5')
            a.p([(21,12),(25,3),(29,4),(28,11),(24,15)],'ink');a.p([(23,12),(26,5),(28,5),(26,11),(24,13)],'leaflight')
            a.e((9,2,14,7),'ink');a.e((18,2,23,7),'ink');a.dot(11,4,'wood4');a.dot(20,4,'wood4')
            a.p([(9,7),(12,5),(20,5),(23,8),(20,12),(16,15),(11,11)],'ink');a.p([(11,7),(14,6),(19,7),(21,8),(18,11),(16,13),(12,10)],'leafwarm')
            big_eye(a,11,7);big_eye(a,18,7);a.dot(16,11,'ink');a.l([(15,17),(17,18),(15,20)],'leafwarm')
    elif fid in (107,108):
        v=fid==108
        for x in (11,21):
            if v:a.l([(x,20),(x-1,27)],'wood3',2)
            a.l([(x-3,29),(x,27),(x+3,29)],'ink',3);a.l([(x-2,28),(x+1,28)],'slate')
        if not v:
            a.e((7,10,25,27),'ink');a.e((9,12,23,25),'fire2');a.l([(12,23),(15,24),(19,23)],'fire3')
            a.l([(8,15),(4,18),(5,22)],'ink',3);a.l([(24,15),(28,18),(27,22)],'ink',3);a.dot(5,19,'fire1');a.dot(27,19,'fire1')
            a.p([(6,12),(8,18),(13,22),(20,21),(26,15),(25,11),(20,16),(12,16)],'ink');a.p([(8,12),(10,17),(14,20),(19,19),(24,14),(22,15),(12,15)],'white')
            a.e((8,3,23,16),'ink');a.e((10,4,21,14),'fire2');big_eye(a,11,7);big_eye(a,18,7)
            a.p([(14,11),(18,11),(20,13),(17,15),(13,13)],'slate');a.l([(14,11),(17,11)],'silver');a.dot(10,11,'rose4')
        else:
            a.e((10,16,25,24),'ink');a.e((12,17,23,22),'fire1')
            a.l([(16,21),(14,15),(15,8)],'ink',5);a.l([(16,20),(15,15),(16,9)],'fire3',2)
            a.p([(8,14),(5,8),(9,2),(19,1),(25,7),(22,14),(18,16),(17,10),(12,10)],'ink')
            a.l([(9,13),(7,8),(10,4),(18,3),(22,7),(21,12)],'white',3);a.l([(10,4),(16,3),(19,4)],'gold3')
            a.e((10,5,20,12),'fire2');big_eye(a,11,6);big_eye(a,17,6);a.p([(13,10),(17,10),(18,12),(15,13),(13,12)],'slate')
            a.l([(11,18),(7,20),(9,23)],'ink',3);a.l([(23,17),(27,20),(25,23)],'ink',3);a.l([(8,20),(9,21)],'fire2');a.dot(25,20,'fire3')
    elif fid in (109,110):
        v=fid==110
        if v:
            a.p([(22,21),(23,9),(26,2),(30,4),(30,16),(27,23)],'ink');a.l([(24,20),(25,10),(27,5)],'wood4',2);a.l([(27,21),(28,13),(29,6)],'gold2')
            a.l([(26,16),(27,10)],'transparent')
        else:
            a.p([(21,23),(26,16),(30,16),(30,25),(26,28)],'ink');a.p([(24,23),(27,18),(29,18),(28,24),(26,26)],'wood4');a.l([(25,24),(29,21)],'wood1')
        for x in (9,15,23):
            a.l([(x,23),(x-1,28),(x-4,29)],'ink',3);a.l([(x-2,28),(x+1,28)],'wood4'if v else'wood3')
        a.p([(6,19),(10,10),(16,7),(23,11),(27,20),(25,25),(10,25)],'ink');a.p([(8,19),(12,11),(16,9),(21,12),(25,21),(22,23),(10,23)],'wood2')
        bands=((10,14),(14,10),(19,10),(23,14))if v else((11,12),(16,10),(21,13))
        for x,y in bands:a.l([(x,y),(x+2,y+2),(x+1,y+8)],'stone5',2);a.dot(x,y,'white')
        a.p([(4,19),(4,12),(7,10),(9,16),(13,18),(13,23),(8,27),(1,24)],'ink')
        a.p([(5,19),(5,14),(6,13),(7,18),(11,19),(11,22),(7,25),(3,24)],'skin2')
        big_eye(a,5,19);a.e((1,23,3,25),'rose0');a.l([(6,25),(9,24)],'wood1');a.dot(4,23,'rose4')
        if v:a.l([(10,26),(8,29),(5,29)],'wood5',2)
    elif fid in (111,112):
        v=fid==112
        a.l([(17,16),(23,12),(26,7),(24,3)],'ink',3);a.l([(18,15),(23,11),(25,7),(24,4)],'water3')
        if v:a.p([(24,7),(21,3),(25,1),(30,3),(28,7)],'ink');a.p([(24,5),(23,3),(26,2),(28,3),(27,5)],'water4')
        if not v:
            a.p([(14,8),(21,13),(29,19),(26,25),(21,23),(16,28),(10,24),(3,25),(1,20),(8,13)],'ink')
            a.p([(14,10),(20,15),(27,19),(25,23),(21,21),(16,26),(10,22),(4,23),(3,20),(9,15)],'blue3')
            a.l([(4,22),(5,28),(9,29)],'ink',2);a.l([(26,22),(27,27),(23,29)],'ink',2);a.l([(5,25),(6,27),(8,28)],'water4');a.dot(25,27,'water4')
            a.p([(9,18),(14,15),(21,18),(21,22),(16,25),(11,23)],'watergleam')
        else:
            a.l([(13,19),(8,9),(4,12),(2,23),(5,27),(9,24)],'ink',3);a.l([(18,19),(23,7),(28,10),(30,22),(26,27),(22,23)],'ink',3)
            a.l([(12,19),(8,12),(5,13),(3,22),(5,25)],'water4',2);a.l([(19,18),(24,10),(27,12),(28,22),(26,24)],'water3',2)
            a.p([(10,18),(15,13),(21,18),(22,23),(17,27),(11,24)],'ink');a.p([(12,18),(15,15),(19,18),(20,23),(16,25),(12,22)],'watergleam')
            a.l([(5,25),(4,29),(8,29)],'water4',2);a.l([(26,25),(25,28),(22,29)],'water3',2)
        big_eye(a,10,14);big_eye(a,18,14);a.l([(12,21),(15,23),(18,21)],'water0');a.dot(10,20,'rose4');a.dot(20,20,'rose4')
    elif fid==113:
        a.l([(25,19),(29,17),(30,12),(27,10),(25,12),(26,14)],'ink',2);a.dot(28,12,'wood3')
        for x in (8,14,23,26):a.l([(x,22),(x,28),(x-2,29)],'ink',3);a.dot(x,26,'fire0')
        a.p([(7,16),(9,5),(21,5),(25,12),(27,20),(24,25),(10,25)],'ink');a.r((10,7,20,14),'wood1');a.p([(10,14),(19,11),(24,15),(25,21),(22,24),(10,23)],'fire0')
        a.p([(4,16),(4,9),(8,11),(12,10),(16,8),(19,14),(19,23),(12,27),(4,25),(2,20)],'ink')
        a.p([(5,17),(6,12),(9,14),(13,12),(16,11),(17,17),(16,23),(10,25),(5,23)],'wood3')
        big_eye(a,5,16);big_eye(a,13,15);a.e((4,20,14,25),'skin1');a.dot(6,22,'ink');a.dot(11,22,'ink')
        a.l([(3,24),(1,19),(2,17)],'ink',3);a.l([(3,23),(2,19)],'silver')
        a.l([(15,24),(20,20),(20,14),(18,13)],'ink',3);a.l([(16,23),(19,19),(19,15)],'white',2)
    elif fid==114:
        for x,sg in ((13,-1),(18,1)):
            a.p([(x,12),(x+sg*8,4),(x+sg*11,6),(x+sg*10,11),(x+sg*11,16),(x+sg*8,21),(x+sg*5,24),(x,21)],'ink')
            a.p([(x,13),(x+sg*7,6),(x+sg*9,7),(x+sg*8,11),(x+sg*9,16),(x+sg*6,20),(x+sg*4,22),(x,20)],'leaflight')
            for y in (12,16,19):a.l([(x,y),(x+sg*7,y-3)],'pine3')
            a.l([(x+sg*2,10),(x+sg*5,19)],'pine4');a.dot(x+sg*5,9,'white');a.dot(x+sg*7,16,'white')
        for y in (20,24,27):a.l([(14,y-2),(10,y)],'ink');a.l([(17,y-2),(21,y)],'ink')
        a.l([(15,11),(16,20),(15,28)],'ink',5);a.l([(15,13),(16,19),(15,25)],'pine5',2)
        a.l([(13,11),(10,5),(7,2)],'ink');a.l([(10,5),(12,2)],'ink');a.l([(17,11),(21,4),(25,2)],'ink');a.l([(21,4),(20,1)],'ink')
        a.e((11,9,20,16),'ink');a.e((12,10,19,15),'leafwarm');big_eye(a,11,10);big_eye(a,17,10);a.dot(15,15,'pine2')
    elif fid==115:
        for y,z in ((15,0),(19,1),(23,-1),(26,0)):
            a.l([(12,y),(6+z,y-2),(3+z,y+1)],'ink',2);a.dot(6+z,y-2,'fire2')
            a.l([(20,y),(26-z,y-2),(29-z,y+1)],'ink',2);a.dot(26-z,y-2,'fire2')
        a.l([(20,24),(26,18),(28,11),(25,5),(21,5)],'ink',4);a.l([(20,23),(25,17),(26,11),(24,7)],'fire0',2)
        a.e((17,2,24,9),'ink');a.e((18,3,23,8),'fire2');a.e((20,4,22,7),'gold3');a.dot(21,4,'white')
        a.e((11,12,21,28),'ink');a.e((13,14,19,26),'fire0')
        for y in (18,21,24):a.l([(13,y),(19,y)],'fire2')
        a.l([(12,14),(6,10),(2,12),(3,16)],'ink',3);a.l([(20,14),(25,11),(28,13),(27,16)],'ink',3);a.l([(7,10),(4,11)],'fire3');a.dot(26,12,'fire3')
        a.e((9,10,22,18),'ink');a.e((11,11,20,17),'fire1');big_eye(a,10,10);big_eye(a,18,10);a.l([(14,16),(17,16)],'wood5')
    elif fid==116:
        a.l([(26,13),(30,16),(29,23)],'ink',2);a.l([(28,22),(30,24)],'wood2',2)
        for x in (7,13,23,27):a.l([(x,21),(x,29)],'ink',3);a.l([(x,22),(x,26)],'stone5')
        a.p([(4,12),(7,7),(23,7),(28,12),(28,24),(6,24)],'ink');a.r((7,9,24,22),'stone5');a.l([(9,9),(21,9)],'white',2)
        a.p([(7,20),(9,29),(12,27),(15,29),(17,25),(19,27),(20,20)],'ink');a.p([(9,21),(10,26),(13,24),(15,27),(18,23)],'white')
        a.l([(7,13),(2,11),(1,5),(4,8)],'ink',3);a.l([(6,12),(3,10),(2,7)],'wood4')
        a.l([(20,12),(26,10),(28,5),(28,9),(25,13)],'ink',3);a.l([(21,12),(25,10),(27,7)],'wood4')
        a.r((5,11,22,22),'ink');a.r((7,12,20,21),'stone5');big_eye(a,7,14);big_eye(a,17,14)
        a.r((6,19,21,23),'stone2');a.dot(9,20,'ink');a.dot(18,20,'ink');a.l([(10,23),(16,23)],'stone4')
    elif fid==117:
        a.l([(15,14),(16,21),(14,25),(17,30)],'ink',3);a.l([(15,16),(16,21),(15,25),(17,28)],'wood3')
        for x,y in ((16,19),(15,23),(16,27)):a.l([(x-1,y),(x+1,y)],'gold3')
        for y,z in ((12,-2),(19,0)):
            for x,sg in ((12,-1),(19,1)):
                a.p([(x,y),(x+sg*6,y-5+z),(x+sg*10,y-5+z),(x+sg*10,y-1+z),(x+sg*4,y+1)],'ink')
                a.p([(x+sg,y),(x+sg*7,y-4+z),(x+sg*9,y-4+z),(x+sg*9,y-2+z),(x+sg*4,y)],'silver')
                a.l([(x+sg*6,y-3+z),(x+sg*8,y-3+z)],'white');a.dot(x+sg*5,y-1,'wood4')
        a.l([(14,10),(16,18)],'ink',5);a.l([(14,12),(16,16)],'gold2')
        a.e((9,7,15,15),'ink');a.e((10,8,14,13),'watergleam');a.e((17,6,23,14),'ink');a.e((18,7,22,12),'water4')
        a.r((11,9,12,12),'ink');a.dot(11,9,'white');a.r((19,8,20,11),'ink');a.dot(19,8,'white');a.l([(15,14),(18,14)],'wood4')
    elif fid==118:
        for x,y,sg in ((8,18,-1),(24,16,1),(9,25,-1),(24,24,1)):
            a.p([(x,y),(x+sg*5,y-2),(x+sg*6,y+3),(x+sg,y+4)],'ink');a.p([(x,y+1),(x+sg*4,y),(x+sg*4,y+2),(x+sg,y+3)],'water4')
        a.l([(25,16),(29,13)],'ink',2);a.dot(28,14,'water4')
        a.e((4,11,28,27),'ink');a.e((5,12,27,25),'watergleam');a.e((7,13,25,23),'teal1');a.l([(10,16),(15,14),(21,15),(23,18)],'water3');a.l([(9,21),(14,23),(22,21)],'water0')
        a.l([(14,22),(10,18),(8,12)],'ink',5);a.l([(13,21),(10,17),(9,12)],'water4',3)
        a.e((3,6,14,16),'ink');a.e((5,7,13,14),'water4');big_eye(a,5,7);big_eye(a,10,8)
        a.l([(5,12),(2,15),(1,17)],'ink',3);a.l([(5,12),(3,15),(2,16)],'water3');a.dot(1,17,'water0');a.l([(6,14),(9,15)],'water0')
    elif fid==119:
        a.l([(25,28),(29,25),(26,21),(17,24),(10,23),(6,18),(11,13),(20,14),(24,10),(20,6)],'ink',5)
        a.l([(25,28),(27,25),(25,23),(17,25),(10,23),(8,18),(12,15),(20,15),(22,11),(20,7)],'pine4',3)
        for x,y,lean in ((10,22,-1),(12,14,1),(22,10,0)):
            a.p([(x,y+3),(x-4,y),(x-3+lean,y-5),(x+1,y-3),(x+4,y),(x+2,y+3)],'ink')
            a.p([(x,y+1),(x-2,y-1),(x-2+lean,y-3),(x,y-2),(x+2,y),(x+1,y+1)],'leaflight');a.l([(x,y-2),(x,y)],'pine3')
        a.p([(10,5),(15,2),(22,3),(25,7),(21,11),(13,11),(8,8)],'ink');a.p([(11,5),(16,4),(21,5),(23,7),(20,9),(13,9),(10,7)],'pine5')
        big_eye(a,11,5);big_eye(a,19,5);a.l([(13,10),(18,10)],'wood5');a.dot(10,8,'rose4')
    else:
        a.e((24,20,30,26),'ink');a.e((25,21,29,25),'white')
        for x in (11,22):a.l([(x,24),(x-1,28),(x-5,29)],'ink',3);a.l([(x-2,28),(x,27)],'silver')
        a.e((7,15,27,28),'ink');a.e((9,16,25,26),'silver');a.l([(12,22),(15,24),(18,23)],'white',2)
        a.l([(12,17),(8,12),(7,7)],'ink',3);a.e((2,2,12,12),'ink');a.e((4,4,10,10),'wood4');a.l([(5,4),(8,4),(10,6)],'white');a.dot(7,7,'gold1')
        a.l([(20,16),(24,12),(25,8)],'ink',3);a.e((20,4,30,14),'ink');a.e((22,6,28,12),'gold2');a.l([(23,6),(26,6),(28,8)],'white');a.dot(25,9,'wood3')
        a.e((5,13,23,25),'ink');a.e((7,14,21,23),'stone5');big_eye(a,8,16);big_eye(a,17,16)
        a.p([(13,20),(16,20),(15,22)],'rose4');a.l([(11,23),(14,24),(17,23)],'white');a.dot(7,20,'rose5')
    return a.im

def mask(im):return Image.frombytes('L',im.size,bytes(255 if n else 0 for n in im.tobytes()))
def paste(target,im,xy):target.paste(im.convert(target.mode),xy,mask(im))
def normalized_mask(im):
    m=mask(im);b=m.getbbox();return m.crop(b).size,m.crop(b).tobytes()
def save_image(im,path):
    if im.mode=='P':im.save(path,transparency=0,optimize=False)
    else:im.save(path,optimize=False)
def validate_pixels(fields,abilities,portraits):
    assert tuple(f['id']for f in BRIEFS)==FORM_IDS
    allimgs=[im for tensor in(fields,abilities)for row in tensor for direction in row for im in direction]+portraits
    for im in allimgs:assert im.mode=='P'and im.getpalette()==PAL and 0 in im.tobytes()and max(im.tobytes())<97
    for i,row in enumerate(fields):
        for d in range(4):
            walk=row[d];cast=abilities[i][d];group=walk+cast
            assert len({im.tobytes()for im in group})==7,(NAMES[i],DIRECTIONS[d],'seven unique poses')
            assert len({normalized_mask(im)for im in walk})==4,(NAMES[i],DIRECTIONS[d],'four articulated walks')
            assert len({normalized_mask(im)for im in cast})==3,(NAMES[i],DIRECTIONS[d],'three articulated casts')
            for im in group:
                assert im.size==(16,16)
                assert all(im.getpixel((x,y))==0 for x in range(16)for y in(0,15)),(NAMES[i],'vertical bounds')
                assert all(im.getpixel((x,y))==0 for x in(0,15)for y in range(16)),(NAMES[i],'horizontal bounds')
                assert 35<=sum(bool(n)for n in im.tobytes())<=210,(NAMES[i],'occupancy')
        assert len({mask(im[0]).tobytes()for im in row})==4,(NAMES[i],'four directional silhouettes')
        assert all(row[3][f].tobytes()==row[2][f].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes()for f in range(4))
        assert portraits[i].size==(32,32)and portraits[i].tobytes()!=row[0][0].resize((32,32),Image.Resampling.NEAREST).tobytes()
    assert len({normalized_mask(row[0][0])for row in fields})==16
    assert len({normalized_mask(im)for im in portraits})==16
    pair_differences=[]
    for i in range(0,8,2):
        changes=[sum(bool(a)!=bool(b)for a,b in zip(fields[i][d][0].tobytes(),fields[i+1][d][0].tobytes()))for d in range(4)]
        assert min(changes)>=8,(NAMES[i],'evolution morphology')
        pair_differences.append({'forms':[FORM_IDS[i],FORM_IDS[i+1]],'silhouette_changed_pixels_by_direction':changes})
    return {'images':464,'field_dimensions':[16,4,4,256],'ability_dimensions':[16,4,3,256],'portrait_dimensions':[16,1024],
      'actor_palette_entries':97,'palette_indices':sorted({n for im in allimgs for n in im.tobytes()}),'transparent_zero':True,
      'transparent_outer_field_boundary':True,'unique_direction_masks_per_form':4,'articulated_walk_masks_per_direction':4,
      'articulated_cast_masks_per_direction':3,'unique_front_silhouettes':16,'independently_composed_native_portraits':True,'evolution_morphology':pair_differences}
SCENE_SOURCES=(('OLD GRASS','assets/southern_region/frondshore_commons.png',(276,262,300,286)),
 ('OLD CREAM','assets/southern_region/sunlace_anchorage.png',(40,96,64,120)),
 ('OLD TEAL','assets/southern_region/sunlace_anchorage.png',(32,287,56,311)),
 ('RETURN GRASS','assets/return_region/greenwake_common.png',(208,192,232,216)),
 ('RETURN CREAM','assets/return_region/sunlace_shade_terraces.png',(264,112,288,136)),
 ('RETURN TEAL','assets/return_region/overflow_gardens.png',(152,104,176,128)))
def make_previews(fields,abilities,portraits):
    roster=Image.new('RGB',(640,400),RGB[P['dirt4']]);rd=ImageDraw.Draw(roster)
    rd.text((4,3),'SHARED HORIZONS / ORIGINAL NATIVE PIXELS / ART REVIEW',fill=RGB[1])
    sheet=Image.new('RGB',(384,16*88+22),RGB[P['dirt4']]);sd=ImageDraw.Draw(sheet)
    sd.text((4,3),'DOWN UP LEFT RIGHT / WALK x4 | ANTICIPATE RELEASE SETTLE',fill=RGB[1])
    patches=[];sources=[]
    for label,rel,box in SCENE_SOURCES:
        with Image.open(ROOT/rel)as im:patches.append(im.convert('RGB').crop(box))
        sources.append({'name':label,'path':rel,'crop':list(box),'sha256':hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()})
    for i,(fid,key,name)in enumerate(zip(FORM_IDS,KEYS,NAMES)):
        x=(i%4)*160;y=20+(i//4)*95
        rd.text((x+3,y),str(fid)+' '+name,fill=RGB[1]);paste(roster,portraits[i],(x+3,y+17))
        for d in range(4):paste(roster,fields[i][d][0],(x+43+d*27,y+21))
        rd.text((x+42,y+40),'D   U   L   R',fill=RGB[1])
        for p in range(3):paste(roster,abilities[i][0][p],(x+45+p*30,y+60))
        w=Art(64,64,'transparent').im;c=Art(48,64,'transparent').im
        for d in range(4):
            for f in range(4):w.paste(fields[i][d][f],(f*16,d*16))
            for p in range(3):c.paste(abilities[i][d][p],(p*16,d*16))
        save_image(w,OUT/f'{key}_walk.png');save_image(c,OUT/f'{key}_ability.png');save_image(portraits[i],OUT/f'{key}_portrait.png')
        sy=22+i*88;sd.text((4,sy),str(fid)+' '+name,fill=RGB[1]);paste(sheet,portraits[i],(4,sy+19))
        for d in range(4):
            sd.text((42,sy+18+d*16),DIRECTIONS[d][0].upper(),fill=RGB[1])
            for n,im in enumerate(fields[i][d]+abilities[i][d]):paste(sheet,im,(66+n*42,sy+18+d*16))
        native=Image.new('RGB',(240,160),RGB[P['deep']]);nd=ImageDraw.Draw(native);nd.text((3,2),str(fid)+' '+name+' / ART',fill=RGB[P['white']]);paste(native,portraits[i],(204,22))
        for bg,y0 in(('deep',20),('dirt4',92)):
            nd.rectangle((0,y0,200,y0+64),fill=RGB[P[bg]])
            for d in range(4):
                for n,im in enumerate(fields[i][d]+abilities[i][d]):paste(native,im,(2+n*28,y0+d*16))
        save_image(native,OUT/f'{key}_native.png');save_image(native.resize((720,480),Image.Resampling.NEAREST),OUT/f'{key}_3x.png')
        terrain=Image.new('RGB',(6*168,116),RGB[P['deep']]);td=ImageDraw.Draw(terrain)
        for b,(label,_,_)in enumerate(SCENE_SOURCES):
            td.text((b*168+3,2),label+' / '+str(fid),fill=RGB[P['white']])
            for d in range(4):
                for f,im in enumerate(fields[i][d]+abilities[i][d]):tile=patches[b].copy();paste(tile,im,(4,4));terrain.paste(tile,(b*168+f*24,18+d*24))
        save_image(terrain,OUT/f'{key}_terrain_native.png')
        walking=[];motion=[]
        for f in range(4):
            tile=Image.new('RGB',(64,16),RGB[P['dirt4']])
            for d in range(4):paste(tile,fields[i][d][f],(16*d,0))
            walking.append(tile)
        walking[0].save(OUT/f'{key}_walk_native.gif',save_all=True,append_images=walking[1:],duration=[n*17 for n in WALK_TICKS[i]],loop=0,optimize=False,disposal=2)
        for mode,frame in [('walk',n)for n in range(4)]+[('cast',n)for n in range(3)]+[('walk',n)for n in range(4)]:
            tile=Image.new('RGB',(192,48),RGB[P['dirt4']])
            for d in range(4):paste(tile,(fields if mode=='walk'else abilities)[i][d][frame].resize((48,48),Image.Resampling.NEAREST),(48*d,0))
            motion.append(tile)
        motion[0].save(OUT/f'{key}_motion.gif',save_all=True,append_images=motion[1:],duration=[n*17 for n in WALK_TICKS[i]]+[140,260,170]+[n*17 for n in WALK_TICKS[i]],loop=0,optimize=False,disposal=2)
    for stem,im in(('roster',roster),('all_frames',sheet)):
        save_image(im,OUT/f'{stem}_native.png');save_image(im.resize((im.width*2,im.height*2),Image.Resampling.NEAREST),OUT/f'{stem}_2x.png')
    lineage=Image.new('RGB',(400,4*82+22),RGB[P['dirt4']]);ld=ImageDraw.Draw(lineage);ld.text((4,3),'EVOLUTION / NEW STANCE, ANATOMY AND NEGATIVE SPACE',fill=RGB[1])
    for n in range(4):
        i=n*2;y=24+n*82;ld.text((4,y),NAMES[i]+' > '+NAMES[i+1],fill=RGB[1]);paste(lineage,portraits[i],(4,y+16));paste(lineage,portraits[i+1],(43,y+16))
        for d in range(4):paste(lineage,fields[i][d][0],(100+d*28,y+18));paste(lineage,fields[i+1][d][0],(100+d*28,y+42))
    save_image(lineage,OUT/'lineage_native.png');save_image(lineage.resize((800,lineage.height*2),Image.Resampling.NEAREST),OUT/'lineage_2x.png')
    return sources,patches

def terrain_metrics(fields,abilities,patches):
    rows=[]
    for i,fid in enumerate(FORM_IDS):
        for b,patch in enumerate(patches):
            fractions=[];bounds=[]
            for d in range(4):
                for im in fields[i][d]+abilities[i][d]:
                    pixels=im.tobytes();opaque=[];boundary=[]
                    for y in range(16):
                        for x in range(16):
                            c=pixels[y*16+x]
                            if not c:continue
                            fg=RGB[c];bg=patch.getpixel((x+4,y+4));diff=sum((fg[k]-bg[k])**2 for k in range(3));visible=diff>=48**2
                            opaque.append(visible)
                            if any(nx<0 or ny<0 or nx>=16 or ny>=16 or not pixels[ny*16+nx]for nx,ny in((x-1,y),(x+1,y),(x,y-1),(x,y+1))):boundary.append(visible)
                    fractions.append(sum(opaque)/len(opaque));bounds.append(sum(boundary)/len(boundary))
            rows.append({'form':fid,'scene':SCENE_SOURCES[b][0],'minimum_opaque_fraction':round(min(fractions),6),'minimum_boundary_fraction':round(min(bounds),6)})
    return {'samples':16*4*7*6,'metric':'Native RGB555 Euclidean distance >=48; heuristic readability only, not emulator evidence','rows':rows,'minimum_opaque_fraction':min(r['minimum_opaque_fraction']for r in rows),'minimum_boundary_fraction':min(r['minimum_boundary_fraction']for r in rows)}
def silhouette_comparison(fields):
    # Frozen accepted104 contact sheet is read only. No old pixels enter authoring.
    prior=json.loads((ROOT/'assets/return_creatures/manifest.json').read_text())
    oldids=prior['silhouette_comparison']['released_form_ids']+prior['form_ids'];assert len(oldids)==104 and len(set(oldids))==104
    rel='assets/return_creatures/released104_silhouettes_native.png'
    with Image.open(ROOT/rel)as source:source=source.convert('RGB')
    old=[];current=[mask(row[0][0]).tobytes()for row in fields]
    sheet=Image.new('RGB',(560,24+18*42),RGB[P['white']]);dr=ImageDraw.Draw(sheet)
    dr.text((4,3),'120 NATIVE SILHOUETTES / ACCEPTED104 + HORIZONS16 / ART ONLY',fill=RGB[1])
    for i,fid in enumerate(oldids+list(FORM_IDS)):
        x=i%7*80;y=24+i//7*42;dr.text((x+4,y),str(fid),fill=RGB[1])
        for d in range(4):
            if i<104:
                xx=i%7*80+4+d*18;yy=24+i//7*42+13;tile=source.crop((xx,yy,xx+16,yy+16))
                data=bytes(255 if p==RGB[1]else 0 for p in getattr(tile,'get_flattened_data',tile.getdata)());m=Image.frombytes('L',(16,16),data)
                if d==0:old.append(data)
            else:m=mask(fields[i-104][d][0])
            sheet.paste(Image.new('RGB',(16,16),RGB[1]),(x+4+d*18,y+13),m)
    assert not set(current).intersection(old),'An accepted silhouette was reused'
    nearest=[]
    for i,ma in enumerate(current):
        pool=list(zip(oldids,old))+[(FORM_IDS[j],m)for j,m in enumerate(current)if j!=i]
        delta,fid=min((sum(a!=b for a,b in zip(ma,m)),fid)for fid,m in pool)
        nearest.append({'form_id':FORM_IDS[i],'nearest_form_id':fid,'different_front_mask_pixels':delta})
    save_image(sheet,OUT/'released120_silhouettes_native.png');save_image(sheet.resize((1120,sheet.height*2),Image.Resampling.NEAREST),OUT/'released120_silhouettes_2x.png')
    return {'current_unique_front_masks':16,'released_form_ids':oldids,'cross_release_front_mask_matches':0,'nearest_front_masks':nearest,
      'source':rel,'source_sha256':hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()}
def output_hashes():
    files=sorted(p for p in OUT.iterdir()if p.is_file()and p.suffix in('.png','.gif','.json','.txt')and p.name!='validation.json')
    files+=sorted((ROOT/'src/horizons_creature_art_data').glob('*.inc'))+[ROOT/'src/horizons_creature_art.c',ROOT/'src/horizons_creature_art.h']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}
def generate():
    OUT.mkdir(exist_ok=True)
    fields=[[[field(fid,d,f)for f in range(4)]for d in DIRECTIONS]for fid in FORM_IDS]
    abilities=[[[field(fid,d,p,p)for p in range(3)]for d in DIRECTIONS]for fid in FORM_IDS];portraits=[portrait(fid)for fid in FORM_IDS]
    validation=validate_pixels(fields,abilities,portraits)
    spec=importlib.util.spec_from_file_location('horizons_creature_codegen',OUT/'codegen.py');cg=importlib.util.module_from_spec(spec);spec.loader.exec_module(cg)
    chunks=cg.emit_code(ROOT,FORM_IDS,NAMES,fields,abilities,portraits);sources,patches=make_previews(fields,abilities,portraits);terrain=terrain_metrics(fields,abilities,patches)
    (OUT/'terrain_readability.json').write_text(json.dumps(terrain,indent=2)+'\n')
    manifest={'schema_version':1,'design_version':'SHARED_HORIZONS','design_manifest_sha256':hashlib.sha256(PLAN.read_bytes()).hexdigest(),
      'generator':'assets/generate_horizons_creatures.py','form_ids':list(FORM_IDS),'names':list(NAMES),'directions':list(DIRECTIONS),
      'status':'ART ONLY: these are authored sprite sheets and art-review composites, not emulator captures, obtainability proof, live-rendering proof or gameplay acceptance.',
      'rights':'Original code-native pixel geometry, authored from silhouettes and anatomy in the Shared Horizons brief. No traced, downloaded, image-generated or third-party creature pixels.',
      'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'codegen_sha256':hashlib.sha256((OUT/'codegen.py').read_bytes()).hexdigest(),
      'palette_sha256':hashlib.sha256(json.dumps(COLORS).encode()).hexdigest(),'data_bytes':cg.DATA_BYTES,'runtime_data_bytes':0,'runtime_bss_bytes':0,'persistent_obj_allocation_bytes':0,
      'rom_budget_bytes':cg.ROM_BUDGET_BYTES,'include_bytes':chunks,'max_include_bytes':max(chunks),'scene_review_sources':sources,
      'anchor':[8,8],'shadow_anchor':[8,13],'shadow_in_sprite':False,'idle_frame':0,'walk_ticks_by_form':dict(zip(map(str,FORM_IDS),WALK_TICKS)),
      'ability_poses':['anticipation','release','settle'],'recovery':'Return to walking after settle; no fourth cast pose. Effect pixels are owned by the separate effect renderer.',
      'briefs':BRIEFS,'validation':validation,'silhouette_comparison':silhouette_comparison(fields),
      'terrain_visibility_minimum_opaque':terrain['minimum_opaque_fraction'],'terrain_visibility_minimum_boundary':terrain['minimum_boundary_fraction']}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'CREDITS.txt').write_text(manifest['rights']+'\n464 original indexed images. Fields leave a transparent one-pixel rim. Portraits are separately composed at 32px.\nShared RGB555 palette unchanged. Background crops are read only for art review. These previews are not emulator evidence.\n')
    return manifest

def verify(manifest):
    before=output_hashes();generate();assert before==output_hashes(),'Nondeterministic regeneration'
    report={'deterministic_regeneration':True,'pixel_validation':manifest['validation'],'output_sha256':output_hashes()}
    with tempfile.TemporaryDirectory(prefix='horizons-art-')as td:
        td=Path(td);sys.path.insert(0,str(ROOT/'tools'));from arm_toolchain import resolve_arm_tools
        tc=resolve_arm_tools('gcc','size','nm','objdump',root=ROOT);obj=td/'horizons_creature_art.o'
        subprocess.run([tc['gcc'],'-std=c99','-mcpu=arm7tdmi','-mthumb','-O2','-ffreestanding','-fno-builtin','-fstack-usage','-Wall','-Wextra','-Werror','-c',str(ROOT/'src/horizons_creature_art.c'),'-o',str(obj)],check=True,capture_output=True)
        sections=list(map(int,subprocess.check_output([tc['size'],str(obj)],text=True).splitlines()[-1].split()[:3]));assert sections[1:]==[0,0]and sections[0]<=manifest['rom_budget_bytes']
        assert not subprocess.check_output([tc['nm'],'-u',str(obj)],text=True).strip()
        segments=subprocess.check_output([tc['objdump'],'-h',str(obj)],text=True).lower();assert 'iwram'not in segments and'ewram'not in segments
        stack=[int(line.split('\t')[1])for p in td.glob('*.su')for line in p.read_text().splitlines()];assert stack and max(stack)<=24
        report.update({'arm_compile':'passed','arm_rom_object_bytes':sections[0],'arm_data_bytes':sections[1],'arm_bss_bytes':sections[2],'max_arm_stack_bytes':max(stack),'max_include_bytes':manifest['max_include_bytes']})
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');return {k:v for k,v in report.items()if k not in('output_sha256','pixel_validation')}
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--verify',action='store_true');args=p.parse_args();m=generate()
    print(json.dumps(verify(m)if args.verify else{'generated_forms':FORM_IDS,'data_bytes':m['data_bytes'],'max_include_bytes':m['max_include_bytes']},indent=2))
if __name__=='__main__':main()
