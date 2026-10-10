#!/usr/bin/env python3
"""Read-only story handoffs, distinct from earned controller progression."""
import ctypes as C
import json
from pathlib import Path
import re
import subprocess
import tempfile
import unittest
from test_save5 import Save

ROOT = Path(__file__).resolve().parents[1]

class Goal(C.Structure):
    _fields_ = [('title', C.c_int), ('detail', C.c_int),
                ('target', C.c_uint), ('stage', C.c_uint)]

class JourneyGoals(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory(prefix='journey-goals-')
        cls.addClassCleanup(cls.tmp.cleanup)
        folder = Path(cls.tmp.name)
        support = folder / 'support.c'
        support.write_text('#include "save5.h"\nunsigned save5_quest_state(const Save5Quests*q,unsigned n){return n<64?(q->states[n>>2]>>((n&3)*2))&3:0;}\n')
        so = folder / 'goals.so'
        subprocess.run(['cc', '-shared', '-fPIC', '-O2', '-std=c99',
                        '-Wall', '-Wextra', '-Werror', '-I'+str(ROOT/'src'),
                        str(ROOT/'src/journey_goal.c'), str(support), '-o', str(so)], check=True)
        cls.lib = C.CDLL(str(so))
        cls.lib.journey_goal_read.argtypes = [C.POINTER(Save), C.c_uint, C.c_uint]
        cls.lib.journey_goal_read.restype = Goal
        ids = list(dict.fromkeys(re.findall(r'\bTX_[A-Z0-9_]+\b', (ROOT/'src/ui.h').read_text())))
        cls.names = dict(enumerate(ids))

    def claimed(self, s, q):
        s.quests.states[q >> 2] |= 3 << ((q & 3) * 2)

    def goal(self, s, flags=15, room=0):
        before = bytes(s)
        g = self.lib.journey_goal_read(C.byref(s), flags, room)
        self.assertEqual(bytes(s), before, 'Browsing must not change complete Save5 state')
        self.assertLess(g.target, 78)
        self.assertTrue(self.names[g.title].startswith(('TX_JG_', 'TX_C_QUEST_')))
        self.assertTrue(self.names[g.detail].startswith('TX_JG_'))
        return g

    def test_celebration_is_a_chapter_handoff(self):
        copy = json.loads((ROOT/'assets/journey_guidance_ui.json').read_text())
        self.assertNotIn('THE END', copy['C_FINAL_SMALL'])
        self.assertNotIn('終章', copy['C_CHAPTER3_CLEAR'])
        self.assertIn('続く', copy['THANKS'])
        self.assertTrue(copy['C_POSTGAME'].startswith('A '))
        source = (ROOT/'src/game.c').read_text()
        # Source integration contract only. Native endroll and independent
        # state tests separately establish released-key behavior and save I/O.
        handoff = 'if(game_state==WIN){if(ending_credits_update()){game_state=PLAY;enter_room(0,3);}return;}'
        first_ending = 'if(!(chapter_flags&SAVE4_ENDING_SEEN)){chapter_flags|=SAVE4_ENDING_SEEN;completed=1;save_at(0,3);}game_state=WIN;ending_credits_begin();'
        def integrated(text):
            return text.count(handoff) == 1 and text.count(first_ending) == 1
        self.assertTrue(integrated(source))
        mutations = [
            (first_ending, first_ending.replace('if(!(chapter_flags&SAVE4_ENDING_SEEN))', 'if(1)')),
            (first_ending, first_ending.replace('save_at(0,3);', '')),
            (first_ending, first_ending.replace('ending_credits_begin();', '')),
            (handoff, handoff.replace('enter_room(0,3)', 'enter_room(1,3)')),
            (handoff, handoff.replace('ending_credits_update()', 'pressed&(KEY_A|KEY_START)')),
        ]
        for before, after in mutations:
            with self.subTest(mutation=after):
                changed = source.replace(before, after, 1)
                self.assertNotEqual(changed, source)
                self.assertFalse(integrated(changed))

    def test_original_and_new_region_knowledge(self):
        s = Save()
        self.assertEqual(self.goal(s, 0).target, 1)
        self.assertEqual(self.goal(s, 1).target, 4)
        self.assertEqual(self.goal(s, 3).target, 9)
        self.assertEqual(self.goal(s, 7).title, self.id('TX_JG_ELDER'))
        self.assertEqual(self.goal(s, 15).target, 16)
        s.quests.region_flags[0] = 1
        self.assertEqual(self.goal(s).target, 17)
        self.claimed(s, 2)
        self.assertEqual(self.goal(s).target, 18)
        self.claimed(s, 3)
        self.assertEqual(self.goal(s).target, 22)

    def id(self, name):
        return next(n for n, text in self.names.items() if text == name)

    def test_revisits_follow_actual_regional_progress(self):
        for completed, target, stage in ((21,30,3),(24,38,4),(32,46,5),(40,46,6),(51,60,7)):
            s = Save(); self.claimed(s, completed)
            for room in (0,1,16,22,30,38,46,54,60):
                g = self.goal(s, room=room)
                self.assertEqual((g.target,g.stage),(target,stage))

    def test_region_before_original_ending_keeps_work(self):
        s = Save(); s.quests.region_flags[1] = 1
        self.assertEqual(self.goal(s,7,0).title,self.id('TX_JG_ELDER'))
        self.assertEqual(self.goal(s,7,22).title,self.id('TX_JG_CARGO'))
        self.claimed(s,57)
        self.assertEqual(self.goal(s,7,62).title,self.id('TX_JG_ELDER'))
        self.assertEqual(self.goal(s,15,62).detail,self.id('TX_JG_ELDER_NEW'))

    def test_return_main_steps_and_reports(self):
        s=Save();self.claimed(s,40)
        self.assertEqual(self.goal(s).title,self.id('TX_JG_RECORD_COPY'))
        s.quests.objectives[46]=1
        self.assertEqual(self.goal(s).target,0)
        self.claimed(s,46)
        self.assertEqual(self.goal(s).target,54)
        s.quests.region_flags[5]=1
        self.assertEqual(self.goal(s).target,16)
        for q,target in ((47,30),(49,22),(48,16),(50,60)):
            self.claimed(s,q);self.assertEqual(self.goal(s).target,target)
        s.quests.objectives[51]=3
        self.assertEqual(self.goal(s).target,61)
        s.quests.objectives[51]=7
        self.assertEqual(self.goal(s).detail,self.id('TX_JG_MAP_REPORT'))

    def test_finished_fights_point_to_claim_not_dungeon_entrance(self):
        # Native handlers claim21 at crown29 or the town22 NPC; claim24 at
        # crown37,32 with Ressa38 and40 with the keeper46. READY is not CLAIMED.
        for prior, q, target, expected in ((21,24,37,'TX_JG_SUNWELL_REPORT'),
                (24,32,38,'TX_JG_RESSA_REPORT'),
                (32,40,46,'TX_JG_KEEPER_REPORT')):
            s=Save();self.claimed(s,prior)
            first={24:22,32:30,40:38}[q]
            self.claimed(s,first);self.claimed(s,first+1)
            region={24:2,32:3,40:4}[q];s.quests.region_flags[region]=1
            s.quests.states[q>>2]|=2<<((q&3)*2)
            for room in (0,16,22,30,38,46):
                g=self.goal(s,room=room)
                self.assertEqual((g.target,g.title),(target,self.id(expected)))
        s=Save();s.quests.region_flags[1]=1
        self.claimed(s,11);self.claimed(s,13)
        s.quests.states[21>>2]|=2<<((21&3)*2)
        self.assertEqual(self.goal(s,room=29).target,29)
        self.assertEqual(self.goal(s,room=0).target,22)

    def test_final_work_choice_and_completed_homecoming(self):
        s=Save();self.claimed(s,57)
        for bit,target in ((0,0),(1,62),(3,70)):
            s.quests.objectives[60]=bit
            self.assertEqual(self.goal(s).target,target)
        for q,target in ((60,70),(61,74),(62,70)):
            self.claimed(s,q);self.assertEqual(self.goal(s).target,target)
        s.quests.objectives[63]=1
        self.assertEqual(self.goal(s).target,62)
        s.quests.objectives[63]=3
        self.assertEqual(self.goal(s).target,0)
        self.claimed(s,63)
        for room in range(78):
            g=self.goal(s,room=room)
            self.assertEqual((g.stage,g.title),(9,self.id('TX_JG_HOME')))

    def test_no_future_reward_or_puzzle_solution_copy(self):
        text=json.loads((ROOT/'assets/journey_guidance_ui.json').read_text())
        self.assertIn('東',text['JG_HEARTHWAKE_DETAIL'])
        self.assertIn('船',text['JG_SUNLACE_DETAIL'])
        self.assertIn('昇降機',text['JG_KILNSTEP_DETAIL'])
        self.assertNotIn('THE END',json.dumps(text))
        self.assertEqual(len(text),len(set(text)))

if __name__=='__main__': unittest.main()
