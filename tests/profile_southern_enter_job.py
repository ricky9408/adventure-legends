#!/usr/bin/env python3
"""Isolated ARM Southern entry timings: exact direct/queued final-save equality.
Includes synthetic 160-individual saves: real base grants, or retained form27
clones with fresh instance IDs. Both must pass the unchanged full validator.
Drawing/IRQ/main-engine work is excluded; this is not frame-cadence acceptance.
"""
import argparse,hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from arm_toolchain import resolve_arm_tools
from mgba_runner import Emulator
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
MAIN=r'''
#include "south_enter_fixtures.h"
#define REG16(a) (*(volatile unsigned short *)(a))
void *memcpy(void*d,const void*s,unsigned n){unsigned char*a=d;const unsigned char*b=s;while(n--)*a++=*b++;return d;}
void *memset(void*d,int c,unsigned n){unsigned char*a=d;while(n--)*a++=(unsigned char)c;return d;}
int memcmp(const void*a,const void*b,unsigned n){const unsigned char*x=a,*y=b;while(n--){if(*x!=*y)return *x-*y;++x;++y;}return 0;}
static Save5State base,expected;
volatile unsigned sync_cycles[4],begin_cycles[4],prepare_cycles[4][32],prepare_phases[4][32],steps[4],commit_cycles[4],roster_counts[4],completed,error;
static unsigned now(void){unsigned hi,lo,hi2;do{hi=REG16(0x0400010C);lo=REG16(0x04000108);hi2=REG16(0x0400010C);}while(hi!=hi2);return(hi<<16)|lo;}
static void reset(void){south_game_reset();adventure_save=base;room=base.campaign.room;checkpoint_spawn=base.campaign.spawn;chapter_flags=base.campaign.chapter_flags;px=240;py=268;face=1;game_state=1;}
int main(void){unsigned n,i,t,status,slot,exemplar=160;int r;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;
 for(n=0;n<4;++n){
  for(i=0;i<32768;++i)((volatile unsigned char*)0x0e000000)[i]=(n==0?minimal_fixture:n==1?full_fixture:complete_fixture)[i];
  if(!save5_load(&base)){error=1;break;}
  if(n==2)while(creatures_roster_count(&base.roster)<160){
   if(creatures_grant(&base.roster,1,50,100,0,0)==255){error=2;break;}
  }
  if(n==3){
   for(i=0;i<160;++i)if(base.roster.instances[i].form_id==27)exemplar=i;
   if(exemplar==160){error=10;break;}
   for(slot=0;slot<160;++slot)if(!base.roster.instances[slot].form_id){
    base.roster.instances[slot]=base.roster.instances[exemplar];
    base.roster.instances[slot].instance_id=base.roster.next_instance_id++;
   }
  }
  if(error||!save5_validate(&base)){if(!error)error=3;break;}
  roster_counts[n]=creatures_roster_count(&base.roster);reset();t=now();r=south_game_enter(30,0);sync_cycles[n]=now()-t;
  if(!r){error=4;break;}expected=adventure_save;
  reset();t=now();r=south_game_request_enter(30,0);begin_cycles[n]=now()-t;if(r!=2){error=5;break;}
  game_state=10;
  do{
   i=steps[n]++;if(i>=32){error=6;break;}
   prepare_phases[n][i]=save5_preflight_phase(south_enter_job.token);t=now();status=south_game_prepare_enter();prepare_cycles[n][i]=now()-t;
   if(memcmp(&adventure_save,&base,sizeof base)){error=7;break;}
  }while(status==SAVE5_BUSY);
  if(error||status!=SAVE5_DONE){if(!error)error=8;break;}
  game_state=1;t=now();r=south_game_commit_enter();commit_cycles[n]=now()-t;
  if(r!=1||south_game_enter_pending()||memcmp(&adventure_save,&expected,sizeof expected)){error=9;break;}
 }
 completed=error?2:1;while(1){}return 0;
}
'''
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
 fixture_paths=[ROOT/'tests/fixtures'/n for n in ['v5-revision6/underwater-minimal12-town.sav','v5-revision6/underwater-all89-town.sav','v5-revision7/return-all104-town.sav']]
 pins=['3f5bbccab022f86b38f4d180e8cf66b04c055791fe4804ddbebbdefb5406aeda','41cf371618208e0097fe6ee10393e3185b4bffb2af9dad9e5f81e2663d6673a0','d482466d04050c3d7f2e8eb8e1960729c9b9b33aa3e32440d186a4b54b854a69']
 assert [sha(p) for p in fixture_paths]==pins
 (out/'south_enter_fixtures.h').write_text('\n'.join('static const unsigned char '+name+'[32768]={'+','.join(map(str,p.read_bytes()))+'};' for name,p in zip(['minimal_fixture','full_fixture','complete_fixture'],fixture_paths)))
 prefix=(ROOT/'tests/southern_enter_differential.c').read_text().split('#include SOUTH_SOURCE')[0]
 for n in ['assert.h','limits.h','stdio.h','stdlib.h','string.h']:prefix=prefix.replace('#include <'+n+'>\n','')
 unit=out/'main.c';unit.write_text(prefix+'\n#include "south_game.c"\nconst SouthArtRoom south_art_rooms[8]={{0}};\nvoid enter_room(int r,int s){if(south_game_request_enter((unsigned)r,(unsigned)s)!=1)return;room=r;checkpoint_spawn=s;(void)south_game_enter((unsigned)r,(unsigned)s); }\n'+MAIN)
 arm=resolve_arm_tools('gcc','objcopy','nm',root=ROOT);mods=['save4','save5','creatures','creature_data','equipment','equipment_data','southern_quests'];sources=[unit]+[ROOT/'src'/f'{n}.c' for n in mods]
 flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-fstack-usage','-ffunction-sections','-fdata-sections','-I'+str(ROOT/'src'),'-I'+str(out)]
 hashes={str(p.relative_to(ROOT)):sha(p) for p in (ROOT/'src').rglob('*') if p.is_file()}
 for n,source in zip(['main',*mods],sources):subprocess.run([arm['gcc'],*flags,'-c',str(source),'-o',str(out/f'{n}.o')],check=True)
 subprocess.run([arm['gcc'],'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c',str(ROOT/'src/startup.s'),'-o',str(out/'startup.o')],check=True)
 elf=out/'probe.elf';rom=out/'probe.gba';subprocess.run([arm['gcc'],'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,--gc-sections','-Wl,-T,'+str(ROOT/'linker.ld'),*[str(out/f'{n}.o') for n in ['startup','main',*mods]],'-lgcc','-o',str(elf)],check=True)
 subprocess.run([arm['objcopy'],'-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,str(ROOT/'tools/fix_header.py'),str(rom)],check=True,capture_output=True)
 syms={r[2]:int(r[0],16) for line in subprocess.check_output([arm['nm'],'-n',str(elf)],text=True).splitlines() if len(r:=line.split())==3};report={'scope':__doc__,'rom_sha256':sha(rom),'elf_sha256':sha(elf),'fixtures':dict(zip(map(str,fixture_paths),pins)),'runtime_sources':hashes,'cases':[]}
 with Emulator(rom) as e:
  for _ in range(100):
   e.frames(300)
   if e.read(syms['completed']):break
  assert e.read(syms['completed'])==1,e.read(syms['error'])
  for n in range(4):
   get=lambda k,i=n:e.read(syms[k]+i*4);steps=get('steps');row={'retained':get('roster_counts'),'synthetic':n>=2,'filler_form':0 if n<2 else 1 if n==2 else 27,'synchronous_cycles':get('sync_cycles'),'request_cycles':get('begin_cycles'),'commit_cycles':get('commit_cycles'),'steps':steps,'prepare_cycles':[get('prepare_cycles',n*32+i) for i in range(steps)],'phase_at_entry':[get('prepare_phases',n*32+i) for i in range(steps)],'exact_save_equal':True};row['maximum_prepare_cycles']=max(row['prepare_cycles']);report['cases'].append(row);print(json.dumps(row),flush=True)
 report['relevant_sources_unchanged']=all(sha(ROOT/p)==v for p,v in hashes.items() if p.startswith('src/south') or p in ['src/'+n+'.c' for n in mods]);assert report['relevant_sources_unchanged'];(out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
