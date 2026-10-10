#!/usr/bin/env python3
"""Pure authored geometry, old interaction retention and deterministic art tests."""
from pathlib import Path
from collections import deque
import sys,json,itertools,unittest,hashlib,re,subprocess
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'assets'))
import os,sys
from retained_ui_story_successor import read_view_for_flags
_UI=read_view_for_flags(ROOT,sys.argv)
from generate_region import occupancy
from generate_northern_region import collision_bands
G=json.loads((ROOT/'assets/return_region/geometry.json').read_text())['rooms']
OLD={0:[(152,112),(176,112),(104,112)],16:[(368,152),(424,144),(112,144)],17:[(264,284)],18:[(208,112)],20:[(208,112)],22:[(416,144),(192,192),(352,176)],30:[(432,256),(448,192)],38:[(208,272)],46:[(200,272)]}
def reachable(r):
 w,h=r['width'],r['height'];blocked=occupancy(r,False);start=r['spawns']['0'];start=start[1]*w+start[0];seen=bytearray(w*h);seen[start]=1;q=deque([start])
 while q:
  p=q.popleft()
  for n in [p-1,p+1,p-w,p+w]:
   if 0<=n<w*h and abs(n%w-p%w)+abs(n//w-p//w)==1 and not blocked[n] and not seen[n]:seen[n]=1;q.append(n)
 return blocked,seen
class Geometry(unittest.TestCase):
 def test_dimensions_spawns_and_all_dynamic_state_reachability(self):
  self.assertEqual([r['id']for r in G],list(range(54,62)));self.assertEqual(sum(r['width']==480 for r in G),4)
  for r in G:
   for choices in itertools.product(*[range(2)for _ in r['dynamic_rectangles']]):
    v={**r,'solids':r['solids']+[{'rect':d['states'][choice]}for d,choice in zip(r['dynamic_rectangles'],choices)]};b,seen=reachable(v);w=r['width']
    targets=list(r['spawns'].values())+[e['approach']for e in r['exits']]+[e['via']for e in r.get('route_landmarks',[])]+[p for t in r['trial_workspaces']for p in t['walk']]
    for x,y in targets:self.assertTrue(seen[y*w+x] and not b[y*w+x],(r['id'],choices,'required landing',x,y))
    fixtures=[o['center']for o in r['objects']]+r['field_targets']+[p for t in r['trial_workspaces']for p in [t['lectern']]+t['manual']+t['targets']]
    for x,y in fixtures:
     points=[(x+dx*n,y+dy*n)for dx,dy in [(1,0),(-1,0),(0,1),(0,-1)]for n in range(16,27)]
     self.assertTrue(any(0<=xx<w and 0<=yy<r['height'] and seen[yy*w+xx]and not b[yy*w+xx]for xx,yy in points),(r['id'],choices,'fixture',x,y))
 def test_row_band_exact_half_open_rectangles(self):
  for r in G:
   rows,bands,stats=collision_bands(r);blocked=occupancy(r,False);w=r['width']
   for y,row in enumerate(rows):
    n=bands[row];ints=list(zip(bands[row+1:row+1+2*n:2],bands[row+2:row+1+2*n:2]));self.assertTrue(all(a<b for a,b in ints));self.assertTrue(all(ints[i][1]<ints[i+1][0] for i in range(n-1)))
    for x in range(w):self.assertEqual(bool(blocked[y*w+x]),any(a<=x<b for a,b in ints),(r['id'],x,y))
 def test_distinct_local_trial_workspaces_and_marked_targets(self):
  t=[x for r in G for x in r['trial_workspaces']];self.assertEqual(sorted(x['index']for x in t),list(range(13)));self.assertEqual(len({tuple(map(tuple,x['targets']))for x in t}),13)
  self.assertTrue(all(len(x['targets'])<=3 for x in t));self.assertTrue(all(o['marked_diameter']>=24 for r in G for o in r['objects']))
 def test_original_npc_approaches_are_not_stolen(self):
  for folder in ['region','northern_region','southern_region','magma_region','underwater_region']:
   for r in json.loads((ROOT/'assets'/folder/'layout.json').read_text())['rooms']:
    if r['id']not in OLD:continue
    b,seen=reachable(r);w=r['width']
    for x,y in OLD[r['id']]:
     self.assertTrue(any(0<=xx<w and 0<=yy<r['height'] and seen[yy*w+xx]and not b[yy*w+xx] for xx,yy in [(x+18,y),(x-18,y),(x,y+18),(x,y-18)]),(r['id'],x,y))
    for ob in r['objects']:
     if not any(z in str(ob.get('kind',''))+' '+str(ob.get('type',''))+' '+str(ob.get('sprite',''))for z in ['npc','NPC','SMITH','MIRA','EDDA','TOVE','CURATOR','rest','REST']):continue
     x,y=ob['approach']
     for tx,ty in OLD[r['id']]:
      f=y-ty;s=abs(x-tx);self.assertFalse(6<=f<=26 and s<=10 and s<=f//2,(r['id'],ob['key'],'intercepted',tx,ty))
 def test_art_and_ui_artifact_limits_and_stable_old_ids(self):
  for p in list((ROOT/'src/return_art_data').glob('*.inc'))+list((ROOT/'assets/return_region').glob('*.json'))+[ROOT/'assets/ui_texts.json',ROOT/'assets/ui_texts_return.json']:self.assertLess(p.stat().st_size,75000,str(p))
  # Connected Roads starts from authenticated accepted Experience Polish P2.
  # Three reviewed road clues now change; every other P2 value/raster stays exact.
  # The original Return I release oracle remains in assets/return_region/ui_retention.json.
  evidence=json.loads((ROOT/'docs/connected-roads/accepted-p2-ui-contract.json').read_text());new=_UI.header;names=re.findall(r' TX_([^, ]+),',new)
  self.assertEqual(hashlib.sha256('\n'.join(names[:evidence['legacy_identifier_count']]).encode()).hexdigest(),evidence['legacy_identifier_sha256'])
  route_copy=json.loads((ROOT/'docs/connected-roads/route-clue-ui-contract.json').read_text());allowed=set(route_copy['allowed_keys'])
  metadata=_UI.metadata('assets/ui_texts.json')
  untouched={k:v for k,v in metadata.items()if k not in allowed}
  canonical=json.dumps(untouched,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
  self.assertEqual(hashlib.sha256(canonical).hexdigest(),route_copy['unchanged_metadata_sha256']['assets/ui_texts.json'])
  for change in route_copy['metadata_changes']:
   if change['file']=='assets/ui_texts.json':self.assertEqual(metadata[change['key']],change['new'])
  data=_UI.raster_source;rows=re.findall(r'static const UiRun txt_\w+_[01]\[\] = \{[^\n]*\};',data)
  retained=[]
  for row in rows[:evidence['old_raster_statements']]:
   name,key=re.match(r'static const UiRun (txt_(\w+)_[01])\[',row).groups()
   if key in allowed:self.assertEqual(hashlib.sha256(row.encode()).hexdigest(),route_copy['new_raster_sha256'][name])
   else:retained.append(row)
  self.assertEqual(hashlib.sha256('\n'.join(retained).encode()).hexdigest(),route_copy['unchanged_legacy_raster_sha256'])

if __name__=='__main__':unittest.main()
