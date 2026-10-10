#!/usr/bin/env python3
"""Isolated real-DMA mGBA pixel/timing gate for the current production box.

Builds a tiny separate cartridge, never the game ROM. The production box stays
in ROM, and the historical five-rectangle reference plus rect/pix stay in IWRAM.
Run without arguments for a fresh timestamped build directory, or pass --output
with a nonexistent/empty directory. Requires the restored ARM toolchain and mGBA.
"""
from __future__ import annotations
import argparse
import ctypes as C
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import subprocess

ROOT = Path(__file__).resolve().parents[1]
CASES = [
    ('common_party_gear', 8, 31, 224, 123), ('map_growth', 8, 31, 224, 122),
    ('quest', 8, 31, 224, 119), ('full_card_216', 12, 42, 216, 105),
    ('full_card_200', 20, 38, 200, 114), ('unaligned_full_card', 26, 29, 188, 131),
    ('save_badge', 136, 3, 64, 17), ('dialog', 5, 99, 230, 56),
    ('new_game_confirmation', 8, 50, 224, 76), ('title_choices', 43, 112, 154, 36),
    ('death', 22, 60, 196, 57), ('ending', 17, 40, 206, 103),
    ('small_aligned', 8, 20, 24, 12), ('small_odd', 9, 21, 15, 9),
    ('one_pixel', 5, 5, 1, 1), ('short_height', 8, 40, 224, 2),
    ('minimal_fast', 8, 40, 32, 3), ('clipped', -4, -3, 224, 123),
    ('outside', 242, 163, 24, 12), ('full_screen', 0, 0, 240, 160),
]
MODES = ('forced_blank_line_0', 'mode4_line_0', 'mode4_line_80', 'mode4_vblank_160')
FUNCTIONS = ('reference_iwram', 'production_rom', 'empty_iwram')
REPEATS = 9
REFERENCE = '''void reference_box(int x,int y,int w,int h){rect(x,y,w,h,UI_BG);rect(x,y,w,1,UI_BORDER);rect(x,y+h-1,w,1,UI_BORDER);rect(x,y,1,h,UI_BORDER);rect(x+w-1,y,1,h,UI_BORDER);}\n'''
HEAD = '''/* Isolated test cartridge, not a gameplay build. */
#define COLD __attribute__((section(".text.rom"),long_call,noinline))
typedef unsigned char u8;typedef unsigned short u16;typedef unsigned int u32;
#define REG16(a) (*(volatile u16*)(a))
#define REG32(a) (*(volatile u32*)(a))
u16 *screen;int world_mask_active,world_mask_left,world_mask_right,world_mask_top,world_mask_bottom;
'''
TAIL = r'''
volatile unsigned bench_status,bench_progress;
volatile unsigned native_mismatches[CASES][2];
volatile unsigned samples[CASES][2][4][REPEATS][3];
volatile unsigned start_lines[CASES][2][4][REPEATS][3];
typedef void (*BoxFn)(int,int,int,int);
__attribute__((noinline)) void empty_box(int x,int y,int w,int h){__asm__ volatile("":::"memory");(void)x;(void)y;(void)w;(void)h;}
BoxFn volatile functions[3]={reference_box,production_box,empty_box};
void sync_line(unsigned line){while(REG16(0x04000006)!=227){}while(REG16(0x04000006)==227){}while(REG16(0x04000006)<line){}}
void fill_pages(void){unsigned n;for(n=0;n<9600;n++){((volatile u32*)0x06000000)[n]=n*1664525u+1013904223u;((volatile u32*)0x0600A000)[n]=n*1664525u+1013904223u;}}
int main(void){unsigned i,c,m,r,f,n,start,end,line;int x,y,w,h;BoxFn fn;
 REG16(0x04000208)=0;REG16(0x04000000)=0x80;REG16(0x04000204)=0x4317;
 REG16(0x04000020)=256;REG16(0x04000026)=256;REG16(0x04000022)=0;REG16(0x04000024)=0;REG32(0x04000028)=0;REG32(0x0400002C)=0;REG16(0x0400000C)=3;
 REG16(0x0400010C)=0;REG16(0x0400010E)=0x84;REG16(0x04000108)=0;REG16(0x0400010A)=0x80;
 world_mask_left=8;world_mask_right=232;world_mask_top=31;world_mask_bottom=153;
 bench_status=1;
 for(i=0;i<CASES;i++)for(c=0;c<2;c++){
   world_mask_active=c;x=cases[i][0];y=cases[i][1];w=cases[i][2];h=cases[i][3];
   REG16(0x04000000)=0x80;fill_pages();screen=(u16*)0x06000000;functions[0](x,y,w,h);screen=(u16*)0x0600A000;functions[1](x,y,w,h);
   for(n=0;n<9600;n++)if(((volatile u32*)0x06000000)[n]!=((volatile u32*)0x0600A000)[n])native_mismatches[i][c]++;
   for(m=0;m<4;m++){
     REG16(0x04000000)=m?0x1444:0x84;line=m==2?80:m==3?160:0;
     for(r=0;r<REPEATS;r++)for(n=0;n<3;n++){
       f=r&1?2-n:n;fn=functions[f];sync_line(line);
       start_lines[i][c][m][r][f]=REG16(0x04000006);
       start=cycle_now();fn(x,y,w,h);end=cycle_now();
       samples[i][c][m][r][f]=end-start;bench_progress++;
     }
   }
 }
 bench_status=2;while(1){}return 0;
}
'''


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def extract_function(text, name):
    masked = re.sub(r'/\*.*?\*/|//[^\n]*|"(?:\\.|[^"\\])*"',
                    lambda m: ' ' * len(m[0]), text, flags=re.S)
    match = re.search(r'^(?:static\s+)?(?:COLD\s+)?(?:unsigned(?:\s+int)?|int|void)\s+'
                      + name + r'\([^;{}]*\)\s*\{', masked, re.M)
    if not match:
        raise ValueError('Cannot extract production function: ' + name)
    end = masked.index('{', match.start()) + 1
    depth = 1
    while depth:
        depth += (masked[end] == '{') - (masked[end] == '}')
        end += 1
    return text[match.start():end] + '\n'


