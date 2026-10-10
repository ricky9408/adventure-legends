#!/usr/bin/env python3
"""Exhaustive revision1..6 creature acceptance against delivered Underwater.

Tables are compared byte-for-byte, not by a digest. This tests all 16-bit masks,
all command bytes at every level 0..51 for all form bytes, and malformed scalar
records. Source archives and every source input are independently SHA-pinned.
"""
import collections
import ctypes as C
import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest

from test_save5 import ROOT, Save, Instance, Roster
from test_return_history_differential import (SOURCE_COMMIT, MANIFEST_SHA,
    build, digest, erase_live_tables, extract_oracle, source_closure, FIXTURES, SOURCES)

V6 = json.loads((ROOT / 'assets/history/creatures-v6.json').read_text())
ROWS = {row['id']: row for row in V6['forms']}

TABLE_HARNESS = r'''
#include <string.h>
void history_command_table(unsigned revision, unsigned form, unsigned char *out) {
    unsigned level, command;
    for (level=0; level<52; ++level) for (command=0; command<256; ++command)
        *out++ = (unsigned char)creatures_command_learned_revision(form, level, command, revision);
}
void history_mask_table(const CreatureInstance *seed, unsigned revision, unsigned char *out) {
    unsigned mask;
    CreatureInstance c, before;
    for (mask=0; mask<65536; ++mask) {
        c=*seed; c.trial_flags=(CreatureU16)mask; before=c;
        *out=(unsigned char)creatures_instance_validate_revision(&c, revision);
        if (memcmp(&c,&before,sizeof c)) *out+=2;
        ++out;
    }
}
void history_instance_byte_table(const CreatureInstance *seed, unsigned revision, unsigned char *out) {
    unsigned byte, value;
    CreatureInstance c, before;
    for (byte=0; byte<sizeof c; ++byte) for (value=0; value<256; ++value) {
        c=*seed; ((unsigned char *)&c)[byte]=(unsigned char)value; before=c;
        *out=(unsigned char)creatures_instance_validate_revision(&c, revision);
        if (memcmp(&c,&before,sizeof c)) *out+=2;
        ++out;
    }
}
'''


def configure(lib):
    signatures = {
        'creatures_form_allowed_revision': [C.c_uint] * 2,
        'creatures_trial_allowed_mask': [C.c_uint] * 2,
        'creatures_family_revision': [C.c_uint] * 2,
        'creatures_legacy_spirit_revision': [C.c_uint] * 2,
        'creatures_command_learned_revision': [C.c_uint] * 4,
        'creatures_instance_validate_revision': [C.POINTER(Instance), C.c_uint],
        'creatures_roster_validate_revision': [C.POINTER(Roster), C.c_uint],
        'creatures_instance_validate': [C.POINTER(Instance)],
        'history_command_table': [C.c_uint, C.c_uint, C.c_void_p],
        'history_mask_table': [C.POINTER(Instance), C.c_uint, C.c_void_p],
        'history_instance_byte_table': [C.POINTER(Instance), C.c_uint, C.c_void_p],
    }
    for name, args in signatures.items():
        getattr(lib, name).argtypes = args
        getattr(lib, name).restype = C.c_uint
    return lib


def instance(row, mask=None):
    c = Instance()
    c.form_id = row['id']; c.flags = 1; c.instance_id = 1
    c.level = 50; c.xp = 470596; c.bond = 100
    c.trial_flags = row['trial_mask'] if mask is None else mask
    c.polarity = row['polarity']; c.equipped[0] = row['learn'][0][1]
    return c


