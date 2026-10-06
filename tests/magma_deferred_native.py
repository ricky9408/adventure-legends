#!/usr/bin/env python3
"""Native patch-compatibility/timing probe from exact controller-earned C SRAM.
Only SRAM is cold imported. Never a producer machine state or game RAM write.
This verifies forward retained-data rest behavior, not new acquisition on D.
"""
import argparse,hashlib,json,shutil
from pathlib import Path
from magma_journey import ROOT,Emulator,digest,elf_locals
from northern_journey import newest_bank
SOURCE_REPORT_SHA='439a0096fc5f70109fcebc52082ad6bf815c53eef148e1b6b3aada5892913c27'
SOURCE_ROM_SHA='8080b2fb1c82a99650da9837c5f5037a570dc3e5b17eb1a10ee7a9d7c31ffde4'
SOURCE_SRAM_SHA='8287fb0c34b2cdd2a73408bd24bf290f640281ac3a8b7d98d0ad8a5f009ece28'
p=argparse.ArgumentParser(description=__doc__)
for n in ('rom','symbols','source-report','output'):p.add_argument('--'+n,required=True,type=Path)
for n in ('expected-rom-sha','expected-symbols-sha'):p.add_argument('--'+n,required=True)
a=p.parse_args();assert digest(a.rom)==a.expected_rom_sha and digest(a.symbols)==a.expected_symbols_sha
assert digest(a.source_report)==SOURCE_REPORT_SHA
r=json.loads(a.source_report.read_text());assert r['rom_sha256']==SOURCE_ROM_SHA and r['controller_only'] and not r['game_ram_writes'] and not r['failures'] and all(c['passed'] for c in r['checks'])
rec=r['snapshots']['09-all65-earned-town'];source=Path(rec['sram_path']);assert digest(source)==SOURCE_SRAM_SHA==rec['sram_sha256']
bank=newest_bank(source.read_bytes());assert int.from_bytes(bank[12:14],'little')==5
assert sum(bool(bank[161+i*24]&1) for i in range(160))==34 and sum(x.bit_count() for x in bank[112:128])==65
out=a.output;out.mkdir(parents=True,exist_ok=False)
for src,dst in ((a.rom,out/'tested.gba'),(a.symbols,out/'tested.sym'),(a.rom.with_suffix('.elf'),out/'tested.elf'),(source,out/'source-C-earned34.sav'),(a.source_report,out/'source-C-acquisition.json')):shutil.copyfile(src,dst)
elf_locals(out/'tested.elf',out/'tested.gba')
rows=[x for line in (out/'tested.sym').read_text().splitlines() if len(x:=line.split())==3]
sym={x[2]:int(x[0],16) for x in rows};e=Emulator(out/'tested.gba');e.load_save(out/'source-C-earned34.sav');e.reset()
def reject(*args,**kwargs):raise AssertionError('No RAM/state mutation allowed')
e.write=reject;e.state=reject
checks=[];trace=[]
def check(v,label):checks.append({'passed':bool(v),'label':label});assert v,label
def get(n):return e.read(sym[n])
def settle():
 for _ in range(160):
  if get('game_state')!=6:break
  e.frames(1)
 check(get('game_state')==1 and not get('save_failed'),'normal native boot/save returns to play')
try:
 e.frames(150);e.frames(2,'START');e.frames(35);settle();check(get('room')==38,'full34 source resumes at town anchor')
 e.frames(160);e.frames(2,'UP');e.frames(4);check(abs(get('px')-112)+abs(get('py')-248)<23,'actual player is in anchor interaction range')
 before=e.bytes(sym['adventure_save'],5300);last=get('frame');page=e.read(0x04000000,2)&16
 for i in range(180):
  e.frames(1,'A' if i==0 else 0);now=get('frame');npage=e.read(0x04000000,2)&16
  trace.append({'hardware_frame':e.frame,'update_delta':(now-last)&0xffffffff,'page_flip':npage!=page,'cycles':get('render_cycles'),'state':get('game_state'),'save_gate':get('save_begin_pending'),'writer_state':e.read(sym['writer_status'])})
  last,page=now,npage
 check(all(t['update_delta']==1 and t['page_flip'] for t in trace),'every native rest/save hardware frame updates and presents')
 check(max(t['cycles'] for t in trace)<280896,'no measured update exceeds hardware budget')
 check({1,2,3}<={t['save_gate'] for t in trace},'both notice pages warm before exact deferred proof and snapshot')
 check(any(t['state']==6 for t in trace) and trace[-1]['state']==1 and not get('save_failed'),'actual incremental save completes successfully')
 saved=e.bytes(0x0e000000,32768);(out/'saved-D.sav').write_bytes(saved);latest=newest_bank(saved)
 check(latest[96:5056]==bank[96:5056],'retained roster quests equipment and lifetime evidence remain byte-identical')
 e.screenshot(out/'native-after-save.png')
finally:
 report={'suite':'magma-native-deferred-rest-forward-compatibility','controller_only':True,'game_ram_writes':0,'machine_state_loads':0,'source_report_sha256':SOURCE_REPORT_SHA,'source_rom_sha256':SOURCE_ROM_SHA,'source_sram_sha256':SOURCE_SRAM_SHA,'rom_sha256':digest(out/'tested.gba'),'symbols_sha256':digest(out/'tested.sym'),'elf_sha256':digest(out/'tested.elf'),'test_sha256':digest(__file__),'scope':'ExactC earned34 SRAM cold-import, actual rest and full save. Not target-ROM acquisition evidence.','checks':checks,'trace':trace,'max_cycles':max((t['cycles'] for t in trace),default=0),'updates':sum(t['update_delta'] for t in trace),'flips':sum(t['page_flip'] for t in trace)}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');e.close();print(json.dumps({k:report[k] for k in ('checks','max_cycles','updates','flips')},indent=2))
