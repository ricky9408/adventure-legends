#!/usr/bin/env python3
"""Original Southern native animal pixels. Art only, never roster/acquisition logic.
Writes only this region's asset directory and immutable C art source/tables.
Every direction is pixel-authored; bilateral side views deliberately mirror.
"""
from pathlib import Path
import argparse, hashlib, importlib.util, io, json, shutil, subprocess, sys, tempfile
from PIL import Image, ImageDraw
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'assets/southern_creatures';SRC=ROOT/'src'
spec=importlib.util.spec_from_file_location('southern_palette',ROOT/'assets/generate_assets.py')
base=importlib.util.module_from_spec(spec);spec.loader.exec_module(base)
Art,P,PAL,RGB=base.Art,base.P,base.PAL,base.rgb
DIRECTIONS=('down','up','left','right')
FORM_IDS=(25,26,28,29,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94)
NAMES=('Tangleaper','Boughvault','Duneroll','Dunescoop','Skimkip','Sailskip','Warmcroak','Bellowswell','Shellwaddle','Vaultback','Clipmantis','Foilscythe','Swaylemur','Canopetail','Rillnewt','Veilcrest','Glimmerbat','Flarefan','Needletrot','Quillstride')
KEYS=tuple(n.lower() for n in NAMES)
class Pen:
    def __init__(self,a,dy=0):self.a,self.dy=a,dy
    def p(self,pts,c):self.a.p([(x,y+self.dy) for x,y in pts],c)
    def l(self,pts,c,w=1):self.a.l([(x,y+self.dy) for x,y in pts],c,w)
    def e(self,b,c):self.a.e((b[0],b[1]+self.dy,b[2],b[3]+self.dy),c)
    def r(self,b,c):self.a.r((b[0],b[1]+self.dy,b[2],b[3]+self.dy),c)
    def dot(self,x,y,c):self.a.dot(x,y+self.dy,c)
def eye(q,x,y,look=0,heavy=False):
    q.r((x,y,x+1,y+2),'white');q.dot(x+look,y+1,'ink');q.dot(x+look,y+2,'ink')
    if heavy:q.l([(x,y),(x+1,y)],'rose0')
def pair(q,x1,x2,y,heavy=False):eye(q,x1,y,1,heavy);eye(q,x2,y,0,heavy)
def finish(a,d):
    if d=='right':a.im=a.im.transpose(Image.Transpose.FLIP_LEFT_RIGHT);a.d=ImageDraw.Draw(a.im)
    return a
def beat(f,cast=None,hop=False):
    # Foot phase is independent of body lift; four contours, not color flicker.
    if cast is not None:return (0,-1)[cast],(-1,1)[cast]
    return ((0,1,-1,0) if hop else (0,0,-1,0))[f],(0,-1,0,1)[f]
def limb(a,pts,c,bright):a.l(pts,c,2);a.l(pts,bright)
def face(q,d,x1,x2,y,heavy=False):
    if d=='down':pair(q,x1,x2,y,heavy)
    elif d in ('left','right'):eye(q,x1,y,0,heavy)
    else:q.l([(x1,y+1),(x2+1,y+1)],'mint')

def gecko(d,f,ev=False,cast=None):
    a=Art(16,16,'transparent');dy,s=beat(f,cast,ev);q=Pen(a,dy);side=d in ('left','right')
    # Tangleaper coils a real tail; Boughvault spans continuous skin membranes.
    if ev:
        if side:
            q.p([(3,6),(7,3),(12,5),(15,11+s),(11,10),(8,13),(5,10),(1,12-s)],'ink')
            q.p([(4,7),(7,4),(11,6),(13,10+s),(10,9),(8,11),(5,9),(2,11-s)],'pine4')
            q.l([(7,5),(8,8),(11,7)],'mint')
        else:
            q.p([(7,4),(3,5),(0,11+s),(5,10),(7,13),(10,10),(15,11-s),(12,5),(8,4)],'ink')
            q.p([(7,5),(4,6),(2,10+s),(5,9),(7,11),(10,9),(13,10-s),(11,6)],'pine4')
            q.l([(4,6),(6,8),(3,10+s)],'mint');q.l([(11,6),(9,8),(12,10-s)],'pine5')
    else:
        if side:q.l([(10,9),(14,8+s),(14,4+s),(12,3+s),(11,4+s),(12,5+s)],'ink',2);q.l([(11,9),(13,7+s),(13,4+s),(12,4+s)],'pine5')
        else:q.l([(9,10),(13,9),(14,5+s),(12,3+s),(10,4+s),(11,6+s)],'ink',2);q.l([(10,10),(12,8),(13,5+s),(12,4+s)],'pine5')
    for x,y,k in ((4,9,s),(10,10,-s),(4,13,-s),(10,13,s)):
        a.l([(6 if x<7 else 9,8+dy),(x+k,y-1),(x+k-1,y),(x+k+1,y)],'ink');a.dot(x+k,y-1,'mint')
    if side:
        q.e((4,6,11,12),'ink');q.e((5,7,10,11),'pine3');q.l([(6,8),(9,8)],'mint')
        q.p([(2,5),(5,5),(7,7),(6,10),(2,10),(0,8)],'ink');q.p([(2,6),(5,6),(6,8),(4,9),(1,8)],'pine5')
        eye(q,2,6);q.dot(1,9,'rose4');q.dot(5,9,'mint')
    else:
        q.e((5,5,10,12),'ink');q.e((6,6,9,11),'pine3');q.l([(7,6),(7,10)],'pine5')
        if d=='down':
            q.p([(4,5),(10,5),(12,7),(11,10),(8,11),(4,10),(3,7)],'ink');q.p([(5,6),(10,6),(11,7),(10,9),(5,9),(4,7)],'pine5');pair(q,4,9,6);q.l([(6,9),(8,10),(9,9)],'pine0')
        else:q.e((4,3,11,8),'ink');q.e((5,4,10,7),'pine4');q.dot(6,4,'mint');q.l([(7,11),(8,14),(10,14)],'ink');q.dot(9,13,'pine5')
    if cast is not None:q.l([(4,11),(3-cast,12),(2-cast,11)],'mint');q.dot(11,7,'leafwarm')
    return finish(a,d)

def dune(d,f,ev=False,cast=None):
    a=Art(16,16,'transparent');dy,s=beat(f,cast,not ev);q=Pen(a,dy);side=d in ('left','right')
    if ev:
        # Forward-weighted broad digging forefeet; low body and high ear arc.
        for x,k in ((3,s),(10,-s)):
            a.p([(x,9+dy),(x+2,9+dy),(x+3+k,12),(x+3+k,14),(x-2+k,14),(x-2+k,12)],'ink');a.l([(x-1+k,13),(x+1+k,12)],'skin2')
    else:
        for x,k in ((4,s),(9,-s)):
            a.p([(x,10+dy),(x+2,10+dy),(x+2+k,13),(x+4+k,14),(x+k,14),(x-1,12)],'ink');a.l([(x+k,13),(x+2+k,13)],'wood4')
    if side:
        q.l([(11,10),(14,9+s),(14,6+s)],'ink');q.p([(13,5+s),(14,4+s),(15,6+s),(14,7+s)],'wood4')
        q.e((3,6,13 if ev else 11,12),'ink');q.e((4,7,12 if ev else 10,11),'wood3');q.e((4,8,8,11),'skin2')
        q.p([(3,7),(1,4),(2,1),(4,2),(5,6),(5,2),(7,1),(8,2),(7,7)],'ink');q.l([(2,3),(3,5)],'skin1');q.l([(6,2),(6,5)],'gold3')
        q.p([(2,5),(6,5),(8,7),(7,10),(3,11),(0,9),(0,7)],'ink');q.p([(2,6),(5,6),(7,7),(6,9),(3,10),(1,8)],'wood4');eye(q,2,6);q.dot(0,8,'ink');q.dot(5,9,'rose4')
    else:
        q.e((4 if not ev else 3,6,11 if not ev else 12,12),'ink');q.e((5 if not ev else 4,7,10 if not ev else 11,11),'wood3')
        q.p([(4,7),(2,3),(3,1),(5,2),(6,6),(8,5),(9,1),(11,1),(12,2),(10,7)],'ink');q.l([(3,2),(4,5)],'skin2');q.l([(10,2),(9,5)],'skin1')
        if d=='down':
            q.e((3,5,12,11),'ink');q.e((4,6,11,10),'wood4');pair(q,4,9,6);q.dot(7,9,'ink');q.l([(6,10),(8,10)],'skin2')
        else:q.e((4,4,11,10),'ink');q.e((5,5,10,9),'wood3');q.l([(5,5),(7,4),(9,5)],'wood5');q.l([(9,11),(12,12+s),(14,11+s)],'ink');q.dot(14,10+s,'wood4')
    if cast is not None:q.l([(3,12),(4,11-cast),(5,12)],'gold3');q.l([(10,12),(11,11-cast)],'skin2')
    return finish(a,d)

