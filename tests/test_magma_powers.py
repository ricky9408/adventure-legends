#!/usr/bin/env python3
"""Strict and sanitizer host C integration, plus ARM ROM/data/stack accounting.

Not a substitute for a controller-only native gameplay acceptance route.
"""
from pathlib import Path
import json
import hashlib
import os
import subprocess
ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build' / 'magma-powers-host'
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = ['tests/magma_powers_native.c', 'tests/legacy_underwater_hooks.c', 'src/magma_powers.c', 'src/magma_power_art.c', 'src/southern_powers.c', 'src/southern_power_art.c', 'src/northern_powers.c',
           'src/northern_power_art.c', 'src/advanced_powers.c',
           'src/regional_powers.c', 'src/gear_runtime.c', 'src/weapon_actions.c',
           'src/combat_rules.c', 'src/equipment.c', 'src/equipment_data.c',
           'src/creatures.c', 'src/creature_data.c', 'src/assets.c']
for name, flags in [('strict', []), ('sanitized', ['-fsanitize=address,undefined',
                                                '-fno-omit-frame-pointer'])]:
    exe = OUT / name
    subprocess.run(['cc', '-std=c99', '-O1', '-g', '-Wall', '-Wextra', '-Werror',
                    '-Wno-misleading-indentation', '-pedantic', '-Isrc',
                    *flags, *SOURCES, '-o', str(exe)], cwd=ROOT, check=True)
    subprocess.run([str(exe)], cwd=ROOT, check=True,
                   env=dict(os.environ, ASAN_OPTIONS='detect_leaks=0'))
arm = ROOT / 'tools/sysroot/usr/bin/arm-none-eabi-gcc'
if arm.exists():
    prefix = str(arm).removesuffix('gcc')
    objects = []
    for source in ['src/magma_powers.c', 'src/magma_power_art.c']:
        obj = OUT / (Path(source).stem + '.o')
        subprocess.run([str(arm), '-mcpu=arm7tdmi', '-mthumb-interwork', '-mthumb',
                        '-std=c99', '-O2', '-ffreestanding', '-fno-builtin',
                        '-fno-strict-aliasing', '-fomit-frame-pointer', '-Wall',
                        '-Wextra', '-Werror', '-fstack-usage', '-Isrc', '-c',
                        source, '-o', str(obj)], cwd=ROOT, check=True)
        objects.append(str(obj))
    size = subprocess.check_output([prefix+'size', *objects], text=True)
    sections = subprocess.check_output([prefix+'objdump', '-h', *objects], text=True)
    undefined = subprocess.check_output([prefix+'nm', '-u', objects[0]], text=True)
    assert '__aeabi_idiv' not in undefined and '__aeabi_uidiv' not in undefined, 'Effect paths must not require integer division'
    stack = '\n'.join(p.read_text() for p in OUT.glob('*.su'))
    assert '.iwram' not in sections, 'Magma code must stay ROM-resident'
    rows = [line.split() for line in size.strip().splitlines()[1:]]
    bss = sum(int(row[2]) for row in rows)
    data = sum(int(row[1]) for row in rows)
    max_stack = max(int(line.split('\t')[1]) for line in stack.splitlines() if line)
    assert bss+data < 1024, 'New transient state exceeds the 1 KiB bound'
    assert max_stack <= 128, 'No large local pixel/grid buffers allowed'
    report = {'kind':'host-and-ARM-object-evidence-not-native-gameplay', 'bss_bytes':bss, 'data_bytes':data,
              'max_individual_function_stack_bytes':max_stack, 'rom_resident':True, 'additional_resident_OBJ_bytes':0,
              'size':size, 'stack_usage':stack, 'sections':sections,
              'source_sha256':hashlib.sha256((ROOT/'src/magma_powers.c').read_bytes()).hexdigest(),
              'module_only_call_chain_bound_bytes':384,
              'stack_note':'Conservative module-only bound; excludes external world/renderer/progression callbacks and IRQ context.',
              'all_commands_all_five_phases_and_neutral':144,'observed_max_draw_objects':19,'hard_draw_object_cap':24,
              'max_internal_missiles':3,'max_enemy_ledger_entries':6,
              'scope':'Exact core65 catalog with existing Q4/gear/weapon runtime. Synthetic world/collision/OBJ and exposed chapter-coupling bridges; real gear busy and weapons; no controller gameplay claim.'}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(size,end='')
    print(f'ARM: BSS+data={bss+data}; max individual stack={max_stack}; no IWRAM; OBJ delta=0')
