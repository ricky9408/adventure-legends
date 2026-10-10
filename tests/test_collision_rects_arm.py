#!/usr/bin/env python3
"""Compile-only ARM7TDMI ROM/stack/writable-data audit of the exact snapshot."""
import json
import os
import re
import subprocess
from test_collision_rects import ROOT, OUT, PIN, current_pins, digest


def main():
    assert current_pins() == json.loads(PIN.read_text()), 'Production source pins require review'
    OUT.mkdir(parents=True, exist_ok=True)
    prefix = os.environ.get('ARM_PREFIX')
    if not prefix:
        bundled = ROOT / 'tools/sysroot/usr/bin/arm-none-eabi-gcc'
        prefix = str(bundled)[:-3] if bundled.exists() else 'arm-none-eabi-'
    headers = ('asset_collisions.h', 'world.h', 'campaign_rules.h', 'progression.h',
               'trials.h', 'region_art.h', 'region_game.h', 'regional_quests.h',
               'magma_art.h', 'magma_game.h', 'north_art.h', 'south_art.h', 'return_art.h', 'return_game.h')
    source = ''.join('#include "' + h + '"\n' for h in headers)
    source += '''#define COLD __attribute__((section(".text.rom"),long_call,noinline))
extern volatile int room,bridge_open,torches;
unsigned progress_bits(void);
#include "collision_rects.inc"
'''
    unit, obj = OUT / 'arm-probe.c', OUT / 'arm-probe.o'
    unit.write_text(source)
    flags = ['-mcpu=arm7tdmi', '-mthumb-interwork', '-mthumb', '-O2', '-g',
             '-std=c99', '-ffreestanding', '-fno-builtin', '-fno-strict-aliasing',
             '-fomit-frame-pointer', '-Wall', '-Wextra', '-Werror', '-fstack-usage', '-Isrc']
    subprocess.run([prefix + 'gcc', *flags, '-c', str(unit), '-o', str(obj)], cwd=ROOT, check=True)
    text = subprocess.check_output([prefix + 'objdump', '-h', str(obj)], text=True)
    sections = {name: int(size, 16) for name, size in re.findall(r'^\s*\d+\s+(\S+)\s+([0-9a-fA-F]+)\s', text, re.M)}
    assert sections['.text'] == sections['.data'] == sections['.bss'] == 0
    assert 0 < sections['.text.rom'] <= 6144
    symbols = subprocess.check_output([prefix + 'nm', '-S', str(obj)], text=True)
    assert not re.search(r'^\S+\s+\S+\s+[bBdD]\s+', symbols, re.M)
    stack = {}
    for line in (OUT / 'arm-probe.su').read_text().splitlines():
        identity, size, kind = line.split('\t')
        assert kind == 'static'
        stack[identity.rsplit(':', 1)[-1]] = int(size)
    assert set(stack) == {'game_collision_rects', 'collision_rect_add', 'collision_rect_rows'}
    # Snapshot-owned chain, including rows -> add. External pre-existing Magma
    # predicates are accounted separately, not silently treated as zero stack.
    internal_max = sum(stack.values())
    assert internal_max <= 256
    # Compile actual production Magma with identical flags for the external
    # calls used by game_collision_rects. It is evidence only, not new runtime RAM.
    magma_obj = OUT / 'arm-magma.o'
    subprocess.run([prefix + 'gcc', *flags, '-c', 'src/magma_game.c', '-o', str(magma_obj)], cwd=ROOT, check=True)
    magma_stack = {}
    for line in (OUT / 'arm-magma.su').read_text().splitlines():
        identity, size, kind = line.split('\t')
        name = identity.rsplit(':', 1)[-1]
        if name in ('magma_game_collision_inputs', 'magma_puzzle_count', 'magma_puzzle_position', 'trial_brick'):
            assert kind == 'static'
            magma_stack[name] = int(size)
    return_obj = OUT / 'arm-return.o'
    subprocess.run([prefix + 'gcc', *flags, '-c', 'src/return_game.c', '-o', str(return_obj)], cwd=ROOT, check=True)
    return_stack = {}
    for line in (OUT / 'arm-return.su').read_text().splitlines():
        identity, size, kind = line.split('\t')
        name = identity.rsplit(':', 1)[-1]
        if name in ('return_game_collision_rects', 'dynamic_rects', 'return_game_is_room'):
            assert kind == 'static'
            return_stack[name] = int(size)
    return_symbols = subprocess.check_output([prefix + 'objdump', '-t', str(return_obj)], text=True)
    wrapper = re.search(r'^\S+\s+g\s+F\s+(\S+)\s+([0-9a-fA-F]+)\s+return_game_collision_rects$', return_symbols, re.M)
    assert wrapper and wrapper[1] == '.text.rom'
    wrapper_bytes = int(wrapper[2], 16)
    assert 0 < wrapper_bytes <= 512
    conservative_max = max(internal_max, stack['game_collision_rects'] + sum(magma_stack.values()),
                           stack['game_collision_rects'] + sum(return_stack.values()))
    assert conservative_max <= 256
    report = {'scope': 'isolated ARM7TDMI compile audit, not native pacing or whole-ROM budget acceptance',
              'compiler': subprocess.check_output([prefix + 'gcc', '--version'], text=True).splitlines()[0],
              'snapshot_rom_bytes': sections['.text.rom'], 'new_iwram_code_bytes': sections['.text'],
              'new_ewram_or_writable_data_bytes': sections['.data'] + sections['.bss'],
              'snapshot_stack_bytes': stack, 'snapshot_owned_nested_stack_bytes': internal_max,
              'existing_magma_callee_stack_bytes': magma_stack,
              'return_wrapper_and_existing_callee_stack_bytes': return_stack,
              'return_wrapper_rom_bytes': wrapper_bytes,
              'total_new_helper_rom_bytes': sections['.text.rom'] + wrapper_bytes,
              'conservative_total_nested_stack_bytes': conservative_max,
              'existing_header_rodata_bytes': sections.get('.rodata', 0),
              'note': 'Probe .rodata is existing asset_collisions.h data; the real inclusion in game.c reuses it',
              'snapshot_sha256': digest((ROOT / 'src/collision_rects.inc').read_bytes()),
              'api_header_sha256': digest((ROOT / 'src/collision_rects.h').read_bytes())}
    (OUT / 'arm-report.json').write_text(json.dumps(report, indent=2) + '\n')
    (OUT / 'arm-sections.txt').write_text(text)
    (OUT / 'arm-symbols.txt').write_text(symbols)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
