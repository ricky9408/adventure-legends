"""Portable orchestration checks; fake controller transport, no game claim."""
import ctypes as C
import unittest
from current_field_controls import CurrentFieldControls, FIELD_PICKER_HOLD_UPDATES


class Member(C.Structure):
    _fields_=[('flags',C.c_ubyte),('form_id',C.c_ushort),('instance_id',C.c_ushort)]


class Roster(C.Structure):
    _fields_=[('instances',Member*160),('party',C.c_ubyte*4),('selected_party',C.c_ubyte)]


class Transport(CurrentFieldControls):
    """Model only enough selector protocol to reject wrong physical buttons."""
    def __init__(self):
        self.live=Roster();self.live.party[:]=(0,7,29,41)
        for i in (0,7,29,41,159):
            self.live.instances[i]=Member(1,1,i+1)
        self.values={'game_state':1,'quickparty_open':0,'quickparty_visible':0,'quickparty_candidate':255,'summoned':0}
        self.inputs=[];self.held=set();self.arming=0;self.e=type('Clock',(),{'frame':0})()

    def get(self,name):return self.values[name]
    def roster(self):return self.live
    def tap(self,key,hold=2,release=2):self.step(hold,key);self.step(release)
    def step(self,frames,keys=0):
        self.inputs.append((frames,keys))
        held=set(keys.split('+')) if keys else set()
        pressed=held-self.held;self.e.frame+=frames
        if self.values['quickparty_open']:
            if 'B' in pressed:
                self.values['quickparty_open']=self.values['quickparty_visible']=0
                self.arming=0
            elif 'L' not in held:
                if not self.values['quickparty_visible']:
                    self.live.selected_party=(self.live.selected_party+1)%4
                else:
                    index=self.values['quickparty_candidate'];party=list(self.live.party)
                    if index in party:self.live.selected_party=party.index(index)
                    else:self.live.party[self.live.selected_party]=index
                self.values['quickparty_open']=self.values['quickparty_visible']=0
                self.arming=0
            elif not self.values['quickparty_visible']:
                self.arming+=frames
                if self.arming>=FIELD_PICKER_HOLD_UPDATES:
                    self.values['quickparty_visible']=1
                    self.values['quickparty_candidate']=self.live.party[self.live.selected_party]
            elif len(pressed&{'LEFT','RIGHT'})==1:
                owned=[i for i,m in enumerate(self.live.instances) if m.flags&1]
                at=owned.index(self.values['quickparty_candidate'])
                self.values['quickparty_candidate']=owned[(at+(1 if 'RIGHT' in pressed else -1))%len(owned)]
        elif 'L' in pressed:
            self.values['quickparty_open']=1;self.values['quickparty_visible']=0
            self.values['quickparty_candidate']=255;self.arming=frames
            if frames>=FIELD_PICKER_HOLD_UPDATES:
                self.values['quickparty_visible']=1
                self.values['quickparty_candidate']=self.live.party[self.live.selected_party]
        elif self.values['game_state']==1:
            if 'R' in pressed:self.values['summoned']^=1
            elif 'B' in pressed:self.values['summoned']=1
        self.held=held


class CurrentControlTransportTests(unittest.TestCase):
    def test_explicit_field_actions_emit_physical_buttons(self):
        route=Transport();route.field_ability(3,4)
        self.assertEqual(route.inputs,[(3,'B'),(4,0)])
        route.set_summoned(False)
        self.assertEqual(route.inputs[-2:],[(2,'R'),(2,0)])
        route.hold_field_ability(7)
        self.assertEqual(route.inputs[-1],(7,'B'))

    def test_field_helpers_cannot_remap_menu_cancellation(self):
        route=Transport();route.values['game_state']=3
        with self.assertRaisesRegex(AssertionError,'actual PLAY'):route.field_ability()
        with self.assertRaisesRegex(AssertionError,'actual PLAY'):route.set_summoned(True)
        route.tap('B')
        self.assertEqual(route.inputs,[(2,'B'),(2,0)])

    def test_presence_change_releases_a_previous_raw_r_hold(self):
        route=Transport();route.step(1,'R')
        route.set_summoned(False)
        self.assertEqual(route.inputs[-3:],[(1,0),(2,'R'),(2,0)])
        self.assertFalse(route.get('summoned'))

    def test_reserve_and_duplicate_form_identity_use_carousel_buttons(self):
        route=Transport();before=bytes(route.live.instances)
        route.select_owned_identity(160)
        self.assertEqual(route.live.party[route.live.selected_party],159)
        self.assertEqual(bytes(route.live.instances),before)
        self.assertTrue(any(keys in ('L+LEFT','L+RIGHT') for _,keys in route.inputs))
        self.assertFalse(any(keys in ('L+UP','L+DOWN','A','R') for _,keys in route.inputs))
        self.assertEqual(route.field_control_events[-1]['instance_id'],160)
        route.select_owned_instance(29)
        self.assertEqual(route.live.selected_party,2)
        self.assertEqual(list(route.live.party),[159,7,29,41])

    def test_long_hold_current_individual_never_short_cycles(self):
        route=Transport();before=bytes(route.live)
        route.select_owned_instance(0)
        self.assertEqual(bytes(route.live),before)
        self.assertEqual([entry for entry in route.inputs if entry[1]=='L'],[(1,'L')]*13)
        self.assertFalse(any(isinstance(keys,str) and '+' in keys for _,keys in route.inputs))
        with self.assertRaisesRegex(AssertionError,'not owned'):route.select_owned_instance(158)
        route.step(12,'L');self.assertFalse(route.get('quickparty_visible'))
        route.step(1);self.assertEqual(route.live.selected_party,1)
        self.assertEqual(list(route.live.party),[0,7,29,41])


if __name__=='__main__':unittest.main(verbosity=2)
