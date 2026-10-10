#!/usr/bin/env python3
"""Adaptive controller Magma diagnostic from genuine I2 South SRAM.

Use for the linked ordinary-save budget probe only. No game RAM writes or
machine states; no source-complete or empty-SRAM acceptance claim.
"""
from pathlib import Path
import argparse,gzip,json,shutil,sys,traceback
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from journey_guidance_earned import RegionalJourney
from player_feedback_native import sha

class ProbeJourney(RegionalJourney):
 def __init__(self,*a,**kw):self.room44_rows=[];super().__init__(*a,**kw)
 def raw_step(self,n,keys=0):
  for _ in range(n):
   before_room=self.get('room');before=self.get('frame');page=self.e.read(0x04000000,2)&16;super().raw_step(1,keys)
   if self.mode=='journey'and (before_room==44 or self.get('room')==44):
    r={'hardware_frame':self.e.frame,'keys':keys,'delta':(self.get('frame')-before)&0xffffffff,'flip':bool((self.e.read(0x04000000,2)&16)!=page),'room':self.get('room'),'state':self.get('game_state'),'cycles':self.get('render_cycles'),'x':self.get('px'),'y':self.get('py'),'game_frame':self.get('frame'),'writer_phase':self.get('writer_phase'),'writer_status':self.get('writer_status'),'save_background':self.get('save_feedback_background'),'save_step_cycles':self.get('save_step_cycles'),'save_begin_cycles':self.get('save_begin_cycles'),'save_requested':self.get('save_requested'),'preflight_status':self.e.read(self.sym['preflight']+8),'preflight_phase':self.e.read(self.sym['preflight']+12),'magma_puzzle':list(self.e.bytes(self.sym['magma_game_puzzle'],4)),'grab':self.e.read(self.locals['magma_game.c:grab'][0],1)}
    serial=self.get('render_profile_serial')
    if not serial&1:r['completed_profile']={'serial':serial,**{n:self.get('render_profile_'+n)for n in ('frame','state','room','update','save','render','world','card','actors','save_begin','save_step','music','vblank_cycles','vblank_start','vblank_end','commit')}}
    self.room44_rows.append(r)
 def diagnostic_report(self):
  rows=self.room44_rows
  result={'diagnostic_only':True,'acceptance_claim':False,'candidate':self.candidate,'controller_only':True,'game_ram_writes':0,'machine_state_imports':0,'origin':self.provenance,'route_complete':self.route_complete,'failures':self.failures,'checks':len(self.checks),'scope':'Adaptive same-route controller replay of the complete Magma chapter from genuine I2 South SRAM. All room44 push/turn/release frames included.','room44':{'observations':len(rows),'missed_updates':sum(r['delta']!=1 for r in rows),'missed_flips':sum(not r['flip']for r in rows),'cycle_overruns':sum(r['cycles']>=280896 for r in rows),'peak_cycles':max((r['cycles']for r in rows),default=0),'rows':rows}}
  (self.out.parent/'diagnostic.json').write_text(json.dumps(result,indent=2)+'\n')
  return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('probe','origin-report','bridge','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--snapshot',default='south-south-main-before-continue');a=p.parse_args()
 assert not a.output.exists()or not any(a.output.iterdir());a.output.mkdir(parents=True,exist_ok=True)
 manifest=json.loads((a.probe/'probe.json').read_text());a.rom=(a.probe/'emberbond.gba').resolve();a.symbols=(a.probe/'emberbond.sym').resolve();a.source_root=ROOT
 for name in ('emberbond.gba','emberbond.sym','emberbond.elf'):assert sha(a.probe/name)==manifest['candidate'][name]
 a.expected_rom_sha=sha(a.rom);a.expected_symbols_sha=sha(a.symbols)
 a.candidate={'rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols),'elf_sha256':sha(a.rom.with_suffix('.elf')),'source_manifest_sha256':sha(a.probe/'probe.json'),'source_manifest_kind':'diagnostic linked-object manifest; not source-complete acceptance','bridge_sha256':sha(a.bridge)}
 a.baseline=False;a.cross_rom_diagnostic=True;a.diagnostic_boundary_report=a.origin_report;a.stop_after='magma'
 source=Path(json.loads(a.origin_report.read_text())['snapshots'][a.snapshot]['sram_path'])
 helpers={}
 for d,pattern in (('tests','*.py'),('tools','mgba_runner.py')):
  for f in (ROOT/d).glob(pattern):
   target=a.output/'helper-source'/d/f.name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,target);helpers[str(f.relative_to(ROOT))]=sha(target)
 (a.output/'helper-source-hashes.json').write_text(json.dumps(helpers,indent=2)+'\n');shutil.copyfile(a.probe/'probe.json',a.output/'probe.json');r=None
 try:
  r=ProbeJourney(a,source,a.origin_report);r.chapter='magma';r.entry(38);r.magma_route();r.history=['magma'];r.route_complete=True;r.snapshot('save-budget-probe-finished')
 except Exception as ex:
  traceback.print_exc()
  if r:r.failures.append({'error':repr(ex),'status':r.status()});r.e.screenshot(r.out/'failure.png')
 finally:
  if r:
   result=r.diagnostic_report();r.close();print(json.dumps({k:v for k,v in result.items()if k not in ('origin','room44')},indent=2));print(json.dumps({k:v for k,v in result['room44'].items()if k!='rows'},indent=2))
 if not r:return 1
 return int(not result['route_complete']or bool(result['failures'])or any(result['room44'][k]for k in ('missed_updates','missed_flips','cycle_overruns')))
if __name__=='__main__':raise SystemExit(main())
