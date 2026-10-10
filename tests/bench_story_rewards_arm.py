#!/usr/bin/env python3
"""Isolated actual ARM timings of original story operations; not full-frame acceptance."""
from pathlib import Path
import ctypes as C,hashlib,json,subprocess,sys,tempfile
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
import covenants_host_support as host
out=ROOT/'build/story-rewards-arm';out.mkdir(parents=True,exist_ok=True)
with tempfile.TemporaryDirectory()as d:
 l=host.build(d);sources=[]
 for count,chapter in [(2,0),(18,3),(72,7),(157,0),(160,7)]:
  r=host.Roster();assert l.creatures_migrate_legacy(C.byref(r),chapter,0)
  for n in range(sum(bool(c.form_id)for c in r.instances),count):assert l.creatures_grant(C.byref(r),1,1+n%50,20,0,0)<160
  assert l.creatures_roster_validate(C.byref(r));sources.append(bytes(r))
size=len(sources[0]);blob='static const unsigned char sources[5]['+str(size)+']={'+','.join('{'+','.join(map(str,s))+'}'for s in sources)+'};\n'
head=r'''
#include "creatures.h"
static void*memcpy(void*d,const void*s,unsigned n){unsigned char*a=d;const unsigned char*b=s;while(n--)*a++=*b++;return d;}
volatile unsigned bench_done,bench_failed,bench_cycles[5][5];
static CreatureRoster working;
#define REG16(a) (*(volatile unsigned short *)(a))
static unsigned now(void){unsigned hi,lo,n;do{hi=REG16(0x0400010c);lo=REG16(0x04000108);n=REG16(0x0400010c);}while(hi!=n);return(hi<<16)|lo;}
'''
main=r'''
int main(void){unsigned row,op,t;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010c)=0;REG16(0x0400010e)=0x84;REG16(0x04000108)=0;REG16(0x0400010a)=0x80;
 for(row=0;row<5;row++)for(op=0;op<5;op++){
  memcpy(&working,sources[row],sizeof working);
  if(!creatures_roster_validate(&working)){bench_failed=1;while(1){}}
  t=now();if(op<4)creatures_grant_story(&working,op,7);else creatures_apply_story_floors(&working,7);
  bench_cycles[row][op]=now()-t;
 }
 bench_done=1;while(1){}return 0;
}
'''
source=out/'bench.c';source.write_text(head+blob+main);arm=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc';prefix=str(arm).removesuffix('gcc')
flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections','-Isrc']
objects=[]
for path in [source,ROOT/'src/creatures.c',ROOT/'src/creature_data.c']:
 obj=out/(path.stem+'.o');subprocess.run([str(arm),*flags,'-c',str(path),'-o',str(obj)],cwd=ROOT,check=True);objects.append(obj)
startup=out/'startup.o';subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-c','src/startup.s','-o',str(startup)],cwd=ROOT,check=True)
elf=out/'bench.elf';rom=out/'bench.gba';subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,--gc-sections','-Wl,-T,linker.ld',str(startup),*[str(p)for p in objects],'-lgcc','-o',str(elf)],cwd=ROOT,check=True)
subprocess.run([prefix+'objcopy','-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,'tools/fix_header.py',str(rom)],cwd=ROOT,check=True)
sym={p[2]:int(p[0],16)for line in subprocess.check_output([prefix+'nm','-n',str(elf)],text=True).splitlines()if len(p:=line.split())==3}
with Emulator(rom)as e:
 for _ in range(400):
  e.frames(10)
  if e.read(sym['bench_done'])or e.read(sym['bench_failed']):break
 assert e.read(sym['bench_done'])and not e.read(sym['bench_failed'])
 cycles=[[e.read(sym['bench_cycles']+(row*5+op)*4)for op in range(5)]for row in range(5)]
report={'scope':__doc__,'roster_counts':[2,18,72,157,160],'columns':['story0','story1','story2','story3','floors'],'cycles':cycles,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [ROOT/'src/creatures.c',ROOT/'src/creature_admission_job.inc',ROOT/'src/creature_data.c']},'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest()}
(out/'original-operations.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
