#!/usr/bin/env python3
"""Host-only sparse catalog readiness. These fixtures are NOT playable content.

Only temporary ROM table/policy declarations are shuffled or mutated. The C
lookup, grant, validation, trial and evolution functions are copied unchanged.
No authored catalog, enabled list, generated source or save format is altered.
Also imported by test_creatures.py so the normal core suite runs these checks.
"""
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

def edit_array(text, name, edit):
    pattern = r'(\b' + re.escape(name) + r'\[[^\]]*\]\s*=\s*\{\n)(.*?)(\n\s*\};)'
    def replace(match):
        return match[1] + edit(match[2]) + match[3]
    result, count = re.subn(pattern, replace, text, flags=re.S)
    if count != 1:
        raise AssertionError(f'Expected exactly one {name} declaration, got {count}')
    return result


def refresh_key_indexes(core, data):
    """Regenerate matching fixture indexes after intentionally reordering rows.
    A stale index is corruption, not permission for a fallback linear scan.
    """
    def rewrite(source, index_name, record_name, bound, key=0):
        pattern=r'\b'+re.escape(record_name)+r'\[[^\]]*\]\s*=\s*\{\n(.*?)\n\s*\};'
        body=re.search(pattern,source,re.S)[1]
        records=re.findall(r'\{([^{}]*)\}',body) if record_name != 'creature_forms' else re.findall(r'\{(\d+),[^\n]*',body)
        # Form rows contain nested stats; their immutable ID is still first.
        ids=[int(record.split(',')[key].strip()) for record in records]
        if record_name == 'creature_forms':ids=[int(x) for x in records]
        values=[0]*(bound+1)
        for row,id_ in enumerate(ids):
            if not 0<id_<=bound or values[id_]:raise AssertionError((record_name,id_))
            values[id_]=row+1
        return edit_array(source,index_name,lambda _: '\n'.join('    '+', '.join(map(str,values[i:i+16]))+',' for i in range(0,len(values),16)))
    for index,record,bound,key in [('creature_form_index','creature_forms',128,0),
                                    ('creature_ability_index','creature_abilities',255,0),
                                    ('creature_incoming_evolution_index','creature_evolutions',128,1)]:
        data=rewrite(data,index,record,bound,key)
    for record,bound in [('form_policy',128),('family_policy',60),('ability_policy',255)]:
        core=rewrite(core,record+'_index',record,bound)
    return core,data

def fixture_sources(*, high_bit=False, reordered=False):
    header = (ROOT / 'src/creatures.h').read_text()
    core = (ROOT / 'src/creatures.c').read_text()
    data = (ROOT / 'src/creature_data.c').read_text()
    if high_bit:
        # Synthetic host-only remapping demonstrates the unchanged u16 wire
        # width. It is neither a real trial allocation nor playable content.
        header = header.replace('CREATURE_TRIAL_MASK = 1023', 'CREATURE_TRIAL_MASK = 33279')
        header = header.replace('CREATURE_TRIAL_COMPASS_ROUND = 512', 'CREATURE_TRIAL_COMPASS_ROUND = 32768')
        old = '{77, 78, 20, 50, 512,'
        assert data.count(old) == 1
        data = data.replace(old, '{77, 78, 20, 50, 32768,')
        # Current per-form masks are independent of the frozen1–4 snapshot.
        def remap_current_masks(body):
            return re.sub(r'(\{(?:77|78),[^\n]+, )512(, 0x)',r'\g<1>32768\2',body)
        core = edit_array(core, 'form_policy', remap_current_masks)
    if reordered:
        def reverse(body):
            return '\n'.join(line.rstrip().rstrip(',') + ',' for line in reversed(body.splitlines()))
        for name in ('creature_forms', 'creature_abilities'):
            data = edit_array(data, name, reverse)
        for name in ('form_policy', 'family_policy', 'ability_policy'):
            core = edit_array(core, name, reverse)
    if reordered:
        core, data = refresh_key_indexes(core, data)
    return header, core, data


