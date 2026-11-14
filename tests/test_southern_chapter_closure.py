#!/usr/bin/env python3
"""Mina introduces the southern lens request and celebrates reopening the conservatory."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from test_covenants_engine import function

texts = json.loads((ROOT / 'assets/ui_texts.json').read_text())
region = json.loads((ROOT / 'assets/southern_region/ui_additions.json').read_text())
assert texts['ST_RETURN_A'] == region['ST_RETURN_A'] == 'ミナ：待ってた苗を植えられる'
assert texts['ST_RETURN_B'] == region['ST_RETURN_B'] == '市場の窓が開いた。港へ戻ろう'
assert texts['ST_CLUE24A'] == region['ST_CLUE24A'] == 'ミナ：水のレンズ、金の留め具へ'
assert texts['ST_CLUE24B'] == region['ST_CLUE24B'] == '仲間を選び、印の前でＢ'
south = (ROOT / 'src/south_game.c').read_text()
assert '{TX_ST_CLUE24A,TX_ST_CLUE24B}' in south
assert 'if(npc_close(400,192)){if(done(24))mina_talk();else talk(24);' in south
assert 'if(done(24)&&close(400,216))return mina_plant();' in south
source = (ROOT / 'src/game_shop.c').read_text()
code = r'''
#include <assert.h>
#define COLD
#define PLAY 1
enum {TX_NT_RETURN_A, TX_NT_RETURN_B, TX_ST_RETURN_A, TX_ST_RETURN_B,
      TX_MG_END, TX_MG_ENDB, TX_UW_END, TX_UW_HOME};
int receipt_later, receipt_fresh, return_state, receipt_boss, calls, first, second;
void dialogue(int a,int b,int state){assert(state==PLAY);first=a;second=b;calls++;}
''' + function(source, 'finish_later_story') + r'''
int main(void){
 receipt_later=receipt_fresh=return_state=1;receipt_boss=1;
 finish_later_story();assert(calls==1&&first==TX_ST_RETURN_A&&second==TX_ST_RETURN_B&&!receipt_fresh);
 finish_later_story();assert(calls==1);
 receipt_fresh=1;receipt_later=0;finish_later_story();assert(calls==1&&!receipt_fresh);
 receipt_fresh=receipt_later=1;return_state=3;finish_later_story();assert(calls==1&&!receipt_fresh);
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    p=Path(tmp); (p/'test.c').write_text(code)
    subprocess.run(['cc','-std=c99','-Wall','-Wextra','-Werror','-fsanitize=undefined',str(p/'test.c'),'-o',str(p/'test')],check=True)
    subprocess.run([str(p/'test')],check=True)
print('PASS: fresh Southern receipt, next-route clue, one-shot and recovery exclusions')
