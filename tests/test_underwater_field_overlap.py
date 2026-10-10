#!/usr/bin/env python3
"""Exact octagonal target intersection versus exhaustive active-pixel oracle."""
from pathlib import Path
import subprocess,json,hashlib
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/underwater-field-overlap';OUT.mkdir(exist_ok=True,parents=True)
SOURCES=['src/underwater_power_art.c','src/magma_powers.c','src/magma_power_art.c','src/southern_powers.c','src/southern_power_art.c','src/northern_powers.c','src/northern_power_art.c','src/advanced_powers.c','src/regional_powers.c','src/gear_runtime.c', 'tests/legacy_return_hooks.c','src/weapon_actions.c','src/combat_rules.c','src/equipment.c','src/equipment_data.c','src/creatures.c','src/creature_data.c','src/assets.c']
wrapper=r'''
int optimized_field(int x,int y,int r){return field_contains(x,y,r);}
int exhaustive_field(int x,int y,int r){int xx,yy;
 if(r<0||r>10)return 0;
 for(yy=y-r;yy<=y+r;yy++)for(xx=x-r;xx<=x+r;xx++)
  if(abs_i(xx-x)+abs_i(yy-y)<=r+3&&contains(xx,yy)&&clear(xx,yy,x,y))return 1;
 return 0;
}
'''
driver=r'''
#define main original_integration_main
#include "underwater_powers_native.c"
#undef main
int optimized_field(int,int,int);int exhaustive_field(int,int,int);
int main(void){unsigned c,d,scene,n,j,r,count=0;static const int targets[][2]={{12,3},{24,0},{24,8},{16,0},{12,-10},{32,14},{-8,3},{0,0}};
 for(c=67;c<=90;c++)for(d=0;d<4;d++)for(scene=0;scene<3;scene++){
  setup(c);face=(int)d;
  if(scene==1)wall(115,75,1,51);
  if(scene==2){wall(101,100,1,1);wall(100,99,1,1);}
  assert(underwater_power(c));
  for(n=1;n<=life[c-67];n++){
   if(scene==2&&n==20){wall_count=0;underwater_powers_geometry_changed();}
   underwater_powers_tick();
   if(n!=start[c-67]&&n!=start[c-67]+active_len[c-67]/2&&n!=start[c-67]+active_len[c-67]-1)continue;
   for(j=0;j<8;j++)for(r=1;r<=10;r+=9){int x=100+targets[j][0],y=100+targets[j][1],a,b;
    a=optimized_field(x,y,(int)r);b=exhaustive_field(x,y,(int)r);
    if(a!=b){fprintf(stderr,"field mismatch command%u direction%u scene%u age%u target%d,%d radius%u got%d expected%d\n",c,d,scene,n,x,y,r,a,b);return 1;}
    count++;
   }
  }
 }
 printf("%u exact octagonal intersections match exhaustive pixel oracle\n",count);return 0;
}
'''
(OUT/'module.c').write_text((ROOT/'src/underwater_powers.c').read_text()+wrapper);(OUT/'driver.c').write_text(driver)
exe=OUT/'field-equivalence'
subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pedantic','-Isrc','-Itests',str(OUT/'driver.c'),str(OUT/'module.c'),*SOURCES,'-o',str(exe)],cwd=ROOT,check=True)
result=subprocess.check_output([str(exe)],cwd=ROOT,text=True);print(result,end='')
(OUT/'report.json').write_text(json.dumps({'result':result.strip(),'source_sha256':hashlib.sha256((ROOT/'src/underwater_powers.c').read_bytes()).hexdigest(),'shapes':24,'directions':4,'collision_scenes':3,'ages_per_cast':3,'target_locations':8,'radii':[1,10],'enemy_and_boss_inflation':False},indent=2)+'\n')
