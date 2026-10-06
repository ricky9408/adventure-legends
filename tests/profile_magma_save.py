#!/usr/bin/env python3
"""Isolated ARM validation/write timing; no claim about whole-engine cadence."""
import argparse,hashlib,json,os,subprocess,sys,tempfile
from pathlib import Path
from test_magma_save_limits import ROOT,SOURCES,prepare,sha,FIXTURE,FIXTURE_SHA
from test_southern_save_limits import object_sizes
sys.path.insert(0,str(ROOT/'tools'))
from arm_toolchain import resolve_arm_tools
from mgba_runner import Emulator
MAIN=r'''
#include "magma_quests.h"
#ifdef AUTHENTIC34
#include "magma_earned34.h"
#endif
int magma_test_southern(Save5State*);int magma_test_completed(Save5State*,unsigned);int magma_test_full48(Save5State*);
#ifndef BENCH_BUDGET
#define BENCH_BUDGET 1024
#endif
#define REG16(a) (*(volatile unsigned short *)(a))
void *memcpy(void*d,const void*s,unsigned n){unsigned char*a=d;const unsigned char*b=s;while(n--)*a++=*b++;return d;}
static Save5State state;
volatile unsigned begin_cycles[4][3],step_cycles[4][3][256],step_counts[4][3],results[4][3],validation_cycles[4][4],validation_results[4][4],counts[4],completed,fixture_error;
const char sram_id[]="SRAM_V113";
static unsigned now(void){unsigned hi,lo,hi2;do{hi=REG16(0x0400010C);lo=REG16(0x04000108);hi2=REG16(0x0400010C);}while(hi!=hi2);return(hi<<16)|lo;}
static void bench(unsigned n,unsigned k){unsigned t=now(),i=0;
 results[n][k]=(unsigned)save5_begin(&state);begin_cycles[n][k]=now()-t;
 while(save5_status()==SAVE5_BUSY&&i<256){t=now();save5_step(BENCH_BUDGET);step_cycles[n][k][i++]=now()-t;}
 step_counts[n][k]=i;results[n][k]=save5_status();}
int main(void){unsigned n,k,t;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;
 for(n=0;n<4;++n){
#ifndef SYNTHETIC_FULL48
  if(n==3)continue;
#endif
  fixture_error=n?magma_test_completed(&state,n>=2):magma_test_southern(&state);
#ifdef AUTHENTIC34
  if(n==1){for(k=0;k<32768;++k)((volatile unsigned char*)0x0E000000)[k]=magma_earned34[k];fixture_error=save5_load(&state)?0:999;}
#endif
#ifdef SYNTHETIC_FULL48
  if(n==3&&!fixture_error)fixture_error=magma_test_full48(&state);
#endif
  if(fixture_error){completed=2;while(1){}}
  counts[n]=creatures_roster_count(&state.roster);
  for(k=0;k<4;++k){t=now();validation_results[n][k]=k&1?save5_validate_revision(&state,n?5:4):save5_validate(&state);validation_cycles[n][k]=now()-t;}
  for(k=0;k<3;++k)bench(n,k);
 }
 completed=1;while(1){}return 0;
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/magma-save-arm.json');p.add_argument('--authentic34',type=Path);p.add_argument('--authentic34-sha256');args=p.parse_args()
 if args.authentic34:
  assert args.authentic34_sha256 and sha(args.authentic34)==args.authentic34_sha256,'Authenticate the earned controller fixture explicitly'
 prefix=os.environ.get('ARM_PREFIX',str(ROOT/'tools/sysroot/usr/bin/arm-none-eabi-'));cc=prefix+'gcc'
 flags=['-I',str(ROOT/'src'),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-fstack-usage']
 report=dict(purpose='Isolated ARM7TDMI save validation and bounded steps; not native world acquisition or whole-engine frame cadence',fixture_sha256=FIXTURE_SHA,authentic34_sha256=args.authentic34_sha256,waitcnt='0x4317',timer_clock_hz=16777216,frame_cycles=280896,effective_budget_cap=3072,compiler=subprocess.check_output([cc,'--version'],text=True).splitlines()[0],source_sha256={n:sha(ROOT/'src'/f'{n}.c') for n in SOURCES},variants=[])
 with tempfile.TemporaryDirectory(prefix='magma-native-save-') as tmp:
  for synthetic in (False,True):
   out=Path(tmp)/('synthetic-full48' if synthetic else 'authored');out.mkdir();sources=prepare(out,synthetic,synthetic);localflags=flags+['-I',str(out)]
   (out/'main.c').write_text(MAIN)
   if args.authentic34:
    data=args.authentic34.read_bytes();assert len(data)==32768
    (out/'magma_earned34.h').write_text('static const unsigned char magma_earned34[32768]={'+','.join(map(str,data))+'};\n')
   for name,path in sources.items():subprocess.run([cc,*localflags,'-c',str(path),'-o',str(out/f'{name}.o')],check=True)
   subprocess.run([cc,*localflags,'-DMAGMA_SETUP_ONLY','-c',str(ROOT/'tests/magma_save_sanitizer.c'),'-o',str(out/'setup.o')],check=True)
   subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c',str(ROOT/'src/startup.s'),'-o',str(out/'startup.o')],check=True)
   variant=dict(synthetic_gear_catalog=synthetic,temporary_additions='47 zero-stat body definitions and revision5-only codec rows100–146' if synthetic else None,object_sizes={n:object_sizes(prefix,out/f'{n}.o') for n in SOURCES},own_function_stack_usage={n:(out/f'{n}.su').read_text() for n in SOURCES},budgets=[])
   for budget in (1024,3072,4096):
    subprocess.run([cc,*localflags,f'-DBENCH_BUDGET={budget}',*(['-DSYNTHETIC_FULL48'] if synthetic else []),*(['-DAUTHENTIC34'] if args.authentic34 else []),'-c',str(out/'main.c'),'-o',str(out/'main.o')],check=True)
    elf=out/f'timing-{budget}.elf';rom=out/f'timing-{budget}.gba'
    subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,-T,'+str(ROOT/'linker.ld'),*[str(out/f'{n}.o') for n in ('startup','main','setup',*SOURCES)],'-lgcc','-o',str(elf)],check=True)
    subprocess.run([prefix+'objcopy','-O','binary',str(elf),str(rom)],check=True)
    subprocess.run([sys.executable,str(ROOT/'tools/fix_header.py'),str(rom)],check=True,capture_output=True)
    nm=subprocess.check_output([prefix+'nm','-n',str(elf)],text=True);symbols={x[2]:int(x[0],16) for l in nm.splitlines() if len(x:=l.split())==3};cases=[]
    with Emulator(rom) as e:
     for _ in range(100):
      e.frames(600)
      if e.read(symbols['completed']):break
     assert e.read(symbols['completed'])==1,('fixture setup',e.read(symbols['fixture_error']))
     labels=('authentic-S3-21',('authentic-Magma34' if args.authentic34 else 'synthetic-Magma34'),'synthetic-Magma160','synthetic-Magma160-full48')
     for n in range(4 if synthetic else 3):
      count=e.read(symbols['counts']+n*4);assert count==(21 if n==0 else 34 if n==1 else 160)
      validation=[e.read(symbols['validation_cycles']+(n*4+k)*4) for k in range(4)]
      assert all(e.read(symbols['validation_results']+(n*4+k)*4)==1 for k in range(4))
      writes=[]
      for k in range(3):
       steps=e.read(symbols['step_counts']+(n*3+k)*4);status=e.read(symbols['results']+(n*3+k)*4)
       assert status==2 and 0<steps<256,(n,k,status,steps)
       values=[e.read(symbols['step_cycles']+((n*3+k)*256+j)*4) for j in range(steps)]
       writes.append(dict(begin_cycles=e.read(symbols['begin_cycles']+(n*3+k)*4),steps=steps,max_step_cycles=max(values),step_cycles=values,status=status))
      cases.append(dict(scenario=labels[n],roster=count,gear_records=48 if n==3 else 25 if n==0 else 31,blocking_current_cycles=validation[::2],blocking_declared_revision_cycles=validation[1::2],writes=writes))
    maxstep=max(w['max_step_cycles'] for c in cases for w in c['writes']);maxbegin=max(w['begin_cycles'] for c in cases for w in c['writes'])
    limit=70000 if budget==1024 else 230000
    variant['budgets'].append(dict(requested_budget=budget,max_begin_cycles=maxbegin,max_step_cycles=maxstep,step_limit_cycles=limit,within_prior_isolated_limits=maxbegin<70000 and maxstep<limit,rom_sha256=sha(rom),cases=cases))
    print('synthetic48',synthetic,'budget',budget,'begin',maxbegin,'step',maxstep,'prior-limit',limit,flush=True)
   report['variants'].append(variant)
 report['source_unchanged_during_measurement']=report['source_sha256']=={n:sha(ROOT/'src'/f'{n}.c') for n in SOURCES}
 report['within_prior_isolated_limits']=all(b['within_prior_isolated_limits'] for v in report['variants'] for b in v['budgets'])
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,separators=(',',':'))+'\n');print('Report',args.output)
 if not report['within_prior_isolated_limits']:raise SystemExit('Isolated timing limit exceeded; optimize before acceptance')
if __name__=='__main__':main()
