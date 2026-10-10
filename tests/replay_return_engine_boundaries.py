#!/usr/bin/env python3
"""Independent cold-SRAM replay of an authenticated boundary failure's inputs.
Forward rendering/performance diagnostic, not fresh acquisition. No code/RAM
writes or machine-state imports. Original raw misses are retained in control.
"""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def run(root,report,output,end):
 manifest=root/'build/source-hashes.json';m=json.loads(manifest.read_text());assert all(sha(root/k)==v for k,v in m.items())
 d=json.loads(report.read_text());assert len(d['cold_sram_sources'])==1 and d['game_ram_writes']==0 and d['machine_state_loads']==0
 source=d['cold_sram_sources'][0];saved=Path(source['path']);assert sha(saved)==source['sha256'];commands={}
 for v in d['inputs']:
  for f in range(v['frame'],min(end,v['frame']+v['frames'])):assert f not in commands;commands[f]=v['keys']
 assert set(range(end))<=commands.keys()
 output.mkdir(parents=True,exist_ok=False);rom=root/'build/emberbond.gba';sym=rom.with_suffix('.sym');syms={p[2]:int(p[0],16)for line in sym.read_text().splitlines()if len(p:=line.split())==3};rows=[];gate=False
 with Emulator(rom) as e:
  def reject(*a,**kw):raise AssertionError('No RAM write or machine-state load permitted')
  e.write=reject;e.lib.eb_write=reject;e.state=reject;e.load_save(saved);e.reset();get=lambda n:e.read(syms[n])
  for f in range(end):
   old=get('frame');state=get('game_state');page=e.read(0x04000000,2)&16;e.frames(1,commands[f]);new=get('frame')
   if not gate and state!=0 and new>0 and new>=old:gate=True
   row=dict(hardware_frame=e.frame,keys=commands[f],before=old,after=new,updates=(new-old)&0xffffffff,flip=bool((e.read(0x04000000,2)&16)!=page),cycles=get('render_cycles'),room=get('room'),state=get('game_state'),tab=get('journal_tab'),obj=get('obj_count'),strict=gate);rows.append(row)
   if f in (299,349,579,599):e.screenshot(output/f'frame-{f+1}.png')
 result=dict(suite='cold-earned-SRAM-boundary-replay',scope=__doc__,rom_sha256=sha(rom),symbols_sha256=sha(sym),elf_sha256=sha(rom.with_suffix('.elf')),manifest_sha256=sha(manifest),source_report_sha256=sha(report),source_sram_sha256=sha(saved),controller_only=True,game_ram_writes=0,machine_state_imports=0,trace=rows,strict_frames=sum(r['strict']for r in rows),exceptions=[r for r in rows if r['strict']and(r['updates']!=1 or not r['flip']or r['cycles']>=280896 or r['obj']>128)],max_cycles=max(r['cycles']for r in rows if r['strict']))
 (output/'report.json').write_text(json.dumps(result,indent=2)+'\n');return result

def main():
 p=argparse.ArgumentParser()
 for k in ('before-root','after-root','report','output'):p.add_argument('--'+k,type=Path,required=True)
 p.add_argument('--frames',type=int,default=600);a=p.parse_args();a.output.mkdir(exist_ok=False,parents=True)
 b=run(a.before_root.resolve(),a.report.resolve(),a.output/'before',a.frames);c=run(a.after_root.resolve(),a.report.resolve(),a.output/'after',a.frames)
 result=dict(before_rom=b['rom_sha256'],after_rom=c['rom_sha256'],before_exceptions=b['exceptions'],after_exceptions=c['exceptions'],before_max=b['max_cycles'],after_max=c['max_cycles'],strict_frames=c['strict_frames'],helper_sha256=sha(__file__))
 (a.output/'comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2));assert not c['exceptions']
if __name__=='__main__':main()
