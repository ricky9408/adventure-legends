#!/usr/bin/env python3
"""Test-only reviewed F013 branch tables exercise actual runtime APIs.
No synthetic identity, command or capability is added to the cartridge catalog.
"""
import os
from pathlib import Path
import shlex
import subprocess
import tempfile
import unittest
from test_creature_sparse import ROOT, edit_array, refresh_key_indexes

def branch_sources(extended=False):
    h=(ROOT/'src/creatures.h').read_text()
    c=(ROOT/'src/creatures.c').read_text()
    d=(ROOT/'src/creature_data.c').read_text()
    for old,new in [('CREATURE_ENABLED_COUNT = 41','CREATURE_ENABLED_COUNT = 44'),
                    ('CREATURE_LEARNSET_COUNT = 61','CREATURE_LEARNSET_COUNT = 66'),
                    ('CREATURE_EVOLUTION_COUNT = 20','CREATURE_EVOLUTION_COUNT = 22'),
                    ('CREATURE_ABILITY_COUNT = 41','CREATURE_ABILITY_COUNT = 44')]:
        assert old in h;h=h.replace(old,new)
    def append(text,name,rows):return edit_array(text,name,lambda body:body+'\n'+rows)
    d=append(d,'creature_forms','''    {37, 13, 0, 0, 1, 0, {36, 36, 36, 36, 36}, 43, 0x00000800u, 37, 61, 1, 2, 20, 0, 37, 1},
    {38, 13, 0, 0, 2, 0, {48, 48, 48, 48, 48}, 44, 0x00000800u, 38, 62, 2, 0, 0, 0, 38, 1},
    {39, 13, 0, 0, 2, 0, {48, 48, 48, 48, 48}, 45, 0x00000800u, 39, 64, 2, 0, 0, 0, 39, 1},''')
    d=append(d,'creature_learnsets','    {1, 43},\n    {1, 43},\n    {20, 44},\n    {1, 43},\n    {20, 45},')
    edges='    {37, 38, 20, 40, 1, 64},\n    {37, 39, 20, 40, 1, 64},'
    d=append(d,'creature_evolutions',edges)
    d=append(d,'creature_abilities','    {43, 0, 90, 0x00000800u},\n    {44, 0, 120, 0x00000800u},\n    {45, 0, 120, 0x00000800u},')
    c=append(c,'form_policy','    {37, 13, 1, 43, 61, 1, 20, 2},\n    {38, 13, 2, 44, 62, 2, 0, 0},\n    {39, 13, 2, 45, 64, 2, 0, 0},')
    c=append(c,'family_policy','    {13, CREATURE_WOOD, CREATURE_YIN, 1, FIELD_GROW_ROOTS, 0},')
    c=append(c,'ability_policy','    {43, 90},\n    {44, 120},\n    {45, 120},')
    c=append(c,'expected_edges',edges)
    c=append(c,'trial_policy','    {13, 1, 1, 0, 4},')
    if extended:
        c=append(c,'capability_policy','    {33, 0},')
        c=append(c,'capability_memberships','    {37, 33},\n    {38, 33},\n    {39, 33},')
    c,d=refresh_key_indexes(c,d)
    return h,c,d

def check(sources,*,invalid=False,extended=False,sanitize=True):
    with tempfile.TemporaryDirectory(prefix='creature-branch-') as temp:
        path=Path(temp)
        for name,src in zip(('creatures.h','creatures.c','creature_data.c'),sources):(path/name).write_text(src)
        flags=['-std=c99','-O1','-Wall','-Wextra','-Werror','-pedantic','-I'+str(path)]
        if invalid:flags+=['-DEXPECT_INVALID_CATALOG']
        if extended:flags+=['-DEXTENDED_CAPABILITY']
        if sanitize:flags+=['-fsanitize=address,undefined','-fno-omit-frame-pointer','-no-pie']
        subprocess.run(shlex.split(os.environ.get('HOST_CC','cc'))+flags+[str(path/'creatures.c'),str(path/'creature_data.c'),str(ROOT/'tests/creatures_branch_native.c'),'-o',str(path/'native')],check=True)
        subprocess.run([str(path/'native')],check=True,env=dict(os.environ,ASAN_OPTIONS='detect_leaks=0:halt_on_error=1',UBSAN_OPTIONS='halt_on_error=1'))

class BranchTests(unittest.TestCase):
    def test_exact_two_edges_never_implicitly_choose_first(self):check(branch_sources())
    def test_key33_has_no_legacy_projection_and_inherits(self):check(branch_sources(True),extended=True)
    def test_every_branch_edge_preserves_exact_family_graph_commands_and_caps(self):
        h,c,d=branch_sources()
        mutations=[('cycle','{37, 39, 20, 40, 1, 64}','{39, 37, 20, 40, 1, 64}'),
                   ('merge','{37, 39, 20, 40, 1, 64}','{37, 38, 20, 40, 1, 64}'),
                   ('crossfamily','{37, 39, 20, 40, 1, 64}','{37, 26, 20, 40, 1, 64}'),
                   ('lostcommand','{1, 43},\n    {20, 45}','{1, 45},\n    {20, 45}'),
                   ('lostcapability','39, 0x00000800u','39, 0x00000000u'),
                   ('badedgecount','37, 61, 1, 2, 20','37, 61, 1, 1, 20')]
        # Signature45 precedes the final form's capability field.
        mutations[4]=('lostcapability','45, 0x00000800u, 39','45, 0x00000000u, 39')
        for label,old,new in mutations:
            with self.subTest(label=label):
                self.assertIn(old,d);check((h,c,d.replace(old,new,1)),invalid=True)
    def test_extended_capability_loss_duplicate_keys_and_trial_aliases_fail_closed(self):
        h,c,d=branch_sources(True)
        for label,old,new in [('lostextended','    {39, 33},',''),
                              ('duplicatekey','    {33, 0},','    {26, 0},'),
                              ('trialalias','    {13, 1, 1, 0, 4},','    {13, 1, 1, 0, 4},\n    {13, 2, 1, 0, 4},'),
                              ('trialoverflow','    {13, 1, 1, 0, 4},','    {61, 1, 1, 0, 4},')]:
            with self.subTest(label=label):
                self.assertIn(old,c);check((h,c.replace(old,new,1),d),invalid=True)

if __name__=='__main__':unittest.main(verbosity=2)
