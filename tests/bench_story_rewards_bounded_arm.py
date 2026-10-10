#!/usr/bin/env python3
"""Actual ARM bounded story validation/commit timing; isolated diagnostic ROM."""
from pathlib import Path
import hashlib,json,subprocess,sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
out=ROOT/'build/story-rewards-bounded-arm';out.mkdir(parents=True,exist_ok=True)
original=(ROOT/'build/story-rewards-arm/bench.c').read_text();head=original[:original.index('int main(void)')]
head=head.replace('static CreatureRoster working;','static CreatureRoster working,snapshot;')
main=r'''
int main(void){unsigned row,t,token,status,n,elapsed;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010c)=0;REG16(0x0400010e)=0x84;REG16(0x04000108)=0;REG16(0x0400010a)=0x80;
 for(row=0;row<5;row++){
  memcpy(&snapshot,sources[row],sizeof snapshot);memcpy(&working,&snapshot,sizeof working);
  t=now();token=creatures_story_job_begin(&snapshot,7);bench_cycles[row][0]=now()-t;
  if(!token){bench_failed=1;while(1){}}
  for(n=0;n<100;n++){
   t=now();status=(unsigned)creatures_admission_job_step(token,4);elapsed=now()-t;
   if(elapsed>bench_cycles[row][1])bench_cycles[row][1]=elapsed;
   if(status==1)break;
   if(status!=0){bench_failed=2;while(1){}}
  }
  bench_cycles[row][3]=n+1;
  t=now();status=(unsigned)creatures_story_job_commit(token,&working);bench_cycles[row][2]=now()-t;
  if(!status||!creatures_roster_validate(&working)){bench_failed=3;while(1){}}
 }
 bench_done=1;while(1){}return 0;
}
'''
source=out/'bench.c';source.write_text(head+main);arm=ROOT/'tools/sysroot/usr/bin/arm-none-eabi-gcc';prefix=str(arm).removesuffix('gcc')
flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-ffunction-sections','-fdata-sections','-fstack-usage','-Isrc']
objects=[]
for path in [source,ROOT/'src/creatures.c',ROOT/'src/creature_data.c']:
 obj=out/(path.stem+'.o');subprocess.run([str(arm),*flags,'-c',str(path),'-o',str(obj)],cwd=ROOT,check=True);objects.append(obj)
startup=out/'startup.o';subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-c','src/startup.s','-o',str(startup)],cwd=ROOT,check=True)
elf=out/'bench.elf';rom=out/'bench.gba';subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,--gc-sections','-Wl,-T,linker.ld',str(startup),*[str(p)for p in objects],'-lgcc','-o',str(elf)],cwd=ROOT,check=True)
subprocess.run([prefix+'objcopy','-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,'tools/fix_header.py',str(rom)],cwd=ROOT,check=True)
sym={p[2]:int(p[0],16)for line in subprocess.check_output([prefix+'nm','-n',str(elf)],text=True).splitlines()if len(p:=line.split())==3}
with Emulator(rom)as e:
 for _ in range(200):
  e.frames(10)
  if e.read(sym['bench_done'])or e.read(sym['bench_failed']):break
 assert e.read(sym['bench_done'])and not e.read(sym['bench_failed'])
 cycles=[[e.read(sym['bench_cycles']+(row*5+op)*4)for op in range(4)]for row in range(5)]
report={'scope':__doc__,'roster_counts':[2,18,72,157,160],'columns':['begin','max_validation_step','atomic_commit','steps'],'cycles':cycles,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()for p in [ROOT/'src/creatures.c',ROOT/'src/creature_admission_job.inc',ROOT/'src/creature_data.c']},'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest()}
(out/'timing.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
