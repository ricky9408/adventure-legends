#!/usr/bin/env python3
"""Source/art supplier reachability; not emulator/controller route evidence."""
from collections import deque
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[1]
source=(ROOT/'src/regional_shop.h').read_text()
def array(name):
 return list(map(int,re.search(r'\b'+name+r'\[8\]=\{([^}]+)\}',source)[1].split(',')))
xs,ys=array('xs'),array('ys')
tables=[('region','region_reedhaven'),('north','north_hearthwake_quay'),
 ('south','south_sunlace_anchorage'),('magma','magma_kilnstep_commons'),
 ('underwater','underwater_nacreway'),('return','return_greenwake_common'),
 ('horizons','horizons_room62'),('covenants','covenants_room70')]
for index,(family,name) in enumerate(tables):
 text=''.join(p.read_text() for p in sorted((ROOT/'src'/f'{family}_art_data').glob('part_*.inc')))
 body=re.search(r'const \w+ArtRect '+name+r'_solids\[.*?\] = \{(.*?)\};',text,re.S)[1]
 rectangles=[tuple(map(int,row)) for row in re.findall(r'\{\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\}',body)]
 def blocked(x,y):
  return x<8 or x>472 or y<8 or y>304 or any(x+5>=a and x-5<a+w and y+5>=b and y-5<b+h for a,b,w,h in rectangles)
 point=(xs[index],ys[index]);assert not blocked(*point),(name,'supplier in solid',point)
 queue=deque([(240,284)]);visited=set(queue);found=False
 while queue:
  x,y=queue.popleft()
  if abs(x-point[0])+abs(y-point[1])<22:found=True;break
  for dx,dy in ((-4,0),(4,0),(0,-4),(0,4)):
   q=(x+dx,y+dy)
   if q not in visited and not blocked(*q):visited.add(q);queue.append(q)
 assert found,(name,'no static foot route from arrival road',point)
 assert sum(not blocked(point[0]+dx,point[1]+dy) for dx,dy in ((-12,0),(12,0),(0,-12),(0,12)))>=2,(name,'too few safe approaches')
 print('PASS',name,point,'static five-pixel foot route and at least two safe approach centers')
print('Static geometry evidence only; native room/puzzle/road integration is checked separately.')
