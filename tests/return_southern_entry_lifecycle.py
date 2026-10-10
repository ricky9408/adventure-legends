#!/usr/bin/env python3
"""Strict controller-only Southern rest/spawn2/death/SRAM-reload boundaries.
Uses the normal Return global hardware-frame producer and delivered revision6
SRAM. No RAM writes, cross-ROM states, gate changes or cadence exemptions.
"""
import argparse,traceback
from pathlib import Path
from return_journey import ReturnJourney,PLAY,DEAD
class SouthernEntryLifecycle(ReturnJourney):
 def south_field(self):
  self.goto(304,16);self.step(8,'UP');self.settle();self.check(self.get('room')==31,'ordinary north exit enters Southern field')
 def run_southern(self):
  self.boot();self.travel(30)
  self.check((self.get('px'),self.get('py'),self.get('checkpoint_spawn'))==(288,264,0),'Magma lift arrival preserves old safe coordinate and checkpoint0')
  self.snapshot('01-first-southern-return')
  self.target(112,208,1);self.check(self.get('checkpoint_spawn')==2,'actual Southern town rest binds checkpoint2')
  self.cold_reboot('02-southern-town-spawn2')
  self.check(self.get('room')==30 and self.get('checkpoint_spawn')==2,'cold town Continue preserves Southern spawn2')
  self.south_field();self.target(80,248,1)
  self.check(self.get('room')==31 and self.get('checkpoint_spawn')==2,'actual Southern field rest binds checkpoint2')
  self.cold_reboot('03-southern-field-spawn2')
  self.check(self.get('room')==31 and self.get('checkpoint_spawn')==2,'cold field Continue preserves Southern spawn2')
  before=self.state_signature();self.goto(208,264);damage=[]
  for _ in range(1000):
   damage.append({'hardware_frame':self.e.frame,'hp':self.get('hp'),'state':self.get('game_state')})
   if self.get('game_state')==DEAD:break
   self.step(10)
  self.cases.append({'name':'southern-real-enemy-death','trace':damage})
  self.check(self.get('game_state')==DEAD,'ordinary Southern enemy damage reaches death without health injection')
  self.snapshot('04-southern-death',settle=False)
  self.measured('whole-southern-spawn2-death-retry',lambda:(self.tap('A',2,30),self.settle()))
  self.check(self.get('game_state')==PLAY and self.get('room')==31 and self.get('checkpoint_spawn')==2 and self.get('hp')>0,'actual A retry consumes prepared Southern spawn2 and restores safe live play')
  self.check((self.get('px'),self.get('py'))==(80,264),'Southern death retry preserves the authored anchor landing')
  self.check(self.state_signature()==before,'death/retry preserves all exact creature, quest and equipment bytes')
  self.snapshot('05-southern-death-recovered');self.cold_reboot('06-southern-retry-reload')
  self.verify_closures();self.finished_scope='southern-entry-lifecycle'
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for name in ['rom','symbols','source-manifest','source-root','output']:p.add_argument('--'+name,type=Path,required=True)
 for name in ['expected-rom-sha','expected-symbols-sha','expected-elf-sha','expected-manifest-sha']:p.add_argument('--'+name,required=True)
 p.add_argument('--source-sram',type=Path);a=p.parse_args()
 r=SouthernEntryLifecycle(a.rom,a.symbols,a.output,a.expected_rom_sha,a.expected_symbols_sha,a.expected_elf_sha,a.source_manifest,a.expected_manifest_sha,a.source_sram,a.source_root,'strict')
 try:r.run_southern()
 except Exception as e:r.failures.append({'error':str(e),'traceback':traceback.format_exc(),'status':r.status()});r.snapshot('failure',settle=False);raise
 finally:r.close_global_trace();r.report();r.e.close()
if __name__=='__main__':main()
