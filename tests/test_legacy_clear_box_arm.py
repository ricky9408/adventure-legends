#!/usr/bin/env python3
"""Compile-only ROM/stack audit; this deliberately does not claim GBA pacing."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
from test_legacy_clear_box import ROOT, OUT, PIN, current_pins


def main():
    assert current_pins() == json.loads(PIN.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    prefix = os.environ.get('ARM_PREFIX')
    if not prefix:
        bundled = ROOT / 'tools/sysroot/usr/bin/arm-none-eabi-gcc'
        prefix = str(bundled)[:-3] if bundled.exists() else 'arm-none-eabi-'
    headers = ('asset_collisions.h', 'world.h', 'campaign_rules.h',
               'progression.h', 'trials.h', 'region_art.h', 'region_game.h',
               'regional_quests.h', 'north_art.h', 'south_art.h')
    source = ''.join('#include "' + h + '"\n' for h in headers)
    source += '''#define COLD __attribute__((section(".text.rom"),long_call,noinline))
extern volatile int room,bridge_open,torches;
unsigned progress_bits(void);
#include "legacy_clear_box.inc"
'''
    unit, obj = OUT / 'arm-probe.c', OUT / 'arm-probe.o'
    unit.write_text(source)
    flags = ['-mcpu=arm7tdmi', '-mthumb-interwork', '-mthumb', '-O2', '-g',
             '-std=c99', '-ffreestanding', '-fno-builtin',
             '-fno-strict-aliasing', '-fomit-frame-pointer', '-Wall',
             '-Wextra', '-Werror', '-fstack-usage', '-Isrc']
    subprocess.run([prefix + 'gcc', *flags, '-c', str(unit), '-o', str(obj)],
                   cwd=ROOT, check=True)
    sections_text = subprocess.check_output([prefix + 'objdump', '-h', str(obj)], text=True)
    sections = {name: int(size, 16) for name, size in re.findall(
        r'^\s*\d+\s+(\S+)\s+([0-9a-fA-F]+)\s', sections_text, re.M)}
    assert sections['.text'] == sections['.data'] == sections['.bss'] == 0
    assert 0 < sections['.text.rom'] < 4096
    symbols = subprocess.check_output([prefix + 'nm', '-S', str(obj)], text=True)
    assert not re.search(r'^\S+\s+\S+\s+[bBdD]\s+', symbols, re.M)
    assert 'legacy_game_clear_box' in symbols and 'legacy_rows_clear' in symbols
    stack = {}
    for line in (OUT / 'arm-probe.su').read_text().splitlines():
        identity, size, kind = line.split('\t')
        assert kind == 'static'
        stack[identity.rsplit(':', 1)[-1]] = int(size)
    assert set(stack) == {'legacy_game_clear_box', 'legacy_rows_clear'}
    assert sum(stack.values()) <= 128
    report = {
        'scope': 'isolated ARM7TDMI compile audit; not native pacing acceptance',
        'compiler': subprocess.check_output([prefix + 'gcc', '--version'], text=True).splitlines()[0],
        'code_rom_bytes': sections['.text.rom'], 'iwram_code_bytes': sections['.text'],
        'new_writable_data_bytes': sections['.data'] + sections['.bss'],
        'stack_bytes': stack, 'maximum_nested_certificate_stack_bytes': sum(stack.values()),
        'note': 'Probe .rodata is the already-existing asset_collisions.h; game.c does not duplicate it',
        'certificate_sha256': hashlib.sha256((ROOT / 'src/legacy_clear_box.inc').read_bytes()).hexdigest(),
    }
    (OUT / 'arm-report.json').write_text(json.dumps(report, indent=2) + '\n')
    (OUT / 'arm-sections.txt').write_text(sections_text)
    print(json.dumps(report, indent=2))


if __name__ == '__main__':
    main()
