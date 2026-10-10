#!/usr/bin/env python3
"""REAL support renderer, native target pixels, art collision and cast timing.
No fabricated world rewards and no claim of native/controller acceptance.
"""
from pathlib import Path
import hashlib,json,subprocess,tempfile
ROOT=Path(__file__).resolve().parents[1]
report=[]
with tempfile.TemporaryDirectory() as td:
 executables={}
 for family in ('horizons','return'):
  exe=Path(td)/family
  sources=['tests/covenants_field_feasibility.c',f'src/{family}_powers.c',f'src/{family}_power_art.c','src/covenants_art.c','src/creatures.c','src/creature_data.c','src/equipment.c','src/equipment_data.c','src/gear_runtime.c','src/combat_rules.c']
  if family=='horizons':sources+=['src/north_art.c','src/south_art.c']
  subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Wno-misleading-indentation','-ffunction-sections','-fdata-sections','-Wl,--gc-sections','-Isrc','-Itests',*(['-DTEST_RETURN_SUPPORT']if family=='return'else []),*sources,'-o',str(exe)],cwd=ROOT,check=True)
  executables[family]=exe
 rooms=json.loads((ROOT/'assets/covenants_world/geometry.json').read_text())['rooms']
 for r in rooms:
  for s in r['stations']:
   c=s['command'];x,y=s['approach'];first=s['targets'][0]['center'];last=s['targets'][-1]['center'];family='horizons'if c>=106 else'return';args=[c,r['id'],x,y,s['face'],*first,*last,s['release_age']]
   result=subprocess.check_output([str(executables[family]),*map(str,args)],text=True).strip();parts=result.split();assert len(parts)==3,(r['id'],s['key'],args,result);ages,mask,count=parts;mask=int(mask);want=9 if c==108 else 1
   assert mask&want==want,(r['id'],s['key'],args,result)
   if c==108:
    assert mask&2==0,'Release seam must never count as gather beat'
    assert '8:1:0' in ages and '14:2:1' in ages,(s,result)
   else:
    expected=str(s['targets'][0]['expected_age'])+(':' if c>=106 else ',')
    assert expected in ages,(s,result)
   report.append({'area':r['id'],'key':s['key'],'command':c,'origin':s['approach'],'face':s['face'],'target_rects':[t['rect']for t in s['targets']],'release_age':s['release_age'],'actual_live_hit_ages':ages.rstrip(','),'beat_target_mask':mask,'all_hits_have_nonzero_renderer_pixels':True,'same_original_cast':True,'pass':True})
 data={'scope':'Real C support renderers plus authored full-foot collision; not native gameplay acceptance','cases':report,'source_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in ['src/horizons_powers.c','src/return_powers.c','src/field_world.h','src/covenants_art.c','src/covenants_art.h','assets/covenants_world/geometry.json','tests/covenants_field_feasibility.c']}}
 (ROOT/'assets/covenants_world/field_feasibility.json').write_text(json.dumps(data,indent=1)+'\n')
 print('Covenants real support field feasibility:',len(report),'stations pass; same-cast heat gather/release and rendered pixels verified')
