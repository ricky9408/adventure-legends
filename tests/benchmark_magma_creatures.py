#!/usr/bin/env python3
"""Bounded isolated ARM7TDMI creature/admission timings and stack watermark.

The earned21 SRAM is read-only input, hash-pinned to delivered S3. The staged34
and full160 profiles are host-constructed core states, never native route proof.
No full game ROM, saves or external state are modified by this benchmark.
"""
import argparse, ctypes as C, hashlib, json, re, struct, subprocess, sys, tempfile
from pathlib import Path
from test_creatures import build, Instance, Roster, ROOT
sys.path.insert(0,str(ROOT/'tools'))
from arm_toolchain import resolve_arm_tools
PIN='0bd83c19eb0dee81b3cd9e2b48462f6362b559786e38fa119312fe05787b0bd3'
MAIN=r'''
#include "creatures.h"
#include "fixture.h"
#define REG16(a) (*(volatile unsigned short *)(a))
static CreatureRoster roster, reference;
volatile unsigned cycles[4][7][4], answers[4][7][4], stack_bytes[4][7], counts[4], completed, error;
static CreatureCoverage coverage;
static CreatureAdmission admission;
static unsigned now(void){unsigned hi,lo,hi2;do{hi=REG16(0x0400010C);lo=REG16(0x04000108);hi2=REG16(0x0400010C);}while(hi!=hi2);return(hi<<16)|lo;}
static void copy_roster(const CreatureRoster *r){unsigned i;for(i=0;i<sizeof roster;++i)((unsigned char*)&roster)[i]=((const unsigned char*)r)[i];}
static unsigned setup(unsigned scenario){
 static const unsigned char roots[13]={31,34,37,37,40,40,43,43,46,46,95,97,99};
 static const unsigned char targets[13]={33,36,38,39,41,42,44,45,47,48,96,98,100};
 unsigned i,slot;
 copy_roster(&earned);
 if(scenario){
  for(i=0;i<13;++i){
   if(!creatures_admission_allowed(creatures_grant_admitted(&roster,roots[i],50,100,0,0,&slot)))return 1;
   if(!creatures_mark_trial_qualified(&roster.instances[slot],creatures_form(roots[i])->family,1))return 2;
   if(i<2&&creatures_evolve_to(&roster,slot,roots[i]+1,1023,1,1))return 4;
   if(creatures_trial_mask_for_key(creatures_form(roots[i])->family,2)&&!creatures_mark_trial_qualified(&roster.instances[slot],creatures_form(roots[i])->family,2))return 3;
   if(creatures_evolve_to(&roster,slot,targets[i],1023,1,1))return 5;
  }
 }
 if(scenario==2){
  /* A retained flexible real copy plus complete terminal coverage; raw grant
   * intentionally constructs a legal grandfathered full160 test fixture. */
  if(creatures_grant(&roster,37,50,100,0,0)==255)return 6;
  while(creatures_roster_count(&roster)<160)if(creatures_grant(&roster,1,50,100,0,0)==255)return 7;
 }
 if(scenario==3){
  creatures_roster_init(&roster);
  while(creatures_roster_count(&roster)<89)if(creatures_grant(&roster,1,50,100,0,0)==255)return 8;
 }
 return !creatures_roster_validate(&roster);
}
int main(void){
 unsigned scenario,op,k,t,sp,lowest,result,slot,i;volatile unsigned *word;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;
 for(scenario=0;scenario<4;++scenario){
  if((error=setup(scenario))){completed=2;while(1){}}
  counts[scenario]=creatures_roster_count(&roster);
  for(i=0;i<sizeof roster;++i)((unsigned char*)&reference)[i]=((const unsigned char*)&roster)[i];
  for(op=0;op<7;++op)for(k=0;k<4;++k){
   copy_roster(&reference);
   __asm__ volatile("mov %0, sp":"=r"(sp));
   for(word=(volatile unsigned*)0x03007000;word<(volatile unsigned*)sp;++word)*word=0xA55A3CC3u;
   t=now();
   switch(op){
    case 0:result=creatures_catalog_validate();break;
    case 1:result=creatures_roster_validate(&roster);break;
    case 2:result=creatures_roster_validate_revision(&roster,4);break;
    case 3:result=creatures_collection_coverage(&roster,&coverage);break;
    case 4:result=creatures_admission_query_grant(&roster,31,&admission);break;
    case 5:result=creatures_admission_query_evolution(&roster,scenario==2?34:0,38,&admission);break;
    default:result=creatures_grant_admitted(&roster,1,50,100,0,0,&slot);break;
   }
   cycles[scenario][op][k]=now()-t;answers[scenario][op][k]=result;
   lowest=sp;
   for(word=(volatile unsigned*)0x03007000;word<(volatile unsigned*)sp;++word)if(*word!=0xA55A3CC3u){lowest=(unsigned)word;break;}
   if(sp-lowest>stack_bytes[scenario][op])stack_bytes[scenario][op]=sp-lowest;
  }
 }
 completed=1;while(1){}return 0;
}
'''
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def decode_roster(blob):
    assert len(blob)==32768 and hashlib.sha256(blob).hexdigest()==PIN
    off=max((512,6656),key=lambda o:struct.unpack_from('<I',blob,o+8)[0]);b=blob[off:off+6144]
    assert b[20]==0xA5 and struct.unpack_from('<H',b,12)[0]==4
    r=Roster()
    for i in range(160):r.instances[i]=Instance.from_buffer_copy(b[160+i*24:184+i*24])
    for field,start,length in [('seen',96,16),('obtained',112,16),('rewards',128,16),('party',4000,4),('expedition_bond',4296,160),('expedition_events',4456,64),('lifetime_field_aid',4520,16)]:getattr(r,field)[:]=b[start:start+length]
    r.selected_party=b[4004];r.next_instance_id=struct.unpack_from('<I',b,4008)[0]
    return r
