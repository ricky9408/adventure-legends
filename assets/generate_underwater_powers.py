#!/usr/bin/env python3
"""Original code-native Underwater command glyphs; no sampled/extracted art.
The glyph is a floating cast emblem; native collision uses the tiny particles.
"""
from pathlib import Path
import math
from generate_assets import P, PAL
ROOT=Path(__file__).resolve().parents[1]
# Deliberately authored16x16 motifs, eight families x3 differentiated signs.
paths=[
 [(2,5),(13,5),(13,10),(7,10),(9,8)],
 [(2,3),(6,7),(2,11),None,(13,3),(9,7),(13,11)],
 [(2,2),(5,2),(5,5),(2,5),(2,2),None,(10,2),(13,2),(13,5),(10,5),(10,2),None,(10,10),(13,10),(13,13),(10,13),(10,10),None,(2,10),(5,10),(5,13),(2,13),(2,10)],
 [(3,8),(5,4),(10,3),(13,6),(11,11),(5,12),(3,8),None,(7,6),(7,10),(5,8)],
 [(3,3),(12,3),(12,12),(3,12),None,(3,9),(7,9),(5,7)],
 [(2,3),(6,3),(6,7),(2,7),(2,3),None,(9,8),(13,8),(13,12),(9,12),(9,8),None,(7,2),(7,13)],
 [(3,12),(3,3),(11,3),(11,8),(7,8)],
 [(3,12),(3,3),(12,12),None,(3,8),(7,11),(12,12)],
 [(2,4),(7,4),None,(8,8),(13,8),None,(2,12),(7,12)],
 [(3,12),(3,3),(12,3),None,(6,10),(6,6),(11,6)],
 [(2,4),(13,4),None,(2,11),(13,11),None,(9,6),(12,8),(9,9)],
 [(2,2),(13,2),(13,13),(2,13),(2,2),None,(4,5),(6,5),(6,9),(4,9),(4,5),None,(9,4),(11,4),(11,8),(9,8),(9,4)],
 [(2,8),(5,3),(9,12),(13,7)],
 [(2,7),(4,3),(8,2),None,(13,8),(11,12),(7,13)],
 [(2,11),(5,7),(9,9),(13,3),None,(9,3),(13,3),(13,7)],
 [(7,2),(9,6),(13,6),(10,9),(11,13),(7,11),(3,13),(4,9),(1,6),(5,6),(7,2)],
 [(2,6),(6,6),(6,3),(9,3),(9,6),(13,6),None,(2,9),(6,9),(6,12),(9,12),(9,9),(13,9)],
 [(2,3),(7,5),(4,10),(13,12)],
 [(2,3),(7,3),(7,11),(13,11),None,(2,6),(4,6),None,(10,8),(13,8)],
 [(2,12),(7,7),(13,7),None,(7,7),(11,2)],
 [(7,7),(3,6),(2,3),(5,2),(7,7),(12,4),(14,8),(12,12),(8,11),(7,7)],
 [(3,2),(3,13),None,(3,3),(10,3),None,(3,6),(10,6),None,(3,9),(10,9),None,(3,12),(10,12)],
 [(2,2),(13,2),(13,13),(2,13),(2,2),None,(4,2),(13,11),None,(2,5),(10,13)],
 [(7,1),(14,13),(1,13),(7,1),None,(6,7),(9,7),(9,10),(6,10),(6,7)]
]
colors=[(P['water3'],P['watergleam'])]*3+[(P['dirt3'],P['gold4'])]*3+[(P['pine5'],P['mint'])]*3+[(P['gold2'],P['gold4'])]*3+[(P['fire2'],P['fire3'])]*3+[(P['pine5'],P['mint'])]*3+[(P['silver'],P['white'])]*3+[(P['water3'],P['watergleam'])]*3

def line(im,a,b,c):
 x,y=a;tx,ty=b;dx=abs(tx-x);dy=-abs(ty-y);sx=1 if x<tx else -1;sy=1 if y<ty else -1;err=dx+dy
 while True:
  im[y][x]=c
  if (x,y)==(tx,ty):break
  e=err*2
  if e>=dy:err+=dy;x+=sx
  if e<=dx:err+=dx;y+=sy

def tiled(im):
 h=len(im);w=len(im[0]);return [im[y+j][x+i] for y in range(0,h,8) for x in range(0,w,8) for j in range(8) for i in range(8)]
marks=[];particles=[]
for i,path in enumerate(paths):
 im=[[0]*16 for _ in range(16)];prev=None
 for pt in path:
  if pt is not None:
   if prev is not None:line(im,prev,pt,colors[i][0])
   im[pt[1]][pt[0]]=colors[i][1]
  prev=pt
 marks.append(tiled(im))
 pair=[]
 for active in (0,1):
  sm=[[0]*8 for _ in range(8)]
  # Only2x2 pixels are opaque: safe apertures never get an8px visual blob.
  sm[3][3]=colors[i][0];sm[4][4]=colors[i][1]
  if active:sm[3][4]=sm[4][3]=colors[i][1]
  pair.append(tiled(sm))
 particles.append(pair)
out=['#include "underwater_power_art.h"','const unsigned char underwater_power_marks[24][256]={']
out+=[' {'+','.join(map(str,a))+'},' for a in marks];out+=['};','const unsigned char underwater_power_particles[24][2][64]={']
out+=[' {'+','.join('{'+','.join(map(str,a))+'}' for a in pair)+'},' for pair in particles];out+=['};']
(ROOT/'src/underwater_power_art.c').write_text('\n'.join(out)+'\n')
# Deterministic integer orbit table is ROM geometry, not a rendered sprite.
orb=['/* Original radius16 five-tip rotation, inclusive0..72 degrees. ROM only. */','static const signed char underwater_tip_orbit[16][5][2]={']
for t in range(16):orb.append(' {'+','.join('{%d,%d}'%(round(16*math.cos((t/15*72+j*72)*math.pi/180)),round(16*math.sin((t/15*72+j*72)*math.pi/180))) for j in range(5))+'},')
orb.append('};');(ROOT/'src/underwater_tip_orbit.inc').write_text('\n'.join(orb)+'\n')
if __name__=='__main__':
 from PIL import Image,ImageDraw
 # Native-size and integer-enlarged review sheet, not player-facing spoiler art.
 palette=[tuple(PAL[i:i+3]) for i in range(0,len(PAL),3)]
 sheet=Image.new('RGB',(192,96),(14,33,49));draw=ImageDraw.Draw(sheet)
 for i,path in enumerate(paths):
  im=Image.new('RGB',(16,16),(14,33,49));data=marks[i]
  for y in range(16):
   for x in range(16):
    c=data[(y//8*2+x//8)*64+y%8*8+x%8]
    if c:im.putpixel((x,y),palette[c])
  x=(i%8)*24+4;y=(i//8)*32;sheet.paste(im,(x,y));draw.text((x,y+17),str(i+67),fill=(220,233,240))
 outdir=ROOT/'build/underwater-powers-art';outdir.mkdir(parents=True,exist_ok=True)
 sheet.save(outdir/'glyphs-1x.png');sheet.resize((768,384),Image.Resampling.NEAREST).save(outdir/'glyphs-4x.png')
 print('Original Underwater glyphs:24 x (256+128) ROM bytes; zero new resident OBJ bytes')
