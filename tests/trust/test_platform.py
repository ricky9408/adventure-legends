import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from arm_toolchain import resolve_arm_tools


PERIODIC_CASES = r'''
#include <limits.h>
#include <stdio.h>
#include <string.h>
#include "music_copy.h"

int main(void) {
    signed char track[67], original[67], output[1028];
    unsigned cases = 0;
    for (unsigned length = 1; length <= 65; length++) {
        for (unsigned i = 0; i < sizeof(track); i++) track[i] = (signed char)(i * 37u + length);
        memcpy(original, track, sizeof(track));
        for (unsigned cursor = 0; cursor < length; cursor++) {
            for (unsigned count = 0; count <= 1025; count += 25) {
                memset(output, 0x5a, sizeof(output));
                volatile unsigned loops = UINT_MAX - 1u;
                unsigned actual = music_copy_periodic(output + 1, track, length, cursor, count, &loops);
                if (actual != (cursor + count) % length) return 1;
                if (loops != UINT_MAX - 1u + (cursor + count) / length) return 2;
                if (output[0] != 0x5a || output[count + 1] != 0x5a) return 3;
                for (unsigned i = 0; i < count; i++)
                    if (output[i + 1] != original[(cursor + i) % length]) return 4;
                if (memcmp(track, original, sizeof(track))) return 5;
                cases++;
            }
        }
    }
    printf("%u periodic stream cases passed\n", cases);
    return 0;
}
'''


class PlatformContracts(unittest.TestCase):
    def periodic(self, header):
        with tempfile.TemporaryDirectory(prefix='trust-periodic-') as temporary:
            directory = Path(temporary)
            (directory / 'music_copy.h').write_text(header)
            source = directory / 'cases.c'
            source.write_text(PERIODIC_CASES)
            binary = directory / 'cases'
            subprocess.run([
                os.environ.get('HOST_CC', 'cc'), '-std=c99', '-O1', '-Wall', '-Wextra', '-Werror',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer',
                str(source), '-o', str(binary),
            ], check=True, capture_output=True, text=True)
            return subprocess.run([str(binary)], capture_output=True, text=True, timeout=20,
                                  env={**os.environ, 'ASAN_OPTIONS': 'detect_leaks=0:halt_on_error=1',
                                       'UBSAN_OPTIONS': 'halt_on_error=1'})

    def test_pcm_periods_preserve_every_sample_and_destination_bounds(self):
        result = self.periodic((ROOT / 'src/music_copy.h').read_text())
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('90090 periodic stream cases passed', result.stdout)

    def test_pcm_oracle_rejects_a_broken_wrap_boundary(self):
        header = (ROOT / 'src/music_copy.h').read_text()
        before = 'if(cursor==length)'
        self.assertEqual(header.count(before), 1)
        result = self.periodic(header.replace(before, 'if(cursor>=length-1)'))
        self.assertNotEqual(result.returncode, 0)

    def test_pcm_oracle_rejects_repeated_first_samples(self):
        header = (ROOT / 'src/music_copy.h').read_text()
        before = 'dst[i]=src[cursor+i]'
        self.assertEqual(header.count(before), 1)
        result = self.periodic(header.replace(before, 'dst[i]=src[0]'))
        self.assertNotEqual(result.returncode, 0)

    def link(self, iwram_size, ewram_size=0, rom_size=0):
        compiler = resolve_arm_tools('gcc')['gcc']
        with tempfile.TemporaryDirectory(prefix='trust-link-') as temporary:
            directory = Path(temporary)
            source = directory / 'fixture.s'
            source.write_text(f'''.syntax unified
.cpu arm7tdmi
.arm
.section .text.startup,"ax",%progbits
.global _start
_start: b _start
.section .iwram.text.fixture,"ax",%progbits
.space {iwram_size}
.section .bss.fixture,"aw",%nobits
.space {ewram_size}
.section .rodata.fixture,"a",%progbits
.space {rom_size}
''')
            return subprocess.run([
                compiler, '-mcpu=arm7tdmi', '-nostdlib', '-Wl,-T,' + str(ROOT / 'linker.ld'),
                str(source), '-o', str(directory / 'fixture.elf'),
            ], capture_output=True, text=True, timeout=30)

    def test_linker_accepts_memory_exactly_at_declared_bounds(self):
        result = self.link(0x7000, 0x40000)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_linker_rejects_code_overlapping_the_stack_reserve(self):
        result = self.link(0x7004)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('reserved stack', result.stderr)

    def test_linker_rejects_state_larger_than_ewram(self):
        result = self.link(0, 0x40004)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('EWRAM', result.stderr)

    def test_linker_rejects_a_cartridge_over_32_mib(self):
        result = self.link(0, 0, 0x2000000)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn('ROM', result.stderr)


if __name__ == '__main__':
    unittest.main()
