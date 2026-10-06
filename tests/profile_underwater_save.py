#!/usr/bin/env python3
"""Isolated ARM7TDMI cold transaction + validation + writer costs, not FPS."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
from test_underwater_save import ROOT,SOURCES,prepare,sha,FIXTURE_SHA,runtime_hashes
sys.path.insert(0,str(ROOT/'tools'))
from arm_toolchain import resolve_arm_tools
from mgba_runner import Emulator
LABELS=('save5_validate','save5_validate_revision6','first_source_status','repeat_source_status','trial_status','visit_existing','anchor_transaction','quest_claim_transaction','repeat_grant_transaction','trial_complete_transaction')
MAIN=r'''
#include "underwater_quests.h"
int underwater_test_earned34(Save5State*);int underwater_test_completed(Save5State*,unsigned);int underwater_test_ready(Save5State*,unsigned);unsigned underwater_test_slot(const Save5State*,unsigned);
#define REG16(a) (*(volatile unsigned short *)(a))
#ifndef BENCH_BUDGET
#define BENCH_BUDGET 1024
#endif
void *memcpy(void*d,const void*s,unsigned n){unsigned char*a=d;const unsigned char*b=s;while(n--)*a++=*b++;return d;}
static Save5State state,baseline;
volatile unsigned cycles[3][10][3],results[3][10][3],counts[3],completed,fixture_error;
volatile unsigned begin_cycles[3][3],step_cycles[3][3][512],step_counts[3][3],write_results[3][3];
const char sram_id[]="SRAM_V113";
static unsigned now(void){unsigned hi,lo,hi2;do{hi=REG16(0x0400010C);lo=REG16(0x04000108);hi2=REG16(0x0400010C);}while(hi!=hi2);return(hi<<16)|lo;}
static unsigned measure(unsigned test,unsigned slot){
 switch(test){
 case 0:return save5_validate(&state);
 case 1:return save5_validate_revision(&state,6);
 case 2:return underwater_source_status(&state,1);
 case 3:return underwater_branch_status(&state,1);
 case 4:return underwater_trial_status(&state,slot,state.roster.instances[slot].instance_id,17,1,1);
 case 5:return underwater_visit(&state,46);
 case 6:return underwater_anchor(&state,46);
 case 7:return underwater_quest_claim(&state,38);
 case 8:return underwater_branch_recruit(&state,1);
 case 9:return underwater_trial_complete(&state,slot,state.roster.instances[slot].instance_id,17,1,1);
 default:return 0;
 }
}
#ifdef UNDERWATER_FULL48
static void full48(Save5State*s){unsigned i,j;
 for(i=1;i<48;++i){EquipmentRecord*r=&s->equipment.bag[i];r->item_id=(unsigned short)(99+i);r->rank=r->flags=0;r->quantity=1;
  for(j=0;j<3;++j)r->reserved[j]=0;
  s->equipment.seen[r->item_id>>3]|=(unsigned char)(1u<<(r->item_id&7));}
 s->equipment.equipped[0]=0;for(i=1;i<5;++i)s->equipment.equipped[i]=255;
}
#endif
int main(void){unsigned n,j,k,t,slot,steps;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;
 for(n=0;n<3;++n){fixture_error=n?underwater_test_completed(&baseline,n==2):underwater_test_earned34(&baseline);
  if(fixture_error){completed=2;while(1){}}
#ifdef UNDERWATER_FULL48
  if(n==2)full48(&baseline);
#endif
  counts[n]=creatures_roster_count(&baseline.roster);
  for(j=0;j<10;++j)for(k=0;k<3;++k){
   memcpy(&state,&baseline,sizeof state);slot=underwater_test_slot(&state,50);if(slot==255)slot=0;
   /* Receipt-specific setup is deliberately outside the measured operation. */
   if(j==7&&n==0){if(underwater_visit(&state,46)!=1||underwater_test_ready(&state,38)){fixture_error=100;completed=2;while(1){}}}
   if(j==9&&n==1){if(underwater_branch_recruit(&state,1)!=3){fixture_error=101;completed=2;while(1){}}slot=underwater_test_slot(&state,49);}
   t=now();results[n][j][k]=measure(j,slot);cycles[n][j][k]=now()-t;
  }
  memcpy(&state,&baseline,sizeof state);
  for(k=0;k<3;++k){t=now();write_results[n][k]=save5_begin(&state);begin_cycles[n][k]=now()-t;steps=0;
   while(save5_status()==SAVE5_BUSY&&steps<512){t=now();save5_step(BENCH_BUDGET);step_cycles[n][k][steps++]=now()-t;}
   step_counts[n][k]=steps;write_results[n][k]=save5_status();}
 }
 completed=1;while(1){}return 0;
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/underwater-save-arm.json');p.add_argument('--budgets',type=int,nargs='+',default=[1024,3072]);p.add_argument('--synthetic-full48',action='store_true');args=p.parse_args()
 arm=resolve_arm_tools('gcc','objcopy','nm',root=ROOT);cc=arm['gcc']
 report={'scope':'Isolated cold ARM7TDMI validation and typed transactions; no full-engine cadence or native Underwater acquisition claim','fixture_sha256':FIXTURE_SHA,'waitcnt':'0x4317','timer_clock_hz':16777216,'frame_cycles':280896,'source_sha256':runtime_hashes(),'variants':[]}
 with tempfile.TemporaryDirectory(prefix='underwater-arm-profile-') as td:
  out=Path(td);sources=prepare(out,args.synthetic_full48,args.synthetic_full48);(out/'main.c').write_text(MAIN)
  report['compiled_source_sha256']={n:sha(path) for n,path in sources.items()};report['synthetic_full48']=args.synthetic_full48
  flags=[*(['-DUNDERWATER_FULL48'] if args.synthetic_full48 else []),'-I'+str(ROOT/'src'),'-I'+str(out),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-fstack-usage']
  for n,path in {**sources,'setup':ROOT/'tests/underwater_save_setup.c'}.items():subprocess.run([cc,*flags,'-c',str(path),'-o',str(out/f'{n}.o')],check=True)
  subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c',str(ROOT/'src/startup.s'),'-o',str(out/'startup.o')],check=True)
  report['stack_usage']={n:(out/f'{n}.su').read_text().splitlines() for n in ('save5','underwater_quests','equipment')}
  for budget in args.budgets:
   subprocess.run([cc,*flags,f'-DBENCH_BUDGET={budget}','-c',str(out/'main.c'),'-o',str(out/'main.o')],check=True)
   elf=out/'timing.elf';rom=out/'timing.gba'
   subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,-T,'+str(ROOT/'linker.ld'),*[str(out/f'{n}.o') for n in ('startup','main','setup',*SOURCES)],'-lgcc','-o',str(elf)],check=True)
   subprocess.run([arm['objcopy'],'-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,str(ROOT/'tools/fix_header.py'),str(rom)],check=True,capture_output=True)
   symbols={x[2]:int(x[0],16) for line in subprocess.check_output([arm['nm'],'-n',str(elf)],text=True).splitlines() if len(x:=line.split())==3};variant={'budget':budget,'rom_sha256':sha(rom),'cases':[]}
   with Emulator(rom) as emu:
    for _ in range(100):
     emu.frames(600)
     if emu.read(symbols['completed']):break
    assert emu.read(symbols['completed'])==1,('setup failed',emu.read(symbols['fixture_error']))
    for n,label in enumerate(('authentic-Magma34','synthetic-Underwater50','synthetic-grandfathered160')):
     row={'label':label+('-temporary-full48' if args.synthetic_full48 and n==2 else ''),'retained':emu.read(symbols['counts']+n*4),'operations':{},'writes':[]}
     assert row['retained']==(34,50,160)[n]
     for j,name in enumerate(LABELS):
      values=[emu.read(symbols['cycles']+((n*10+j)*3+k)*4) for k in range(3)];results=[emu.read(symbols['results']+((n*10+j)*3+k)*4) for k in range(3)]
      row['operations'][name]={'cycles':values,'max_cycles':max(values),'results':results}
     for k in range(3):
      count=emu.read(symbols['step_counts']+(n*3+k)*4);result=emu.read(symbols['write_results']+(n*3+k)*4);assert result==2,(n,k,result,count)
      steps=[emu.read(symbols['step_cycles']+((n*3+k)*512+i)*4) for i in range(count)]
      row['writes'].append({'begin_cycles':emu.read(symbols['begin_cycles']+(n*3+k)*4),'steps':count,'max_step_cycles':max(steps),'step_cycles':steps})
     variant['cases'].append(row)
     print(budget,label,{name:r['max_cycles'] for name,r in row['operations'].items()},'max-step',max(w['max_step_cycles'] for w in row['writes']),flush=True)
   report['variants'].append(variant)
 report['source_unchanged_during_measurement']=report['source_sha256']==runtime_hashes()
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,separators=(',',':'))+'\n');assert args.output.stat().st_size<90000
 print(args.output)
if __name__=='__main__':main()
