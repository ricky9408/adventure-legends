#!/usr/bin/env python3
"""Original, deterministic code-native optional-trial pixel art.

Uses the existing exact GBA palette; never imports or traces outside art.
Run from any cwd: python assets/generate_trials.py. Generated include chunks
are <=32000 bytes. All background/actor state lives in ROM, not RAM copies.
"""
from pathlib import Path
import importlib.util, json, hashlib, random, sys
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]; OUT=ROOT/'assets/trials'; OUT.mkdir(exist_ok=True)
spec=importlib.util.spec_from_file_location('base',ROOT/'assets/generate_assets.py');B=importlib.util.module_from_spec(spec);spec.loader.exec_module(B)
Art=B.Art;P=B.P;PAL=B.PAL
AIDS=[(184,280,0),(296,208,0),(320,72,0),(80,136,1),(400,136,1),(304,280,1)]
VANES=[(88,64),(88,112),(168,112)];PLATES=[(88,56),(152,104)]

def diamond(a,x,y,r,c):a.p([(x,y-r),(x+r,y),(x,y+r),(x-r,y)],c)
def ellipse(a,box,c,w=1):a.d.ellipse(box,outline=P[c],width=w)
def cloud(a,x,y,w):
 a.e((x,y+3,x+w,y+13),'water4');a.e((x+6,y,x+w-10,y+11),'watergleam');a.r((x+7,y+4,x+w-6,y+9),'watergleam')
def border(a,sky):
 for x in (8,228):
  a.r((x,28,x+3,148),'blue1' if sky else 'wood1')
  a.r((x+1,28,x+2,148),'blue2' if sky else 'wood3')
 for x in (14,216):
  for y in (46,142):
   a.r((x,y,x+8,y+5),'bg_temple_stone2' if sky else 'wood2');a.r((x+1,y,x+7,y+2),'bg_temple_stone5' if sky else 'wood5')
 for x in (12,136):
  a.r((x,149,x+91,155),'bg_temple_stone1' if sky else 'wood1');a.r((x,149,x+91,150),'bg_temple_stone5' if sky else 'wood4')
 for y in (140,144,148,152):a.r((105,y,134,y+1),'bg_temple_stone2' if sky else 'wood2')
 a.l([(111,145),(119,150),(128,145)],'teal1' if sky else 'gold2')
def spool(a,x,y,c):
 a.r((x-3,y-5,x+3,y+5),'wood2');a.r((x-4,y-5,x+4,y-4),'gold3');a.r((x-4,y+4,x+4,y+5),'gold3')
 for yy in range(y-2,y+4,2):a.r((x-2,yy,x+2,yy),c)