def native_check(sources, *, high_bit=False, invalid=False,
                 unknown_family=False, sanitize=False):
    with tempfile.TemporaryDirectory(prefix='creature-sparse-synthetic-') as temp:
        directory = Path(temp)
        for name, source in zip(('creatures.h', 'creatures.c', 'creature_data.c'), sources):
            (directory / name).write_text(source)
        flags = ['-std=c99', '-O1' if sanitize else '-O2', '-Wall', '-Wextra',
                 '-Werror', '-pedantic', '-I' + str(directory)]
        flags.append('-DSPARSE_FIXTURE')
        if high_bit:
            flags.append('-DLAST_TRIAL=32768')
        if invalid:
            flags.append('-DEXPECT_INVALID_CATALOG')
        if unknown_family:
            flags.append('-DEXPECT_UNKNOWN_FAMILY')
        if sanitize:
            flags += ['-fsanitize=address,undefined', '-fno-omit-frame-pointer', '-no-pie']
        output = directory / 'sparse-native'
        subprocess.run(shlex.split(os.environ.get('HOST_CC', 'cc')) + flags + [
            str(directory / 'creatures.c'), str(directory / 'creature_data.c'),
            str(ROOT / 'tests/creatures_sparse_native.c'), '-o', str(output)], check=True)
        env = dict(os.environ, ASAN_OPTIONS='detect_leaks=0:halt_on_error=1', UBSAN_OPTIONS='halt_on_error=1')
        subprocess.run([str(output)], env=env, check=True)


class SparseCreatureTests(unittest.TestCase):
    def test_sparse_development_rows_leave_unlisted_content_disabled(self):
        native_check(fixture_sources())

    def test_sparse_synthetic_twenty_one_forms_with_unordered_keys(self):
        native_check(fixture_sources(reordered=True))

    def test_sparse_synthetic_full_u16_trial_width(self):
        native_check(fixture_sources(high_bit=True), high_bit=True)

    def test_sparse_synthetic_lookup_and_trial_sanitizers(self):
        native_check(fixture_sources(reordered=True), sanitize=True)
        native_check(fixture_sources(high_bit=True), high_bit=True, sanitize=True)

    def test_sparse_synthetic_family_policy_rejects_collisions(self):
        header, core, data = fixture_sources()
        for label, old, new in [
            ('duplicate family', '{25, CREATURE_WATER, CREATURE_YANG, CREATURE_TRIAL_FRAGILE_CARGO,', '{7, CREATURE_WATER, CREATURE_YANG, CREATURE_TRIAL_FRAGILE_CARGO,'),
            ('duplicate trial', '{25, CREATURE_WATER, CREATURE_YANG, CREATURE_TRIAL_FRAGILE_CARGO,', '{25, CREATURE_WATER, CREATURE_YANG, CREATURE_TRIAL_TENSION_ROOF,'),
            ('combined trial', '{25, CREATURE_WATER, CREATURE_YANG, CREATURE_TRIAL_FRAGILE_CARGO,', '{25, CREATURE_WATER, CREATURE_YANG, 192,'),
            ('out of capacity family', '{25, CREATURE_WATER, CREATURE_YANG, CREATURE_TRIAL_FRAGILE_CARGO,', '{255, CREATURE_WATER, CREATURE_YANG, CREATURE_TRIAL_FRAGILE_CARGO,'),
        ]:
            with self.subTest(label=label):
                self.assertEqual(core.count(old), 1)
                native_check((header, core.replace(old, new), data), invalid=True, sanitize=True)

    def test_sparse_synthetic_malformed_indexes_fail_closed(self):
        header, core, data = fixture_sources()
        for name,where in [('creature_form_index','data'),('creature_ability_index','data'),
                           ('creature_incoming_evolution_index','data'),('form_policy_index','core'),
                           ('family_policy_index','core'),('ability_policy_index','core')]:
            for value in [1,255]:
                with self.subTest(name=name,value=value):
                    def corrupt(body):
                        values=[int(v) for v in re.findall(r'\d+',body)]
                        values[0]=value
                        return '    '+', '.join(map(str,values))+','
                    modified=edit_array(data if where=='data' else core,name,corrupt)
                    native_check((header,core if where=='data' else modified,modified if where=='data' else data),invalid=True,sanitize=True)

    def test_sparse_synthetic_unknown_family_is_not_array_index(self):
        header, core, data = fixture_sources()
        old, new = '{16, 6, 3, 1, 1, 0,', '{16, 255, 3, 1, 1, 0,'
        self.assertEqual(data.count(old), 1)
        native_check((header, core, data.replace(old, new)), invalid=True, unknown_family=True, sanitize=True)

    def test_sparse_synthetic_unknown_duplicate_and_reserved_ability_reject(self):
        header, core, data = fixture_sources()
        for ability in (0, 12, 13, 255):
            with self.subTest(ability=ability):
                old = '{22, 3, 120,'
                self.assertEqual(data.count(old), 1)
                native_check((header, core, data.replace(old, '{%d, 3, 120,' % ability)),
                             invalid=True, sanitize=True)


if __name__ == '__main__':
    unittest.main(verbosity=2)
