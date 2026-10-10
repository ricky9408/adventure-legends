#!/usr/bin/env python3
"""Controller-only companion menus on an immutable ROM and authenticated SRAM.

This inspects an existing developer collection, not a fresh acquisition route.
No game-memory writes, state imports, inputs during save writes or real user save.
"""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_native import Native
from test_save5 import Save

def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--save',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True);(args.output/'companion_guide_native.py').write_text(Path(__file__).read_text())
 symbols={v[2]:int(v[0],16) for line in args.symbols.read_text().splitlines() if len(v:=line.split())==3}
 e=Native(args.rom,args.bridge);inputs=[];captures=[];profiles=[]
 def g(n):return e.read(symbols[n],4)
 def step(frames=1,buttons=0):
  inputs.append({'frame':e.frame,'frames':frames,'buttons':buttons})
  for _ in range(frames):
   e.frames(1,buttons)
   if g('game_state')==3:profiles.append({'hardware_frame':e.frame,'bitmap_page':(e.read(0x04000000,2)>>4)&1,**{n:g(n) for n in ['frame','render_cycles','render_profile_state','render_profile_serial','render_profile_card','render_profile_update','render_profile_render','render_profile_vblank_start','render_profile_vblank_end','render_profile_vblank_cycles','render_profile_music','render_profile_save']}})
 def tap(buttons):step(2,buttons);step(5)
 def snapshot():return e.bytes(symbols['adventure_save'],C.sizeof(Save))
 def state():return Save.from_buffer_copy(snapshot())
 def shot(name):
  step(4);path=args.output/(name+'.png');e.screenshot(path);captures.append({'file':path.name,'sha256':digest(path),'frame':e.frame,'state':{n:g(n) for n in ['journal_tab','quickparty_menu_candidate','quickparty_menu_detail','quickparty_menu_command','progression_menu_detail','progression_menu_command','companion_guide_page']}})
 def browse(index):
  assert g('journal_tab')==2 and not g('quickparty_menu_detail')
  for _ in range(162):
   if g('quickparty_menu_candidate')==index:return
   tap('DOWN')
  raise AssertionError('owned candidate inaccessible')
 try:
  e.load_save(args.save);e.reset();step(160);tap('A');step(240)
  for _ in range(1800):
   if g('game_state')==1 and not g('scene_present_phase') and not g('save_feedback_background') and not g('save_requested'):break
   step()
  assert g('game_state')==1 and not g('scene_present_phase')
  tap('START');assert g('game_state')==3;baseline=snapshot();s=state();cooldown=g('ability_cd');heal=g('heal_cd')
  owned=[i for i,c in enumerate(s.roster.instances) if c.flags&1];assert len(owned)==72
  tap('DOWN');tap('A');assert g('journal_tab')==2;shot('01-party-browse')
  stored=next(i for i in owned if i not in s.roster.party);browse(stored);tap('A');assert g('quickparty_menu_detail')==1;shot('02-stored-combat')
  tap('DOWN');assert g('companion_guide_page')==1;shot('03-stored-field');step(70,'RIGHT');step(5);tap('SELECT');tap('R')
  assert snapshot()==baseline and g('ability_cd')==cooldown and g('heal_cd')==heal
  tap('B');assert g('journal_tab')==2 and not g('quickparty_menu_detail')
  # Five phases and both saved polarities, using actual retained individual data.
  phase_forms={};polarities=set()
  # Read only the native catalog and its byte index, never infer sparse identity.
  for index in owned:
   c=s.roster.instances[index];row=e.read(symbols['creature_form_index']+c.form_id,1);assert row
   phase=e.read(symbols['creature_forms']+(row-1)*32+2,1);phase_forms.setdefault(phase,index);polarities.add(int(c.polarity))
  assert len(phase_forms)==5 and polarities=={0,1}
  for phase,index in phase_forms.items():
   browse(index);tap('A');assert g('quickparty_menu_detail');shot(f'04-phase-{phase}');tap('B')
  # Name-width extremum among retained forms is readable at the same full width.
  for index in owned:
   if s.roster.instances[index].form_id==128:
    browse(index);tap('A');shot('05-late-companion');tap('B');break
  tap('B');assert g('journal_tab')==13;tap('RIGHT');tap('A');assert g('journal_tab')==3
  shot('06-growth-browse');tap('A');assert g('progression_menu_detail');shot('07-growth-combat')
  tap('DOWN');shot('08-growth-field');step(70,'RIGHT');step(5);tap('SELECT');tap('R')
  assert snapshot()==baseline and g('ability_cd')==cooldown and g('heal_cd')==heal
  tap('B');assert g('journal_tab')==3 and not g('progression_menu_detail');tap('A');assert g('progression_menu_detail');tap('START');assert g('game_state')==1
  # Freeze again before comparing persistence; normal PLAY can advance counters.
  tap('START');assert g('game_state')==3
  # Explicit commits run only after purity evidence, on this copied developer save.
  def settle_save():
   for _ in range(2400):
    if g('game_state')==3 and not g('save_requested') and not g('save_feedback_background'):return
    step()
   raise AssertionError('menu save did not settle')
  tap('DOWN');tap('A');assert g('journal_tab')==2;target=g('quickparty_menu_slot');browse(stored);before_assign=snapshot();tap('A');assert g('quickparty_menu_detail') and snapshot()==before_assign
  tap('A');settle_save();assert state().roster.party[target]==stored and not g('quickparty_menu_detail');shot('09-explicit-party-assignment')
  tap('B');tap('RIGHT');tap('A');assert g('journal_tab')==3;before_equip=snapshot();tap('A');assert g('progression_menu_detail') and snapshot()==before_equip
  old=g('progression_menu_command');tap('RIGHT');next_command=g('progression_menu_command');assert next_command!=old and snapshot()==before_equip;shot('10-explicit-command-preview');tap('A');settle_save()
  after_equip=state();member=after_equip.roster.instances[after_equip.roster.party[after_equip.roster.selected_party]];assert member.equipped[member.selected_command]==next_command and not g('progression_menu_detail');shot('11-explicit-command-equipped')
  assert not int(e.lib.eb_faults(e.ptr))
  result={'rom_sha256':digest(args.rom),'symbols_sha256':digest(args.symbols),'fixture_sha256':digest(args.save),'evidence_scope':'controller-only browsing of historical developer full collection; not fresh acquisition or all-form gameplay','owned_individuals':len(owned),'inspected_phases':sorted(phase_forms),'saved_polarities':sorted(polarities),'save_unchanged_while_browsing':True,'recovery_unchanged_while_browsing':True,'native_core_faults':int(e.lib.eb_faults(e.ptr)),'party_second_a_commits':True,'command_second_a_commits':True,'no_game_memory_writes':True,'no_machine_state_imports':True,'harness_sha256':digest(args.output/'companion_guide_native.py'),'captures':captures,'inputs':inputs,'profiles':profiles}
  (args.output/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['inputs','profiles','captures']},indent=2))
 finally:e.close()
if __name__=='__main__':main()