def wind_background():
 a=Art(240,160,'blue3');cloud(a,-15,24,62);cloud(a,188,80,76);cloud(a,-18,132,54)
 # The full-screen view includes a distant sky garden and suspended cloths.
 cloud(a,66,3,62);cloud(a,174,5,74)
 a.l([(0,13),(52,7),(112,10),(169,5),(239,13)],'wood2')
 for x,y,col in [(21,11,'gold3'),(42,9,'flower0'),(68,8,'watergleam'),(96,10,'gold3'),(121,9,'flower0'),(205,10,'gold3'),(224,12,'watergleam')]:
  a.p([(x,y),(x+6,y),(x+6,y+7),(x+3,y+10),(x,y+7)],col);a.l([(x+1,y+2),(x+4,y+2)],'gold4')
 for x in (4,232):
  a.l([(x,28),(x+2,20),(x+1,13)],'bg_sunlit_pine1',2)
  for dx,yy in [(-3,17),(3,19),(-2,23),(3,26)]:a.e((x+dx-3,yy-2,x+dx+3,yy+1),'bg_sunlit_pine4')

 a.r((12,44,227,148),'bg_temple_stone4')
 # Large interlocking pale tesserae. Airy and quiet around playable mechanisms.
 for y in range(46,146,16):
  for x in range(16+(8 if y%32==14 else 0),228,24):
   a.l([(x,y),(min(x+19,226),y)],'bg_temple_stone3');a.dot(x+1,y+1,'bg_temple_stone5')
 for x,y in [(28,67),(209,106),(117,53),(119,124),(44,95)]:
  a.l([(x-5,y+2),(x+5,y+2),(x+8,y),(x+7,y-3),(x+4,y-3)],'bg_temple_stone3');a.l([(x-4,y+5),(x+8,y+5)],'bg_temple_stone5')
 # Top wall is a hand-built weaving bench, outside player foot bounds.
 a.r((12,25,227,43),'bg_temple_stone1');a.r((13,26,226,29),'bg_temple_stone5');a.r((14,30,225,41),'blue2')
 for x in (24,57,200,221):
  a.r((x-4,27,x+4,43),'bg_temple_stone2');a.r((x-3,27,x+2,30),'bg_temple_stone5')
 for x,col in [(35,'teal2'),(46,'flower0'),(70,'gold4')]:spool(a,x,35,col)
 # Tapestry loom: a sunlit wooden frame and many visible warp threads.
 a.r((138,25,184,43),'wood1');a.r((140,27,182,42),'wood3')
 for x in range(144,181,4):a.l([(x,29),(x,42)],'gold4')
 for y in range(31,43,3):a.l([(144,y),(180,y)],'teal1' if y%2 else 'flower0')
 for x in (135,185):a.r((x,24,x+3,45),'wood4');a.dot(x+1,24,'gold4')
 # An unfinished cloth curls around the receiver, separate from the beam.
 a.p([(152,42),(177,42),(180,54),(173,59),(154,54)],'blue2')
 a.l([(155,45),(173,45),(174,51)],'gold3');a.l([(156,48),(172,48),(173,53)],'gold4')
 # Faded inlaid thread joins the courtyard's three working stands.
 a.l([(40,64),(88,64),(88,112),(168,112),(168,49)],'bg_temple_stone2',3)
 a.l([(40,64),(88,64),(88,112),(168,112),(168,49)],'water4')
 for x,y in VANES:
  ellipse(a,(x-13,y-10,x+13,y+10),'bg_temple_stone2');ellipse(a,(x-11,y-8,x+11,y+8),'bg_temple_stone5')
  for dx,dy in [(0,-13),(14,0),(0,12),(-14,0)]:diamond(a,x+dx,y+dy,1,'gold1')
 # West wind-mouth, fluted shell and feather-like intake strokes.
 a.p([(24,57),(32,54),(39,59),(43,64),(39,69),(32,73),(24,71)],'bg_temple_stone1')
 a.p([(25,58),(31,56),(38,60),(40,64),(37,68),(29,69)],'bg_temple_stone5')
 for y in (59,63,67):a.l([(29,y),(36,y+1)],'water2')
 # Side gardens are inlaid low-growing vines, never invisible collision.
 for x in (19,219):
  for y in range(79,105,6):
   a.l([(x,y+5),(x+2,y)],'bg_sunlit_pine2');a.e((x-2,y,x+1,y+2),'bg_sunlit_pine4');a.dot(x+3,y+1,'flower1')
 # Reset plinth and return trail are pictorial and visually separate.
 ellipse(a,(20,113,44,129),'bg_temple_stone2');a.l([(33,132),(33,139),(97,139)],'bg_temple_stone3')
 border(a,True);return a

