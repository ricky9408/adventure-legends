#!/usr/bin/env python3
"""Separately labeled authenticated predecessor-SRAM Magma66 diagnostic.

The original same-candidate/frozen-v5 acceptance guards remain unchanged.
Authenticate the I acquisition by running their unchanged same-I constructor,
then cold-import only those exact SRAM bytes into K. No predecessor machine
state is loaded. All actual controls and cadence checks reuse lifetime(66).
Final release acceptance still requires freshly earned same-ROM sources.
"""
import argparse,copy,json,shutil
from pathlib import Path
from magma_combat_tests import MagmaCombat,ROOT,digest
from magma_journey import MagmaJourney
p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--source-workspace',required=True,type=Path);p.add_argument('--source-report-sha',required=True)
p.add_argument('--candidate',required=True,type=Path);p.add_argument('--expected-rom-sha',required=True);p.add_argument('--expected-symbols-sha',required=True)
p.add_argument('--output',required=True,type=Path);a=p.parse_args()
source=a.source_workspace.resolve();candidate=a.candidate.resolve();out=a.output.resolve();out.mkdir(parents=True,exist_ok=True)
report=source/'build/magma-journey/magma-journey.json';assert digest(report)==a.source_report_sha
# This invokes all unchanged source/ELF/ROM/SRAM/history/identity checks on I.
verified=MagmaCombat(source/'build/emberbond.gba',source/'build/emberbond.sym',out/'source-authentication',digest(source/'build/emberbond.gba'),digest(source/'build/emberbond.sym'),report,'09-all65-earned-town',source/'build/source-hashes.json',None)
evidence=copy.deepcopy(verified.source_evidence);source_record=copy.deepcopy(verified.snapshots[verified.source_snapshot]);fixture=verified.fixture;verified.e.close()
assert len(evidence['historical_forms'])==65 and len(evidence['owned_forms'])==34
assert digest(Path(source_record['sram_path']))==evidence['sram_sha256']
class Diagnostic(MagmaCombat):
 def __init__(self):
  self.report_ready=False
  MagmaJourney.__init__(self,candidate/'emberbond.gba',candidate/'emberbond.sym',out/'replay',a.expected_rom_sha,a.expected_symbols_sha,fixture=fixture,source_manifest=candidate/'source-hashes.json')
  self.source_evidence=evidence;self.source_evidence.update(diagnostic_only=True,cross_rom_sram_import=True,source_machine_state_loaded=False,source_machine_state_policy='No predecessor machine state import; exact authenticated I SRAM only')
  self.source_snapshot='authenticated-predecessor-sram';record=copy.deepcopy(source_record)
  save=self.out/'authenticated-predecessor.sav';shutil.copyfile(record['sram_path'],save);assert digest(save)==evidence['sram_sha256'];record.update(sram_path=str(save),state_path=None)
  self.snapshots[self.source_snapshot]=record
  self.branch_loads=[];self.screenshots=[];self.accepted_commands=[];self.covered=[];self.native_write_attempts=[]
  self.source_checks={name:digest(self.source_root/name)==sha for name,sha in self.source_hashes.items()}
  assert all(self.source_checks.values())
  def deny(*args,**kwargs):self.native_write_attempts.append(repr(args));raise AssertionError('Game-memory writes are forbidden')
  self.e.write=deny;self.e.lib.eb_write=deny;self.report_ready=True
 def report(self):
  if not self.report_ready:return
  result={'suite':'magma66-cross-candidate-cold-SRAM-diagnostic','diagnostic_only':True,'same_rom_final_acceptance':False,'controller_only':True,'game_ram_writes':0,'game_ram_write_attempts':self.native_write_attempts,'cross_rom_machine_state_imports':0,**self.candidate,'source_manifest_sha256':self.source_manifest_sha,'frozen_source_checks':self.source_checks,'provenance':self.source_evidence,'observer_sha256':digest(__file__),'test_sources':self.test_sources,'branch_loads':self.branch_loads,'checks':self.checks,'failures':self.failures,'cases':self.cases,'frame_windows':self.frame_windows,'snapshots':self.snapshots,'inputs':self.inputs}
  (self.out/'diagnostic-report.json').write_text(json.dumps(result,indent=2)+'\n')
r=Diagnostic()
try:r.boot();r.run_case('lifetime-66',lambda:r.lifetime(66))
finally:r.report();r.e.close()
print(json.dumps({'passed':not r.failures,'checks':len(r.checks),'peak_cycles':max(w['max_cycles'] for w in r.frame_windows),'report':str(r.out/'diagnostic-report.json')},indent=2))
raise SystemExit(bool(r.failures))