def fish(d,f,ev=False,cast=None):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);q=Pen(a,dy);side=d in ('left','right');spread=(s if cast is None else (-1,1)[cast])
    if side:
        q.p([(10,7),(14,4+spread),(15,5+spread),(13,8),(15,11-spread),(14,12-spread),(10,10)],'ink');q.l([(12,7),(14,5+spread)],'water4');q.l([(12,9),(14,11-spread)],'blue3')
        if ev:q.p([(6,8),(6,1),(8,1),(10,3),(11,8),(13,12),(10,11),(8,8),(6,13),(3,14),(4,10)],'ink');q.p([(7,7),(7,2),(8,2),(9,4),(10,7)],'blue3');q.l([(7,3),(8,6)],'white')
        else:q.p([(6,8),(7,4+spread),(11,3+spread),(11,5+spread),(9,9),(8,13),(5,14),(3,12)],'ink');q.p([(7,8),(8,5+spread),(10,4+spread),(9,7)],'water3')
        q.p([(2,6),(5,5),(9,6),(12,8),(10,11),(5,12),(2,11),(0,9),(0,7)],'ink');q.p([(2,7),(5,6),(9,7),(10,8),(9,10),(5,11),(2,10),(1,8)],'blue2');q.l([(3,10),(6,10),(9,9)],'water4');eye(q,1,7);q.dot(4,9,'rose5');q.dot(0,9,'ink')
        q.p([(6,9),(9,8),(10,10+spread),(7,13+spread),(5,12)],'ink');q.l([(7,10),(8,10),(6,12+spread)],'water4')
    else:
        if ev:
            q.p([(6,9),(2,1+spread),(0,2+spread),(1,8),(4,12),(6,11),(9,11),(12,12),(14,8),(15,2-spread),(12,2-spread),(9,9)],'ink');q.p([(5,9),(2,3+spread),(2,7),(4,10)],'blue3');q.p([(10,9),(13,3-spread),(13,7),(11,10)],'water4')
        else:
            q.p([(6,8),(2,5+spread),(0,6+spread),(1,10),(4,12),(6,11),(9,11),(12,12),(15,9-spread),(14,5-spread),(11,6),(9,8)],'ink');q.p([(5,9),(2,7+spread),(2,9),(4,10)],'water3');q.p([(10,9),(13,7-spread),(13,9),(11,10)],'water4')
        q.p([(6,9),(9,9),(9,12),(11,14),(9,15),(7,13),(5,15),(4,14),(6,12)],'ink');q.l([(7,11),(7,12),(5,14)],'water4')
        q.e((5,4,10,12),'ink');q.e((6,5,9,11),'blue2')
        if d=='down':q.e((4,5,11,10),'ink');q.e((5,6,10,9),'blue3');pair(q,4,9,6);q.dot(6,9,'rose5');q.dot(9,9,'rose4');q.l([(7,10),(8,10)],'ink')
        else:q.p([(7,2),(9,4),(10,7),(8,10),(5,7),(5,4)],'ink');q.p([(7,3),(8,4),(9,7),(7,8),(6,6)],'blue2');q.l([(7,4),(7,7)],'water4')
    if cast is not None:q.dot(5,10,'watergleam');q.dot(9,10,'white')
    return finish(a,d)

def frog(d,f,ev=False,cast=None):
    a=Art(16,16,'transparent');dy,s=beat(f,cast,True);q=Pen(a,dy);side=d in ('left','right')
    # Four webbed living feet, a single pouch versus connected paired cheek folds.
    for x,k in ((2,s),(11,-s)):
        a.p([(x+1,8+dy),(x+3,10+dy),(x+2+k,13),(x-1+k,14),(x-1+k,12),(x,11)],'ink');a.l([(x+1,10+dy),(x+1+k,12)],'rose3');a.dot(x+k,13,'fire3')
    if side:
        q.e((3,6 if ev else 7,13,12),'ink');q.e((4,7 if ev else 8,12,11),'rose2');q.l([(9,8),(11,9)],'fire2')
        q.e((1,4 if ev else 6,8,11),'ink');q.e((2,5 if ev else 7,7,10),'fire2');eye(q,2,5 if ev else 6,0,True);q.l([(1,9),(4,10),(6,9)],'rose0')
        q.e((3,9,9 if ev else 7,13),'ink');q.e((4,10,8 if ev else 6,12),'skin2')
        if ev:q.e((7,7,12,11),'rose0');q.e((8,8,11,10),'fire3');q.l([(5,8),(6,7)],'gold4')
    else:
        q.e((2 if ev else 3,5 if ev else 7,13 if ev else 12,13),'ink');q.e((3 if ev else 4,6 if ev else 8,12 if ev else 11,12),'rose3')
        if d=='down':
            q.e((3,4 if ev else 6,12,11),'ink');q.e((4,5 if ev else 7,11,10),'fire2');pair(q,3,10,5 if ev else 6,True)
            q.l([(5,9),(7,10),(10,9)],'rose0')
            if ev:
                q.e((2,9,7,13),'rose0');q.e((3,10,6,12),'skin2');q.e((8,9,13,13),'rose0');q.e((9,10,12,12),'skin2');q.r((7,11,8,12),'fire3')
            else:q.e((5,10,10,13),'rose0');q.e((6,11,9,12),'skin2')
        else:
            q.e((4,3 if ev else 5,11,10),'ink');q.e((5,4 if ev else 6,10,9),'rose3');q.l([(6,6),(8,5),(10,7)],'fire2');q.dot(6,8,'fire3');q.dot(10,10,'rose5')
    for x,k in ((5,-s),(9,s)):a.l([(x,10+dy),(x+k,13),(x+k-1,14)],'ink');a.dot(x+k,13,'fire3')
    if cast is not None:q.l([(5,11-cast),(7,12-cast),(10,11-cast)],'gold4')
    return finish(a,d)

def crab(d,f,ev=False,cast=None):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);q=Pen(a,dy);side=d in ('left','right')
    # Low sideways crab versus an open raised shell vault and distinct abdomen.
    for x,sg in ((2,1),(12,-1)):
        for j,y in enumerate((8,10,12)):
            h=(5 if ev else 9)+dy
            a.l([(5 if sg==1 else 10,h),(x,y-1),(x+sg*s+(j%2),y+2)],'ink');a.dot(x,y,'wood4')
    if ev:
        q.p([(2,6),(4,3),(7,2),(11,3),(13,6),(13,8),(11,7),(10,5),(5,5),(4,8),(2,8)],'ink');q.l([(3,6),(5,4),(8,3),(11,4),(12,6)],'wood4',2);q.dot(6,3,'gold4')
        q.e((5,9,10,12),'ink');q.e((6,10,9,11),'skin2');q.l([(7,6),(7,9)],'wood3')
    else:q.e((3,7,12,12),'ink');q.e((4,8,11,11),'wood3');q.l([(5,8),(8,7),(10,8)],'gold3');q.dot(10,10,'skin2')
    if d=='down':
        for x in (5,9):q.l([(x,8 if not ev else 5),(x,5 if not ev else 2)],'ink');eye(q,x-1,4 if not ev else 1,1 if x==5 else 0)
        q.l([(6,10 if not ev else 11),(8,11 if not ev else 12),(9,10 if not ev else 11)],'wood0')
    elif side:
        q.l([(4,8 if not ev else 5),(2,6 if not ev else 3)],'ink');eye(q,1,4 if not ev else 1);q.dot(4,10 if not ev else 11,'rose4')
    else:q.l([(5,8 if not ev else 4),(10,8 if not ev else 4)],'wood1');q.dot(8,9 if not ev else 3,'gold4')
    # Unequal soft tips close during anticipation and reopen in recovery.
    clawshift=s if cast is None else (-2,2)[cast]
    q.l([(4,9 if not ev else 6),(1,7+clawshift),(1,5+clawshift)],'ink',2)
    q.p([(0,4+clawshift),(1,3+clawshift),(2,5+clawshift),(3,3+clawshift),(4,4+clawshift),(3,7+clawshift),(1,7+clawshift)],'ink');q.dot(1,5+clawshift,'skin2');q.dot(2,6+clawshift,'wood4')
    q.l([(11,9 if not ev else 6),(14,7-clawshift)],'ink',2);q.p([(13,5-clawshift),(14,4-clawshift),(15,6-clawshift),(14,8-clawshift),(12,7-clawshift)],'ink');q.dot(14,6-clawshift,'gold3')
    return finish(a,d)

