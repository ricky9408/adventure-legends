#!/usr/bin/env python3
"""Synthetic exhaustive/wide-gap storage scan equivalence on actual C code."""
from pathlib import Path
import os
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
C_SOURCE = r'''
#include <assert.h>
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include "quickparty.c"
Save5State adventure_save;
unsigned progression_form_spirit(unsigned id) { return id == 1 ? 0 : PROGRESSION_SPIRIT_COUNT; }
static unsigned rng = 0x31415926;
static unsigned random_u32(void) { rng ^= rng << 13; rng ^= rng >> 17; rng ^= rng << 5; return rng; }
static int reference(int start, int delta) {
    int i = (unsigned)start < 160 ? start : 160;
    unsigned n;
    for (n = 0; n < 161; ++n) {
        i = (i + delta + 161) % 161;
        if (i == 160 || ((adventure_save.roster.instances[i].flags & CREATURE_OCCUPIED) &&
                        progression_form_spirit(adventure_save.roster.instances[i].form_id) < PROGRESSION_SPIRIT_COUNT))
            return i == 160 ? EMPTY : i;
    }
    assert(0); return -1;
}
int main(void) {
    unsigned pattern, slot, count = 0;
    int start, delta;
    CreatureRoster before;
    for (pattern = 0; pattern < 512; ++pattern) {
        memset(&adventure_save, 0, sizeof adventure_save);
        for (slot = 0; slot < 160; ++slot) {
            unsigned occupied = pattern < 160 ? slot == pattern :
                                pattern == 160 ? slot < 21 :
                                pattern == 161 ? 0 : pattern == 162 ? 1 : random_u32() & 1;
            adventure_save.roster.instances[slot].flags = occupied ? CREATURE_OCCUPIED : 0;
            adventure_save.roster.instances[slot].form_id = pattern < 163 || (random_u32() & 3) ? 1 : 0;
        }
        before = adventure_save.roster;
        for (start = -2; start <= 256; ++start) for (delta = -1; delta <= 1; delta += 2) {
            int expected = reference(start, delta);
            quickparty_menu_candidate = start; quickparty_revision = 100; menu_notice = 1;
            menu_move(delta);
            assert(quickparty_menu_candidate == expected);
            assert(quickparty_revision == 101 && menu_notice == 0);
            assert(!memcmp(&before, &adventure_save.roster, sizeof before));
            ++count;
        }
    }
    printf("storage scan: %u reference-equivalent cases; roster unchanged\n", count);
    return 0;
}
'''

def main():
    with tempfile.TemporaryDirectory(prefix='southern-party-scan-') as temp:
        source = Path(temp) / 'scan.c'
        source.write_text(C_SOURCE)
        for name, flags in [('strict', []), ('sanitized', ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]:
            target = Path(temp) / name
            subprocess.run(['cc', '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror',
                            '-Wno-misleading-indentation', '-ffunction-sections', '-fdata-sections',
                            '-Wl,--gc-sections', '-I' + str(ROOT / 'src'), *flags,
                            str(source), '-o', str(target)], check=True)
            subprocess.run([str(target)], env=dict(os.environ, ASAN_OPTIONS='detect_leaks=0'), check=True)

if __name__ == '__main__':
    main()