def color_constant(text, name):
    for _ in range(8):
        match = re.search(r'^#define\s+' + name + r'\s+(\w+)\s*$', text, re.M)
        if not match:
            raise ValueError('Cannot resolve color macro: ' + name)
        name = match[1]
        try:
            value = int(name, 0)
            assert 0 <= value < 256
            return value
        except ValueError:
            pass
    raise ValueError('Recursive color macro')


def build(output, arm_prefix, host_cc):
    inputs = output / 'inputs'
    sources = ('src/game.c', 'src/assets.h', 'src/startup.s', 'linker.ld',
               'tests/player_feedback_mgba_bridge.c', 'tools/mgba_bridge.c',
               'tools/fix_header.py', 'tests/test_player_feedback_box_native.py')
    for relative in sources:
        target = inputs / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    game = (inputs / 'src/game.c').read_text()
    colors = game + '\n' + (inputs / 'src/assets.h').read_text()
    production = extract_function(game, 'box').replace('void box(', 'void production_box(', 1)
    if not production.startswith('COLD '):
        raise AssertionError('Production box must retain its COLD ROM placement')
    source = HEAD + ''.join('#define ' + name + ' ' + str(color_constant(colors, name)) + '\n'
                           for name in ('UI_BG', 'UI_BORDER'))
    source += ''.join(extract_function(game, name) for name in ('game_world_rect_hidden', 'pix', 'rect'))
    source += REFERENCE + production + extract_function(game, 'cycle_now')
    source += '#define CASES ' + str(len(CASES)) + '\n#define REPEATS ' + str(REPEATS) + '\n'
    source += 'const int cases[CASES][4]={' + ','.join('{' + ','.join(map(str, case[1:])) + '}' for case in CASES) + '};\n'
    (output / 'game.c').write_text(source + TAIL)
    cpu = ['-mcpu=arm7tdmi', '-mthumb-interwork']
    flags = [*cpu, '-mthumb', '-O2', '-g', '-std=c99', '-ffreestanding', '-fno-builtin',
             '-fno-strict-aliasing', '-fomit-frame-pointer', '-Wall', '-Wextra']
    sysroot = ROOT / 'tools/sysroot/usr'
    library = sysroot / 'lib/x86_64-linux-gnu'
    commands = [
        [arm_prefix + 'gcc', *flags, '-c', str(output / 'game.c'), '-o', str(output / 'game.o')],
        [arm_prefix + 'gcc', *cpu, '-marm', '-g', '-x', 'assembler-with-cpp', '-c', str(inputs / 'src/startup.s'), '-o', str(output / 'startup.o')],
        [arm_prefix + 'gcc', *cpu, '-mthumb', '-nostdlib', '-Wl,-T,' + str(inputs / 'linker.ld') + ',-Map,' + str(output / 'benchmark.map'), str(output / 'startup.o'), str(output / 'game.o'), '-lgcc', '-o', str(output / 'benchmark.elf')],
        [arm_prefix + 'objcopy', '-O', 'binary', str(output / 'benchmark.elf'), str(output / 'benchmark.gba')],
        [os.sys.executable, str(inputs / 'tools/fix_header.py'), str(output / 'benchmark.gba')],
        [host_cc, '-std=c11', '-D_GNU_SOURCE', '-O2', '-fPIC', '-shared', str(inputs / 'tests/player_feedback_mgba_bridge.c'), '-I' + str(sysroot / 'include'), '-L' + str(library), '-Wl,-rpath,' + str(library), '-o', str(output / 'bridge.so'), '-lmgba'],
    ]
    for command in commands:
        subprocess.run(command, check=True)
    for tool, args, name in [('nm', ['-n', '-S'], 'benchmark.sym'), ('objdump', ['-d'], 'benchmark.disassembly.txt'), ('objdump', ['-h'], 'benchmark.sections.txt')]:
        command = [arm_prefix + tool, *args, str(output / 'benchmark.elf')]
        commands.append(command)
        (output / name).write_text(subprocess.check_output(command, text=True))
    compiler = Path(shutil.which(arm_prefix + 'gcc') or arm_prefix + 'gcc').resolve()
    manifest = {'created_at': datetime.now(timezone.utc).isoformat(), 'commands': commands,
                'compiler': subprocess.check_output([str(compiler), '--version'], text=True).splitlines()[0],
                'compiler_sha256': sha(compiler), 'libmgba_sha256': sha(library / 'libmgba.so'),
                'input_sha256': {relative: sha(inputs / relative) for relative in sources},
                'artifact_sha256': {p.name: sha(p) for p in sorted(output.iterdir()) if p.is_file()}}
    (output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
    return manifest


def run(output, manifest):
    symbols = {p[-1]: int(p[0], 16) for line in (output / 'benchmark.sym').read_text().splitlines()
               if len(p := line.split()) in (3, 4)}
    for name in ('reference_box', 'rect', 'pix', 'cycle_now'):
        assert 0x03000000 <= symbols[name] < 0x03007000, (name, hex(symbols[name]))
    assert 0x08000000 <= symbols['production_box'] < 0x0A000000
    lib = C.CDLL(str(output / 'bridge.so'))
    for name, args, result in [
        ('eb_open', [C.c_char_p], C.c_void_p), ('eb_close', [C.c_void_p], None),
        ('eb_frames', [C.c_void_p, C.c_uint, C.c_uint], None),
        ('eb_read', [C.c_void_p, C.c_uint32, C.c_uint], C.c_uint32),
        ('eb_faults', [C.c_void_p], C.c_uint), ('eb_framecounter', [C.c_void_p], C.c_uint),
    ]:
        fn = getattr(lib, name)
        fn.argtypes, fn.restype = args, result
    emulator = lib.eb_open(str(output / 'benchmark.gba').encode())
    assert emulator, 'mGBA open failed'
    expected = len(CASES) * 2 * len(MODES) * REPEATS * len(FUNCTIONS)
    try:
        def read(address):
            return lib.eb_read(emulator, address, 4)
        # Each synchronized measurement normally takes one frame. This bounds a
        # hang or pathological raster regression without touching emulator state.
        for _ in range((expected * 2 + 600) // 100):
            lib.eb_frames(emulator, 100, 0)
            if read(symbols['bench_status']) == 2:
                break
        completed = read(symbols['bench_status']) == 2 and read(symbols['bench_progress']) == expected
        faults = lib.eb_faults(emulator)
        mismatches = [read(symbols['native_mismatches'] + i * 4) for i in range(len(CASES) * 2)]
        rows, raw, offset, line_errors = [], [], 0, 0
        for case in CASES:
            for cover in (0, 1):
                for mode_index, mode in enumerate(MODES):
                    values, lines = [[], [], []], [[], [], []]
                    expected_line = (0, 0, 80, 160)[mode_index]
                    for repeat in range(REPEATS):
                        for index, name in enumerate(FUNCTIONS):
                            cycles = read(symbols['samples'] + offset * 4)
                            line = read(symbols['start_lines'] + offset * 4)
                            offset += 1
                            values[index].append(cycles)
                            lines[index].append(line)
                            line_errors += line != expected_line
                            raw.append({'case': case[0], 'world_mask_active': cover, 'mode': mode,
                                        'repeat': repeat, 'function': name, 'cycles': cycles, 'line': line})
                    stats = {name: {'min': min(v), 'median': statistics.median(v), 'max': max(v)}
                             for name, v in zip(FUNCTIONS, values)}
                    baseline, current = statistics.median(values[0]), statistics.median(values[1])
                    rows.append({'case': case[0], 'box': case[1:], 'world_mask_active': cover,
                                 'mode': mode, 'statistics': stats,
                                 'start_lines': {name: sorted(set(v)) for name, v in zip(FUNCTIONS, lines)},
                                 'cycles_saved': baseline - current,
                                 'percent_saved': 100 * (baseline - current) / baseline if baseline else None})
        success = completed and not faults and not any(mismatches) and not line_errors
        report = {'status': 'PASS' if success else 'FAIL', 'completed': completed,
                  'completed_measurements': read(symbols['bench_progress']), 'expected_measurements': expected,
                  'native_full_frame_comparisons': len(mismatches), 'native_word_mismatches': sum(mismatches),
                  'native_mismatch_words_by_case_cover': mismatches, 'mGBA_faults': faults,
                  'start_line_errors': line_errors, 'external_state_writes': 0,
                  'hardware_frames': lib.eb_framecounter(emulator), 'samples_per_entry': REPEATS,
                  'placements': {name: hex(symbols[name]) for name in ('reference_box', 'rect', 'pix', 'production_box', 'game_world_rect_hidden', 'cycle_now', '__iwram_end')},
                  'hashes': {'rom_sha256': sha(output / 'benchmark.gba'), 'elf_sha256': sha(output / 'benchmark.elf'),
                             'symbols_sha256': sha(output / 'benchmark.sym'), 'bridge_sha256': sha(output / 'bridge.so'),
                             'libmgba_sha256': manifest['libmgba_sha256'], 'compiler_sha256': manifest['compiler_sha256'],
                             'production_source_sha256': manifest['input_sha256']['src/game.c']},
                  'timing': 'Raw CPU-clock Timer2/Timer3 cycles, including generic call and timer overhead; actual DMA3 to VRAM back page 0x0600A000, WAITCNT 0x4317.',
                  'caveats': ['Isolated mGBA microbenchmark, not physical hardware or gameplay acceptance.',
                              'No music DMA, IRQ, saving, or complete-frame rendering; production code layout differs.',
                              'Empty-call timing is reported without subtraction. Native pixel equality is checked with forced blank; timing spans four display phases.'],
                  'rows': rows}
        (output / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
        (output / 'samples.json').write_text(json.dumps(raw, indent=2) + '\n')
    finally:
        lib.eb_close(emulator)
    for row in report['rows']:
        if not row['world_mask_active'] and row['mode'] == 'mode4_line_0':
            stats = row['statistics']
            print(row['case'], 'reference', stats['reference_iwram'], 'production', stats['production_rom'])
    print(report['status'] + ': ' + str(output / 'report.json'))
    if not success:
        raise SystemExit('Native box gate failed; inspect retained report and cartridge')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--arm-prefix', default=os.environ.get('ARM_PREFIX') or str(ROOT / 'tools/sysroot/usr/bin/arm-none-eabi-'))
    parser.add_argument('--host-cc', default=os.environ.get('HOST_CC', 'cc'))
    args = parser.parse_args()
    output = (args.output or ROOT / ('build/player-feedback-box-native-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))).resolve()
    if output.exists() and any(output.iterdir()):
        raise FileExistsError('Use a fresh output directory; existing evidence is never overwritten: ' + str(output))
    output.mkdir(parents=True, exist_ok=True)
    run(output, build(output, args.arm_prefix, args.host_cc))


if __name__ == '__main__':
    main()
