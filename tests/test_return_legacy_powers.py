#!/usr/bin/env python3
"""Historical field exports/provenance, old-combat differential, authored-floor
feasibility, and ARM resource accounting. Synthetic evidence, NOT a native
controller-earned release acceptance route or complete-world frame timing.
"""
from pathlib import Path
import ctypes as C
import hashlib,json,os,subprocess
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/return-legacy-host'
OUT.mkdir(parents=True,exist_ok=True)
SOURCES=['tests/return_legacy_powers_host.c']+['src/'+s+'.c' for s in ['return_legacy_powers','advanced_powers','regional_powers','northern_powers','southern_powers','northern_power_art','southern_power_art','creatures','creature_data','assets']]
FLAGS=['-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pedantic','-Isrc']
for name,extra in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
 exe=OUT/name
 subprocess.run(['cc',*FLAGS,*extra,*SOURCES,'-o',str(exe)],cwd=ROOT,check=True)
 subprocess.run([str(exe)],cwd=ROOT,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0'),check=True)
so=OUT/'probe.so'
subprocess.run(['cc',*FLAGS,'-fPIC','-shared',*SOURCES,'-o',str(so)],cwd=ROOT,check=True)
l=C.CDLL(str(so))
rooms=json.loads((ROOT/'assets/return_region/geometry.json').read_text())['rooms']
contracts={0:[1,5],1:[2,6],2:[3,7],3:[4,8],4:[9,10],5:[11],6:[11],7:[13,14],8:[15,16],9:[23,24],10:[25,26]}
# 5px collision-footprint expansion matches return_game_geometry_solid and
# dynamic_solid, validated independently against the authored world test suite.
def probe(r,c,t,dx,dy,mask,others):
 x,y=t[0]+dx,t[1]+dy
 l.fixture_begin(c,r['id'],x,y,*t)
 for other in others:l.fixture_forbid(*other)
 for a,b,w,h in [v['rect']for v in r['solids']]+[v['states'][(mask>>v['setting'])&1]for v in r['dynamic_rectangles']]:
  l.fixture_wall(a-5,b-5,w+10,h+10)
 return l.fixture_run(c)
results=[]
for r in rooms:
 for work in r['trial_workspaces']:
  index=work['index']
  if index not in contracts:continue
  for c in contracts[index]:
   for target,t in enumerate(work['targets']):
    # Third root target is the intentional drain-gap exclusion, not an action.
    if index==1 and target==2:continue
    # Third hearth is intentionally kept warm by manual hood, never hit.
    if index==8 and target==2:continue
    # The third bell mark is the intentional quiet center, not an action.
    if index==6 and target==2:continue
    for mask in range(8 if r['dynamic_rectangles'] else 1):
     preferred={1:(0,32),2:(0,24),3:(0,32),4:(0,24),5:(0,32),6:(-20,20),7:(0,32),8:(12,8),9:(0,24),10:(0,36),11:(0,32),13:(0,32),14:(0,24),15:(0,24),16:(0,32),23:(8,16),24:(0,32),25:(0,24),26:(0,24)}[c]
     candidates=[preferred]+[(dx,dy)for dy in range(8,57,4)for dx in range(-32,33,4)]
     found=None
     for dx,dy in candidates:
      age=probe(r,c,t,dx,dy,mask,[v for v in work['targets']if v!=t])
      if age>0:
       # Require a 9x9 navigation tolerance box rather than a single magic pixel.
       ages=[probe(r,c,t,dx+ox,dy+oy,mask,[v for v in work['targets']if v!=t])for ox,oy in [(ox,oy)for ox in range(-4,5)for oy in range(-4,5)]]
       if all(a>0 for a in ages):found=(dx,dy,age,max(ages));break
     assert found,(r['id'],index,c,target,mask,'no forgiving 9x9 launch footprint')
     results.append({'room':r['id'],'trial_index':index,'command':c,'target_index':target,'target':t,'dynamic_mask':mask,'launch':[t[0]+found[0],t[1]+found[1]],'first_overlap_update':found[2],'latest_tolerance_overlap_update':found[3],'face':1,'navigation_tolerance':'+/-4px in x/y, all81 positions','other_target_overlaps_during_full_cast':0})
(OUT/'fixture-footprints.json').write_text(json.dumps({'kind':'synthetic-real-authored-collision-and-live-old-effect-feasibility-not-controller-acceptance','cases':results},indent=2)+'\n')
print(f'Authored fixtures: {len(results)} command/target/topology cases have a forgiving 9x9 launch footprint')
arm=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc'
if arm.exists():
 prefix=str(arm).removesuffix('gcc');objects=[]
 for module in ['return_legacy_powers','advanced_powers','regional_powers','northern_powers','southern_powers']:
  obj=OUT/(module+'.o')
  subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-std=c99','-O2','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-fstack-usage','-Isrc','-c','src/'+module+'.c','-o',str(obj)],cwd=ROOT,check=True);objects.append(str(obj))
 size=subprocess.check_output([prefix+'size',*objects],text=True)
 sections=subprocess.check_output([prefix+'objdump','-h',*objects],text=True)
 stack='\n'.join(p.read_text()for p in OUT.glob('*.su'))
 assert '.iwram' not in sections
 row=size.strip().splitlines()[1].split();assert int(row[1])==0 and int(row[2])<=40
 own_stack=(OUT/'return_legacy_powers.su').read_text();maximum=max(int(v.split('\t')[1])for v in own_stack.splitlines())
 assert maximum<=128
 report={'kind':'ARM-object-accounting-not-native-frame-timing','bridge_rom_bytes':int(row[0]),'bridge_bss_bytes':int(row[2]),'bridge_max_individual_stack_bytes':maximum,'resident_OBJ_delta_bytes':0,'IWRAM_delta_bytes':0,'size':size,'stack':stack,'fixture_case_count':len(results),'source_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest()for s in SOURCES}}
 (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(size,end='');print('Bridge maximum individual stack:',maximum)