def stone_background():
 a=Art(240,160,'bg_twilight_dusk2');a.r((12,44,227,148),'bg_sunlit_dirt3')
 # Warm geode masonry continues into the newly full-screen upper view.
 a.r((12,0,227,23),'bg_twilight_dusk3')
 for x in range(14,226,24):
  a.p([(x,1),(x+18,1),(x+22,9),(x+18,21),(x+2,22),(x-1,13)],'bg_twilight_dusk2')
  a.l([(x+2,3),(x+15,2),(x+18,6)],'bg_twilight_dusk4')
 for x in (28,119,213):
  a.l([(x,0),(x,7)],'wood1');diamond(a,x,13,6,'gold1');diamond(a,x,12,4,'gold3');diamond(a,x,12,2,'gold4')
 a.l([(13,22),(226,22)],'wood1');a.l([(14,23),(225,23)],'gold2')

 for y in range(46,149,16):
  for x in range(15,227,24):
   a.l([(x,y),(min(x+18,226),y)],'bg_sunlit_dirt2');a.l([(x+2,y+1),(min(x+17,225),y+1)],'bg_sunlit_dirt4')
 # Thick workshop wall, engraved beams, chisel rack and shelves.
 a.r((12,24,227,43),'wood1');a.r((13,25,226,28),'wood5');a.r((14,30,225,41),'wood3')
 for x in range(16,220,18):a.l([(x,31),(x+6,39)],'wood2')
 for x in (22,64,112,174,217):
  a.r((x,26,x+4,43),'wood1');a.r((x+1,26,x+2,40),'wood5')
 for x in (35,43,51):
  a.r((x,29,x+1,36),'stone1');a.r((x-2,35,x+3,37),'stone4');a.dot(x,29,'gold4')
 for x in (79,92,127,140):
  a.r((x-4,31,x+4,39),'wood1');a.r((x-3,32,x+3,36),'gold1');a.l([(x-3,33),(x+2,33)],'gold3')
 # The amber arch is monumental at the wall, with a reachable working seal.
 a.r((182,26,217,44),'stone1');a.r((184,28,215,43),'gold1');a.r((187,29,212,42),'wood1')
 a.p([(190,43),(190,34),(195,30),(205,30),(210,34),(210,43)],'bg_twilight_dusk1')
 for x in (185,212):a.r((x,30,x+2,43),'gold3')
 diamond(a,200,32,4,'gold4');diamond(a,200,32,2,'fire2')
 # Sliding board, 7 by 4 exact16px cells; raised rail is a FLAT inlay.
 a.r((62,46,178,114),'wood2');a.r((64,48,176,112),'wood5')
 for row,y in enumerate(range(48,112,16)):
  for col,x in enumerate(range(64,176,16)):
   a.r((x,y,x+15,y+15),'bg_sunlit_stone4' if (row+col)%2 else 'bg_sunlit_stone3')
   a.l([(x,y+15),(x+15,y+15)],'bg_sunlit_stone2');a.l([(x+15,y),(x+15,y+15)],'bg_sunlit_stone2')
   a.dot(x+2,y+2,'bg_sunlit_stone5')
 # Copper signal channels visibly connect BOTH plates to the upper arch seal.
 a.l([(88,56),(88,45),(180,45),(180,59),(200,59)],'wood1',3)
 a.l([(88,56),(88,45),(180,45),(180,59),(200,59)],'gold3')
 a.l([(152,104),(184,104),(184,70),(200,70)],'wood1',3)
 a.l([(152,104),(184,104),(184,70),(200,70)],'gold2')
 for x,y in PLATES:
  a.r((x-7,y-7,x+7,y+7),'stone2');a.r((x-5,y-5,x+5,y+5),'gold0');diamond(a,x,y,4,'gold3');diamond(a,x,y,2,'wood1')
 # Outlined launch bays show that these parcels belong to the rail board.
 for x in (88,136):
  a.l([(x-5,84),(x-5,82),(x-2,82)],'wood2');a.l([(x+5,92),(x+5,94),(x+2,94)],'wood2')
 ellipse(a,(188,54,212,76),'gold1');ellipse(a,(190,56,210,74),'gold3')
 # Sawdust curls, stone samples, and low mosaic tool silhouettes flank board.
 for x,y in [(39,63),(30,91),(207,99),(207,132),(58,132)]:
  a.l([(x-4,y),(x+2,y),(x+4,y-3),(x+2,y-5),(x,y-4)],'bg_sunlit_dirt1')
 a.p([(19,65),(23,60),(28,61),(31,66),(26,70),(21,69)],'bg_sunlit_stone3')
 a.l([(21,64),(25,62),(28,66)],'bg_sunlit_stone5')
 ellipse(a,(20,113,44,129),'bg_sunlit_dirt1');a.l([(33,132),(33,139),(97,139)],'bg_sunlit_dirt2')
 border(a,False);return a

