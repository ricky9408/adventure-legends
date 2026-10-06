#!/usr/bin/env python3
"""Compare optimized geometry to immutable candidate A, with exact point grids.

Only candidate A's command77 cadence is adapted to its separately tested new
132/154/180 contract. No reference geometry/prefix/collision code is edited.
The comparison excludes the deliberately changed field-target area bridge.
"""
from pathlib import Path
import hashlib,json,subprocess,os
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/underwater-geometry-equivalence';OUT.mkdir(parents=True,exist_ok=True)
FROZEN=ROOT/'tests/fixtures/underwater_powers_candidate_a.c'
SOURCES=['src/underwater_power_art.c','src/magma_powers.c','src/magma_power_art.c','src/southern_powers.c','src/southern_power_art.c','src/northern_powers.c','src/northern_power_art.c','src/advanced_powers.c','src/regional_powers.c','src/gear_runtime.c','src/weapon_actions.c','src/combat_rules.c','src/equipment.c','src/equipment_data.c','src/creatures.c','src/creature_data.c','src/assets.c']
# Pin archived oracle: a future optimized implementation may never rewrite it.
PIN='e2ec1a0adcb188fe1e69c730d7bd02f17d22eed54484344dcf65e73792bfacd0'
assert hashlib.sha256(FROZEN.read_bytes()).hexdigest()==PIN
wrapper='\nint oracle_point(int x,int y){return contains(x,y);}\nint oracle_ray(int x,int y,int tx,int ty){return clear(x,y,tx,ty);}\n'
driver=r'''
#define main original_integration_main
#include "underwater_powers_native.c"
#undef main
int oracle_point(int,int);int oracle_ray(int,int,int,int);
static unsigned digest;
static void add(unsigned n){digest=(digest^n)*16777619u;}
int main(void){unsigned c,dir,scene,n;int f,l;
 for(c=67;c<=90;c++)for(dir=0;dir<4;dir++)for(scene=0;scene<8;scene++){
  setup(c);face=(int)dir;
  if(scene==1)wall(108,60,1,81);
  if(scene==2){wall(101,100,1,1);wall(100,99,1,1);}
  if(scene==3){wall(120,91,3,4);wall(110,115,4,3);}
  if(scene==5){px=3;py=3;}
  assert(underwater_power(c));
  for(n=0;n<life[c-67];n++){
   if(scene>=6&&n==2&&underwater_powers_can_aim())assert(underwater_powers_input(c==83||c==90?64:16));
   if(scene==7&&n==10)wall(113,93,4,13);
   if(scene==4&&n==20)wall(104,60,1,81);
   if(scene==4&&n==27){wall_count=0;underwater_powers_geometry_changed();}
   if(scene==3&&n==8)assert(c==67||c==71||c==77||c==81||!underwater_powers_input(16));
   if(c==81&&n<8){px++;py+=(n&1)!=0;}
   underwater_powers_tick();digest=2166136261u;
   for(f=-30;f<=52;f+=2)for(l=-32;l<=32;l+=2)add((unsigned)oracle_point(underwater_power_origin_x+f,underwater_power_origin_y+l));
   record_draws=1;capture_count=draws=0;underwater_powers_draw();record_draws=0;
   add((unsigned)capture_count);for(f=0;f<capture_count;f++){add((unsigned)capture_x[f]);add((unsigned)capture_y[f]);add((unsigned)capture_off[f]);}
   printf("%u %u %u %u %u\n",c,dir,scene,n,digest);
  }
 }
 /* Supercover including reversed direction, invalid endpoints and edits. */
 setup(82);assert(underwater_power(82));
 for(scene=0;scene<3;scene++){
  if(scene==1){wall(103,87,1,28);wall(91,92,13,1);}
  if(scene==2){wall_count=0;underwater_powers_geometry_changed();}
  digest=2166136261u;
  for(f=-20;f<=20;f++)for(l=-20;l<=20;l++){
   add((unsigned)oracle_ray(100,100,100+f,100+l));add((unsigned)oracle_ray(100+f,100+l,100,100));
   add((unsigned)oracle_ray(100+f,100+l,97-f,104-l));
  }
  add((unsigned)oracle_ray(-1,0,3,3));add((unsigned)oracle_ray(100,100,300,100));
  printf("rays %u %u\n",scene,digest);
 }
 return 0;
}
'''
(OUT/'driver.c').write_text(driver)
results={}
FROZEN_D=ROOT/'tests/fixtures/underwater_powers_candidate_d.c'
D_PIN='bef0ec007fbda6366e51b6566ab99a6012370dbfe62aa1a197f84ca0baee5d5a'
assert hashlib.sha256(FROZEN_D.read_bytes()).hexdigest()==D_PIN
for name,path in [('reference',FROZEN),('candidate_d',FROZEN_D),('optimized',ROOT/'src/underwater_powers.c')]:
    source=path.read_text()
    if name=='reference':source=source.replace('{14,36,58,120,24,3}','{14,132,154,180,24,3}')
    generated=OUT/(name+'.c');generated.write_text(source+wrapper)
    exe=OUT/name
    subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pedantic','-Isrc','-Itests',str(OUT/'driver.c'),str(generated),*SOURCES,'-o',str(exe)],cwd=ROOT,check=True)
    results[name]=subprocess.check_output([str(exe)],cwd=ROOT)
    (OUT/(name+'.txt')).write_bytes(results[name])
assert results['candidate_d']==results['reference'], 'Frozen D diverges from archived original geometry'
a=results['reference'].splitlines();b=results['optimized'].splitlines()
assert len(a)==len(b)
for i,(x,y) in enumerate(zip(a,b)):
    assert x==y,('geometry mismatch',i,x,y)
report={'frozen_oracle_sha256':PIN,'frozen_candidate_d_sha256':D_PIN,'optimized_sha256':hashlib.sha256((ROOT/'src/underwater_powers.c').read_bytes()).hexdigest(),'matched_cast_frame_records':len(a)-3,'point_tests_per_frame':42*33,'matched_ray_checks':3*(41*41*3+2),'all_commands':24,'directions':4,'collision_scenes':8,'intentional_reference_adaptation':'command77 cadence only: startup14 active132 lifetime154 cooldown180','field_overlap':'excluded: separately tested intentional octagonal field-target area contract'}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
