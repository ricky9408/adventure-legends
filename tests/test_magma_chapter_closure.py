#!/usr/bin/env python3
"""Magma's fresh receipt gives Ressa a personal wish and retains the route clue."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from test_covenants_engine import function

texts = json.loads((ROOT / 'assets/ui_texts.json').read_text())
region = json.loads((ROOT / 'assets/magma_region/dialogue.json').read_text())
assert texts['MG_END'] == region['MG_END'] == 'レッサ：待ってたれんがを焼ける'
assert texts['MG_ENDB'] == region['MG_ENDB'] == '下の泉はいつか海へつながる'
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
 receipt_later=receipt_fresh=return_state=1;receipt_boss=2;
 finish_later_story();assert(calls==1&&first==TX_MG_END&&second==TX_MG_ENDB&&!receipt_fresh);
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
print('PASS: fresh Magma receipt, next-route clue, one-shot and recovery exclusions')
