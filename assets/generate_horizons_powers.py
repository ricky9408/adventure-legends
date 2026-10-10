#!/usr/bin/env python3
"""Original Shared Horizons native power motifs, exact collision diamonds."""
from pathlib import Path
import hashlib,json,sys
from PIL import Image,ImageDraw
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'assets'))
from magma_palette import PAL
COLORS=[(13,14),(12,14),(50,51),(48,51),(45,47),(44,47),(55,96),(54,96),(6,7),(13,14),(50,51),(45,47),(6,7),(55,96),(12,14),(6,7)]
# Exact command-specific anticipation marks: returning hem, corner, vessel,
# hood, nudge, paired pads, offset blade, unequal glints, rail, slit shelter,
# rear spark, hoof, short-long strokes, split bowls, root seam, expanding fan.
MOTIFS=[[(3,8,12,8),(3,8,5,6),(3,8,5,10)],[(3,12,10,12),(10,12,10,3),(10,3,8,5)],[(4,5,4,10),(4,10,11,10),(11,10,11,5),(6,3,9,3)],[(3,11,8,4),(8,4,13,11),(7,8,9,8)],[(3,5,12,8),(12,8,3,11)],[(3,9,6,9),(10,5,13,5)],[(4,4,4,12),(7,7,12,7)],[(3,10,7,10),(9,4,14,4)],[(2,8,13,8),(11,6,13,8),(13,8,11,10)],[(3,12,7,4),(9,4,13,12)],[(3,4,3,10),(3,10,8,13)],[(4,11,4,4),(4,4,12,4),(12,4,12,11)],[(3,4,8,4),(3,11,13,11)],[(3,4,6,4),(2,5,7,5),(9,10,13,10),(8,11,14,11)],[(7,2,7,13),(4,5,10,5),(4,10,10,10)],[(3,7,12,2),(3,7,12,12),(12,2,12,12)]]
def line(x,y,tx,ty):
 dx=abs(tx-x);dy=-abs(ty-y);sx=1 if x<tx else -1;sy=1 if y<ty else -1;e=dx+dy
 while True:
  yield x,y
  if (x,y)==(tx,ty):break
  q=e*2
  if q>=dy:e+=dy;x+=sx
  if q<=dx:e+=dx;y+=sy
marks=[];particles=[]
for i,(col,bright) in enumerate(COLORS):
 p=[0]*256
 for segment in MOTIFS[i]:
  for x,y in line(*segment):p[y*16+x]=col
 marks.append(p);pair=[]
 for live in range(2):
  p=[0]*64
  for y in range(8):
   for x in range(8):
    if abs(x-3)+abs(y-3)<=2:p[y*8+x]=bright if live and (x,y)==(3,3) else col
  pair.append(p)
 particles.append(pair)
header='''#ifndef EMBERBOND_HORIZONS_POWER_ART_H
#define EMBERBOND_HORIZONS_POWER_ART_H
/* Original native exact13-pixel radius2 diamond masks. Reuses existing
 * PIN256B and WATER_DROP64B shared lease; zero resident OBJ growth. */
extern const unsigned char horizons_power_marks[16][256];
extern const unsigned char horizons_power_particles[16][2][64];
#endif
'''
out='#include "horizons_power_art.h"\nconst unsigned char horizons_power_marks[16][256]={\n'+''.join(' {'+','.join(map(str,p))+'},\n' for p in marks)+'};\nconst unsigned char horizons_power_particles[16][2][64]={\n'+''.join(' {'+','.join('{'+','.join(map(str,p))+'}' for p in pair)+'},\n' for pair in particles)+'};\n'
(ROOT/'src/horizons_power_art.h').write_text(header)
(ROOT/'src/horizons_power_art.c').write_text(out)
directory=ROOT/'assets/horizons_powers';directory.mkdir(exist_ok=True)
manifest={'authorship':'Original code-native motifs and exact collision diamonds; no imported or traced artwork','commands':list(range(106,122)),'tile_lease':'existing PIN256B + WATER_DROP64B','rom_art_bytes':6144,'source_sha256':hashlib.sha256(out.encode()).hexdigest(),'rows':[]}
sheet=Image.new('RGB',(8*64,2*64),(25,34,46));draw=ImageDraw.Draw(sheet)
for i in range(16):
 manifest['rows'].append({'command':106+i,'motif_sha256':hashlib.sha256(bytes(marks[i])).hexdigest(),'particle_sha256':[hashlib.sha256(bytes(p)).hexdigest() for p in particles[i]],'particle_mask':'abs(x-3)+abs(y-3)<=2','motif_segments':MOTIFS[i]})
 im=Image.new('P',(16,16));im.putpalette(PAL);im.putdata(marks[i]);im=im.convert('RGB').resize((48,48),Image.Resampling.NEAREST)
 sheet.paste(im,((i%8)*64+8,(i//8)*64));draw.text(((i%8)*64+20,(i//8)*64+49),str(i+106),fill=(255,240,204))
(directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');sheet.save(directory/'contact_sheet_3x.png')
if __name__=='__main__':print(hashlib.sha256(out.encode()).hexdigest())