def aid_sprite(kind,lit):
 a=Art(16,16,'transparent')
 if kind<3:
  a.e((1,9,14,14),'shadowsoft');a.e((2,9,13,13),'stone1');a.e((3,8,12,11),'stone3')
  if kind==0: # Circular cooking hearth, surviving pot bracket.
   a.r((3,4,4,11),'wood2');a.r((11,4,12,11),'wood2');a.r((4,3,11,4),'stone2');a.r((6,5,9,7),'stone1');a.r((6,5,9,5),'stone4')
  elif kind==1: # Fox-eared bronze brazier.
   a.p([(3,5),(4,2),(6,5),(10,5),(12,2),(12,7),(10,10),(5,10)],'gold0');a.l([(4,5),(11,5)],'gold2');a.r((6,10,9,12),'wood1')
  else: # Cracked miniature kiln.
   a.p([(3,11),(3,5),(6,2),(11,3),(13,6),(12,12)],'wood2');a.p([(4,8),(6,5),(10,5),(11,8),(10,12),(4,12)],'wood1');a.l([(7,3),(8,4),(7,5)],'gold3')
  if lit:
   a.p([(5,11),(5,8),(7,9),(8,5),(10,9),(11,11),(9,13),(6,13)],'fire1');a.p([(6,11),(8,7),(9,10),(9,12),(6,12)],'fire3');a.dot(8,10,'gold4');a.dot(13,4,'gold3')
  else:
   a.l([(5,10),(10,11)],'stone0');a.l([(6,12),(11,9)],'wood0');a.dot(8,8,'stone2')
 else:
  a.e((1,10,14,14),'shadowsoft')
  if kind==3: # Split flower urn.
   a.p([(3,6),(13,6),(11,13),(5,13)],'stone2');a.r((3,5,13,6),'stone4');a.l([(8,7),(7,9),(9,11),(8,13)],'stone0')
  elif kind==4: # Fallen hollow-log planter.
   a.r((3,8,12,13),'wood2');a.e((1,7,6,13),'wood3');a.e((2,8,5,12),'wood1');a.r((5,7,13,9),'wood1');a.l([(7,11),(11,11)],'wood4')
  else: # Weathered seed mosaic.
   a.p([(1,9),(7,6),(14,9),(14,13),(7,15),(1,12)],'stone2');a.p([(3,10),(7,8),(12,10),(7,13)],'moss1');a.l([(8,8),(8,11),(10,12)],'stone0')
  a.l([(8,11),(7,6),(9,3)],'pine2' if lit else 'wood1')
  if lit:
   a.p([(7,8),(3,7),(2,4),(5,4),(8,7)],'pine4');a.p([(8,6),(10,2),(13,3),(12,5)],'leaflight');a.p([(8,10),(11,7),(14,8),(12,10)],'pine5')
   a.e((5,0,9,4),'flower0' if kind==3 else 'gold3');a.dot(7,2,'flower1');a.dot(2,3,'mint')
  else:a.l([(7,6),(4,5),(3,3)],'wood2');a.l([(8,7),(11,6),(12,4)],'wood2');a.dot(9,3,'moss1')
 return a

def vane_sprite(d):
 a=Art(16,16,'transparent');a.e((2,10,13,15),'shadowsoft');a.e((3,9,12,13),'stone2');a.e((4,8,11,11),'gold1');a.r((7,4,8,11),'wood1')
 # Cardinal direction of the bright triangular sail; arrow is obvious at1x.
 u=[(0,-1),(1,0),(0,1),(-1,0)][d];v=(-u[1],u[0]);cx,cy=8,7
 q=lambda forward,side:(cx+u[0]*forward+v[0]*side,cy+u[1]*forward+v[1]*side)
 a.p([q(6,0),q(-3,4),q(-1,0),q(-3,-4)],'teal0');a.p([q(5,0),q(-2,3),q(0,0)],'watergleam');a.p([q(5,0),q(-2,-3),q(0,0)],'gold3');a.dot(8,7,'gold4');return a

