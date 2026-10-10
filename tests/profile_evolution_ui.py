#!/usr/bin/env python3
"""Isolated ARM production evolution update slices; not final-engine cadence."""
import argparse
import hashlib
import gzip
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from arm_toolchain import resolve_arm_tools
from mgba_runner import Emulator
MODULES=('horizons_quests','horizons_game','horizons_art','horizons_powers','horizons_power_art','horizons_creature_art','return_quests','return_game','return_art','return_powers','return_power_art','return_legacy_powers','return_creature_art','progression','creatures','creature_data','equipment','equipment_data','save4','save5',
         'underwater_quests','magma_quests','southern_quests','northern_quests','regional_quests',
         'campaign_rules','progression_events','evolution_art','regional_creature_art',
         'northern_creature_art','southern_creature_art','magma_creature_art','underwater_creature_art','ui','assets')
MAIN=r'''
#include "progression.h"
#define REG16(a) (*(volatile unsigned short *)(a))
extern volatile int game_state;
extern volatile int room,px,py;extern volatile unsigned chapter_flags;extern int journal_tab;
void host_select(unsigned);unsigned host_count(void);int host_save_valid(void);
int underwater_test_earned34(Save5State*);int underwater_test_completed(Save5State*,unsigned);unsigned underwater_test_slot(const Save5State*,unsigned);
void *memcpy(void*d,const void*s,unsigned n){unsigned char*a=d;const unsigned char*b=s;while(n--)*a++=*b++;return d;}
void *memset(void*d,int c,unsigned n){unsigned char*a=d;while(n--)*a++=(unsigned char)c;return d;}
int memcmp(const void*a,const void*b,unsigned n){const unsigned char*x=a,*y=b;while(n--){if(*x!=*y)return *x-*y;++x;++y;}return 0;}
volatile unsigned begin_cycles[3][2],step_cycles[3][2][180],step_counts[3][2],retained[3],completed,fixture_error;
static unsigned now(void){unsigned hi,lo,hi2;do{hi=REG16(0x0400010C);lo=REG16(0x04000108);hi2=REG16(0x0400010C);}while(hi!=hi2);return(hi<<16)|lo;}
int main(void){unsigned n,j,t,i,slot;CreatureInstance*c;const CreatureForm*f;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;
 for(n=0;n<3;n++){
  progression_evolution_cancel();
  fixture_error=n?(unsigned)underwater_test_completed(&adventure_save,n==2):(unsigned)underwater_test_earned34(&adventure_save);
  if(fixture_error){completed=2;while(1){}}
  /* Typed source/quest/gear history is real34 or the established synthetic
   * completed50/160. Only this evolution participant is reset synthetically. */
  slot=underwater_test_slot(&adventure_save,n?50:38);
  if(slot==255){fixture_error=100;completed=2;while(1){}}
  c=&adventure_save.roster.instances[slot];f=creatures_form(n?49:37);
  c->form_id=f->id;c->polarity=f->polarity;c->trial_flags=3;
  c->equipped[0]=creature_learnsets[f->learnset_offset].ability_id;c->equipped[1]=0;c->selected_command=0;
  host_select(slot);room=n?46:38;px=py=120;chapter_flags=adventure_save.campaign.chapter_flags;journal_tab=3;game_state=3;
  progression_refresh();
  if(!host_save_valid()){fixture_error=101;completed=2;while(1){}}
  retained[n]=host_count();
  for(j=0;j<2;j++){
   t=now();if(j)progression_confirm_input(1);else progression_menu_input(4);begin_cycles[n][j]=now()-t;
   for(i=0;i<180&&progression_evolution_busy();i++){
    t=now();progression_confirm_input(0);step_cycles[n][j][i]=now()-t;
   }
   step_counts[n][j]=i;
   if(progression_evolution_busy()||game_state!=(j?8:7)){fixture_error=4+j;completed=2;while(1){}}
  }
  if(adventure_save.roster.instances[slot].form_id!=(n?50:38)||!host_save_valid()){fixture_error=6;completed=2;while(1){}}
 }
 completed=1;while(1){}return 0;
}
'''
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def sources_hashes():
 pending=[ROOT/'src'/f'{n}.c' for n in MODULES]+[ROOT/'tests/magma_evolution_ui_host.c',ROOT/'tests/underwater_save_setup.c',Path(__file__)];result={}
 while pending:
  path=pending.pop().resolve();key=str(path.relative_to(ROOT))
  if key in result:continue
  result[key]=sha(path)
  for name in re.findall(r'#include\s+"([^"]+)"',path.read_text()):
   child=path.parent/name
   if not child.exists():child=ROOT/'src'/name
   if child.exists():pending.append(child)
 return dict(sorted(result.items()))