def mantis(d,f,ev=False,cast=None):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);q=Pen(a,dy);side=d in ('left','right');k=s if cast is None else (-2,1)[cast]
    # Four thin walking legs leave open air beneath a longer folded abdomen.
    for x,y,sg in ((3,12,1),(12,12,-1),(5,14,-1),(10,14,1)):
        a.l([(7 if x<8 else 9,8+dy),(x,y-2),(x+sg*s,y)],'ink');a.dot(x,y-1,'silver')
    if side:
        q.p([(7,6),(10,5),(12,7),(13,11 if ev else 10),(11,13 if ev else 11),(9,10),(7,9)],'ink');q.l([(10,6),(11,8),(12,11 if ev else 9)],'stone4');q.l([(8,5),(7,10)],'ink',2);q.l([(8,6),(8,9)],'silver')
        q.p([(2,3),(7,3),(8,4),(6,7),(4,7),(1,5)],'ink');q.p([(2,4),(6,4),(5,6),(3,5)],'stone4');eye(q,1,3);q.dot(5,4,'white');q.l([(3,3),(2,1),(3,1)],'ink');q.l([(6,3),(8,1)],'ink')
        if ev:q.p([(6,7),(4,8),(1,7+k),(0,9+k),(1,12+k),(4,12+k),(3,10+k),(6,9)],'ink');q.l([(3,8+k),(1,9+k),(2,11+k)],'white')
        else:q.l([(6,7),(3,9+k),(1,8+k),(2,6+k)],'ink',2);q.l([(3,8+k),(2,7+k)],'silver')
    else:
        q.p([(6,6),(9,6),(10,9),(9,13 if ev else 11),(7,12),(6,9)],'ink');q.l([(7,7),(8,10),(8,12 if ev else 10)],'silver')
        q.l([(5,3),(3,1)],'ink');q.l([(10,3),(12,1)],'ink')
        if d=='down':q.p([(2,3),(6,2),(10,2),(13,3),(10,7),(6,7)],'ink');q.p([(3,4),(6,3),(10,3),(11,4),(9,6),(6,6)],'stone4');pair(q,3,10,3);q.dot(7,6,'pine0')
        else:q.p([(3,2),(7,1),(11,2),(12,4),(9,6),(6,6),(3,4)],'ink');q.p([(4,3),(7,2),(10,3),(9,5),(6,5)],'stone3');q.dot(7,3,'white')
        for sg in (-1,1):
            x=7 if sg<0 else 8
            if ev:q.p([(x,7),(x+sg*3,6+k),(x+sg*6,7+k),(x+sg*6,10+k),(x+sg*4,12+k),(x+sg*2,11+k),(x+sg*4,10+k),(x+sg*4,8+k),(x,9)],'ink');q.l([(x+sg*4,7+k),(x+sg*5,9+k),(x+sg*4,10+k)],'white')
            else:q.l([(x,7),(x+sg*4,8+k),(x+sg*4,11+k),(x+sg*2,10+k)],'ink');q.l([(x+sg*3,8+k),(x+sg*3,10+k)],'silver')
    return finish(a,d)

def lemur(d,f,ev=False,cast=None):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);q=Pen(a,dy);side=d in ('left','right')
    if ev:
        # Raised tail loop supports visual counterbalance, with empty center.
        q.l([(10,10),(13,7+s),(13,2),(10,1),(7,2),(7,4),(9,5)],'ink',2);q.l([(11,9),(12,6+s),(12,3),(10,2),(8,3)],'pine4');q.dot(11,2,'mint');q.dot(12,6+s,'mint')
    else:
        q.l([(10,11),(14,10),(14,6+s),(12,4+s),(10,5+s)],'ink',2);q.l([(11,11),(13,9),(13,6+s)],'pine4');q.p([(12,6+s),(9,4+s),(10,2+s),(12,3+s)],'ink');q.dot(10,3+s,'pine5');q.p([(14,8+s),(15,6+s),(14,5+s),(12,7+s)],'pine5')
    for x,k in ((5,s),(9,-s)):
        a.l([(x,10+dy),(x+k,13),(x+k+2,14)],'ink',2);a.dot(x+k+1,13,'skin2')
    if side:
        q.e((5,7 if ev else 8,10,12),'ink');q.e((6,8 if ev else 9,9,11),'purple2')
        if ev:q.l([(6,8),(3,10+s),(2,13+s)],'ink',2);q.dot(2,13+s,'skin2')
        else:q.l([(6,10),(3,11+s)],'ink',2);q.dot(3,11+s,'skin2')
        q.e((0,3 if ev else 5,3,7 if ev else 9),'ink');q.dot(1,5 if ev else 7,'skin1');q.e((6,4 if ev else 5,9,8 if ev else 9),'ink');q.dot(8,6 if ev else 7,'skin2')
        q.e((1,4 if ev else 6,8,10),'ink');q.e((2,5 if ev else 7,7,9),'purple2');q.e((1,7,5,10),'skin2');eye(q,2,6 if ev else 7);q.dot(0,9,'ink');q.dot(5,9,'rose4')
    else:
        q.e((5,7,10,12),'ink');q.e((6,8,9,11),'purple2')
        for x,sg in ((4,-1),(11,1)):
            if ev:q.l([(6 if x<8 else 9,7),(x,10+s*sg),(x+sg,13-s*sg)],'ink',2);q.dot(x+sg,13-s*sg,'skin2')
            else:q.l([(6 if x<8 else 9,10),(x,12+s*sg)],'ink',2);q.dot(x,12+s*sg,'skin2')
        q.e((1,4 if ev else 5,5,8 if ev else 9),'ink');q.e((2,5 if ev else 6,4,7 if ev else 8),'skin1');q.e((10,4 if ev else 5,14,8 if ev else 9),'ink');q.e((11,5 if ev else 6,13,7 if ev else 8),'skin1')
        q.e((3,4 if ev else 5,12,10),'ink');q.e((4,5 if ev else 6,11,9),'purple2')
        if d=='down':q.e((5,7,10,10),'skin2');pair(q,4,9,5 if ev else 6);q.dot(7,9,'ink');q.dot(6,10,'rose4')
        else:q.l([(5,6),(7,5),(10,6)],'pine5');q.l([(6,8),(9,8)],'purple1')
    if cast is not None:q.dot(3,11,'mint');q.dot(11,11,'mint')
    return finish(a,d)

def newt(d,f,ev=False,cast=None):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);q=Pen(a,dy);side=d in ('left','right')
    for x,y,k in ((3,11,s),(10,11,-s),(4,14,-s),(11,14,s)):
        a.l([(6 if x<8 else 9,9+dy),(x,y-2),(x+k-1,y),(x+k+1,y)],'ink');a.dot(x+k,y-1,'teal2')
    if side:
        q.p([(9,9),(12,7),(15,6+s),(14,9+s),(11,12),(8,12)],'ink');q.l([(10,10),(12,9),(14,7+s)],'teal2')
        if ev:q.p([(5,8),(6,4),(8,2),(10,5),(12,3),(14,5),(14,8),(11,10)],'ink');q.p([(6,7),(7,4),(8,4),(10,7),(12,5),(13,6),(12,8)],'water4');q.l([(8,5),(9,8)],'purple3')
        q.e((4,8,12,12),'ink');q.e((5,9,11,11),'water2');q.l([(6,9),(9,9)],'teal2')
        q.p([(1,7),(5,6),(8,8),(7,11),(4,12),(1,11),(0,9)],'ink');q.p([(2,8),(5,7),(7,8),(6,10),(4,11),(1,10)],'teal2');eye(q,1,7);q.l([(1,10),(3,11),(5,10)],'water0');q.dot(5,8,'water4')
        if ev:q.l([(5,10),(3,12+s),(1,11+s)],'purple3');q.l([(9,10),(10,12-s),(12,11-s)],'water4')
    else:
        q.p([(7,9),(10,10),(13,12+s),(12,15),(9,14),(6,12)],'ink');q.l([(8,10),(11,12+s),(11,14)],'teal2')
        if ev:q.p([(6,8),(4,5),(6,2),(7,4),(9,1),(11,3),(10,7),(11,10)],'ink');q.p([(6,7),(5,5),(6,4),(7,6),(9,3),(10,4),(9,8)],'water4');q.dot(8,5,'purple3')
        q.e((4,7,11,12),'ink');q.e((5,8,10,11),'water2')
        if d=='down':q.e((2,6,13,11),'ink');q.e((3,7,12,10),'teal2');pair(q,3,10,6);q.l([(5,10),(7,11),(10,10)],'water0');q.dot(5,8,'water4')
        else:q.e((4,4,11,9),'ink');q.e((5,5,10,8),'water2');q.l([(6,5),(8,6),(9,5)],'water4')
        if ev:q.l([(4,10),(2,12+s),(4,12+s)],'purple3');q.l([(11,10),(13,12-s),(11,12-s)],'water4')
    if cast is not None:q.dot(6,11,'watergleam');q.dot(9,10,'white')
    return finish(a,d)

def bat(d,f,ev=False,cast=None):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);q=Pen(a,dy);side=d in ('left','right');flap=(0,-1,1,0)[f] if cast is None else (-2,2)[cast]
    if side:
        if ev:q.p([(7,7),(10,2+flap),(13,3+flap),(15,6),(14,10),(12,8),(11,12),(8,10),(6,11)],'ink');q.p([(8,7),(10,4+flap),(12,4+flap),(14,6),(13,8),(11,7),(10,10)],'rose3');q.l([(10,4),(11,7),(12,8)],'fire3')
        else:q.p([(6,8),(9,4+flap),(13,4+flap),(15,7),(13,10),(11,8),(9,11),(6,10)],'ink');q.p([(8,8),(10,5+flap),(12,5+flap),(14,7),(12,8),(10,7),(9,9)],'purple2')
        q.e((4,7,9,12),'ink');q.e((5,8,8,11),'rose2');q.p([(2,7),(1,2),(3,1),(5,5),(6,2),(8,3),(7,8)],'ink');q.l([(2,3),(3,5)],'fire3');q.dot(6,4,'rose4')
        q.e((1,5,7,10),'ink');q.e((2,6,6,9),'rose3');eye(q,1,6);q.r((0,9,3,10),'fire3');q.dot(0,9,'ink')
    else:
        if ev:
            q.p([(6,8),(4,3+flap),(1,2+flap),(0,7),(2,11),(4,9),(5,12),(7,10),(9,10),(10,12),(12,9),(14,11),(15,7),(14,3-flap),(11,3-flap),(9,8)],'ink')
            q.p([(5,8),(3,4+flap),(2,4+flap),(1,7),(2,9),(4,7),(5,10),(6,9)],'rose3');q.p([(10,8),(12,4-flap),(13,4-flap),(14,7),(13,9),(11,7),(10,10),(9,9)],'rose3');q.l([(3,4),(4,7),(5,9)],'fire3');q.l([(12,4),(11,7),(10,9)],'fire2')
        else:
            q.p([(6,8),(4,5+flap),(1,5+flap),(0,8),(2,11),(4,9),(6,12),(9,12),(11,9),(13,11),(15,8),(14,5-flap),(11,5-flap),(9,8)],'ink');q.p([(5,8),(3,6+flap),(1,7),(2,9),(4,8),(5,10)],'purple2');q.p([(10,8),(12,6-flap),(14,7),(13,9),(11,8),(10,10)],'purple3')
        q.e((5,7,10,12),'ink');q.e((6,8,9,11),'rose2')
        q.p([(4,6),(3,1),(5,1),(7,5),(9,4),(10,1),(12,1),(11,6)],'ink');q.l([(4,2),(5,4)],'fire3');q.l([(11,2),(10,4)],'rose4')
        q.e((4,4,11,10),'ink');q.e((5,5,10,9),'rose3')
        if d=='down':pair(q,4,9,5);q.e((6,8,9,10),'fire3');q.dot(7,9,'ink');q.dot(8,9,'ink')
        else:q.l([(5,5),(7,4),(10,5)],'rose5');q.l([(6,7),(9,7)],'rose2')
    for x,sg in ((6,1),(9,-1)):
        yy=14 if ev else 13
        a.l([(x,11+dy),(x+s*sg,yy),(x+s*sg-1,yy)],'ink');a.dot(x+s*sg,yy-1,'fire3')
    return finish(a,d)