else:
    print('ARM compiler unavailable; ARM object/stack evidence NOT run')

# Separate timing cartridge; never replace build/emberbond.{elf,gba,sym}.
# ELF symbols are selected by STT_FILE scope, never last-name-wins nm parsing.
def scoped_elf_objects(path, filename):
    import struct
    raw=Path(path).read_bytes()
    assert raw[:6]==b'\x7fELF\x01\x01'
    h=struct.unpack_from('<16sHHIIIIIHHHHHH',raw)
    assert h[2]==40
    sections=[struct.unpack_from('<IIIIIIIIII',raw,h[6]+i*h[11]) for i in range(h[12])]
    result={}
    for section in sections:
        if section[1]!=2: continue
        strings=sections[section[6]];strings=raw[strings[4]:strings[4]+strings[5]]
        current=None
        for p in range(section[4],section[4]+section[5],section[9]):
            n,value,size,info,other,index=struct.unpack_from('<IIIBBH',raw,p)
            name=strings[n:].split(b'\0',1)[0].decode()
            if info&15==4: current=name
            if current==filename and info>>4==0 and info&15==1:
                assert name not in result, (filename,name)
                result[name]={'address':value,'size':size}
    return result

if arm.exists():
    import sys
    bench=OUT/'arm-bench';bench.mkdir(exist_ok=True)
    harness=(ROOT/'tests/magma_powers_native.c').read_text().split('static const unsigned start')[0]
    for header in ['assert.h','stdio.h','stdlib.h','string.h','limits.h']:
        harness=harness.replace('#include <'+header+'>','')
    prelude=r'''
typedef unsigned size_t;
static volatile unsigned bench_completed,bench_fault_line;
#define assert(c) do {if(!(c)){bench_fault_line=__LINE__;bench_completed=2;while(1){}}} while(0)
static int abs(int n){return n<0?-n:n;}
static void *memset(void*v,int c,unsigned n){unsigned char*p=v;while(n--)*p++=(unsigned char)c;return v;}
static void *memcpy(void*v,const void*s,unsigned n){unsigned char*p=v;const unsigned char*q=s;while(n--)*p++=*q++;return v;}
'''
    main=r'''
#define REG16(a) (*(volatile unsigned short *)(a))
static volatile unsigned bench_timings[24][4],bench_counts[24][4],bench_steady[24][2];
static unsigned now(void){unsigned hi,lo,next;do{hi=REG16(0x0400010c);lo=REG16(0x04000108);next=REG16(0x0400010c);}while(hi!=next);return(hi<<16)|lo;}
int main(void){unsigned c,i,n,t,elapsed;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010c)=0;REG16(0x0400010e)=0x84;REG16(0x04000108)=0;REG16(0x0400010a)=0x80;
 for(c=43;c<=66;c++){
  setup(c);for(i=0;i<5;i++)enemy(i,112+(int)i*5,92+(int)i*4,100);
  t=now();assert(magma_power(c));bench_timings[c-43][0]=now()-t;
  for(n=0;n<96;n++){
   if(n==12&&c==47)magma_powers_melee_guard(0,enemies[0].x,enemies[0].y);
   if(n==16&&c==60){shot(0,124,100,-8,0,30,1);magma_powers_intercept_shot(0,124,100,116,100,1);}
   if(n==18){chapter_enabled=1;chapter_x=132;chapter_y=100;}
   if(n==22)wall(125,104,4,5);
   if(n==26){wall_count=0;magma_powers_geometry_changed();}
   solid_calls=0;t=now();magma_powers_tick();elapsed=now()-t;
   if(elapsed>bench_timings[c-43][1])bench_timings[c-43][1]=elapsed;
   if((unsigned)solid_calls>bench_counts[c-43][0])bench_counts[c-43][0]=(unsigned)solid_calls;
   draws=solid_calls=0;t=now();magma_powers_draw();elapsed=now()-t;
   if(elapsed>bench_timings[c-43][2])bench_timings[c-43][2]=elapsed;
   if((unsigned)draws>bench_counts[c-43][1])bench_counts[c-43][1]=(unsigned)draws;
   if((unsigned)solid_calls>bench_counts[c-43][2])bench_counts[c-43][2]=(unsigned)solid_calls;
   solid_calls=draws=0;t=now();magma_powers_draw();elapsed=now()-t;
   if(elapsed>bench_steady[c-43][0])bench_steady[c-43][0]=elapsed;
   if((unsigned)solid_calls>bench_steady[c-43][1])bench_steady[c-43][1]=(unsigned)solid_calls;
   t=now();assert(!magma_power_time||magma_powers_busy());elapsed=now()-t;
   if(elapsed>bench_timings[c-43][3])bench_timings[c-43][3]=elapsed;
   regional_powers_tick();advanced_tick();game_combat_tick();if(ability_cd)ability_cd--;
  }
  updates(1);
 }
 bench_completed=1;while(1){}return 0;
}
'''
    (bench/'main.c').write_text(prelude+harness+main)
    flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fstack-usage','-ffunction-sections','-fdata-sections','-Isrc']
    objects=[]
    for source in [str(bench/'main.c'),*SOURCES[1:]]:
        obj=bench/(Path(source).stem+'.o')
        subprocess.run([str(arm),*flags,'-c',source,'-o',str(obj)],cwd=ROOT,check=True)
        objects.append(str(obj))
    startup=bench/'startup.o'
    subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c','src/startup.s','-o',str(startup)],cwd=ROOT,check=True)
    elf=bench/'bench.elf';rom=bench/'bench.gba';raw_image=bench/'bench-unfixed.bin'
    subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,--gc-sections,-T,linker.ld',str(startup),*objects,'-lgcc','-o',str(elf)],cwd=ROOT,check=True)
    subprocess.run([prefix+'objcopy','-O','binary',str(elf),str(rom)],check=True)
    raw_image.write_bytes(rom.read_bytes())
    subprocess.run([sys.executable,'tools/fix_header.py',str(rom)],cwd=ROOT,check=True)
    assert raw_image.read_bytes()[192:]==rom.read_bytes()[192:]
    scoped=scoped_elf_objects(elf,'main.c');power_scoped=scoped_elf_objects(elf,'magma_powers.c')
    for name,size in [('bench_completed',4),('bench_fault_line',4),('bench_timings',384),('bench_counts',384),('bench_steady',192)]:
        assert scoped[name]['size']==size,(name,scoped.get(name))
    assert power_scoped['caster_id']['size']==4 and power_scoped['paths']['size']==240
    sys.path.insert(0,str(ROOT/'tools'));from mgba_runner import Emulator
    with Emulator(rom) as emu:
        for _ in range(240):
            emu.frames(10)
            if emu.read(scoped['bench_completed']['address']):break
        assert emu.read(scoped['bench_completed']['address'])==1,('benchmark fault',emu.read(scoped['bench_fault_line']['address']))
        timing=[[emu.read(scoped['bench_timings']['address']+(c*4+n)*4) for n in range(4)] for c in range(24)]
        counts=[[emu.read(scoped['bench_counts']['address']+(c*4+n)*4) for n in range(4)] for c in range(24)]
        steady=[[emu.read(scoped['bench_steady']['address']+(c*2+n)*4) for n in range(2)] for c in range(24)]
    measured={'kind':'isolated-ARM7TDMI-module-timing-synthetic-world-and-OBJ-callbacks',
              'waitcnt':'0x4317','clock_hz':16777216,'frame_cycles':280896,
              'columns':['cast_cycles','max_tick_cycles','max_draw_cycles','max_busy_check_cycles'],
              'commands':{str(c+43):{'cycles':timing[c],'max_tick_solid_calls':counts[c][0],
                 'max_draw_objects':counts[c][1],'max_draw_solid_calls':counts[c][2],
                 'max_steady_draw_cycles':steady[c][0],'max_steady_draw_solid_calls':steady[c][1]} for c in range(24)},
              'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),
              'elf_sha256':hashlib.sha256(elf.read_bytes()).hexdigest(),
              'elf_symbol_source':'STT_FILE-scoped main.c and magma_powers.c objects, size checked',
              'elf_rom_matched_bytes':len(rom.read_bytes())-192,
              'conservative_max_tick_plus_draw_cycles':max(row[1]+row[2] for row in timing),
              'source_sha256':{src:hashlib.sha256((ROOT/src).read_bytes()).hexdigest() for src in SOURCES},
              'limitation':'No full game loop, actual room collision, OAM/cache pressure, controller acceptance, physical hardware or native frame-budget guarantee is implied.'}
    (OUT/'arm-timing.json').write_text(json.dumps(measured,indent=2)+'\n')
    print('ARM7TDMI maxima: cast/tick/draw/busy cycles',*[max(row[n] for row in timing) for n in range(4)])
    print('Repeated unchanged draw: max scenery probes',max(row[1] for row in steady))
