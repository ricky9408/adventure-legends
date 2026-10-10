#!/usr/bin/env python3
"""Run every retained engine/save assertion with the exact accepted ending hint.

The historical engine script remains byte-identical. Only its independently
rendered phase-zero continuation-card hint changes from TX_C_POSTGAME to the
accepted ending-card hint. Ending-roll pixel/state tests remain separate.
"""
from pathlib import Path
import hashlib,os
from player_feedback_host_mapping import run_protected_probe
from verify_companion_browsing_successor import verify
ROOT=Path(__file__).resolve().parents[1]
if __name__=='__main__'and os.environ.get('PLAYER_FEEDBACK_PROBE_CHILD')!='1':
 raise SystemExit(run_protected_probe(Path(__file__).resolve()))
verify()
p=ROOT/'tests/test_player_feedback_engine.py';raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='e4fa2598d5a08185c7d6724d89b4264adb2772d4dd0148acf04e3a69e2c99ff1'
s=raw.decode();before="current_card='box(8,40,224,105);centered(TX_COMPLETE,49,GOLD);centered(TX_THANKS,67,CREAM);{JourneyGoal g=journey_goal_read(&adventure_save,chapter_flags,(unsigned)room);centered(g.title,83,TEAL);}centered(TX_C_POSTGAME,126,CREAM);'"
after=before.replace('centered(TX_C_POSTGAME,126,CREAM);','ending_credits_card_hint();')
assert s.count(before)==1;s=s.replace(before,after)
marker=' win_cases=0\n';assert s.count(marker)==1
s=s.replace(marker," assert C.c_uint.in_dll(lib,'ending_credits_phase').value==0, 'phase-zero card reference only'\n"+marker)
exec(compile(s,str(p),'exec'),{'__name__':'__main__','__file__':str(p)})
