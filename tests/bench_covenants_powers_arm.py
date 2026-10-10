#!/usr/bin/env python3
"""Actual ARM7TDMI cycles for isolated production powers and synthetic callbacks.

This builds a separate diagnostic ROM; timers2/3 belong only to that ROM.
It is neither controller-obtainability nor full-game frame-budget evidence.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import struct
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'build/covenants-powers-host/arm-bench'
OUT.mkdir(parents=True, exist_ok=True)
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--mgba-tools', type=Path, default=ROOT / 'tools')
parser.add_argument('--power-source', type=Path, default=ROOT / 'src/covenants_powers.c')
parser.add_argument('--output', type=Path, default=OUT)
args = parser.parse_args()
OUT = args.output.resolve()
OUT.mkdir(parents=True, exist_ok=True)
assert (args.mgba_tools / 'mgba_bridge.so').is_file(), 'Pass --mgba-tools with a built supported bridge'
arm = ROOT / 'tools/sysroot/usr/bin/arm-none-eabi-gcc'
prefix = str(arm).removesuffix('gcc')
def run(command):
    subprocess.run(command, cwd=ROOT, check=True)

harness = (ROOT / 'tests/covenants_powers_host.c').read_text().split('static void invalid_contract')[0]
for header in ('assert.h', 'stdio.h', 'stdlib.h', 'string.h'):
    harness = harness.replace('#include <' + header + '>', '')
aliases = {'solid': 'inherited_solid', 'game_clear_box': 'inherited_clear_box',
           'game_collision_rects': 'inherited_collision_rects',
           'covenants_game_supercover': 'inherited_covenants_supercover'}
harness = ''.join('#define ' + a + ' ' + b + '\n' for a, b in aliases.items()) + harness
harness += ''.join('#undef ' + a + '\n' for a in aliases)
practice_helpers = (ROOT / 'tests/covenants_practice_geometry.c').read_text().split('#include "covenants_art.h"', 1)[1].split('static int visible', 1)[0]
practice_helpers = '#include "covenants_art.h"\n' + practice_helpers
practice_helpers = practice_helpers.replace('unsigned i;const unsigned short *b;', 'unsigned i;const unsigned short *b;if(!art)return inherited_solid(x,y);')
practice_helpers = practice_helpers.replace('int y;unsigned i,offset;const unsigned short *b;', 'int y;unsigned i,offset;const unsigned short *b;if(!art)return inherited_clear_box(x0,y0,x1,y1);')
practice_helpers = practice_helpers.replace('unsigned i,n=0,offset;int y,end,last;const unsigned short *b;', 'unsigned i,n=0,offset;int y,end,last;const unsigned short *b;if(!art)return inherited_collision_rects(x0,y0,x1,y1,out,cap);')
practice_helpers = practice_helpers.replace('if(solid(x,y)||solid(tx,ty))return 0;', 'if(!art)return inherited_covenants_supercover(x,y,tx,ty);if(solid(x,y)||solid(tx,ty))return 0;')
harness += practice_helpers
geometry = json.loads((ROOT / 'assets/covenants_world/geometry.json').read_text())
practice_cases = [room['practice'] for room in geometry['rooms']]
practice_source = 'static const short practice_origins[8][2]={' + ','.join('{' + ','.join(map(str, case['start_xy'])) + '}' for case in practice_cases) + '};\n'
practice_source += 'static const short practice_targets[8][2][3]={' + ','.join('{' + ','.join('{' + ','.join(map(str, target['center'] + [target['radius']])) + '}' for target in case['targets']) + '}' for case in practice_cases) + '};\n'
harness += practice_source
prelude = r'''
static volatile unsigned bench_completed,bench_fault_line;
#define assert(c) do {if(!(c)){bench_fault_line=__LINE__;bench_completed=2;while(1){}}} while(0)
static int abs(int n){return n<0?-n:n;}
static void *memset(void*v,int c,unsigned n){unsigned char*p=v;while(n--)*p++=(unsigned char)c;return v;}
static void *memcpy(void*v,const void*s,unsigned n){unsigned char*p=v;const unsigned char*q=s;while(n--)*p++=*q++;return v;}
'''
main = r'''
#define REG16(a) (*(volatile unsigned short *)(a))
static volatile unsigned bench_timings[6][8][4],bench_counts[6][8][3];
static unsigned now(void){unsigned hi,lo,next;do{hi=REG16(0x0400010c);lo=REG16(0x04000108);next=REG16(0x0400010c);}while(hi!=next);return(hi<<16)|lo;}
int main(void){unsigned mode,c,i,n,t,elapsed;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x0400010c)=0;REG16(0x0400010e)=0x84;REG16(0x04000108)=0;REG16(0x0400010a)=0x80;
 for(mode=0;mode<6;mode++)for(c=0;c<8;c++){
  snapshot_refuse=mode==2||mode==5;setup(commands[c]);art=mode>=4?&covenants_art_rooms[c]:0;
  for(i=0;i<6;i++)enemy(i,12+(int)i*5,-8+(int)i*3,0);
  for(i=0;i<8;i++)target(i,8+(int)i*4,(int)(i%3)*8-8,3);
  if(mode==1||mode==2){wall(111,94,1,12);wall(92,80,12,1);}
  if(mode==3)for(i=0;i<48;i++)wall(76+(int)(i%8)*7,78+(int)(i/8)*7,2,2);
  if(mode>=4){room=70+(int)c;px=practice_origins[c][0];py=practice_origins[c][1];face=1;field_count=0;
   for(i=0;i<2;i++)if(practice_targets[c][i][2]){targets[field_count][0]=practice_targets[c][i][0];targets[field_count][1]=practice_targets[c][i][1];targets[field_count++][2]=practice_targets[c][i][2];}}
  t=now();assert(covenants_power(commands[c]));bench_timings[mode][c][0]=now()-t;
  for(n=0;n<lifetime[c];n++){
   if(n==18){revision++;covenants_powers_geometry_changed();}
   solid_calls=rays=0;t=now();covenants_powers_tick();elapsed=now()-t;
   if(n==18)bench_timings[mode][c][3]=elapsed;
   if(elapsed>bench_timings[mode][c][1])bench_timings[mode][c][1]=elapsed;
   if(solid_calls>bench_counts[mode][c][0])bench_counts[mode][c][0]=solid_calls;
   if(rays>bench_counts[mode][c][1])bench_counts[mode][c][1]=rays;
   draws=0;t=now();covenants_powers_draw();elapsed=now()-t;
   if(elapsed>bench_timings[mode][c][2])bench_timings[mode][c][2]=elapsed;
   if(draws>bench_counts[mode][c][2])bench_counts[mode][c][2]=draws;
   assert(!covenants_power_time||covenants_powers_busy());
   if(ability_cd)ability_cd--;
  }
 }
 bench_completed=1;while(1){}return 0;
}
'''
(OUT / 'bench_main.c').write_text(prelude + harness + main)
sources = [str(OUT / 'bench_main.c'), str(args.power_source.resolve()), 'src/covenants_power_art.c', 'src/covenants_art.c',
           'src/creatures.c', 'src/creature_data.c', 'src/gear_runtime.c',
           'src/combat_rules.c', 'src/north_art.c', 'src/south_art.c']
flags = ['-mcpu=arm7tdmi', '-mthumb-interwork', '-mthumb', '-O2', '-std=c99',
         '-ffreestanding', '-fno-builtin', '-fno-strict-aliasing', '-fomit-frame-pointer',
         '-Wall', '-Wextra', '-Werror', '-Wno-unused-function', '-Wno-unused-const-variable',
         '-Wno-misleading-indentation', '-ffunction-sections', '-fdata-sections', '-Isrc']
objects = []
for source in sources:
    obj = OUT / (Path(source).stem + '.o')
    run([str(arm), *flags, '-c', source, '-o', str(obj)])
    objects.append(str(obj))
startup = OUT / 'startup.o'
run([str(arm), '-mcpu=arm7tdmi', '-mthumb-interwork', '-marm', '-x', 'assembler-with-cpp',
     '-c', 'src/startup.s', '-o', str(startup)])
elf = OUT / 'bench.elf'
rom = OUT / 'bench.gba'
run([str(arm), '-mcpu=arm7tdmi', '-mthumb-interwork', '-mthumb', '-nostdlib',
     '-Wl,--gc-sections,-T,linker.ld', str(startup), *objects, '-lgcc', '-o', str(elf)])
run([prefix + 'objcopy', '-O', 'binary', str(elf), str(rom)])
raw = rom.read_bytes()
run(['python3', 'tools/fix_header.py', str(rom)])
assert raw[192:] == rom.read_bytes()[192:]

def scoped_objects(path, filename):
    raw = path.read_bytes()
    assert raw[:6] == b'\x7fELF\x01\x01'
    header = struct.unpack_from('<16sHHIIIIIHHHHHH', raw)
    assert header[2] == 40
    sections = [struct.unpack_from('<IIIIIIIIII', raw, header[6] + i*header[11]) for i in range(header[12])]
    result = {}
    for section in sections:
        if section[1] != 2:
            continue
        strings = sections[section[6]]
        strings = raw[strings[4]:strings[4] + strings[5]]
        current = None
        for offset in range(section[4], section[4] + section[5], section[9]):
            name, address, size, info, _, _ = struct.unpack_from('<IIIBBH', raw, offset)
            name = strings[name:].split(b'\0', 1)[0].decode()
            if info & 15 == 4:
                current = name
            if current == filename and info >> 4 == 0 and info & 15 == 1:
                assert name not in result
                result[name] = {'address': address, 'size': size}
    return result

symbols = scoped_objects(elf, 'bench_main.c')
for name, size in [('bench_completed', 4), ('bench_fault_line', 4), ('bench_timings', 768), ('bench_counts', 576)]:
    assert symbols[name]['size'] == size
spec = importlib.util.spec_from_file_location('mgba_runner', args.mgba_tools / 'mgba_runner.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
with module.Emulator(rom) as emu:
    for _ in range(500):
        emu.frames(10)
        if emu.read(symbols['bench_completed']['address']):
            break
    assert emu.read(symbols['bench_completed']['address']) == 1, ('benchmark fault or timeout', emu.read(symbols['bench_fault_line']['address']))
    timings = [[[emu.read(symbols['bench_timings']['address'] + ((mode*8+c)*4+n)*4)
                 for n in range(4)] for c in range(8)] for mode in range(6)]
    counts = [[[emu.read(symbols['bench_counts']['address'] + ((mode*8+c)*3+n)*4)
                for n in range(3)] for c in range(8)] for mode in range(6)]
names = ['open_exact', 'near_wall_exact', 'near_wall_synthetic_ray_fallback', 'dense48_exact', 'authored_practice_static_exact', 'authored_practice_static_ray_fallback']
commands = [12] + list(range(122, 129))
report = {'kind': 'isolated actual ARM7TDMI cycles; synthetic scenery and OBJ callbacks',
          'waitcnt': '0x4317', 'clock_hz': 16777216, 'frame_cycles': 280896,
          'cycle_columns': ['cast', 'max_tick', 'max_draw', 'geometry_refresh_tick'],
          'count_columns': ['max_tick_point_probes', 'max_tick_fallback_rays', 'max_draw_objects'],
          'scenarios': {name: {str(command): {'cycles': timings[mode][c], 'counts': counts[mode][c]}
                              for c, command in enumerate(commands)} for mode, name in enumerate(names)},
          'rom_sha256': hashlib.sha256(rom.read_bytes()).hexdigest(),
          'elf_sha256': hashlib.sha256(elf.read_bytes()).hexdigest(),
          'elf_symbol_scope': 'STT_FILE bench_main.c with exact object size checks',
          'elf_rom_matched_bytes': len(raw) - 192,
          'source_sha256': {s: hashlib.sha256((ROOT / s).read_bytes()).hexdigest() for s in sources[1:]},
          'limitation': 'No actual room callback, full-game loop, OAM/cache-pressure, controller or native frame-budget guarantee'}
(OUT / 'arm-timing.json').write_text(json.dumps(report, indent=2) + '\n')
for mode, name in enumerate(names):
    print(name, 'max cast/tick/draw cycles:', [max(row[n] for row in timings[mode]) for n in range(4)])
