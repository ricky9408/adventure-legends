#!/usr/bin/env python3
"""Paired controller-only cold-modal replay; never import cross-ROM machine state.

The target source trees and ROMs are immutable inputs. The producer supplies an
exact prior input sequence, not a success claim. Every hardware frame is kept,
including the control's known misses. Settled native framebuffer/OAM comparisons
check the uncovered growth-panel row as part of all 240x160 pixels.
"""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(root,producer,out):
 rom=root/'build/emberbond.gba';sym=rom.with_suffix('.sym');manifest=root/'build/source-hashes.json'
 sources=json.loads(manifest.read_text());assert all(sha(root/k)==v for k,v in sources.items())
 d=json.loads(producer.read_text());fixture=Path(d['provenance']['fixture_path']);assert sha(fixture)==d['provenance']['sram_sha256']
 symbols={v[2]:int(v[0],16) for line in sym.read_text().splitlines() if len(v:=line.split())==3}
 inputs={}
 for v in d['inputs']:
  for n in range(v['frame'],min(440,v['frame']+v['frames'])):inputs[n]=v['keys']
 assert set(range(440))<=inputs.keys()
 out.mkdir(parents=True,exist_ok=False);trace=[];scenes={}
 with Emulator(rom) as e:
  def reject(*a,**kw):raise AssertionError('RAM writes/state import forbidden')
  e.write=reject;e.state=reject;e.lib.eb_write=reject
  e.load_save(fixture);e.reset()
  get=lambda n:e.read(symbols[n])
  for n in range(440):
   old=get('frame');page=e.read(0x04000000,2)&16;e.frames(1,inputs[n])
   if n>=362:trace.append(dict(hardware_frame=e.frame,delta=(get('frame')-old)&0xffffffff,flip=(e.read(0x04000000,2)&16)!=page,cycles=get('render_cycles'),state=get('game_state'),tab=get('journal_tab')))
   if e.frame in range(368,435,6):
    name=f'frame-{e.frame}-tab-{get("journal_tab")}';im=e.screenshot(out/(name+'.png'))
    scenes[name]=dict(rgb_sha256=hashlib.sha256(im.tobytes()).hexdigest(),oam_sha256=hashlib.sha256(e.bytes(0x07000000,1024)).hexdigest(),state=get('game_state'),tab=get('journal_tab'))
  save=e.bytes(0x0e000000,32768)
 result=dict(rom_sha256=sha(rom),symbols_sha256=sha(sym),elf_sha256=sha(rom.with_suffix('.elf')),source_manifest_sha256=sha(manifest),producer_sha256=sha(producer),fixture_sha256=sha(fixture),controller_only=True,game_ram_writes=0,machine_state_imports=0,trace=trace,scenes=scenes,final_sram_sha256=hashlib.sha256(save).hexdigest(),max_cycles=max(v['cycles'] for v in trace),misses=[v for v in trace if v['delta']!=1 or not v['flip'] or v['cycles']>=280896])
 (out/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result

def main():
 p=argparse.ArgumentParser(description=__doc__)
 for k in ('before-root','after-root','producer','output'):p.add_argument('--'+k,type=Path,required=True)
 a=p.parse_args();a.output.mkdir(parents=True,exist_ok=False)
 b=run(a.before_root.resolve(),a.producer.resolve(),a.output/'before');c=run(a.after_root.resolve(),a.producer.resolve(),a.output/'after')
 checks=[dict(scene=k,pixels_same=b['scenes'][k]['rgb_sha256']==v['rgb_sha256'],oam_same=b['scenes'][k]['oam_sha256']==v['oam_sha256'],state_same=(b['scenes'][k]['state'],b['scenes'][k]['tab'])==(v['state'],v['tab'])) for k,v in c['scenes'].items()]
 report=dict(suite='paired-real-controller-cold-modal-reuse',before_rom=b['rom_sha256'],after_rom=c['rom_sha256'],controller_only=True,game_ram_writes=0,cross_rom_state_imports=0,checks=checks,sram_equal=b['final_sram_sha256']==c['final_sram_sha256'],before_max=b['max_cycles'],after_max=c['max_cycles'],before_misses=b['misses'],after_misses=c['misses'],helper_sha256=sha(__file__))
 (a.output/'comparison.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
 assert all(v['pixels_same'] and v['oam_same'] and v['state_same'] for v in checks) and report['sram_equal'] and not c['misses']
if __name__=='__main__':main()
