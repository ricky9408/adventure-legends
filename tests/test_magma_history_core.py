#!/usr/bin/env python3
"""Historical validation is independent of changed current authored relations."""
import ctypes as C, hashlib, itertools, json, random, subprocess, tempfile, unittest
from pathlib import Path
from test_save5 import ROOT, Instance, Roster
POLICY=json.loads((ROOT/'assets/history/creatures-v1-v4.json').read_text())['forms']
LOOKUP={f['id']:f for f in POLICY}

def reference(c,rev):
    if rev not in (1,2,3,4):return False
    if not c.form_id:return not any(bytes(c))
    p=LOOKUP.get(c.form_id)
    if p is None or not p['revision_bits']&(1<<(rev-1)):return False
    if not(c.flags&1) or c.flags&~7 or not 1<=c.level<=50 or c.bond>100 or c.xp>470596 or not 0<c.instance_id<0xffffffff or c.nickname_id:return False
    if c.flags&2 and not 1<=p['family']<=4:return False
    if c.polarity!=p['polarity'] or c.level<p['min_level'] or c.trial_flags&~p['trial_mask']:return False
    if c.xp<4*(c.level-1)**3 or c.level<50 and c.xp>=4*c.level**3:return False
    if c.selected_command>1 or not c.equipped[c.selected_command] or c.equipped[0] and c.equipped[0]==c.equipped[1]:return False
    return all(not ability or any(a==ability and level<=c.level for level,a in p['learn']) for ability in c.equipped)

class HistoricalCoreTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory(prefix='magma-history-core-');cls.addClassCleanup(cls.temp.cleanup);p=Path(cls.temp.name);cls.libs=[]
        data=(ROOT/'src/creature_data.c').read_text()
        mutated=data.replace('    {1, 1},','    {1, 23},',1)
        # Removing a CURRENT form-index row is also irrelevant to past policy.
        broken=data.replace('0, 1, 2, 0, 3, 4, 0, 5, 6, 0, 7, 8, 0, 9, 10, 0,','0, 0, 2, 0, 3, 4, 0, 5, 6, 0, 7, 8, 0, 9, 10, 0,',1)
        assert data!=mutated and data!=broken
        for name,text in [('normal',data),('command-removed',mutated),('form-index-removed',broken)]:
            source=p/(name+'.c');source.write_text(text);so=p/(name+'.so')
            subprocess.run(['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-shared','-fPIC','-I'+str(ROOT/'src'),str(ROOT/'src/creatures.c'),str(source),'-o',str(so)],check=True)
            lib=C.CDLL(str(so));lib.creatures_instance_validate_revision.argtypes=[C.POINTER(Instance),C.c_uint]
            lib.creatures_instance_validate.argtypes=[C.POINTER(Instance)]
            lib.creatures_roster_validate_revision.argtypes=[C.POINTER(Roster),C.c_uint]
            cls.libs.append(lib)
    def test_current_command1_replacement23_cannot_revoke_old_command(self):
        c=Instance();c.form_id=1;c.flags=1;c.level=1;c.instance_id=1;c.polarity=1;c.equipped[0]=1
        self.assertTrue(self.libs[0].creatures_instance_validate(C.byref(c)))
        self.assertFalse(self.libs[1].creatures_instance_validate(C.byref(c)))
        for lib in self.libs:
            for rev in range(1,5):self.assertTrue(lib.creatures_instance_validate_revision(C.byref(c),rev))
        c.equipped[0]=23
        for lib in self.libs:
            for rev in range(1,5):self.assertFalse(lib.creatures_instance_validate_revision(C.byref(c),rev))
    def test_every_snapshot_form_levels_commands_trials_and_zero_bond(self):
        count=0
        for p in POLICY:
            c=Instance();c.form_id=p['id'];c.flags=1;c.instance_id=1;c.polarity=p['polarity']
            commands={0,1,12,23,255}|{a for _,a in p['learn']}
            for level,bond,mask,command in itertools.product((1,p['min_level']-1,p['min_level'],50),(0,100),(0,p['trial_mask'],1024,65535),commands):
                c.level=level;c.xp=4*max(0,level-1)**3;c.bond=bond;c.trial_flags=mask;c.equipped[0]=command
                for rev in range(1,5):
                    wanted=reference(c,rev)
                    for lib in self.libs:self.assertEqual(bool(lib.creatures_instance_validate_revision(C.byref(c),rev)),wanted,(p['id'],rev,level,bond,mask,command))
                    count+=1
        self.assertGreater(count,30000)
        print('historical instance policy comparisons:',count*len(self.libs))
    def test_deterministic_corruptions_match_independent_wire_reference(self):
        rng=random.Random(20261005);count=0
        for _ in range(12000):
            p=rng.choice(POLICY);c=Instance();c.form_id=p['id'];c.flags=1;c.instance_id=rng.randrange(1,160);c.level=50;c.xp=470596;c.polarity=p['polarity'];c.equipped[0]=p['learn'][0][1]
            raw=bytearray(bytes(c));raw[rng.randrange(24)]=rng.randrange(256);c=Instance.from_buffer_copy(raw)
            for rev in (1,2,3,4):
                expected=reference(c,rev)
                for lib in self.libs:self.assertEqual(bool(lib.creatures_instance_validate_revision(C.byref(c),rev)),expected)
                count+=1
        self.assertEqual(count,48000)
    def test_decoded_roster_uses_history_for_members_collection_and_story(self):
        r=Roster();self.libs[0].creatures_roster_init(C.byref(r));c=r.instances[0];c.form_id=1;c.flags=3;c.level=1;c.instance_id=1;c.polarity=1;c.equipped[0]=1
        r.party[0]=0;r.selected_party=0;r.next_instance_id=2;r.seen[0]=r.obtained[0]=r.rewards[0]=1
        for lib in self.libs:
            for rev in (1,2,3,4):self.assertTrue(lib.creatures_roster_validate_revision(C.byref(r),rev))
        before=bytes(r);r.party[1]=0
        for lib in self.libs:self.assertFalse(lib.creatures_roster_validate_revision(C.byref(r),1))
        r=Roster.from_buffer_copy(before);r.instances[159]=r.instances[0]
        for lib in self.libs:self.assertFalse(lib.creatures_roster_validate_revision(C.byref(r),1))

if __name__=='__main__':unittest.main(verbosity=2)
