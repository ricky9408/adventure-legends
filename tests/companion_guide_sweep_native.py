#!/usr/bin/env python3
"""Controller-only inherited-command UI sweep; no fresh-acquisition claim."""
from pathlib import Path
import argparse,ctypes as C,hashlib,json,sys
ROOT=Path(__file__).resolve().parents[1];sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_native import Native
from test_save5 import Save

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--save',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();a.output.mkdir(parents=True,exist_ok=True);(a.output/Path(__file__).name).write_text(Path(__file__).read_text())
 sym={v[2]:int(v[0],16) for line in a.symbols.read_text().splitlines() if len(v:=line.split())==3};e=Native(a.rom,a.bridge);inputs=[];profiles=[];captures=[];seen=set();label='loading'
 def g(n):return e.read(sym[n],4)
 def step(n=1,k=0):
  inputs.append({'hardware_frame':e.frame,'frames':n,'buttons':k})
  for _ in range(n):
   e.frames(1,k)
   if g('game_state')==3:profiles.append({'label':label,'hardware_frame':e.frame,'bitmap_page':(e.read(0x04000000,2)>>4)&1,**{x:g(x) for x in ['frame','render_cycles','render_profile_serial','render_profile_state','render_profile_update','render_profile_render','render_profile_vblank_start','render_profile_vblank_end']}})
 def tap(k):step(2,k);step(4)
 def snapshot():return e.bytes(sym['adventure_save'],C.sizeof(Save))
 def shot(command,page):
  f=a.output/f'command-{command:03}-{page}.png';e.screenshot(f);captures.append({'command':command,'page':page,'file':f.name,'sha256':sha(f),'hardware_frame':e.frame})
 try:
  e.load_save(a.save);e.reset();step(160);tap('A');step(240)
  for _ in range(2400):
   if g('game_state')==1 and not g('scene_present_phase') and not g('save_requested') and not g('save_feedback_background'):break
   step()
  assert g('game_state')==1;tap('START');tap('DOWN');tap('A');assert g('journal_tab')==2;baseline=snapshot();s=Save.from_buffer_copy(baseline);owned=[i for i,c in enumerate(s.roster.instances) if c.flags&1]
  for index in owned:
   c=s.roster.instances[index];row=e.read(sym['creature_form_index']+c.form_id,1);f=sym['creature_forms']+(row-1)*32;offset=e.read(f+18,2);count=e.read(f+20,1)
   learned={e.read(sym['creature_learnsets']+(offset+n)*2+1,1) for n in range(count) if e.read(sym['creature_learnsets']+(offset+n)*2,1)<=c.level};assert learned
   label=f'party-instance-{index}'
   for _ in range(162):
    if g('quickparty_menu_candidate')==index:break
    tap('DOWN')
   assert g('quickparty_menu_candidate')==index;tap('A');assert g('quickparty_menu_detail');previewed=set()
   for _ in range(len(learned)):
    command=g('quickparty_menu_command');assert command in learned and command not in previewed;previewed.add(command);label=f'command-{command}-combat';step(3)
    if command not in seen:shot(command,'combat')
    label=f'command-{command}-field';tap('DOWN');assert g('companion_guide_page')==1
    if command not in seen:shot(command,'field')
    seen.add(command);label=f'command-{command}-combat';tap('UP');assert not g('companion_guide_page');tap('RIGHT');assert snapshot()==baseline
   assert previewed==learned;tap('B');assert not g('quickparty_menu_detail') and g('journal_tab')==2
  assert seen==set(range(1,129));assert snapshot()==baseline and not e.lib.eb_faults(e.ptr)
  completed=list({p['render_profile_serial']:p for p in profiles if p['render_profile_state']==3}.values());over=[p for p in completed if p['render_cycles']>280896];gaps=[]
  for old,new in zip(completed,completed[1:]):
   if new['render_profile_serial']==old['render_profile_serial']+2 and new['hardware_frame']-old['hardware_frame']!=1:gaps.append({'before':old,'after':new})
  flips=[{'before':old,'after':new} for old,new in zip(completed,completed[1:]) if new['render_profile_serial']==old['render_profile_serial']+2 and new['bitmap_page']==old['bitmap_page']]
  result={'rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols),'fixture_sha256':sha(a.save),'harness_sha256':sha(a.output/Path(__file__).name),'scope':'128 inherited-command combat/field descriptions through controller-only Party browsing on historical72-individual collection; not fresh acquisition or command gameplay','commands':sorted(seen),'owned_individuals':len(owned),'save_unchanged':True,'no_game_memory_writes':True,'no_machine_state_imports':True,'faults':0,'completed_pause_updates':len(completed),'max_active_cycles':max(p['render_cycles'] for p in completed),'over_budget':over,'hardware_gaps':gaps,'missed_bitmap_flips':flips,'captures':captures,'inputs':inputs,'profiles':profiles};(a.output/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['captures','inputs','profiles','commands','over_budget','hardware_gaps','missed_bitmap_flips']},indent=2));print('over budget',len(over),'hardware gaps',len(gaps),'missed flips',len(flips))
 finally:e.close()
if __name__=='__main__':main()