class ReturnHistoricalCore(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='return-history-core-')
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.folder = Path(cls.tmp.name)
        cls.oracle = cls.folder / 'oracle'
        cls.manifest = extract_oracle(cls.oracle)
        cls.old = configure(build(cls.oracle, cls.folder / 'old', extra_harness=TABLE_HARNESS))
        cls.new = configure(build(ROOT, cls.folder / 'new', extra_harness=TABLE_HARNESS))
        cls.erased = configure(build(ROOT, cls.folder / 'erased', erase_live_tables, TABLE_HARNESS))
        cls.counts = collections.Counter()
        assert V6['source_commit'] == SOURCE_COMMIT and len(ROWS) == 89

    @classmethod
    def tearDownClass(cls):
        for row in cls.manifest['files']:
            assert digest((cls.oracle / row['path']).read_bytes()) == row['sha256']
        print(json.dumps({'suite': 'return-history-core', 'checks': dict(cls.counts),
            'oracle_commit': SOURCE_COMMIT, 'oracle_manifest_sha256': MANIFEST_SHA,
            'candidate_source_sha256': cls.new._hashes}, sort_keys=True))

    def same_table(self, method, args, count, label, erased=False):
        old, new = (C.c_ubyte * count)(), (C.c_ubyte * count)()
        getattr(self.old, method)(*args, old)
        getattr(self.erased if erased else self.new, method)(*args, new)
        a, b = bytes(old), bytes(new)
        if a != b:
            mismatch = next(i for i, pair in enumerate(zip(a, b)) if pair[0] != pair[1])
            self.fail(f'{label}: first differing index {mismatch}: oracle={a[mismatch]}, candidate={b[mismatch]}')
        self.assertLessEqual(max(a), 1, (label, 'validator mutated input'))
        self.counts[method + ('_erased_live' if erased else '')] += count

    def test_all_form_bytes_command_bytes_and_levels_every_revision(self):
        for revision in range(1, 7):
            for form in range(256):
                self.same_table('history_command_table', (revision, form), 52 * 256,
                                (revision, form, 'command-level'))
            for form in list(range(256)) + [256, 65535, 65536, 65537, 0xffffffff]:
                for name in ('creatures_form_allowed_revision', 'creatures_trial_allowed_mask',
                             'creatures_family_revision', 'creatures_legacy_spirit_revision'):
                    self.assertEqual(getattr(self.new, name)(form, revision),
                                     getattr(self.old, name)(form, revision), (revision, form, name))
                    self.counts['form_policy_api'] += 1
                for level in (0, 1, 12, 28, 50, 51, 255, 256, 65537, 0xffffffff):
                    for command in (0, 1, 90, 91, 127, 255, 256, 65537, 0xffffffff):
                        self.assertEqual(self.new.creatures_command_learned_revision(form, level, command, revision),
                                         self.old.creatures_command_learned_revision(form, level, command, revision),
                                         (revision, form, level, command))
                        self.counts['wide_scalar_command_api'] += 1

    def test_every_16bit_mask_and_single_record_byte_every_revision(self):
        for revision in range(1, 7):
            for form, row in ROWS.items():
                if not self.old.creatures_form_allowed_revision(form, revision):
                    continue
                c = instance(row, self.old.creatures_trial_allowed_mask(form, revision))
                self.assertEqual(self.old.creatures_instance_validate_revision(C.byref(c), revision), 1,
                                 (revision, form, 'valid seed control'))
                self.assertEqual(self.new.creatures_instance_validate_revision(C.byref(c), revision), 1)
                self.same_table('history_mask_table', (C.byref(c), revision), 65536,
                                (revision, form, 'mask'))
                self.same_table('history_instance_byte_table', (C.byref(c), revision), 24 * 256,
                                (revision, form, 'record-byte'))
                self.counts['valid_form_revision_pairs'] += 1

    def test_r6_frozen_independent_of_every_live_table(self):
        for form in range(256):
            self.same_table('history_command_table', (6, form), 52 * 256,
                            (6, form, 'erased command-level'), erased=True)
        for form, row in ROWS.items():
            c = instance(row)
            self.assertEqual(self.erased.creatures_instance_validate_revision(C.byref(c), 6), 1, form)
            self.assertEqual(self.erased.creatures_instance_validate(C.byref(c)), 0,
                             (form, 'erased live table control'))
            self.same_table('history_mask_table', (C.byref(c), 6), 65536,
                            (6, form, 'erased mask'), erased=True)
            self.same_table('history_instance_byte_table', (C.byref(c), 6), 24 * 256,
                            (6, form, 'erased record-byte'), erased=True)

    def test_frozen_r6_manifest_exact_allowed_masks_learn_and_terminal_bounds(self):
        for form, row in ROWS.items():
            self.assertEqual(self.old.creatures_trial_allowed_mask(form, 6), row['trial_mask'])
            self.assertEqual(self.old.creatures_family_revision(form, 6), row['family'])
            for level in range(52):
                for command in range(256):
                    expected = int(1 <= level <= 50 and any(l <= level and a == command for l, a in row['learn']))
                    self.assertEqual(self.old.creatures_command_learned_revision(form, level, command, 6), expected,
                                     (form, level, command))
            for level in (0, 1, max(1, row['min_level'] - 1), row['min_level'], 49, 50, 51):
                for bond in (0, max(0, row['min_bond'] - 1), row['min_bond'], 100, 101):
                    for mask in (0, row['required_trial'], row['trial_mask'], 65535):
                        c = instance(row, mask); c.level = level; c.bond = bond
                        c.xp = 4 * (max(1, level) - 1) ** 3
                        a = self.old.creatures_instance_validate_revision(C.byref(c), 6)
                        b = self.new.creatures_instance_validate_revision(C.byref(c), 6)
                        self.assertEqual(a, b, (form, level, bond, mask))
                        self.counts['terminal_threshold_combinations'] += 1
            self.counts['manifest_command_cases'] += 52 * 256

    def test_roster_holes_duplicates_collections_party_and_nonmutation(self):
        for revision, name, sha in FIXTURES:
            image = (ROOT / f'tests/fixtures/v5-revision{revision}' / name).read_bytes()
            self.assertEqual(digest(image), sha)
            state = Save()
            self.assertEqual(self.old.history_probe_image(image, C.byref(state)), 1)
            raw = bytes(state.roster)
            self.assertEqual(self.new.creatures_roster_validate_revision(C.byref(state.roster), revision), 1)
            # Every byte including padding, empty slots, expedition credits and collections.
            for offset in range(len(raw)):
                changed = bytearray(raw); changed[offset] ^= 255
                old, new = Roster.from_buffer_copy(changed), Roster.from_buffer_copy(changed)
                self.assertEqual(self.old.creatures_roster_validate_revision(C.byref(old), revision),
                                 self.new.creatures_roster_validate_revision(C.byref(new), revision),
                                 (revision, name, offset))
                self.assertEqual(bytes(old), changed); self.assertEqual(bytes(new), changed)
                self.counts['roster_byte_cases'] += 1
            occupied = [i for i, c in enumerate(state.roster.instances) if c.form_id]
            for first in occupied:
                for second in occupied:
                    if first == second:
                        continue
                    r = Roster.from_buffer_copy(raw)
                    r.instances[first].instance_id = r.instances[second].instance_id
                    self.assertEqual(self.old.creatures_roster_validate_revision(C.byref(r), revision), 0)
                    self.assertEqual(self.new.creatures_roster_validate_revision(C.byref(r), revision), 0)
                    self.counts['duplicate_instance_ids'] += 1
        for rev in (0, 9, 255, 256, 65535, 0xffffffff):
            self.assertEqual(self.new.creatures_instance_validate_revision(None, rev), 0)
            self.assertEqual(self.new.creatures_roster_validate_revision(None, rev), 0)

    def test_independent_native_asan_ubsan_oracle_and_candidate(self):
        """Run both source closures as executables so sanitizer runtimes load first."""
        seeds = ',\n'.join('{%d,%d,%d,%d}' % (r['id'], r['polarity'], r['learn'][0][1], r['trial_mask'])
                          for r in ROWS.values())
        main = r'''
#include <stdio.h>
#include <stdlib.h>
static const unsigned seeds[][4] = {SEEDS};
static unsigned long long hash=1469598103934665603ULL;
static void add(unsigned v) { hash^=v; hash*=1099511628211ULL; }
int main(int argc, char **argv) {
    CreatureInstance c;
    Save5State s, before;
    unsigned r, f, l, a, i, m;
    unsigned char *out=(unsigned char *)malloc(65536);
    if(!out)return 2;
    for(r=1;r<=6;++r) {
        if(creatures_instance_validate_revision(0,r)||creatures_roster_validate_revision(0,r)||save5_validate_revision(0,r))return 3;
        for(f=0;f<256;++f) {
            add(creatures_form_allowed_revision(f,r));add(creatures_trial_allowed_mask(f,r));
            history_command_table(r,f,out);
            for(i=0;i<52*256;++i)add(out[i]);
        }
        for(i=0;i<sizeof seeds/sizeof seeds[0];++i) {
            if(!creatures_form_allowed_revision(seeds[i][0],r))continue;
            memset(&c,0,sizeof c);c.form_id=seeds[i][0];c.polarity=seeds[i][1];c.equipped[0]=seeds[i][2];
            c.flags=1;c.instance_id=1;c.level=50;c.bond=100;c.xp=470596;
            c.trial_flags=creatures_trial_allowed_mask(c.form_id,r);
            if(!creatures_instance_validate_revision(&c,r))return 4;
            history_mask_table(&c,r,out);for(m=0;m<65536;++m){if(out[m]>1)return 5;add(out[m]);}
            history_instance_byte_table(&c,r,out);for(m=0;m<24*256;++m){if(out[m]>1)return 6;add(out[m]);}
            for(l=0;l<52;++l)for(a=0;a<4;++a){c.level=l;c.xp=l?4*(l-1)*(l-1)*(l-1):0;c.trial_flags=a;add(creatures_instance_validate_revision(&c,r));}
        }
    }
    for(i=1;i<(unsigned)argc;++i) {
        unsigned char image[32768];FILE *file=fopen(argv[i],"rb");
        if(!file||fread(image,1,sizeof image,file)!=sizeof image)return 7;
        fclose(file);
        if(history_probe_image(image,&s)!=1)return 8;
        /* Read the recorded content revision from the original bank header. */
        r=image[SAVE5_BANK_A+12];
        if(!save5_validate_revision(&s,r))return 10;
        before=s;
        for(m=0;m<sizeof s;++m) {
            ((unsigned char *)&s)[m]^=255;add(save5_validate_revision(&s,r));
            ((unsigned char *)&s)[m]^=255;
            if(memcmp(&s,&before,sizeof s))return 11;
        }
    }
    printf("%llu\n",hash);free(out);return 0;
}
'''.replace('SEEDS', seeds)
        outputs = []
        for tag, root in (('oracle-sanitized', self.oracle), ('candidate-sanitized', ROOT)):
            folder = self.folder / tag; folder.mkdir()
            for path, raw in source_closure(root).items():
                (folder / Path(path).name).write_bytes(raw)
            from test_save5_history_differential import HARNESS
            common_main=main.replace('for(m=0;m<sizeof s;++m)',f'for(m=0;m<{Save.economy.offset}u;++m)')
            (folder / 'main.c').write_text(HARNESS + TABLE_HARNESS + common_main)
            exe = folder / 'test'
            subprocess.run(shlex.split(os.environ.get('HOST_CC', 'cc')) + [
                '-std=c99', '-O1', '-Wall', '-Wextra', '-Werror', '-pedantic',
                '-ffreestanding', '-fno-builtin', '-DSAVE4_HOST_TEST', '-DSAVE5_HOST_TEST',
                '-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-no-pie',
                '-I' + str(folder), *[str(folder / (n + '.c')) for n in SOURCES],
                str(folder / 'main.c'), '-o', str(exe)], check=True)
            result = subprocess.run([str(exe), *[str(ROOT / f'tests/fixtures/v5-revision{r}' / n)
                     for r, n, sha in FIXTURES]], check=True, capture_output=True, text=True,
                env=dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1'))
            self.assertEqual(result.stderr, '')
            outputs.append(result.stdout.strip())
        # Byte-wise differential tests above establish exact equality; this is
        # a second independent sanitizer execution, with an additional checksum.
        self.assertEqual(outputs[0], outputs[1])
        self.counts['asan_ubsan_executables'] += 2


if __name__ == '__main__':
    unittest.main(verbosity=2)
