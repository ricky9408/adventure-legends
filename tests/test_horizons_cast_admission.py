#!/usr/bin/env python3
"""Real cast admission/silhouette contracts; synthetic host geometry, not play.

Optional --baseline-source plus its SHA compares the complete observable cast
trace with an authenticated prior module. Current checks require one snapshot
for successful admission and none for an authoritative blocked origin.
"""
import argparse, ast, hashlib, os, subprocess, sys, tempfile
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
DRIVER = r'''
#define main inherited_main
#include "horizons_powers_host.c"
#undef main
static unsigned snapshots;
int game_collision_rects(int l,int t,int r,int b,short out[][4],unsigned cap){
 unsigned i,n=0;snapshots++;
 for(i=0;i<(unsigned)wall_count;i++){
  int x=walls[i].x,y=walls[i].y,xx=x+walls[i].w-1,yy=y+walls[i].h-1;
  if(xx<l||x>r||yy<t||y>b)continue;
  if(n==cap)return -1;
  out[n][0]=(short)(x<l?l:x);out[n][1]=(short)(y<t?t:y);
  out[n][2]=(short)(xx>r?r:xx);out[n][3]=(short)(yy>b?b:yy);n++;
 }return (int)n;
}
int underwater_game_supercover(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;return -1;}
int game_road_box_touched(unsigned a,int b,int c,int d,int e){(void)a;(void)b;(void)c;(void)d;(void)e;return 0;}
int return_power_time,covenants_power_time;
#define ABSENT(chapter) \
int chapter##_game_is_room(unsigned a){(void)a;return 0;} \
int chapter##_game_clear_box(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;return 0;} \
int chapter##_game_supercover(int a,int b,int c,int d){(void)a;(void)b;(void)c;(void)d;return -1;} \
unsigned chapter##_game_action_begin(unsigned a){(void)a;return 0;} \
int chapter##_game_field_target(unsigned a,int*b,int*c,int*d){(void)a;(void)b;(void)c;(void)d;return 0;} \
int chapter##_game_field_hit(unsigned a,unsigned b,unsigned c,unsigned d,unsigned e){(void)a;(void)b;(void)c;(void)d;(void)e;return 0;} \
void chapter##_game_revoke_cast(unsigned a){(void)a;}
ABSENT(return) ABSENT(covenants)
static unsigned digest=2166136261u;
static void bytes(const void*p,unsigned n){const unsigned char*b=p;while(n--){digest^=*b++;digest*=16777619u;}}
static void observe(void){
 int state[]={horizons_power_kind,horizons_power_time,horizons_power_direction,
  horizons_power_origin_x,horizons_power_origin_y,horizons_power_age,
  horizons_power_cast_time,ability_cd,(int)field_calls,(int)field_accepts,
  (int)field_beats,(int)draws,(int)token,(int)revoked,(int)owner};
 bytes(state,sizeof state);bytes(enemies,sizeof enemies);bytes(enemy_hp_q4,sizeof enemy_hp_q4);
 bytes(vram,sizeof vram);bytes(draw_x,draws*sizeof(int));bytes(draw_y,draws*sizeof(int));
 bytes(draw_off,draws*sizeof(int));bytes(draw_w,draws*sizeof(int));
}
int main(void){unsigned c,d,w,i,cases=0;
 for(c=106;c<=121;c++)for(d=0;d<4;d++)for(w=0;w<5;w++){
  setup(c);face=(int)d;token=0;memset(vram,0,sizeof vram);
  if(w==1)wall(111,0,2,320);if(w==2)wall(0,111,480,2);
  if(w==3)wall(98,98,5,5);if(w==4)wall(107,95,1,1);
  field_count=1;field_x=120;field_y=100;enemy(0,20,0,0);snapshots=0;
  if(w==3){
   assert(!horizons_power(c)&&!horizons_power_time&&!owner&&!ability_cd&&!token);
   assert(!field_calls);bytes(vram,sizeof vram);
#ifndef REFERENCE_BASELINE
   assert(!snapshots);
#endif
   cases++;continue;
  }
  assert(horizons_power(c));assert(!field_calls);
#ifndef REFERENCE_BASELINE
  assert(snapshots==1);
#endif
  draws=0;horizons_powers_draw();observe();
  for(i=1;i<=lifetime[c-106];i++){tick();help(c,i);observe();}
  assert(!horizons_power_time);cases++;
 }
 printf("%u cast traces %08x\n",cases,digest);return 0;
}
'''
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--baseline-source',type=Path);p.add_argument('--expected-baseline-sha')
    a=p.parse_args();assert bool(a.baseline_source)==bool(a.expected_baseline_sha)
    tree=ast.parse((ROOT/'tests/test_horizons_powers.py').read_text())
    sources=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='SOURCES'for t in n.targets))[1:]
    link=['-Wl,-dead_strip']if sys.platform=='darwin'else['-Wl,--gc-sections']
    with tempfile.TemporaryDirectory(prefix='horizons-admission-')as tmp:
        tmp=Path(tmp);driver=tmp/'admission.c';driver.write_text(DRIVER);outputs=[]
        variants=[('current',ROOT/'src/horizons_powers.c',[])]
        if a.baseline_source:
            assert hashlib.sha256(a.baseline_source.read_bytes()).hexdigest()==a.expected_baseline_sha
            variants.append(('baseline',a.baseline_source,['-DREFERENCE_BASELINE']))
        for label,module,extra in variants:
            for sanitizer,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
                exe=tmp/(label+'-'+sanitizer)
                selected=[str(module)if s=='src/horizons_powers.c'else s for s in sources]
                subprocess.run([os.environ.get('HOST_CC','cc'),'-std=c99','-O1','-g','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-pedantic','-ffunction-sections','-fdata-sections',*link,'-Isrc','-Itests',*flags,*extra,str(driver),*selected,'-o',str(exe)],cwd=ROOT,check=True)
                output=subprocess.check_output([str(exe)],cwd=ROOT,env={**os.environ,'ASAN_OPTIONS':'detect_leaks=0:halt_on_error=1','UBSAN_OPTIONS':'halt_on_error=1'})
                outputs.append(output);print(label,sanitizer,output.decode().strip())
        assert len(set(outputs))==1,'Admission changed visual/combat/field/lifetime trace'
if __name__=='__main__':main()
