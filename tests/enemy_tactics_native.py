#!/usr/bin/env python3
"""Controller-only charger integration from authenticated unmodified earned SRAM.

Cross-ROM follow-up only; not fresh-campaign acquisition or subjective balance.
"""
from pathlib import Path
import argparse,hashlib,json,struct,sys,traceback
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from journey_guidance_earned import RegionalJourney
from player_feedback_native import sha

class ChargerRun(RegionalJourney):
 def __init__(self,*args):
  self.watch=False;self.samples=[];self.captures={};self.hitstop_frozen=0
  super().__init__(*args)
 def enemy(self):return struct.unpack('<5i',self.e.bytes(self.sym['enemies']+3*20,20))
 def value(self,name):return struct.unpack('<i',self.e.bytes(self.sym[name]+3*4,4))[0]
 def observation(self):
  return {'frame':self.e.frame,'enemy':self.enemy(),'warning':self.value('enemy_windups'),
          'clock':self.value('enemy_clocks'),'aim':[self.value('enemy_aimx'),self.value('enemy_aimy')],
          'hero':[self.get('px'),self.get('py')],'hp_q4':self.get('hero_hp_q4'),'hitstop':self.get('hitstop'),'state':self.get('game_state')}
 def capture(self,name):
  self.e.screenshot(self.out/(name+'.png'));self.captures[name]=self.observation()
 def raw_step(self,count,keys=0):
  for _ in range(count):
   old=self.observation() if self.watch else None
   super().raw_step(1,keys)
   if not self.watch:continue
   now=self.observation();self.samples.append(now)
   if old['hitstop'] and old['state']==now['state']==1:
    self.check(old['enemy']==now['enemy'] and old['clock']==now['clock'] and old['warning']==now['warning'],'actual hitstop freezes charger simulation')
    self.hitstop_frozen+=1
   for name,predicate in [('warning',now['warning']>0),('rush',now['clock']<0),('recovery',now['clock']>0),('interrupt',now['enemy'][3]>0),('dead',now['state']==4)]:
    if predicate and name not in self.captures:self.capture(name)
 def until(self,predicate,limit=1200,keys=0):
  for _ in range(limit):
   if predicate():return
   self.step(1,keys)
  raise AssertionError(('native condition timed out',self.observation()))
 def run(self):
  self.chapter='magma';self.entry(39)
  self.check(self.enemy()==(328,56,5,0,3),'one authored Magma39 slot keeps position and5HP')
  self.check(self.e.read(self.sym['enemy_phases']+3,1)==4,'authored Earth phase is unchanged')
  self.check(self.value('enemy_clocks')==self.value('enemy_windups')==0,'room arrival starts clean tactics')
  self.watch=True;self.capture('idle');self.goto(280,56,radius=2)
  self.until(lambda:self.value('enemy_windups')>0)
  start=self.observation();self.capture('warning-player-approach')
  # Move perpendicular to the locked horizontal lane using normal D-pad.
  self.goto(self.get('px'),88,radius=2)
  self.until(lambda:self.value('enemy_clocks')>0)
  end=self.observation();self.capture('sidestep-recovery')
  self.check(start['aim'][0]!=0 and start['aim'][1]==0 and end['enemy'][1]==start['enemy'][1],'charger holds its horizontal lane after player sidesteps')
  self.check(abs(end['hero'][1]-end['enemy'][1])>=20,'side-step leaves hero outside charge contact')
  # The recovery gives time to approach; then a real sword strike interrupts.
  self.equip_item(0,1);x,y=self.enemy()[:2];self.goto(x,y+18,radius=2);self.face(1)
  self.until(lambda:self.value('enemy_windups')>0)
  hp=self.enemy()[2];self.tap('A',8,2)
  self.until(lambda:self.enemy()[3]>0,60)
  self.check(self.enemy()[2]<hp and not self.value('enemy_windups') and self.value('enemy_clocks')>0,'real sword hit cancels warning into recovery')
  self.step(8);self.check(self.hitstop_frozen>0,'native hitstop freeze was observed')
  self.entry(38);self.entry(39)
  self.check(self.enemy()==(328,56,5,0,3) and not self.value('enemy_clocks') and not self.value('enemy_windups'),'real room re-entry restores actor and clears tactics')
  # Actual ordinary encounter death, no writes or scripted HP setup.
  self.goto(280,56,radius=2);self.until(lambda:self.get('game_state')==4,8000)
  dead=self.observation();self.step(20)
  self.check(self.observation()['enemy']==dead['enemy'] and self.value('enemy_clocks')==dead['clock'],'DEAD freezes the charger')
  self.tap('A',2,2);self.settle()
  self.check(self.get('game_state')==1 and self.enemy()==(328,56,5,0,3),'ordinary A death retry restores the authored actor')
  self.check(not self.value('enemy_clocks') and not self.value('enemy_windups'),'death retry discards prior warning/rush/recovery')
  self.capture('retry');self.route_complete=True
 def final_report(self):
  d={'scope':'Controller-only cross-ROM integration from earned unmodified SRAM; no fresh campaign or subjective balance claim',
     'candidate':self.candidate,'provenance':self.provenance,'checks':self.checks,'metrics':self.metrics,
     'captures':self.captures,'hitstop_frozen_frames':self.hitstop_frozen,'samples':self.samples,
     'game_ram_writes':0,'machine_state_imports':0,'completed':self.route_complete}
  (self.out/'enemy-tactics-report.json').write_text(json.dumps(d,indent=2)+'\n')
  self.report();return d

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('rom','symbols','bridge','source-manifest','source-report','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--snapshot',default='magma-magma-main-after-continue');a=p.parse_args()
 a.source_root=ROOT;a.cross_rom_diagnostic=True;a.baseline=False;a.diagnostic_boundary_report=a.source_report
 a.diagnostic_start_chapter='magma';a.stop_after='covenants';a.expected_rom_sha=sha(a.rom);a.expected_symbols_sha=sha(a.symbols)
 a.candidate={'rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols),'elf_sha256':sha(a.rom.with_suffix('.elf')),'source_manifest_sha256':sha(a.source_manifest),'bridge_sha256':sha(a.bridge)}
 assert all(sha(ROOT/n)==v for n,v in json.loads(a.source_manifest.read_text()).items())
 producer=json.loads(a.source_report.read_text());assert producer['route_complete'] and not producer['failures']
 save=Path(producer['snapshots'][a.snapshot]['sram_path']);assert sha(save)==producer['snapshots'][a.snapshot]['sram_sha256']
 assert not a.output.exists()or not any(a.output.iterdir());a.output.mkdir(parents=True,exist_ok=True)
 r=None
 try:r=ChargerRun(a,save,a.source_report);r.run();r.final_report()
 except Exception:
  if r:r.capture('failure');r.final_report()
  raise
 finally:
  if r:r.e.close()
 return 0
if __name__=='__main__':raise SystemExit(main())
