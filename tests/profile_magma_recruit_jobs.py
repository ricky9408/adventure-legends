#!/usr/bin/env python3
"""Native ARM isolated synchronous-before vs bounded-after branch transactions.

The unmodified historical synchronous API and new runtime job execute on the
same ROM, source save and clock. This excludes full-engine drawing and IRQs.
"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from arm_toolchain import resolve_arm_tools
from mgba_runner import Emulator
MAIN=r'''
#include "magma_quests.h"
#include "magma_recruit_fixtures.h"
#define REG16(a) (*(volatile unsigned short *)(a))
void *memcpy(void*d,const void*s,unsigned n){unsigned char*a=d;const unsigned char*b=s;while(n--)*a++=*b++;return d;}
void *memset(void*d,int c,unsigned n){unsigned char*a=d;while(n--)*a++=(unsigned char)c;return d;}
int memcmp(const void*a,const void*b,unsigned n){const unsigned char*x=a,*y=b;while(n--){if(*x!=*y)return *x-*y;++x;++y;}return 0;}
static Save5State base,live,expected;
volatile unsigned sync_cycles[3][4],begin_cycles[3][4],phase_cycles[3][4][16],phase_calls[3][4][16],results[3][4],completed,error;
static unsigned now(void){unsigned hi,lo,hi2;do{hi=REG16(0x0400010C);lo=REG16(0x04000108);hi2=REG16(0x0400010C);}while(hi!=hi2);return(hi<<16)|lo;}
int main(void){unsigned n,j,i,t,token,phase,status=SAVE5_FAILED,elapsed;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;
 for(n=0;n<3;++n){
  for(i=0;i<32768;++i)((volatile unsigned char*)0x0e000000)[i]=(n?recruit_104_fixture:recruit_65_fixture)[i];
  if(!save5_load(&base)){error=1;break;}
  if(n==2)while(creatures_roster_count(&base.roster)<160)if(creatures_grant(&base.roster,1,50,100,0,0)==255){error=2;break;}
  for(j=0;j<4;++j){
   expected=base;t=now();results[n][j]=magma_branch_recruit(&expected,16+j);sync_cycles[n][j]=now()-t;
   live=base;t=now();token=magma_recruit_job_begin(&live,16+j,17);begin_cycles[n][j]=now()-t;
   if(!token){error=3;break;}
   do{
    phase=magma_recruit_job_phase(token);phase=phase?11+phase:save5_preflight_phase(token);
    if(phase>14){error=4;break;}
    t=now();status=magma_recruit_job_step(token,640,17);elapsed=now()-t;
    if(elapsed>phase_cycles[n][j][phase])phase_cycles[n][j][phase]=elapsed;
    ++phase_calls[n][j][phase];
    if(phase!=14&&memcmp(&live,&base,sizeof live)){error=5;break;}
   }while(status==SAVE5_BUSY);
   if(status!=SAVE5_DONE||(unsigned)magma_recruit_job_result(token)!=results[n][j]||memcmp(&live,&expected,sizeof live)){error=6;break;}
   magma_recruit_job_cancel();
  }
  if(error)break;
 }
 completed=error?2:1;while(1){}return 0;
}
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'build/return-bounded-magma-arm');p.add_argument('--source-root',type=Path,default=ROOT);p.add_argument('--fixture104',type=Path,default=ROOT/'build/return-controller-b-full-04/05-all104-cold-reboot-after.sav');a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);src=a.source_root.resolve();o=a.output.resolve()
 tools=resolve_arm_tools('gcc','objcopy','nm',root=ROOT);cc=tools['gcc'];old=ROOT/'tests/fixtures/v5-revision5/magma-all65-town.sav'
 assert sha(old)=='a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858';assert sha(a.fixture104)=='d482466d04050c3d7f2e8eb8e1960729c9b9b33aa3e32440d186a4b54b854a69'
 (o/'magma_recruit_fixtures.h').write_text('\n'.join('static const unsigned char '+n+'[32768]={'+','.join(map(str,f.read_bytes()))+'};' for n,f in [('recruit_65_fixture',old),('recruit_104_fixture',a.fixture104)]));(o/'main.c').write_text(MAIN)
 mods=['save4','save5','creatures','creature_data','equipment','equipment_data','magma_quests'];flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-fstack-usage','-ffunction-sections','-fdata-sections','-I'+str(src/'src'),'-I'+str(o)]
 manifest={str(f.relative_to(src)):sha(f) for f in (src/'src').rglob('*') if f.is_file()}
 for n,f in [('main',o/'main.c')]+[(n,src/'src'/f'{n}.c') for n in mods]:subprocess.run([cc,*flags,'-c',str(f),'-o',str(o/f'{n}.o')],check=True)
 subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c',str(src/'src/startup.s'),'-o',str(o/'startup.o')],check=True)
 elf=o/'profile.elf';rom=o/'profile.gba';subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,--gc-sections','-Wl,-T,'+str(src/'linker.ld'),*[str(o/f'{n}.o') for n in ('startup','main',*mods)],'-lgcc','-o',str(elf)],check=True);subprocess.run([tools['objcopy'],'-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,str(ROOT/'tools/fix_header.py'),str(rom)],check=True,capture_output=True)
 symbols={x[2]:int(x[0],16) for line in subprocess.check_output([tools['nm'],'-n',str(elf)],text=True).splitlines() if len(x:=line.split())==3};report={'scope':__doc__,'rom_sha256':sha(rom),'fixture104_sha256':sha(a.fixture104),'source_sha256':manifest,'cases':[]}
 with Emulator(rom) as e:
  for _ in range(100):
   e.frames(300)
   if e.read(symbols['completed']):break
  assert e.read(symbols['completed'])==1,e.read(symbols['error'])
  for n,count in enumerate((34,52,160)):
   for j in range(4):
    cycles=[e.read(symbols['phase_cycles']+((n*4+j)*16+i)*4) for i in range(15)];calls=[e.read(symbols['phase_calls']+((n*4+j)*16+i)*4) for i in range(15)];row={'retained':count,'source':j+16,'result':e.read(symbols['results']+(n*4+j)*4),'synchronous_cycles':e.read(symbols['sync_cycles']+(n*4+j)*4),'begin_cycles':e.read(symbols['begin_cycles']+(n*4+j)*4),'phase_cycles':cycles,'phase_calls':calls,'steps':sum(calls),'noncommit_max':max(cycles[:14]),'commit_cycles':cycles[14]};report['cases'].append(row);print(count,j+16,row['synchronous_cycles'],row['noncommit_max'],row['commit_cycles'],row['steps'],flush=True)
 report['source_unchanged']=manifest=={str(f.relative_to(src)):sha(f) for f in (src/'src').rglob('*') if f.is_file()};report['result']='PASS' if report['source_unchanged'] and all(r['noncommit_max']<90000 and r['commit_cycles']<280896 and r['steps']<150 for r in report['cases']) else 'FAIL';(o/'report.json').write_text(json.dumps(report,indent=2)+'\n');assert report['result']=='PASS'
if __name__=='__main__':main()
