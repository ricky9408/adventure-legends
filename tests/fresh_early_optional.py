#!/usr/bin/env python3
"""Bounded fresh-cartridge controller proof: first boss, shop, fire field trial.
No historical SRAM input, RAM writes, or machine-state imports. Same-run cold
Continue is separately labeled persistence verification, not starting progress.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse,gzip,json,shutil,sys,traceback
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from treasure_full_journey import TreasureOriginalJourney
from player_feedback_native import sha

class FreshEarly(TreasureOriginalJourney):
 def proof_state(self):
  row=super().proof_state();state=self.state()
  row.update(gold=state.economy.gold,supplies=list(state.economy.supplies),boss_claims=state.economy.boss_claims,fire_trial_flags=self.instance(0).trial_flags,fire_xp=self.instance(0).xp)
  return row
 def report(self):
  super().report()
  p=self.out/'report.json'
  if p.is_file():
   data=json.loads(p.read_text());data.update(suite='fresh-early-optional-controller',scope='empty cartridge through first boss, shop, Fire trial/evolution, equipment preview, and own-save Continue',complete_fresh_main_journey=False,full_collection_proven=False)
   p.write_text(json.dumps(data,indent=2)+'\n')

 def wait_prepared(self):
  pairing=self.evolution_observer()
  for _ in range(180):
   if self.get('game_state')==7 and self.e.read(pairing['address']+8)==0:break
   self.raw_step(1)
  self.check(self.get('game_state')==7 and self.e.read(pairing['address']+8)==0 and self.get('progression_evolution_reason')==0,'earned evolution is genuinely eligible and prepared')
 def run(self):
  self.first_chapter()
  self.check(self.state().economy.boss_claims==1,'first boss grants exactly first unique treasure')
  gold=self.state().economy.gold
  self.snapshot('first-boss-earned')
  self.goto(y=100);self.goto(x=56);self.tap('A')
  self.check(self.get('game_state')==11,'walk and A open actual village merchant')
  self.shot('shop-stock')
  self.tap('A');self.check(self.get('game_shop_confirm')==1,'purchase shows confirmation before charging')
  self.shot('heart-purchase-confirm');self.tap('B')
  self.check(self.state().economy.gold==gold and not self.state().economy.supplies[0],'B cancels purchase without charge')
  self.raw_step(320,'A');self.step(3)
  # Releasing then pressing is needed: held initial A must not count as confirm.
  self.check(self.state().economy.gold==gold,'held initial A cannot confirm purchase')
  self.raw_step(320,'A');self.step(3)
  self.check(self.state().economy.gold==gold-18 and self.state().economy.supplies[0]==1,'fresh held confirmation buys one Heart tonic for 18G')
  self.shot('heart-purchase-saved');self.tap('DOWN');self.tap('A');self.tap('A')
  self.check(self.state().economy.gold==gold-42 and self.state().economy.supplies[1]==1,'Spirit tonic costs 24G once')
  self.tap('B');self.tap('B');self.select(2);self.ready();self.tap('R')
  self.check(self.get('ability_cd')>0,'earned wind companion power causes actual cooldown')
  self.open_tab(15);self.tap('DOWN');self.tap('A');self.shot('spirit-use-confirm');self.tap('A')
  self.check(self.state().economy.supplies[1]==0 and self.get('ability_cd')==0,'Spirit tonic consumes once and clears actual cooldown')
  self.close_menu();self.snapshot('earned-shop-use')
  self.goto(x=120);self.earned_fire_trial()
  self.check(self.instance(0).trial_flags&1,'three reachable optional field requests earn Fire trial')
  self.snapshot('optional-fire-trial-earned')
  self.growth(0);self.shot('fire-growth-after-first-boss')
  self.tap('DOWN');before=bytes(self.instance(0));identity=self.instance(0).instance_id
  self.tap('A');self.wait_prepared();self.shot('earned-evolution-confirmation');self.tap('B')
  self.check(self.get('game_state')==3 and bytes(self.instance(0))==before,'B declines evolution with exact individual unchanged')
  self.tap('A');self.wait_prepared();self.raw_step(2,'A');self.raw_step(3)
  observed_animation=False
  for _ in range(600):
   observed_animation |= self.get('game_state')==8
   if self.get('game_state')==3:break
   self.raw_step(1)
  self.check(observed_animation and self.get('game_state')==3 and self.instance(0).form_id==2,'fresh A earns Fire evolution and returns to Growth')
  self.check(self.instance(0).instance_id==identity,'evolution retains same earned individual')
  self.shot('earned-fire-evolution');self.close_menu()
  self.snapshot('early-fire-evolution-earned')
  self.open_tab(4);before=bytes(self.state().equipment)
  self.tap('RIGHT');self.check(self.get('gear_menu_slot')==1,'Right selects next equipment part')
  self.tap('LEFT');self.check(self.get('gear_menu_slot')==0,'Left returns to weapon part')
  self.tap('DOWN');self.check(bytes(self.state().equipment)==before,'browsing another equipment candidate changes no saved gear')
  self.shot('equipment-preview-before-A');self.tap('B');self.tap('START')
  self.check(bytes(self.state().equipment)==before,'backing out of preview preserves equipped starter weapon')
  self.cold_reboot('early-optional-progress')
  self._frames.close()
  observations=[json.loads(line) for line in gzip.open(self.out/'native-frames.jsonl.gz','rt')]
  measured=[row for row in observations if row['phase']=='journey']
  self.check(bool(measured) and all(row['delta']==1 and row['flip'] and row['cycles']<280896 for row in measured),'every measured gameplay/menu/transaction/evolution frame updates and presents within hardware budget')
  self.route_complete=True;self.coverage.extend(['empty-SRAM-first-boss-shop-purchase-use','three-earned-fire-field-requests','first-boss-earned-fire-evolution','horizontal-equipment-parts-and-cancel-preview']);self.history=['early-optional'];self.report()

if __name__=='__main__':
 parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('output',type=Path);parser.add_argument('--bridge',type=Path,default=ROOT/'build/player-feedback-bridge.so');options=parser.parse_args()
 out=options.output.resolve();out.mkdir(parents=True,exist_ok=False)
 a=SimpleNamespace(output=out,rom=ROOT/'build/emberbond.gba',symbols=ROOT/'build/emberbond.sym',bridge=options.bridge.resolve(),source_root=ROOT,baseline=False,cross_rom_diagnostic=False,stop_after='original')
 a.expected_rom_sha=sha(a.rom);a.candidate={'rom_sha256':a.expected_rom_sha,'symbols_sha256':sha(a.symbols),'elf_sha256':sha(a.rom.with_suffix('.elf')),'source_manifest_sha256':sha(ROOT/'build/source-hashes.json'),'bridge_sha256':sha(a.bridge)}
 manifest=json.loads((ROOT/'build/source-hashes.json').read_text())
 assert all(sha(ROOT/name)==digest for name,digest in manifest.items()),'ROM source manifest must match checkout'
 shutil.copyfile(__file__,out/'fresh_early_optional.py')
 (out/'candidate.json').write_text(json.dumps({**a.candidate,'test_sha256':sha(__file__)},indent=2)+'\n')
 r=FreshEarly(a)
 try:
  r.run()
  assert r.route_complete and not r.failures,'Fresh route did not complete cleanly'
 except Exception as e:
  r.failures.append({'error':str(e),'traceback':traceback.format_exc()});r.report()
  if r.e:r.e.screenshot(out/'failure.png')
  raise
 finally:r.close()
