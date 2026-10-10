#!/usr/bin/env python3
"""Deterministic original Return power motifs; no external art inputs."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[1]
COLORS=[(13,14),(50,51),(50,51),(45,47),(55,96),(6,7),(6,7),(50,51),(13,14),(50,51),(45,47),(6,7),(6,7),(55,96),(55,96)]
# Each sixteen-pixel preview depicts its command's authored geometry.
MOTIFS=[[(3,11,12,11),(3,11,3,6),(12,11,12,6),(6,5,9,5)],[(4,12,4,4),(4,4,12,4),(12,4,12,12)],[(3,12,11,12),(11,12,11,4),(11,4,7,4)],[(3,10,12,10),(7,10,7,5),(5,7,9,7)],[(3,4,11,4),(11,4,11,11),(11,11,7,11)],[(4,3,4,12),(4,7,9,7),(9,7,9,5)],[(3,3,3,12),(12,3,12,12)],[(2,5,5,8),(5,8,10,8),(10,8,13,4)],[(4,3,10,3),(10,3,13,7),(13,7,10,11),(10,11,4,11)],[(2,11,8,11),(8,11,8,4),(8,4,12,4)],[(3,3,3,12),(11,5,11,12)],[(4,3,4,12),(4,8,11,8)],[(3,12,12,7),(12,7,3,2)],[(3,3,3,9),(3,9,12,9)],[(2,3,12,7),(2,12,7,12),(7,12,12,7)]]
def line(a,b,c,d):
 x,y=a,b;dx=abs(c-a);dy=-abs(d-b);sx=1 if a<c else -1;sy=1 if b<d else -1;e=dx+dy
 while True:
  yield x,y
  if (x,y)==(c,d):break
  q=2*e
  if q>=dy:e+=dy;x+=sx
  if q<=dx:e+=dx;y+=sy
marks=[];particles=[]
for i,(col,bright) in enumerate(COLORS):
 p=[0]*256
 for seg in MOTIFS[i]:
  for x,y in line(*seg):p[y*16+x]=col
 marks.append(p)
 frames=[]
 for live in range(2):
  p=[0]*64
  for y in range(8):
   for x in range(8):
    if abs(x-3)+abs(y-3)<=2:p[y*8+x]=bright if live and (x,y)==(3,3) else col
  frames.append(p)
 particles.append(frames)
out='#include "return_power_art.h"\nconst unsigned char return_power_marks[15][256]={\n'+''.join(' {'+','.join(map(str,p))+'},\n' for p in marks)+'};\nconst unsigned char return_power_particles[15][2][64]={\n'+''.join(' {'+','.join('{'+','.join(map(str,p))+'}' for p in pair)+'},\n' for pair in particles)+'};\n'
(ROOT/'src/return_power_art.c').write_text(out)
directory=ROOT/'assets/return_powers';directory.mkdir(exist_ok=True)
manifest={'authorship':'Original code-native motifs and exact collision particle diamonds; no external or extracted assets',
          'commands':list(range(91,106)),'tile_lease':'existing PIN256B + WATER_DROP64B',
          'source_sha256':hashlib.sha256(out.encode()).hexdigest(),'rows':[]}
for i in range(15):
 manifest['rows'].append({'command':91+i,'motif_sha256':hashlib.sha256(bytes(marks[i])).hexdigest(),
                         'particle_sha256':[hashlib.sha256(bytes(p)).hexdigest() for p in particles[i]],
                         'particle_mask':'abs(x-3)+abs(y-3)<=2','motif_segments':MOTIFS[i]})
(directory/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
if __name__=='__main__':print(hashlib.sha256(out.encode()).hexdigest())
