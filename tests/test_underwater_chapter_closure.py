#!/usr/bin/env python3
"""A fresh regional receipt ends in a person's voice and keeps its onward clue."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from test_covenants_engine import function

texts = json.loads((ROOT / 'assets/ui_texts.json').read_text())
region = json.loads((ROOT / 'assets/underwater_region/dialogue_ja.json').read_text())
assert texts['UW_END'] == region['UW_END'] == 'シオリ：待ってた皆を迎えられる'
assert texts['UW_ENDB'] == region['UW_ENDB'] == '写した地図を、里の机へ。'
assert '記録守シオリ' in region['UW_CLUE38A']
assert texts['UW_GUARDIAN_DONE'] == region['UW_GUARDIAN_DONE']
assert texts['UW_GUARDIAN_HOME'] == region['UW_GUARDIAN_HOME']
assert region['UW_GUARDIAN_DONE'].startswith('守り手：')
source = (ROOT / 'src/game_shop.c').read_text()
code = r'''
#include <assert.h>
#define COLD
#define PLAY 1
enum {TX_NT_RETURN_A, TX_NT_RETURN_B, TX_ST_RETURN_A, TX_ST_RETURN_B,
      TX_MG_END, TX_MG_ENDB, TX_UW_END, TX_UW_HOME, TX_UW_ENDB};
int receipt_later, receipt_fresh, return_state, receipt_boss, calls, first, second;
void dialogue(int a,int b,int state){assert(state==PLAY);first=a;second=b;calls++;}
''' + function(source, 'finish_later_story') + r'''
int main(void){
 const int expected[4][2]={{TX_NT_RETURN_A,TX_NT_RETURN_B},
  {TX_ST_RETURN_A,TX_ST_RETURN_B},{TX_MG_END,TX_MG_ENDB},{TX_UW_END,TX_UW_ENDB}};
 int region;
 for(region=0;region<4;region++){
  receipt_boss=region;receipt_later=receipt_fresh=return_state=1;calls=0;
  finish_later_story();assert(calls==1&&first==expected[region][0]&&second==expected[region][1]&&!receipt_fresh);
  finish_later_story();assert(calls==1);
  receipt_fresh=1;receipt_later=0;finish_later_story();assert(calls==1&&!receipt_fresh);
  receipt_fresh=receipt_later=1;return_state=3;finish_later_story();assert(calls==1&&!receipt_fresh);
  return_state=1;receipt_fresh=0;finish_later_story();assert(calls==1);
 }
 return 0;
}
'''
with tempfile.TemporaryDirectory() as tmp:
    p = Path(tmp)
    (p / 'test.c').write_text(code)
    subprocess.run(['cc', '-std=c99', '-Wall', '-Wextra', '-Werror',
                    '-fsanitize=address,undefined', str(p / 'test.c'), '-o', str(p / 'test')], check=True)
    subprocess.run([str(p / 'test')], check=True)
print('PASS: four personal chapter closures, onward clues, one-shot and recovery exclusions')
