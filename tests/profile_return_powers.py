#!/usr/bin/env python3
"""Isolated ARM cycle microbenchmark. Synthetic callbacks, not full-engine cadence."""
from pathlib import Path
import subprocess,hashlib,json,sys,re
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'build/return-powers-host/arm-bench';OUT.mkdir(parents=True,exist_ok=True)
arm=str(ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc');prefix=arm.removesuffix('gcc')
s=(ROOT/'tests/return_powers_host.c').read_text().split('static void all_commands')[0]
for h in ['assert.h','stdio.h','string.h','stdlib.h']:s=s.replace('#include <'+h+'>','')
pre=r'''
static volatile unsigned bench_completed,bench_fault_line;
#define assert(c) do {if(!(c)){bench_fault_line=__LINE__;bench_completed=2;while(1){}}} while(0)
static int abs(int n){return n<0?-n:n;}
static void*memset(void*v,int c,unsigned n){unsigned char*p=v;while(n--)*p++=(unsigned char)c;return v;}
static void*memcpy(void*v,const void*s,unsigned n){unsigned char*p=v;const unsigned char*q=s;while(n--)*p++=*q++;return v;}
'''
main=r'''
#define REG16(a) (*(volatile unsigned short*)(a))
static volatile unsigned bench_cycles[15][4],bench_counts[15][2];
static unsigned now(void){unsigned hi,lo,n;do{hi=REG16(0x0400010c);lo=REG16(0x04000108);n=REG16(0x0400010c);}while(hi!=n);return(hi<<16)|lo;}
int main(void){unsigned c,a,t,n,phase;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010c)=0;REG16(0x0400010e)=0x84;REG16(0x04000108)=0;REG16(0x0400010a)=0x80;
 for(c=91;c<=105;c++)for(phase=0;phase<3;phase++){
  setup(c);prepare_hit(c);field_count=8;field_x=124;field_y=100;
  if(phase==1)wall(128,106,2,12);
  if(phase==2)wall(126,84,1,32);
  t=now();assert(return_power(c));n=now()-t;if(n>bench_cycles[c-91][0])bench_cycles[c-91][0]=n;
  for(a=1;a<=lifetime[c-91];a++){
   solid_calls=0;t=now();return_powers_tick();n=now()-t;if(n>bench_cycles[c-91][1])bench_cycles[c-91][1]=n;
   if(solid_calls>bench_counts[c-91][0])bench_counts[c-91][0]=solid_calls;
   draws=0;t=now();return_powers_draw();n=now()-t;if(n>bench_cycles[c-91][2])bench_cycles[c-91][2]=n;
   if(draws>bench_counts[c-91][1])bench_counts[c-91][1]=draws;
   t=now();help(c,a);n=now()-t;if(n>bench_cycles[c-91][3])bench_cycles[c-91][3]=n;
   if(ability_cd)ability_cd--;
  }
 }
 bench_completed=1;while(1){}return 0;
}
'''
(OUT/'main.c').write_text(pre+s+main)
sources=[str(OUT/'main.c'),'src/return_powers.c','src/return_power_art.c','src/creatures.c','src/creature_data.c','src/gear_runtime.c','src/combat_rules.c']
flags='-mcpu=arm7tdmi -mthumb-interwork -mthumb -O2 -std=c99 -ffreestanding -fno-builtin -fno-strict-aliasing -fomit-frame-pointer -Wall -Wextra -Wno-unused-function -Wno-unused-const-variable -Wno-misleading-indentation -ffunction-sections -fdata-sections -Isrc'.split();objects=[]
for src in sources:
 obj=OUT/(Path(src).stem+'.o');subprocess.run([arm,*flags,'-c',src,'-o',str(obj)],cwd=ROOT,check=True);objects.append(str(obj))
startup=OUT/'startup.o';subprocess.run([arm,'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-c','src/startup.s','-o',str(startup)],cwd=ROOT,check=True)
elf=OUT/'bench.elf';rom=OUT/'bench.gba';subprocess.run([arm,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,--gc-sections,-T,linker.ld',str(startup),*objects,'-lgcc','-o',str(elf)],cwd=ROOT,check=True);subprocess.run([prefix+'objcopy','-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,'tools/fix_header.py',str(rom)],cwd=ROOT,check=True)
symbols={}
for line in subprocess.check_output([prefix+'nm','-S','--defined-only',str(elf)],text=True).splitlines():
 p=line.split()
 if len(p)==4 and p[3].startswith('bench_'):assert p[3] not in symbols;symbols[p[3]]=(int(p[0],16),int(p[1],16))
for name,size in [('bench_completed',4),('bench_fault_line',4),('bench_cycles',240),('bench_counts',120)]:assert symbols[name][1]==size
sys.path.insert(0,str(ROOT/'tools'));from mgba_runner import Emulator
with Emulator(rom) as e:
 for _ in range(100):
  e.frames(10)
  if e.read(symbols['bench_completed'][0]):break
 assert e.read(symbols['bench_completed'][0])==1,('fault line',e.read(symbols['bench_fault_line'][0]))
 cycles=[[e.read(symbols['bench_cycles'][0]+(c*4+j)*4) for j in range(4)] for c in range(15)];counts=[[e.read(symbols['bench_counts'][0]+(c*2+j)*4) for j in range(2)] for c in range(15)]
r={'scope':'isolated-ARM7TDMI-module-synthetic-scene-not-full-engine-or-controller-acceptance','ROM_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),'columns':['cast','maximum_tick','maximum_draw','maximum_control_intercept'],'waitcnt':'0x4317','commands':{str(c+91):{'cycles':cycles[c],'max_solid_queries':counts[c][0],'max_draws':counts[c][1]} for c in range(15)},'max_tick_plus_draw':max(x[1]+x[2] for x in cycles)}
(OUT/'timing.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r,indent=2))
