#!/usr/bin/env python3
"""Keep all journey goal tests, asserting the accepted ending replay contract."""
from pathlib import Path
import hashlib
from verify_companion_browsing_successor import verify
ROOT=Path(__file__).resolve().parents[1]
verify();p=ROOT/'tests/test_journey_goals.py';raw=p.read_bytes()
assert hashlib.sha256(raw).hexdigest()=='73c650a403bfd9fc48ce66c7766cc26dac643098d9b69ad010e828d2de290738'
s=raw.decode()
pairs=[("'if(game_state==WIN){if(pressed&(KEY_A|KEY_START))'","'if(game_state==WIN){if(ending_credits_update()){game_state=PLAY;enter_room(0,3);}return;}'"),("'chapter_flags|=SAVE4_ENDING_SEEN;completed=1;save_at(0,3);game_state=WIN;'","'if(!(chapter_flags&SAVE4_ENDING_SEEN)){chapter_flags|=SAVE4_ENDING_SEEN;completed=1;save_at(0,3);}game_state=WIN;ending_credits_begin();'")]
for before,after in pairs:assert s.count(before)==1;s=s.replace(before,after)
__file__=str(p)
exec(compile(s,str(p),'exec'),globals())