def tenrec(d,f,ev=False,cast=None):
    a=Art(16,16,'transparent');dy,s=beat(f,cast);q=Pen(a,dy);side=d in ('left','right')
    if ev:
        # Separate radiating quills stand above the slim body, never a solid saw.
        for pts in ([(7,8),(3,3),(4,2)],[(8,8),(6,1)],[(9,8),(9,1)],[(10,8),(12,1)],[(11,9),(15,3)],[(11,10),(15,6)]):q.l(pts,'ink',2);q.l(pts,'silver')
    else:
        q.p([(4,8),(5,5),(7,6),(8,3),(10,5),(12,4),(12,7),(14,7),(13,10)],'ink');q.l([(6,6),(7,8)],'silver');q.l([(9,5),(10,8)],'stone4');q.dot(12,6,'white')
    for x,k in ((5,s),(11,-s)):
        a.l([(x,9+dy),(x+k,13),(x+k+1,14)],'ink',2 if ev and x==11 else 1);a.dot(x+k,13,'stone4')
    # Evolved torso rides two pixels higher on visibly lengthened rear legs.
    if ev:q=Pen(a,dy-2)
    if side:
        q.e((4,8,13,11 if ev else 12),'ink');q.e((5,9,12,10 if ev else 11),'dusk1');q.l([(6,9),(10,9)],'stone3')
        q.e((4,6,7,9),'ink');q.dot(5,7,'skin2')
        q.p([(4,7),(7,8),(8,10),(5,12),(1,12),(0,11),(1,9)],'ink');q.p([(4,8),(6,9),(6,10),(4,11),(1,11),(2,10)],'stone4');q.dot(0,11,'ink');eye(q,3,8);q.dot(5,10,'skin2')
    else:
        q.e((4,7,12,11 if ev else 13),'ink');q.e((5,8,11,10 if ev else 12),'dusk1');q.l([(6,8),(8,7),(10,8)],'silver')
        q.e((2,6,5,9),'ink');q.dot(3,7,'skin2');q.e((10,6,13,9),'ink');q.dot(12,7,'skin1')
        if d=='down':q.p([(4,7),(11,7),(12,10),(9,12),(8,14),(6,13),(4,11),(3,9)],'ink');q.p([(5,8),(10,8),(11,9),(8,11),(7,13),(5,10),(4,9)],'stone4');pair(q,4,9,8);q.dot(7,13,'ink');q.dot(6,11,'skin2')
        else:q.e((4,4,11,10),'ink');q.e((5,5,10,9),'dusk1');q.l([(6,5),(8,6),(9,5)],'silver');q.l([(10,11),(12,13+s),(14,12+s)],'ink')
    if cast is not None:q.l([(8,5-cast),(9,7),(10,5-cast)],'white')
    return finish(a,d)

FAMILIES=(gecko,dune,fish,frog,crab,mantis,lemur,newt,bat,tenrec)
FIELD_FUNCTIONS=tuple((lambda d,f,fn=fn,ev=ev:fn(d,f,ev)) for fn in FAMILIES for ev in (False,True))
# Stable face anchors also support explicit cast intent without covering pupils.
FRONT_PUPILS=((5,9,7),(5,9,7),(5,9,7),(5,9,7),(5,9,7),(5,9,7),
 (4,10,7),(4,10,6),(5,8,5),(5,8,2),(4,10,4),(4,10,4),(5,9,7),
 (5,9,6),(4,10,7),(4,10,7),(5,9,6),(5,9,6),(5,9,9),(5,9,7))
