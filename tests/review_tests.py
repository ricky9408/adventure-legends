#!/usr/bin/env python3
"""Read-only reviewer mGBA coverage. All normal cases are input-only.
The corrupted-save rejection case alters a COPY of the cartridge save file;
no test writes emulated RAM. Outputs stay under build/review.
"""
from pathlib import Path
import sys,json,hashlib,os
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tests'))
import playthrough
OUT=Path(os.environ.get('EMBERBOND_REVIEW_OUTPUT',ROOT/'build/review')).resolve();OUT.mkdir(parents=True,exist_ok=True)
PRIMARY_OUT=Path(os.environ.get('EMBERBOND_PRIMARY_OUTPUT',playthrough.OUT)).resolve()
playthrough.OUT=OUT
P=playthrough.Play
report={'controller_only':True,'ram_injection':False,'passes':[],'rom_sha256':hashlib.sha256(playthrough.ROM.read_bytes()).hexdigest()}
def ok(p,condition,label):
 p.check(condition,label);report['passes'].append(label)
def shot(p,n):p.e.screenshot(OUT/(n+'.png'))
def fresh():
 p=P();p.step(90);p.tap('SELECT');p.dialogs();return p
# Real damage/death and checkpoint retry, no injections.
p=fresh();p.nextroom(1);p.goto(y=248);p.goto(x=180);p.goto(y=230)
for i in range(200):
 p.step(12)
 if p.get('game_state')==4:break
ok(p,p.get('game_state')==4 and p.get('hp')==0,'enemy damage leads to death');shot(p,'death')
old=(p.get('px'),p.get('py'));p.step(80,'UP')
ok(p,(p.get('px'),p.get('py'))==old,'death blocks player movement')
p.tap('A');ok(p,p.get('game_state')==1 and p.get('hp')==6 and p.get('room')==1,'A retries current room with six hearts')
ok(p,p.get('summoned')==0 and p.get('ability_cd')==0 and p.get('heal_cd')==0,'retry recalls spirit and clears ability/heal cooldowns');shot(p,'retry')
# Use bridge then attempt immediate second power to confirm cooldown.
p.goto(x=240);p.goto(y=180);p.tap('L');p.tap('B');p.tap('R');p.dialogs()
ok(p,p.get('bridge_open')==1,'input-only checkpoint puzzle solved')
oldcd=p.get('ability_cd');p.tap('R')
ok(p,0<p.get('ability_cd')<oldcd,'immediate repeat power is blocked by shared cooldown')
oldcd=p.get('ability_cd');p.tap('L');p.tap('R')
ok(p,0<=p.get('ability_cd')<oldcd,'switching spirits does not bypass shared cooldown')
# SRAM checkpoint from actual gameplay, independently reopened by a new core.
save=OUT/'forest-checkpoint.sav';save.write_bytes(p.e.bytes(0x0E000000,32768));p.e.close()
p=P();p.e.load_save(save);p.e.reset();p.step(90)
ok(p,p.get('has_save')==1,'new emulator recognizes real SRAM checkpoint');p.tap('START')
ok(p,p.get('room')==1 and p.get('bridge_open')==1 and p.get('hp')==6,'continue restores room and puzzle progress');shot(p,'continue');p.e.close()
# First-lantern save made by the primary controller-only regression.
completed=PRIMARY_OUT/'checkpoint.sav'
if not completed.exists():
 raise FileNotFoundError('First-lantern checkpoint missing; run tests/playthrough.py first or set EMBERBOND_PRIMARY_OUTPUT: '+str(completed))
if completed.exists():
 p=P();p.e.load_save(completed);p.e.reset();p.step(90);p.tap('START')
 p.dialogs()
 ok(p,p.get('game_state')==1 and p.get('room')==0 and p.get('chapter_flags')==1 and p.get('completed')==0,'first-lantern SRAM reopens continuing village');shot(p,'grove-cleared-resume')
 for _ in range(3):
  if p.get('spirit')==2:break
  p.tap('L')
 ok(p,p.get('spirit')==2,'first-lantern resume preserves earned wind companion')
 p.e.reset();p.step(90)
 before=p.e.bytes(0x0E000000,32768);p.tap('SELECT');ok(p,p.get('game_state')==9 and p.e.bytes(0x0E000000,32768)==before,'title Select asks before replacing existing progress')
 p.tap('A');ok(p,p.get('chapter_flags')==0 and p.get('completed')==0 and p.get('bridge_open')==0 and p.get('torches')==0 and p.get('room')==0 and p.get('game_state')==2,'fresh confirmation starts new adventure and clears prior chapter progress')
 p.e.reset();p.step(90);p.tap('START')
 ok(p,p.get('completed')==0 and p.get('room')==0,'fresh Select persists replacement checkpoint');p.e.close()
# Walk from our real forest checkpoint into the guardian encounter.
p=P();p.e.load_save(save);p.e.reset();p.step(90);p.tap('START');p.nextroom(2);p.dialogs();p.tap('B')
for _ in range(4):
 if p.get('spirit')==0:break
 p.tap('L')
ok(p,p.get('spirit')==0,'review explicitly selects Homura after saved companion restoration')
p.goto(y=94);p.goto(x=64);p.goto(y=84);p.defend(160);p.goto(x=64,y=84);p.tap('R')
p.goto(y=94);p.goto(x=176);p.goto(y=84);p.defend(160);p.goto(x=176,y=84);p.tap('R');p.dialogs()
p.goto(y=94);p.goto(x=120);p.nextroom(3);p.dialogs();p.goto(y=94);p.step(2,'UP');p.step(2)
before=p.get('boss_hp')
for _ in range(3):p.tap('A');p.step(25)
ok(p,p.get('boss_armor')==0 and p.get('boss_hp')==before,'sword cannot damage armored guardian');shot(p,'armored-sword')
p.tap('R');p.goto(x=p.get('boss_x'),y=p.get('boss_y')+28);p.step(2,'UP');p.step(2)
for _ in range(3):p.tap('A');p.step(25)
ok(p,p.get('boss_armor')>0 and p.get('boss_hp')<before,'fire exposure permits sword damage');shot(p,'exposed-sword')
for _ in range(800):
 if p.get('game_state')==4:break
 p.step(15)
ok(p,p.get('game_state')==4,'guardian fight can naturally cause death');shot(p,'boss-death')
p.tap('A');ok(p,p.get('game_state')==1 and p.get('hp')==6 and p.get('room')==3 and p.get('boss_hp')==12 and p.get('boss_armor')==0,'boss death retry resets guardian and restores hearts')
ok(p,p.get('bridge_open')==1 and p.get('torches')==3,'boss retry preserves puzzle progression');shot(p,'boss-retry');p.e.close()
# Explicit malformed-save input: mutate a copy, never RAM.
corrupt=OUT/'corrupt-copy.sav';b=bytearray(save.read_bytes());b[0x200+16]^=1;b[0x1a00+16]^=1;corrupt.write_bytes(b)
p=P();p.e.load_save(corrupt);p.e.reset();p.step(90)
ok(p,p.get('has_save')==0,'corrupted v5 bank checksums are rejected');p.e.close()
report['corrupted_save_case']='CRC byte in both v5 banks of a copied SRAM file intentionally changed; no RAM injection'
(OUT/'review-tests.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