def misc_sprite(kind):
 a=Art(16,16,'transparent')
 if kind in (0,1):
  a.r((7,8,8,15),'wood1');a.r((2,2,13,11),'wood1');a.r((3,3,12,10),'blue2' if kind==0 else 'gold1');a.l([(3,3),(12,3)],'gold4')
  if kind==0:a.l([(5,5),(10,5),(11,6),(10,7),(5,7),(4,8),(5,9),(10,9)],'watergleam')
  else:diamond(a,8,7,3,'wood1');diamond(a,8,7,1,'gold4')
 elif kind==2:
  # Mechanical reset lever: cool steel T-handle and two rewind chevrons.
  # Deliberately no orange/yellow glow or flame-like round knob.
  a.e((1,11,14,15),'shadowsoft');a.r((3,11,12,14),'stone1');a.r((4,11,11,12),'stone4')
  a.e((5,7,11,12),'stone0');a.e((6,8,10,11),'stone3')
  a.l([(8,10),(4,3)],'stone0',3);a.l([(7,9),(4,3)],'silver')
  a.r((1,1,7,4),'stone0');a.r((2,1,6,2),'watergleam');a.r((2,3,6,3),'teal1')
  a.p([(10,3),(7,6),(10,9)],'teal0');a.p([(14,3),(11,6),(14,9)],'teal0')
  a.p([(10,4),(8,6),(10,8)],'watergleam');a.p([(14,4),(12,6),(14,8)],'watergleam')
 elif kind==3:
  a.r((1,2,14,15),'shadowsoft');a.r((1,1,13,13),'stone1');a.r((2,2,12,11),'stone3');a.r((2,2,12,3),'stone5');a.r((12,3,13,12),'stone2');a.l([(3,12),(11,12)],'wood2');diamond(a,7,7,4,'gold0');diamond(a,7,7,2,'gold3');a.dot(7,6,'gold4')
 elif kind in (4,5):
  a.r((1,1,14,14),'wood1');a.r((2,1,3,14),'wood4');a.r((12,1,13,14),'wood4');a.r((3,2,12,3),'gold3');a.r((3,11,12,12),'gold3')
  for x in (5,7,9,11):a.l([(x,4),(x,10)],'gold4')
  for y in (5,7,9):a.l([(4,y),(11,y)],'teal2' if kind==5 else 'blue2')
  if kind==5:diamond(a,8,7,3,'gold4');a.dot(8,7,'teal0')
 else:
  a.p([(1,15),(1,6),(4,2),(8,0),(12,2),(15,6),(15,15),(11,15),(11,7),(8,5),(5,7),(5,15)],'gold0');a.l([(2,13),(2,6),(5,3),(8,2),(11,3),(14,6),(14,13)],'gold3');diamond(a,8,8,3,'gold4' if kind==7 else 'stone1');a.dot(8,8,'fire2' if kind==7 else 'stone3')
 return a

def paste(target,a,x,y):target.paste(a.im,(x,y),Image.frombytes('L',a.im.size,bytes(255 if p else 0 for p in a.im.tobytes())))
def beam_preview(a,states):
 a.l([(40,64),(88,64)],'gold4');active=True
 for i,(x,y) in enumerate(VANES):
  if not active:break
  d=states[i];good=d==[2,1,0][i]
  end=[(88,112),(168,112),(168,48)][i] if good else [(x,48),(216,y),(x,136),(24,y)][d]
  a.l([(x,y),end],'gold4');active=good

def emit(arrays):
 text='/* Generated original trial art. Existing palette; ROM-only. */\n'
 for name,shape,items in arrays:
  text+=f'const unsigned char {name}{shape} __attribute__((aligned(4))) = {{\n'
  # Braces are authored from shape dimensions to remain strict-C99 warning-free.
  dims=[int(x) for x in shape.replace(']', '').split('[')[1:]]
  def nest(values,dimensions,indent=0):
   if len(dimensions)==1:return ''.join(' '+','.join(map(str,values[i:i+32]))+',\n' for i in range(0,len(values),32))
   step=1
   for d in dimensions[1:]:step*=d
   return ''.join('{\n'+nest(values[i*step:(i+1)*step],dimensions[1:],indent+1)+'},\n' for i in range(dimensions[0]))
  text+=nest(items,dims)+'};\n'
 chunks=[];chunk=''
 for ln in text.splitlines(True):
  if len((chunk+ln).encode())>32000:chunks.append(chunk);chunk=''
  chunk+=ln
 if chunk:chunks.append(chunk)
 dst=ROOT/'src/trial_art_data';dst.mkdir(exist_ok=True)
 for f in dst.glob('part_*.inc'):f.unlink()
 for i,t in enumerate(chunks):(dst/f'part_{i:03d}.inc').write_text(t)
 (ROOT/'src/trial_art.c').write_text('#include "trial_art.h"\n'+''.join(f'#include "trial_art_data/part_{i:03d}.inc"\n' for i in range(len(chunks))))
 return len(chunks)

