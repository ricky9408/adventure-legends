#!/usr/bin/env python3
"""Synthetic host bitmap previews with actual world overlay/actor pixels.
No native/controller completion claim and no fabricated gameplay HUD.
"""
from pathlib import Path
import ctypes as C,json,sys
from PIL import Image,ImageDraw
from test_horizons_world import World,ROOT
sys.path.insert(0,str(ROOT/"assets"))
from generate_assets import P
World.setUpClass();w=World();w.setUp();w.test_all_four_personal_trials_and_rehearsal();l=w.l
out=ROOT/'assets/horizons_region/host_previews';out.mkdir(exist_ok=True)
palette=Image.open(ROOT/'assets/horizons_region/room62.png').getpalette();bitmap=(C.c_ubyte*(240*160)).in_dll(l,'world_bitmap');items=[]
def take(name,area,cx=0,cy=0):
 w.entry(area);l.render_bitmap(cx,cy);im=Image.frombytes('P',(240,160),bytes(bitmap));im.putpalette(palette);im.save(out/(name+'.png'));items.append((name,im.convert('RGB')));return im
negative=take('gallery_negative',66);assert negative.getpixel((144,80))==P["gold4"],negative.getpixel((144,80)) # PAL_GOLD4
# Black bar and round dot must be present; dry opening is deliberately blank.
assert negative.getpixel((176,80))==P["wood1"] and negative.getpixel((208,80))==P["wood1"]
for args in [('gallery_lower',66,0,160),('theater_complete',64,0,0),('fair_homecoming',62,120,160),('transfer_complete',67,240,160),('assembly_complete',68,0,0)]:take(*args)
cases=[(63,105,106,(336,128),(336,104),240,0),(67,107,108,(368,208),(300,232),240,160),(66,109,110,(48,72),(80,160),0,160),(68,111,112,(48,112),(80,112),0,0)]
for i,(area,base,cmd,lectern,manual,cx,cy)in enumerate(cases):
 slot=w.select(base,cmd);assert l.evolve(slot,base+1)==0;w.entry(area);w.select(base+1,cmd+1);w.act(*lectern);w.act(*manual);l.render_bitmap(cx,cy);im=Image.frombytes('P',(240,160),bytes(bitmap));im.putpalette(palette);name=f'evolved_practice_{base+1}';im.save(out/(name+'.png'));items.append((name,im.convert('RGB')))
sheet=Image.new('RGB',(480,180*((len(items)+1)//2)),(24,32,48));d=ImageDraw.Draw(sheet)
for i,(name,im) in enumerate(items):x=(i%2)*240;y=(i//2)*180;d.text((x+3,y+3),name,fill=(255,240,175));sheet.paste(im,(x,y+20))
sheet.save(out/'contact_native.png');(out/'README.txt').write_text('Synthetic host previews of generated background plus actual world bitmap overlays and original actor pixels. No player, gameplay HUD or native acquisition evidence is fabricated. Pixel assertions verify the gallery dry opening remains blank and bar/dot symbols match the positive clue.\n')
print('Verified blank/bar/dot pixels and saved',len(items),'host native-size overlay previews')
World.doClassCleanups()
