#!/usr/bin/env python3
"""Isolated ARM7TDMI synthetic field bridge timing. This uses the real effect
handlers/catalog/art, with synthetic collision/OAM/world callbacks. It cannot
establish controller-acquired access or whole-game K frame-budget headroom.
"""
from pathlib import Path
import json,subprocess,sys,hashlib
ROOT=Path(__file__).resolve().parents[1];COUNT=int(sys.argv[1]) if len(sys.argv)>1 else 8
assert COUNT in (1,8)
OUT=ROOT/('build/return-legacy-host/arm-probe-'+str(COUNT));OUT.mkdir(parents=True,exist_ok=True)
arm=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc';prefix=str(arm).removesuffix('gcc')
assert arm.exists()
s=(ROOT/'tests/return_legacy_powers_host.c').read_text().split('static int opaque(')[0]
for h in ['assert.h','stdio.h','string.h','stdlib.h']:s=s.replace('#include <'+h+'>','')
s=s.replace('target_x+(int)i*80','target_x') # maximum8 same-frame overlapping targets
prelude='''
typedef unsigned size_t;
volatile unsigned completed,fault_line;
#define assert(c) do {if(!(c)){fault_line=__LINE__;completed=2;while(1){}}} while(0)
static int abs(int x){return x<0?-x:x;}
static void *memset(void*v,int c,unsigned n){unsigned char*p=v;while(n--)*p++=(unsigned char)c;return v;}
static void *memcpy(void*v,const void*s,unsigned n){unsigned char*p=v;const unsigned char*q=s;while(n--)*p++=*q++;return v;}
'''
main='''
#define REG16(a) (*(volatile unsigned short *)(a))
volatile unsigned timings[19][5],counts[19];
static unsigned now(void){unsigned hi,lo,again;do{hi=REG16(0x0400010c);lo=REG16(0x04000108);again=REG16(0x0400010c);}while(hi!=again);return(hi<<16)|lo;}
int main(void){unsigned j,a,d,t,v;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010c)=0;REG16(0x0400010e)=0x84;REG16(0x04000108)=0;REG16(0x0400010a)=0x80;
 for(j=0;j<19;j++)for(d=0;d<4;d++){
  unsigned c=commands[j];setup(c);face=(int)d;field_count=8;target_x=100+(d==2?-24:d==3?24:0);target_y=100+(d==1?-24:d==0?24:0);
  t=now();assert(cast_power(c));v=now()-t;if(v>timings[j][0])timings[j][0]=v;
  for(a=0;a<96;a++){
   t=now();effects_tick();v=now()-t;if(v>timings[j][1])timings[j][1]=v;
   collision_calls=0;t=now();return_legacy_tick();v=now()-t;if(v>timings[j][2])timings[j][2]=v;if(collision_calls>counts[j])counts[j]=collision_calls;
   t=now();effects_draw(c);v=now()-t;if(v>timings[j][3])timings[j][3]=v;
   /* Occluded but visually still alive: no eight-target scan may blow up. */
   walls[0].x=100+(d==2?-12:d==3?12:-40);walls[0].y=100+(d==1?-12:d==0?12:-40);
   walls[0].w=d>=2?1:80;walls[0].h=d>=2?80:1;wall_count=1;
   t=now();(void)return_legacy_overlap(target_x,target_y,12);v=now()-t;if(v>timings[j][4])timings[j][4]=v;
   wall_count=0;
  }
 }
 completed=1;while(1){}return 0;
}
'''
main=main.replace('field_count=8','field_count='+str(COUNT))
(OUT/'main.c').write_text(prelude+s+main)
sources=[OUT/'main.c']+[ROOT/'src'/f'{m}.c'for m in ['return_legacy_powers','advanced_powers','regional_powers','northern_powers','southern_powers','northern_power_art','southern_power_art','creatures','creature_data','assets']]
flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-ffunction-sections','-fdata-sections','-Isrc']
objects=[]
for source in sources:
 obj=OUT/(source.stem+'.o');subprocess.run([str(arm),*flags,'-c',str(source),'-o',str(obj)],cwd=ROOT,check=True);objects.append(str(obj))
startup=OUT/'startup.o';subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c','src/startup.s','-o',str(startup)],cwd=ROOT,check=True)
elf=OUT/'probe.elf';rom=OUT/'probe.gba'
subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,--gc-sections,-T,linker.ld',str(startup),*objects,'-lgcc','-o',str(elf)],cwd=ROOT,check=True)
subprocess.run([prefix+'objcopy','-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,'tools/fix_header.py',str(rom)],cwd=ROOT,check=True)
syms={p[2]:int(p[0],16)for line in subprocess.check_output([prefix+'nm',str(elf)],text=True).splitlines()if len(p:=line.split())==3}
sys.path.insert(0,str(ROOT/'tools'));from mgba_runner import Emulator
with Emulator(rom)as emu:
 for _ in range(500):
  emu.frames(10)
  if emu.read(syms['completed']):break
 assert emu.read(syms['completed'])==1,('synthetic benchmark failure',emu.read(syms['fault_line']))
 timing=[[emu.read(syms['timings']+(j*5+n)*4)for n in range(5)]for j in range(19)]
 counts=[emu.read(syms['counts']+j*4)for j in range(19)]
commands=[1,2,3,4,5,6,7,8,9,10,11,13,14,15,16,23,24,25,26]
report={'kind':'isolated-ARM7TDMI-synthetic-world-timing-not-controller-acceptance','waitcnt':'0x4317','targets':COUNT,'columns':['cast_including_bridge_cycles','old_effect_tick_cycles','bridge_tick_cycles','old_effect_draw_cycles','occluded_single_overlap_cycles'],'commands':{str(c):{'cycles':timing[j],'bridge_solid_probes':counts[j]}for j,c in enumerate(commands)},'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),'limitation':'No live world scene, renderer OAM/cache pressure, controller acquisition or whole-game frame-budget guarantee; eight target centers intentionally overlap to stress same-frame dispatch.'}
(OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
print('Synthetic ARM7TDMI maxima:',*[max(row[n]for row in timing)for n in range(5)])