def cast_frame(index,d,pose):
    a=FAMILIES[index//2](d,pose,bool(index%2),cast=pose)
    if d=='down':
        x1,x2,y=FRONT_PUPILS[index];y+=(0,-1)[pose]
        # Gather narrows the upper eyelid; recovery visibly opens both eyes.
        for x in (x1,x2):a.dot(x,y-1,'purple0' if pose==0 else 'white')
    return a
ABILITY_FUNCTIONS=tuple((lambda d,p,i=i:cast_frame(i,d,p)) for i in range(20))
def mask(im):return Image.frombytes('L',im.size,bytes(255 if n else 0 for n in im.tobytes()))
def paste(target,sprite,xy):
    im=sprite.im if isinstance(sprite,Art) else sprite;target.paste(im.convert(target.mode),xy,mask(im))
def save_indexed(im,path):im.save(path,transparency=0,optimize=False)
def save_review(im,path):
    pal=Image.new('P',(1,1));pal.putpalette(PAL);im.quantize(palette=pal,dither=Image.Dither.NONE).save(path,optimize=True)
def concept_sheet(path=None):
    sheet=Image.new('RGB',(480,330),RGB[P['dirt4']]);d=ImageDraw.Draw(sheet)
    d.text((6,4),'SOUTHERN / ORIGINAL NATIVE ANIMALS / ART ONLY',fill=RGB[P['ink']])
    for i,fn in enumerate(FIELD_FUNCTIONS):
        x=(i%4)*120;y=24+(i//4)*60;d.text((x+3,y),str(FORM_IDS[i])+' '+NAMES[i],fill=RGB[P['ink']])
        for j,di in enumerate(DIRECTIONS):
            im=fn(di,0).im;paste(sheet,im,(x+6+j*27,y+15));sheet.paste(Image.new('RGB',(16,16),RGB[P['ink']]),(x+6+j*27,y+36),mask(im))
    OUT.mkdir(exist_ok=True);save_review(sheet,path or OUT/'silhouette_native.png');return sheet

# Portraits are separately composed at32×32. No upscaled field-pixel inputs.
def portrait_eye(a,x,y,look=1,heavy=False):
    a.p([(x+1,y),(x+3,y),(x+4,y+2),(x+3,y+5),(x+1,y+5),(x,y+3),(x,y+1)],'ink')
    a.p([(x+1,y+1),(x+3,y+1),(x+3,y+4),(x+1,y+4)],'white');a.r((x+look,y+2,x+look+1,y+4),'ink');a.dot(x+look,y+2,'blue3')
    if heavy:a.l([(x,y+1),(x+4,y+1)],'rose0')
def p_gecko(ev=False):
    a=Art(32,32,'transparent')
    if ev:
        a.p([(14,10),(8,8),(2,13),(1,24),(7,21),(12,28),(16,22),(22,27),(25,20),(31,23),(28,11),(22,8)],'ink')
        a.p([(13,12),(8,10),(4,14),(3,21),(7,19),(12,25),(15,20),(21,24),(24,18),(28,20),(26,13),(21,10)],'pine4')
        a.l([(8,11),(13,16),(7,19)],'mint');a.l([(23,11),(18,16),(25,19)],'pine5')
    else:
        a.l([(20,22),(27,23),(29,19),(28,13),(25,11),(23,13),(24,15)],'ink',4);a.l([(21,22),(26,22),(28,19),(27,14),(25,13)],'pine5',2)
    for pts in ([(12,17),(7,22),(4,23)],[(19,19),(22,25),(25,26)],[(12,24),(9,29),(6,29)]):a.l(pts,'ink',3);a.l(pts,'pine5');a.dot(pts[-1][0]+1,pts[-1][1]-1,'mint')
    a.e((10,12,23,26),'ink');a.e((11,13,21,24),'pine3');a.e((13,16,20,24),'mint');a.l([(20,14),(21,18),(19,22)],'pine5')
    a.p([(7,8),(10,4),(19,3),(24,7),(24,13),(20,17),(11,17),(6,13),(5,10)],'ink');a.p([(8,9),(11,5),(19,4),(22,8),(22,12),(19,15),(11,15),(7,12)],'pine5')
    a.e((7,5,13,12),'pine3');a.e((18,4,24,11),'pine3');portrait_eye(a,8,6,2);portrait_eye(a,18,5,1)
    a.l([(10,13),(14,15),(18,14),(20,12)],'pine0');a.dot(11,12,'rose4');a.dot(21,11,'mint');a.l([(14,6),(16,5),(17,6)],'leafwarm')
    if ev:a.l([(20,25),(22,29),(27,29)],'ink',2);a.dot(26,28,'pine5')
    return a

def p_dune(ev=False):
    a=Art(32,32,'transparent')
    a.l([(21,22),(28,24),(30,19)],'ink',2);a.p([(28,18),(30,15),(31,19),(30,21)],'wood4')
    if ev:
        a.p([(8,18),(17,15),(24,17),(27,22),(25,26),(17,28),(8,25)],'ink');a.p([(10,19),(17,17),(23,18),(25,22),(23,24),(16,26),(10,24)],'wood3')
        for x,y in ((7,23),(20,25)):
            a.p([(x,19),(x+5,20),(x+7,y+3),(x+5,y+5),(x-3,y+5),(x-4,y+2)],'ink');a.p([(x+1,21),(x+3,22),(x+4,y+3),(x-2,y+3)],'skin2');a.l([(x-1,y+2),(x-1,y+4)],'wood2');a.l([(x+2,y+2),(x+2,y+4)],'wood2')
    else:
        a.e((9,15,24,27),'ink');a.e((10,16,22,25),'wood3');a.e((12,18,20,25),'skin2')
        a.p([(9,23),(13,22),(15,28),(12,30),(5,30),(4,28),(9,26)],'ink');a.l([(8,28),(12,28)],'wood4',2)
        a.p([(20,23),(23,22),(26,27),(30,28),(29,30),(23,30),(21,28)],'ink');a.l([(24,28),(28,29)],'skin2')
    a.p([(9,14),(4,7),(4,1),(7,0),(11,5),(13,12),(15,11),(16,4),(20,1),(22,3),(20,9),(18,15)],'ink')
    a.p([(8,11),(6,6),(6,2),(8,4),(10,8)],'skin2');a.p([(17,11),(18,5),(20,3),(19,8)],'skin1')
    a.p([(8,11),(16,9),(21,12),(21,17),(17,22),(9,21),(5,18),(4,15)],'ink');a.p([(8,12),(16,10),(19,13),(19,17),(16,20),(9,19),(6,17),(6,14)],'wood4')
    portrait_eye(a,7,12,2);portrait_eye(a,15,11,1);a.e((10,17,16,21),'skin2');a.dot(12,18,'ink');a.l([(12,19),(11,20),(13,20)],'wood0');a.r((6,18,8,19),'rose4')
    return a

def p_fish(ev=False):
    a=Art(32,32,'transparent')
    a.p([(21,17),(29,11),(31,12),(28,19),(31,25),(29,27),(21,23)],'ink');a.p([(24,18),(28,14),(27,19),(29,24),(24,22)],'water4')
    if ev:
        a.p([(12,16),(8,4),(9,0),(12,2),(18,13),(23,2),(26,1),(26,7),(22,19),(16,24),(10,28),(5,30),(7,22)],'ink')
        a.p([(12,14),(10,5),(11,3),(16,13)],'blue3');a.p([(19,14),(23,5),(24,4),(24,8),(21,16)],'water4');a.l([(12,6),(15,12)],'white');a.l([(23,7),(21,13)],'watergleam')
    else:
        a.p([(12,16),(7,10),(1,9),(0,12),(5,20),(11,23),(19,24),(23,20),(27,8),(25,7),(18,12)],'ink');a.p([(10,16),(5,12),(2,12),(6,18),(10,20)],'water3');a.p([(20,17),(24,10),(25,10),(22,18)],'blue3')
    a.p([(4,14),(10,11),(19,12),(24,16),(25,20),(22,23),(15,26),(7,24),(2,20),(1,17)],'ink');a.p([(5,15),(10,12),(18,13),(22,16),(23,20),(20,22),(15,24),(7,22),(3,19),(3,17)],'blue2');a.p([(4,18),(8,20),(17,20),(21,18),(20,22),(14,24),(7,22)],'water4')
    portrait_eye(a,4,14,2);portrait_eye(a,12,13,1);a.r((4,21,6,22),'rose5');a.r((17,20,19,21),'rose4');a.l([(8,22),(10,23),(13,22)],'water0');a.dot(9,12,'watergleam')
    a.p([(17,20),(22,19),(22,24),(18,29),(12,29),(14,26)],'ink');a.p([(18,22),(20,21),(20,24),(17,27),(15,27)],'water3');a.l([(18,23),(17,26)],'white')
    return a

def p_frog(ev=False):
    a=Art(32,32,'transparent')
    for x in (2,21):
        a.e((x,17,x+8,27),'ink');a.e((x+1,18,x+7,25),'rose3');a.p([(x+3,23),(x+5,26),(x+8,29),(x+5,30),(x,30),(x,28)],'ink');a.l([(x+2,28),(x+5,28)],'fire3')
    a.e((5,12 if ev else 15,26,28),'ink');a.e((6,13 if ev else 16,25,26),'rose3')
    a.e((4,7 if ev else 10,26,22),'ink');a.e((5,8 if ev else 11,25,20),'fire2')
    a.e((5,5 if ev else 8,13,15),'ink');a.e((18,5 if ev else 8,26,15),'ink');a.e((6,6 if ev else 9,12,14),'fire2');a.e((19,6 if ev else 9,25,14),'fire2')
    portrait_eye(a,7,8 if ev else 10,2,True);portrait_eye(a,19,8 if ev else 10,1,True);a.l([(8,18),(12,20),(19,20),(23,17)],'rose0');a.dot(7,17,'rose5');a.dot(23,16,'gold4')
    if ev:
        a.e((3,20,15,28),'rose0');a.e((4,21,14,26),'skin2');a.e((16,19,28,28),'rose0');a.e((17,20,26,26),'skin2');a.r((14,23,17,26),'fire3');a.l([(6,23),(11,24)],'gold4');a.l([(20,22),(24,22)],'gold4')
    else:a.e((10,20,22,28),'rose0');a.e((11,21,21,26),'skin2');a.l([(13,23),(18,24)],'gold4')
    for x in (9,22):a.l([(x,24),(x-1,28),(x-3,30)],'ink',2);a.dot(x-1,28,'fire3')
    return a

def p_crab(ev=False):
    a=Art(32,32,'transparent')
    for sg in (-1,1):
        x=15
        for j in range(3):
            pts=[(x+sg*6,12 if ev else 21),(x+sg*(11+j),20+j*3),(x+sg*(9+j),28+j)]
            a.l(pts,'ink',2);a.l(pts,'wood4')
    if ev:
        a.p([(4,15),(5,9),(10,5),(17,4),(24,6),(28,11),(28,17),(24,15),(22,10),(11,10),(8,15)],'ink');a.l([(6,13),(8,9),(12,6),(18,6),(23,8),(26,12)],'wood4',3);a.l([(10,8),(16,6),(21,8)],'gold4')
        a.e((11,20,22,26),'ink');a.e((12,21,21,24),'skin2');a.l([(16,11),(17,20)],'wood3',2)
    else:
        a.e((6,15,26,26),'ink');a.e((7,16,24,24),'wood3');a.p([(8,19),(11,16),(17,16),(22,18),(20,21),(12,22)],'wood4');a.l([(11,17),(17,17),(20,18)],'gold4')
    for x,y in ((10,8 if ev else 11),(20,8 if ev else 11)):
        a.l([(x+2,15 if ev else 20),(x+1,y)],'ink',2);a.e((x-1,y-2,x+5,y+5),'ink');portrait_eye(a,x,y-1,2 if x==10 else 1)
    a.l([(13,23 if ev else 22),(16,24 if ev else 23),(19,22 if ev else 21)],'wood0')
    a.l([(8,17),(3,17),(2,12)],'ink',3);a.p([(1,10),(0,6),(2,5),(4,10),(5,5),(7,6),(7,12),(5,16),(2,15)],'ink');a.p([(2,9),(3,12),(5,10),(5,13),(3,14)],'skin2')
    a.l([(25,18),(29,14),(29,11)],'ink',2);a.p([(26,10),(26,7),(28,6),(29,9),(30,6),(31,8),(31,13),(28,14)],'ink');a.l([(28,10),(29,12),(30,10)],'gold3')
    return a

def p_mantis(ev=False):
    a=Art(32,32,'transparent')
    for pts in ([(13,19),(7,23),(5,30)],[(18,18),(25,23),(28,29)],[(14,22),(12,27),(10,31)],[(19,21),(21,28),(24,31)]):a.l(pts,'ink',2);a.l(pts,'silver')
    a.p([(14,11),(19,13),(23,19),(23,27 if ev else 24),(21,29 if ev else 26),(17,23),(14,19)],'ink');a.p([(16,13),(18,14),(21,20),(21,26 if ev else 23),(19,23),(16,18)],'stone3');a.l([(18,15),(20,20),(21,24)],'white')
    a.l([(14,11),(13,18),(15,23)],'ink',3);a.l([(14,13),(14,19)],'silver')
    a.l([(10,5),(7,1),(4,0)],'ink');a.l([(19,4),(22,1),(25,1)],'ink')
    a.p([(4,6),(10,3),(18,3),(25,6),(22,11),(16,15),(11,13),(6,10)],'ink');a.p([(6,7),(11,4),(18,4),(23,7),(20,10),(16,13),(11,11)],'stone4')
    portrait_eye(a,6,5,2);portrait_eye(a,18,5,1);a.l([(13,11),(15,12),(17,10)],'pine0');a.dot(14,6,'white')
    if ev:
        a.p([(12,16),(7,14),(2,15),(0,20),(1,25),(5,27),(8,25),(4,23),(3,19),(6,18),(11,20)],'ink');a.l([(6,16),(3,17),(2,20),(3,24),(5,25)],'white',2)
        a.p([(18,16),(24,13),(29,14),(31,18),(31,22),(28,25),(25,23),(28,21),(28,17),(24,16),(20,20)],'ink');a.l([(26,14),(29,16),(30,20),(28,23)],'silver',2)
    else:
        a.l([(12,16),(5,17),(3,22),(6,25),(10,22)],'ink',2);a.l([(6,18),(5,22),(7,23)],'silver')
        a.l([(19,16),(25,15),(28,19),(26,23),(23,21)],'ink',2);a.l([(25,17),(27,19),(25,21)],'white')
    return a

def p_lemur(ev=False):
    a=Art(32,32,'transparent')
    if ev:
        a.l([(22,21),(28,17),(29,8),(26,3),(20,1),(16,4),(17,8),(21,8)],'ink',4);a.l([(23,21),(27,16),(27,8),(25,5),(20,3),(18,5)],'pine4',2);a.dot(25,5,'mint');a.dot(28,12,'mint')
    else:
        a.l([(22,25),(28,22),(28,13),(24,9),(21,12)],'ink',4);a.l([(23,25),(26,21),(27,14),(24,11)],'pine4',2);a.p([(23,12),(19,8),(19,5),(22,4),(25,8)],'ink');a.p([(22,10),(20,7),(22,6),(24,9)],'pine5');a.p([(28,17),(31,12),(29,10),(26,14)],'pine5')
    a.e((10,13,23,27),'ink');a.e((11,14,21,25),'purple2');a.e((12,17,19,24),'skin2')
    if ev:
        a.l([(12,16),(6,21),(3,28)],'ink',3);a.l([(20,17),(24,23),(26,29)],'ink',3);a.l([(3,27),(2,29),(5,29)],'skin2',2);a.dot(26,28,'skin2')
    else:a.l([(11,20),(6,22),(6,25)],'ink',3);a.dot(6,24,'skin2');a.l([(20,21),(23,23)],'ink',3);a.dot(23,23,'skin2')
    a.l([(13,25),(11,29),(8,30)],'ink',3);a.dot(9,29,'skin2');a.l([(20,25),(20,29),(24,30)],'ink',3);a.dot(23,29,'skin2')
    a.e((2,5 if ev else 7,11,14 if ev else 16),'ink');a.e((3,6 if ev else 8,9,12 if ev else 14),'skin1');a.e((19,5 if ev else 7,28,14 if ev else 16),'ink');a.e((21,6 if ev else 8,26,12 if ev else 14),'skin1')
    a.e((6,5 if ev else 7,24,21),'ink');a.e((7,6 if ev else 8,22,19),'purple2');a.e((10,13,20,21),'skin2');portrait_eye(a,8,9 if ev else 10,2);portrait_eye(a,17,8 if ev else 10,1);a.r((13,17,15,18),'ink');a.l([(14,18),(13,20),(16,20)],'wood0');a.dot(10,18,'rose4');a.dot(21,16,'rose5')
    return a

def p_newt(ev=False):
    a=Art(32,32,'transparent')
    a.p([(20,22),(25,18),(30,16),(31,19),(27,25),(20,28),(17,25)],'ink');a.p([(22,22),(28,19),(27,23),(21,26)],'teal2')
    if ev:
        a.p([(13,14),(12,8),(14,3),(17,1),(20,6),(23,3),(26,6),(25,13),(29,12),(28,18),(23,22)],'ink');a.p([(15,13),(14,9),(16,4),(17,4),(20,10),(23,6),(24,8),(23,16),(26,15),(25,18)],'water4');a.l([(17,6),(18,11),(17,15)],'purple3');a.l([(22,10),(21,16)],'watergleam')
    for pts in ([(12,22),(8,27),(4,28)],[(21,22),(25,28),(28,29)],[(12,18),(7,22),(3,22)]):a.l(pts,'ink',3);a.l(pts,'teal2');a.dot(pts[-1][0]+1,pts[-1][1]-1,'water4')
    a.e((9,14,26,27),'ink');a.e((10,15,24,25),'water2');a.l([(16,17),(20,18),(22,21)],'teal2',2)
    a.p([(5,12),(10,9),(18,9),(24,13),(23,18),(19,23),(9,23),(3,20),(1,16)],'ink');a.p([(5,13),(10,10),(18,10),(22,14),(21,18),(18,21),(9,21),(4,19),(3,16)],'teal2');a.l([(5,18),(9,21),(15,22),(20,19)],'water0');portrait_eye(a,5,12,2);portrait_eye(a,16,11,1);a.dot(10,11,'water4');a.dot(21,16,'purple3')
    if ev:a.p([(8,22),(4,24),(2,21),(1,24),(3,28),(8,25)],'purple3');a.p([(21,22),(26,23),(28,21),(30,24),(26,27),(23,25)],'water4')
    return a

def p_bat(ev=False):
    a=Art(32,32,'transparent')
    if ev:
        a.p([(12,17),(9,8),(4,3),(1,5),(0,15),(3,23),(6,19),(9,26),(13,22),(17,22),(21,26),(24,19),(29,23),(31,15),(30,5),(27,3),(22,8),(19,17)],'ink');a.p([(10,17),(8,10),(4,6),(2,8),(2,15),(4,20),(6,16),(9,22),(12,20)],'rose3');a.p([(21,17),(23,10),(27,6),(29,8),(29,15),(27,20),(25,16),(22,22),(19,20)],'rose3');a.l([(4,6),(6,12),(6,16)],'fire3');a.l([(27,6),(25,12),(25,16)],'fire2')
    else:
        a.p([(12,16),(8,11),(3,10),(0,13),(2,20),(6,23),(8,19),(12,25),(19,25),(23,19),(26,23),(30,20),(31,13),(28,10),(23,11),(19,16)],'ink');a.p([(10,17),(7,13),(3,12),(2,14),(4,19),(6,20),(7,17),(11,22)],'purple2');a.p([(21,17),(24,13),(28,12),(29,14),(27,19),(25,20),(24,17),(20,22)],'purple3')
    a.e((10,13,22,26),'ink');a.e((11,14,20,24),'rose2');a.l([(12,24),(11,29 if ev else 27),(8,30 if ev else 28)],'ink',2);a.l([(20,24),(22,29 if ev else 27),(25,30 if ev else 28)],'ink',2);a.dot(10,29 if ev else 27,'fire3');a.dot(23,29 if ev else 27,'fire3')
    a.p([(9,12),(6,4),(7,0),(10,2),(14,10),(18,10),(20,2),(23,0),(25,4),(22,13)],'ink');a.p([(9,9),(8,4),(9,3),(12,9)],'fire3');a.p([(20,10),(22,4),(23,3),(23,7)],'rose4')
    a.e((7,8,24,21),'ink');a.e((8,9,22,19),'rose3');portrait_eye(a,9,10,2);portrait_eye(a,18,10,1);a.e((12,16,20,21),'fire3');a.r((14,17,16,18),'ink');a.l([(15,19),(14,20),(17,20)],'rose0');a.dot(9,18,'rose5')
    return a

def p_tenrec(ev=False):
    a=Art(32,32,'transparent')
    if ev:
        for pts in ([(16,18),(7,5),(5,4)],[(17,17),(11,2)],[(19,17),(16,0)],[(21,17),(22,1)],[(22,18),(28,3)],[(23,20),(31,9)],[(23,22),(31,16)]):a.l(pts,'ink',3);a.l(pts,'silver');a.dot(pts[-1][0],pts[-1][1],'white')
    else:
        a.p([(8,15),(9,10),(12,11),(13,5),(17,8),(20,5),(22,9),(27,8),(26,14),(29,16),(25,21),(13,21)],'ink');a.l([(11,11),(14,16)],'silver',2);a.l([(15,9),(18,15)],'stone4',2);a.l([(21,10),(22,16)],'white');a.l([(25,12),(24,17)],'silver')
    a.e((9,15,28,25),'ink');a.e((10,16,26,23),'dusk1');a.l([(17,17),(22,17),(25,19)],'stone3',2)
    a.l([(13,22),(10,28),(7,29)],'ink',2);a.dot(8,28,'stone4');a.l([(24,21),(26,27),(29,29)],'ink',3 if ev else 2);a.dot(28,28,'stone4')
    a.e((7,10,14,17),'ink');a.e((8,11,12,15),'skin2');a.e((20,11,25,17),'ink');a.dot(22,13,'skin1')
    a.p([(9,13),(18,13),(23,17),(20,22),(13,25),(7,26),(2,24),(0,22),(3,18)],'ink');a.p([(9,14),(17,14),(21,17),(18,21),(12,23),(7,24),(2,22),(5,19)],'stone4');a.p([(6,20),(10,21),(11,23),(7,24),(2,22)],'skin2');portrait_eye(a,8,15,2);portrait_eye(a,17,15,1);a.r((1,22,3,23),'ink');a.l([(5,24),(8,24)],'wood0');a.dot(15,21,'white')
    return a
PORTRAIT_FAMILIES=(p_gecko,p_dune,p_fish,p_frog,p_crab,p_mantis,p_lemur,p_newt,p_bat,p_tenrec)
PORTRAIT_FUNCTIONS=tuple((lambda fn=fn,ev=ev:fn(ev)) for fn in PORTRAIT_FAMILIES for ev in (False,True))

def emit_code(fields,abilities,portraits):
    upper=', '.join('SOUTHERN_CREATURE_'+key.upper() for key in KEYS)
    header=f'''/* Generated original art; edit assets/generate_southern_creatures.py. */
#ifndef EMBERBOND_SOUTHERN_CREATURE_ART_H
#define EMBERBOND_SOUTHERN_CREATURE_ART_H
#define SOUTHERN_CREATURE_ART_COUNT 20
#define SOUTHERN_CREATURE_ART_FRAME_BYTES 256
#define SOUTHERN_CREATURE_ART_PORTRAIT_BYTES 1024
#define SOUTHERN_CREATURE_ART_DIRECTION_COUNT 4
#define SOUTHERN_CREATURE_ART_WALK_FRAME_COUNT 4
#define SOUTHERN_CREATURE_ART_ABILITY_FRAME_COUNT 2
enum {{ {upper} }};
/* Stable, noncontiguous form IDs: 25,26,28,29,79,80,81,82,83,84,85,86,87,88,89,90,91,92,93,94.
 * Directions: down/up/left/right. Four walk beats, two cast poses per direction.
 * Native row-major 8bpp palette indices. Transparent zero. Field anchor (8,8).
 * Existing 178-entry game_palette, no runtime palette mutation or buffers.
 * All art lives in const ROM: no mutable data/BSS. No gameplay unlocks.
 */
extern const unsigned char southern_creature_form_ids[SOUTHERN_CREATURE_ART_COUNT];
extern const unsigned char southern_creature_direction_frames[SOUTHERN_CREATURE_ART_COUNT][4][4][256];
extern const unsigned char southern_creature_ability_frames[SOUTHERN_CREATURE_ART_COUNT][4][2][256];
extern const unsigned char southern_creature_portraits[SOUTHERN_CREATURE_ART_COUNT][1024];
/* Unsupported IDs return -1/NULL. Invalid direction or pose returns NULL. */
int southern_creature_art_index(unsigned int form_id);
const unsigned char *southern_creature_art_frame(unsigned int form_id,unsigned int direction,unsigned int frame);
const unsigned char *southern_creature_art_ability_frame(unsigned int form_id,unsigned int direction,unsigned int pose);
const unsigned char *southern_creature_art_portrait(unsigned int form_id);
#endif
'''
    (SRC/'southern_creature_art.h').write_text(header)
    buf=io.StringIO();buf.write('const unsigned char southern_creature_form_ids[20] = {'+','.join(map(str,FORM_IDS))+'};\n\n')
    base.emit_image_tensor(buf,'southern_creature_direction_frames',fields,[20,4,4,256])
    base.emit_image_tensor(buf,'southern_creature_ability_frames',abilities,[20,4,2,256])
    base.emit_image_tensor(buf,'southern_creature_portraits',portraits,[20,1024])
    chunks=[];lines=[];size=0
    for line in buf.getvalue().splitlines(keepends=True):
        n=len(line.encode())
        if lines and size+n>30000:chunks.append(''.join(lines));lines=[];size=0
        lines.append(line);size+=n
    if lines:chunks.append(''.join(lines))
    folder=SRC/'southern_creature_art_data';folder.mkdir(exist_ok=True)
    for old in folder.glob('part_*.inc'):old.unlink()
    for i,chunk in enumerate(chunks):(folder/f'part_{i:03d}.inc').write_text(chunk)
    code='#include "southern_creature_art.h"\n/* Generated original ROM pixels. */\n'
    code+=''.join(f'#include "southern_creature_art_data/part_{i:03d}.inc"\n' for i in range(len(chunks)))
    code+='\nint southern_creature_art_index(unsigned int form_id) {\n    switch(form_id) {\n'
    code+=''.join(f'    case {id}: return SOUTHERN_CREATURE_{key.upper()};\n' for id,key in zip(FORM_IDS,KEYS))
    code+='''    default: return -1;
    }
}
const unsigned char *southern_creature_art_frame(unsigned int form_id,unsigned int direction,unsigned int frame) {
    int i=southern_creature_art_index(form_id);
    if(i<0 || direction>=4 || frame>=4) return (const unsigned char *)0;
    return southern_creature_direction_frames[i][direction][frame];
}
const unsigned char *southern_creature_art_ability_frame(unsigned int form_id,unsigned int direction,unsigned int pose) {
    int i=southern_creature_art_index(form_id);
    if(i<0 || direction>=4 || pose>=2) return (const unsigned char *)0;
    return southern_creature_ability_frames[i][direction][pose];
}
const unsigned char *southern_creature_art_portrait(unsigned int form_id) {
    int i=southern_creature_art_index(form_id);
    return i<0 ? (const unsigned char *)0 : southern_creature_portraits[i];
}
'''
    (SRC/'southern_creature_art.c').write_text(code)
    return [len(c.encode()) for c in chunks]


MOTIONS=(
 'Wide-toed gecko alternates splayed feet while the coil of its long tail sways',
 'Lean gliding gecko crouches, opens attached flank membranes, hops and settles',
 'Compact dune mammal pushes off long hind feet and rocks its big ears',
 'Longer dune digger plants broad forefeet and scoops into a low forward bound',
 'Flying fish skims low, alternately planting paired pectoral fins and forked tail',
 'Sail-finned fish banks its longer body through a high open V of connected fins',
 'Round frog breathes through a pale single pouch and makes deliberate webfoot hops',
 'Broad frog braces wide hind feet, rears, gathers paired throat folds and exhales',
 'Low crab sidesteps on alternating legs; stalk eyes lead unequal soft claws',
 'High-vault crab struts on long legs above its visible suspended abdomen',
 'Thin mantis advances four walking legs while long forearms gather and open',
 'Long-abdomen mantis high-steps beneath broad crescent forearm foils',
 'Tree mammal countersteps under two large living tail tufts with small reaching hands',
 'Long-armed tree mammal hangs beneath a raised open tail loop and counterbalances',
 'Broad-smiling newt crawls with opposing knuckles and a swaying flat tail',
 'Newt lifts frilled elbows beneath a continuous dorsal veil and fans its tail',
 'Fruit bat quickly flaps linked fingers, pauses with tucked toes, then folds',
 'Broad fruit bat opens a shallow W, lands on long toes and slowly folds fingers',
 'Long-snouted tenrec noses forward with a quick low trot under its quill crest',
 'Slim tenrec rises onto long hind legs, pivots its separated quill fan and settles')
SCENE_SOURCES=(('GRASS','assets/southern_region/frondshore_commons.png',(276,262,300,286)),
 ('WATER','assets/southern_region/sunlace_anchorage.png',(32,287,56,311)),
 ('PLASTER','assets/southern_region/sunlace_anchorage.png',(40,96,64,120)),
 ('WOOD','assets/southern_region/awning_loft.png',(136,120,160,144)))

def legacy_fields():
    # Read-only import of released authors. Never regenerate or modify their art.
    def load(name):
        sp=importlib.util.spec_from_file_location('southern_compare_'+name,ROOT/'assets'/('generate_'+name+'.py'));m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m
    campaign=load('campaign');campaign.Art=Art;campaign.P=P;campaign.PAL=PAL;campaign.RGB=RGB;evolution=load('evolutions');regional=load('regional_creatures');north=load('northern_creatures')
    rows=[(1,'Homura',base.fox_direction),(4,'Midori',base.leaf_direction),(7,'Fuuri',campaign.fuuri),(10,'Kohaku',campaign.kohaku)]
    for m in (evolution,regional,north):rows.extend(zip(m.FORM_IDS,m.NAMES,m.FIELD_FUNCTIONS))
    return sorted(rows)

def make_comparison(fields):
    before=legacy_fields();rows=[(id,name,[fn(d,0).im for d in DIRECTIONS]) for id,name,fn in before]
    rows += [(id,name,[fields[i][d][0].im for d in range(4)]) for i,(id,name) in enumerate(zip(FORM_IDS,NAMES))]
    sheet=Image.new('RGB',(560,278),RGB[P['dirt4']]);draw=ImageDraw.Draw(sheet);draw.text((6,4),'41 FORMS / RELEASED21 + SOUTHERN20 / NATIVE BLACK SILHOUETTES / ART ONLY',fill=RGB[P['ink']])
    for i,(id,name,frames) in enumerate(rows):
        x=i%7*80;y=22+i//7*42;draw.text((x+4,y),str(id),fill=RGB[P['ink']])
        for j,im in enumerate(frames):sheet.paste(Image.new('RGB',(16,16),RGB[P['ink']]),(x+4+j*18,y+13),mask(im))
    save_review(sheet,OUT/'prior21_silhouettes_native.png')
    current=[mask(row[0][0].im).tobytes() for row in fields];old=[mask(frames[0]).tobytes() for _,_,frames in rows[:21]]
    assert len(set(current))==20 and not set(current).intersection(old)
    nearest=[]
    for i,m in enumerate(current):
        pool=[(FORM_IDS[j],n) for j,n in enumerate(current) if j!=i]+[(before[j][0],n) for j,n in enumerate(old)]
        distance,id=min((sum(x!=y for x,y in zip(m,n)),id) for id,n in pool)
        nearest.append({'form_id':FORM_IDS[i],'nearest_form_id':id,'different_mask_pixels':distance})
    return {'prior_form_ids':[r[0] for r in before],'current_unique_masks':20,'cross_release_mask_matches':0,'nearest_front_mask_distance':nearest}

def make_previews(fields,abilities,portraits):
    concept_sheet();provenance=[];patches=[]
    for name,rel,box in SCENE_SOURCES:
        p=ROOT/rel
        with Image.open(p) as im:patches.append(im.convert('RGB').crop(box))
        provenance.append({'terrain':name,'path':rel,'crop':list(box),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
    for i,key in enumerate(KEYS):
        w=Art(64,64,'transparent').im;c=Art(32,64,'transparent').im
        for d in range(4):
            for f in range(4):w.paste(fields[i][d][f].im,(16*f,16*d))
            for p in range(2):c.paste(abilities[i][d][p].im,(16*p,16*d))
        save_indexed(w,OUT/f'{key}_walk.png');save_indexed(c,OUT/f'{key}_ability.png');save_indexed(portraits[i].im,OUT/f'{key}_portrait.png')
        native=Image.new('RGB',(240,166),RGB[P['deep']]);nd=ImageDraw.Draw(native);nd.text((4,3),f'{FORM_IDS[i]} {NAMES[i]} / ART ONLY',fill=RGB[P['white']]);paste(native,portraits[i],(204,28))
        for bg,y in (('deep',24),('dirt4',100)):
            nd.rectangle((0,y-2,199,y+65),fill=RGB[P[bg]])
            for d in range(4):
                for f,sp in enumerate(fields[i][d]+abilities[i][d]):paste(native,sp,(4+f*30,y+d*16))
        save_review(native,OUT/f'{key}_native.png')
        terrain=Image.new('RGB',(576,112),RGB[P['deep']]);td=ImageDraw.Draw(terrain)
        for t,(name,_,_) in enumerate(SCENE_SOURCES):
            td.text((t*144+2,1),name+' / '+str(FORM_IDS[i]),fill=RGB[P['white']])
            for d in range(4):
                for f,sp in enumerate(fields[i][d]+abilities[i][d]):
                    tile=patches[t].copy();paste(tile,sp,(4,4));terrain.paste(tile,(t*144+f*24,16+d*24))
        save_review(terrain,OUT/f'{key}_terrain_native.png')
        anim=[]
        for frame in range(6):
            tile=Image.new('RGB',(128,48),RGB[P['dirt4']]);dr=ImageDraw.Draw(tile);dr.text((2,1),NAMES[i],fill=RGB[P['ink']])
            for d in range(4):paste(tile,(fields[i][d]+abilities[i][d])[frame],(8+d*30,23))
            anim.append(tile)
        anim[0].save(OUT/f'{key}_motion.gif',save_all=True,append_images=anim[1:],duration=[170,110,110,110,240,220],loop=0,disposal=2,optimize=False)
    return provenance

def validate_pixels(fields,abilities,portraits):
    allimgs=[s.im for forms in (fields,abilities) for row in forms for direction in row for s in direction]+[p.im for p in portraits]
    for im in allimgs:
        assert im.mode=='P' and im.getpalette()==PAL and im.size in ((16,16),(32,32))
        assert 0 in im.tobytes() and max(im.tobytes())<97
    distinct=[];pairdist=[]
    for i,row in enumerate(fields):
        for d in range(4):
            walk=[s.im for s in row[d]];cast=[s.im for s in abilities[i][d]]
            assert len({s.tobytes() for s in walk+cast})==6,(NAMES[i],DIRECTIONS[d],'six poses')
            assert len({mask(s).tobytes() for s in walk})==4,(NAMES[i],DIRECTIONS[d],'four walk masks')
            assert len({mask(s).tobytes() for s in cast})==2,(NAMES[i],DIRECTIONS[d],'two cast masks')
            assert all(45<=sum(bool(n) for n in s.tobytes())<=230 for s in walk+cast)
        assert len({s[0].im.tobytes() for s in row})==4,(NAMES[i],'four views')
        assert all(row[3][f].im.tobytes()==row[2][f].im.transpose(Image.Transpose.FLIP_LEFT_RIGHT).tobytes() for f in range(4)),(NAMES[i],'side symmetry')
        assert portraits[i].im.tobytes()!=row[0][0].im.resize((32,32),Image.Resampling.NEAREST).tobytes()
        assert sum(bool(n) for n in portraits[i].im.tobytes())>250
        distinct.append(len({mask(r[0].im).tobytes() for r in row}))
        if i%2:pairdist.append([sum(a!=b for a,b in zip(mask(fields[i-1][d][0].im).tobytes(),mask(row[d][0].im).tobytes())) for d in range(4)])
    assert len({mask(p.im).tobytes() for p in portraits})==20
    return {'images':500,'field_dimensions':[20,4,4,256],'ability_dimensions':[20,4,2,256],'portrait_dimensions':[20,1024],
      'palette_entries':178,'existing_actor_palette_only':True,'palette_indices':sorted({n for im in allimgs for n in im.tobytes()}),
      'transparent_zero':True,'native_field_footprint':[16,16],'distinct_walk_silhouettes_per_direction':4,'cast_poses_per_direction':2,
      'distinct_direction_silhouettes':distinct,'evolution_different_mask_pixels_by_direction':pairdist,
      'exact_bilateral_side_symmetry':True,'independently_authored_portraits':True}

def output_hashes():
    files=sorted(p for p in OUT.iterdir() if p.is_file() and p.name!='validation.json')
    files+=sorted((SRC/'southern_creature_art_data').glob('*.inc'))+[SRC/'southern_creature_art.c',SRC/'southern_creature_art.h']
    return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
def generate():
    OUT.mkdir(exist_ok=True);fields=[[[fn(d,f) for f in range(4)] for d in DIRECTIONS] for fn in FIELD_FUNCTIONS];abilities=[[[fn(d,p) for p in range(2)] for d in DIRECTIONS] for fn in ABILITY_FUNCTIONS];portraits=[fn() for fn in PORTRAIT_FUNCTIONS]
    validation=validate_pixels(fields,abilities,portraits);comparison=make_comparison(fields);chunks=emit_code(fields,abilities,portraits);sources=make_previews(fields,abilities,portraits)
    sizes={p.name:p.stat().st_size for p in sorted(OUT.glob('*.png'))};assert max(sizes.values())<30000
    manifest={'schema_version':1,'generator':'assets/generate_southern_creatures.py','form_ids':list(FORM_IDS),'names':list(NAMES),'directions':list(DIRECTIONS),
       'status':'ART ONLY. Native rendering, acquisition, catalog enablement and gameplay powers require independent integration acceptance.',
       'rights':'Original code-native pixel geometry. No extracted Nintendo or other game art, tracing, downloaded raster reference, or raster-generated creature input.',
       'palette_sha256':hashlib.sha256(json.dumps(base.COLORS).encode()).hexdigest(),'data_bytes':143380,'runtime_data_bytes':0,'runtime_bss_bytes':0,
       'persistent_obj_allocation_bytes':0,'rom_budget_bytes':174080,'include_bytes':chunks,'max_include_bytes':max(chunks),'scene_review_sources':sources,
       'anchor':[8,8],'frame_ticks_suggestion':8,'ability_poses':['anticipation','recovery'],'motions':list(MOTIONS),'png_sizes':sizes,'validation':validation,'silhouette_comparison':comparison}
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');(OUT/'CREDITS.txt').write_text(manifest['rights']+'\nAll art authored at native16×16 or32×32 in Python/Pillow; existing178-color RGB555 palette preserved.\nNative previews are art composites, never emulator evidence or acquisition proof.\n')
    return manifest

def verify(manifest):
    before=output_hashes();generate();assert before==output_hashes(),'Nondeterministic regeneration'
    report={'deterministic_regeneration':True,'pixel_validation':manifest['validation'],'output_sha256':output_hashes()}
    with tempfile.TemporaryDirectory(prefix='southern-art-') as td:
        td=Path(td);arm=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc'
        if not arm.exists():
            found=shutil.which('arm-none-eabi-gcc');assert found,'ARM toolchain missing';arm=Path(found)
        obj=td/'southern_art.o';subprocess.run([str(arm),'-std=c99','-mcpu=arm7tdmi','-mthumb','-O2','-ffreestanding','-fno-builtin','-fstack-usage','-Wall','-Wextra','-Werror','-c',str(SRC/'southern_creature_art.c'),'-o',str(obj)],check=True,capture_output=True)
        size=subprocess.check_output([str(arm).replace('gcc','size'),str(obj)],text=True);sections=list(map(int,size.splitlines()[-1].split()[:3]));assert sections[1:]==[0,0] and sections[0]<=174080
        stack=[int(line.split('\t')[1]) for p in td.glob('*.su') for line in p.read_text().splitlines()];assert stack and max(stack)<=24
        report.update({'arm_compile':'passed','arm_rom_object_bytes':sections[0],'arm_data_bytes':sections[1],'arm_bss_bytes':sections[2],'max_arm_stack_bytes':max(stack),'max_include_bytes':manifest['max_include_bytes']})
    (OUT/'validation.json').write_text(json.dumps(report,indent=2)+'\n');return {k:v for k,v in report.items() if k not in ('output_sha256','pixel_validation')}
def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--verify',action='store_true');parser.add_argument('--concept',action='store_true');args=parser.parse_args()
    if args.concept:concept_sheet();return
    manifest=generate();print(json.dumps(verify(manifest) if args.verify else {'generated_forms':FORM_IDS,'data_bytes':manifest['data_bytes'],'max_include_bytes':manifest['max_include_bytes']},indent=2))
if __name__=='__main__':main()
