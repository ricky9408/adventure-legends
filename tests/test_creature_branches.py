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
    # F013 is now an actual reviewed current branch. Preserve the independent
    # synthetic capability extension and all malformed-graph cases below.
    def append(text,name,rows):return edit_array(text,name,lambda body:body+'\n'+rows)
    if extended:
        c=append(c,'capability_policy','    {33, 0},')
        c=append(c,'capability_memberships','    {37, 33},\n    {38, 33},\n    {39, 33},')
    c,d=refresh_key_indexes(c,d)
    return h,c,d

def check(sources,*,invalid=False,extended=False,sanitize=True):
    with tempfile.TemporaryDirectory(prefix='creature-branch-') as temp:
        path=Path(temp)
        for name,src in zip(('creatures.h','creatures.c','creature_data.c'),sources):(path/name).write_text(src)
        (path/'creature_history_v5.inc').write_bytes((ROOT/'src/creature_history_v5.inc').read_bytes())
        (path/'creature_admission_job.inc').write_bytes((ROOT/'src/creature_admission_job.inc').read_bytes())
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
        mutations=[('cycle','{37, 39, 26, 45, 2, 256}','{39, 37, 26, 45, 2, 256}'),
                   ('merge','{37, 39, 26, 45, 2, 256}','{37, 38, 26, 45, 2, 256}'),
                   ('crossfamily','{37, 39, 26, 45, 2, 256}','{37, 26, 26, 45, 2, 256}'),
                   ('lostcommand','{1, 49},\n    {26, 51}','{1, 51},\n    {26, 51}'),
                   ('lostcapability','39, 0x00000800u','39, 0x00000000u'),
                   ('badedgecount','37, 73, 1, 2, 24','37, 73, 1, 1, 24')]
        # Signature51 precedes the final form's capability field.
        mutations[4]=('lostcapability','51, 0x00000800u, 39','51, 0x00000000u, 39')
        for label,old,new in mutations:
            with self.subTest(label=label):
                self.assertIn(old,d);check((h,c,d.replace(old,new,1)),invalid=True)
    def test_extended_capability_loss_duplicate_keys_and_trial_aliases_fail_closed(self):
        h,c,d=branch_sources(True)
        for label,old,new in [('lostextended','    {39, 33},',''),
                              ('duplicatekey','    {33, 0},','    {26, 0},'),
                              ('trialalias','    {13, 1, 1, 0, 5},','    {13, 1, 1, 0, 5},\n    {13, 2, 1, 0, 5},'),
                              ('trialoverflow','    {13, 1, 1, 0, 5},','    {61, 1, 1, 0, 5},')]:
            with self.subTest(label=label):
                self.assertIn(old,c);check((h,c.replace(old,new,1),d),invalid=True)

if __name__=='__main__':unittest.main(verbosity=2)
