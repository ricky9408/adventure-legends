#!/usr/bin/env python3
"""Actual-C companion trial tests, including exhaustive puzzle-state exploration.

Run python3 tests/test_trials.py. Compiles trials.c and the real creature rules
into a temporary host shared library. Only rendering and progression's thin
engine adapters are stubbed; no puzzle/reward implementation is duplicated.
Pixel-center flood fills use trials_solid itself. Source-manifest route checks
cover existing world/campaign geometry independently of optional trial state.
This is host rule coverage, not a controller-only emulator playthrough.
"""
from collections import deque
import ctypes as C
import itertools
import json
import os
from pathlib import Path
import re
import shlex
import subprocess
import tempfile
import unittest

from test_creatures import Instance, Roster, U8
from test_save4 import CampaignSave

ROOT = Path(__file__).resolve().parents[1]
WIND, STONE = 14, 15
FACES = ((0, 1), (0, -1), (-1, 0), (1, 0))
INITIAL_PARCELS = ((88, 88), (136, 88))
PLATES = ((88, 56), (152, 104))
SOLVED_VANES = (2, 1, 0)


class Save(C.Structure):
    _fields_ = [('campaign', CampaignSave), ('roster', Roster),
                ('quest_reserved', U8 * 264), ('equipment_reserved', U8 * 512)]


class Aid(C.Structure):
    _fields_ = [('x', C.c_short), ('y', C.c_short), ('family', U8), ('event', U8)]


STUBS = r'''
#include <string.h>
#include "trials.h"
#include "progression.h"
Save5State adventure_save;
unsigned progression_forms[PROGRESSION_SPIRIT_COUNT], progression_revision;
volatile int room,px,py,spirit;
int face,frame,save_requested,save_resume_state,game_state;
volatile unsigned chapter_flags;
void progression_refresh(void) { progression_revision++; }
int progression_field(unsigned event) {
 int r=creatures_credit_event(&adventure_save.roster,384+event,100,CREATURE_CREDIT_FIELD_AID);
 if(r>0)progression_revision++;
 return r;
}
void rect(int x,int y,int w,int h,unsigned char c) {(void)x;(void)y;(void)w;(void)h;(void)c;}
void line(int x,int y,int xx,int yy,int c) {(void)x;(void)y;(void)xx;(void)yy;(void)c;}
void obj_add(int a,int b,int c,int d,int e,int f,int g,int h) {(void)a;(void)b;(void)c;(void)d;(void)e;(void)f;(void)g;(void)h;}
void obj_upload(const unsigned char *p,int w,int h,int offset) {(void)p;(void)w;(void)h;(void)offset;}
void host_reset(void) {
 memset(&adventure_save,0,sizeof adventure_save);
 creatures_migrate_legacy(&adventure_save.roster,3,0);
 adventure_save.campaign.chapter_flags=3;chapter_flags=3;
 progression_revision=trials_revision=0;room=14;px=120;py=132;spirit=0;face=0;frame=0;
 trials_enter(14);trials_enter(15);
}
static unsigned char reachable[240*160];
static int queue[240*160];
int host_reachable(int x,int y) {
 return x>=0&&x<240&&y>=0&&y<160&&reachable[y*240+x];
}
int host_flood(unsigned r,int sx,int sy) {
 int head=0,tail=0,dx[4]={0,0,-1,1},dy[4]={1,-1,0,0};
 memset(reachable,0,sizeof reachable);
 if(sx<0||sx>=240||sy<0||sy>=160||trials_solid(r,sx,sy))return 0;
 reachable[sy*240+sx]=1;queue[tail++]=sy*240+sx;
 while(head<tail) {
  int pos=queue[head++],x=pos%240,y=pos/240,k;
  for(k=0;k<4;k++) {
   int xx=x+dx[k],yy=y+dy[k],p=yy*240+xx;
   if(xx<0||xx>=240||yy<0||yy>=160||reachable[p]||trials_solid(r,xx,yy))continue;
   reachable[p]=1;queue[tail++]=p;
  }
 }
 return tail;
}
int host_free_count(unsigned r) {
 int x,y,total=0;for(y=0;y<160;y++)for(x=0;x<240;x++)total+=!trials_solid(r,x,y);return total;
}
/* Every integer-pixel push stance accepted by the documented range, with the
 * current actual-C flood fill. Restore transient state after each probe. */
unsigned host_push_probes;
int host_push_x[8],host_push_y[8];
int host_push_mask(void) {
 short initial[2][2];unsigned tr=trials_revision,pr=progression_revision;
 int dx[4]={0,0,-1,1},dy[4]={1,-1,0,0},i,f,d,s,mask=0;
 memcpy(initial,trial_parcels,sizeof initial);
 for(i=0;i<2;i++)for(f=0;f<4;f++)for(d=10;d<=21;d++)for(s=-5;s<=5;s++) {
  int x=initial[i][0]-dx[f]*d+(dy[f]?s:0);
  int y=initial[i][1]-dy[f]*d+(dx[f]?s:0),r,j;
  if(!host_reachable(x,y))continue;
  host_push_probes++;r=trials_try_push(x,y,(unsigned)f);
  if(r==1) {
   mask|=1<<(i*4+f);host_push_x[i*4+f]=x;host_push_y[i*4+f]=y;
   for(j=0;j<2;j++)if(trial_parcels[j][0]!=initial[j][0]+(j==i?16*dx[f]:0)||
                        trial_parcels[j][1]!=initial[j][1]+(j==i?16*dy[f]:0))return -1;
  }else if(memcmp(initial,trial_parcels,sizeof initial))return -2;
  memcpy(trial_parcels,initial,sizeof initial);trials_revision=tr;progression_revision=pr;
 }
 return mask;
}
'''


