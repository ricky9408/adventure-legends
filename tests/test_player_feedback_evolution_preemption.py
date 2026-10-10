#!/usr/bin/env python3
"""Independent real-engine regression for evolution/ordinary-save ownership.

The existing engine fixture uses explicit synthetic host state and real codec
logic. This additional probe is not native controller-acquisition evidence.
"""
import sys,runpy,ctypes as C,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
ctx=runpy.run_path(str(ROOT/'tests/test_player_feedback_engine.py'))
lib=ctx['lib'];drain=ctx['drain'];get=ctx['get'];put=ctx['put'];live=ctx['live'];load=ctx['load']
lib.start_game(0);drain();put('game_state',1)
lib.creatures_migrate_legacy.argtypes=[C.c_void_p,C.c_uint,C.c_uint]
assert lib.creatures_migrate_legacy(C.byref(live.roster),1,0)
put('chapter_flags',1);put('room',0)
c=live.roster.instances[0];c.level=50;c.xp=lib.creatures_xp_threshold(50);c.bond=100;c.trial_flags=1
lib.progression_refresh();lib.save_game();drain();put('game_state',1);assert lib.save5_validate(C.byref(live))
base_gold=live.economy.gold;assert lib.economy_award_combat(C.byref(live),6)==6;lib.save_game_ordinary()
for _ in range(10):
 lib.save_frame()
 if get('save_feedback_background'):break
assert get('save_feedback_background')
put('journal_tab',3);put('game_state',3);lib.progression_menu_reset();lib.progression_menu_input(128);lib.progression_menu_input(1)
def observation():return {'mode':get('game_state'),'proof':lib.save5_preflight_active(),'background':get('save_feedback_background'),'requested':get('save_requested'),'failure':get('save_failed')}
opened=observation();lib.save_frame();during=observation();lib.progression_confirm_input(2);drain()
end={'failure':get('save_failed'),'gold_live':live.economy.gold,'gold_saved':load().economy.gold,'gold_expected':base_gold+6}
print('Evolution preemption:',json.dumps({'opened':opened,'during_proof':during,'after_cancel_and_drain':end},sort_keys=True))
assert opened['mode']==7 and opened['proof'];assert during['requested']==1 and not during['failure'] and during['proof'];assert not end['failure'] and end['gold_saved']==end['gold_expected']
print('PASS real engine preserves and saves queued ordinary progress after evolution cancellation')
