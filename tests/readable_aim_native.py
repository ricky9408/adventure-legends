#!/usr/bin/env python3
"""Controller-only hold/notice diagnostic from hash-bound earned ordinary SRAM.

If the producer ROM differs, report that compatibility branch explicitly; never
claim fresh candidate acquisition. No game-RAM writes or machine states.
"""
import argparse,ctypes as C,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from journey_guidance_earned import StrictNative
from test_save5 import Save
from mgba_runner import keymask
def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--rom',type=Path,required=True);p.add_argument('--symbols',type=Path,required=True);p.add_argument('--bridge',type=Path,required=True);p.add_argument('--producer-report',type=Path,required=True);p.add_argument('--snapshot',default='horizons-03-water-contribution');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 a.output.mkdir(parents=True,exist_ok=False)
 producer=json.loads(a.producer_report.read_text());snapshot=producer['snapshots'][a.snapshot]
 source=Path(snapshot['sram_path']);assert sha(source)==snapshot['sram_sha256']
 candidate=sha(a.rom);sym={v[2]:int(v[0],16)for line in a.symbols.read_text().splitlines()if len(v:=line.split())==3}
 report={'scope':__doc__,'candidate_rom_sha256':candidate,'symbols_sha256':sha(a.symbols),'bridge_sha256':sha(a.bridge),'producer_report_sha256':sha(a.producer_report),'producer_rom_sha256':snapshot['candidate_sha256'],'source_sram_sha256':sha(source),'source_snapshot':a.snapshot,'cross_rom_ordinary_sram_diagnostic':candidate!=snapshot['candidate_sha256'],'fresh_candidate_acquisition_claimed':False,'game_ram_writes':0,'machine_state_imports':0,'personal_save_access':False,'inputs':[],'captures':[],'checks':[],'metrics':{'measured_frames':0,'update_misses':0,'flip_misses':0,'overruns':0,'peak_cycles':0},'frames':[]}
 e=None;case=''
 def g(n,w=4):return e.read(sym[n],w)
 def save_state():return Save.from_buffer_copy(e.bytes(sym['adventure_save'],C.sizeof(Save)))
 def check(label,value):
  report['checks'].append({'case':case,'label':label,'passed':bool(value)});assert value,label
 def step(n,k=0,measured=True):
  report['inputs'].append({'case':case,'hardware_frame':e.frame,'frames':n,'keys':keymask(k),'measured':measured})
  for _ in range(n):
   old=g('frame');page=e.read(0x04000000,2)&16;e.frames(1,k)
   if measured:
    row={'case':case,'hardware_frame':e.frame,'delta':(g('frame')-old)&0xffffffff,'flip':bool((e.read(0x04000000,2)&16)!=page),'cycles':g('render_cycles'),'state':g('game_state'),'age':g('return_power_age'),'time':g('return_power_time'),'cooldown':g('ability_cd'),'toast_ticks':g('toast_ticks'),'x':g('px'),'y':g('py')}
    report['frames'].append(row);m=report['metrics'];m['measured_frames']+=1;m['update_misses']+=row['delta']!=1;m['flip_misses']+=not row['flip'];m['overruns']+=row['cycles']>=280896;m['peak_cycles']=max(m['peak_cycles'],row['cycles'])
 def tap(k,n=2,r=3):step(n,k);step(r)
 def capture(label):
  path=a.output/(label+'.png');e.screenshot(path)
  report['captures'].append({'case':case,'label':label,'png_sha256':sha(path),'hardware_frame':e.frame,'state':{n:g(n)for n in ('game_state','room','px','py','summoned','ability_cd','return_power_age','return_power_time','return_power_cast_time','toast_ticks','play_notice_hint','play_notice_toast')}})
 def boot(label):
  nonlocal e,case
  if e:e.close()
  case=label;e=StrictNative(a.rom,a.bridge);e.load_save(source);e.reset()
  step(160,measured=False);step(2,'A',False);step(3,measured=False);step(450,measured=False)
  check('ordinary Continue reaches PLAY',g('game_state')==1)
  r=save_state().roster;c=r.instances[r.party[r.selected_party]]
  check('earned Rillkite/104 remains selected',c.form_id==103 and c.equipped[c.selected_command]==104)
  if g('summoned'):tap('B')
  step(150);tap('B');check('B retains summon semantics',g('summoned')==1)
 try:
  boot('deliberate-hold-and-deferred-toast');capture('summon-toast')
  step(2,'R');position=(g('px'),g('py'));camera=(g('camera_x'),g('camera_y'));walk_phase=g('walk_phase');time=g('return_power_time');pose=g('return_power_cast_time');toast=g('toast_ticks');cd=g('ability_cd');quests=bytes(save_state().quests)
  step(60,'R');capture('held-aim-after-one-second')
  check('held anticipation freezes age/effect/pose, not cooldown',g('return_power_age')==0 and g('return_power_time')==time and g('return_power_cast_time')==pose and g('ability_cd')==max(0,cd-60))
  check('action hint defers the entire toast timer',g('toast_ticks')==toast)
  check('anticipation grants no saved quest progress',bytes(save_state().quests)==quests)
  step(2,'R+LEFT');capture('revised-aim-without-walking')
  check('aim direction does not move the hero',position==(g('px'),g('py')))
  check('aim direction does not move the camera',camera==(g('camera_x'),g('camera_y')))
  check('aim direction does not advance walking animation',g('walk_phase')==walk_phase)
  step(2,'R+START');check('START opens pause',g('game_state')==3);before=(g('return_power_age'),g('return_power_time'),g('ability_cd'),g('toast_ticks'));step(60,'R');capture('paused-held-aim')
  check('pause freezes ability/cooldown/deferred notification',before==(g('return_power_age'),g('return_power_time'),g('ability_cd'),g('toast_ticks')))
  step(2,'R+B');step(1,'R');check('B closes pause without dismissing held companion',g('game_state')==1 and g('summoned')==1)
  step(3);capture('released-aim-and-resumed-toast')
  check('release resumes original effect timeline',g('return_power_age')>0 and g('return_power_time')==time-g('return_power_age'))
  check('toast resumes only after hint relinquishes the slot',g('toast_ticks')<toast and g('toast_ticks')>=toast-5)
  boot('bounded-timeout');step(96,'R');capture('hold-timeout-starts-default-cast')
  check('holding forever times out without recast',3<=g('return_power_age')<=8 and g('return_power_time')==30-g('return_power_age'))
  boot('dismissal-semantics');step(30,'R');step(2,'R+B');step(10,'R')
  check('B still dismisses and cannot keep anticipation held',g('summoned')==0 and g('return_power_age')>0)
  boot('companion-field-guide');tap('START');baseline=bytes(save_state());tap('DOWN');tap('A')
  check('A opens the companion browser',g('journal_tab')==2);tap('A');tap('DOWN');step(4);capture('localized-held-aim-field-guide')
  check('field guide explains hold/release without committing changes',g('quickparty_menu_detail')==1 and g('companion_guide_page')==1 and bytes(save_state())==baseline)
  check('measured input/menu/render cadence has no misses',not any(report['metrics'][n]for n in ('update_misses','flip_misses','overruns')))
  check('native core has no faults',e.lib.eb_faults(e.ptr)==0)
  report['passed']=True
 finally:
  if e:e.close()
  assert sha(source)==snapshot['sram_sha256'],'source earned save changed'
  (a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n')
 print(json.dumps({'passed':report.get('passed',False),'metrics':report['metrics'],'cross_rom_ordinary_sram_diagnostic':report['cross_rom_ordinary_sram_diagnostic']},indent=2))
if __name__ == '__main__':
    from current_field_controls import require_current_acceptance
    require_current_acceptance(__file__)

if __name__=='__main__':main()