def build(directory):
    stub = Path(directory) / 'trial_host.c'
    stub.write_text(STUBS)
    output = Path(directory) / 'trials.so'
    subprocess.run(shlex.split(os.environ.get('HOST_CC', 'cc')) + [
        '-std=c99', '-O2', '-Wall', '-Wextra', '-Werror', '-fPIC', '-shared',
        '-I' + str(ROOT / 'src'), str(stub),
        *[str(ROOT / 'src' / name) for name in ('trials.c', 'trial_art.c', 'creatures.c', 'creature_data.c')],
        '-o', str(output)], check=True)
    lib = C.CDLL(str(output))
    signatures = {
        'host_reset': (None, []), 'host_flood': (C.c_int, [C.c_uint, C.c_int, C.c_int]),
        'host_reachable': (C.c_int, [C.c_int, C.c_int]),
        'host_free_count': (C.c_int, [C.c_uint]), 'host_push_mask': (C.c_int, []),
        'trials_enter': (None, [C.c_uint]), 'trials_is_room': (C.c_int, [C.c_uint]),
        'trials_solid': (C.c_int, [C.c_uint, C.c_int, C.c_int]),
        'trials_interact': (C.c_int, [C.c_uint, C.c_int, C.c_int, C.c_uint]),
        'trials_power': (C.c_int, [C.c_uint, C.c_int, C.c_int, C.c_uint]),
        'trials_exit': (C.c_int, [C.c_uint, C.c_int, C.c_int]),
        'trials_complete': (C.c_int, [C.c_uint]), 'trials_done': (C.c_int, [C.c_uint]),
        'trials_event_needs_save': (C.c_int, [C.c_int]),
        'trials_wind_solved': (C.c_int, []), 'trials_plate_mask': (C.c_uint, []),
        'trials_try_push': (C.c_int, [C.c_int, C.c_int, C.c_uint]),
        'trials_background': (C.POINTER(U8), [C.c_uint]),
        'trials_room_name': (C.c_char_p, [C.c_uint]),
        'creatures_roster_init': (None, [C.POINTER(Roster)]),
        'creatures_migrate_legacy': (C.c_int, [C.POINTER(Roster), C.c_uint, C.c_uint]),
        'creatures_grant': (C.c_uint, [C.POINTER(Roster)] + [C.c_uint] * 5),
        'creatures_roster_validate': (C.c_int, [C.POINTER(Roster)]),
        'creatures_begin_expedition': (None, [C.POINTER(Roster)]),
    }
    for name, (result, arguments) in signatures.items():
        fn = getattr(lib, name)
        fn.restype, fn.argtypes = result, arguments
    return lib


