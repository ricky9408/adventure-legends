#!/usr/bin/env python3
"""Original shop/entrance artwork, baked into sparse, aligned palette row runs.

No runtime scene construction: both destination halfword alignments have exact
opaque source bytes. The palette and travel footprints remain authoritative.
"""
from pathlib import Path
import hashlib,json,re
from PIL import Image,ImageDraw
import connected_road_art as roads
ROOT=Path(__file__).resolve().parents[1]
PAL={k:int(v)for k,v in re.findall(r'#define PAL_(\w+) (\d+)',(ROOT/'src/assets.h').read_text())}
P=lambda n:PAL[n]
PATH=P('BG_SUNLIT_DIRT3');PALE=P('BG_SUNLIT_STONE4');STONE=P('BG_SUNLIT_STONE2');EDGE=P('BG_SUNLIT_STONE0');TIMBER=P('BG_SUNLIT_WOOD3')
class Painter:
 def __init__(self):self.im=Image.new('P',(480,320),0);self.d=ImageDraw.Draw(self.im)
 def r(self,x,y,w,h,c):
  if w>0 and h>0:self.d.rectangle((x,y,x+w-1,y+h-1),fill=c)
 def l(self,x,y,xx,yy,c):self.d.line((x,y,xx,yy),fill=c,width=1)
 def emblem(self,x,y,kind):
  r,l=self.r,self.l
  if kind=='leaf':r(x-2,y-2,5,4,P('PINE3'));r(x,y-3,3,2,P('MINT'));l(x-2,y+2,x+2,y-2,P('GOLD4'))
  elif kind=='bell':r(x-2,y-3,5,5,P('GOLD2'));r(x-3,y+1,7,1,P('GOLD4'));r(x,y+2,1,1,P('WOOD1'));r(x-1,y-3,1,3,P('GOLD4'))
  elif kind=='wind':l(x-3,y+1,x+2,y-3,P('WHITE'));l(x-3,y+1,x+3,y,P('WHITE'));r(x+2,y-2,2,2,P('WATER3'))
  elif kind=='water':l(x-3,y,x-1,y+1,P('WATER4'));l(x-1,y+1,x+1,y-1,P('WATER4'));l(x+1,y-1,x+3,y,P('WATER4'));r(x-2,y+3,5,1,P('WATER3'))
  else:r(x-2,y-3,5,6,P('WOOD1'));r(x-1,y-2,3,4,P('GOLD3'));r(x,y-1,1,2,P('GOLD4'))
 def step(self,x,y,w,h,warm=False):
  r=self.r;r(x+1,y,w-2,h,P('BG_SUNLIT_DIRT2')if warm else STONE);r(x+3,y,w-6,2,EDGE)
  for i in range(3,h,4):r(x+1,y+i,w-2,1,PALE);r(x+2,y+i+1,w-4,1,P('WOOD3')if warm else P('STONE2'))
  r(x,y+h-1,w,2,PALE);r(x+3,y+h+2,w-6,1,PATH)
 def arch(self,x,y,w,h,kind='lamp',wood=False):
  r=self.r;cx=x+w//2;cy=y+h//2;half=w//2+1;dark=P('WOOD1')if wood else EDGE;mid=TIMBER if wood else STONE
  r(x,y-4,w,h+6,PATH);r(x+2,y+h+2,w-4,2,P('BG_SUNLIT_DIRT4'))
  r(cx-half,cy-17,3,22,dark);r(cx+half-2,cy-17,3,22,dark);r(cx-half,cy-17,1,21,mid);r(cx+half-2,cy-17,1,21,PALE)
  r(cx-half-1,cy+4,5,3,mid);r(cx+half-3,cy+4,5,3,mid);r(cx-half+2,cy-20,2*half-3,4,dark);r(cx-half+3,cy-20,2*half-5,1,PALE)
  r(cx-half+4,cy-23,2*half-7,3,mid);r(cx-half+5,cy-23,2*half-9,1,PALE);r(cx-4,cy-23,9,8,P('PINE1')if wood else P('SLATE'));self.emblem(cx,cy-19,kind)
  r(x+2,cy+2,w-4,1,PALE);r(x+3,cy+5,w-6,2,P('BG_SUNLIT_DIRT2'))
  if kind=='leaf':r(cx-half-2,cy-16,3,4,P('PINE3'));r(cx+half,cy-13,2,3,P('PINE4'))
 def stairs(self,x,y,w,h,down=False,warm=False):
  r=self.r;left=x+1;right=x+w-2;wall=P('WOOD1')if warm else EDGE;light=TIMBER if warm else PALE
  r(left,y,w-2,h,wall);r(left+2,y+1,w-6,h-2,P('DEEP'))
  for i in range(4):
   yy=y+2+i*(h-3)//4;pad=i if down else 3-i;r(left+2+pad,yy,w-6-pad*2,2,light);r(left+2+pad,yy+2,w-6-pad*2,1,P('WOOD2')if warm else P('STONE2'))
  r(left,y-2,2,h+3,light);r(right-1,y-2,2,h+3,light);r(left-1,y-3,4,2,wall);r(right-2,y-3,4,2,wall);r(left+3,y+h,w-8,2,PATH)
 def gangway(self,x,y,w,h,nautical=False):
  r,l=self.r,self.l;cx=x+w//2;r(x,y-3,w,h+8,P('WOOD1'))
  for i in range(-2,h+5,4):r(x+2,y+i,w-4,3,TIMBER);r(x+3,y+i,w-6,1,P('WOOD5'))
  r(x-2,y-8,3,h+9,P('WOOD1'));r(x+w-1,y-8,3,h+9,P('WOOD1'));r(x-2,y-8,2,3,P('WOOD5'));r(x+w-1,y-8,2,3,P('WOOD5'))
  l(x-1,y-5,x-1,y+h-1,P('GOLD1'));l(x+w,y-5,x+w,y+h-1,P('GOLD1'))
  if nautical:r(cx-1,y-26,2,18,P('WOOD1'));l(cx+1,y-24,cx+9,y-13,P('WHITE'));l(cx+9,y-13,cx+1,y-13,P('WHITE'));l(cx+1,y-23,cx+1,y-13,P('WHITE'));r(cx-4,y-9,10,2,P('WATER3'))
 def lift(self,x,y,w,h):
  self.gangway(x,y,w,h);r=self.r;cx=x+w//2;r(x-3,y-22,3,27,EDGE);r(x+w,y-22,3,27,EDGE);r(x-3,y-24,w+6,3,EDGE);r(x-2,y-24,w+4,1,P('GOLD3'))
  r(cx-3,y-25,7,7,P('WOOD1'));r(cx-2,y-24,5,5,P('GOLD2'));r(cx,y-23,1,3,P('GOLD4'));self.l(cx,y-18,cx,y-6,P('GOLD1'));r(cx-4,y-7,9,2,P('WOOD1'))
 def dive(self,x,y,w,h):
  r=self.r;r(x-2,y-6,w+4,h+10,P('WATER2'));r(x,y-4,w,h+6,P('WATER1'))
  for i in range(4):r(x+3,y+i*4,w-6,2,PALE);r(x+3,y+i*4+2,w-6,1,P('WATER3'))
  r(x,y-6,2,h+5,P('GOLD2'));r(x+w-2,y-6,2,h+5,P('GOLD2'));r(x-2,y-7,4,2,P('GOLD4'));r(x+w-2,y-7,4,2,P('GOLD4'))
 def panel(self,x,y,w,h):
  r=self.r;r(x,y,w,h,P('WOOD1'));r(x+1,y+1,w-2,h-2,TIMBER)
  for xx in range(x+3,x+w-1,4):r(xx,y+1,1,h-2,P('WOOD2'))
  r(x+w-3,y+h//2,1,2,P('GOLD4'))
 def shop(self):
  r=self.r;x,y=56,100;r(x-18,y-18,37,3,P('WOOD1'));r(x-20,y-17,41,8,P('WOOD1'))
  for i in range(5):r(x-18+i*8,y-17,7,7,P('GOLD4')if i&1 else P('WATER2'));r(x-18+i*8,y-10,7,3,P('WHITE')if i&1 else P('WATER3'))
  r(x-20,y-8,2,13,P('WOOD1'));r(x+19,y-8,2,13,P('WOOD1'))
  r(x-4,y-10,9,3,P('WOOD1'));r(x-3,y-13,7,3,P('GOLD2'));r(x-5,y-10,11,2,P('GOLD4'))
  r(x-3,y-8,7,6,P('SKIN2'));r(x-2,y-6,1,1,P('INK'));r(x+2,y-6,1,1,P('INK'));r(x-4,y-2,9,5,P('WATER2'));r(x-2,y-2,5,5,P('WATER4'))
  r(x-17,y,35,3,P('WOOD1'));r(x-16,y,33,1,P('WOOD5'));r(x-15,y+2,31,2,TIMBER)
  r(x-12,y-6,3,1,P('GOLD4'));r(x-13,y-5,5,4,P('ROSE3'));r(x-12,y-4,1,2,P('ROSE5'));r(x+9,y-5,6,4,P('GOLD1'));r(x+10,y-6,4,1,P('WOOD1'))
  r(x+20,y-18,7,2,P('WOOD1'));r(x+24,y-16,1,3,P('WOOD1'));r(x+20,y-13,9,9,P('WOOD1'));r(x+21,y-12,7,7,P('GOLD3'));r(x+23,y-11,3,5,P('GOLD1'));r(x+24,y-10,1,3,P('GOLD4'))
 def entry(self,e):
  x,y,w,h=e['footprint'];room,target,action=e['room'],e['target'],e['action']
  if action=='TRAVEL_DIVE':self.dive(x,y,w,h)
  elif action=='TRAVEL_LIFT':self.lift(x,y,w,h)
  elif action=='TRAVEL_FERRY':self.gangway(x,y,w,h,True)
  elif room==0 and action=='TRAVEL_CAMPAIGN':self.stairs(x+1,y,w-2,h,target==9,target==4)
  elif room==0:self.arch(x,y,w,h,'leaf'if target==54 else'lamp',target==54)
  elif (room,target)in[(22,16),(30,22),(38,30)]:self.gangway(x,y,w,h,room!=38)
  elif action=='TRAVEL_RETURN':self.arch(x,y,w,h,'bell'if target==55 else'wind'if target==57 else'lamp'if target==60 else'water',target in(55,57))
  elif action in('TRAVEL_HORIZONS','TRAVEL_UNDERWATER'):self.arch(x,y,w,h,'water')
  elif action=='TRAVEL_REGION'or(room,target)==(16,22):self.arch(x,y,w,h,'leaf'if action=='TRAVEL_REGION'else'wind',True)
  elif action=='TRAVEL_TRIAL':self.arch(x,y,w,h,'wind'if target==14 else'lamp')
  elif (room==22 and target in(24,25))or room in(23,26,27,28,32)or(room,target)in[(30,32),(31,33),(31,34),(36,31),(38,40),(39,41),(39,42)]:self.step(x,y,w,h,room>=30)
  else:self.stairs(x,y,w,h,target<room,30<=room<38)
def pictures(entries):
 rooms={r:Painter()for r in sorted({e['room']for e in entries}|{0,16,17})}
 rooms[0].shop()
 managed={(a['room'],b['room']) for road in roads.DATA['roads'] for a,b in [road['ends'],list(reversed(road['ends']))]}
 managed.update((d['room'],d['target']) for d in roads.DATA['doorways'])
 managed.update(((4,14),(9,15),(39,40),(40,39),(42,43),(43,44),(44,45),(44,39)))
 for e in entries:
  if (e['room'],e['target']) not in managed:rooms[e['room']].entry(e)
 for r,x,y,w,h in[(16,76,115,24,14),(16,332,136,24,13),(16,332,218,24,19),(17,348,43,24,20)]:rooms[r].step(x,y,w,h,True)
 for r,x,y,w,h in[(16,179,46,15,22),(16,399,45,15,22),(22,183,78,11,23),(30,214,95,15,27),(30,394,98,15,27),(38,214,93,17,22),(38,390,108,17,22)]:rooms[r].panel(x,y,w,h)
 return {r:p.im for r,p in rooms.items()}
def main():
 entries=json.loads((ROOT/'assets/feedback_travel_entries.json').read_text())['entries'];images=pictures(entries);runs=[];blob=bytearray();ranges={};manifest=[]
 out=ROOT/'assets/feedback_world';out.mkdir(exist_ok=True)
 for old in out.glob('overlay-*.png'):old.unlink()
 palette=Image.open(ROOT/'assets/village.png').getpalette()
 for room,im in images.items():
  if not im.getbbox():
   im.putpalette(palette);im.save(out/f'overlay-{room:02d}.png',transparency=0);continue
  first=len(runs);raw=im.tobytes()
  for y in range(320):
   x=0
   while x<480:
    if not raw[y*480+x]:x+=1;continue
    end=x+1
    while end<480 and raw[y*480+end]:end+=1
    pixels=raw[y*480+x:y*480+end];offsets=[]
    for parity in(0,1):
     while len(blob)%4:blob.append(0)
     if parity:blob.append(0)
     offsets.append(len(blob));blob.extend(pixels)
    runs.append((x,y,end-x,*offsets));x=end
  left,top,right,bottom=im.getbbox();ranges[room]=(first,len(runs)-first,left,top,right-left,bottom-top);im.putpalette(palette);im.save(out/f'overlay-{room:02d}.png');manifest.append({'room':room,'runs':len(runs)-first,'opaque_pixels':sum(bool(v)for v in raw),'image_sha256':hashlib.sha256(raw).hexdigest()})
 lines=['/* Original generated palette rows. Regenerate, do not hand edit. */\n','static const unsigned char feedback_pixels[] __attribute__((aligned(4)))={\n']
 lines += [','.join(map(str,blob[i:i+32]))+',\n'for i in range(0,len(blob),32)];lines += ['};\n','static const FeedbackRun feedback_runs[]={\n']
 lines += ['{%d,%d,%d,0,{%d,%d}},\n'%r for r in runs];lines += ['};\n','static const FeedbackRoom feedback_rooms[78]={\n']
 lines += ['[%d]={%s},\n'%(r,','.join(map(str,values)))for r,values in ranges.items()];lines+=['};\n']
 parts=[];part=''
 for line in lines:
  if len((part+line).encode())>30000:parts.append(part);part=''
  part+=line
 if part:parts.append(part)
 folder=ROOT/'src/feedback_world_data';folder.mkdir(exist_ok=True)
 for p in folder.glob('part_*.inc'):p.unlink()
 for i,part in enumerate(parts):(folder/f'part_{i:03d}.inc').write_text(part)
 (ROOT/'src/feedback_world_data.inc').write_text(''.join(f'#include "feedback_world_data/part_{i:03d}.inc"\n'for i in range(len(parts))))
 (out/'manifest.json').write_text(json.dumps({'entries':len(entries),'palette_bytes':len(blob),'runs':len(runs),'rooms':manifest},indent=2)+'\n')
 bg=Image.open(ROOT/'assets/village.png').convert('RGB');overlay=images[0].crop((0,0,240,160));bg.paste(overlay.convert('RGB'),mask=Image.frombytes('L',overlay.size,bytes(255 if x else 0 for x in overlay.tobytes())));bg.save(out/'village.png')
 print('Generated',len(entries),'entries,',len(runs),'aligned row runs,',len(blob),'palette bytes')
if __name__=='__main__':main()