def main():
 wind=wind_background();stone=stone_background();aids=[[aid_sprite(i,s) for s in range(2)] for i in range(6)];vanes=[vane_sprite(d) for d in range(4)];misc=[misc_sprite(i) for i in range(8)]
 for name,a in [('wind_loom',wind),('amber_workshop',stone)]:a.im.save(OUT/f'{name}.png');a.im.resize((960,640),Image.Resampling.NEAREST).save(OUT/f'{name}_4x.png')
 for label,states in [('initial',[0,0,0]),('flow',[2,1,0])]:
  scene=wind_background();beam_preview(scene,states)
  for (x,y),d in zip(VANES,states):paste(scene.im,vanes[d],x-8,y-8)
  paste(scene.im,misc[2],24,112);paste(scene.im,misc[5 if label=='flow' else 4],160,40);scene.im.save(OUT/f'wind_{label}.png')
 scene=stone_background()
 for x,y in [(88,88),(136,88)]:paste(scene.im,misc[3],x-8,y-8)
 paste(scene.im,misc[2],24,112);paste(scene.im,misc[6],192,56);scene.im.save(OUT/'stone_initial.png')
 sheet=Image.new('RGB',(720,420),(23,32,57))
 for i,(name,title) in enumerate([('wind_initial','WIND-LOOM COURTYARD'),('stone_initial','AMBER WORKSHOP')]):
  im=Image.open(OUT/f'{name}.png').convert('RGB').resize((480,320),Image.Resampling.NEAREST)
  # Single tall sheet, preserving exact nearest-neighbor2x rendering.
  if i==0:sheet=Image.new('RGB',(976,366),(23,32,57))
  sheet.paste(im,(8+i*488,34));ImageDraw.Draw(sheet).text((12+i*488,12),title,fill=(255,240,175))
 sheet.save(OUT/'contact_sheet.png')
 grove=Image.open(ROOT/'assets/overworld.png').convert('P');grove.putpalette(PAL)
 for i,(x,y,_) in enumerate(AIDS):paste(grove,aids[i][0],x-8,y-8)
 grove.resize((960,640),Image.Resampling.NEAREST).save(OUT/'grove_discovery_preview.png')
 spr=Image.new('P',(16*12,16*3));spr.putpalette(PAL)
 for i in range(6):
  for state in range(2):paste(spr,aids[i][state],i*32+state*16,0)
 for i,a in enumerate(vanes):paste(spr,a,i*16,16)
 for i,a in enumerate(misc):paste(spr,a,i*16,32)
 spr.resize((1152,288),Image.Resampling.NEAREST).save(OUT/'sprites_6x.png')
 flat=lambda arr:[p for a in arr for p in a.im.tobytes()]
 arrays=[('trial_background_wind','[38400]',list(wind.im.tobytes())),('trial_background_stone','[38400]',list(stone.im.tobytes())),('trial_aid_sprites','[6][2][256]',flat([a for pair in aids for a in pair])),('trial_vane_sprites','[4][256]',flat(vanes)),('trial_misc_sprites','[8][256]',flat(misc))]
 chunks=emit(arrays)
 manifest={'art':'Original deterministic code-native pixel art; exact existing nativeGBA palette; no external art','rooms':{'14':{'name':'Wind-loom courtyard','bounds':[12,44,216,104],'entrance':[4,204,64],'return':[204,86],'arrival':[120,132],'reset':[32,120],'vanes':VANES,'source':[40,64],'receiver':[168,48]},'15':{'name':'Amber workshop','bounds':[12,44,216,104],'entrance':[9,208,120],'return':[208,140],'arrival':[120,132],'reset':[32,120],'parcels':[[88,88],[136,88]],'plates':PLATES,'arch':[200,64],'parcel_grid':[72,56,7,4,16]}},'grove_aids':[{'x':x,'y':y,'family':f,'lifetime_bit':i} for i,(x,y,f) in enumerate(AIDS)],'palette_count':len(B.COLORS),'chunks':chunks,'rom_pixel_bytes':sum(len(v) for _,_,v in arrays),'sha256':{n:hashlib.sha256(bytes(v)).hexdigest() for n,_,v in arrays},'reward':'First restoration credits field aid once. Completed personal quest grants180XP and10bond to matching story companion independent of ordinary expedition cap; trial bit prevents repetition. No save5 reserved bytes used.'}
 (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 # Mechanical asset assertions, not claims about emulator gameplay.
 assert all(min(v)>0 for _,_,v in arrays[:2]);assert all(max(v)<len(B.COLORS) for _,_,v in arrays)
 assert all(a.im.tobytes()!=b.im.tobytes() for a,b in aids);assert len({a.im.tobytes() for a in vanes})==4
 assert all(f.stat().st_size<=32000 for f in (ROOT/'src/trial_art_data').glob('*.inc'))
 print(f'Generated {sum(len(v) for _,_,v in arrays)} ROM pixel bytes, {chunks} chunks; palette/transparency/distinct-state assertions passed')
if __name__=='__main__':main()
