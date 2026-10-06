#!/usr/bin/env python3
"""Southern revision4 ledger tests. Host fixtures are not controller acquisition proof."""
import ctypes as C
import hashlib
import json
import unittest
import test_save5 as base
from test_save5 import ROOT, A, B, SIZE, BUSY, DONE, FAILED, Save, Instance, Roster, Quests, compare_state, repair_crc

FORMS=(79,85,25,28,81,83,87,89,91,93)
FAMILIES=(28,31,9,10,29,30,32,33,34,35)
TOKENS=(1,2,16,17,18,19,20,21,22,23)
LEVELS=(20,20,20,22,22,22,24,22,24,22)
BONDS=(40,40,40,45,45,45,45,45,45,45)
MASKS=(3,3,15,7,3,3,3,3)
NEW_ITEMS=(4,12,36,52,66,84)
NEW_FORMS=tuple(sorted(f for x in FORMS for f in (x,x+1)))

class SouthernSaveTests(base.Save5Tests):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        for name in ('southern_can_enter','southern_visit','southern_anchor','southern_quest_available',
                     'southern_quest_offer','southern_quest_claim','southern_field_recruit','southern_discover',
                     'southern_source_claimed'):
            getattr(cls.lib,name).argtypes=[C.POINTER(Save),C.c_uint]
            getattr(cls.lib,name).restype=C.c_int
        cls.lib.southern_quest_objective.argtypes=[C.POINTER(Save),C.c_uint,C.c_uint]
        cls.lib.southern_trial_complete.argtypes=[C.POINTER(Save)]+[C.c_uint]*5
        cls.lib.southern_source_family.argtypes=[C.c_uint]
        cls.lib.southern_source_token_for_family.argtypes=[C.c_uint]
        cls.lib.southern_recruit_level.argtypes=[C.POINTER(Roster)]
        cls.lib.southern_context.argtypes=[C.POINTER(Save)]
        cls.lib.creatures_mark_trial_qualified.argtypes=[C.POINTER(Instance),C.c_uint,C.c_uint]
        cls.lib.creatures_instance_validate_revision.argtypes=[C.POINTER(Instance),C.c_uint]

    def southern(self):
        self.reset()
        self.put((ROOT/'tests/fixtures/v5-revision3/northern-all21-town.sav').read_bytes())
        s=self.load()
        self.assertEqual(self.lib.southern_visit(C.byref(s),30),1)
        return s

    def ready(self,s,q):
        self.assertIn(self.lib.southern_quest_offer(C.byref(s),q),(0,1))
        for bit in (1,2,4,8):
            if MASKS[q-22]&bit:self.assertIn(self.lib.southern_quest_objective(C.byref(s),q,bit),(0,1,2))
        self.assertEqual(self.lib.save5_quest_state(C.byref(s.quests),q),2)

    def claim(self,s,q):
        self.ready(s,q)
        self.assertEqual(self.lib.southern_quest_claim(C.byref(s),q),3)
        self.assertEqual(self.lib.save5_validate(C.byref(s)),1)

    def recruits(self):
        s=self.southern()
        for room in (31,32,33):self.assertEqual(self.lib.southern_visit(C.byref(s),room),1)
        self.claim(s,22);self.claim(s,23)
        for q,d in ((29,0),(28,1)):
            self.ready(s,q);self.assertEqual(self.lib.southern_discover(C.byref(s),d),1)
        for token in TOKENS[2:]:self.assertEqual(self.lib.southern_field_recruit(C.byref(s),token),3)
        return s

    def slot(self,s,form):
        return next(i for i,c in enumerate(s.roster.instances) if c.form_id in (form,form+1))

    def trial(self,s,index):
        slot=self.slot(s,FORMS[index]);c=s.roster.instances[slot]
        self.assertEqual(self.lib.southern_trial_complete(C.byref(s),slot,c.instance_id,FAMILIES[index],1,TOKENS[index]),3)
        return slot

    def unchanged(self,s,call,result):
        before=bytes(s);self.assertEqual(call(),result);self.assertEqual(bytes(s),before)

    def reject_snapshot(self,s):
        before=bytes(self.sram);writes=self.lib.save5_test_write_count()
        self.assertEqual(self.lib.save5_validate(C.byref(s)),0)
        if self.lib.save5_begin(C.byref(s)):
            while self.lib.save5_status()==BUSY:self.lib.save5_step(3072)
        self.assertEqual(self.lib.save5_status(),FAILED)
        self.assertEqual(self.lib.save5_test_write_count(),writes);self.assertEqual(bytes(self.sram),before)

    def test_south_empty_instance_zero_contract_every_byte_and_revision(self):
        self.lib.creatures_instance_validate.argtypes=[C.POINTER(Instance)]
        for offset in range(24):
            for value in range(1,256):
                raw=bytearray(24);raw[offset]=value
                c=Instance.from_buffer_copy(raw)
                self.assertEqual(self.lib.creatures_instance_validate(C.byref(c)),0,(offset,value))
                for revision in (1,2,3,4):
                    self.assertEqual(self.lib.creatures_instance_validate_revision(C.byref(c),revision),0,(offset,value,revision))
        c=Instance()
        self.assertEqual(self.lib.creatures_instance_validate(C.byref(c)),1)
        for revision in (1,2,3,4):self.assertEqual(self.lib.creatures_instance_validate_revision(C.byref(c),revision),1)

    def test_south_authentic_N5_revision3_migration_is_payload_identity(self):
        folder=ROOT/'tests/fixtures/v5-revision3';data=(folder/'northern-all21-town.sav').read_bytes()
        provenance=json.loads((folder/'provenance.json').read_text())
        self.assertEqual(hashlib.sha256(data).hexdigest(),'f4e853c85445b8567263a1a875eba967e552e0dcae30958ca42f39bfec4e4479')
        self.assertEqual(provenance['source_rom_sha256'],'302316c53d6fb9dafa0ecbf9f679c9c39af3a150af3aa78398c368312e50399e')
        self.assertIn('publication pending',provenance['source_release_status'])
        self.assertTrue(provenance['controller_only']);self.assertEqual(provenance['game_ram_writes'],0)
        self.put(data);s=self.load();self.assertEqual(bytes(self.sram),data)
        src=max((A,B),key=lambda o:int.from_bytes(data[o+8:o+12],'little'));dst=B if src==A else A
        self.store(s);written=bytes(self.sram[dst:dst+SIZE]);self.assertEqual(written[12:14],b'\x04\0')
        self.assertEqual(written[32:],data[src+32:src+SIZE]);self.assertEqual(bytes(self.sram[src:src+SIZE]),data[src:src+SIZE])
        self.assertEqual(bytes(s.quests.region_flags[2:]),bytes(30))

    def test_south_guarantees_field_claims_discoveries_trials_all41_and25_gear(self):
        s=self.recruits();party=bytes(s.roster.party);selected=s.roster.selected_party
        for i in range(10):
            slot=self.trial(s,i);c=s.roster.instances[slot]
            self.assertGreaterEqual(c.level,LEVELS[i]);self.assertGreaterEqual(c.bond,BONDS[i]);self.assertEqual(c.trial_flags,1)
            self.assertEqual(self.lib.creatures_evolve(C.byref(s.roster),slot,64,1,1),0)
            self.assertEqual(self.lib.save5_validate(C.byref(s)),1)
        for q in range(24,30):
            if self.lib.save5_quest_state(C.byref(s.quests),q)==2:self.assertEqual(self.lib.southern_quest_claim(C.byref(s),q),3)
            else:self.claim(s,q)
        for room in range(34,38):self.assertEqual(self.lib.southern_visit(C.byref(s),room),1)
        for room in (30,31):self.assertEqual(self.lib.southern_anchor(C.byref(s),room),1)
        s.campaign.room=37;s.campaign.spawn=0
        self.assertEqual(self.lib.southern_context(C.byref(s)),192)
        self.assertEqual(bytes(s.roster.party),party);self.assertEqual(s.roster.selected_party,selected)
        self.assertEqual(sum(v.bit_count() for v in s.roster.obtained),41)
        self.assertEqual(sum(bool(c.form_id) for c in s.roster.instances),21)
        self.assertEqual(sum(bool(x.item_id) for x in s.equipment.bag),25)
        self.store(s);self.assertEqual(compare_state(self.load()),compare_state(s))
        for token in TOKENS[2:]:self.unchanged(s,lambda:self.lib.southern_field_recruit(C.byref(s),token),0)
        for q in range(22,30):self.unchanged(s,lambda:self.lib.southern_quest_claim(C.byref(s),q),0)

    def test_south_full160_no_party_replace_and_source_retry(self):
        for q,token in ((22,None),(23,None),(None,16)):
            s=self.southern();self.lib.southern_visit(C.byref(s),31)
            if q:self.ready(s,q)
            while sum(bool(c.form_id) for c in s.roster.instances)<160:
                self.assertLess(self.lib.creatures_grant(C.byref(s.roster),1,20,20,0,0),160)
            call=(lambda:self.lib.southern_quest_claim(C.byref(s),q)) if q else (lambda:self.lib.southern_field_recruit(C.byref(s),token))
            self.unchanged(s,call,5);self.store(s);self.assertEqual(compare_state(self.load()),compare_state(s))
        s=self.recruits()
        self.assertEqual(bytes(s.roster.party),bytes((6,7,2,10)))
        self.assertEqual(self.lib.southern_recruit_level(C.byref(s.roster)),20)

    def test_south_identity_source_key_and_same_copy_floor_atomicity(self):
        s=self.recruits()
        for i in range(10):
            slot=self.slot(s,FORMS[i]);c=s.roster.instances[slot]
            for wrongslot,identity,family,key,token in ((160,c.instance_id,FAMILIES[i],1,TOKENS[i]),
                (slot,c.instance_id+1,FAMILIES[i],1,TOKENS[i]),(slot,c.instance_id,FAMILIES[(i+1)%10],1,TOKENS[i]),
                (slot,c.instance_id,FAMILIES[i],0,TOKENS[i]),(slot,c.instance_id,FAMILIES[i],65537,TOKENS[i]),
                (slot,c.instance_id,FAMILIES[i],1,TOKENS[(i+1)%10]),(slot,c.instance_id,FAMILIES[i],1,0)):
                self.unchanged(s,lambda:self.lib.southern_trial_complete(C.byref(s),wrongslot,identity,family,key,token),-1)
            self.trial(s,i)
            self.unchanged(s,lambda:self.lib.southern_trial_complete(C.byref(s),slot,c.instance_id,FAMILIES[i],1,TOKENS[i]),0)
            bad=Save.from_buffer_copy(bytes(s));bad.roster.instances[slot].bond=BONDS[i]-1
            # Another high-training copy cannot repair the first copy's evidence.
            self.assertLess(self.lib.creatures_grant(C.byref(bad.roster),FORMS[i],50,100,0,0),160)
            self.reject_snapshot(bad)
        for token,family in zip(TOKENS,FAMILIES):
            self.assertEqual(self.lib.southern_source_family(token),family)
            self.assertEqual(self.lib.southern_source_token_for_family(family),token)
        for invalid in (0,3,15,24,255,65536,0xffffffff):self.assertEqual(self.lib.southern_source_family(invalid),0)

    def test_south_sources_require_retained_exact_family_and_prerequisites(self):
        s=self.recruits()
        for i in range(10):
            bad=Save.from_buffer_copy(bytes(s));slot=self.slot(bad,FORMS[i]);C.memset(C.byref(bad.roster.instances[slot]),0,C.sizeof(Instance))
            self.reject_snapshot(bad)
        for byte,bit in ((2,1),(2,2),(2,4),(2,8),(18,1),(18,2)):
            bad=Save.from_buffer_copy(bytes(s));bad.quests.region_flags[byte]&=~bit;self.reject_snapshot(bad)
        self.trial(s,0)
        for q in (21,22,23,28,29):
            bad=Save.from_buffer_copy(bytes(s));self.set_quest(bad,q,0,0,False)
            # Clearing Q22/Q23 requires clearing linked gear source too, isolating typed recruit/trial semantics.
            if q in (22,23):
                bad=Save.from_buffer_copy(bytes(s));self.set_quest(bad,q,0,0,False)
            self.reject_snapshot(bad)

    def test_south_q24_prefix_room_spawn_visits_and_discovery_gates(self):
        s=self.southern()
        for room in range(34,38):self.unchanged(s,lambda:self.lib.southern_visit(C.byref(s),room),4)
        self.claim(s,22);self.claim(s,23);self.lib.southern_quest_offer(C.byref(s),24)
        for value in range(16):
            bad=Save.from_buffer_copy(bytes(s));self.set_quest(bad,24,2 if value==15 else 1,value)
            if value not in (0,1,3,7,15):self.reject_snapshot(bad)
        self.unchanged(s,lambda:self.lib.southern_quest_objective(C.byref(s),24,2),4)
        for room,bit in ((34,1),(35,2),(36,4),(37,8)):
            self.assertEqual(self.lib.southern_visit(C.byref(s),room),1)
            self.assertIn(self.lib.southern_quest_objective(C.byref(s),24,bit),(1,2))
        self.assertEqual(self.lib.southern_quest_claim(C.byref(s),24),3)
        for room in range(30,38):
            self.lib.southern_visit(C.byref(s),room)
            for spawn in range(6):
                copy=Save.from_buffer_copy(bytes(s));copy.campaign.room=room;copy.campaign.spawn=spawn
                allowed=spawn<=({30:4,31:3}.get(room,0)) and not(spawn==2 and room in (30,31))
                self.assertEqual(self.lib.save5_validate(C.byref(copy)),int(allowed),(room,spawn))
        self.unchanged(s,lambda:self.lib.southern_discover(C.byref(s),0),4)
        self.ready(s,29);self.assertEqual(self.lib.southern_discover(C.byref(s),0),1)
        self.assertEqual(self.lib.save5_quest_state(C.byref(s.quests),29),2)

    def test_south_historical_generic_rewards_and_all_event_aid_bits_survive(self):
        for revision,filename in ((1,'all-evolved-village.sav'),(2,'all-eleven-town.sav'),(3,'northern-all21-town.sav')):
            data=(ROOT/f'tests/fixtures/v5-revision{revision}'/filename).read_bytes()
            src=max((A,B),key=lambda o:int.from_bytes(data[o+8:o+12],'little'))
            original=data[src:src+SIZE]
            for reward in range(5,129):
                b=bytearray(original);bit=reward-1;b[128+bit//8]|=1<<(bit%8)
                b[4456:4536]=bytes([255])*80
                self.reset();self.put(repair_crc(b),A);old=self.load();self.store(old)
                if revision==1:
                    self.assertEqual(bytes(self.sram[B+96:B+4032]),bytes(b[96:4032]))
                    self.assertEqual(bytes(self.sram[B+4296:B+4544]),bytes(b[4296:4544]))
                else:self.assertEqual(bytes(self.sram[B+32:B+SIZE]),bytes(b[32:]))
        s=self.southern();s.roster.rewards[0]|=240
        for i in range(1,16):s.roster.rewards[i]=255
        s.roster.expedition_events[:]=bytes([255])*64;s.roster.lifetime_field_aid[:]=bytes([255])*16
        saved=(bytes(s.roster.rewards),bytes(s.roster.expedition_events),bytes(s.roster.lifetime_field_aid))
        self.lib.southern_visit(C.byref(s),31);self.claim(s,22);self.claim(s,23)
        self.assertEqual(self.lib.southern_field_recruit(C.byref(s),16),3);self.trial(s,2)
        self.assertEqual(saved,(bytes(s.roster.rewards),bytes(s.roster.expedition_events),bytes(s.roster.lifetime_field_aid)))

    def test_south_historical_revision_command_and_trial_matrix(self):
        for revision,forms in ((1,base.LEGACY_ENABLED),(2,base.REVISION2_ENABLED),(3,base.ENABLED)):
            for form in forms:
                s=self.fresh(3);slot=self.lib.creatures_grant(C.byref(s.roster),form,50,0,0,0)
                self.reset();self.store(s);b=bytearray(self.sram[A:A+SIZE]);b[12:14]=revision.to_bytes(2,'little')
                if revision==1:b[4032:4296]=bytes(264);b[4544:5056]=bytes(512)
                offset=160+24*slot
                # New/current commands must never leak into any old snapshot.
                for ability in (12,*range(23,43),*(range(13,23) if revision<3 else ())):
                    bad=bytearray(b);bad[offset+16]=ability;self.reset();self.put(repair_crc(bad),A);self.invalid()
                masks={1:1,2:1,4:2,5:2,7:4,8:4,10:8,11:8,13:16,14:16,16:0,19:32,20:32,22:64,23:64,73:128,74:128,75:256,76:256,77:512,78:512}
                for bit in range(16):
                    bad=bytearray(b);bad[offset+14:offset+16]=(1<<bit).to_bytes(2,'little')
                    self.reset();self.put(repair_crc(bad),A)
                    if 1<<bit==masks[form]:self.load()
                    else:self.invalid()
                self.reset();self.put(repair_crc(b),A);self.load() # Historical evolved zero trial/bond remains legal.

    def test_south_old_revisions_reject_every_new_typed_field_item_form(self):
        self.store(self.fresh(3));original=bytes(self.sram[A:A+SIZE])
        for revision in (1,2,3):
            b=bytearray(original);b[12:14]=revision.to_bytes(2,'little')
            if revision==1:b[4544:5056]=bytes(512)
            mutations=[(4248+2,1),(4280+2,1)]
            mutations += [(4248+8,1<<i) for i in range(8)]+[(4248+18,1<<i) for i in range(2)]
            mutations += [(96+(f-1)//8,1<<((f-1)%8)) for f in NEW_FORMS]
            mutations += [(4944+i//8,1<<(i%8)) for i in NEW_ITEMS]
            mutations += [(5024+i//8,1<<(i%8)) for i in range(19,25)]
            for offset,value in mutations:
                bad=bytearray(b);bad[offset]|=value;self.reset();self.put(repair_crc(bad),A);self.invalid()

    def test_south_crc_valid_source_trial_discovery_corruption_and_zero_write_snapshots(self):
        s=self.recruits();self.trial(s,0);self.reset();self.store(s)
        original=bytes(self.sram[A:A+SIZE]);slot=self.slot(s,79)
        mutations=[(4248+18,0),(4248+2,1),(4280+2,4),
                   (160+slot*24+3,0),(160+slot*24+14,2),(5024+2,0)]
        for offset,value in mutations:
            bad=bytearray(original);bad[offset]=value;self.reset();self.put(repair_crc(bad),A)
            self.invalid()
        for i in range(10):
            target=Save.from_buffer_copy(bytes(s));slot=self.slot(target,FORMS[i])
            if not target.roster.instances[slot].trial_flags:self.trial(target,i)
            if i<2:self.set_quest(target,22+i,0,0,False)
            else:target.quests.region_flags[8]&=~(1<<(i-2))
            self.reject_snapshot(target)
        for byte in (*range(3,8),*range(9,18),*range(19,32)):
            bad=Save.from_buffer_copy(bytes(s));bad.quests.region_flags[byte]=1;self.reject_snapshot(bad)
        for byte in range(3,16):
            bad=Save.from_buffer_copy(bytes(s));bad.quests.anchors[byte]=1;self.reject_snapshot(bad)

    def test_south_new_transaction_readback_corruption_preserves_old_bank(self):
        old=self.southern();self.ready(old,22);target=Save.from_buffer_copy(bytes(old))
        self.assertEqual(self.lib.southern_quest_claim(C.byref(target),22),3)
        self.reset();self.store(old);initial=bytes(self.sram)
        for offset in (12,160+11*24,160+11*24+8,4032+22//4,4048+22*2,4176+22//8,4248+2,4544+19*8,4944,5024,6143):
            self.put(initial);self.lib.save5_test_reset_writer();self.lib.save5_test_fail_after(-1)
            self.lib.save5_test_corrupt_write(offset+1 if offset<20 else offset,1)
            self.assertEqual(self.lib.save5_store(C.byref(target)),0)
            self.assertEqual(compare_state(self.load()),compare_state(old))
            self.assertEqual(bytes(self.sram[A:A+SIZE]),initial[A:A+SIZE])
        self.lib.save5_test_corrupt_write(-1,0);self.store(target)
        self.assertEqual(compare_state(self.load()),compare_state(target))

    def test_south_every_durable_cut_mixed_recruit_all_trials_evolutions_crown_migration(self):
        transitions=[]
        s=self.southern();self.ready(s,22);t=Save.from_buffer_copy(bytes(s));self.lib.southern_quest_claim(C.byref(t),22)
        transitions.append(('mixed-Q22',s,t))
        s=self.southern();self.lib.southern_visit(C.byref(s),31);t=Save.from_buffer_copy(bytes(s));self.lib.southern_field_recruit(C.byref(t),16)
        transitions.append(('field-16',s,t))
        s=self.recruits()
        for i in range(10):
            t=Save.from_buffer_copy(bytes(s));slot=self.trial(t,i);transitions.append(('trial-'+str(FORMS[i]),s,t));s=t
            t=Save.from_buffer_copy(bytes(s));self.assertEqual(self.lib.creatures_evolve(C.byref(t.roster),slot,64,1,1),0)
            transitions.append(('evolve-'+str(FORMS[i]),s,t));s=t
        self.ready(s,24);t=Save.from_buffer_copy(bytes(s));self.lib.southern_quest_claim(C.byref(t),24);transitions.append(('crown',s,t))
        for name,old,target in transitions:
            self.reset();self.store(old);initial=bytes(self.sram)
            for cut in range(SIZE+2):
                self.put(initial);self.lib.save5_test_reset_writer();self.lib.save5_test_fail_after(cut)
                ok=self.lib.save5_store(C.byref(target));self.assertEqual(ok,int(cut>=SIZE+1),(name,cut))
                self.assertEqual(compare_state(self.load()),compare_state(target if ok else old),(name,cut))
                self.assertEqual(bytes(self.sram[:A]),initial[:A]);self.assertEqual(bytes(self.sram[A:A+SIZE]),initial[A:A+SIZE])
            self.lib.save5_test_fail_after(-1);self.store(target);self.assertEqual(compare_state(self.load()),compare_state(target))
        data=(ROOT/'tests/fixtures/v5-revision3/northern-all21-town.sav').read_bytes()
        self.reset();self.put(data);old=self.load()
        for cut in range(SIZE+2):
            self.put(data);self.lib.save5_test_reset_writer();self.lib.save5_test_fail_after(cut)
            self.assertEqual(self.lib.save5_store(C.byref(old)),int(cut>=SIZE+1));self.assertEqual(compare_state(self.load()),compare_state(old))
        self.lib.save5_test_fail_after(-1)


def load_tests(loader,tests,pattern):
    return unittest.TestSuite(SouthernSaveTests(name) for name in loader.getTestCaseNames(SouthernSaveTests) if name.startswith('test_south_'))

if __name__=='__main__':unittest.main(verbosity=2)
