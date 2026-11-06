#!/usr/bin/env python3
"""Check the real village dialogue path at each chapter boundary."""
import json
from pathlib import Path
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'src/game.c').read_text(encoding='utf-8')


def function(name):
    match = re.search(r'^COLD (?:void|int) ' + name + r'\([^;{}]*\)\s*\{', SOURCE, re.M)
    assert match, f'Missing production function {name}'
    start = match.start()
    depth = 0
    for end in range(SOURCE.index('{', start), len(SOURCE)):
        depth += (SOURCE[end] == '{') - (SOURCE[end] == '}')
        if depth == 0:
            return SOURCE[start:end + 1]
    raise AssertionError(f'Unterminated production function {name}')


story = json.loads((ROOT / 'assets/campaign_dialogue.json').read_text(encoding='utf-8'))['dialogue']
opening = json.loads((ROOT / 'assets/opening_scene.json').read_text(encoding='utf-8'))
ui = json.loads((ROOT / 'assets/ui_texts.json').read_text(encoding='utf-8'))
assert any('パンを分けよう' in line for page in opening['pages'] for line in page['lines'])
assert any('スープを温めて待ってる' in line for page in opening['pages'] for line in page['lines'])
assert 'パン' in ''.join(story['ELDER_ACT2']['pages'][-1])
assert 'スープ' in ''.join(story['ELDER_ACT2']['pages'][-1])
assert '三つの灯' in ''.join(story['ELDER_FINAL']['pages'][-1])
assert '食卓' in ''.join(story['ELDER_FINAL']['pages'][-1])
assert 'パン' in ''.join(story['ENDING_FRIENDS']['pages'][-1])
for scene, page in (('ELDER_ACT2', 2), ('ELDER_FINAL', 3)):
    for line, text in enumerate(story[scene]['pages'][page]):
        assert ui[f'C_{scene}_{page}_{line}'] == text
assert len(story['ELDER_FINAL']['pages']) + len(story['ENDING_FRIENDS']['pages']) == 6

fixture = r'''
#include <assert.h>
#include <string.h>
#include "campaign_rules.h"
#include "campaign_art.h"
#include "save4.h"
#define COLD
#define PLAY 1
#define DIALOG 2
#define MAX_ENEMIES 6
typedef struct { int x,y,hp,flash,kind; } Enemy;
Enemy enemies[MAX_ENEMIES];
int room,px,py,boss_x,boss_y,game_state,dpage,dcount,dafter,dialogue_action;
int dialog_lines[12],dialog_speakers[6],heals,saves;
unsigned chapter_flags,optional_flags,story_seen,dialogue_seen;
int near(int x,int y,int tx,int ty,int radius){int dx=x-tx,dy=y-ty;return (dx<0?-dx:dx)+(dy<0?-dy:dy)<=radius;}
void game_health_fill(void){heals++;}
void save_game(void){saves++;}
int boss_active(void){return 0;}
void toast(int id){(void)id;}
#include "village_homecoming.inc"
static void reset(unsigned flags){
 memset(enemies,0,sizeof enemies);memset(dialog_lines,0,sizeof dialog_lines);
 room=0;px=120;py=94;chapter_flags=flags;optional_flags=story_seen=0;
 game_state=PLAY;dpage=dcount=dafter=dialogue_action=0;heals=saves=0;
}
static void visit(unsigned flags,int first,int pages,int action){
 reset(flags);assert(campaign_interact()==1);
 assert(game_state==DIALOG&&dialog_lines[0]==first&&dcount==pages);
 assert(dialogue_action==action&&heals==1&&saves==1);
 assert(chapter_flags==flags&&optional_flags==0&&story_seen==0);
}
int main(void){
 visit(0,TX_C_ELDER_ACT1_0_0,1,0);
 visit(SAVE4_GROVE_CLEAR,TX_C_ELDER_ACT2_0_0,3,0);
 assert(dialog_lines[2]==TX_C_ELDER_ACT2_1_0);
 assert(dialog_lines[4]==TX_C_ELDER_ACT2_2_0);
 assert(dialog_lines[5]==TX_C_ELDER_ACT2_2_1);
 visit(SAVE4_GROVE_CLEAR|SAVE4_SKY_CLEAR,TX_C_ELDER_ACT3_0_0,2,0);
 visit(SAVE4_GROVE_CLEAR|SAVE4_SKY_CLEAR|SAVE4_CORE_CLEAR,
       TX_C_ELDER_FINAL_0_0,6,2);
 assert(dialog_lines[6]==TX_C_ELDER_FINAL_3_0);
 assert(dialog_lines[7]==TX_C_ELDER_FINAL_3_1);
 assert(dialog_lines[8]==TX_C_ENDING_FRIENDS_0_0);
 assert(dialog_lines[10]==TX_C_ENDING_FRIENDS_1_0);
 visit(SAVE4_GROVE_CLEAR|SAVE4_SKY_CLEAR|SAVE4_CORE_CLEAR|SAVE4_ENDING_SEEN,
       TX_C_ELDER_POSTGAME_0_0,1,0);
 reset(SAVE4_GROVE_CLEAR);optional_flags=SAVE4_RIDGE_CHIME;
 assert(campaign_interact()==1&&dcount==4);
 assert(dialog_lines[4]==TX_C_ELDER_ACT2_2_0&&dialog_lines[6]==TX_C_ELDER_CHIME_0_0);
 assert(story_seen==0&&dialogue_seen==SAVE4_SEEN_CHIME);
 return 0;
}
'''

with tempfile.TemporaryDirectory(prefix='village-homecoming-') as temporary:
    out = Path(temporary)
    (out / 'village_homecoming.inc').write_text(
        '\n'.join(function(name) for name in ('show_scene', 'append_scene', 'campaign_interact')) + '\n',
        encoding='utf-8')
    source = out / 'host.c'
    source.write_text(fixture, encoding='utf-8')
    for mode, flags in (('strict', []),
                        ('sanitized', ['-fsanitize=address,undefined', '-fno-omit-frame-pointer'])):
        binary = out / mode
        subprocess.run(['cc', '-std=c99', '-O1', '-Wall', '-Wextra', '-Werror', '-pedantic',
                        '-Isrc', '-I' + str(out), *flags, str(source), 'src/campaign_rules.c',
                        '-o', str(binary)], cwd=ROOT, check=True)
        subprocess.run([str(binary)], cwd=ROOT, check=True)
        print(mode + ': village return dialogue PASS')
