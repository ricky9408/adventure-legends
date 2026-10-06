#!/usr/bin/env python3
"""Every bounded raw-save/prepared-transaction phase on ARM; not frame cadence."""
import argparse,json,subprocess,sys,tempfile
from pathlib import Path
from test_underwater_save import ROOT,SOURCES,prepare,sha,FIXTURE_SHA,runtime_hashes
sys.path.insert(0,str(ROOT/'tools'))
from arm_toolchain import resolve_arm_tools
from mgba_runner import Emulator
MAIN=r'''
#include "underwater_quests.h"
int underwater_test_earned34(Save5State*);int underwater_test_completed(Save5State*,unsigned);int underwater_test_ready(Save5State*,unsigned);unsigned underwater_test_slot(const Save5State*,unsigned);
#define REG16(a) (*(volatile unsigned short *)(a))
void *memcpy(void*d,const void*s,unsigned n){unsigned char*a=d;const unsigned char*b=s;while(n--)*a++=*b++;return d;}
void *memset(void*d,int c,unsigned n){unsigned char*a=d;while(n--)*a++=(unsigned char)c;return d;}
static Save5State state,baseline;
volatile unsigned begin_cycles[3][6],phase_cycles[3][6][20],phase_calls[3][6][20],results[3][6],counts[3][6],completed,fixture_error;
const char sram_id[]="SRAM_V113";
static unsigned now(void){unsigned hi,lo,hi2;do{hi=REG16(0x0400010C);lo=REG16(0x04000108);hi2=REG16(0x0400010C);}while(hi!=hi2);return(hi<<16)|lo;}
static void clear_request(UnderwaterRequest*r){unsigned i;for(i=0;i<sizeof(*r)/4;++i)((unsigned*)r)[i]=0;}
int main(void){unsigned n,j,t,phase,elapsed,slot,i,token,st;UnderwaterRequest request;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;
 for(n=0;n<3;++n){fixture_error=n?underwater_test_completed(&baseline,n==2):underwater_test_earned34(&baseline);
  if(fixture_error){completed=2;while(1){}}
  for(j=0;j<6;++j){memcpy(&state,&baseline,sizeof state);clear_request(&request);
   if(j==0||j==5){request.operation=UW_REQUEST_REPEAT_RECRUIT;request.source=1;}
   if(j==1){request.operation=UW_REQUEST_TRIAL_COMPLETE;request.source=1;request.family=17;request.key=2;
    slot=underwater_test_slot(&state,51);
    if(slot==255){slot=0;request.instance_id=state.roster.instances[slot].instance_id;}
    else {CreatureInstance*c=&state.roster.instances[slot];const CreatureForm*f=creatures_form(49);
     c->form_id=49;c->polarity=f->polarity;c->trial_flags=0;c->bond=20;c->equipped[0]=67;c->equipped[1]=0;c->selected_command=0;request.instance_id=c->instance_id;}
    request.slot=slot;}
   if(j==2){request.operation=UW_REQUEST_QUEST_CLAIM;request.quest=45;
    if(n){save5_quest_set_state(&state.quests,45,SAVE5_QUEST_READY);state.quests.rewards[45>>3]&=(unsigned char)~(1u<<(45&7));
     for(i=35;i<=36;++i)state.equipment.reward_claims[i>>3]&=(unsigned char)~(1u<<(i&7));
     for(i=0;i<48;++i)if(state.equipment.bag[i].item_id==68||state.equipment.bag[i].item_id==86){unsigned k;for(k=0;k<5;++k)if(state.equipment.equipped[k]==i)state.equipment.equipped[k]=255;state.equipment.bag[i]=(EquipmentRecord){0};}
    }}
   if(j==3){request.operation=UW_REQUEST_VISIT;request.room=46;}
   if(j==4){request.operation=UW_REQUEST_QUEST_CLAIM;request.quest=38;
    if(!n){if(underwater_visit(&state,46)!=1||underwater_test_ready(&state,38)){fixture_error=100;completed=2;while(1){}}}}
   counts[n][j]=creatures_roster_count(&state.roster);
   t=now();token=underwater_job_begin(&state,&request,17);begin_cycles[n][j]=now()-t;
   if(!token){fixture_error=200;completed=2;while(1){}}
   while(underwater_job_status(token)==SAVE5_BUSY){
    phase=underwater_job_phase(token);phase=phase?12+phase-1:save5_preflight_phase(token);
    if(j==5&&phase==17)state.roster.instances[0].cosmetic_seed^=1;
    t=now();st=underwater_job_step(token,1024,17);elapsed=now()-t;
    if(phase>=20){fixture_error=201;completed=2;while(1){}}
    if(elapsed>phase_cycles[n][j][phase])phase_cycles[n][j][phase]=elapsed;
    ++phase_calls[n][j][phase];
    if(st!=SAVE5_BUSY)break;
   }
   results[n][j]=underwater_job_status(token)==SAVE5_DONE?(unsigned)underwater_job_result(token):0xffffffffu;
   underwater_job_cancel();
  }
 }
 completed=1;while(1){}return 0;
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'docs/evidence/underwater-transactions-arm.json');args=p.parse_args()
 arm=resolve_arm_tools('gcc','objcopy','nm',root=ROOT);cc=arm['gcc']
 report={'scope':'Isolated ARM bounded transaction phases. Authenticated Magma34 and synthetic50/160; not native Underwater collection or full update/draw cadence','fixture_sha256':FIXTURE_SHA,'waitcnt':'0x4317','frame_cycles':280896,'source_sha256':runtime_hashes(),'cases':[]}
 with tempfile.TemporaryDirectory(prefix='underwater-job-arm-') as td:
  out=Path(td);sources=prepare(out);(out/'main.c').write_text(MAIN)
  flags=['-I'+str(ROOT/'src'),'-I'+str(out),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-fstack-usage']
  for n,path in {**sources,'setup':ROOT/'tests/underwater_save_setup.c','main':out/'main.c'}.items():subprocess.run([cc,*flags,'-c',str(path),'-o',str(out/f'{n}.o')],check=True)
  subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c',str(ROOT/'src/startup.s'),'-o',str(out/'startup.o')],check=True)
  elf=out/'jobs.elf';rom=out/'jobs.gba';subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,-T,'+str(ROOT/'linker.ld'),*[str(out/f'{n}.o') for n in ('startup','main','setup',*SOURCES)],'-lgcc','-o',str(elf)],check=True)
  subprocess.run([arm['objcopy'],'-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,str(ROOT/'tools/fix_header.py'),str(rom)],check=True,capture_output=True)
  symbols={x[2]:int(x[0],16) for line in subprocess.check_output([arm['nm'],'-n',str(elf)],text=True).splitlines() if len(x:=line.split())==3}
  report['rom_sha256']=sha(rom);report['stack_usage']={n:(out/f'{n}.su').read_text().splitlines() for n in ('save5','underwater_quests')}
  with Emulator(rom) as emu:
   for _ in range(100):
    emu.frames(600)
    if emu.read(symbols['completed']):break
   assert emu.read(symbols['completed'])==1,emu.read(symbols['fixture_error'])
   for n,label in enumerate(('authentic-Magma34','synthetic-Underwater50','synthetic-grandfathered160')):
    for j,op in enumerate(('repeat_grant','new_personal_trial','two_item_bundle','visit','teaching_claim','changed_state_refusal')):
     phases=[emu.read(symbols['phase_cycles']+((n*6+j)*20+i)*4) for i in range(20)];calls=[emu.read(symbols['phase_calls']+((n*6+j)*20+i)*4) for i in range(20)]
     row={'label':label,'operation':op,'retained':emu.read(symbols['counts']+(n*6+j)*4),'begin_cycles':emu.read(symbols['begin_cycles']+(n*6+j)*4),'phase_max_cycles':phases,'phase_calls':calls,'max_step_cycles':max(phases),'result':emu.read(symbols['results']+(n*6+j)*4)};report['cases'].append(row)
     print(label,op,'begin',row['begin_cycles'],'maxstep',row['max_step_cycles'],'commit',phases[17],'result',row['result'],flush=True)
 report['source_unchanged_during_measurement']=report['source_sha256']==runtime_hashes();report['global_max_stage_cycles']=max(r['max_step_cycles'] for r in report['cases'])
 args.output.parent.mkdir(parents=True,exist_ok=True);args.output.write_text(json.dumps(report,separators=(',',':'))+'\n');assert args.output.stat().st_size<90000
if __name__=='__main__':main()
