#!/usr/bin/env python3
"""SUPPLEMENTAL SYNTHETIC guard provenance/direction test, never earned QA.

Only public scene/roster setup writes are inherited from the feasibility probe.
The real engine creates every projectile; no projectile or power-private bytes
are injected. Boss source is unavailable in the already-cleared earned roster.
"""
import argparse,ctypes as C,json,shutil,traceback
from pathlib import Path
from return_powers_engine_native import Probe,SHA,ROOT
from return_companion_controls import Cast
from magma_journey import elf_locals

class Guards(Probe):
 def setup_case(self,command,source):
  self.setup(command,source!='boss')
  if source=='rear':
   self.put('enemies',115,4,4);self.put('enemy_aimy',-2);self.put('enemy_windups',12)
  if source=='boss':
   for name,value in {'room':3,'chapter_flags':0,'boss_x':120,'boss_y':65,'boss_hp':12,'boss_hp_q4':192,'boss_hp_max':12,'boss_armor':0,'boss_time':99,'boss_flash':0}.items():self.put(name,value)
  self.address,self.size=self.locals['return_powers.c:cast'];assert self.size==C.sizeof(Cast)
 def observe(self):
  d=self.state();c=Cast.from_buffer_copy(self.e.bytes(self.address,self.size));d.update(guard_used=c.guard_used,charged=c.charged,obj=self.get('obj_count'),game_state=self.get('game_state'),boss_time=self.get('boss_time'));return d
 def one(self,command,source):
  self.setup_case(command,source);trace=[self.observe()]
  for n in range(90):self.e.frames(1,'R'if n==0 else 0);trace.append(self.observe())
  observed=[(r['age'],s)for r in trace for s in r['shots']if s[4]>0 and s[5] and s[0]==120]
  used=any(r['guard_used']for r in trace)
  if source=='front':assert used and any(s[6]for _,s in observed),'ordinary front shot was not caught'
  else:
   assert not used,('ineligible shot consumed guard',command,source)
   assert any(s[1]<104 if source=='rear'else s[1]>108 for _,s in observed),('projectile did not visibly pass guard',command,source)
   assert all(s[6]==(source=='rear')for _,s in observed),'wrong native projectile provenance'
  cadence=[dict(hardware=b['hardware_frame']-a['hardware_frame'],updates=b['update_counter']-a['update_counter'],flip=b['display_page']!=a['display_page'],cycles=b['render_cycles'],obj=b['obj'])for a,b in zip(trace,trace[1:])]
  misses=[r for r in cadence if r['hardware']!=1 or r['updates']!=1 or not r['flip']or r['cycles']>=280896 or r['obj']>128]
  self.rows.append({'command':command,'source':source,'synthetic_scene_setup':True,'projectiles_written':False,'power_private_state_written':False,'actual_engine_generated_projectiles':True,'guard_used':used,'maximum_cycles':max(r['cycles']for r in cadence),'native_frame_trace':trace,'cadence':cadence,'cadence_exceptions':misses})
  self.e.screenshot(self.out/f'guard-{command}-{source}.png');self.e.close();self.report();assert not misses,('native cadence failure',misses)
 def report(self):
  if not hasattr(self,'writes'):return
  d={'suite':'SUPPLEMENTAL-SYNTHETIC-native-guard-exclusions','controller_only':False,'excluded_from_earned_acquisition_and_art_acceptance':True,'ROM_sha256':self.a.rom_sha,'symbols_sha256':self.a.symbols_sha,'ELF_sha256':getattr(self,'elf_sha',None),'source_manifest_sha256':getattr(self,'manifest_sha',None),'source_closure_verified_before_and_after':getattr(self,'verified_after',False),'helper_sha256':SHA(__file__),'game_ram_setup_writes':self.writes,'projectile_or_power_private_state_writes':0,'cases':self.rows,'failures':self.failures}
  (self.out/'guard-exclusions.json').write_text(json.dumps(d,indent=2)+'\n')
 def run(self):
  self.manifest_sha=SHA(self.a.source/'build/source-hashes.json');source=json.loads((self.a.source/'build/source-hashes.json').read_text());assert all(SHA(self.a.source/k)==v for k,v in source.items())
  elf=self.a.source/'build/emberbond.elf';self.elf_sha=SHA(elf);self.locals=elf_locals(elf,self.a.rom)
  for p in (Path(__file__),ROOT/'tests/return_companion_controls.py',ROOT/'tests/return_powers_engine_native.py',ROOT/'tests/magma_journey.py',ROOT/'tools/mgba_runner.py',ROOT/'tools/mgba_bridge.so'):
   dest=self.out/'helper-source'/p.relative_to(ROOT);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(p,dest)
  try:
   for c in (92,103):
    for source_kind in ('front','rear','boss'):self.one(c,source_kind)
   self.verified_after=all(SHA(self.a.source/k)==v for k,v in source.items());assert self.verified_after
  except Exception as exc:self.failures.append({'error':str(exc),'traceback':traceback.format_exc()});raise
  finally:self.report()
def main():
 p=argparse.ArgumentParser(description=__doc__);p.add_argument('--source',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.source=a.source.resolve();a.rom=a.source/'build/emberbond.gba';a.symbols=a.rom.with_suffix('.sym');a.rom_sha=SHA(a.rom);a.symbols_sha=SHA(a.symbols);a.fixture=ROOT/'tests/fixtures/v5-revision6/underwater-all89-town.sav';Guards(a).run()
if __name__=='__main__':main()