def initializer(r):
    rows=[]
    for c in r.instances:
        rows.append('{%d,%d,%d,%d,%du,%du,%d,%d,{%d,%d},%d,%d,%du}'%(c.form_id,c.flags,c.level,c.bond,c.xp,c.instance_id,c.nickname_id,c.trial_flags,*c.equipped,c.polarity,c.selected_command,c.cosmetic_seed))
    array=lambda a:'{'+','.join(map(str,a))+'}'
    return 'static const CreatureRoster earned={\n{'+',\n'.join(rows)+'},\n'+array(r.party)+','+str(r.selected_party)+','+str(r.next_instance_id)+','+','.join(array(getattr(r,n)) for n in ['seen','obtained','rewards','expedition_bond','expedition_events','lifetime_field_aid'])+'};\n'
def main():
    ap=argparse.ArgumentParser();ap.add_argument('--earned-sram',type=Path,required=True);ap.add_argument('--output',type=Path,required=True);ap.add_argument('--baseline-source',type=Path);args=ap.parse_args();out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    r=decode_roster(args.earned_sram.read_bytes())
    with tempfile.TemporaryDirectory() as temp:
        lib=build(temp);assert lib.creatures_roster_count(C.byref(r))==21 and lib.creatures_roster_validate(C.byref(r))
        lib.creatures_roster_validate_revision.argtypes=[C.POINTER(Roster),C.c_uint];assert lib.creatures_roster_validate_revision(C.byref(r),4)
    (out/'fixture.h').write_text(initializer(r));(out/'main.c').write_text(MAIN)
    arm=resolve_arm_tools('gcc','nm','objcopy','size');flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-pedantic','-fstack-usage','-I'+str(ROOT/'src'),'-I'+str(out)]
    sources={u:ROOT/'src'/f'{u}.c' for u in ('creatures','creature_data')};sources['main']=out/'main.c'
    source_hash={str(p.relative_to(ROOT)):sha(p) for p in [ROOT/'src/creatures.h',*list(sources.values())[:2]]}
    for u,p in sources.items():subprocess.run([arm['gcc'],*flags,'-c',str(p),'-o',str(out/f'{u}.o')],check=True)
    subprocess.run([arm['gcc'],'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c',str(ROOT/'src/startup.s'),'-o',str(out/'startup.o')],check=True)
    elf=out/'bench.elf';rom=out/'bench.gba'
    subprocess.run([arm['gcc'],'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,-T,'+str(ROOT/'linker.ld'),*[str(out/f'{n}.o') for n in ('startup','main','creatures','creature_data')],'-lgcc','-o',str(elf)],check=True)
    subprocess.run([arm['objcopy'],'-O','binary',str(elf),str(rom)],check=True);subprocess.run([sys.executable,str(ROOT/'tools/fix_header.py'),str(rom)],check=True,stdout=subprocess.DEVNULL)
    syms={a[2]:int(a[0],16) for line in subprocess.check_output([arm['nm'],'-n',str(elf)],text=True).splitlines() if len(a:=line.split())==3}
    from mgba_runner import Emulator
    labels=['catalog_validate','roster_validate','historical_r4_roster_validate','coverage_including_validation','grant_query_including_validation','evolution_query_including_validation','admitted_grant_full_transaction'];results=[]
    with Emulator(rom) as emu:
        for _ in range(100):
            emu.frames(120)
            if emu.read(syms['completed']):break
        assert emu.read(syms['completed'])==1,('setup failed',emu.read(syms['error']))
        for n,label in enumerate(['native-earned-S3-21','host-staged-34-all65-history','grandfathered-full160','safe-extra-limit89']):
            row={'label':label,'retained':emu.read(syms['counts']+n*4),'operations':{}}
            for op,name in enumerate(labels):
                cs=[emu.read(syms['cycles']+((n*7+op)*4+k)*4) for k in range(4)];ans=[emu.read(syms['answers']+((n*7+op)*4+k)*4) for k in range(4)]
                row['operations'][name]={'cycles':cs,'max_cycles':max(cs),'results':ans,'observed_stack_below_main_sp':emu.read(syms['stack_bytes']+(n*7+op)*4)}
            assert row['operations']['catalog_validate']['results']==[1]*4 and row['operations']['roster_validate']['results']==[1]*4
            assert row['operations']['coverage_including_validation']['results']==[1]*4
            results.append(row)
    sections={u:subprocess.check_output([arm['size'],'-A',str(out/f'{u}.o')],text=True) for u in ('creatures','creature_data')}
    stack={}
    for u in ('creatures','creature_data'):
        for line in (out/f'{u}.su').read_text().splitlines():
            name,size,kind=line.split('\t');stack[name.split(':')[-1]]={'bytes':int(size),'kind':kind}
    report={'purpose':__doc__,'earned_sram_sha256':sha(args.earned_sram),'source_sha256':source_hash,'source_unchanged':source_hash=={k:sha(ROOT/k) for k in source_hash},'rom_sha256':sha(rom),'compiler':subprocess.check_output([arm['gcc'],'--version'],text=True).splitlines()[0],'waitcnt':'0x4317','timer_hz':16777216,'frame_cycles':280896,'scenarios':results,'object_sections':sections,'compiler_stack_frames':stack,'stack_note':'Measured isolated subcall watermark below main SP, not whole-engine stack high-water. No core mutable data/bss; benchmark fixture state itself is harness-only.'}
    def object_totals(sections):
        totals={}
        for unit,text in sections.items():
            items={a[0]:int(a[1]) for line in text.splitlines() if len(a:=line.split())==3 and a[0].startswith('.')}
            totals[unit]={'rom_sections':sum(v for k,v in items.items() if k.startswith(('.text','.rodata'))),'mutable_data_bss':sum(v for k,v in items.items() if k in ('.data','.bss')),'sections':items}
        return totals
    report['object_budget']={'current65':object_totals(sections)}
    if args.baseline_source:
        base=args.baseline_source.resolve();folder=out/'baseline';folder.mkdir(exist_ok=True);base_sections={}
        for unit in ('creatures','creature_data'):
            subprocess.run([arm['gcc'],*flags,'-I'+str(base),'-c',str(base/f'{unit}.c'),'-o',str(folder/f'{unit}.o')],check=True)
            base_sections[unit]=subprocess.check_output([arm['size'],'-A',str(folder/f'{unit}.o')],text=True)
        budget=report['object_budget'];budget['baseline_foundation41']=object_totals(base_sections)
        budget['incremental_rom_sections']=sum(d['rom_sections'] for d in budget['current65'].values())-sum(d['rom_sections'] for d in budget['baseline_foundation41'].values())
        budget['baseline_sha256']={u:sha(base/u) for u in ('creatures.c','creatures.h','creature_data.c')}
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');assert report['source_unchanged']
    for row in results:print(row['label'],row['retained'],{k:v['max_cycles'] for k,v in row['operations'].items()})
if __name__=='__main__':main()
