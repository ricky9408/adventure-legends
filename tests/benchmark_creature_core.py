#!/usr/bin/env python3
"""Isolated ARM7TDMI core microbenchmark; never builds the main game ROM.
The optional128-row stress fixture pads/reorders the lookup table only. It is
not a valid/playable128-form catalog and does not enable reserved content.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from arm_toolchain import resolve_arm_tools
MAIN=r'''
#include "creatures.h"
#define REG16(a) (*(volatile unsigned short *)(a))
static CreatureRoster roster;
volatile unsigned timings[8], answers[8], completed;
static unsigned now(void) {
    unsigned hi,lo,again;
    do {hi=REG16(0x0400010c);lo=REG16(0x04000108);again=REG16(0x0400010c);} while(hi!=again);
    return (hi<<16)|lo;
}
int main(void) {
    unsigned i,t,answer=0;
    REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
    REG16(0x0400010c)=0;REG16(0x0400010e)=0x84;REG16(0x04000108)=0;REG16(0x0400010a)=0x80;
    creatures_roster_init(&roster);
    for(i=0;i<160;++i) {
        CreatureInstance *c=&roster.instances[i];
        const CreatureForm *f=creatures_form(BENCH_FORM);
        c->form_id=BENCH_FORM;c->flags=CREATURE_OCCUPIED;c->level=50;c->bond=100;
        c->xp=CREATURE_XP_CAP;c->instance_id=i+1;c->polarity=f->polarity;
        c->equipped[0]=creature_learnsets[f->learnset_offset].ability_id;
    }
    roster.next_instance_id=161;
    roster.seen[(BENCH_FORM-1)>>3]|=1u<<((BENCH_FORM-1)&7);
    roster.obtained[(BENCH_FORM-1)>>3]|=1u<<((BENCH_FORM-1)&7);
    for(i=0;i<4;++i)roster.party[i]=(CreatureU8)i;
    roster.selected_party=0;
    t=now();answer=creatures_catalog_validate();timings[0]=now()-t;answers[0]=answer;
    t=now();answer=creatures_roster_validate(&roster);timings[1]=now()-t;answers[1]=answer;
    t=now();answer=creatures_party_validate(&roster);timings[2]=now()-t;answers[2]=answer;
    t=now();answer=0;for(i=0;i<160;++i)answer+=creatures_instance_validate(&roster.instances[i]);timings[3]=now()-t;answers[3]=answer;
    t=now();answer=0;for(i=0;i<1000;++i)answer+=creatures_form(BENCH_FORM)!=0;timings[4]=now()-t;answers[4]=answer;
    t=now();answer=0;for(i=0;i<1000;++i)answer+=creatures_form(255)!=0;timings[5]=now()-t;answers[5]=answer;
#ifdef REVISION_API
    t=now();answer=0;for(i=0;i<160;++i)answer+=creatures_instance_validate_revision(&roster.instances[i],4);timings[6]=now()-t;answers[6]=answer;
#endif
    completed=1;while(1){}return 0;
}
'''
def main():
    parser=argparse.ArgumentParser();parser.add_argument('--baseline',type=Path,required=True);parser.add_argument('--output',type=Path,default=ROOT/'build/southern-core-timing');args=parser.parse_args()
    out=args.output.resolve();out.mkdir(parents=True,exist_ok=True)
    from mgba_runner import Emulator
    arm=resolve_arm_tools('gcc','objcopy','nm',root=ROOT)
    flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-pedantic','-fstack-usage']
    report={'purpose':__doc__,'waitcnt':'0x4317','frame_cycles':280896,'timer_clock_hz':16777216,'scenarios':[]}
    for mode in ['baseline21','current41','lookup_stress128']:
        folder=out/mode;folder.mkdir(exist_ok=True)
        src=args.baseline if mode=='baseline21' else ROOT/'src'
        for filename in ['creatures.h','creatures.c','creature_data.c']:(folder/filename).write_bytes((src/filename).read_bytes())
        if mode=='lookup_stress128':
            h=(folder/'creatures.h').read_text().replace('CREATURE_ENABLED_COUNT = 41','CREATURE_ENABLED_COUNT = 128');(folder/'creatures.h').write_text(h)
            data=(folder/'creature_data.c').read_text();enabled=[1,2,4,5,7,8,10,11,13,14,16,19,20,22,23,73,74,75,76,77,78,25,26,28,29]+list(range(79,95))
            rows='\n'.join('    {%d, 0, 0, 0, 0, 0, {1, 1, 1, 1, 1}, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0},'%i for i in range(1,129) if i not in enabled)
            data=data.replace('creature_forms[CREATURE_ENABLED_COUNT] = {\n','creature_forms[CREATURE_ENABLED_COUNT] = {\n'+rows+'\n')
            if 'creature_form_index[' in data:
                from test_creature_sparse import edit_array
                ordered=[i for i in range(1,129) if i not in enabled]+enabled
                values=[0]*129
                for row,id_ in enumerate(ordered):values[id_]=row+1
                data=edit_array(data,'creature_form_index',lambda _: '    '+', '.join(map(str,values))+',')
            (folder/'creature_data.c').write_text(data)
        (folder/'main.c').write_text(MAIN)
        defs=['-DBENCH_FORM='+('78' if mode=='baseline21' else '94')]+([] if mode=='baseline21' else ['-DREVISION_API'])
        for unit in ['creatures','creature_data','main']:
            subprocess.run([arm['gcc'],*flags,*defs,'-I'+str(folder),'-c',str(folder/(unit+'.c')),'-o',str(folder/(unit+'.o'))],check=True)
        subprocess.run([arm['gcc'],'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c',str(ROOT/'src/startup.s'),'-o',str(folder/'startup.o')],check=True)
        elf=folder/'bench.elf';rom=folder/'bench.gba'
        subprocess.run([arm['gcc'],'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,-T,'+str(ROOT/'linker.ld'),*[str(folder/(n+'.o')) for n in ['startup','main','creatures','creature_data']],'-lgcc','-o',str(elf)],check=True)
        subprocess.run([arm['objcopy'],'-O','binary',str(elf),str(rom)],check=True)
        subprocess.run([sys.executable,str(ROOT/'tools/fix_header.py'),str(rom)],check=True,stdout=subprocess.DEVNULL)
        symbols={line.split()[2]:int(line.split()[0],16) for line in subprocess.check_output([arm['nm'],str(elf)],text=True).splitlines() if len(line.split())==3}
        with Emulator(rom) as emu:
            for _ in range(300):
                emu.frames(10)
                if emu.read(symbols['completed']):break
            else:raise RuntimeError(mode+' did not complete')
            timings=[emu.read(symbols['timings']+4*i) for i in range(7)];answers=[emu.read(symbols['answers']+4*i) for i in range(7)]
        assert answers[:6]==[0 if mode=='lookup_stress128' else 1,1,1,160,1000,0],(mode,answers)
        if mode!='baseline21':assert answers[6]==160
        labels=['catalog_validate','full160_roster_validate','party4_validate','instances160_validate','lookup_hit_1000','lookup_miss_1000','instances160_revision_validate']
        result={'mode':mode,'cycles':dict(zip(labels,timings)),'answers':answers,'source_sha256':{f:hashlib.sha256((folder/f).read_bytes()).hexdigest() for f in ['creatures.h','creatures.c','creature_data.c']},'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest()}
        report['scenarios'].append(result);print(mode,result['cycles'])
    (out/'report.json').write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
