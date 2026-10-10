#!/usr/bin/env python3
"""Fresh controller-earned Water recruitment, trial, evolution and two-way shortcut.

Default starts empty SRAM. Optional prefix reuse is authenticated same-candidate
controller-earned progress only; no RAM writes or machine-state imports.
"""
from pathlib import Path
from types import SimpleNamespace
import argparse,gzip,json,shutil,traceback
from journey_guidance_earned import RegionalJourney
from treasure_full_journey import TreasureOriginalJourney
from player_feedback_native import sha
ROOT=Path(__file__).resolve().parents[1]

class WaterRoute(RegionalJourney):
 def proof_state(self):
  row=super().proof_state();c=next((x for x in self.roster().instances if x.flags&1 and x.form_id in (13,14)),None)
  row.update(water_quest=self.quest(2),pool_trial_quest=self.quest(4),water=None if c is None else {'instance_id':c.instance_id,'form':c.form_id,'level':c.level,'xp':c.xp,'bond':c.bond,'trial_flags':c.trial_flags,'equipped':list(c.equipped),'selected_command':c.selected_command})
  return row
 def report(self):
  super().report();p=self.out/'report.json'
  if p.is_file():
   r=json.loads(p.read_text());r.update(suite='fresh-earned-water-shortcut',scope='empty-SRAM original prefix, Water recruitment, paired-pool trial, A-confirm evolution and learned command, two-way basin shortcut and own-save Continue',full_collection_proven=False);p.write_text(json.dumps(r,indent=2)+'\n')
 def shot(self,name):self.raw_step(3);self.e.screenshot(self.out/(name+'.png'))
 def wait_prepared(self):
  pairing=self.evolution_observer()
  for _ in range(180):
   if self.get('game_state')==7 and self.e.read(pairing['address']+8)==0:break
   self.raw_step(1)
  self.check(self.get('game_state')==7 and self.e.read(pairing['address']+8)==0 and self.get('progression_evolution_reason')==0,'earned Water evolution reaches genuinely eligible prepared confirmation')
 def courtyard_entry(self):
  self.check(self.get('room')==17,'pool courtyard approach starts in basin')
  self.goto(360,63)
  for _ in range(90):
   if self.get('room')!=17:break
   self.step(1,'UP')
  self.settle();self.check(self.get('room')==19,'walk through real Tide courtyard doorway')
 def run(self):
  self.chapter='water';self.main_only=False
  self.travel(16);self.entry(17)
  self.check(self.quest(2)==0 and not any(c.flags&1 and c.form_id in (13,14) for c in self.roster().instances),'fresh basin has no Water recruitment or evolved progress')
  self.assign(0,1);self.assign(1,4);self.assign(2,7);self.assign(3,10)
  self.act(264,216);self.cast(4,240,199)
  self.check(self.state().quests.objectives[1]==3,'actual handle and Nature power restore dry road')
  self.act(120,232);self.cast(4,98,44);self.cast(7,184,88);self.act(184,88)
  self.check(self.quest(2)==3 and sum(c.flags&1 and c.form_id==13 for c in self.roster().instances)==1,'reeds and wind care recruit exactly one base Water companion')
  self.assign(3,13);self.select_form(13);identity=self.selected().instance_id;self.snapshot('water-recruited')
  self.courtyard_entry();self.cast(13,64,86)
  self.check(self.e.bytes(self.sym['region_game_pool_levels'],2)==bytes((1,0)),'first real Water cast fills only the first paired pool before reset')
  self.act(48,132);self.check(self.e.bytes(self.sym['region_game_pool_levels'],2)==bytes(2),'ordinary A reset clears partially filled paired pools')
  self.cast(13,64,86);self.cast(13,176,86);self.act(64,130);self.act(176,130)
  self.check(self.quest(4)==3 and self.selected().trial_flags&16,'base Water power and two valves earn paired-pool trial')
  self.check(self.selected().form_id==13 and self.selected().level>=15 and self.selected().bond>=45,'authored trial rewards satisfy Water evolution without injected training')
  self.snapshot('paired-pools-earned');self.leave_interior(17);self.act(120,232);self.select_form(13)
  self.open_tab(3);self.tap('DOWN');before=bytes(self.selected());old=self.selected()
  self.tap('A');self.wait_prepared();self.shot('water-evolution-confirm');self.tap('B')
  self.check(self.get('game_state')==3 and bytes(self.selected())==before,'B cancels prepared evolution without changing any individual byte')
  self.tap('A');self.wait_prepared();self.raw_step(2,'A');self.raw_step(3);animated=False
  for _ in range(600):
   if self.get('game_state')==8 and not animated:self.shot('water-evolution-animation');animated=True
   if self.get('game_state')==3:break
   self.raw_step(1)
  self.check(animated and self.get('game_state')==3 and self.selected().form_id==14,'fresh A animates earned Water evolution and returns to Growth')
  c=self.selected();self.check((c.instance_id,c.xp,c.bond,c.trial_flags,c.cosmetic_seed)==(old.instance_id,old.xp,old.bond,old.trial_flags,old.cosmetic_seed),'evolution preserves Water identity and earned personal progress')
  self.check(c.instance_id==identity and c.equipped[c.selected_command]==9,'evolution keeps same recruited individual and its original command')
  self.shot('water-evolved-original-command');self.close_menu();self.goto(296,140);self.ready();before_xy=(self.get('px'),self.get('py'));self.check(self.get('field_pool_mask')==0,'basin pools are unfilled before testing original Water command');self.tap('R');self.settle()
  self.check((self.get('px'),self.get('py'))==before_xy and self.get('field_pool_mask')==1,'retained original Water command fills exactly the near pool without shortcut movement')
  self.open_tab(3);self.tap('RIGHT')
  self.check(self.get('progression_menu_command')==10 and self.selected().equipped[self.selected().selected_command]==9,'Right previews learned command without changing equipped power')
  self.tap('A');self.check(self.get('progression_menu_detail')==1 and self.selected().equipped[self.selected().selected_command]==9,'first A opens learned-command details without equipping')
  self.shot('water-learned-command-detail');self.tap('A')
  self.check(self.selected().equipped[self.selected().selected_command]==10,'second fresh A equips learned Water link command')
  self.close_menu();self.ready();self.tap('R');self.settle()
  self.check((self.get('px'),self.get('py'))==(424,124),'learned Water link crosses to authored far basin')
  self.snapshot('shortcut-crossed');self.ready();self.tap('R');self.settle()
  self.check((self.get('px'),self.get('py'))==(296,140),'same learned command returns through authored shortcut')
  self.snapshot('shortcut-returned');self.cold_reboot('water-shortcut')
  self.check(self.quest(2)==3 and self.quest(4)==3 and self.selected().form_id==14 and self.selected().instance_id==identity and self.selected().equipped[self.selected().selected_command]==10,'cold Continue retains earned Water evolution, trial and explicitly equipped learned command')
  self.check(self.get('room')==17,'cold Continue returns to actual basin checkpoint')
  self.goto(296,140);self.ready();self.tap('R');self.settle();self.check((self.get('px'),self.get('py'))==(424,124),'learned shortcut remains usable after cold Continue')
  self.ready();self.tap('R');self.settle();self.check((self.get('px'),self.get('py'))==(296,140),'post-Continue shortcut also returns safely')
  self.snapshot('shortcut-persisted');self._frames.close()
  measured=[json.loads(line) for line in gzip.open(self.out/'native-frames.jsonl.gz','rt')];measured=[r for r in measured if r['phase']=='journey']
  self.check(bool(measured) and all(r['delta']==1 and r['flip'] and r['cycles']<280896 for r in measured),'every measured Water gameplay, menu, evolution and shortcut frame presents within hardware budget')
  self.route_complete=True;self.history=['water'];self.coverage=['controller-earned-water-recruitment','paired-pool-reset-and-trial','A-confirm-water-evolution','learned-command-detail-before-A-equip','two-way-basin-shortcut','own-save-Continue-retains-shortcut'];self.report()