def events_from_header():
    body = re.search(r'enum TrialEvent\s*\{(.*?)\}',
                     (ROOT / 'src/trials.h').read_text(), re.S).group(1)
    values, value = {}, 0
    for entry in body.split(','):
        name, *assigned = entry.strip().split('=')
        if assigned:
            value = int(assigned[0].strip(), 0)
        values[name.strip()] = value
        value += 1
    return values


def reachable_pixels(width, height, start, blocked):
    """Independent manifest geometry BFS; returns packed integer coordinates."""
    legal = bytearray(width * height)
    for y in range(height):
        for x in range(width):
            legal[y * width + x] = not blocked(x, y)
    root = start[1] * width + start[0]
    if not legal[root]:
        return set()
    queue, seen = deque([root]), {root}
    while queue:
        point = queue.popleft()
        x, y = point % width, point // width
        for xx, yy in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= xx < width and 0 <= yy < height:
                target = yy * width + xx
                if legal[target] and target not in seen:
                    seen.add(target)
                    queue.append(target)
    return seen


class TrialTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='emberbond-trial-host-')
        cls.addClassCleanup(cls.tmp.cleanup)
        cls.lib = build(cls.tmp.name)
        cls.events = events_from_header()
        cls.save = Save.in_dll(cls.lib, 'adventure_save')
        cls.vanes = (U8 * 3).in_dll(cls.lib, 'trial_vanes')
        cls.parcels = ((C.c_short * 2) * 2).in_dll(cls.lib, 'trial_parcels')
        cls.revision = C.c_uint.in_dll(cls.lib, 'trials_revision')
        cls.progress_revision = C.c_uint.in_dll(cls.lib, 'progression_revision')
        cls.aids = (Aid * 6).in_dll(cls.lib, 'trial_grove_aids')

    def setUp(self):
        self.lib.host_reset()

    def event(self, name):
        return self.events['TRIAL_' + name]

    def state(self):
        return tuple(tuple(p) for p in self.parcels)

    def put_parcels(self, state):
        for i, point in enumerate(state):
            self.parcels[i][:] = point

    def reservations(self):
        return bytes(self.save.quest_reserved), bytes(self.save.equipment_reserved)

    def test_optional_room_identity_and_backgrounds(self):
        for room in range(18):
            self.assertEqual(bool(self.lib.trials_is_room(room)), room in (WIND, STONE))
            background = self.lib.trials_background(room)
            if room in (WIND, STONE):
                self.assertTrue(background)
                self.assertTrue(self.lib.trials_room_name(room))
                self.assertNotIn(0, C.string_at(background, 240 * 160), 'background must be opaque')
            else:
                self.assertFalse(background)

    def test_exported_geometry_and_lifetime_bit_ownership(self):
        self.assertEqual([(a.x, a.y, a.family, a.event) for a in self.aids],
                         [(184, 280, 0, 0), (296, 208, 0, 1), (320, 72, 0, 2),
                          (80, 136, 1, 3), (400, 136, 1, 4), (304, 280, 1, 5)])
        vanes = ((C.c_short * 2) * 3).in_dll(self.lib, 'trial_vane_centers')
        plates = ((C.c_short * 2) * 2).in_dll(self.lib, 'trial_plate_centers')
        self.assertEqual([tuple(p) for p in vanes], [(88, 64), (88, 112), (168, 112)])
        self.assertEqual(tuple(tuple(p) for p in plates), PLATES)
        self.assertEqual(self.state(), INITIAL_PARCELS)

    def test_wind_exhaustive_64_states_rotations_reset_and_exit(self):
        solved, rotations = [], 0
        pristine = bytes(self.save)
        for state in itertools.product(range(4), repeat=3):
            self.vanes[:] = state
            if self.lib.trials_wind_solved():
                solved.append(state)
            # Vane orientation cannot wall off the hero, reset or south exit.
            self.assertEqual(self.lib.host_flood(WIND, 120, 132), self.lib.host_free_count(WIND))
            self.assertTrue(self.lib.host_reachable(32, 120))
            self.assertTrue(self.lib.host_reachable(120, 144))
            self.assertEqual(self.lib.trials_exit(WIND, 120, 144), 4)
            for index, point in enumerate(((88, 64), (88, 112), (168, 112))):
                C.memmove(C.byref(self.save), pristine, C.sizeof(Save))
                self.vanes[:] = state
                before = bytes(self.vanes)
                self.assertEqual(self.lib.trials_interact(WIND, *point, 0), self.event('INSPECT'))
                self.assertEqual(bytes(self.vanes), before)
                expected = list(state)
                expected[index] = (expected[index] + 1) % 4
                result = self.lib.trials_power(WIND, *point, 2)
                self.assertEqual(result, self.event('COMPLETE_FUURI') if tuple(expected) == SOLVED_VANES else self.event('ROTATED'))
                self.assertEqual(list(self.vanes), expected)
                rotations += 1
            C.memmove(C.byref(self.save), pristine, C.sizeof(Save))
            self.vanes[:] = state
            self.assertEqual(self.lib.trials_interact(WIND, 32, 120, 0), self.event('RESET'))
            reset = bytes(self.vanes)
            self.assertEqual(self.lib.trials_interact(WIND, 32, 120, 0), self.event('RESET'))
            self.assertEqual(bytes(self.vanes), reset)
            for i in range(3):
                self.vanes[i] = (self.vanes[i] + 1) % 4
            self.lib.trials_enter(WIND)
            self.assertEqual(bytes(self.vanes), reset)
        self.assertEqual(solved, [SOLVED_VANES])
        self.assertEqual(rotations, 192)
        print('  wind: all 64 orientations, 192 rotations, reset and exit reachability verified')

    def test_amber_exhaustive_pixel_reachable_push_states(self):
        # A state is the two labeled parcels plus the player walk component.
        # The actual-C pixel flood proves every non-solid pixel belongs to the
        # spawn component in EACH visited state, so no component key is lost.
        queue, seen, solved = deque([INITIAL_PARCELS]), {INITIAL_PARCELS}, set()
        edges = 0
        stands_x = (C.c_int * 8).in_dll(self.lib, 'host_push_x')
        stands_y = (C.c_int * 8).in_dll(self.lib, 'host_push_y')
        C.c_uint.in_dll(self.lib, 'host_push_probes').value = 0
        while queue:
            state = queue.popleft()
            self.put_parcels(state)
            count = self.lib.host_flood(STONE, 120, 132)
            self.assertGreater(count, 0, state)
            self.assertEqual(count, self.lib.host_free_count(STONE), state)
            self.assertTrue(self.lib.host_reachable(32, 120), state)
            self.assertTrue(self.lib.host_reachable(120, 144), state)
            self.assertEqual(self.lib.trials_exit(STONE, 120, 144), 9)
            mask = self.lib.host_push_mask()
            self.assertGreaterEqual(mask, 0, ('pixel push corruption', state, mask))
            observed_mask = 0
            for i, parcel in enumerate(state):
                for face, (dx, dy) in enumerate(FACES):
                    self.put_parcels(state)
                    key = i * 4 + face
                    if not (mask & (1 << key)):
                        continue
                    stand = stands_x[key], stands_y[key]
                    self.assertTrue(self.lib.host_reachable(*stand))
                    before = bytes(self.save)
                    revision = self.revision.value
                    result = self.lib.trials_try_push(*stand, face)
                    self.assertEqual(bytes(self.save), before, 'pushing must not write persistent state')
                    if result == 1:
                        observed_mask |= 1 << (i * 4 + face)
                        expected = list(state)
                        expected[i] = parcel[0] + dx * 16, parcel[1] + dy * 16
                        self.assertEqual(self.state(), tuple(expected))
                        self.assertGreater(self.revision.value, revision)
                        new = self.state()
                        self.assertNotEqual(new[0], new[1])
                        for x, y in new:
                            self.assertIn(x, range(72, 169, 16))
                            self.assertIn(y, range(56, 105, 16))
                        edges += 1
                        if new not in seen:
                            seen.add(new)
                            queue.append(new)
                    else:
                        self.assertIn(result, (-1, 0))
                        self.assertEqual(self.state(), state)
                        self.assertEqual(self.revision.value, revision)
            self.assertEqual(mask, observed_mask, ('pixel stance transition was not reproduced', state))
            self.put_parcels(state)
            expected_plates = sum(1 << n for n, plate in enumerate(PLATES) if plate in state)
            self.assertEqual(self.lib.trials_plate_mask(), expected_plates)
            if expected_plates == 3:
                solved.add(state)
            self.assertEqual(self.lib.trials_interact(STONE, 32, 120, 0), self.event('RESET'))
            self.assertEqual(self.state(), INITIAL_PARCELS)
            self.lib.trials_interact(STONE, 32, 120, 0)
            self.assertEqual(self.state(), INITIAL_PARCELS)
            self.put_parcels(state)
            self.lib.trials_enter(STONE)
            self.assertEqual(self.state(), INITIAL_PARCELS)
        self.assertEqual(len(seen), 28 * 27, 'all non-overlapping labeled board placements must be reachable')
        self.assertEqual(solved, {PLATES, tuple(reversed(PLATES))})
        probes = C.c_uint.in_dll(self.lib, 'host_push_probes').value
        self.assertGreater(probes, 10000)
        print(f'  amber: {len(seen)} reachable labeled parcel states, {edges} push edges, '
              f'{probes} integer-pixel push stances; every state can reset and exit')

    def test_amber_push_alignment_boundaries_and_blocked_atomicity(self):
        for face, (dx, dy) in enumerate(FACES):
            for distance, side in itertools.product((9, 10, 11, 16, 21, 22), (-6, -5, 0, 5, 6)):
                self.put_parcels(((120, 72), (168, 104)))
                x = 120 - dx * distance + (side if dy else 0)
                y = 72 - dy * distance + (side if dx else 0)
                before = self.state()
                result = self.lib.trials_try_push(x, y, face)
                self.assertEqual(result, 1 if 10 <= distance <= 21 and abs(side) <= 5 else 0,
                                 (face, distance, side))
                if result != 1:
                    self.assertEqual(self.state(), before)
        for parcels, x, y, face in [(((72, 72), (136, 88)), 88, 72, 2),
                                     (((168, 72), (136, 88)), 152, 72, 3),
                                     (((120, 56), (136, 88)), 120, 72, 1),
                                     (((120, 104), (136, 88)), 120, 88, 0),
                                     (((104, 72), (120, 72)), 88, 72, 3)]:
            self.put_parcels(parcels)
            before = bytes(self.save), self.state(), self.revision.value
            self.assertEqual(self.lib.trials_try_push(x, y, face), -1)
            self.assertEqual((bytes(self.save), self.state(), self.revision.value), before)

    def test_story_companion_reward_once_bond_cap_independent_of_expedition(self):
        for family in range(4):
            for bond in (20, 95, 100):
                self.lib.host_reset()
                creature = self.save.roster.instances[family]
                creature.bond = bond
                self.save.roster.expedition_bond[family] = 10
                # Sentinel allocations detect accidental save5 reservation use.
                self.save.quest_reserved[:] = bytes([0xA5]) * 264
                self.save.equipment_reserved[:] = bytes([0x5A]) * 512
                reservations = self.reservations()
                others = [bytes(c) for i, c in enumerate(self.save.roster.instances) if i != family]
                xp = creature.xp
                self.assertFalse(self.lib.trials_done(family))
                self.assertEqual(self.lib.trials_complete(family), self.event('COMPLETE_HOMURA') + family)
                self.assertEqual(creature.bond, min(100, bond + 10))
                self.assertEqual(creature.trial_flags, 1 << family)
                self.assertGreater(creature.xp, xp)
                self.assertLessEqual(creature.xp - xp, 1000, 'trial XP must stay modest')
                self.assertEqual(self.save.roster.expedition_bond[family], 10)
                self.assertEqual([bytes(c) for i, c in enumerate(self.save.roster.instances) if i != family], others)
                self.assertEqual(self.reservations(), reservations)
                self.assertTrue(self.lib.trials_done(family))
                before = bytes(self.save), self.revision.value, self.progress_revision.value
                self.assertEqual(self.lib.trials_complete(family), self.event('ALREADY_DONE'))
                self.assertEqual((bytes(self.save), self.revision.value, self.progress_revision.value), before)
                self.lib.trials_enter(WIND)
                self.lib.trials_enter(STONE)
                self.assertTrue(self.lib.trials_done(family))
                self.lib.creatures_begin_expedition(C.byref(self.save.roster))
                before = bytes(self.save)
                self.assertEqual(self.lib.trials_complete(family), self.event('ALREADY_DONE'))
                self.assertEqual(bytes(self.save), before)

    def test_reward_finds_story_locked_family_not_first_party_position(self):
        self.lib.creatures_roster_init(C.byref(self.save.roster))
        for form in (1, 4, 7, 10):
            self.lib.creatures_grant(C.byref(self.save.roster), form, 20, 20, 0, 0)
        for family, form in enumerate((1, 4, 7, 10)):
            slot = self.lib.creatures_grant(C.byref(self.save.roster), form, 20, 20, 2, family + 1)
            original = bytes(self.save.roster.instances[slot])
            C.memmove(C.byref(self.save.roster.instances[40 + family]), original, C.sizeof(Instance))
            C.memset(C.byref(self.save.roster.instances[slot]), 0, C.sizeof(Instance))
        self.assertEqual(self.lib.creatures_roster_validate(C.byref(self.save.roster)), 1)
        for family in range(4):
            ordinary = bytes(self.save.roster.instances[family])
            target = self.save.roster.instances[40 + family]
            bond = target.bond
            self.lib.trials_complete(family)
            self.assertEqual(bytes(self.save.roster.instances[family]), ordinary)
            self.assertEqual(target.bond, bond + 10)
            self.assertEqual(target.trial_flags, 1 << family)
        for family in range(4):
            self.lib.host_reset()
            self.save.roster.instances[family].flags &= ~2
            before = bytes(self.save)
            self.assertEqual(self.lib.trials_complete(family), self.event('NONE'))
            self.assertEqual(bytes(self.save), before)
        for family in (4, 255, 0xffffffff):
            before = bytes(self.save)
            self.assertEqual(self.lib.trials_complete(family), self.event('NONE'))
            self.assertFalse(self.lib.trials_done(family))
            self.assertEqual(bytes(self.save), before)

    def test_grove_restorations_are_permanent_and_wrong_power_is_atomic(self):
        for index, aid in enumerate(self.aids):
            for wrong in set(range(4)) - {aid.family}:
                before = bytes(self.save)
                self.assertEqual(self.lib.trials_power(1, aid.x, aid.y, wrong), self.event('WRONG_POWER'))
                self.assertEqual(bytes(self.save), before)
            event = self.lib.trials_power(1, aid.x, aid.y, aid.family)
            self.assertIn(event, (self.event('RESTORED'), self.event('COMPLETE_HOMURA') + aid.family))
            self.assertTrue(self.save.roster.lifetime_field_aid[0] & (1 << index))
            before = bytes(self.save)
            self.lib.trials_power(1, aid.x, aid.y, aid.family)
            self.assertEqual(bytes(self.save), before)
            self.lib.creatures_begin_expedition(C.byref(self.save.roster))
            before = bytes(self.save)
            self.lib.trials_power(1, aid.x, aid.y, aid.family)
            self.assertEqual(bytes(self.save), before)
        self.assertEqual(self.save.roster.lifetime_field_aid[0] & 63, 63)
        self.assertTrue(self.lib.trials_done(0))
        self.assertTrue(self.lib.trials_done(1))
        self.assertEqual(self.reservations(), (bytes(264), bytes(512)))

    def test_wind_and_amber_completion_record_field_bits_once(self):
        for room, family, bit in ((WIND, 2, 6), (STONE, 3, 7)):
            self.lib.host_reset()
            # Fill the usual expedition bond allowance before the personal
            # reward; completing the trial must still add its independent ten.
            for i in range(4):
                self.save.roster.expedition_bond[i] = 10
            self.save.roster.instances[family].bond = 85
            if room == WIND:
                self.vanes[:] = (1, 1, 0)
                point = (88, 64)
            else:
                self.put_parcels(PLATES)
                point = (200, 64)
            before_xp = [c.xp for c in self.save.roster.instances[:4]]
            before_bond = [c.bond for c in self.save.roster.instances[:4]]
            for wrong in set(range(4)) - {family}:
                before = bytes(self.save), bytes(self.vanes), self.state()
                self.assertEqual(self.lib.trials_power(room, *point, wrong), self.event('WRONG_POWER'))
                self.assertEqual((bytes(self.save), bytes(self.vanes), self.state()), before)
            self.assertEqual(self.lib.trials_power(room, *point, family), self.event('COMPLETE_HOMURA') + family)
            self.assertEqual(self.save.roster.lifetime_field_aid[0], 1 << bit)
            for i in range(4):
                self.assertEqual(self.save.roster.instances[i].xp - before_xp[i], 280 if i == family else 100)
                self.assertEqual(self.save.roster.instances[i].bond - before_bond[i], 10 if i == family else 0)
                self.assertEqual(self.save.roster.expedition_bond[i], 10)
            before = bytes(self.save)
            self.assertEqual(self.lib.trials_power(room, *point, family), self.event('ALREADY_DONE'))
            self.lib.trials_enter(room)
            self.assertEqual(self.lib.trials_interact(room, 32, 120, 0), self.event('ALREADY_DONE'))
            self.assertEqual(bytes(self.save), before)
            if room == WIND:
                self.assertEqual(tuple(self.vanes), SOLVED_VANES)
            else:
                self.assertEqual(self.state(), PLATES)
                completed = bytes(self.save), self.state(), self.revision.value, self.progress_revision.value
                for x, y, facing in ((88, 72, 1), (136, 104, 3)):
                    self.assertEqual(self.lib.trials_interact(STONE, x, y, facing), self.event('ALREADY_DONE'))
                    self.assertEqual((bytes(self.save), self.state(), self.revision.value, self.progress_revision.value), completed)
                self.assertEqual(self.lib.trials_interact(STONE, 32, 120, 0), self.event('ALREADY_DONE'))
                self.assertEqual((bytes(self.save), self.state(), self.revision.value, self.progress_revision.value), completed)
            self.lib.creatures_begin_expedition(C.byref(self.save.roster))
            before = bytes(self.save)
            self.assertEqual(self.lib.trials_power(room, *point, family), self.event('ALREADY_DONE'))
            self.assertEqual(bytes(self.save), before)

    def test_interaction_power_exit_and_collision_boundaries(self):
        aid = self.aids[0]
        for distance in (22, 23, 27, 28):
            self.lib.host_reset()
            self.assertEqual(self.lib.trials_interact(1, aid.x + distance, aid.y, 0),
                             self.event('INSPECT') if distance < 23 else self.event('NONE'))
            self.assertEqual(self.lib.trials_power(1, aid.x + distance, aid.y, 0),
                             self.event('RESTORED') if distance < 28 else self.event('NONE'))
        for room, exit_room in ((WIND, 4), (STONE, 9)):
            for x in (107, 108, 120, 132, 133):
                for y in (139, 140, 147, 148):
                    self.assertEqual(self.lib.trials_exit(room, x, y),
                                     exit_room if 108 <= x <= 132 and 140 <= y < 148 else -1)
            for x, y, blocked in ((11, 132, 1), (12, 132, 0), (227, 132, 0),
                                   (228, 132, 1), (120, 43, 1), (120, 44, 0),
                                   (120, 147, 0), (120, 148, 1)):
                self.assertEqual(bool(self.lib.trials_solid(room, x, y)), bool(blocked))
        self.put_parcels(INITIAL_PARCELS)
        for dx in range(-12, 13):
            for dy in range(-12, 13):
                self.assertEqual(bool(self.lib.trials_solid(STONE, 88 + dx, 88 + dy)),
                                 abs(dx) < 11 and abs(dy) < 11)
        before = self.state()
        self.assertEqual(self.lib.trials_try_push(88, 104, 4), 0)
        self.assertEqual(self.state(), before)
        self.assertEqual(self.lib.trials_power(STONE, 200, 64, 3), self.event('NEED_PLATES'))
        for name, event in self.events.items():
            self.assertEqual(bool(self.lib.trials_event_needs_save(event)),
                             name == 'TRIAL_RESTORED' or name.startswith('TRIAL_COMPLETE_'))

    def test_existing_world_routes_and_aid_points_remain_reachable(self):
        manifest = json.loads((ROOT / 'assets/world_manifest.json').read_text())
        rects = manifest['static_collision_rectangles']
        river = manifest['dynamic_rectangles'][0]
        rx, ry, rw, rh = river['rect']
        bx, by, bw, bh = river['exception_when_bridge_open']
        def blocked(x, y):
            if x < 12 or x >= 468 or y < 24 or y >= 308:
                return True
            if any(xx <= x < xx + w and yy <= y < yy + h for xx, yy, w, h in rects):
                return True
            return rx <= x < rx + rw and ry <= y < ry + rh and not (bx <= x < bx + bw and by <= y < by + bh)
        visited = reachable_pixels(480, 320, tuple(manifest['landmarks']['spawn']), blocked)
        targets = [(a.x, a.y) for a in self.aids] + [tuple(p) for p in manifest['landmarks'].values()]
        for x, y in targets:
            self.assertIn(y * 480 + x, visited, (x, y))
            self.assertFalse(self.lib.trials_solid(1, x, y), 'trial scenery must add no world collision')
        for aid in self.aids:
            self.lib.trials_power(1, aid.x, aid.y, aid.family)
        for x, y in targets:
            self.assertFalse(self.lib.trials_solid(1, x, y))

    def test_campaign_entrances_returns_and_mandatory_routes_with_foot_expansion(self):
        rooms = {r['id']: r for r in json.loads((ROOT / 'assets/campaign_layouts.json').read_text())['rooms']}
        for room, entrance, arrival, event in ((4, (204, 64), (204, 86), 'ENTER_WIND'),
                                               (9, (208, 120), (208, 140), 'ENTER_STONE')):
            spec = rooms[room]
            for arch_open in (False, True):
                rects = list(spec['static_solids'])
                if not arch_open:
                    rects += [r['rect'] for r in spec['dynamic_solids']]
                def blocked(x, y):
                    if x < 12 or x >= 228 or y < 32 or y >= 148:
                        return True
                    return any(rx - 4 <= x < rx + w + 4 and ry - 4 <= y < ry + h + 4
                               for rx, ry, w, h in rects)
                visited = reachable_pixels(240, 160, (120, 132), blocked)
                for x, y in (entrance, arrival, (120, 144)):
                    self.assertIn(y * 240 + x, visited, (room, arch_open, (x, y)))
                    self.assertFalse(self.lib.trials_solid(room, x, y))
                self.assertEqual(36 * 240 + 120 in visited, room == 4 or arch_open)
                self.assertEqual(self.lib.trials_interact(room, *entrance, 0), self.event('NONE'), 'A no longer duplicates the authored walking doorway')
            for dx, dy in ((18, 0), (0, 18), (9, 9)):
                self.assertEqual(self.lib.trials_interact(room, entrance[0] + dx, entrance[1] + dy, 0), self.event('NONE'), 'nearby A input must not warp into a trial')
            for dx, dy in ((19, 0), (0, 19), (10, 9)):
                self.assertNotEqual(self.lib.trials_interact(room, entrance[0] + dx, entrance[1] + dy, 0), self.event(event))


if __name__ == '__main__':
    unittest.main(verbosity=2)
