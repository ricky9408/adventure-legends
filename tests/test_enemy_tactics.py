#!/usr/bin/env python3
"""Real charger and production enemy-update host integration; not native play."""
from pathlib import Path
import json,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'build/enemy-tactics-host';OUT.mkdir(parents=True,exist_ok=True)
source=(ROOT/'src/game.c').read_text();start=source.index('static COLD void update_charger_contact');end=source.index('\nvoid campaign_boss_update',start)
(OUT/'enemy_update_source.inc').write_text(source[start:end]+'\n')
common=['cc','-std=c99','-O2','-Wall','-Wextra','-Werror','-pedantic','-Isrc','-I'+str(OUT),'tests/enemy_tactics_host.c','src/enemy_tactics.c']
logs={}
for name,flags in [('strict',[]),('sanitized',['-fsanitize=address,undefined','-fno-omit-frame-pointer'])]:
 exe=OUT/name;subprocess.run([*common,*flags,'-o',str(exe)],cwd=ROOT,check=True)
 r=subprocess.run([str(exe)],cwd=ROOT,check=True,capture_output=True,text=True);logs[name]=r.stdout;print(r.stdout)
 # This tests the real update function; no copied tactics algorithm or reward fixture.
assert '{328,56,5,ENEMY_LANE_CHARGER,4}' in (ROOT/'src/magma_game.c').read_text()
assert source.index('if(hitstop){hitstop--;return;}')<source.index('update_enemies();')
assert 'zero(enemy_clocks,sizeof enemy_clocks);zero(enemy_windups,sizeof enemy_windups)' in source
files=['src/enemy_tactics.c','src/enemy_tactics.h','src/enemy_tactics_art.inc','src/game.c','src/magma_game.c','tests/enemy_tactics_host.c']
(OUT/'report.json').write_text(json.dumps({'scope':'host production update integration plus ASan/UBSan; native controller evidence separate','logs':logs,'sources':{f:hashlib.sha256((ROOT/f).read_bytes()).hexdigest()for f in files}},indent=2)+'\n')
