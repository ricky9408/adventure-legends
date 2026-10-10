#!/usr/bin/env python3
"""Native locked-branch display on an authenticated, controller-earned fixture.

The fixture owns unevolved49. This tests inspection/cancellation, not a newly
completed evolution trial or native acquisition. No game RAM/state imports.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_native import Native
from test_save5 import Save

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);(a.output/'companion_branch_native.py').write_text(Path(__file__).read_text())
 fixture=ROOT/'tests/fixtures/v5-revision6/underwater-minimal12-town.sav';provenance=json.loads((fixture.parent/'provenance.json').read_text());record=next(f for f in provenance['fixtures'] if f['fixture']==fixture.name);assert sha(fixture)==record['sha256']
 sym={v[2]:int(v[0],16) for line in a.symbols.read_text().splitlines() if len(v:=line.split())==3};e=Native(a.rom,a.bridge);inputs=[];captures=[];profiles=[]
 def g(n):return e.read(sym[n],4)
 def step(n=1,k=0):
  inputs.append({'hardware_frame':e.frame,'frames':n,'buttons':k})
  for _ in range(n):
   e.frames(1,k)
   if g('game_state') in (3,7):profiles.append({'hardware_frame':e.frame,'bitmap_page':(e.read(0x04000000,2)>>4)&1,**{x:g(x) for x in ['frame','game_state','render_cycles','render_profile_serial','render_profile_state','render_profile_update','render_profile_render','render_profile_vblank_start','render_profile_vblank_end']}})
 def tap(k):step(2,k);step(5)
 def snapshot():return e.bytes(sym['adventure_save'],C.sizeof(Save))
 def settle():
  for _ in range(2400):
   if g('game_state') in (1,3) and not g('scene_present_phase') and not g('save_requested') and not g('save_feedback_background'):return
   step()
  raise AssertionError('save or scene failed to settle')
 def shot(name):
  step(5);f=a.output/(name+'.png');e.screenshot(f);captures.append({'file':f.name,'sha256':sha(f),'target':g('progression_evolution_target'),'reason':g('progression_evolution_reason'),'frame':e.frame})
 try:
  e.load_save(fixture);e.reset();step(160);tap('A');step(240);settle();assert g('game_state')==1;tap('START');tap('DOWN');tap('A');assert g('journal_tab')==2
  for _ in range(161):
   if g('quickparty_menu_candidate')==10:break
   tap('DOWN')
  s=Save.from_buffer_copy(snapshot());assert s.roster.instances[10].form_id==49
  tap('A');assert g('quickparty_menu_detail');tap('A');settle();s=Save.from_buffer_copy(snapshot());slot=list(s.roster.party).index(10)
  # An already-active instance swaps slots without changing selected identity.
  # Explicitly select the assigned slot through the preserved held-L picker.
  tap('START');tap('L+'+['UP','RIGHT','DOWN','LEFT'][slot]);s=Save.from_buffer_copy(snapshot());assert s.roster.party[s.roster.selected_party]==10
  tap('START');tap('DOWN');tap('RIGHT');tap('A');assert g('journal_tab')==3;tap('DOWN');assert g('progression_menu_row')==1
  baseline=snapshot();tap('A');assert g('game_state')==7 and g('progression_evolution_count')==2;assert g('progression_evolution_reason')!=0;shot('01-first-water-branch')
  first=g('progression_evolution_target');tap('RIGHT');assert g('progression_evolution_target')!=first;shot('02-second-water-branch');tap('A');assert snapshot()==baseline and g('game_state')==7
  tap('LEFT');assert g('progression_evolution_target')==first;tap('B');assert g('game_state')==3 and snapshot()==baseline
  tap('A');assert g('game_state')==7;tap('START');assert g('game_state')==1;assert not e.lib.eb_faults(e.ptr)
  result={'rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols),'fixture_sha256':sha(fixture),'harness_sha256':sha(a.output/'companion_branch_native.py'),'source_form':49,'visible_target_forms':[50,51],'scope':'controller-earned historical fixture; locked branch inspection only, not a new trial/evolution success','save_unchanged_during_choice_and_cancel':True,'b_back_start_close':True,'ineligible_a_no_commit':True,'no_game_memory_writes':True,'no_machine_state_imports':True,'faults':0,'captures':captures,'inputs':inputs,'profiles':profiles};(a.output/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['captures','inputs','profiles']},indent=2))
 finally:e.close()
if __name__=='__main__':main()
