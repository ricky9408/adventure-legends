#!/usr/bin/env python3
"""Isolated ARM validation profiling; never builds or overwrites the game ROM."""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
from test_southern_save_limits import ROOT, SOURCES, prepare, sha, object_sizes
sys.path.insert(0,str(ROOT/'tools'))
from arm_toolchain import resolve_arm_tools
LABELS=('campaign','roster','quests','quest_campaign','retained_legacy','southern_evidence','quest_creatures_including_legacy_evidence','southern_sources_including_evidence','equipment','quest_equipment','full_save_validate','southern_anchor_30')
WRAPPER=r'''
unsigned save5_profile_component(unsigned n,Save5State *s) {
 switch(n) {
 case 0:return save5_campaign_validate(&s->campaign);
 case 1:return creatures_roster_validate(&s->roster);
 case 2:return save5_quests_validate(&s->quests);
 case 3:return quest_campaign_validate(&s->campaign,&s->quests);
 case 4:return retained_creatures(&s->roster);
 case 5:return southern_roster_evidence(&s->roster);
 case 6:return quest_creatures_validate(&s->quests,s->roster.obtained,s->roster.rewards,retained_creatures(&s->roster));
 case 7:return southern_sources_validate(&s->quests,s->roster.obtained,southern_roster_evidence(&s->roster));
 case 8:return equipment_validate(&s->equipment);
 case 9:return quest_equipment_validate(&s->quests,&s->equipment);
 case 10:return save5_validate(s);
 default:return 0;
 }
}
'''
MAIN=r'''
#include "southern_quests.h"
#ifdef PROFILE_EARNED_FIXTURE
#include "earned_fixture.h"
#endif
#define REG16(a) (*(volatile unsigned short *)(a))
void *memcpy(void*d,const void*s,unsigned n){unsigned char*a=d;const unsigned char*b=s;while(n--)*a++=*b++;return d;}
int southern_test_northern(Save5State*);
int southern_test_completed(Save5State*,unsigned);
unsigned save5_profile_component(unsigned,Save5State*);
static Save5State state;
volatile unsigned cycles[3][12][4],results[3][12][4],completed,fixture_error,counts[3];
const char sram_id[]="SRAM_V113";
static unsigned now(void){unsigned hi,lo,hi2;do{hi=REG16(0x0400010C);lo=REG16(0x04000108);hi2=REG16(0x0400010C);}while(hi!=hi2);return(hi<<16)|lo;}
int main(void){unsigned scenario,n,k,t,i;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;
 for(scenario=0;scenario<3;++scenario){
#ifdef PROFILE_EARNED_FIXTURE
  if(scenario==1){for(i=0;i<32768;++i)((volatile unsigned char*)0x0E000000)[i]=earned_fixture[i];fixture_error=save5_load(&state)?0:1;}
  else
#endif
  fixture_error=scenario?southern_test_completed(&state,scenario==2):southern_test_northern(&state);
  if(fixture_error){completed=2;while(1){}}
  for(i=0;i<160;++i)counts[scenario]+=!!state.roster.instances[i].form_id;
  for(n=0;n<12;++n)for(k=0;k<4;++k){
   t=now();results[scenario][n][k]=n==11?(unsigned)southern_anchor(&state,30):save5_profile_component(n,&state);
   cycles[scenario][n][k]=now()-t;
  }
 }
 completed=1;while(1){}return 0;
}
'''
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--creatures-source',type=Path);p.add_argument('--earned-fixture',type=Path);args=p.parse_args()
 out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
 sources=prepare(out)
 if args.creatures_source:sources['creatures']=args.creatures_source.resolve()
 source_hash={n:sha(x) for n,x in sources.items()}
 if args.earned_fixture:
  data=args.earned_fixture.read_bytes();assert len(data)==32768
  (out/'earned_fixture.h').write_text('static const unsigned char earned_fixture[32768]={\n'+',\n'.join(','.join(str(x) for x in data[i:i+64]) for i in range(0,len(data),64))+'\n};\n')
 original=sources['save5'].read_text();sources['save5']=out/'profile-save5.c';sources['save5'].write_text(original+WRAPPER)
 main=out/'profile.c';main.write_text(MAIN)
 arm=resolve_arm_tools('gcc','objcopy','nm',root=ROOT);cc=arm['gcc']
 flags=['-I'+str(ROOT/'src'),'-I'+str(out),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-fstack-usage']
 if args.earned_fixture:flags+=['-DPROFILE_EARNED_FIXTURE']
 for n,path in sources.items():subprocess.run([cc,*flags,'-c',str(path),'-o',str(out/f'{n}.o')],check=True)
 subprocess.run([cc,*flags,'-DSOUTHERN_SETUP_ONLY','-c',str(ROOT/'tests/southern_save_sanitizer.c'),'-o',str(out/'setup.o')],check=True)
 subprocess.run([cc,*flags,'-c',str(main),'-o',str(out/'main.o')],check=True)
 subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c',str(ROOT/'src/startup.s'),'-o',str(out/'startup.o')],check=True)
 elf=out/'validation-profile.elf';rom=out/'validation-profile.gba'
 subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,-T,'+str(ROOT/'linker.ld'),*[str(out/f'{n}.o') for n in ('startup','main','setup',*SOURCES)],'-lgcc','-o',str(elf)],check=True)
 subprocess.run([arm['objcopy'],'-O','binary',str(elf),str(rom)],check=True)
 subprocess.run([sys.executable,str(ROOT/'tools/fix_header.py'),str(rom)],check=True)
 symbols={x[2]:int(x[0],16) for line in subprocess.check_output([arm['nm'],'-n',str(elf)],text=True).splitlines() if len(x:=line.split())==3}
 from mgba_runner import Emulator
 report={'purpose':'Isolated ARM7TDMI validation diagnosis; fixtures after N5 use host setup, not native acquisition evidence','source_sha256':source_hash,'compiled_save5_sha256':sha(sources['save5']),'rom_sha256':sha(rom),'waitcnt':'0x4317','timer_hz':16777216,'earned_fixture_sha256':sha(args.earned_fixture) if args.earned_fixture else None,'scenarios':[]}
 with Emulator(rom) as e:
  for _ in range(100):
   e.frames(120)
   if e.read(symbols['completed']):break
  assert e.read(symbols['completed'])==1,('setup failed',e.read(symbols['fixture_error']))
  for i,label in enumerate(('authenticated-N5-plus-South-entry','native-earned-South21-fixture' if args.earned_fixture else 'ordinary-South-complete-host-fixture','synthetic-full160')):
   row={'label':label,'retained':e.read(symbols['counts']+i*4),'components':{}}
   for j,name in enumerate(LABELS):
    cs=[e.read(symbols['cycles']+((i*12+j)*4+k)*4) for k in range(4)]
    rs=[e.read(symbols['results']+((i*12+j)*4+k)*4) for k in range(4)]
    row['components'][name]={'cycles':cs,'max_cycles':max(cs),'results':rs}
   report['scenarios'].append(row)
 report['source_unchanged_during_measurement']=source_hash=={n:sha(ROOT/'src'/f'{n}.c') for n in SOURCES}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 for r in report['scenarios']:
  print(r['label'],r['retained'],{k:v['max_cycles'] for k,v in r['components'].items()})
if __name__=='__main__':main()
