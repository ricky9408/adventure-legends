#!/usr/bin/env python3
"""Isolated ARM7TDMI bounded admission slices; synthetic rosters, never FPS/route proof."""
import argparse,hashlib,json,subprocess,sys,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from arm_toolchain import resolve_arm_tools
from mgba_runner import Emulator
MAIN=r'''
#include "creatures.h"
#define REG16(a) (*(volatile unsigned short *)(a))
static CreatureRoster live,snapshot;
volatile unsigned begin_cycles[3][2],step_cycles[3][2][40],commit_cycles[3][2],results[3][2],steps[3][2],completed,error,job_bytes;
static unsigned now(void){unsigned hi,lo,hi2;do{hi=REG16(0x0400010C);lo=REG16(0x04000108);hi2=REG16(0x0400010C);}while(hi!=hi2);return(hi<<16)|lo;}
static void copy_roster(void){unsigned i;for(i=0;i<sizeof live;++i)((unsigned char*)&snapshot)[i]=((unsigned char*)&live)[i];}
int main(void){unsigned scenario,kind,i,count,t,n,slot;CreatureU32 token;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;
 job_bytes=creatures_admission_job_bytes();
 for(scenario=0;scenario<3;++scenario)for(kind=0;kind<2;++kind){
  count=scenario==0?34:scenario==1?50:160;creatures_roster_init(&live);
  if(creatures_grant(&live,49,28,45,0,0)!=0){error=1;completed=2;while(1){}}
  live.instances[0].trial_flags=3;
  for(i=1;i<count;++i)if(creatures_grant(&live,1,50,100,0,0)!=i){error=2;completed=2;while(1){}}
  copy_roster();t=now();token=creatures_admission_job_begin(&snapshot,kind?50:52,kind?0:255);begin_cycles[scenario][kind]=now()-t;
  if(!token){error=3;completed=2;while(1){}}
  for(n=0;n<40;++n){int answer;t=now();answer=creatures_admission_job_step(token,4);step_cycles[scenario][kind][n]=now()-t;if(answer){++n;break;}}
  steps[scenario][kind]=n;t=now();results[scenario][kind]=kind?creatures_admission_job_commit_evolution(token,&live,1024,1,1):creatures_admission_job_commit_grant(token,&live,28,20,0,0,&slot);commit_cycles[scenario][kind]=now()-t;
 }
 completed=1;while(1){}return 0;
}
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=ROOT/'docs/evidence/underwater-admission-arm.json');args=parser.parse_args()
 arm=resolve_arm_tools('gcc','objcopy','nm','size',root=ROOT)
 inputs=[ROOT/'src'/f for f in ['creatures.h','creatures.c','creature_data.c','creature_history_v5.inc','creature_admission_job.inc']]
 hashes={str(p.relative_to(ROOT)):sha(p) for p in inputs}
 report={'scope':__doc__,'source_sha256':hashes,'waitcnt':'0x4317','frame_cycles':280896,'record_budget':4,'cases':[]}
 with tempfile.TemporaryDirectory(prefix='uw-admission-arm-') as d:
  out=Path(d);(out/'main.c').write_text(MAIN)
  flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-pedantic','-fstack-usage','-I'+str(ROOT/'src')]
  for name,p in {'main':out/'main.c','creatures':ROOT/'src/creatures.c','creature_data':ROOT/'src/creature_data.c'}.items():subprocess.run([arm['gcc'],*flags,'-c',str(p),'-o',str(out/f'{name}.o')],check=True)
  subprocess.run([arm['gcc'],'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c',str(ROOT/'src/startup.s'),'-o',str(out/'startup.o')],check=True)
  elf=out/'profile.elf';rom=out/'profile.gba'
  subprocess.run([arm['gcc'],'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,-T,'+str(ROOT/'linker.ld'),*[str(out/f'{n}.o') for n in ['startup','main','creatures','creature_data']],'-lgcc','-o',str(elf)],check=True)
  subprocess.run([arm['objcopy'],'-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,str(ROOT/'tools/fix_header.py'),str(rom)],check=True,capture_output=True)
  symbols={a[2]:int(a[0],16) for line in subprocess.check_output([arm['nm'],'-n',str(elf)],text=True).splitlines() if len(a:=line.split())==3}
  with Emulator(rom) as emu:
   for _ in range(100):
    emu.frames(120)
    if emu.read(symbols['completed']):break
   assert emu.read(symbols['completed'])==1,emu.read(symbols['error'])
   report['job_mutable_bytes']=emu.read(symbols['job_bytes'])
   for scenario,count in enumerate([34,50,160]):
    for kind,name in enumerate(['grant','evolution']):
     index=scenario*2+kind;steps=emu.read(symbols['steps']+index*4);assert steps==40
     slices=[emu.read(symbols['step_cycles']+(index*40+i)*4) for i in range(steps)]
     row={'retained':count,'operation':name,'begin_cycles':emu.read(symbols['begin_cycles']+index*4),'step_cycles':slices,'max_step_cycles':max(slices),'commit_cycles':emu.read(symbols['commit_cycles']+index*4),'result':emu.read(symbols['results']+index*4)}
     assert row['result']==(3 if count==160 and kind==0 else 0)
     report['cases'].append(row);print(count,name,row['begin_cycles'],row['max_step_cycles'],row['commit_cycles'],flush=True)
  report['compiler_static_frames']=(out/'creatures.su').read_text().splitlines()
  report['object_sections']={n:subprocess.check_output([arm['size'],'-A',str(out/f'{n}.o')],text=True) for n in ['creatures','creature_data']}
  report['rom_sha256']=sha(rom)
 report['source_unchanged']=hashes=={str(p.relative_to(ROOT)):sha(p) for p in inputs};assert report['source_unchanged']
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,indent=2)+'\n');assert args.output.stat().st_size<90000
if __name__=='__main__':main()
