#!/usr/bin/env python3
"""Isolated ARM timing/parity of shipping private regional quest cursor.
Synthetic capacity fixtures; no controller, engine drawing, or acceptance claim.
The same actual synchronous APIs and private cursor run against equal states.
"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from arm_toolchain import resolve_arm_tools
from mgba_runner import Emulator
MAIN=r'''
#include "southern_quests.h"
#include "magma_quests.h"
#include "fixture.h"
#define PLAY 1
#define COLD __attribute__((section(".text.rom"),long_call,noinline))
#define REG16(a) (*(volatile unsigned short *)(a))
void *memcpy(void*d,const void*s,unsigned n){unsigned char*a=d;const unsigned char*b=s;while(n--)*a++=*b++;return d;}
void *memset(void*d,int c,unsigned n){unsigned char*a=d;while(n--)*a++=(unsigned char)c;return d;}
int memcmp(const void*a,const void*b,unsigned n){const unsigned char*x=a,*y=b;while(n--){if(*x!=*y)return *x-*y;++x;++y;}return 0;}
static Save5State base,expected;
Save5State adventure_save;
volatile int room,px,py,game_state,summoned,checkpoint_spawn;
int face;unsigned progression_revision,chapter_flags;
CONFIG
#include "regional_quest_event.inc"
volatile unsigned sync_cycles[5][2],begin_cycles[5][2],phase_cycles[5][2][8],phase_calls[5][2][8],commit_cycles[5][2],results[5][2],completed,error;
static unsigned now(void){unsigned hi,lo,hi2;do{hi=REG16(0x0400010C);lo=REG16(0x04000108);hi2=REG16(0x0400010C);}while(hi!=hi2);return(hi<<16)|lo;}
int main(void){unsigned n,j,i,t,phase,status,elapsed,q;int result;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;
 for(n=0;n<5;++n)for(j=0;j<2;++j){
  rq_cancel();for(i=0;i<32768;++i)((volatile unsigned char*)0x0e000000)[i]=fixture[i];
  if(!save5_load(&base)){error=1;goto end;}
  if(VISIT(&base,RQ_FIRST+8)!=RQ_CHANGED){error=2;goto end;}
  base.campaign.room=RQ_FIRST+8;base.campaign.spawn=0;
  q=RQ_FIRST+j;
  if(n==1){
   if(RQ_DISCOVERY&&creatures_grant(&base.roster,RQ_FORM(q),30,20,0,0)==255){error=3;goto end;}
   while(creatures_admission_allowed(creatures_grant_admitted(&base.roster,1,30,20,0,0,0))){}
  }
  if(n==2)while(creatures_roster_count(&base.roster)<160)if(creatures_grant(&base.roster,1,30,20,0,0)==255){error=4;goto end;}
  if(n==3)base.roster.next_instance_id=0xffffffffu;
  if(n==4){
   for(i=1;i<48;i++){memset(&base.equipment.bag[i],0,sizeof(EquipmentRecord));base.equipment.bag[i].item_id=99+i;base.equipment.bag[i].quantity=1;base.equipment.seen[(99+i)>>3]|=1u<<((99+i)&7);}
   base.equipment.equipped[0]=0;for(i=1;i<5;i++)base.equipment.equipped[i]=255;
  }
  if(!save5_validate(&base)){error=5;goto end;}
  expected=base;t=now();OFFER(&expected,q);OBJECTIVE(&expected,q,1);OBJECTIVE(&expected,q,2);result=CLAIM(&expected,q);sync_cycles[n][j]=now()-t;results[n][j]=(unsigned)result;
  adventure_save=base;room=base.campaign.room;checkpoint_spawn=0;game_state=1;summoned=1;chapter_flags=base.campaign.chapter_flags;
  t=now();rq_enqueue(q,RQ_OFFER,0);rq_enqueue(q,RQ_OBJECTIVE,1);rq_enqueue(q,RQ_OBJECTIVE,2);rq_enqueue(q,RQ_CLAIM,0);if(rq_state(q)!=2||rq_objectives(q)!=3){error=11;goto end;}if(!RQ_SEAL()){error=6;goto end;}begin_cycles[n][j]=now()-t;
  game_state=10;
  do{phase=rq.phase;t=now();status=RQ_PREPARE();elapsed=now()-t;if(phase>7){error=7;goto end;}
   if(elapsed>phase_cycles[n][j][phase])phase_cycles[n][j][phase]=elapsed;
   ++phase_calls[n][j][phase];
   if(memcmp(&adventure_save,&base,sizeof base)){error=8;goto end;}
  }while(status==SAVE5_BUSY);
  if(status!=SAVE5_DONE||rq.result!=result){error=9;goto end;}
  game_state=1;t=now();result=rq_commit_patch();commit_cycles[n][j]=now()-t;
  if(!result||memcmp(&adventure_save,&expected,sizeof expected)){error=10;goto end;}
 }
end:completed=error?2:1;while(1){}return 0;
}
'''
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--output',type=Path,default=ROOT/'build/quest-arm');a=ap.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 tools=resolve_arm_tools('gcc','objcopy','nm',root=ROOT);cc=tools['gcc'];report={'scope':__doc__,'cases':[]}
 for region in ['south','magma']:
  o=out/region;o.mkdir();source=(ROOT/'src'/f'{region}_game.c').read_text();config=source[source.index('static const unsigned char rq_forms'):source.index('#include "regional_quest_event.inc"')]
  pre='southern' if region=='south' else 'magma';config+='\n'+''.join(f'#define {macro} {pre}_{api}\n' for macro,api in [('VISIT','visit'),('OFFER','quest_offer'),('OBJECTIVE','quest_objective'),('CLAIM','quest_claim')])
  main=MAIN.replace('CONFIG',config);(o/'main.c').write_text(main)
  fixture=ROOT/('tests/fixtures/v5-revision3/northern-all21-town.sav' if region=='south' else 'tests/fixtures/v5-revision4/southern-minimal8-town.sav');(o/'fixture.h').write_text('static const unsigned char fixture[32768]={'+','.join(map(str,fixture.read_bytes()))+'};')
  data=(ROOT/'src/equipment_data.c').read_text();marker='const EquipmentDefinition equipment_definitions[EQUIPMENT_DEFINITION_CAPACITY] = {\n';rows=''.join(f'    [{i}] = {{{i}, 1, 0, 0, 255, {{0, 0}}, {{0, 0, 0, 0, 0, 0, 0, 0}}}},\n' for i in range(100,147));(o/'equipment_data.c').write_text(data.replace(marker,marker+rows))
  mods=['save4','save5','creatures','creature_data','equipment','equipment_data','magma_quests','southern_quests'];flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-fstack-usage','-ffunction-sections','-fdata-sections','-I'+str(ROOT/'src'),'-I'+str(o)]
  for name,p in [('main',o/'main.c')]+[(n,o/'equipment_data.c' if n=='equipment_data' else ROOT/'src'/f'{n}.c') for n in mods]:subprocess.run([cc,*flags,'-c',str(p),'-o',str(o/f'{name}.o')],check=True)
  subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c',str(ROOT/'src/startup.s'),'-o',str(o/'startup.o')],check=True)
  elf=o/'profile.elf';rom=o/'profile.gba';subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,--gc-sections','-Wl,-T,'+str(ROOT/'linker.ld'),*[str(o/f'{n}.o') for n in ('startup','main',*mods)],'-lgcc','-o',str(elf)],check=True);subprocess.run([tools['objcopy'],'-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,str(ROOT/'tools/fix_header.py'),str(rom)],check=True,capture_output=True)
  syms={x[2]:int(x[0],16) for line in subprocess.check_output([tools['nm'],'-n',str(elf)],text=True).splitlines() if len(x:=line.split())==3}
  with Emulator(rom) as e:
   for _ in range(100):
    e.frames(300)
    if e.read(syms['completed']):break
   assert e.read(syms['completed'])==1,(region,e.read(syms['error']))
   for n,kind in enumerate(['earned-fixture','reservation-boundary','full160','identity-exhaustion','synthetic-full48']):
    for j in range(2):
     idx=n*2+j;cycles=[e.read(syms['phase_cycles']+(idx*8+i)*4) for i in range(8)];calls=[e.read(syms['phase_calls']+(idx*8+i)*4) for i in range(8)]
     row={'region':region,'kind':kind,'quest':(22 if region=='south' else 30)+j,'result':e.read(syms['results']+idx*4),'synchronous_cycles':e.read(syms['sync_cycles']+idx*4),'begin_cycles':e.read(syms['begin_cycles']+idx*4),'max_prepare_cycles':max(cycles),'commit_cycles':e.read(syms['commit_cycles']+idx*4),'phase_cycles':cycles,'phase_calls':calls,'steps':sum(calls),'rom_sha256':sha(rom),'fixture_sha256':sha(fixture)};report['cases'].append(row);print(region,kind,j,row['synchronous_cycles'],row['max_prepare_cycles'],row['commit_cycles'],flush=True)
 report['result']='PASS';report['cursor_source_sha256']=sha(ROOT/'src/regional_quest_event.inc');(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
