#!/usr/bin/env python3
"""Cold-Continue comparison with accepted Experience Polish P2 ordinary SRAM.

Only button input is used. Compares complete Save5 state and exported cartridge
SRAM after equivalent settled Continue sessions. A supplied authenticated P2
ROM/symbol pair is required; no user save or machine state is read.
"""
import argparse,ctypes as C,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path[:0]=[str(ROOT/'tests'),str(ROOT/'tools')]
from player_feedback_campaign import ControllerNative
from player_feedback_native import sha
from test_save5 import Save
BASE_ROM='b643fb74cf4e7bd524ed56dc43056b3662d0f59ae871853ef3e23456eef47086'
BASE_SYM='0de41203f3406c2e0a7350c92136a785084604c344028acc0e750f1ea5a38039'

def session(rom,symbols,bridge,fixture,out):
 sym={v[2]:int(v[0],16) for line in symbols.read_text().splitlines() if len(v:=line.split())==3}
 e=ControllerNative(rom,bridge);actions=[]
 def g(n):return e.read(sym[n])
 def step(n,k=0):actions.append({'hardware_frame':e.frame,'frames':n,'keys':k});e.frames(n,k)
 try:
  e.load_save(fixture);e.reset();step(160);assert g('game_state')==0 and g('has_save')
  step(2,'A');step(3)
  for _ in range(1600):
   if g('game_state')==1 and not g('save_requested') and not g('save_feedback_background'):break
   if g('game_state')==2:step(2,'A');step(3)
   else:step(1)
  else:raise AssertionError('Continue failed to settle')
  step(10);assert g('game_state')==1 and not g('save_failed') and not e.lib.eb_faults(e.ptr)
  state=e.bytes(sym['adventure_save'],C.sizeof(Save));method=e.save(out)
  return {'state':state,'sram':out.read_bytes(),'actions':actions,'state_sha256':hashlib.sha256(state).hexdigest(),'sram_sha256':sha(out),'export_method':method,'room':g('room'),'hp_q4':g('hero_hp_q4'),'loaded_save_version':g('loaded_save_version'),'hardware_frames':e.frame}
 finally:e.close()

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for n in ('rom','symbols','baseline-rom','baseline-symbols','bridge','output'):p.add_argument('--'+n,type=Path,required=True)
 p.add_argument('--expected-rom-sha',required=True);a=p.parse_args();assert sha(a.rom)==a.expected_rom_sha and sha(a.baseline_rom)==BASE_ROM and sha(a.baseline_symbols)==BASE_SYM
 out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);prov=ROOT/'tests/fixtures/experience-polish-p2/provenance.json';provenance=json.loads(prov.read_text());results=[]
 producer_path=ROOT/provenance['producer_path'];assert sha(producer_path)==provenance['producer_report_sha256'];producer=json.loads(producer_path.read_text());assert producer['candidate']['rom_sha256']==BASE_ROM and producer['controller_only'] and producer['game_ram_writes']==producer['machine_state_imports']==0 and producer['native_cadence_passed'] and not producer['failures']
 for f in provenance['fixtures']:
  fixture=ROOT/f['path'];assert sha(fixture)==f['sha256']==producer['checkpoints'][f['producer_snapshot']]['sram_sha256'];name=fixture.stem
  old=session(a.baseline_rom,a.baseline_symbols,a.bridge,fixture,out/(name+'-p2.sav'))
  new=session(a.rom,a.symbols,a.bridge,fixture,out/(name+'-candidate.sav'))
  result={'fixture':f,'complete_save5_equal':old.pop('state')==new.pop('state'),'complete_sram_equal':old.pop('sram')==new.pop('sram'),'p2':old,'candidate':new}
  assert result['complete_save5_equal'] and result['complete_sram_equal'],result
  assert sha(fixture)==f['sha256'];results.append(result)
 report={'scope':__doc__,'passed':True,'controller_only':True,'game_ram_writes':0,'machine_state_imports':0,'candidate':{'rom_sha256':sha(a.rom),'symbols_sha256':sha(a.symbols)},'baseline':{'rom_sha256':BASE_ROM,'symbols_sha256':BASE_SYM},'helper_sha256':sha(__file__),'bridge_sha256':sha(a.bridge),'fixture_provenance_sha256':sha(prov),'results':results}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'fixtures':len(results),'complete_save5_and_sram_equal':True}))
if __name__=='__main__':main()
