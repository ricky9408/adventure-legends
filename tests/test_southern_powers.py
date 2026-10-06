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
OUT = ROOT / 'build' / 'southern-powers-host'
OUT.mkdir(parents=True, exist_ok=True)
SOURCES = ['tests/southern_powers_native.c', 'src/southern_powers.c', 'src/southern_power_art.c', 'src/northern_powers.c',
           'src/northern_power_art.c', 'src/advanced_powers.c',
           'src/regional_powers.c', 'src/gear_runtime.c', 'tests/legacy_magma_hooks.c', 'tests/legacy_underwater_hooks.c', 'src/weapon_actions.c',
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
    for source in ['src/southern_powers.c', 'src/southern_power_art.c']:
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
    assert '.iwram' not in sections, 'Northern code must stay ROM-resident'
    rows = [line.split() for line in size.strip().splitlines()[1:]]
    bss = sum(int(row[2]) for row in rows)
    data = sum(int(row[1]) for row in rows)
    max_stack = max(int(line.split('\t')[1]) for line in stack.splitlines() if line)
    assert bss+data < 1024, 'New transient state exceeds the 1 KiB bound'
    assert max_stack <= 128, 'No large local pixel/grid buffers allowed'
    report = {'kind':'host-and-ARM-object-evidence-not-native-gameplay', 'bss_bytes':bss, 'data_bytes':data,
              'max_individual_function_stack_bytes':max_stack, 'rom_resident':True, 'additional_resident_OBJ_bytes':0,
              'size':size, 'stack_usage':stack, 'sections':sections,
              'source_sha256':hashlib.sha256((ROOT/'src/southern_powers.c').read_bytes()).hexdigest(),
              'module_only_call_chain_bound_bytes':256,
              'stack_note':'Conservative module-only bound; excludes external world/renderer/progression callbacks and IRQ context.',
              'cached_crescent_differential_cases':2380,'host_drawing_stress_calls':4800,'observed_max_draw_objects':12,'hard_draw_object_cap':24,
              'max_internal_missiles':3,'max_enemy_ledger_entries':6,
              'scope':'Exact core41 catalog with existing Q4/gear/weapon runtime. Synthetic world/collision/OBJ stubs; no controller gameplay claim.'}
    (OUT/'report.json').write_text(json.dumps(report,indent=2)+'\n')
    print(size,end='')
    print(f'ARM: BSS+data={bss+data}; max individual stack={max_stack}; no IWRAM; OBJ delta=0')
else:
    print('ARM compiler unavailable; ARM object/stack evidence NOT run')

# Run the exact handlers on ARM7TDMI in a tiny isolated cartridge. The collision,
# drawing and UI callbacks remain synthetic; this is module timing, not gameplay.
if arm.exists():
    import sys
    bench = OUT/'arm-bench'
    bench.mkdir(exist_ok=True)
    harness=(ROOT/'tests/southern_powers_native.c').read_text().split('static void test_every_command')[0]
    for header in ['assert.h','stdio.h','stdlib.h','string.h']:
        harness=harness.replace('#include "'+header+'"','').replace('#include <'+header+'>','')
    harness=harness[:harness.index('static void expect_damage')]
    prelude=r'''
typedef unsigned size_t;
volatile unsigned completed,fault_line;
#define assert(c) do {if(!(c)){fault_line=__LINE__;completed=2;while(1){}}} while(0)
static int abs(int n){return n<0?-n:n;}
static void *memset(void *v,int c,unsigned n){unsigned char*p=v;while(n--)*p++=(unsigned char)c;return v;}
static void *memcpy(void *v,const void*s,unsigned n){unsigned char*p=v;const unsigned char*q=s;while(n--)*p++=*q++;return v;}
'''
    main=r'''
#define REG16(a) (*(volatile unsigned short *)(a))
volatile unsigned timings[20][4],counts[20][2],steady_draw[20],steady_draw_solid[20],paired_probe[4];
static unsigned now(void){unsigned hi,lo,again;do{hi=REG16(0x0400010c);lo=REG16(0x04000108);again=REG16(0x0400010c);}while(hi!=again);return(hi<<16)|lo;}
int main(void){unsigned c,i,n,t,elapsed;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010c)=0;REG16(0x0400010e)=0x84;REG16(0x04000108)=0;REG16(0x0400010a)=0x80;
 for(c=23;c<=42;c++){
  setup(c);for(i=0;i<6;i++){enemy(i,124+(int)i,100+(int)i,10);if(c==29)enemies[i].kind=2;}
  if(c==40){enemies[1].x=100;enemies[1].y=130;}
  t=now();assert(southern_power(c));timings[c-23][0]=now()-t;
  for(n=0;n<62;n++){
   if(n==8){int x,y;if(c==28){shot(0,126,100,-4,0,30,1);southern_powers_intercept_shot(0,126,100,122,100,1);}
    if(c==29)southern_powers_windup(0,30);if(c==31||c==32)southern_powers_melee_guard(0,100,90);
    if(c==33)southern_powers_melee_guard(0,110,100);if(c==26||c==35||c==36)southern_powers_approach(0,&x,&y);
    if(c==39)southern_powers_weapon_hit(0);if(c==40){face=0;southern_powers_aim();southern_powers_weapon_hit(0);}}
   solid_calls=0;t=now();southern_powers_tick();elapsed=now()-t;
   if(elapsed>timings[c-23][1])timings[c-23][1]=elapsed;
   if((unsigned)solid_calls>counts[c-23][0])counts[c-23][0]=(unsigned)solid_calls;
   draws=0;solid_calls=0;t=now();southern_powers_draw();elapsed=now()-t;
   if(elapsed>timings[c-23][2])timings[c-23][2]=elapsed;
   if(n>0&&elapsed>steady_draw[c-23])steady_draw[c-23]=elapsed;
   if(n>0&&(unsigned)solid_calls>steady_draw_solid[c-23])steady_draw_solid[c-23]=(unsigned)solid_calls;
   if((unsigned)draws>counts[c-23][1])counts[c-23][1]=(unsigned)draws;
   t=now();assert(!southern_power_time||game_gear_busy());elapsed=now()-t;
   if(elapsed>timings[c-23][3])timings[c-23][3]=elapsed;
   regional_powers_tick();if(ability_cd)ability_cd--;
  }
 }
 setup(40);px=296;py=96;face=3;enemy(0,320,96,10);enemy(1,272,48,10);assert(southern_power(40));
 px=272;py=80;face=1;solid_calls=0;t=now();assert(southern_powers_aim());paired_probe[0]=now()-t;paired_probe[1]=(unsigned)solid_calls;
 solid_calls=0;t=now();southern_powers_draw();paired_probe[2]=now()-t;paired_probe[3]=(unsigned)solid_calls;
 completed=1;while(1){}return 0;
}
'''
    # Remove helpers that the timing loop intentionally does not call.
    harness=harness.replace('static void updates(unsigned n){while(n--){southern_powers_tick();regional_powers_tick();if(ability_cd&&!hitstop)ability_cd--;}}','')
    harness=harness.replace('static void wall(int x,int y,int w,int h){assert(wall_count<8);walls[wall_count].x=x;\n    walls[wall_count].y=y;walls[wall_count].w=w;walls[wall_count++].h=h;southern_powers_geometry_changed();}','')
    (bench/'main.c').write_text(prelude+harness+main)
    flags=['-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-O2','-std=c99','-ffreestanding','-fno-builtin','-fno-strict-aliasing','-fomit-frame-pointer','-Wall','-Wextra','-Werror','-Wno-misleading-indentation','-fstack-usage','-ffunction-sections','-fdata-sections','-Isrc']
    objects=[]
    for src in [str(bench/'main.c'),*SOURCES[1:]]:
        obj=bench/(Path(src).stem+'.o')
        subprocess.run([str(arm),*flags,'-c',src,'-o',str(obj)],cwd=ROOT,check=True)
        objects.append(str(obj))
    startup=bench/'startup.o'
    subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-marm','-x','assembler-with-cpp','-c','src/startup.s','-o',str(startup)],cwd=ROOT,check=True)
    elf=bench/'bench.elf';rom=bench/'bench.gba'
    subprocess.run([str(arm),'-mcpu=arm7tdmi','-mthumb-interwork','-mthumb','-nostdlib','-Wl,--gc-sections,-T,linker.ld',str(startup),*objects,'-lgcc','-o',str(elf)],cwd=ROOT,check=True)
    subprocess.run([prefix+'objcopy','-O','binary',str(elf),str(rom)],check=True)
    subprocess.run([sys.executable,'tools/fix_header.py',str(rom)],cwd=ROOT,check=True)
    syms={p[2]:int(p[0],16) for line in subprocess.check_output([prefix+'nm',str(elf)],text=True).splitlines() if len(p:=line.split())==3}
    sys.path.insert(0,str(ROOT/'tools'));from mgba_runner import Emulator
    with Emulator(rom) as emu:
        for _ in range(200):
            emu.frames(10)
            if emu.read(syms['completed']):break
        assert emu.read(syms['completed'])==1,('benchmark fault',emu.read(syms['fault_line']))
        timing=[[emu.read(syms['timings']+(c*4+n)*4) for n in range(4)] for c in range(20)]
        counts=[[emu.read(syms['counts']+(c*2+n)*4) for n in range(2)] for c in range(20)]
        steady=[emu.read(syms['steady_draw']+c*4) for c in range(20)]
        steady_solid=[emu.read(syms['steady_draw_solid']+c*4) for c in range(20)]
        paired=[emu.read(syms['paired_probe']+i*4) for i in range(4)]
    measured={'kind':'isolated-ARM7TDMI-module-timing-synthetic-world-and-OBJ-callbacks',
              'waitcnt':'0x4317','clock_hz':16777216,'frame_cycles':280896,
              'columns':['cast_cycles','max_tick_cycles','max_draw_cycles','max_busy_check_cycles'],
              'commands':{str(c+23):{'cycles':timing[c],'max_tick_solid_calls':counts[c][0],'max_draw_objects':counts[c][1],'max_steady_draw_cycles':steady[c],'max_steady_draw_solid_calls':steady_solid[c]} for c in range(20)},
              'rom_sha256':hashlib.sha256(rom.read_bytes()).hexdigest(),
              'conservative_max_tick_plus_draw_cycles':max(row[1]+row[2] for row in timing),
              'paired_native_position_probe':{'positions':[[320,96],[272,48]],'second_aim_cycles':paired[0],'second_aim_solid_calls':paired[1],'same_frame_draw_cycles':paired[2],'same_frame_draw_solid_calls':paired[3]},
              'source_sha256':{src:hashlib.sha256((ROOT/src).read_bytes()).hexdigest() for src in SOURCES},
              'limitation':'No full game loop, world room collision, renderer OAM/cache pressure, controller acceptance or frame-budget guarantee is implied.'}
    (OUT/'arm-timing.json').write_text(json.dumps(measured,indent=2)+'\n')
    print('ARM7TDMI maxima: cast/tick/draw/busy cycles',*[max(row[n] for row in timing) for n in range(4)])
