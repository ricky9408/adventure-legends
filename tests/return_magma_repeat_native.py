#!/usr/bin/env python3
"""Pinned cold-SRAM controller diagnostic for bounded historical Magma repeats.

Imports only earned current7 SRAM, never cross-ROM machine state or game RAM.
Native cadence retains every sampled frame, including transitions and saves.
"""
import argparse,json,traceback
from pathlib import Path
from return_legacy_baseline import Baseline
from return_journey import ROOT,digest,PLAY
from magma_journey import MagmaJourney
from return_followup_diagnostics import Followup
from northern_journey import newest_bank
class Repeat(Baseline):
 travel=Followup.travel
 entry=Followup.entry
 leave_interior=Followup.leave_interior
 mask=Followup.mask
 def __init__(self,args):
  super().__init__(args)
  self.fixture=args.fixture.resolve();assert digest(self.fixture)=='3c7e60a2e7a791a136eb82cbb45757e371e7adb12a230c9133db5e6a3a363f3d'
  self.source_bytes=self.fixture.read_bytes();self.source_bank=newest_bank(self.source_bytes)
  self.provenance={'fixture':str(self.fixture),'sram_sha256':digest(self.fixture),'cross_rom_machine_state_loaded':False,'earned104_52_source':'return-controller-b-legacy-repeats-02/failure.sav'}
  self.e.load_save(self.fixture);self.e.reset()
 def run(self):
  self.step(150);self.measured('bounded-cold-current7-continue',lambda:(self.tap('START',2,90),self.settle()),cold_continue=True)
  self.check(self.get('room')==39 and self.get('game_state')==PLAY,'authenticated104/52 SRAM resumes39')
  self.check(len(self.live())==52 and len(self.collection())==104,'current7 fixture starts104/52')
  self.check(newest_bank(self.e.bytes(0x0e000000,32768))[32:]==self.source_bank[32:],'cold boot preserves current7 payload')
  self.clear_enemies();self.goto(80,248,radius=4);self.face(1);self.step(120)
  original=self.state();signature=(bytes(original.roster),bytes(original.quests),bytes(original.equipment))
  self.measured('branch37-first-prompt',lambda:(self.tap('A',2,5),self.settle()))
  self.measured('branch37-B-cancel-preparation',lambda:(self.tap('A',2,5),self.tap('B',2,5),self.settle()))
  now=self.state();self.check((bytes(now.roster),bytes(now.quests),bytes(now.equipment))==signature,'B canceled pending repeat without durable change')
  for form,area,x,y in ((37,39,80,232),(40,41,176,64),(43,40,160,112),(46,39,424,240)):
   self.travel(area,clear=True);self.goto(x,y+16,radius=4);self.face(1);self.step(120)
   previous={c.instance_id:bytes(c) for c in self.live()};old=self.state();history=self.collection()
   self.measured('bounded-legacy-invitation-'+str(form),lambda:(self.tap('A',2,120),self.settle(),self.tap('A',2,120),self.settle()))
   fresh=[c for c in self.live() if c.instance_id not in previous]
   self.check(len(fresh)==1 and fresh[0].form_id==form,'repeat'+str(form)+' grants exactly one real base individual')
   self.check(all(bytes(c)==previous[c.instance_id] for c in self.live() if c.instance_id in previous),'all previous individual bytes remain exact')
   now=self.state();self.check(self.collection()==history,'repeat keeps104 histories')
   self.check(bytes(now.roster.lifetime_field_aid)==bytes(old.roster.lifetime_field_aid) and bytes(now.roster.expedition_events)==bytes(old.roster.expedition_events),'repeat has no event credit')
   self.check(bytes(now.roster.party)==bytes(old.roster.party) and now.roster.selected_party==old.roster.selected_party,'repeat preserves party selection')
   self.snapshot('repeat'+str(form)+'-after')
  self.check(len(self.live())==56,'four repeats52→56');self.finished=True;self.report()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('rom','symbols','source-manifest','source-root','output'):p.add_argument('--'+n,type=Path,required=True)
 for n in ('expected-rom-sha','expected-symbols-sha','expected-elf-sha','expected-manifest-sha'):p.add_argument('--'+n,required=True)
 p.add_argument('--expected-revision',type=int,default=7);p.add_argument('--fixture',type=Path,default=ROOT/'build/return-controller-b-legacy-repeats-02/failure.sav');a=p.parse_args();r=Repeat(a)
 try:r.run()
 except Exception as e:r.failures.append({'error':str(e),'traceback':traceback.format_exc(),'status':r.status()});r.snapshot('failure');raise
 finally:r.report();r.e.close()
 return bool(r.failures)
if __name__=='__main__':raise SystemExit(main())
