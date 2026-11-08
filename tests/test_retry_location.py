#!/usr/bin/env python3
"""Death-card destination and unchanged retry input/state contracts (host)."""
from pathlib import Path
import json
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
source = (ROOT / 'src/game.c').read_text()
label = re.search(r'COLD int retry_location_text\(void\)\{[^\n]+', source).group()
retry = re.search(r' if\(game_state==DEAD\)\{if\(pressed&KEY_A\)[^\n]+', source).group()
forest = re.search(r' if\(r==1\)\{px=fromnorth[^\n]+', source).group()
assert 'centered(retry_location_text(),94,CREAM)' in source
texts = json.loads((ROOT / 'assets/ui_texts.json').read_text())
assert texts['RETRY'] == 'A  たき火から再挑戦'
assert texts['RETRY_CHECKPOINT'] == 'A  休んだ場所から再挑戦'
assert texts['C_RETRY_ROOM'] == 'A  部屋の入口から再挑戦'
assert "'RETRY':'A  たき火から再挑戦'" in (ROOT / 'assets/generate_ui.py').read_text()
assert 'enter_room(room,room>=16?checkpoint_spawn:2)' in retry
spans = ''.join(p.read_text() for p in sorted((ROOT / 'src/ui_data').glob('part_*.inc')))
for name in ('RETRY', 'C_RETRY_ROOM', 'RETRY_CHECKPOINT'):
    metadata = re.search(r'\{(\d+),(\d+),0,\{txt_' + name + r'_0,txt_' + name + r'_1\}', spans)
    assert metadata and int(metadata[1]) <= 196 and int(metadata[2]) <= 15, name


harness = r'''
#include <assert.h>
#include <stdio.h>
#include "ui.h"
#include "world.h"
#define COLD
#define KEY_A 1
#define PLAY 1
#define DEAD 2
int room,camp_unlocked,checkpoint_spawn,pressed,game_state;
int hp,max_hp,ability_cd,heal_cd,px,py,entered_room,entered_spawn;
int companions,gold,quest_flags;
void game_health_fill(void){hp=max_hp;}
void enter_room(int r,int fromnorth){
 entered_room=r;entered_spawn=fromnorth;
 /* The forest coordinate branch is copied from production below. Other
  * regional enter hooks are exercised by native gameplay, not this stub. */
 FOREST
}
LABEL
void retry_input(void){RETRY}
static void check(int r,int camp,int spawn,int expected){
 room=r;camp_unlocked=camp;checkpoint_spawn=spawn;game_state=DEAD;
 hp=0;max_hp=8;ability_cd=9;heal_cd=10;
 companions=4;gold=57;quest_flags=23;entered_room=-1;entered_spawn=-1;
 assert(retry_location_text()==expected);
 assert(hp==0&&ability_cd==9&&heal_cd==10&&game_state==DEAD);
 pressed=0;retry_input();
 assert(entered_room==-1&&hp==0&&game_state==DEAD);
 pressed=KEY_A;retry_input();
 assert(entered_room==r&&entered_spawn==(r>=16?spawn:2));
 assert(hp==max_hp&&ability_cd==0&&heal_cd==0&&game_state==PLAY);
 assert(companions==4&&gold==57&&quest_flags==23);
 if(r==1){
  assert(px==(camp?WORLD_CAMP_X:WORLD_SPAWN_X));
  assert(py==(camp?WORLD_CAMP_Y+16:WORLD_SPAWN_Y));
 }
}
int main(void){
 const int anchors[][2]={{16,2},{17,2},{22,2},{23,2},{30,2},{31,2},{38,3},{39,3},{46,2},{47,2},{54,2},{55,2},{62,4},{65,3},{70,4},{74,3}};
 unsigned i;
 for(i=0;i<sizeof anchors/sizeof anchors[0];i++){
  check(anchors[i][0],1,anchors[i][1],TX_RETRY_CHECKPOINT);
  check(anchors[i][0],1,0,TX_C_RETRY_ROOM);
  check(anchors[i][0],1,1,TX_C_RETRY_ROOM);
 }
 check(38,1,2,TX_C_RETRY_ROOM);
 check(39,1,2,TX_C_RETRY_ROOM);
 check(48,1,2,TX_C_RETRY_ROOM);
 check(51,1,2,TX_C_RETRY_ROOM);
 check(52,1,2,TX_C_RETRY_ROOM);
 check(63,1,2,TX_C_RETRY_ROOM);
 check(63,1,3,TX_C_RETRY_ROOM);
 check(65,1,2,TX_C_RETRY_ROOM);
 check(74,1,2,TX_C_RETRY_ROOM);
 check(62,1,3,TX_C_RETRY_ROOM);
 check(70,1,3,TX_C_RETRY_ROOM);
 check(1,0,0,TX_C_RETRY_ROOM);
 check(1,1,2,TX_RETRY);
 check(2,1,1,TX_C_RETRY_ROOM);
 check(4,1,0,TX_C_RETRY_ROOM);
 check(16,1,4,TX_C_RETRY_ROOM);
 check(70,1,1,TX_C_RETRY_ROOM);
 puts("PASS retry labels, forest coordinates, entry indices, and retry state");
 return 0;
}
'''.replace('FOREST',forest).replace('LABEL',label).replace('RETRY}',retry+'}')
with tempfile.TemporaryDirectory(prefix='retry-location-') as temporary:
    out = Path(temporary)
    test = out / 'retry.c'
    test.write_text(harness)
    for name, flags in [('strict', []), ('sanitized', ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'])]:
        target = out / name
        subprocess.run(['cc','-std=c99','-O1','-Wall','-Wextra','-Werror','-pedantic','-Isrc',str(test),*flags,'-o',str(target)],cwd=ROOT,check=True)
        subprocess.run([str(target)],cwd=ROOT,check=True)