def main():
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,default=ROOT/'build/current-host-evidence/bounded-evolution-ui-arm.json');args=p.parse_args()
 arm=resolve_arm_tools('gcc','objcopy','nm',root=ROOT);cc=arm['gcc']
 report={'scope':'Isolated ARM production progression updates using authenticated Magma34 and established synthetic completed Underwater50/160 histories, with a selected evolution participant reset synthetically to its base form. Excludes native drawing, audio and interrupts; not acquisition or full-frame cadence proof.', 'waitcnt':'0x4317','frame_cycles':280896,'batch_slices_per_update':3,'warmup_updates':2,'source_sha256':sources_hashes(),'cases':[]}
 with tempfile.TemporaryDirectory(prefix='evolution-ui-arm-') as td:
  out=Path(td);(out/'main.c').write_text(MAIN)
  fixture=ROOT/'tests/fixtures/v5-revision5/magma-all65-town.sav'
  report['fixture_sha256']=sha(fixture)
  assert report['fixture_sha256']=='a4b45873a14d3ca18c3f93678350f8ab2a0a8c6609cdc17d1eb7a609a9760858'
  (out/'underwater_magma_fixture.h').write_text('static const unsigned char underwater_magma_fixture[32768]={'+','.join(map(str,fixture.read_bytes()))+'};\n')
  flags=['-I'+str(ROOT/'src'),'-I'+str(out),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-fstack-usage','-ffunction-sections','-fdata-sections','-DSAVE4_HOST_TEST','-DSAVE5_HOST_TEST','-DEVOLUTION_ARM_PROFILE']
  report['diagnostic_section_transforms']=[]
  for n,path in {**{n:ROOT/'src'/f'{n}.c' for n in MODULES},'bridge':ROOT/'tests/magma_evolution_ui_host.c','setup':ROOT/'tests/underwater_save_setup.c','main':out/'main.c'}.items():
   if n=='horizons_game':
    # This isolated progression benchmark links real scene callbacks, but not
    # the complete drawing/audio engine. Keep long_call/noinline and ROM
    # placement while permitting --gc-sections to remove unrelated callbacks.
    # No production file or function body is modified; this is not a native
    # full-engine frame or code-layout timing measurement.
    text=path.read_text();before='#define COLD __attribute__((section(".text.rom"),long_call,noinline))';after='#define COLD __attribute__((long_call,noinline))'
    assert text.count(before)==1
    transformed=out/'horizons_game_section_split.c';transformed.write_text(text.replace(before,after,1))
    report['diagnostic_section_transforms'].append({'source':'src/horizons_game.c','source_sha256':sha(path),'compiled_sha256':sha(transformed),'before':before,'after':after,'scope':'ROM function-section separation for isolated callback linkage only; actual function bodies and noinline/long_call preserved'})
    path=transformed
   subprocess.run([cc,*flags,'-c',str(path),'-o',str(out/f'{n}.o')],check=True)
  subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c',str(ROOT/'src/startup.s'),'-o',str(out/'startup.o')],check=True)
  elf=out/'evolution.elf';rom=out/'evolution.gba';subprocess.run([cc,'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,--gc-sections','-Wl,-T,'+str(ROOT/'linker.ld'),*[str(out/f'{n}.o') for n in ('startup','main','bridge','setup',*MODULES)],'-lgcc','-o',str(elf)],check=True)
  subprocess.run([arm['objcopy'],'-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,str(ROOT/'tools/fix_header.py'),str(rom)],check=True,capture_output=True)
  symbols={x[2]:int(x[0],16) for line in subprocess.check_output([arm['nm'],'-n',str(elf)],text=True).splitlines() if len(x:=line.split())==3}
  report['rom_sha256']=sha(rom);report['stack_usage']=(out/'progression.su').read_text().splitlines()
  report['evolution_job_arm_bytes']=int(subprocess.check_output([arm['nm'],'-S',str(elf)],text=True).split(' evolution_job\n')[0].splitlines()[-1].split()[1],16)
  with Emulator(rom) as emu:
   for _ in range(100):
    emu.frames(300)
    if emu.read(symbols['completed']):break
   assert emu.read(symbols['completed'])==1,emu.read(symbols['fixture_error'])
   for n in range(3):
    for j,label in enumerate(('opening_display_preparation','fresh_A_commit')):
     count=emu.read(symbols['step_counts']+(n*2+j)*4)
     steps=[emu.read(symbols['step_cycles']+((n*2+j)*180+i)*4) for i in range(count)]
     row={'retained':emu.read(symbols['retained']+n*4),'operation':label,'begin_cycles':emu.read(symbols['begin_cycles']+(n*2+j)*4),'step_calls':count,'step_cycles':steps,'max_step_cycles':max(steps),'finish_cycles':steps[-1],'max_noncommit_update_cycles':max(steps[:-1]),'preparation_frames':count};report['cases'].append(row)
     print(row['retained'],label,'begin',row['begin_cycles'],'steps',count,'max',max(steps),'finish',steps[-1],flush=True)
 report['source_unchanged_during_measurement']=report['source_sha256']==sources_hashes()
 report['max_update_cycles']=max(max(row['begin_cycles'],row['max_step_cycles']) for row in report['cases'])
 report['max_noncommit_update_cycles']=max(row['max_noncommit_update_cycles'] for row in report['cases'])
 report['gates']={'noncommit_update_cycles_limit':90000,'preparation_frames_limit':60}
 report['result']='PASS' if report['max_noncommit_update_cycles']<=90000 and all(row['preparation_frames']<=60 for row in report['cases']) and report['source_unchanged_during_measurement'] else 'FAIL'
 # Persist failed measurements before enforcing the unchanged thresholds.
 args.output.parent.mkdir(parents=True,exist_ok=True)
 # Preserve the complete enlarged current source closure losslessly while
 # keeping this public summary bounded; do not drop hashes to satisfy a cap.
 source_bytes=(json.dumps(report.pop('source_sha256'),sort_keys=True,separators=(',',':'))+'\n').encode()
 source_path=args.output.with_name(args.output.stem+'.sources.json.gz')
 compressed=gzip.compress(source_bytes,compresslevel=9,mtime=0);source_path.write_bytes(compressed)
 report['source_manifest']={'path':source_path.name,'raw_sha256':hashlib.sha256(source_bytes).hexdigest(),'gzip_sha256':sha(source_path),'entries':len(json.loads(source_bytes)),'lossless_gzip':True}
 args.output.write_text(json.dumps(report,separators=(',',':'))+'\n');assert args.output.stat().st_size<90000
 assert report['max_noncommit_update_cycles']<=90000, report['max_noncommit_update_cycles']
 assert all(row['preparation_frames']<=60 for row in report['cases'])
 assert report['source_unchanged_during_measurement'], 'Source changed while profiling'
if __name__=='__main__':main()
