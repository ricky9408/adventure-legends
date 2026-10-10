#!/usr/bin/env python3
"""Accepted C4 ordinary saves must continue with exactly preserved Save5/SRAM."""
import argparse,json
from pathlib import Path
from connected_roads_save_compatibility import session,sha
BASE_ROM='3f4855b03a08b638c40c21274b858dfca18f2988f9f38deb15c35315bdba7423'
BASE_SYM='9c7a93652a792f0c014c8fe6b0d391bfeca8eadd4cfe05f1822f1bf2db53167b'
def main():
 p=argparse.ArgumentParser()
 for name in ('candidate','baseline-root','bridge','output'):p.add_argument('--'+name,type=Path,required=True)
 a=p.parse_args();assert not a.output.exists();a.output.mkdir(parents=True)
 metadata=json.loads((a.candidate/'candidate.json').read_text());rom=a.candidate/'emberbond.gba';sym=a.candidate/'emberbond.sym'
 assert sha(rom)==metadata['files']['emberbond.gba']['sha256'] and sha(sym)==metadata['files']['emberbond.sym']['sha256']
 base=a.baseline_root/'build/connected-roads-c4';assert sha(base/'emberbond.gba')==BASE_ROM and sha(base/'emberbond.sym')==BASE_SYM
 inputs=a.baseline_root/'build/connected-roads-campaign-c4';producer_path=inputs/'player-feedback-campaign.json';producer=json.loads(producer_path.read_text())
 assert producer['candidate']['rom_sha256']==BASE_ROM and producer['controller_only'] and producer['game_ram_writes']==producer['machine_state_imports']==0 and producer['route_complete'] and producer['native_cadence_passed'] and not producer['failures']
 report={'scope':__doc__,'candidate':metadata,'baseline_rom_sha256':BASE_ROM,'baseline_symbols_sha256':BASE_SYM,'producer_sha256':sha(producer_path),'helper_sha256':sha(__file__),'controller_only':True,'game_ram_writes':0,'machine_state_imports':0,'cases':[]}
 for name in ('grove-boss-entry','grove-complete','sky-complete','core-complete-ending-pending','earned-evolution-village','controller-complete-cold'):
  fixture=inputs/(name+'.sav');h=sha(fixture);assert h==producer['checkpoints'][name]['sram_sha256']
  old=session(base/'emberbond.gba',base/'emberbond.sym',a.bridge,fixture,a.output/(name+'-c4.sav'))
  new=session(rom,sym,a.bridge,fixture,a.output/(name+'-candidate.sav'))
  row={'name':name,'fixture_sha256':h,'save5_equal':old.pop('state')==new.pop('state'),'sram_equal':old.pop('sram')==new.pop('sram'),'baseline':old,'candidate':new};report['cases'].append(row)
  assert row['save5_equal'] and row['sram_equal'],row;assert sha(fixture)==h
 report['passed']=True;(a.output/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'passed':True,'ordinary_c4_fixtures':len(report['cases']),'complete_save5_and_sram_equal':True}))
if __name__=='__main__':main()
