#!/usr/bin/env python3
"""Paired fresh cold-SRAM input replay; compare displayed pixels by game update.
Read-only, with no machine-state loads or game memory writes.
"""
import argparse,hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from mgba_runner import Emulator
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--report',type=Path,required=True);p.add_argument('--start',type=int,required=True);p.add_argument('--end',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();out=a.output.resolve();out.mkdir(exist_ok=False,parents=True);d=json.loads(a.report.read_text());commands={}
for v in d['inputs']:
 for f in range(v['frame'],min(a.end,v['frame']+v['frames'])):commands[f]=v['keys']
 if v['frame']+v['frames']>=a.end:break
results={}
for label,src in [('B',Path(d['source_root'])),('patched',a.candidate.resolve())]:
 rom=src/'build/emberbond.gba';syms={s[2]:int(s[0],16)for line in rom.with_suffix('.sym').read_text().splitlines()if len(s:=line.split())==3};trace=[]
 with Emulator(rom)as e:
  e.write=lambda *args:(_ for _ in()).throw(AssertionError('RAM writes forbidden'));e.lib.eb_write=e.write;e.load_save(d['provenance']['fixture_path']);e.reset()
  for v in d['inputs']:
   if v['frame']>=a.start:break
   assert e.frame==v['frame'];e.frames(min(v['frames'],a.start-e.frame),v['keys'])
  g=lambda n:e.read(syms[n])
  fields=['frame','room','px','py','game_state','hp','face','summoned','ability_cd','toast_id','toast_ticks','camera_x','camera_y','return_game_revision'];before={n:g(n)for n in fields};start_sram=hashlib.sha256(e.bytes(0x0e000000,32768)).hexdigest()
  for f in range(a.start,a.end):
   previous=g('frame');page=e.read(0x04000000,2)&16;e.frames(1,commands[f]);pixels=e.screenshot();state={n:g(n)for n in fields};state['enemies']=e.bytes(syms['enemies'],120).hex();state['shots']=e.bytes(syms['shots'],288).hex();trace.append(dict(hardware_frame=e.frame,update_delta=(g('frame')-previous)&0xffffffff,page_flip=(e.read(0x04000000,2)&16)!=page,cycles=g('render_cycles'),state=state,pixels_sha256=hashlib.sha256(pixels.tobytes()).hexdigest()))
  e.screenshot(out/(label+'-end.png'))
 results[label]=dict(rom_sha256=sha(rom),before=before,start_sram_sha256=start_sram,trace=trace)
left,right=results['B'],results['patched'];assert left['before']==right['before'] and left['start_sram_sha256']==right['start_sram_sha256'],'cold replays reached different starting logical fixtures'
# Compare only completed presentations of the same logical update. Keep raw
# repeated/stalled hardware-frame rows in the receipt.
lrows={r['state']['frame']:r for r in left['trace'] if r['page_flip']};rrows={r['state']['frame']:r for r in right['trace'] if r['page_flip']};matched=sorted(lrows.keys()&rrows.keys());diff=[]
for f in matched:
 l,r=lrows[f],rrows[f]
 if l['state']!=r['state'] or l['pixels_sha256']!=r['pixels_sha256']:diff.append(dict(game_frame=f,baseline_hardware=l['hardware_frame'],patched_hardware=r['hardware_frame'],state_equal=l['state']==r['state'],pixels_equal=l['pixels_sha256']==r['pixels_sha256']))
report=dict(source_report=str(a.report),source_report_sha256=sha(a.report),results=results,matched_presentations=len(matched),differences=diff,game_ram_writes=0,machine_state_loads=0,helper_sha256=sha(__file__));(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'matched_presentations':len(matched),'differences':diff,'candidate_exceptions':[r for r in right['trace']if r['update_delta']!=1 or not r['page_flip']or r['cycles']>=280896]},indent=2));assert not diff