def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--prefix-report',type=Path);p.add_argument('--prefix-report-sha');p.add_argument('--bridge',type=Path,default=ROOT/'build/player-feedback-bridge.so');opts=p.parse_args()
 out=opts.output.resolve()
 if opts.prefix_report:
  source_directory=opts.prefix_report.resolve().parent
  assert out!=source_directory and source_directory not in out.parents,'output must not be inside supplied prefix evidence'
 out.mkdir(parents=True,exist_ok=False)
 a=SimpleNamespace(output=out,rom=ROOT/'build/emberbond.gba',symbols=ROOT/'build/emberbond.sym',bridge=opts.bridge.resolve(),source_root=ROOT,baseline=False,cross_rom_diagnostic=False,stop_after='water',diagnostic_boundary_report=None)
 a.expected_rom_sha=sha(a.rom);a.expected_symbols_sha=sha(a.symbols);a.candidate={'rom_sha256':a.expected_rom_sha,'symbols_sha256':a.expected_symbols_sha,'elf_sha256':sha(a.rom.with_suffix('.elf')),'source_manifest_sha256':sha(ROOT/'build/source-hashes.json'),'bridge_sha256':sha(a.bridge)}
 manifest=json.loads((ROOT/'build/source-hashes.json').read_text());assert all(sha(ROOT/n)==v for n,v in manifest.items())
 shutil.copyfile(__file__,out/'fresh_water_shortcut.py');(out/'candidate.json').write_text(json.dumps({**a.candidate,'test_sha256':sha(__file__)},indent=2)+'\n')
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
  r=WaterRoute(a,sram,prefix);r.run();r.close();r=None
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
