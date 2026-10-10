#!/usr/bin/env python3
"""Controller-earned Reedhaven garden reward, equip, effect, and persistence.

The default starts empty SRAM. An optional prefix report must prove a complete
same-candidate empty-SRAM original chapter, with exact hashes and passing checks.
No synthetic saves, game-RAM writes, machine-state imports, or Select actions.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse,gzip,json,shutil,traceback
from journey_guidance_earned import RegionalJourney
from treasure_full_journey import TreasureOriginalJourney
from player_feedback_native import sha
ROOT=Path(__file__).resolve().parents[1]

class GardenReward(RegionalJourney):
 def proof_state(self):
  row=super().proof_state();s=self.state()
  row.update(garden_state=self.quest(9),garden_objective=s.quests.objectives[9],garden_variable=s.quests.variables[9] if hasattr(s.quests,'variables') else None,boots_owned=sum(x.item_id==50 for x in s.equipment.bag),equipped=list(s.equipment.equipped),gear_bag=[x.item_id for x in s.equipment.bag],ability_max=self.get('ability_max'),hero_hp_q4=self.get('hero_hp_q4'))
  return row
 def report(self):
  super().report();path=self.out/'report.json'
  if path.is_file():
   r=json.loads(path.read_text());r.update(suite='fresh-earned-garden-reward',scope='same-candidate empty-SRAM original prefix, walking garden quest, Surestep Boots claim/equip, cooldown effect, and own-save Continue/revisit',full_collection_proven=False);path.write_text(json.dumps(r,indent=2)+'\n')
 def shot(self,name):self.raw_step(3);self.e.screenshot(self.out/(name+'.png'))
 def boots_count(self):return sum(x.item_id==50 for x in self.state().equipment.bag)
 def garden_entry(self):
  if self.get('room')==21:return
  self.check(self.get('room')==16,'garden approach begins in Reedhaven')
  self.goto(344,234)
  for _ in range(90):
   if self.get('room')!=16:break
   self.step(1,'UP')
  self.settle();self.check(self.get('room')==21,'walking enters actual garden doorway')
 def run(self):
  self.chapter='garden';self.main_only=False
  self.travel(16);self.garden_entry()
  self.check(self.quest(9)==0 and self.boots_count()==0,'freshly earned campaign has neither garden progress nor Surestep Boots')
  self.act(64,136,1)
  self.check(self.quest(9)==1,'A at the actual garden sign accepts the quest')
  for i,(x,y) in enumerate(((72,72),(120,72),(168,104))):
   if i==2:self.goto(168,72)
   self.goto(x,y,radius=2)
   self.check(self.get('region_game_garden_step',1)==i+1,'walking enters ordered garden stone '+str(i+1))
   self.step(30)
   self.check(self.get('region_game_garden_step',1)==i+1,'standing on stone '+str(i+1)+' does not repeatedly advance')
   self.check(self.get('roll_ticks')==0 and self.get('roll_cd')==0,'garden stone requires no dodge or Select')
   self.shot('garden-stone-'+str(i+1))
  self.check(self.quest(9)==2 and self.boots_count()==0,'three walked stones make quest READY without granting reward early')
  self.act(184,64,1)
  self.check(self.quest(9)==3 and self.boots_count()==1,'A at garden bell claims exactly one Surestep Boots')
  self.snapshot('garden-reward-claimed')
  self.select_form(1);self.ready();self.tap('R');base=self.get('ability_max');self.step(30)
  self.open_tab(4);self.check(self.get('gear_menu_slot')==0,'equipment opens at weapon part')
  self.tap('RIGHT');self.tap('RIGHT');self.check(self.get('gear_menu_slot')==2,'two Right presses select boots part')
  self.tap('LEFT');self.check(self.get('gear_menu_slot')==1,'Left returns to previous equipment part');self.tap('RIGHT')
  before=bytes(self.state().equipment);cooldown=self.get('ability_cd');health=self.get('hero_hp_q4')
  for _ in range(49):
   ref=self.get('gear_menu_candidate')
   if ref<48 and self.state().equipment.bag[ref].item_id==50:break
   self.tap('DOWN')
  self.check(ref<48 and self.state().equipment.bag[ref].item_id==50,'Down finds the actually owned Surestep Boots')
  self.check(bytes(self.state().equipment)==before,'candidate preview leaves equipped gear unchanged')
  self.shot('surestep-preview');self.tap('A');self.drain_background()
  self.check(self.equipped_items()[2]==50,'A equips the earned boots in boots slot')
  self.check(self.get('ability_cd')==cooldown and self.get('hero_hp_q4')==health,'equipping during pause preserves running cooldown and current HP')
  self.shot('surestep-equipped');self.close_menu();self.ready();self.tap('R')
  self.check(self.get('ability_max')==base-3,'earned Surestep Boots shorten the next real Fire cooldown by exactly three updates')
  self.snapshot('surestep-power-benefit')
  gear=bytes(self.state().equipment);quests=bytes(self.state().quests)
  self.cold_reboot('garden-boots')
  self.check(self.quest(9)==3 and self.boots_count()==1 and self.equipped_items()[2]==50,'cold Continue keeps claimed quest, one reward and equipped boots')
  self.check(bytes(self.state().equipment)==gear and bytes(self.state().quests)==quests,'cold Continue preserves exact gear and quest bytes')
  self.check(self.get('room') in (16,21),'cold Continue reaches a valid Reedhaven checkpoint')
  self.select_form(1);self.ready();self.tap('R')
  self.check(self.get('ability_max')==base-3,'cold Continue also restores the equipped boots actual cooldown benefit')
  if self.get('room')==21:self.leave_interior(16)
  self.check(self.get('room')==16,'walking out returns to Reedhaven before reward revisit')
  self.garden_entry();self.act(184,64,1);self.act(184,64,1)
  self.check(bytes(self.state().equipment)==gear and bytes(self.state().quests)==quests and self.boots_count()==1,'revisiting and twice reporting the garden reward duplicates nothing')
  self.snapshot('revisited-without-duplicate');self._frames.close()
  rows=[json.loads(line) for line in gzip.open(self.out/'native-frames.jsonl.gz','rt')];measured=[x for x in rows if x['phase']=='journey']
  self.check(bool(measured) and all(x['delta']==1 and x['flip'] and x['cycles']<280896 for x in measured),'all measured garden/menu/reward frames update and present within hardware budget')
  self.route_complete=True;self.history=['garden'];self.coverage=['walking-garden-earned-quest','one-Surestep-Boots-reward','horizontal-parts-A-equip','real-power-cooldown-benefit','own-save-Continue-and-no-duplicate-revisit'];self.report()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--prefix-report',type=Path);p.add_argument('--prefix-report-sha');p.add_argument('--bridge',type=Path,default=ROOT/'build/player-feedback-bridge.so');opts=p.parse_args()
 out=opts.output.resolve()
 if opts.prefix_report:
  source_directory=opts.prefix_report.resolve().parent
  assert out!=source_directory and source_directory not in out.parents,'output must not be inside supplied prefix evidence'
 out.mkdir(parents=True,exist_ok=False)
 a=SimpleNamespace(output=out,rom=ROOT/'build/emberbond.gba',symbols=ROOT/'build/emberbond.sym',bridge=opts.bridge.resolve(),source_root=ROOT,baseline=False,cross_rom_diagnostic=False,stop_after='garden',diagnostic_boundary_report=None)
 a.expected_rom_sha=sha(a.rom);a.expected_symbols_sha=sha(a.symbols);a.candidate={'rom_sha256':a.expected_rom_sha,'symbols_sha256':a.expected_symbols_sha,'elf_sha256':sha(a.rom.with_suffix('.elf')),'source_manifest_sha256':sha(ROOT/'build/source-hashes.json'),'bridge_sha256':sha(a.bridge)}
 manifest=json.loads((ROOT/'build/source-hashes.json').read_text());assert all(sha(ROOT/n)==v for n,v in manifest.items())
 shutil.copyfile(__file__,out/'fresh_garden_reward.py');(out/'candidate.json').write_text(json.dumps({**a.candidate,'test_sha256':sha(__file__)},indent=2)+'\n')
 helper_hashes={}
 for directory,pattern in (('tests','*.py'),('tools','mgba_runner.py')):
  for source in (ROOT/directory).glob(pattern):
   target=out/'helper-source'/directory/source.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,target);helper_hashes[str(target.relative_to(out))]=sha(target)
 (out/'helper-source-hashes.json').write_text(json.dumps(helper_hashes,indent=2)+'\n')
 shutil.copyfile(ROOT/'build/source-hashes.json',out/'source-hashes.json')
 r=None
 try:
  if opts.prefix_report:
   assert not opts.prefix_report.is_symlink(),'prefix report may not be a symlink'
   source_prefix=opts.prefix_report.resolve();assert opts.prefix_report_sha and sha(source_prefix)==opts.prefix_report_sha,'supplied prefix report needs its exact explicit SHA256'
  else:
   r=TreasureOriginalJourney(a);r.run();r.close();r=None;source_prefix=out/'original/report.json'
  report=json.loads(source_prefix.read_text());provenance=report['provenance']
  assert report['candidate']==a.candidate and report['route_complete'] and not report['failures'] and all(c['passed'] for c in report['checks'])
  assert report['controller_only'] and provenance['initial_sram']=='empty cartridge' and not any(provenance[k] for k in ('historical_progress_imports','machine_state_imports','game_ram_writes'))
  assert not report['baseline_diagnostic'] and not report['cross_rom_earned_sram_diagnostic']
  # Resolve snapshot bytes beside the authenticated report, not through an old
  # machine's absolute paths. Preserve immutable source report and file hashes.
  assert not any(path.is_symlink() for path in source_prefix.parent.rglob('*')),'prefix evidence may not contain symlinks'
  for saved in report['snapshots'].values():
   local=source_prefix.parent/Path(saved['sram_path']).name
   assert local.is_file() and sha(local)==saved['sram_sha256'],'prefix directory must include every authenticated SRAM snapshot'
  source_report_sha=sha(source_prefix)
  prefix=out/'original/report.json'
  if opts.prefix_report:
   shutil.copytree(source_prefix.parent,prefix.parent)
  shutil.copyfile(source_prefix,out/'prefix-source-report.json')
  relocated=json.loads((out/'prefix-source-report.json').read_text())
  path_map={}
  for key,saved in relocated['snapshots'].items():
   relative='original/'+Path(saved['sram_path']).name
   assert sha(out/relative)==saved['sram_sha256'],'copied prefix SRAM must match its authenticated source hash'
   path_map[key]={'original_path':saved['sram_path'],'artifact_path':relative,'sha256':saved['sram_sha256']}
   saved['sram_path']=str(out/relative)
  prefix.write_text(json.dumps(relocated,indent=2)+'\n')
  sram=Path(relocated['snapshots']['original-handoff']['sram_path'])
  prefix_files={str(path.relative_to(out)):sha(path) for path in prefix.parent.rglob('*') if path.is_file()}
  (out/'prefix-provenance.json').write_text(json.dumps({'source_report_sha256':source_report_sha,'immutable_source_report':'prefix-source-report.json','report':'original/report.json','report_sha256':sha(prefix),'sram':str(sram.relative_to(out)),'sram_sha256':sha(sram),'candidate':a.candidate,'origin':provenance,'snapshot_path_map':path_map,'copied_prefix_files':prefix_files,'relocation':'Only snapshot sram_path strings changed; all source report bytes retained separately.'},indent=2)+'\n')
  r=GardenReward(a,sram,prefix);r.run();r.close();r=None
 except Exception as e:
  failure={'error':repr(e),'traceback':traceback.format_exc()}
  (out/'failure.json').write_text(json.dumps(failure,indent=2)+'\n')
  if r:
   r.failures.append(failure)
   # Report first: a broken screenshot/core must never hide the failed check.
   r.report()
   try:r.e.screenshot(r.out/'failure.png')
   except Exception as capture_error:
    failure['screenshot_error']=repr(capture_error)
    (out/'failure.json').write_text(json.dumps(failure,indent=2)+'\n')
   finally:r.close()
  raise
if __name__=='__main__':main()
