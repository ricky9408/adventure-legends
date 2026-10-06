#!/usr/bin/env python3
"""Original Magma companion pixels. Native 16px anatomy and independent 32px portraits.
Art-only immutable ROM module. Never changes game palette, catalog, UI, or gameplay.
No downloaded, traced or generated raster references; pixel geometry is authored here.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, json, sys, subprocess, shutil, tempfile
from PIL import Image, ImageDraw
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/magma_creatures'
spec=importlib.util.spec_from_file_location('magma_palette',ROOT/'assets/magma_palette.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
Art,P,PAL,RGB=base.Art,base.P,base.PAL,base.rgb
BRIEFS=json.loads((ROOT/'assets/magma_creature_briefs.json').read_text())
FORM_IDS=tuple(f['id'] for f in BRIEFS);NAMES=tuple(f['name'] for f in BRIEFS);KEYS=tuple(n.lower() for n in NAMES)
DIRECTIONS=('down','up','left','right')
# Per-form art timing recommendations in60Hz updates; integration must own playback.
WALK_TICKS=((12,8,10,12),(10,12,8,12),(14,12,10,14),
 (6,6,7,6),(10,12,8,10),(11,9,11,9),(5,6,5,8),(6,5,6,7),(8,5,6,9),
 (10,9,12,9),(12,10,10,12),(9,12,9,10),(7,8,7,8),(10,8,10,12),(9,9,12,10),
 (6,5,6,8),(8,5,7,9),(12,10,12,8),(12,11,10,13),(11,12,10,13),(8,7,8,7),
 (9,8,9,8),(10,8,10,12),(12,10,10,14))
class Pen:
    def __init__(self,a,dy=0):self.a,self.dy=a,dy
    def p(self,pts,c):self.a.p([(x,y+self.dy) for x,y in pts],c)
    def l(self,pts,c,w=1):self.a.l([(x,y+self.dy) for x,y in pts],c,w)
    def e(self,b,c):self.a.e((b[0],b[1]+self.dy,b[2],b[3]+self.dy),c)
    def r(self,b,c):self.a.r((b[0],b[1]+self.dy,b[2],b[3]+self.dy),c)
    def dot(self,x,y,c):self.a.dot(x,y+self.dy,c)
def eye(q,x,y):
    q.r((x,y,x+1,y+2),'white');q.dot(x,y+1,'ink');q.dot(x,y+2,'ink')
def face(q,d,box,color='skin2'):
    x,y,X,Y=box;q.e(box,'ink');q.e((x+1,y+1,X-1,Y-1),color)
    if d=='down':
        eye(q,x+1,y+1);eye(q,X-2,y+1);q.l([(x+3,Y-1),(X-3,Y-1)],'rose0')
    elif d in ('left','right'):eye(q,x+1,y+1);q.dot(x,Y-1,'ink');q.dot(x+3,Y-1,'rose4')
    else:q.l([(x+2,y+1),(X-2,y+1)],'white');q.dot(X-2,Y-1,'stone3')
def beat(f,cast=None):
    return (((0,0,-1,0)[f],(0,-1,0,1)[f]) if cast is None else ((1,0)[cast],(-1,1)[cast]))
def leg(a,x,y,s,color='skin2',wide=False):
    a.l([(x,y),(x+s,y+2),(x+s+1,y+2)],'ink',2 if wide else 1);a.dot(x+s,y+1,color)
def finish(a,d):return a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT) if d=='right' else a.im

def snail(v,d,f,cast):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);side=d in ('left','right');up=d=='up'
    if cast is None and v==2:dy,s=(0,0,0,-1)[f],(0,-1,1,0)[f]
    q=Pen(a,dy) # Shell rocks after the foot/head; it never bobs the whole animal.
    # One living pale foot, four independently articulated ripple contours.
    a.p([(1,11),(3,9),(10,10),(14,12),(13,13),(2,13),(0,12)],'ink');a.r((2+s,13,4+s,14),'ink');a.r((9-s,13,11-s,14),'ink')
    a.p([(2,11),(4,10),(10,11),(13,12),(12,13),(9,12),(5,13),(2,13)],'skin2');a.dot(3+s,14,'skin1')
    if v==0:
        q.p([(5,9),(5,5),(8,3),(12,3),(14,5),(13,8),(10,9),(8,8),(9,6),(11,6),(10,5),(8,5),(7,7),(8,10)],'ink')
        q.l([(6,7),(7,5),(9,4),(12,4),(13,5),(12,7),(10,8)],'fire2',2);q.dot(10,4,'gold4')
    elif v==1:
        q.p([(5,10),(3,6),(4,2),(8,1),(12,3),(14,7),(12,10),(9,10),(8,8),(10,8),(11,6),(8,4),(6,5),(6,8),(7,10)],'ink')
        q.l([(4,5),(5,3),(8,2),(11,4),(13,7),(11,9),(9,9)],'fire2');q.dot(7,3,'gold4')
        q.p([(6,6),(8,4),(10,7)],'transparent')
    else:
        # Crown fan is a connected upper rim and three ribs, with two true windows.
        q.p([(1,4),(3,2),(7,1),(12,2),(14,4),(13,6),(11,5),(4,5),(2,6)],'ink');q.l([(2,4),(4,3),(8,2),(12,3),(13,4)],'fire3')
        for x in (3,7,12):q.l([(x,5),(x+(1 if x<7 else -1),9)],'ink',2);q.l([(x,5),(x+(1 if x<7 else -1),8)],'fire1')
    q=Pen(a,0)
    y=8 if up else 9
    if side:face(q,d,(0,y,6,13),'skin2');q.l([(2,y),(2,y-2),(3,y-2)],'ink');q.dot(2,y-2,'gold4')
    else:
        face(q,d,(4,y,11,13),'skin2')
        for x in (5,10):q.l([(x,y),(x+s,y-2)],'ink');q.dot(x+s,y-2,'gold3')
    if cast is not None:q.l([(3,13),(7,12-cast),(11,13)],'gold4');q.dot(14,12-cast,'skin2')
    return finish(a,d)

def goat(v,d,f,cast):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);side=d in ('left','right');up=d=='up'
    if cast is None and v==0:dy=(0,0,1,0)[f] # Kid's head dips after paired hoof plant.
    if v==1:dy=0 # Bracer keeps its head level through a planted shuffle.
    q=Pen(a,dy)
    if v==0:
        for x,k in ((4,s),(10,-s)):leg(a,x,11,k,'stone5',True)
        q.e((3,7,12,12),'ink');q.e((4,8,11,11),'wood4');q.p([(8,7),(11,8),(10,10),(8,9)],'stone4')
        hx=1 if side else 4;hy=5 if not up else 4
        q.l([(hx+1,hy+1),(hx+1,hy-2)],'ink',2);q.l([(hx+5,hy+1),(hx+5,hy-2)],'ink',2);q.dot(hx+1,hy-2,'stone5');q.dot(hx+5,hy-2,'stone5')
        face(q,d,(hx,hy,hx+7,hy+6),'wood5')
    elif v==1:
        for x,k in ((3,s),(12,-s)):leg(a,x,10 if cast is None and f==2 else 11,k,'stone5',True)
        q.e((2,7,13,12),'ink');q.e((3,8,12,11),'wood3');q.e((6,7,10,10),'stone3')
        for pts in ([(5,6),(2,3),(1,5),(1,8),(4,9)],[(10,6),(13,3),(14,5),(14,8),(11,9)]):
            q.l(pts,'ink',3);q.l(pts,'stone5')
        face(q,d,(2 if side else 4,6 if not up else 5,9 if side else 11,12),'wood5')
    else:
        for x,k in ((4,s),(11,-s)):
            a.l([(x,9+dy),(x+k,12),(x+k+1,14)],'ink',2);a.l([(x+k,12),(x+k+1,13)],'stone5')
        q.p([(6,7),(10,7),(11,10),(9,11),(9,13),(6,13),(5,10)],'ink');q.l([(7,9),(8,11)],'wood4',2)
        # Buttress horns remain joined above brow while two clear arches survive.
        q.l([(3,8),(1,5),(3,2),(7,1),(12,2),(14,5),(12,8)],'ink',2)
        q.l([(3,7),(2,5),(4,3),(7,2),(11,3),(13,5),(12,7)],'stone5')
        q.l([(7,2),(7,6)],'ink');q.dot(7,3,'gold3')
        face(q,d,(3 if side else 4,6 if not up else 5,10 if side else 11,10),'wood5')
        q.l([(5,10),(7,12),(9,10)],'stone4')
    if cast is not None:q.dot(2,13,'gold4');q.dot(13,13-cast,'gold4')
    return finish(a,d)

def pika(v,d,f,cast):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);q=Pen(a,dy);side=d in ('left','right');up=d=='up'
    if v==2:
        # Pinecone is carried on a tail around the outside, not worn as a hat.
        q.l([(10,11),(14,9),(14,4),(11,2)],'ink',2);q.l([(11,10),(13,8),(13,4)],'wood4')
        if cast==1:q.p([(7,3),(5,1),(8,2),(10,1),(11,2),(14,1),(12,4)],'ink');q.l([(7,2),(10,3),(13,2)],'wood4')
        else:q.p([(8,1),(10,1),(12,2),(12,4),(10,5),(8,4),(7,2)],'ink');q.l([(9,1),(10,2),(9,3),(11,4)],'wood4')
        for x,k in ((5,s),(10,-s)):a.l([(x,10+dy),(x+k,12),(x+k-1,14),(x+k+1,14)],'ink',2);a.dot(x+k,13,'skin2')
        q.e((6,7,9,11),'ink');q.l([(7,8),(8,10)],'wood3',2)
        q.l([(6,8),(3,10+s),(2,8+s)],'ink');q.l([(9,8),(12,10-s),(13,8-s)],'ink')
        hx=2 if side else 4;hy=4
    else:
        for x,k in ((4,s),(11,-s)):leg(a,x,11,k,'skin2',True)
        if v==0:q.r((11,7+s,14,10+s),'ink');q.r((12,8+s,13,9+s),'pine5')
        else:
            for x in (4,10):q.p([(x-2,8),(x-2,4),(x,3),(x+1,5),(x+3,7),(x+2,9)],'ink');q.l([(x-1,7),(x-1,5),(x,4),(x+1,7)],'pine5')
        q.e((3 if v==0 else 1,7,12 if v==0 else 14,12),'ink');q.e((4 if v==0 else 2,8,11 if v==0 else 13,11),'wood3')
        hx=1 if side else 4;hy=6 if not up else 5
    for x in (hx,hx+5):q.e((x,hy-2,x+3,hy+1),'ink');q.dot(x+1,hy-1,'skin2')
    face(q,d,(hx,hy,hx+7,hy+5),'wood5')
    if v==1:
        q.p([(hx+1,hy+4),(hx+3,hy+7),(hx+4,hy+5),(hx+6,hy+7),(hx+7,hy+4)],'ink');q.l([(hx+2,hy+4),(hx+3,hy+6)],'wood4');q.l([(hx+5,hy+4),(hx+6,hy+6)],'wood4')
    elif v==0:
        q.l([(hx+1,hy+3),(max(0,hx-2),hy+1+s)],'pine4');q.l([(hx+6,hy+3),(min(15,hx+10),hy+1-s)],'pine5')
    if cast is not None:q.dot(hx+3,hy+5,'mint')
    return finish(a,d)

def sponge(v,d,f,cast):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);q=Pen(a,dy);side=d in ('left','right');up=d=='up'
    if v==0:
        for x,k in ((4,s),(8,-s),(11,s)):a.e((x-1,11+k,x+1,13+k),'ink');a.dot(x,12+k,'water4')
        q.p([(3,10),(5,6),(6,2),(9,1),(11,3),(9,5),(10,7),(12,9),(13,12),(3,12)],'ink')
        q.p([(4,10),(6,7),(7,3),(9,2),(10,3),(8,5),(9,8),(11,10)],'water4');q.l([(7,3),(9,3)],'water1')
        face(q,d,(2 if side else 4,8 if not up else 7,9 if side else 11,12),'water4')
        q.dot(10,9,'water1');q.dot(6,6,'white')
    elif v==1:
        a.e((2+s,11,7+s,14),'ink');a.e((8-s,11,13-s,14),'ink');a.e((3+s,12,6+s,13),'water4');a.e((9-s,12,12-s,13),'water3')
        q.l([(7,12),(10,9),(10,6),(8,4)],'ink',4);q.l([(7,11),(9,9),(9,6),(8,5)],'water4',2)
        q.p([(3,5),(5,3),(6,1),(10,1),(11,3),(13,5),(12,7),(4,7)],'ink');q.p([(4,5),(6,4),(7,2),(9,2),(10,4),(12,5)],'water4')
        face(q,d,(3 if side else 4,5 if not up else 4,10 if side else 11,9),'blue3');q.l([(3,5),(12,5)],'white');q.dot(8,11,'water1')
    else:
        for x,k in ((2,s),(5,-s),(10,s),(13,-s)):a.l([(x,11+dy),(x+k,13)],'ink');a.dot(x+k,12,'water4')
        q.p([(1,8),(3,7),(3,3),(5,2),(6,7),(9,7),(11,2),(13,3),(13,8),(14,10),(13,12),(2,12),(0,10)],'ink')
        q.p([(2,8),(4,8),(4,4),(5,4),(5,9),(10,9),(11,4),(12,4),(12,9),(13,10),(11,11),(3,11)],'water4');q.l([(6,10),(9,10)],'water1')
        face(q,d,(0 if side else 3,8 if not up else 7,7 if side else 10,12),'blue3')
    if cast is not None:q.dot(8,3+cast,'watergleam');q.dot(10,12,'white')
    return finish(a,d)

def mole(v,d,f,cast):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);q=Pen(a,dy);side=d in ('left','right');up=d=='up'
    if v==2:
        q.l([(10,11),(14,9),(14,3),(11,1),(8,2),(8,4),(10,5)],'ink',2);q.l([(11,10),(13,8),(13,3),(11,2),(9,3)],'silver');q.e((8,3,11,6),'ink');q.dot(10,4,'gold3')
        for x,k in ((5,s),(9,-s)):leg(a,x,11,k,'silver',True)
        q.e((5,6,10,12),'ink');q.e((6,7,9,11),'purple2')
        for x,sg in ((5,-1),(10,1)):q.l([(x,7),(x+sg*2,10+s*sg),(x+sg*2,12+s*sg)],'ink',2);q.dot(x+sg*2,12+s*sg,'silver')
        face(q,d,(1 if side else 4,4 if not up else 3,8 if side else 11,9),'purple3')
    elif v==1:
        q.l([(11,9),(14,8+s)],'ink',2);q.dot(14,8+s,'silver')
        q.p([(3,8),(8,5),(12,7),(13,11),(9,13),(3,12)],'ink');q.p([(4,8),(8,6),(11,8),(12,10),(9,12),(4,11)],'purple2')
        for x,sg in ((4,-1),(11,1)):
            a.p([(x,8+dy),(x+sg*2,9+s*sg),(x+sg*3,12+s*sg),(x+sg,11+s*sg),(x+sg,13+s*sg),(x-sg,12)],'ink');a.l([(x+sg,10+s*sg),(x+sg*2,12+s*sg)],'silver')
        face(q,d,(1 if side else 4,8 if not up else 7,8 if side else 11,12),'purple3')
    else:
        q.l([(10,10),(13,9+s)],'ink',2);q.e((12,7+s,14,10+s),'ink');q.dot(13,8+s,'gold3')
        for x,k in ((4,s),(10,-s)):leg(a,x,11,k,'silver',True)
        q.e((3,5,12,12),'ink');q.e((4,6,11,11),'purple2');face(q,d,(1 if side else 4,6 if not up else 5,8 if side else 11,11),'purple3')
        for x,sg in ((3,-1),(12,1)):q.l([(x,8),(x+sg,10+s*sg),(x+sg*2,10+s*sg)],'ink',2);q.dot(x+sg*2,10+s*sg,'silver')
    if d!='up':q.e((1 if side else 6,9 if v!=2 else 7,5 if side else 9,11 if v!=2 else 9),'skin2');q.dot(2 if side else 7,10 if v!=2 else 8,'rose0')
    if cast is not None:q.dot(2,12,'white');q.dot(13,12-cast,'gold4')
    return finish(a,d)

def hopper(v,d,f,cast):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);q=Pen(a,dy);side=d in ('left','right');up=d=='up'
    if v==1:
        q.p([(7,6),(6,3),(8,1),(10,2),(9,6)],'ink');q.l([(8,5),(8,2)],'fire3')
        q.e((5,6,10,11),'ink');q.e((6,7,9,10),'rose3')
        for x,sg in ((5,-1),(10,1)):a.l([(x,8+dy),(x+sg*2,11),(x-sg+s*sg,14)],'ink');a.dot(x+sg*2,11,'fire3')
        face(q,d,(2 if side else 4,4 if not up else 3,9 if side else 11,8),'fire3')
        q.l([(5,9),(3,10+s)],'ink');q.l([(10,9),(12,10-s)],'ink')
    else:
        for x,k in ((4,s),(11,-s)):a.l([(x,10+dy),(x+k,13),(x+k+1,13)],'ink');a.dot(x+k,12,'fire3')
        if v==0:
            q.p([(7,2),(10,4),(13,7),(10,11),(5,11),(2,7),(5,4)],'ink');q.p([(7,3),(10,5),(12,7),(9,10),(6,10),(3,7)],'fire1');q.l([(7,4),(7,8)],'gold3');q.l([(4,5),(10,8)],'fire3')
        else:
            q.p([(1,8),(3,4),(7,3),(9,5),(13,4),(15,8),(13,11),(8,12),(3,11)],'ink')
            q.p([(2,8),(4,5),(7,4),(8,6),(6,9)],'skin2');q.p([(8,7),(13,5),(14,8),(12,10),(8,11)],'rose5');q.l([(3,7),(7,8),(12,7)],'fire2')
            # True gaps in folded sail seams, not a checkerboard alpha illusion.
            q.l([(8,5),(8,6)],'transparent')
        face(q,d,(0 if side else 4,8 if not up else 6,7 if side else 11,12 if not up else 10),'gold3')
    if d!='up':
        x=2 if side else 5;q.l([(x,5 if v==1 else 8),(x-1,3 if v==1 else 6)],'ink');q.l([(x+5,5 if v==1 else 8),(x+6,3 if v==1 else 6)],'ink')
    if cast is not None:q.dot(2,8,'gold4');q.dot(13,8+cast,'gold4')
    return finish(a,d)

def tapir(v,d,f,cast):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);dy=0;q=Pen(a,dy);side=d in ('left','right');up=d=='up'
    for j,x in enumerate((4,11)):
        k=s if j==0 else -s;leg(a,x,10 if cast is None and f==2 and j==1 else 11,k,'stone5',True)
    if side:
        a.l([(7,11),(7-s,13)],'ink');a.dot(7-s,12,'stone4')
    if side:
        q.p([(3,7),(5,4 if v else 6),(9,6),(13,8),(13,12),(4,12)],'ink');q.p([(4,8),(6,5 if v else 7),(9,7),(12,9),(12,11),(5,11)],'stone3')
    else:q.e((3,6 if v else 7,12,12),'ink');q.e((4,7 if v else 8,11,11),'stone3')
    hx=1 if side else 4;hy=4 if v else 6
    if v:
        q.p([(hx,hy+1),(max(0,hx-1),hy-2),(hx+1,hy-2),(hx+1,hy-3),(hx+3,hy-3),(hx+3,hy+1)],'ink');q.r((hx,hy-2,hx+2,hy),'stone4');q.l([(hx,hy-1),(hx+2,hy-1)],'stone5')
        q.p([(hx+5,hy+1),(hx+5,hy-3),(hx+7,hy-3),(hx+7,hy-2),(hx+9,hy-2),(hx+8,hy+1)],'ink');q.r((hx+6,hy-2,hx+8,hy),'stone4');q.l([(hx+6,hy-1),(hx+8,hy-1)],'stone5')
    else:
        for x in (hx,hx+5):q.e((x,hy-2,x+3,hy+1),'ink');q.dot(x+1,hy-1,'stone5')
    face(q,d,(hx,hy,hx+7,hy+6),'stone4')
    if not up:
        tx=hx if side else hx+3
        q.l([(tx,hy+4),(tx,hy+7 if v else hy+6),(tx+2+s,hy+8 if v else hy+6)],'ink',2);q.l([(tx,hy+4),(tx,hy+6)],'stone5')
    for x,y in ((10,7),(11,9),(9,10)):q.dot(x,y,'white')
    if cast is not None:q.dot(4,13,'gold4');q.dot(11,13,'gold4')
    return finish(a,d)

def crawler(v,d,f,cast):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);q=Pen(a,dy);side=d in ('left','right');up=d=='up'
    for j,x in enumerate((3,7,12)):
        k=(0,-1,1,0)[(f+j)%4] if cast is None else s*(-1 if j==1 else 1)
        for sg in (-1,1):a.l([(x,10+dy),(x+sg,12),(x+sg+k,14)],'ink');a.dot(x+sg+k,13,'skin2')
    if v:
        q.p([(1,10),(3,6),(6,3),(10,3),(13,6),(14,10),(12,11),(10,8),(5,8),(3,11)],'ink')
        q.l([(2,9),(4,6),(7,4),(10,4),(12,6),(13,9)],'pine5')
        for x,y in ((4,6),(8,4),(11,6)):q.l([(x,y),(x,9)],'ink');q.dot(x,y,'mint')
        q.e((2,9,13,12),'ink');q.l([(3,10),(7,11),(12,10)],'skin2',2)
    else:
        q.e((2,8,13,12),'ink');q.e((3,9,12,11),'skin2')
        for j,x in enumerate((2,5,8,11)):
            yy=6+((f+j)%4==1);q.e((x,yy,x+3,10),'ink');q.e((x+1,yy+1,x+2,9),'pine5')
    face(q,d,(0 if side else (3 if v else 4),8 if not up else 6,8 if side and v else (7 if side else (12 if v else 11)),13 if v and not up else (12 if not up else 10)),'wood5')
    if v and not up:q.dot(2 if side else 4,11,'rose4');q.dot(6 if side else 10,12,'skin2')
    if cast is not None:q.l([(5,11),(7,10),(10,11)],'mint')
    return finish(a,d)

def urchin(v,d,f,cast):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);q=Pen(a,dy);side=d in ('left','right');up=d=='up'
    if v:
        # Five curved umbrella ribs and connected tube-foot tassels.
        q.l([(1,6),(3,3),(7,1),(12,3),(14,6)],'ink',2);q.l([(2,5),(4,3),(7,2),(11,3),(13,5)],'water4')
        for x in (3,7,12):q.l([(7,2),(x,5),(x,7)],'ink');q.dot(x,5,'blue3')
        for x,k in ((4,s),(7,-s),(11,s)):a.l([(x,8+dy),(x+k,12),(x+k+1,14)],'ink',2);a.l([(x,9+dy),(x+k,12),(x+k+1,13)],'water4')
        face(q,d,(2 if side else 4,6 if not up else 5,9 if side else 11,10),'blue3')
    else:
        for x,y,X,Y in ((3,9,1,6),(5,7,4,3),(8,7,8,2),(10,7,12,3),(12,9,14,6)):
            q.l([(x,y),(X,Y+s if X<7 else Y-s)],'ink',2);q.dot(X,Y+s if X<7 else Y-s,'water4')
        for x,k in ((4,s),(8,-s),(11,s)):a.e((x-1,11+k,x+1,13+k),'ink');a.dot(x,12+k,'water4')
        q.e((2,6,13,12),'ink');q.e((3,7,12,11),'water2');face(q,d,(1 if side else 4,8 if not up else 6,8 if side else 11,12 if not up else 10),'water4')
    if cast is not None:q.dot(3,7,'white');q.dot(12,7,'watergleam')
    return finish(a,d)

FAMILY_FUNCTIONS=((31,33,snail),(34,36,goat),(37,39,pika),(40,42,sponge),(43,45,mole),(46,48,hopper),(95,96,tapir),(97,98,crawler),(99,100,urchin))
RIM_COLORS=('fire3',)*3+('stone4',)*3+('wood4',)*3+('water4',)*3+('silver',)*3+('fire3',)*3+('stone4',)*2+('pine5',)*2+('blue3',)*2
def material_rim(im,form_id,d):
    # Selective material-colored top/leading rim. Alpha and footprint never change.
    # Keeps existing ink on the lower/trailing edge for bright terrain, and gives
    # thin limbs a readable material edge over genuine dark doorway/foliage tiles.
    out=im.copy();color=P[RIM_COLORS[FORM_IDS.index(form_id)]];left=1 if d=='right' else -1
    def at(x,y):return im.getpixel((x,y)) if 0<=x<16 and 0<=y<16 else 0
    for y in range(16):
        for x in range(16):
            if at(x,y)==P['ink'] and (not at(x,y-1) or not at(x+left,y)) and (at(x,y+1) or at(x-left,y)):
                out.putpixel((x,y),color)
    return out

def field(form_id,d,f,cast=None):
    if form_id not in FORM_IDS or d not in DIRECTIONS or not isinstance(f,int) or not 0<=f<4 or cast not in (None,0,1):raise ValueError('Invalid native art coordinate')
    for low,high,fn in FAMILY_FUNCTIONS:
        if low<=form_id<=high:return material_rim(fn(form_id-low,d,f,cast),form_id,d)
    raise ValueError('No art')
def mask(im):return Image.frombytes('L',im.size,bytes(255 if n else 0 for n in im.tobytes()))
def paste(target,im,xy):target.paste(im.convert(target.mode),xy,mask(im))

# Portraits are separately composed at32px; no resize/scale of field rasters.
def peye(a,x,y):
    a.e((x,y,x+4,y+6),'ink');a.r((x+1,y,x+3,y+4),'white');a.r((x+1,y+2,x+2,y+5),'ink');a.dot(x+2,y+1,'white')
def pface(a,box,color='skin2',ears=False):
    x,y,X,Y=box
    if ears:
        for ex in (x,X-5):a.e((ex-1,y-5,ex+5,y+2),'ink');a.e((ex,y-4,ex+4,y),'skin1')
    a.e(box,'ink');a.e((x+1,y+1,X-1,Y-1),color);a.l([(x+3,y+2),(X-4,y+1)],'white')
    peye(a,x+2,y+3);peye(a,X-6,y+2)
    a.dot(x+2,Y-3,'rose4');a.dot(X-2,Y-4,'rose4');a.l([(x+5,Y-3),(x+7,Y-2),(X-4,Y-3)],'rose0')
def portrait(form_id):
    if form_id not in FORM_IDS:raise ValueError('Unsupported form')
    a=Art(32,32,'transparent')
    if 31<=form_id<=33:
        v=form_id-31
        a.p([(2,24),(6,20),(19,21),(29,25),(30,28),(26,30),(20,29),(14,30),(6,29),(1,27)],'ink');a.p([(3,24),(7,22),(19,23),(28,26),(28,28),(22,28),(17,27),(11,29),(4,27)],'skin2');a.l([(5,25),(10,24),(17,25),(24,26)],'white')
        if v==0:
            a.p([(10,20),(8,14),(10,6),(16,3),(23,4),(28,9),(28,14),(23,18),(17,17),(15,13),(17,10),(22,10),(23,12),(20,14),(22,14),(25,12),(24,8),(19,6),(14,9),(13,15),(16,20)],'ink');a.l([(10,14),(12,8),(17,5),(22,6),(26,10),(26,13),(23,16),(18,15),(17,12),(21,11)],'fire2',2);a.l([(14,7),(18,6),(22,7)],'gold4')
        elif v==1:
            a.p([(9,21),(6,14),(8,5),(16,1),(24,4),(29,12),(27,19),(22,22),(17,20),(17,17),(21,17),(23,13),(18,8),(13,10),(12,16),(15,21)],'ink');a.l([(8,13),(10,6),(16,3),(23,6),(27,12),(25,18),(22,20),(19,19)],'fire2',2);a.p([(14,12),(18,9),(21,14)],'transparent');a.l([(12,6),(16,5),(20,6)],'gold3')
        else:
            a.p([(1,7),(5,3),(14,1),(24,2),(30,6),(28,10),(23,8),(8,8),(3,11)],'ink');a.l([(3,7),(7,4),(15,3),(23,4),(28,7)],'fire3',2);a.l([(7,6),(14,5),(24,6)],'gold4')
            for x in (5,15,26):a.l([(x,8),(x+(3 if x<15 else -3),20)],'ink',3);a.l([(x,9),(x+(2 if x<15 else -2),18)],'fire1')
        pface(a,(3,18,19,27));a.l([(6,19),(5,14),(7,13)],'ink',2);a.l([(15,19),(17,14),(19,14)],'ink',2);a.dot(6,14,'gold4');a.dot(18,14,'gold4')
    elif 34<=form_id<=36:
        v=form_id-34
        for x in (9,23):a.l([(x,22),(x-1,28),(x+3,29)],'ink',4);a.l([(x,25),(x,28)],'stone5')
        if v==0:
            a.e((7,13,27,26),'ink');a.e((8,14,26,25),'wood4');a.p([(21,14),(26,16),(24,20),(20,18)],'stone4');a.l([(10,10),(9,3)],'ink',3);a.l([(20,9),(21,2)],'ink',3);a.l([(10,8),(10,4)],'stone5');a.l([(20,7),(21,3)],'stone5');pface(a,(5,9,24,22),'wood5')
        elif v==1:
            a.e((4,15,28,26),'ink');a.e((5,16,27,25),'wood3')
            for pts in ([(10,12),(5,5),(2,7),(2,15),(8,19)],[(21,12),(26,4),(29,6),(29,15),(24,19)]):a.l(pts,'ink',5);a.l(pts,'stone5',2)
            pface(a,(7,11,25,24),'wood5');a.p([(13,22),(15,27),(18,26),(20,22)],'stone4')
        else:
            a.p([(11,16),(21,15),(23,21),(20,25),(13,25),(9,21)],'ink');a.p([(12,17),(20,17),(21,21),(18,24),(14,23)],'wood4')
            a.l([(6,16),(2,10),(5,4),(15,1),(26,4),(30,10),(26,16)],'ink',3);a.l([(6,14),(4,10),(7,5),(15,3),(24,5),(28,10),(26,14)],'stone5',2);a.l([(15,3),(15,11)],'ink',2);a.l([(15,4),(15,8)],'gold3');pface(a,(7,12,24,23),'wood5');a.p([(11,22),(15,27),(20,22)],'stone4')
    elif 37<=form_id<=39:
        v=form_id-37
        for x in (9,22):a.l([(x,23),(x-2,28),(x+3,29)],'ink',4);a.dot(x,27,'skin2')
        if v==2:
            a.l([(20,24),(28,21),(29,9),(23,5)],'ink',3);a.l([(22,23),(26,20),(27,10)],'wood4');a.p([(20,1),(24,0),(28,3),(28,7),(23,10),(19,7),(18,3)],'ink');a.p([(21,2),(24,1),(27,4),(26,7),(23,8),(20,6)],'wood3');a.l([(21,3),(24,5),(21,6),(24,7)],'wood5');a.e((11,16,21,26),'ink');a.e((12,17,20,25),'wood3');a.l([(12,18),(6,23),(3,20)],'ink',3);a.l([(20,18),(25,23),(28,20)],'ink',3);pface(a,(6,11,24,21),'wood5',True)
        else:
            if v==0:a.r((24,15,30,22),'ink');a.r((25,16,29,21),'pine5');a.l([(25,16),(28,18),(26,20)],'mint')
            else:
                for x in (8,21):a.p([(x-4,18),(x-3,7),(x,9),(x+2,5),(x+5,16)],'ink');a.p([(x-2,14),(x-1,9),(x+1,11),(x+2,8),(x+3,15)],'pine5');a.dot(x,12,'mint')
            a.e((4,15,28,27),'ink');a.e((5,16,27,26),'wood3');pface(a,(4,13,23,25),'wood5',True)
            if v==0:a.l([(6,21),(1,17)],'pine4',2);a.l([(22,21),(30,16)],'pine5',2)
            else:a.p([(7,23),(9,30),(12,26),(15,30),(19,26),(21,28),(23,23)],'ink');a.l([(9,24),(10,27)],'wood4');a.l([(14,24),(15,28)],'wood5');a.l([(20,24),(20,26)],'wood4')
    elif 40<=form_id<=42:
        v=form_id-40
        if v==0:
            for x in (7,15,24):a.e((x-3,23,x+3,29),'ink');a.e((x-2,24,x+2,28),'water4')
            a.p([(5,21),(10,13),(11,5),(17,2),(23,6),(20,11),(20,16),(27,23),(25,27),(7,27)],'ink');a.p([(7,21),(12,14),(13,6),(17,4),(21,7),(18,11),(18,17),(25,23),(22,25)],'water4');a.e((14,5,20,8),'water1');a.l([(14,5),(17,4),(20,6)],'white');pface(a,(5,17,24,27),'water4');a.dot(22,16,'water1');a.dot(11,15,'water1')
        elif v==1:
            a.e((3,23,14,30),'ink');a.e((16,23,28,30),'ink');a.e((4,24,13,29),'water4');a.e((17,24,27,29),'water3');a.l([(12,26),(21,20),(22,11),(17,7)],'ink',7);a.l([(13,25),(20,19),(20,12),(17,9)],'water4',4)
            a.p([(4,11),(9,6),(10,2),(22,2),(23,6),(28,11),(26,15),(6,15)],'ink');a.p([(6,10),(11,6),(12,3),(20,3),(21,7),(26,11)],'water4');pface(a,(6,11,25,21),'blue3');a.l([(4,11),(13,10),(27,11)],'white',2);a.dot(21,22,'water1')
        else:
            for x in (4,11,21,27):a.e((x-2,24,x+2,29),'ink');a.dot(x,27,'water4')
            a.p([(2,18),(5,15),(5,5),(9,2),(12,6),(12,16),(18,16),(21,5),(25,3),(28,6),(27,17),(30,22),(27,26),(4,26),(1,23)],'ink');a.p([(4,19),(7,17),(7,6),(9,5),(10,7),(10,20),(20,20),(23,6),(25,5),(26,7),(25,19),(28,22),(25,25),(6,24)],'water4');a.l([(8,8),(8,15)],'white');a.l([(24,8),(22,17)],'blue3');pface(a,(2,18,20,27),'blue3');a.dot(25,22,'water1')
    elif 43<=form_id<=45:
        v=form_id-43
        for x in (10,21):a.l([(x,22),(x-2,28),(x+3,29)],'ink',4);a.l([(x-1,28),(x+2,28)],'silver')
        if v==2:
            a.l([(20,24),(28,21),(29,7),(24,2),(18,3),(17,8),(21,11)],'ink',4);a.l([(22,23),(26,20),(27,8),(24,4),(20,5),(19,8)],'silver');a.e((18,8,24,14),'ink');a.e((19,9,23,13),'gold2');a.dot(20,10,'white');a.e((10,14,22,27),'ink');a.e((11,15,21,26),'purple2');a.l([(11,17),(5,21),(3,27)],'ink',4);a.l([(21,17),(25,23),(26,28)],'ink',4);a.l([(3,25),(3,27)],'silver',2);a.l([(26,26),(26,28)],'silver',2);pface(a,(5,8,23,21),'purple3',True)
        elif v==1:
            a.l([(23,17),(30,14)],'ink',3);a.p([(5,15),(17,6),(25,13),(28,22),(22,27),(7,26)],'ink');a.p([(7,15),(17,8),(24,15),(26,22),(21,25),(8,24)],'purple2')
            for pts in ([(7,17),(2,20),(1,26),(4,25),(5,29),(8,27),(11,23)],[(23,17),(28,20),(30,26),(27,25),(27,29),(24,27),(20,23)]):a.p(pts,'ink')
            for x,y in ((2,24),(5,27),(28,24),(26,27)):a.l([(x,y-3),(x,y)],'silver',2)
            pface(a,(6,16,24,27),'purple3')
        else:
            a.l([(24,21),(28,18)],'ink',3);a.e((25,14,30,20),'ink');a.e((26,15,29,19),'gold2');a.dot(27,16,'white');a.e((5,10,27,27),'ink');a.e((6,11,26,26),'purple2');a.l([(7,19),(2,22),(1,24)],'ink',3);a.l([(25,19),(29,24),(30,24)],'ink',3);a.dot(1,23,'silver');a.dot(30,23,'silver');pface(a,(4,11,23,25),'purple3',True)
        a.e((9,21 if v!=2 else 17,18,27 if v!=2 else 23),'skin2');a.e((10,22 if v!=2 else 18,14,24 if v!=2 else 20),'rose0');a.dot(11,22 if v!=2 else 18,'white')
    elif 46<=form_id<=48:
        v=form_id-46
        if v==1:
            a.p([(14,13),(11,7),(15,0),(20,3),(19,10),(16,15)],'ink');a.p([(14,8),(16,3),(18,4),(17,10)],'fire3');a.e((10,14,23,25),'ink');a.e((11,15,22,24),'rose3')
            for pts in ([(11,18),(4,22),(9,29)],[(22,18),(28,22),(23,29)]):a.l(pts,'ink',3);a.l(pts,'fire3')
            pface(a,(6,10,25,21),'gold3');a.l([(8,11),(5,6)],'ink',2);a.l([(22,11),(26,6)],'ink',2)
        else:
            for x in (8,24):a.l([(x,21),(x-2,28),(x+1,29)],'ink',3);a.dot(x-1,27,'fire3')
            if v==0:
                a.p([(15,2),(24,8),(29,15),(23,24),(10,25),(2,15),(7,9)],'ink');a.p([(15,4),(23,10),(27,15),(21,22),(11,23),(4,15),(9,10)],'fire1');a.l([(15,6),(15,18)],'gold3',2);a.l([(8,11),(20,18)],'fire3',2)
            else:
                a.p([(1,17),(5,7),(14,4),(18,9),(25,6),(31,15),(27,23),(18,26),(6,24)],'ink');a.p([(3,17),(7,9),(13,6),(16,10),(12,19)],'skin2');a.p([(17,13),(25,8),(29,16),(25,22),(18,24),(13,21)],'rose5');a.l([(6,14),(13,16),(24,13)],'fire2');a.l([(17,9),(17,11)],'transparent');a.dot(23,17,'gold4')
            pface(a,(5,18,24,28),'gold3');a.l([(8,19),(6,14)],'ink',2);a.l([(22,19),(24,14)],'ink',2)
    elif 95<=form_id<=96:
        v=form_id-95
        for x in (9,24):a.l([(x,22),(x-1,28),(x+3,29)],'ink',4);a.l([(x,27),(x+2,27)],'stone5')
        a.p([(5,17),(10,9 if v else 13),(18,14),(27,18),(28,25),(8,27)],'ink');a.p([(7,18),(11,11 if v else 15),(18,16),(25,20),(26,24),(9,25)],'stone3')
        if v:
            a.p([(5,14),(2,9),(2,5),(5,5),(5,2),(10,2),(12,12)],'ink');a.l([(4,8),(7,4),(9,4)],'stone5',2);a.p([(20,13),(20,2),(25,2),(25,5),(29,5),(29,9),(25,14)],'ink');a.l([(22,4),(24,4),(27,8)],'stone5',2)
        pface(a,(4,10 if v else 13,23,24),'stone4',not v)
        a.l([(9,21),(8,27 if v else 25),(12,29 if v else 26),(15,27 if v else 25)],'ink',4);a.l([(9,21),(9,26 if v else 24),(12,27 if v else 25)],'stone5',2)
        for x,y in ((23,16),(25,19),(23,22)):a.e((x-1,y-1,x+1,y+1),'white')
    elif 97<=form_id<=98:
        v=form_id-97
        for x in (6,15,25):
            for sg in (-1,1):a.l([(x,22),(x+sg*2,26),(x+sg*2,29)],'ink',2);a.dot(x+sg*2,28,'skin2')
        if v:
            a.p([(1,21),(4,12),(11,5),(20,5),(28,12),(31,21),(27,23),(23,16),(9,16),(5,23)],'ink');a.l([(3,20),(6,12),(12,7),(20,7),(26,13),(29,20)],'pine5',2)
            for x,y in ((7,12),(15,7),(24,12)):a.l([(x,y),(x,20)],'ink',2);a.l([(x,y+1),(x,18)],'pine4');a.dot(x,y,'mint')
        else:
            for x,y in ((2,12),(9,10),(17,12),(24,10)):a.e((x,y,x+6,22),'ink');a.e((x+1,y+1,x+5,21),'pine5');a.l([(x+2,y+2),(x+4,y+3)],'mint')
        a.e((3,20,29,26),'ink');a.e((4,21,28,25),'skin2');pface(a,(2,16,21,27),'wood5');a.l([(4,16),(10,15),(16,16)],'wood3')
    elif 99<=form_id<=100:
        v=form_id-99
        if v:
            a.l([(1,13),(5,6),(15,2),(26,6),(30,13)],'ink',3);a.l([(3,12),(7,7),(15,4),(24,7),(28,12)],'water4',2)
            for x in (5,15,26):a.l([(15,4),(x,10),(x,15)],'ink',2);a.l([(15,5),(x,11)],'blue3');a.dot(x,12,'white')
            for x,k in ((7,-1),(14,1),(23,-1)):a.l([(x,18),(x+k,25),(x+k+2,30)],'ink',3);a.l([(x,19),(x+k,25),(x+k+2,29)],'water4')
            pface(a,(5,14,25,24),'blue3')
        else:
            for pts in ([(6,20),(1,12)],[(10,15),(7,5)],[(16,15),(17,2)],[(21,15),(26,5)],[(25,20),(30,12)]):a.l(pts,'ink',4);a.l(pts,'water4',2)
            for x in (7,16,25):a.e((x-3,24,x+3,30),'ink');a.e((x-2,25,x+2,29),'water4')
            a.e((3,12,29,27),'ink');a.e((4,13,28,26),'water2');pface(a,(5,16,25,27),'water4');a.dot(25,15,'white');a.dot(8,14,'blue3')
    return a.im

SCENE_SOURCES=(('GRASS','assets/review_terrain/frondshore_commons.png',(276,262,300,286)),
 ('WATER','assets/review_terrain/sunlace_anchorage.png',(32,287,56,311)),
 ('PLASTER','assets/review_terrain/sunlace_anchorage.png',(40,96,64,120)),
 ('WOOD','assets/review_terrain/awning_loft.png',(136,120,160,144)),
 ('SHADE','assets/review_terrain/forest.png',(172,16,196,40)),
 ('DOOR','assets/review_terrain/sunlace_anchorage.png',(68,104,92,128)))
def save_indexed(im,path):im.save(path,transparency=0,optimize=False)
def save_review(im,path):im.save(path,optimize=False)
def make_previews(fields,abilities,portraits):
    provenance=[];patches=[]
    for name,rel,box in SCENE_SOURCES:
        p=ROOT/rel
        with Image.open(p) as im:patches.append(im.convert('RGB').crop(box))
        provenance.append({'terrain':name,'path':rel,'crop':list(box),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    roster=Image.new('RGB',(480,288),RGB[P['dirt4']]);rd=ImageDraw.Draw(roster)
    black=Image.new('RGB',(480,224),RGB[P['white']]);bd=ImageDraw.Draw(black)
    for i,(id,key,name) in enumerate(zip(FORM_IDS,KEYS,NAMES)):
        w=Art(64,64,'transparent').im;c=Art(32,64,'transparent').im
        for d in range(4):
            for f in range(4):w.paste(fields[i][d][f],(16*f,16*d))
            for p in range(2):c.paste(abilities[i][d][p],(16*p,16*d))
        save_indexed(w,OUT/f'{key}_walk.png');save_indexed(c,OUT/f'{key}_ability.png');save_indexed(portraits[i],OUT/f'{key}_portrait.png')
        native=Image.new('RGB',(240,166),RGB[P['deep']]);nd=ImageDraw.Draw(native);nd.text((4,3),f'{id} {name} / ART ONLY',fill=RGB[P['white']]);paste(native,portraits[i],(204,28))
        for bg,y in (('deep',24),('dirt4',100)):
            nd.rectangle((0,y-2,199,y+65),fill=RGB[P[bg]])
            for d in range(4):
                for f,sp in enumerate(fields[i][d]+abilities[i][d]):paste(native,sp,(4+f*30,y+d*16))
        save_review(native,OUT/f'{key}_native.png')
        terrain=Image.new('RGB',(len(SCENE_SOURCES)*144,112),RGB[P['deep']]);td=ImageDraw.Draw(terrain)
        for t,(name,_,_) in enumerate(SCENE_SOURCES):
            td.text((t*144+2,1),name+' / '+str(id),fill=RGB[P['white']])
            for d in range(4):
                for f,sp in enumerate(fields[i][d]+abilities[i][d]):
                    tile=patches[t].copy();paste(tile,sp,(4,4));terrain.paste(tile,(t*144+f*24,16+d*24))
        save_review(terrain,OUT/f'{key}_terrain_native.png')
        anim=[]
        for frame in range(6):
            tile=Image.new('RGB',(128,48),RGB[P['dirt4']]);dr=ImageDraw.Draw(tile);dr.text((2,1),NAMES[i],fill=RGB[P['ink']])
            for d in range(4):paste(tile,(fields[i][d]+abilities[i][d])[frame],(8+d*30,23))
            anim.append(tile)
        anim[0].save(OUT/f'{key}_motion.gif',save_all=True,append_images=anim[1:],duration=[n*1000//60 for n in WALK_TICKS[i]]+[240,220],loop=0,disposal=2,optimize=False)
        x=(i%6)*80;y=(i//6)*72;rd.text((x+2,y+2),NAMES[i],fill=RGB[1]);rd.text((x+43,y+20),str(id),fill=RGB[1]);paste(roster,portraits[i],(x+3,y+16))
        for d in range(4):paste(roster,fields[i][d][0],(x+d*18+2,y+52))
        x=(i%6)*80;y=(i//6)*56;bd.text((x+2,y+2),str(id),fill=RGB[1])
        for d in range(4):black.paste(Image.new('RGB',(16,16),RGB[1]),(x+d*18+2,y+20),mask(fields[i][d][0]))
    save_review(roster,OUT/'roster_native.png');save_review(black,OUT/'silhouettes_native.png')
    save_review(roster.resize((960,576),Image.Resampling.NEAREST),OUT/'roster_2x.png')
    # Native240×160 compositions preserve actual scene pixels and sprite scale.
    # These are art-review composites, not screenshots of a playable build.
    composites=[]
    for name,rel,crop in SCENE_SOURCES:
        with Image.open(ROOT/rel) as src:scene=src.convert('RGB').crop((0,0,240,160))
        for i in range(24):paste(scene,fields[i][i%4][0],(10+(i%6)*38,24+(i//6)*32))
        save_review(scene,OUT/f'fullscreen_{name.lower()}_native.png');composites.append(scene)
    # Animation over one real native scene; no per-frame scaling or smoothing.
    with Image.open(ROOT/SCENE_SOURCES[0][1]) as src:scene=src.convert('RGB').crop((0,0,240,160))
    frames=[]
    for f in range(4):
        cur=scene.copy()
        for i in range(24):paste(cur,fields[i][i%4][f],(10+(i%6)*38,24+(i//6)*32))
        frames.append(cur)
    frames[0].save(OUT/'roster_walk_native.gif',save_all=True,append_images=frames[1:],duration=130,loop=0,disposal=2,optimize=False)
    return provenance,patches

def silhouette_metrics(fields):
    current=[mask(row[0][0]).tobytes() for row in fields]
    assert len(set(current))==24,'Distinct front silhouettes required'
    edges=((31,32),(32,33),(34,35),(35,36),(37,38),(37,39),(40,41),(40,42),(43,44),(43,45),(46,47),(46,48),(95,96),(97,98),(99,100),(38,39),(41,42),(44,45),(47,48))
    result=[]
    for left,right in edges:
        distances=[sum(x!=y for x,y in zip(mask(fields[FORM_IDS.index(left)][d][0]).tobytes(),mask(fields[FORM_IDS.index(right)][d][0]).tobytes())) for d in range(4)]
        result.append({'from':left,'to':right,'different_mask_pixels_by_direction':distances})
    nearest=[]
    for i,m in enumerate(current):
        distance,id=min((sum(x!=y for x,y in zip(m,n)),FORM_IDS[j]) for j,n in enumerate(current) if j!=i)
        nearest.append({'form_id':FORM_IDS[i],'nearest_form_id':id,'different_mask_pixels':distance})
    prior=json.loads((ROOT/'assets/review_terrain/released41_ids.json').read_text())['form_ids']
    source=Image.open(ROOT/'assets/review_terrain/released41_silhouettes_native.png').convert('RGB')
    comparison=Image.new('RGB',(560,444),RGB[P['white']]);draw=ImageDraw.Draw(comparison)
    draw.text((5,3),'65 NATIVE SILHOUETTES / RELEASED41 + MAGMA24 / ART ONLY',fill=RGB[1])
    old_masks=[]
    for i,id in enumerate(prior+list(FORM_IDS)):
        x=(i%7)*80;y=23+(i//7)*42;draw.text((x+4,y),str(id),fill=RGB[1])
        for d in range(4):
            if i<41:
                sx=(i%7)*80+4+d*18;sy=22+(i//7)*42+13
                tile=source.crop((sx,sy,sx+16,sy+16));m=Image.new('L',(16,16))
                m.putdata([255 if px==RGB[1] else 0 for px in getattr(tile,'get_flattened_data',tile.getdata)()])
                if d==0:old_masks.append(m.tobytes())
            else:m=mask(fields[i-41][d][0])
            comparison.paste(Image.new('RGB',(16,16),RGB[1]),(x+4+d*18,y+13),m)
    assert len(old_masks)==41 and not set(current).intersection(old_masks),'Released silhouette copied'
    save_review(comparison,OUT/'released65_silhouettes_native.png')
    return {'current_unique_front_masks':24,'released_form_ids':prior,'cross_release_front_mask_matches':0,
      'evolution_and_branch_distances':result,'nearest_front_mask_distances':nearest} 
def normalized_mask(im):
    m=mask(im);box=m.getbbox();return (box[2]-box[0],box[3]-box[1],m.crop(box).tobytes())
def validate_pixels(fields,abilities,portraits):
    allimgs=[s for forms in (fields,abilities) for row in forms for direction in row for s in direction]+portraits
    for im in allimgs:
        assert im.mode=='P' and im.getpalette()==PAL and im.size in ((16,16),(32,32))
        assert 0 in im.tobytes() and max(im.tobytes())<97
    for i,row in enumerate(fields):
        for d in range(4):
            walk=row[d];cast=abilities[i][d]
            assert len({s.tobytes() for s in walk+cast})==6,(NAMES[i],DIRECTIONS[d],'six poses')
            assert len({normalized_mask(s) for s in walk})==4,(NAMES[i],DIRECTIONS[d],'four articulated walk masks')
            assert len({normalized_mask(s) for s in cast})==2,(NAMES[i],DIRECTIONS[d],'two articulated cast masks')
            assert all(40<=sum(bool(n) for n in s.tobytes())<=230 for s in walk+cast),(NAMES[i],'occupancy')
        assert len({s[0].tobytes() for s in row})==4,(NAMES[i],'four views')
        assert all(row[3][f].tobytes()==row[2][f].transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes() for f in range(4))
        assert portraits[i].tobytes()!=row[0][0].resize((32,32),Image.Resampling.NEAREST).tobytes()
    assert len({mask(p).tobytes() for p in portraits})==24
    return {'images':600,'field_dimensions':[24,4,4,256],'ability_dimensions':[24,4,2,256],'portrait_dimensions':[24,1024],
      'palette_entries':178,'existing_actor_palette_only':True,'palette_indices':sorted({n for im in allimgs for n in im.tobytes()}),
      'transparent_zero':True,'native_field_footprint':[16,16],'distinct_articulated_walk_silhouettes_per_direction':4,'cast_poses_per_direction':2,
      'exact_bilateral_side_symmetry':True,'independently_composed_native_portraits':True}
def terrain_metrics(fields,abilities,patches):
    # Pixel visibility diagnostic, not a substitute for native visual review.
    # Measure opaque pixel RGB Euclidean distance from the actual terrain beneath.
    rows=[]
    for i,id in enumerate(FORM_IDS):
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
                                a=RGB[p];b=patch.getpixel((x+4,y+4));visible=sum((v-w)**2 for v,w in zip(a,b))>=48**2
                                n+=1;good+=visible
                                if any(not(0<=xx<16 and 0<=yy<16) or im.getpixel((xx,yy))==0 for xx,yy in ((x-1,y),(x+1,y),(x,y-1),(x,y+1))):en+=1;egood+=visible
                        ratios.append(good/n);edge_ratios.append(egood/en)
            rows.append({'form_id':id,'terrain':SCENE_SOURCES[t][0],'minimum_distinct_opaque_fraction':round(min(ratios),4),'minimum_distinct_boundary_fraction':round(min(edge_ratios),4)})
    return {'metric':'Native RGB555-preview RGB distance >=48; all24 poses checked per terrain. Heuristic only, not a gameplay/emulator performance claim.', 'samples':24*24*len(SCENE_SOURCES),'rows':rows,
      'minimum_opaque_fraction':min(r['minimum_distinct_opaque_fraction'] for r in rows),'minimum_boundary_fraction':min(r['minimum_distinct_boundary_fraction'] for r in rows)}
def output_hashes():
    files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='validation.json')
    files+=sorted((ROOT/'src/magma_creature_art_data').glob('*.inc'))+[ROOT/'src/magma_creature_art.c',ROOT/'src/magma_creature_art.h']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
def generate():
    OUT.mkdir(exist_ok=True)
    fields=[[[field(id,d,f) for f in range(4)] for d in DIRECTIONS] for id in FORM_IDS]
    abilities=[[[field(id,d,p,cast=p) for p in range(2)] for d in DIRECTIONS] for id in FORM_IDS]
    portraits=[portrait(id) for id in FORM_IDS]
    validation=validate_pixels(fields,abilities,portraits)
    sp=importlib.util.spec_from_file_location('magma_codegen',ROOT/'assets/magma_codegen.py');cg=importlib.util.module_from_spec(sp);sp.loader.exec_module(cg)
    chunks=cg.emit_code(ROOT,FORM_IDS,NAMES,fields,abilities,portraits)
    sources,patches=make_previews(fields,abilities,portraits);comparison=silhouette_metrics(fields);terrain=terrain_metrics(fields,abilities,patches)
    (OUT/'terrain_readability.json').write_text(json.dumps(terrain,indent=2)+'\n')
    manifest={'schema_version':1,'generator':'assets/generate_magma_creatures.py','form_ids':list(FORM_IDS),'names':list(NAMES),'directions':list(DIRECTIONS),
       'status':'ART ONLY. Native rendering, acquisition, catalog enablement and gameplay powers require independent integration acceptance.',
       'rights':'Original code-native pixel geometry. No Nintendo or other game art, tracing, downloaded raster reference, or raster-generated creature input.',
       'generator_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
       'codegen_sha256':hashlib.sha256((ROOT/'assets/magma_codegen.py').read_bytes()).hexdigest(),
       'palette_sha256':hashlib.sha256(json.dumps(base.COLORS).encode()).hexdigest(),'data_bytes':172056,'runtime_data_bytes':0,'runtime_bss_bytes':0,
       'persistent_obj_allocation_bytes':0,'rom_budget_bytes':174080,'include_bytes':chunks,'max_include_bytes':max(chunks),'scene_review_sources':sources,
       'anchor':[8,8],'frame_ticks_suggestion':8,'walk_ticks_by_form':dict(zip(map(str,FORM_IDS),WALK_TICKS)),'ability_poses':['anticipation','recovery'],'briefs':BRIEFS,'validation':validation,'silhouette_comparison':comparison,
       'terrain_visibility_minimum_opaque':terrain['minimum_opaque_fraction'],'terrain_visibility_minimum_boundary':terrain['minimum_boundary_fraction']}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (OUT/'CREDITS.txt').write_text(manifest['rights']+'\nAll sprites authored natively at16×16 or32×32 in Python/Pillow. Existing178-color RGB555 palette preserved.\nNative previews are art composites, never emulator evidence or acquisition proof.\n')
    return manifest

def verify(manifest):
    before=output_hashes();generate();assert before==output_hashes(),'Nondeterministic regeneration'
    report={'deterministic_regeneration':True,'pixel_validation':manifest['validation'],'output_sha256':output_hashes()}
    with tempfile.TemporaryDirectory(prefix='magma-art-') as td:
        td=Path(td);sys.path.insert(0,str(ROOT/'tools'))
        from arm_toolchain import resolve_arm_tools
        tools=resolve_arm_tools('gcc','size',root=ROOT);arm=Path(tools['gcc'])
        obj=td/'magma_art.o';subprocess.run([str(arm),'-std=c99','-mcpu=arm7tdmi','-mthumb','-O2','-ffreestanding','-fno-builtin','-fstack-usage','-Wall','-Wextra','-Werror','-c',str(ROOT/'src/magma_creature_art.c'),'-o',str(obj)],check=True,capture_output=True)
        size=subprocess.check_output([tools['size'],str(obj)],text=True);sections=list(map(int,size.splitlines()[-1].split()[:3]));assert sections[1:]==[0,0] and sections[0]<=174080
        stack=[int(line.split('\t')[1]) for p in td.glob('*.su') for line in p.read_text().splitlines()];assert stack and max(stack)<=24
        report.update({'arm_compile':'passed','arm_rom_object_bytes':sections[0],'arm_data_bytes':sections[1],'arm_bss_bytes':sections[2],'max_arm_stack_bytes':max(stack),'max_include_bytes':manifest['max_include_bytes']})
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');return {k:v for k,v in report.items() if k not in ('output_sha256','pixel_validation')}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');args=parser.parse_args()
    manifest=generate();print(json.dumps(verify(manifest) if args.verify else {'generated_forms':FORM_IDS,'data_bytes':manifest['data_bytes'],'max_include_bytes':manifest['max_include_bytes']},indent=2))
if __name__=='__main__':main()
